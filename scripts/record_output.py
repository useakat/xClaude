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
import re
import socket
from datetime import datetime

# IPv6 が通らない環境向けに DNS を IPv4 固定する。
# googleapis.com が AAAA（IPv6）優先で解決されると gspread の接続がハングするため
# （threads 系スクリプトと同じ対策）。
_orig_gai = socket.getaddrinfo
socket.getaddrinfo = lambda *a, **k: [r for r in _orig_gai(*a, **k) if r[0] == socket.AF_INET] or _orig_gai(*a, **k)

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"
SHEET_NAME = "outputs"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SA_FILE = os.path.join(os.path.dirname(__file__), "..", "gcp", "charming-well-464402-u4-2cfb7bddf343.json")

# z01（X短文投稿）専用: SS1 側で「短文最終使用日」列を持つシートと列位置
SS1_SPREADSHEET_ID = "1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM"
SHORT_POST_DATE_COLUMN = {"noteNeta": "N", "newsTopics": "I"}


def get_client():
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if key_json:
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(os.path.abspath(SA_FILE), scopes=SCOPES)
    return gspread.authorize(creds)


def record_short_post_usage(client, neta_id: str):
    """z01 の実投稿成功時、SS1 の該当ネタ行の短文最終使用日を更新する。"""
    m = re.match(r"^(noteNeta|newsTopics)\[(\d+)\]$", neta_id)
    if not m:
        return
    sheet_name, no = m.group(1), m.group(2)
    column = SHORT_POST_DATE_COLUMN[sheet_name]
    sheet = client.open_by_key(SS1_SPREADSHEET_ID).worksheet(sheet_name)
    no_column = sheet.col_values(1)  # A列
    if no not in no_column:
        print(f"⚠ 短文最終使用日の更新スキップ: {sheet_name}[{no}] の行が見つかりません")
        return
    row_index = no_column.index(no) + 1  # gspread は 1-indexed
    today = datetime.now().strftime("%Y-%m-%d")
    sheet.update_acell(f"{column}{row_index}", today)
    print(f"✓ 短文最終使用日を更新: {sheet_name}[{no}] → {column}{row_index} = {today}")


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

    if how_id == "z01" and neta_id:
        record_short_post_usage(client, neta_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X投稿を outputs シートに記録する")
    parser.add_argument("url", help="ツイート URL")
    parser.add_argument("how_id", help="what_id（例: W003 / z01）")
    parser.add_argument("--neta-id", default="", help="neta_id 列の値（例: noteNeta[33]）")
    parser.add_argument("--thought-id", default="", help="thought_id 列の値（例: T007）")
    args = parser.parse_args()
    record(args.url, args.how_id, args.neta_id, args.thought_id)
