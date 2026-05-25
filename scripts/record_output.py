#!/usr/bin/env python3
"""
X投稿の記録を Google Sheets の outputs シートに追記する。
Usage: python3 record_output.py <url> <how_id> [neta_id]
Example: python3 record_output.py https://x.com/i/web/status/123 W003 onePointNeta[3]
"""

import json
import os
import sys
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"
SHEET_NAME = "outputs"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SA_FILE = os.path.join(os.path.dirname(__file__), "..", "gcp", "charming-well-464402-u4-2cfb7bddf343.json")


def get_client():
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if key_json:
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(os.path.abspath(SA_FILE), scopes=SCOPES)
    return gspread.authorize(creds)


def record(url: str, how_id: str, neta_id: str = ""):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    sheet.append_row([dt, url, how_id, neta_id], value_input_option="USER_ENTERED")
    print(f"✓ 記録完了: {dt}, {url}, {how_id}, {neta_id}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python3 record_output.py <url> <how_id> [neta_id]")
        sys.exit(1)
    record(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else "")
