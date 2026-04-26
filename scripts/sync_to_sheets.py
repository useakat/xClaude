#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "gspread",
#   "google-auth-oauthlib",
# ]
# ///
"""database/ CSV → Google Sheets への同期スクリプト."""

import csv
import json
import os
import sys
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
DB_DIR = Path(__file__).parent.parent / "database"

# スプレッドシートごとの同期マップ: {spreadsheet_id: {csv_filename: sheet_name}}
SYNC_CONFIG = {
    "1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM": {
        "onePointNeta.csv": "onePointNeta",
        "noteNeta.csv": "noteNeta",
        "newsTopics.csv": "newsTopics",
    },
    "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc": {
        "persona.csv": "persona",
        "pain.csv": "pain",
        "what.csv": "what",
    },
}


def get_client():
    json_content = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
    if json_content:
        creds = Credentials.from_service_account_info(json.loads(json_content), scopes=SCOPES)
        return gspread.authorize(creds)

    creds_path = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        str(Path(__file__).parent.parent / "gcp" / "charming-well-464402-u4-a7fefbac9372.json"),
    )
    if not os.path.exists(creds_path):
        print("エラー: 認証情報が見つかりません。", file=sys.stderr)
        print("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT 環境変数か GCPファイルを設定してください。", file=sys.stderr)
        sys.exit(1)
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def sync_csv_to_sheet(ws, csv_path: Path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    ws.clear()
    if rows:
        ws.update(rows)
    return len(rows) - 1  # ヘッダー除く件数


def main():
    client = get_client()

    for ss_id, sheet_map in SYNC_CONFIG.items():
        ss = client.open_by_key(ss_id)
        for filename, sheet_name in sheet_map.items():
            csv_path = DB_DIR / filename
            if not csv_path.exists():
                print(f"スキップ: {filename} が見つかりません")
                continue
            try:
                try:
                    ws = ss.worksheet(sheet_name)
                except gspread.WorksheetNotFound:
                    ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=20)
                count = sync_csv_to_sheet(ws, csv_path)
                print(f"✓ {sheet_name}: {count}件 同期完了")
            except Exception as e:
                print(f"✗ {sheet_name}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
