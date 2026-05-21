#!/usr/bin/env python3
"""
リプ・引用一覧シートから指定 tweet_ids の反応を抽出して /tmp/sheet_replies.json に保存。

使い方:
  python3 fetch_sheet_replies.py --tweet_ids "id1,id2,..."

出力形式:
  [{"username": "@...", "display_name": "...", "tweet_id": "...", "parent_tweet_id": "...",
    "type": "リプライ|引用RT", "reaction_text": "..."}, ...]

列構成（リプ・引用一覧）:
  A=投稿日時 / B=アカウントID(@username) / C=アカウント名 / D=ポストURL /
  E=ポスト本文 / F=ポスト種類 / G=親ポストURL
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import requests

SS1 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
RANGE_REPLIES = "リプ・引用一覧!A:G"
OUTPUT_PATH = "/tmp/sheet_replies.json"
SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"

COL_USERNAME = 1     # B: アカウントID (@username)
COL_DISPNAME = 2     # C: アカウント名
COL_POST_URL = 3     # D: ポストURL
COL_TEXT = 4         # E: ポスト本文
COL_TYPE = 5         # F: ポスト種類
COL_PARENT_URL = 6   # G: 親ポストURL


def b64u(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def get_access_token(key_data: dict) -> str:
    now = int(time.time())
    header = b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = b64u(json.dumps({
        "iss": key_data["client_email"],
        "scope": SCOPES,
        "aud": TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
    }).encode())
    msg = header + b"." + payload

    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(key_data["private_key"])
        tmpkey = f.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", tmpkey],
            input=msg, capture_output=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"openssl error: {result.stderr.decode()}")
        sig = b64u(result.stdout)
    finally:
        os.unlink(tmpkey)

    jwt_token = (msg + b"." + sig).decode()
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def extract_tweet_id(url: str) -> str:
    m = re.search(r"/status/(\d+)", str(url))
    return m.group(1) if m else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tweet_ids", required=True, help="カンマ区切りの tweet_id リスト")
    args = parser.parse_args()

    target_ids = set(tid.strip() for tid in args.tweet_ids.split(",") if tid.strip())
    if not target_ids:
        print("ERROR: --tweet_ids が空です", file=sys.stderr)
        sys.exit(1)

    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not raw:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_KEY が未設定", file=sys.stderr)
        sys.exit(1)
    key_data = json.loads(raw)

    print("STEP 1: アクセストークン取得中...", file=sys.stderr)
    token = get_access_token(key_data)

    print("STEP 2: リプ・引用一覧取得中...", file=sys.stderr)
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SS1}/values/{requests.utils.quote(RANGE_REPLIES)}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    resp.raise_for_status()
    rows = resp.json().get("values", [])
    print(f"  取得行数: {len(rows)} 行（ヘッダー含む）", file=sys.stderr)

    results = []
    seen = set()  # (username, parent_tweet_id) の重複除去

    for row in rows[1:]:  # ヘッダースキップ
        if len(row) <= COL_PARENT_URL:
            continue

        parent_url = str(row[COL_PARENT_URL]).strip()
        parent_tweet_id = extract_tweet_id(parent_url)
        if parent_tweet_id not in target_ids:
            continue

        post_url = str(row[COL_POST_URL]).strip() if len(row) > COL_POST_URL else ""
        tweet_id = extract_tweet_id(post_url)
        username = str(row[COL_USERNAME]).strip() if len(row) > COL_USERNAME else ""
        display_name = str(row[COL_DISPNAME]).strip() if len(row) > COL_DISPNAME else ""
        reaction_text = str(row[COL_TEXT]).strip() if len(row) > COL_TEXT else ""
        post_type = str(row[COL_TYPE]).strip() if len(row) > COL_TYPE else ""

        # @が付いていない場合は付与
        if username and not username.startswith("@"):
            username = "@" + username

        dedup_key = (username, parent_tweet_id)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        results.append({
            "username": username,
            "display_name": display_name,
            "tweet_id": tweet_id,
            "parent_tweet_id": parent_tweet_id,
            "type": post_type,
            "reaction_text": reaction_text,
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(results)}件を {OUTPUT_PATH} に保存しました")


if __name__ == "__main__":
    main()
