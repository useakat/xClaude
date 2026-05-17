#!/usr/bin/env python3
"""
/tmp/x_analytics_map.json（csv_map）と
/tmp/x_analytics_b_col.json（Sheets B列）を読み込み、
status ID でマッチングして sheets_batch_update_values 用の
update_data JSON を stdout に出力する。
"""

import json
import re
import sys

CSV_MAP_PATH = "/tmp/x_analytics_map.json"
B_COL_PATH   = "/tmp/x_analytics_b_col.json"
SHEET_NAME   = "X投稿一覧"


def main():
    # csv_map 読み込み
    with open(CSV_MAP_PATH) as f:
        data = json.load(f)
    csv_map    = data["csv_map"]
    file_title = data["file"]

    # B列データ読み込み（[[url], [url], ...] 形式）
    with open(B_COL_PATH) as f:
        b_col = json.load(f)

    # マッチング
    update_data = []
    for i, row in enumerate(b_col[1:], start=2):  # 1行目はヘッダー
        url = row[0] if row else ""
        m = re.search(r"/status/(\d+)", url)
        if m and m.group(1) in csv_map:
            v = csv_map[m.group(1)]
            update_data.append({
                "range":  f"{SHEET_NAME}!AA{i}:AC{i}",
                "values": [[v["detail_expands"], v["url_clicks"], v["new_follows"]]],
            })

    result = {
        "file":        file_title,
        "match_count": len(update_data),
        "total_csv":   len(csv_map),
        "update_data": update_data,
    }
    print(json.dumps(result, ensure_ascii=False))
    print(f"マッチ件数: {len(update_data)} / CSV総投稿数: {len(csv_map)}", file=sys.stderr)


if __name__ == "__main__":
    main()
