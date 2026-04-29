#!/usr/bin/env python3
"""
Read neta from CSV files in database/.
Usage: python3 csv_reader.py list <neta_type> [--unused-only] [--full]
Example: python3 csv_reader.py list one-point --unused-only --full
"""

import csv
import sys
from pathlib import Path

CSV_MAP = {
    "one-point": "database/onePointNeta.csv",
    "note": "database/noteNeta.csv",
    "news": "database/newsTopics.csv",
}

def list_neta(neta_type, unused_only=False, full=False):
    csv_path = Path(CSV_MAP.get(neta_type, ""))

    if not csv_path or not csv_path.exists():
        print(f"❌ ファイルが見つかりません: {csv_path}")
        sys.exit(1)

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if unused_only and row.get("ステータス") != "未使用":
                continue
            rows.append(row)

    if not rows:
        print("未使用のネタはありません。")
        return

    for row in rows:
        if full:
            print(f"No.{row['No']} 【{row['テーマ']}】 難易度:{row['難易度']} ステータス:{row['ステータス']}")
            print(f"  冒頭1行案   : {row['冒頭1行案']}")
            print(f"  身近さ接続  : {row['身近さ接続']}")
            print(f"  仕組みのポイント: {row['仕組みのポイント']}")
            print(f"  感情的締め案: {row['感情的締め案']}")
            print()
        else:
            print(f"No.{row['No']} 【{row['テーマ']}】 難易度:{row['難易度']} ステータス:{row['ステータス']}")

if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) < 2 or args[0] != "list":
        print("使用方法: python3 csv_reader.py list <neta_type> [--unused-only] [--full]")
        print("例: python3 csv_reader.py list one-point --unused-only --full")
        sys.exit(1)

    neta_type = args[1]
    unused_only = "--unused-only" in args
    full = "--full" in args

    if neta_type not in CSV_MAP:
        print(f"❌ 不明なネタ型: {neta_type}（使用可能: {', '.join(CSV_MAP.keys())}）")
        sys.exit(1)

    list_neta(neta_type, unused_only=unused_only, full=full)
