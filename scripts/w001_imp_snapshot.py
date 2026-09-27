#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W001 投稿の累積インプレッションを日次でスナップショット記録する（H4 検証用）。

X投稿一覧のインプ列は毎日更新されるが累積値しか残らないため、
投稿から8日間の伸び（尾）を後から追えない。このスクリプトを毎日実行して
logs/w001_imp_daily.csv に「記録日, tweet_id, 投稿日, 累積IMP」を追記し、
日次差分から「W001 は翌日以降もインプを引くか（H4）」を検証可能にする。

呼び出し元: reporter-daily（毎日 21:00 JST の日報 routine）STEP 10.5

- Sheets 読み取りは scripts/sheets_values.py（サービスアカウント認証）経由。
  リモート routine でも動く（mcp-gsheets 不要）
- 対象: outputs シートで what_id=W001 の X 投稿のうち、投稿から9日以内のもの
  （インプ更新が最大8日分のため。9日目を最後の記録とする）
- 同じ (記録日, tweet_id) の行が既にあれば追記しない（再実行しても安全）
"""

import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SHEETS_CLI = os.path.join(SCRIPT_DIR, "sheets_values.py")
CSV_PATH = os.path.join(REPO_ROOT, "logs", "w001_imp_daily.csv")

SS2 = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"  # outputs
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # X投稿一覧
JST = timezone(timedelta(hours=9))
MAX_AGE_DAYS = 9


def sheets_get(spreadsheet_id, rng):
    out = subprocess.run(
        [sys.executable, SHEETS_CLI, "get", spreadsheet_id, rng],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout).get("values", [])


def tweet_id(url):
    m = re.search(r"/status(?:es)?/(\d+)", url or "")
    return m.group(1) if m else None


def main():
    today = datetime.now(JST).date()

    # outputs から W001 の X 投稿（tweet_id → 投稿日）を集める
    outputs = sheets_get(SS2, "outputs!A:C")
    w001 = {}
    for row in outputs[1:]:
        row = row + [""] * (3 - len(row))
        if row[2].strip() != "W001":
            continue
        tid = tweet_id(row[1])
        if not tid:
            continue
        try:
            post_date = datetime.strptime(row[0][:10].replace("/", "-"), "%Y-%m-%d").date()
        except ValueError:
            continue
        w001[tid] = post_date

    targets = {t: d for t, d in w001.items() if 0 <= (today - d).days <= MAX_AGE_DAYS}
    if not targets:
        print("対象なし（投稿9日以内の W001 が無い）")
        return

    # X投稿一覧から現在の累積IMPを取得（B: URL / K: インプ）
    xrows = sheets_get(SS3, "X投稿一覧!B:K")
    imp_map = {}
    for row in xrows[1:]:
        row = row + [""] * (10 - len(row))
        tid = tweet_id(row[0])
        if tid in targets:
            imp = str(row[9]).replace(",", "").strip()
            if imp.isdigit():
                imp_map[tid] = int(imp)

    # 既存行を読んで (記録日, tweet_id) の重複追記を防ぐ
    existing = set()
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 2:
                    existing.add((row[0], row[1]))

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    new_file = not os.path.exists(CSV_PATH)
    added = 0
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["記録日", "tweet_id", "投稿日", "累積IMP"])
        for tid, post_date in sorted(targets.items(), key=lambda kv: kv[1]):
            if (str(today), tid) in existing:
                continue
            if tid not in imp_map:
                print(f"  IMP未取得のためスキップ: {tid}（投稿日 {post_date}）")
                continue
            w.writerow([today, tid, post_date, imp_map[tid]])
            added += 1

    print(f"✅ W001 日次IMPスナップショット: {added}件追記（対象 {len(targets)}本） → {os.path.relpath(CSV_PATH, REPO_ROOT)}")


if __name__ == "__main__":
    main()
