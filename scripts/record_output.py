#!/usr/bin/env python3
"""
X投稿の記録を database/outputs.csv に追記する。
Usage: python3 record_output.py <url> <how_id>
Example: python3 record_output.py https://x.com/i/web/status/123 W003
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "database" / "outputs.csv"


def record(url: str, how_id: str):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([dt, url, how_id])
    print(f"✓ 記録完了: {dt}, {url}, {how_id}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 record_output.py <url> <how_id>")
        sys.exit(1)
    record(sys.argv[1], sys.argv[2])
