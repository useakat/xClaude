#!/usr/bin/env python3
"""
X投稿の記録を Google Sheets の outputs シートに追記する。
Usage: python3 record_output.py <url> <how_id>
Example: python3 record_output.py https://x.com/i/web/status/123 W003
"""

import json
import os
import sys
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM"
SHEET_NAME = "outputs"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_client():
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_json:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_KEY が設定されていません")
    creds = Credentials.from_service_account_info(json.loads(key_json), scopes=SCOPES)
    return gspread.authorize(creds)


def record(url: str, how_id: str):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    sheet.append_row([dt, url, how_id], value_input_option="USER_ENTERED")
    print(f"✓ 記録完了: {dt}, {url}, {how_id}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 record_output.py <url> <how_id>")
        sys.exit(1)
    record(sys.argv[1], sys.argv[2])
