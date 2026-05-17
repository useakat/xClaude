#!/usr/bin/env python3
"""
/tmp/x_analytics_b64.txt（Drive MCP から取得した base64 CSV）を読み込み、
パースして /tmp/x_analytics_map.json に保存する。

エージェントが Drive MCP で CSV をダウンロードし、base64 文字列を
Write ツールで /tmp/x_analytics_b64.txt に保存した後に実行する。
"""

import base64
import csv
import io
import json
import re
import sys

B64_PATH   = "/tmp/x_analytics_b64.txt"
OUTPUT_PATH = "/tmp/x_analytics_map.json"


def main():
    with open(B64_PATH) as f:
        b64 = f.read().strip()

    try:
        csv_text = base64.b64decode(b64).decode("utf-8")
    except Exception as e:
        print(f"ERROR: base64 デコード失敗: {e}", file=sys.stderr)
        sys.exit(1)

    csv_map = {}
    file_title = B64_PATH  # フォールバック

    reader = csv.reader(io.StringIO(csv_text))
    next(reader)  # ヘッダースキップ
    for row in reader:
        if len(row) <= 14:
            continue
        m = re.search(r"/status/(\d+)", row[3])
        if not m:
            continue
        try:
            csv_map[m.group(1)] = {
                "detail_expands": int(row[13] or 0),
                "url_clicks":     int(row[14] or 0),
                "new_follows":    int(row[9]  or 0),
            }
        except (ValueError, IndexError):
            continue

    print(f"  CSV 投稿数: {len(csv_map)} 件", file=sys.stderr)

    output = {"file": file_title, "csv_map": csv_map}
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"✅ {OUTPUT_PATH} に保存しました（{len(csv_map)}件）")


if __name__ == "__main__":
    main()
