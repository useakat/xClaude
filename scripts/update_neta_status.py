#!/usr/bin/env python3
"""
Update neta status in CSV files.
Usage: python3 update_neta_status.py <neta_type> <no> <status>
Example: python3 update_neta_status.py one-point 5 使用済み
"""

import csv
import sys
from pathlib import Path

def update_neta_status(neta_type, no, status):
    """Update the status of a neta in the CSV file."""

    # Map neta type to CSV file
    csv_map = {
        "one-point": "database/onePointNeta.csv",
        "note": "database/noteNeta.csv",
        "news": "database/newsTopics.csv",
    }

    if neta_type not in csv_map:
        print(f"❌ 不明なネタ型: {neta_type}")
        sys.exit(1)

    csv_path = Path(csv_map[neta_type])

    if not csv_path.exists():
        print(f"❌ ファイルが見つかりません: {csv_path}")
        sys.exit(1)

    try:
        no = int(no)
    except ValueError:
        print(f"❌ No番号は整数で指定してください: {no}")
        sys.exit(1)

    # Read CSV
    rows = []
    fieldnames = None
    found = False

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if int(row["No"]) == no:
                row["ステータス"] = status
                found = True
            rows.append(row)

    if not found:
        print(f"❌ ネタNo.{no} が見つかりません")
        sys.exit(1)

    # Write CSV
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ ネタNo.{no} のステータスを「{status}」に更新しました")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用方法: python3 update_neta_status.py <neta_type> <no> <status>")
        print("例: python3 update_neta_status.py one-point 5 使用済み")
        sys.exit(1)

    neta_type = sys.argv[1]
    no = sys.argv[2]
    status = sys.argv[3]

    update_neta_status(neta_type, no, status)
