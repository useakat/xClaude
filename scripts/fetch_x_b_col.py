#!/usr/bin/env python3
"""
X投稿一覧シートの B列（ツイートURL）を取得し、
/tmp/x_analytics_b_col.json に保存する。

サービスアカウント JWT を openssl で署名し、Google Sheets API を直接呼ぶ。
LLM コンテキストを経由しないためトークンゼロで動作する。
"""

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import requests

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
RANGE = "X投稿一覧!B:B"
OUTPUT_PATH = "/tmp/x_analytics_b_col.json"
SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"


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


def main():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not raw:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_KEY が未設定", file=sys.stderr)
        sys.exit(1)
    key_data = json.loads(raw)

    print("STEP 1: アクセストークン取得中...", file=sys.stderr)
    token = get_access_token(key_data)

    print(f"STEP 2: Sheets B列取得中... ({RANGE})", file=sys.stderr)
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{RANGE}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    values = data.get("values", [])
    print(f"  取得行数: {len(values)} 行", file=sys.stderr)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(values, f, ensure_ascii=False)
    print(f"✅ {OUTPUT_PATH} に保存しました（{len(values)}行）")


if __name__ == "__main__":
    main()
