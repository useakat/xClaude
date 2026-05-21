#!/usr/bin/env python3
"""
X投稿一覧から対象投稿を抽出して /tmp/target_posts.json に保存。

フィルタ:
  --keyword TEXT   : 本文（C列）部分一致
  --how_id  ID     : outputs シート（SS2）の howID 列で絞り込み（例: W003）
  --days_back N    : 投稿日時が直近 N 日以内のもの（デフォルト: 制限なし）

出力形式:
  [{"tweet_id": "...", "date": "...", "text": "...", "profile_clicks": N, "follows": N}, ...]
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
from datetime import datetime, timedelta, timezone

import requests

SS1 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
SS2 = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"
RANGE_POSTS = "X投稿一覧!A:AC"
RANGE_OUTPUTS = "outputs!A:C"
OUTPUT_PATH = "/tmp/target_posts.json"
SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# 列インデックス（0-based）
COL_DATE = 0        # A: 投稿日時
COL_URL = 1         # B: ポストURL
COL_TEXT = 2        # C: ポスト本文
COL_PROFILE = 16    # Q: プロフアクセス
COL_FOLLOWS = 28    # AC: フォロー増


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


def fetch_sheet(token: str, spreadsheet_id: str, range_: str) -> list:
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{requests.utils.quote(range_)}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("values", [])


def safe_int(val: str) -> int:
    try:
        return int(str(val).replace(",", "").strip()) if val else 0
    except (ValueError, TypeError):
        return 0


def extract_tweet_id(url: str) -> str:
    m = re.search(r"/status/(\d+)", str(url))
    return m.group(1) if m else ""


def parse_date(val: str) -> datetime | None:
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(val).strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", default="")
    parser.add_argument("--how_id", default="")
    parser.add_argument("--days_back", type=int, default=0)
    args = parser.parse_args()

    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not raw:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_KEY が未設定", file=sys.stderr)
        sys.exit(1)
    key_data = json.loads(raw)

    print("STEP 1: アクセストークン取得中...", file=sys.stderr)
    token = get_access_token(key_data)

    # how_id フィルタ: SS2 outputs シートから対象 URL を取得
    allowed_urls: set | None = None
    if args.how_id:
        print(f"STEP 2a: outputs シートから how_id={args.how_id} の URL を取得...", file=sys.stderr)
        rows = fetch_sheet(token, SS2, RANGE_OUTPUTS)
        allowed_urls = set()
        for row in rows[1:]:  # ヘッダースキップ
            if len(row) >= 3 and str(row[2]).strip() == args.how_id:
                url = str(row[1]).strip()
                tid = extract_tweet_id(url)
                if tid:
                    allowed_urls.add(tid)
        print(f"  該当 tweet_id: {len(allowed_urls)}件", file=sys.stderr)

    print(f"STEP 2b: X投稿一覧取得中...", file=sys.stderr)
    rows = fetch_sheet(token, SS1, RANGE_POSTS)
    print(f"  取得行数: {len(rows)} 行（ヘッダー含む）", file=sys.stderr)

    cutoff = None
    if args.days_back > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days_back)

    results = []
    for row in rows[1:]:  # ヘッダースキップ
        if len(row) <= COL_URL:
            continue

        url = str(row[COL_URL]).strip() if len(row) > COL_URL else ""
        tweet_id = extract_tweet_id(url)
        if not tweet_id:
            continue

        # how_id フィルタ
        if allowed_urls is not None and tweet_id not in allowed_urls:
            continue

        text = str(row[COL_TEXT]).strip() if len(row) > COL_TEXT else ""

        # keyword フィルタ
        if args.keyword and args.keyword not in text:
            continue

        date_val = str(row[COL_DATE]).strip() if len(row) > COL_DATE else ""
        dt = parse_date(date_val)

        # days_back フィルタ
        if cutoff and dt and dt < cutoff:
            continue

        profile_clicks = safe_int(row[COL_PROFILE]) if len(row) > COL_PROFILE else 0
        follows = safe_int(row[COL_FOLLOWS]) if len(row) > COL_FOLLOWS else 0

        results.append({
            "tweet_id": tweet_id,
            "date": dt.strftime("%Y-%m-%d %H:%M:%S") if dt else date_val,
            "text": text,
            "profile_clicks": profile_clicks,
            "follows": follows,
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(results)}件を {OUTPUT_PATH} に保存しました")


if __name__ == "__main__":
    main()
