#!/usr/bin/env python3
"""
X投稿の記録を Google Sheets の outputs シートに追記する。
Usage:
  python3 record_output.py <url> <how_id> [--neta-id NETA_ID] [--thought-id THOUGHT_ID]
Example:
  python3 record_output.py https://x.com/i/web/status/123 W003
  python3 record_output.py https://x.com/i/web/status/123 z01 --neta-id "noteNeta[33]"
  python3 record_output.py https://x.com/i/web/status/123 z01 --thought-id T007

outputs 列: 日時(A) | URL(B) | what_id(C) | neta_id(D) | thought_id(E) | note_url(F) | img-pattern_id(G)
"""

import argparse
import json
import os
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


def record(url: str, how_id: str, neta_id: str = "", thought_id: str = ""):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 列順: 日時(A), URL(B), what_id(C), neta_id(D), thought_id(E)
    row = [dt, url, how_id]
    if neta_id or thought_id:
        row.append(neta_id)        # D列（thought のときは空文字）
    if thought_id:
        row.append(thought_id)     # E列
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    sheet.append_row(row, value_input_option="USER_ENTERED")
    print(f"✓ 記録完了: {row}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X投稿を outputs シートに記録する")
    parser.add_argument("url", help="ツイート URL")
    parser.add_argument("how_id", help="what_id（例: W003 / z01）")
    parser.add_argument("--neta-id", default="", help="neta_id 列の値（例: noteNeta[33]）")
    parser.add_argument("--thought-id", default="", help="thought_id 列の値（例: T007）")
    args = parser.parse_args()
    record(args.url, args.how_id, args.neta_id, args.thought_id)
