#!/usr/bin/env python3
"""
X アナリティクス CSV と Sheets B列のマッチングを行い、
Sheets batch_update_values 用の update_data を stdout に出力する。

入力:
  /tmp/x_analytics_map.json  - fetch_x_analytics_csv.py の出力
  /tmp/x_analytics_b_col.json - fetch_x_b_col.py の出力

出力 (stdout):
  {
    "match_count": int,
    "total_csv": int,
    "csv_file": str,
    "update_data": [
      {"range": "X投稿一覧!AA<row>:AC<row>", "values": [[detail_expands, url_clicks, new_follows]]},
      ...
    ]
  }
"""

import json
import re
import sys

CSV_MAP_PATH = "/tmp/x_analytics_map.json"
B_COL_PATH   = "/tmp/x_analytics_b_col.json"
SHEET_NAME   = "X投稿一覧"


def extract_tweet_id(url: str) -> str | None:
    """URL からツイート ID を抽出する。"""
    if not url:
        return None
    m = re.search(r"/status/(\d+)", url)
    return m.group(1) if m else None


def main():
    # 入力ファイル読み込み
    try:
        csv_data = json.load(open(CSV_MAP_PATH))
    except FileNotFoundError:
        print(f"ERROR: {CSV_MAP_PATH} が見つかりません。fetch_x_analytics_csv.py を先に実行してください。", file=sys.stderr)
        sys.exit(1)

    try:
        b_col = json.load(open(B_COL_PATH))
    except FileNotFoundError:
        print(f"ERROR: {B_COL_PATH} が見つかりません。fetch_x_b_col.py を先に実行してください。", file=sys.stderr)
        sys.exit(1)

    csv_map  = csv_data["csv_map"]
    csv_file = csv_data.get("file", "unknown")

    print(f"CSV 投稿数: {len(csv_map)} 件", file=sys.stderr)
    print(f"Sheets B列 行数: {len(b_col)} 行", file=sys.stderr)

    # マッチング: B列の各行を走査して CSV map と照合
    update_data = []
    matched_ids = set()

    for row_idx, cell in enumerate(b_col):
        # row_idx 0 → Sheet 行 1（ヘッダー行など）
        sheet_row = row_idx + 1

        # B列の値（空セルはリストが空または要素なし）
        url = cell[0] if cell else ""
        tweet_id = extract_tweet_id(url)
        if not tweet_id:
            continue

        if tweet_id in csv_map:
            stats = csv_map[tweet_id]
            detail_expands = stats.get("detail_expands", 0)
            url_clicks     = stats.get("url_clicks", 0)
            new_follows    = stats.get("new_follows", 0)

            range_str = f"{SHEET_NAME}!AA{sheet_row}:AC{sheet_row}"
            update_data.append({
                "range":  range_str,
                "values": [[detail_expands, url_clicks, new_follows]],
            })
            matched_ids.add(tweet_id)

    match_count = len(matched_ids)
    unmatched   = len(csv_map) - match_count

    print(f"マッチ件数: {match_count} / {len(csv_map)}（未マッチ: {unmatched}）", file=sys.stderr)

    result = {
        "match_count": match_count,
        "total_csv":   len(csv_map),
        "csv_file":    csv_file,
        "update_data": update_data,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
