#!/usr/bin/env python3
"""Threads の自分の投稿一覧＋メトリクスを取得し、発信記録スプレッドシートの
「Threads投稿一覧」シートに permalink 突合で upsert する。

- 認証: gcp/threads_token.json（access_token, user_id）。長期トークン(60日)。
- この VPS は IPv6 が通らないため、DNS 解決を IPv4 に固定する（graph.threads.net は
  IPv6 のみ返す環境があり、放置すると接続ハングする）。
- H列「X投稿URL」は手動入力列。スクリプトは絶対に上書きしない。

Usage:
  python3 scripts/fetch_threads_posts.py [--dry-run] [--max-pages N]
"""
import argparse
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# --- IPv4 固定（IPv6 が通らない環境でのハング回避）---
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
socket.getaddrinfo = _ipv4_only

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(ROOT, "gcp", "threads_token.json")
API = "https://graph.threads.net/v1.0"
SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
SHEET_NAME = "Threads投稿一覧"
JST = timezone(timedelta(hours=9))
POST_FIELDS = "id,text,permalink,timestamp,media_type,media_url,thumbnail_url,is_quote_post"
INSIGHT_METRICS = "views,likes,replies,reposts,quotes,shares"


def _load_token():
    with open(TOKEN_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return d["access_token"], str(d["user_id"])


def _get(url, timeout=30):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"APIエラー ({e.code}): {e.read().decode()}")


def fetch_posts(token, user_id, max_pages):
    """投稿一覧を全ページ取得（新しい順）。"""
    posts = []
    url = f"{API}/{user_id}/threads?" + urllib.parse.urlencode(
        {"fields": POST_FIELDS, "limit": 100, "access_token": token}
    )
    for _ in range(max_pages):
        d = _get(url)
        posts.extend(d.get("data", []))
        nxt = d.get("paging", {}).get("next")
        if not nxt:
            break
        url = nxt
    return posts


def fetch_insights(token, media_id):
    url = f"{API}/{media_id}/insights?" + urllib.parse.urlencode(
        {"metric": INSIGHT_METRICS, "access_token": token}
    )
    try:
        d = _get(url)
    except SystemExit:
        return {}
    out = {}
    for m in d.get("data", []):
        name = m.get("name")
        val = 0
        if m.get("values"):
            val = m["values"][0].get("value", 0)
        elif isinstance(m.get("total_value"), dict):
            val = m["total_value"].get("value", 0)
        out[name] = val or 0
    return out


def _jst(ts):
    """ISO(UTC) → 'YYYY/MM/DD HH:MM:SS'(JST)。"""
    try:
        dt = datetime.fromisoformat(ts.replace("+0000", "+00:00"))
        return dt.astimezone(JST).strftime("%Y/%m/%d %H:%M:%S")
    except Exception:
        return ts


def build_row(post, ins, now_str):
    text = post.get("text") or ""
    views = ins.get("views", 0)
    likes = ins.get("likes", 0)
    replies = ins.get("replies", 0)
    reposts = ins.get("reposts", 0)
    quotes = ins.get("quotes", 0)
    shares = ins.get("shares", 0)
    eng = likes + replies + reposts + quotes + shares
    def rate(x):
        return round(x / views, 4) if views else ""
    meta = [
        _jst(post.get("timestamp", "")),                 # A 投稿日時
        post.get("permalink", ""),                        # B 投稿URL
        text,                                             # C 本文
        post.get("media_type", ""),                       # D 種類
        len(text),                                        # E 文字数
        post.get("media_url") or post.get("thumbnail_url") or "",  # F 画像URL
        "",                                               # G 親投稿URL（v1は空）
    ]
    metrics = [
        views, likes, replies, reposts, quotes, shares,   # I〜N
        eng,                                              # O エンゲージメント合計
        rate(eng), rate(likes), rate(reposts),            # P,Q,R
        now_str,                                          # S 最終更新
    ]
    return meta, metrics


def get_gspread_ws():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if key_json:
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
    else:
        sa = os.path.join(ROOT, "gcp", "charming-well-464402-u4-2cfb7bddf343.json")
        creds = Credentials.from_service_account_file(sa, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-pages", type=int, default=20)
    args = ap.parse_args()

    token, user_id = _load_token()
    now_str = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")

    posts = fetch_posts(token, user_id, args.max_pages)
    print(f"投稿取得: {len(posts)} 件")

    rows = []  # (permalink, meta[A:G], metrics[I:S])
    for p in posts:
        ins = fetch_insights(token, p["id"])
        meta, metrics = build_row(p, ins, now_str)
        rows.append((p.get("permalink", ""), meta, metrics))
        time.sleep(0.2)  # レート制限に配慮

    if args.dry_run:
        print("--- dry-run: 書き込みはしません。先頭5件 ---")
        for permalink, meta, metrics in rows[:5]:
            print(f"[{meta[0]}] {meta[3]} views={metrics[0]} like={metrics[1]} rep={metrics[3]} | {meta[2][:36]}")
        print(f"（合計 {len(rows)} 行を upsert 予定）")
        return

    ws = get_gspread_ws()
    existing = ws.get_all_values()
    row_by_permalink = {}
    for i, row in enumerate(existing[1:], start=2):  # 2行目以降
        if len(row) > 1 and row[1]:
            row_by_permalink[row[1]] = i

    updates = []       # batch_update 用（既存行のメトリクス更新）
    new_rows = []      # 追記用（新規投稿）
    for permalink, meta, metrics in rows:
        r = row_by_permalink.get(permalink)
        if r:
            # A:G（本文等）と I:S（メトリクス）を更新。H（X投稿URL）は非上書き。
            updates.append({"range": f"A{r}:G{r}", "values": [meta]})
            updates.append({"range": f"I{r}:S{r}", "values": [metrics]})
        else:
            # 新規: A..G, H(空), I..S
            new_rows.append((meta, metrics))

    # 新規は古い順に追記（新しい順で取得しているため反転）
    new_rows.reverse()
    appended = 0
    if new_rows:
        payload = [meta + [""] + metrics for meta, metrics in new_rows]
        ws.append_rows(payload, value_input_option="USER_ENTERED")
        appended = len(payload)
    if updates:
        ws.batch_update(updates, value_input_option="USER_ENTERED")

    print(f"✓ 完了: 新規 {appended} 件追記 / 既存 {len(updates)//2} 件メトリクス更新")


if __name__ == "__main__":
    main()
