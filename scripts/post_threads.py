#!/usr/bin/env python3
"""Threads へ投稿する。500字を超える本文は返信チェーン（スレッド）で分割投稿する。
セルフリプ（--reply-text）は本文スレッドの末尾に返信で連結する。画像は各先頭投稿に付ける。
--image-url / --reply-image-url は空白・改行区切りで複数指定可（2枚以上はカルーセル投稿）。

Usage:
  python3 scripts/post_threads.py --text "本文" [--image-url "URL1 URL2 ..."] \
      [--reply-text "セルフリプ"] [--reply-image-url "URL ..."] [--dry-run]

認証: gcp/threads_token.json（access_token, user_id）。要 threads_content_publish スコープ。
IPv6 が通らない環境向けに DNS を IPv4 固定する。
"""
import argparse
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

_orig = socket.getaddrinfo
socket.getaddrinfo = lambda *a, **k: [r for r in _orig(*a, **k) if r[0] == socket.AF_INET] or _orig(*a, **k)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(ROOT, "gcp", "threads_token.json")
API = "https://graph.threads.net/v1.0"
LIMIT = 500  # Threads 1投稿の文字数上限


def _load_token():
    d = json.load(open(TOKEN_PATH, encoding="utf-8"))
    return d["access_token"], str(d["user_id"])


def _pack(units, sep):
    out, cur = [], ""
    for u in units:
        cand = (cur + sep + u) if cur else u
        if len(cand) <= LIMIT:
            cur = cand
        else:
            if cur:
                out.append(cur)
            cur = u
    if cur:
        out.append(cur)
    return out


def split_text(text):
    """text を ≤500字のチャンクに分割（段落→文→ハードの順で自然な境界を優先）。"""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= LIMIT:
        return [text]
    subunits = []
    for para in text.split("\n\n"):
        para = para.strip("\n")
        if not para:
            continue
        if len(para) <= LIMIT:
            subunits.append(para)
            continue
        sents = [s for s in re.split(r"(?<=。)|(?<=\n)", para) if s]
        norm = []
        for s in sents:
            while len(s) > LIMIT:
                norm.append(s[:LIMIT])
                s = s[LIMIT:]
            if s:
                norm.append(s)
        subunits.extend(_pack(norm, ""))
    return _pack(subunits, "\n\n")


def _api_post(path, params):
    data = urllib.parse.urlencode(params).encode()
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(f"{API}/{path}", data=data), timeout=60))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"APIエラー ({e.code}): {e.read().decode()}")


def _publish(token, user_id, creation_id, retries=5, wait=8):
    """コンテナを publish する。Threads の一時的な整合性遅延（作成直後の
    「素材が見つからない」= code 24 / subcode 4279009 や code 1）に備え、
    その種のエラーのときだけ数回リトライする。それ以外のエラーは即中断。"""
    url = f"{API}/{user_id}/threads_publish"
    data = urllib.parse.urlencode({"access_token": token, "creation_id": creation_id}).encode()
    last = ""
    for i in range(retries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=60))["id"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            last = f"{e.code}: {body}"
            transient = ('4279009' in body or '"code":24' in body
                         or 'does not exist' in body or '"code":1' in body)
            if i < retries - 1 and transient:
                print(f"  publish 一時エラー、{wait}秒後にリトライ ({i+1}/{retries})", flush=True)
                time.sleep(wait)
                continue
            raise SystemExit(f"APIエラー (publish {last})")


def _api_get(path, params):
    q = urllib.parse.urlencode(params)
    try:
        return json.load(urllib.request.urlopen(f"{API}/{path}?{q}", timeout=60))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"APIエラー ({e.code}): {e.read().decode()}")


def _wait_finished(token, creation_id, timeout=90):
    """コンテナが FINISHED になるまで待つ。"""
    waited = 0
    while waited < timeout:
        d = _api_get(creation_id, {"fields": "status,error_message", "access_token": token})
        st = d.get("status")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise SystemExit(f"コンテナ作成失敗: status={st} {d.get('error_message','')}")
        time.sleep(5)
        waited += 5
    # タイムアウトしても publish を試みる（テキストは status 省略されることがある）


CAROUSEL_MAX = 20  # Threads カルーセルの最大枚数


def parse_urls(s):
    """空白・改行区切りの画像URL文字列を URL リストにする。"""
    return [u for u in re.split(r"\s+", (s or "").strip()) if u]


def post_one(token, user_id, text, image_urls=None, reply_to_id=None):
    """1投稿を作成→公開し post_id を返す。画像2枚以上はカルーセルにする。"""
    image_urls = image_urls or []
    if len(image_urls) >= 2:
        # カルーセル: 各画像の item コンテナ → CAROUSEL コンテナ → publish
        urls = image_urls[:CAROUSEL_MAX]
        if len(image_urls) > CAROUSEL_MAX:
            print(f"  ⚠ 画像 {len(image_urls)}枚 → 上限 {CAROUSEL_MAX}枚に切り詰め")
        child_ids = []
        for u in urls:
            child = _api_post(f"{user_id}/threads", {
                "access_token": token, "media_type": "IMAGE",
                "is_carousel_item": "true", "image_url": u,
            })["id"]
            _wait_finished(token, child)
            child_ids.append(child)
        params = {
            "access_token": token, "media_type": "CAROUSEL",
            "children": ",".join(child_ids), "text": text,
        }
        if reply_to_id:
            params["reply_to_id"] = reply_to_id
        cid = _api_post(f"{user_id}/threads", params)["id"]
        _wait_finished(token, cid)
        time.sleep(3)  # publish 前の整合性バッファ
        return _publish(token, user_id, cid)

    # テキスト or 単一画像
    params = {"access_token": token, "text": text}
    params["media_type"] = "IMAGE" if image_urls else "TEXT"
    if image_urls:
        params["image_url"] = image_urls[0]
    if reply_to_id:
        params["reply_to_id"] = reply_to_id
    cid = _api_post(f"{user_id}/threads", params)["id"]
    _wait_finished(token, cid)
    time.sleep(3)  # publish 前の整合性バッファ
    return _publish(token, user_id, cid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--image-url", default="")
    ap.add_argument("--reply-text", default="")
    ap.add_argument("--reply-image-url", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    body_chunks = split_text(args.text)
    reply_chunks = split_text(args.reply_text)
    body_imgs = parse_urls(args.image_url)
    reply_imgs = parse_urls(args.reply_image_url)
    if not body_chunks:
        sys.exit("本文が空です")

    if args.dry_run:
        print(f"--- dry-run: 本文{len(body_chunks)}件＋リプ{len(reply_chunks)}件 ---")
        for i, c in enumerate(body_chunks, 1):
            tag = f"[本文画像{len(body_imgs)}枚{'/カルーセル' if len(body_imgs) >= 2 else ''}]" if (i == 1 and body_imgs) else ""
            print(f"本文{i}({len(c)}字){tag}: {c[:60]}")
        for i, c in enumerate(reply_chunks, 1):
            tag = f"[リプ画像{len(reply_imgs)}枚{'/カルーセル' if len(reply_imgs) >= 2 else ''}]" if (i == 1 and reply_imgs) else ""
            print(f"リプ{i}({len(c)}字){tag}: {c[:60]}")
        return

    token, user_id = _load_token()
    prev_id = None
    first_id = None
    # 本文スレッド（画像は先頭投稿にまとめて付ける。2枚以上はカルーセル）
    for i, chunk in enumerate(body_chunks):
        imgs = body_imgs if i == 0 else None
        pid = post_one(token, user_id, chunk, image_urls=imgs, reply_to_id=prev_id)
        prev_id = pid
        if first_id is None:
            first_id = pid
        print(f"  本文{i+1}/{len(body_chunks)} 投稿 id={pid}")
    # セルフリプ（本文末尾に連結）
    for i, chunk in enumerate(reply_chunks):
        imgs = reply_imgs if i == 0 else None
        pid = post_one(token, user_id, chunk, image_urls=imgs, reply_to_id=prev_id)
        prev_id = pid
        print(f"  リプ{i+1}/{len(reply_chunks)} 投稿 id={pid}")

    permalink = _api_get(first_id, {"fields": "permalink", "access_token": token}).get("permalink", "")
    print(f"PERMALINK={permalink}")  # 機械可読（シェルが抽出）
    print(f"✓ 投稿完了: {permalink}（本文{len(body_chunks)}件＋リプ{len(reply_chunks)}件）")


if __name__ == "__main__":
    main()
