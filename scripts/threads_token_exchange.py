#!/usr/bin/env python3
"""Threads OAuth: 認可コード → 長期トークン(60日) を取得し gcp/threads_token.json に保存する。

Usage:
  THREADS_APP_SECRET='<Threads App Secret>' python3 scripts/threads_token_exchange.py [--code CODE]

認可コードは --code / 環境変数 THREADS_CODE / gcp/threads_code.txt の順で解決する。
App Secret は環境変数 THREADS_APP_SECRET から読む（引数・ファイルには残さない）。
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

THREADS_APP_ID = "4371768313073061"
REDIRECT_URI = "https://httpbin.org/get"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_code(arg_code: str) -> str:
    if arg_code:
        return arg_code.strip()
    if os.environ.get("THREADS_CODE"):
        return os.environ["THREADS_CODE"].strip()
    p = os.path.join(ROOT, "gcp", "threads_code.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    sys.exit("認可コードが見つかりません（--code / THREADS_CODE / gcp/threads_code.txt）")


def _post(url: str, data: bytes) -> dict:
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data)))
    except urllib.error.HTTPError as e:
        sys.exit(f"APIエラー ({e.code}): {e.read().decode()}")


def _get(url: str) -> dict:
    try:
        return json.load(urllib.request.urlopen(url))
    except urllib.error.HTTPError as e:
        sys.exit(f"APIエラー ({e.code}): {e.read().decode()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default="")
    args = ap.parse_args()

    secret = os.environ.get("THREADS_APP_SECRET")
    if not secret:
        sys.exit("THREADS_APP_SECRET 環境変数が未設定です")
    code = _resolve_code(args.code)

    # 1) 認可コード → 短期トークン
    body = urllib.parse.urlencode({
        "client_id": THREADS_APP_ID,
        "client_secret": secret,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }).encode()
    d = _post("https://graph.threads.net/oauth/access_token", body)
    short = d["access_token"]
    uid = d.get("user_id")
    print(f"短期トークン取得OK user_id={uid}")

    # 2) 短期 → 長期トークン(60日)
    q = urllib.parse.urlencode({
        "grant_type": "th_exchange_token",
        "client_secret": secret,
        "access_token": short,
    })
    d2 = _get("https://graph.threads.net/access_token?" + q)

    out = {
        "access_token": d2["access_token"],
        "user_id": uid,
        "token_type": d2.get("token_type"),
        "expires_in": d2.get("expires_in"),
        "obtained_at": int(time.time()),
    }
    os.makedirs(os.path.join(ROOT, "gcp"), exist_ok=True)
    with open(os.path.join(ROOT, "gcp", "threads_token.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"✓ 長期トークンを gcp/threads_token.json に保存。有効日数≈{(d2.get('expires_in') or 0)//86400}")

    # 使い終わった認可コードファイルは削除（単回利用のため）
    cp = os.path.join(ROOT, "gcp", "threads_code.txt")
    if os.path.exists(cp):
        os.remove(cp)


if __name__ == "__main__":
    main()
