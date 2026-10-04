#!/usr/bin/env python3
"""
X の固定ポストを毎日確認し、変わっていたら「発信記録」の `固定ポスト履歴` シートに記録する。

固定ポストの note リンクは通常のセルフリプと同じ xpost.usephys.net/<記事ID>/<投稿キー>（投稿キー＝元ポストの
tweet ID）のままにし、「いつ・どの投稿が固定だったか」をこのシートで管理する。転送クリック明細のキー
<記事ID>/<投稿ID> と突き合わせれば固定ポストの日別クリックが分かる（2026-10-04）。

列: 開始日 / 終了日 / 媒体 / 投稿URL / 投稿ID / 記事ID / 投稿キー / メモ
  - X の行はこのスクリプトが自動で書く（固定が変わった日に前の行へ終了日を入れ、新しい行を追加）
  - Threads は API に固定情報が無いので、固定を変えたときに手で1行書く（媒体 = Threads）

使い方:
  python3 scripts/record_pinned_post.py            # 確認して必要なら記録（cron 用）
  python3 scripts/record_pinned_post.py --dry-run  # シートに書かない

認証: X は .env の X_BEARER_TOKEN（1日1回のユーザー取得のみ）、Sheets はサービスアカウント（sheets_values.py と同じ）
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from sheets_values import get_client, open_with_retry  # noqa: E402

load_dotenv(REPO_ROOT / ".env")

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
SHEET_NAME = "固定ポスト履歴"
POSTS_SHEET = "X投稿一覧"
USER_ID = "548606471"  # @usephys
HEADER = ["開始日", "終了日", "媒体", "投稿URL", "投稿ID", "記事ID", "投稿キー", "メモ"]
JST = timezone(timedelta(hours=9))

XPOST_RE = re.compile(r"xpost\.usephys\.net/(n[0-9a-f]{10,16})/([A-Za-z0-9_-]{1,32})")
NOTE_RE = re.compile(r"note\.com/takaesu7431/n/(n[0-9a-f]{10,16})")


def fetch_pinned_id(token: str) -> str:
    r = requests.get(f"https://api.x.com/2/users/{USER_ID}",
                     headers={"Authorization": f"Bearer {token}"},
                     params={"user.fields": "pinned_tweet_id"}, timeout=30)
    r.raise_for_status()
    return str((r.json().get("data") or {}).get("pinned_tweet_id") or "")


def find_link(ss, tweet_id: str) -> tuple[str, str, str]:
    """X投稿一覧から固定ポスト本文（優先）かそのセルフリプの note リンクを探し (記事ID, 投稿キー, メモ) を返す"""
    vals = ss.worksheet(POSTS_SHEET).get_all_values()
    h = vals[0]
    i_url, i_parent, i_note = h.index("ポストURL"), h.index("親ポストURL"), h.index("noteURL")
    cands = []
    for r in vals[1:]:
        if len(r) <= i_note or not r[i_note].strip():
            continue
        if tweet_id in (r[i_url] or ""):
            cands.append((0, r[i_note].strip()))
        elif tweet_id in (r[i_parent] or ""):
            cands.append((1, r[i_note].strip()))
    if not cands:
        return "", "", "X投稿一覧に note リンクが見つからない"
    cands.sort()
    url = cands[0][1].split("\n")[0]
    m = XPOST_RE.search(url)
    if m:
        return m.group(1), m.group(2), ""
    m = NOTE_RE.search(url)
    if m:
        return m.group(1), "", "生 note リンク（xpost 導入前）"
    return "", "", f"不明なリンク: {url}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        print("X_BEARER_TOKEN が未設定（.env を確認）", file=sys.stderr)
        return 1
    pinned = fetch_pinned_id(token)
    today = datetime.now(JST).date().isoformat()

    ss = open_with_retry(get_client(), SPREADSHEET_ID)
    try:
        ws = ss.worksheet(SHEET_NAME)
    except Exception:
        ws = None
    vals = ws.get_all_values() if ws else []
    first = len(vals) <= 1

    open_row = None  # (行番号, 投稿ID) — 媒体が X で終了日が空の行
    for i, r in enumerate(vals[1:], start=2):
        if len(r) >= 5 and r[2].strip() == "X" and not r[1].strip():
            open_row = (i, r[4].strip())

    if open_row and open_row[1] == pinned:
        print(f"変更なし: 固定ポスト {pinned}")
        return 0

    actions = []
    if open_row:
        actions.append(f"固定解除を記録: {open_row[1]}（終了日 {today}）")
    new_row = None
    if pinned:
        art, key, memo = find_link(ss, pinned)
        if first:
            memo = (memo + "；" if memo else "") + "初期登録（実際の固定開始日は不明）"
        new_row = [today, "", "X", f"https://x.com/usephys/status/{pinned}", pinned, art, key, memo]
        actions.append(f"固定ポストを記録: {pinned} 記事ID={art or '-'} 投稿キー={key or '-'} {memo}")
    else:
        actions.append("固定ポストなし")
    for a in actions:
        print(a)
    if args.dry_run:
        return 0

    if ws is None:
        ws = ss.add_worksheet(title=SHEET_NAME, rows=200, cols=len(HEADER) + 2)
        ws.update(values=[HEADER], range_name="A1:H1", value_input_option="RAW")
    if open_row:
        ws.update_cell(open_row[0], 2, today)
    if new_row:
        # 投稿ID は 19 桁。USER_ENTERED だと数値化されて末尾が丸まるので RAW で文字列のまま書く
        ws.append_row(new_row, value_input_option="RAW")
    print("✅ 固定ポスト履歴 を更新しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
