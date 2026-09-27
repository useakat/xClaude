#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X アナリティクス CSV（Drive の Xanalytics/tmp）を取り込み、
X投稿一覧シートの AA:AC（詳細表示・リンククリック・フォロー増）を更新する。

update-x-analytics エージェント（mcp-gsheets 書き込み・手動実行）の週次無人版。
リモート routine から Bash 一発で完結する：

  python3 scripts/update_x_analytics_weekly.py [--max-age-days N] [--dry-run]

- Drive 検索・CSV ダウンロードは fetch_x_analytics_csv.py の関数を再利用
  （Drive MCP プロキシ直叩き。base64 を LLM コンテキストに乗せない）
- Sheets の読み書きは scripts/sheets_values.py（サービスアカウント認証）
- 最新 CSV の modifiedTime が --max-age-days（既定7日）より古い場合は
  何も書かずに exit code 2 で終了する（routine 側がリマインドメールを送る）
- 書き込みは AA2:AC(最終行) を「既存値に CSV マッチ分を上書きした全体ブロック」
  として1回で update する（マッチしない行の既存値は保持される）

exit code: 0=更新完了 / 2=新しい CSV なし / 1=エラー
"""

import argparse
import base64
import csv
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from fetch_x_analytics_csv import DRIVE_UUID, FOLDER_ID, drive_call  # noqa: E402


def get_drive_config():
    """Drive MCP プロキシの URL とヘッダーを返す。

    fetch_x_analytics_csv.py 版は mcpServers のキーが UUID である前提だが、
    セッションによってはキーが名前（Google_Drive）になるため、
    UUID キー → 名前キー → URL に drivemcp を含むもの、の順で探す。
    """
    session_id = os.environ["CLAUDE_CODE_REMOTE_SESSION_ID"]
    config = json.load(open(f"/tmp/mcp-config-{session_id}.json"))
    servers = config["mcpServers"]
    drive = servers.get(DRIVE_UUID) or servers.get("Google_Drive")
    if drive is None:
        drive = next((v for v in servers.values()
                      if "drivemcp" in v.get("url", "")), None)
    if drive is None:
        raise RuntimeError("Drive MCP サーバーが mcp-config に見つかりません")
    ingress_token = open("/home/claude/.claude/remote/.session_ingress_token").read().strip()
    headers = {
        **drive.get("headers", {}),
        "Authorization": f"Bearer {ingress_token}",
        "Content-Type": "application/json",
    }
    return drive["url"], headers

SHEETS_CLI = os.path.join(SCRIPT_DIR, "sheets_values.py")
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # X投稿一覧
SHEET = "X投稿一覧"


def sheets_get(rng):
    out = subprocess.run(
        [sys.executable, SHEETS_CLI, "get", SS3, rng],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout).get("values", [])


def sheets_update(rng, values):
    out = subprocess.run(
        [sys.executable, SHEETS_CLI, "update", SS3, rng, "-"],
        input=json.dumps(values, ensure_ascii=False),
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def parse_csv(csv_text):
    """CSV → {tweet_id: {detail_expands, url_clicks, new_follows}}（fetch_x_analytics_csv.py と同じ列定義）"""
    csv_map = {}
    reader = csv.reader(io.StringIO(csv_text))
    next(reader)
    for row in reader:
        if len(row) <= 14:
            continue
        m = re.search(r"/status/(\d+)", row[3])
        if not m:
            continue
        try:
            csv_map[m.group(1)] = {
                "detail_expands": int(row[13] or 0),
                "url_clicks": int(row[14] or 0),
                "new_follows": int(row[9] or 0),
            }
        except (ValueError, IndexError):
            continue
    return csv_map


def tweet_id(url):
    m = re.search(r"/status(?:es)?/(\d+)", url or "")
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-days", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true", help="Sheets へ書き込まず件数だけ出す")
    args = ap.parse_args()

    # STEP 1: Drive の最新 CSV と鮮度チェック
    drive_url, drive_headers = get_drive_config()
    result = drive_call(drive_url, drive_headers, "search_files",
                        {"query": f"parentId = '{FOLDER_ID}'", "excludeContentSnippets": True})
    files = result.get("files", [])
    if not files:
        print("Xanalytics/tmp に CSV がありません", file=sys.stderr)
        sys.exit(2)
    latest = sorted(files, key=lambda f: f.get("modifiedTime", ""), reverse=True)[0]
    modified = latest.get("modifiedTime", "")
    try:
        mtime = datetime.fromisoformat(modified.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - mtime).days
    except ValueError:
        age_days = None
    print(f"最新CSV: {latest.get('title', latest['id'])}（更新 {modified} / {age_days}日前）", file=sys.stderr)
    if age_days is None or age_days > args.max_age_days:
        print(f"NO_FRESH_CSV: 最新CSVが {args.max_age_days}日より古いため更新しません")
        sys.exit(2)

    # STEP 2: CSV ダウンロード・パース
    dl = drive_call(drive_url, drive_headers, "download_file_content", {"fileId": latest["id"]})
    b64 = dl.get("content")
    if not b64:
        print(f"CSV コンテンツを取得できません: {str(dl)[:200]}", file=sys.stderr)
        sys.exit(1)
    csv_map = parse_csv(base64.b64decode(b64).decode("utf-8"))
    print(f"CSV 投稿数: {len(csv_map)}件", file=sys.stderr)

    # STEP 3: シートの B列（URL）と既存 AA:AC を取得してマッチ
    b_col = sheets_get(f"{SHEET}!B:B")
    aac = sheets_get(f"{SHEET}!AA:AC")
    n_rows = len(b_col)  # ヘッダー含む
    block = []  # 行2〜n_rows の AA:AC
    matched = 0
    for i in range(1, n_rows):  # 0=ヘッダー
        cur = aac[i] if i < len(aac) else []
        cur = list(cur) + [""] * (3 - len(cur))
        tid = tweet_id(b_col[i][0] if b_col[i] else "")
        if tid and tid in csv_map:
            m = csv_map[tid]
            cur = [m["detail_expands"], m["url_clicks"], m["new_follows"]]
            matched += 1
        block.append(cur[:3])

    if matched == 0:
        print("シートにマッチする投稿がありません（更新なし）")
        return

    # STEP 4: 一括書き込み（マッチしない行は既存値をそのまま書き戻す）
    if args.dry_run:
        print(f"[dry-run] マッチ {matched}件 / 書き込み範囲 {SHEET}!AA2:AC{n_rows}（書き込みは省略）")
        return
    resp = sheets_update(f"{SHEET}!AA2:AC{n_rows}", block)
    print(f"✅ X投稿一覧 アナリティクス更新完了")
    print(f"   CSVファイル: {latest.get('title', latest['id'])}")
    print(f"   マッチ件数: {matched}件 / CSV総投稿数: {len(csv_map)}件")
    print(f"   更新列: 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）")
    print(f"   API応答: {resp[:200]}")


if __name__ == "__main__":
    main()
