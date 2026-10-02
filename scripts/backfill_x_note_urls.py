#!/usr/bin/env python3
"""
X投稿一覧の AI 列「noteURL」を一回限りでバックフィルする。

本文（C列）に t.co を含む行の tweet_id を X API で引き直し（entities / note_tweet.entities の
expanded_url）、note.com を含む URL があれば AI 列に書く（複数は改行区切り）。
以後の新規行は GAS（GetMyTweets.js）が同じ列に書くので、このスクリプトは通常再実行不要。

使い方:
  python3 scripts/backfill_x_note_urls.py --dry-run   # 書き込まず対象と結果を表示
  python3 scripts/backfill_x_note_urls.py             # AI 列へ書き込み（空のセルだけ）

課金: 自分の投稿の読み取り $0.001/件。対象は t.co を含む行のみ（約290行 ≒ $0.29）。
認証: X は .env の X_BEARER_TOKEN、Sheets はサービスアカウント（sheets_values.py と同じ）
"""

import argparse
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(Path(__file__).parent))
from sheets_values import get_client, open_with_retry  # noqa: E402

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
SHEET = "X投稿一覧"
COL_URL, COL_TEXT, COL_NOTE = 2, 3, 35   # B, C, AI（1始まり）
NOTE_PATTERN = re.compile(r"https?://(?:www\.)?note\.com/\S+")


def tweet_id(url: str) -> str:
    m = re.search(r"/status/(\d+)", url or "")
    return m.group(1) if m else ""


def fetch_note_urls(token: str, ids: list[str]) -> dict[str, list[str]]:
    """tweet_id → note.com を含む展開後 URL のリスト。100件ずつ /2/tweets で引く。"""
    out: dict[str, list[str]] = {}
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        r = requests.get("https://api.x.com/2/tweets", headers=headers, timeout=60,
                         params={"ids": ",".join(chunk), "tweet.fields": "entities,note_tweet"})
        if r.status_code != 200:
            raise RuntimeError(f"X API エラー {r.status_code}: {r.text[:200]}")
        for t in r.json().get("data", []):
            urls = []
            for src in (t.get("entities") or {}, (t.get("note_tweet") or {}).get("entities") or {}):
                for u in src.get("urls", []) or []:
                    ex = u.get("expanded_url") or u.get("unwound_url") or ""
                    if NOTE_PATTERN.match(ex) and ex not in urls:
                        urls.append(ex)
            if urls:
                out[t["id"]] = urls
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        print("ERROR: X_BEARER_TOKEN が未設定（.env を確認）", file=sys.stderr)
        return 1

    ws = open_with_retry(get_client(), SPREADSHEET_ID).worksheet(SHEET)
    rows = ws.get_all_values()
    if len(rows[0]) < COL_NOTE or rows[0][COL_NOTE - 1] != "noteURL":
        print(f"ERROR: AI1 が「noteURL」ではありません（現在: {rows[0][COL_NOTE-1] if len(rows[0])>=COL_NOTE else '（列なし）'}）", file=sys.stderr)
        return 1

    targets = []  # (row_number, tweet_id)
    for i, r in enumerate(rows[1:], start=2):
        text = r[COL_TEXT - 1] if len(r) >= COL_TEXT else ""
        existing = r[COL_NOTE - 1] if len(r) >= COL_NOTE else ""
        tid = tweet_id(r[COL_URL - 1] if len(r) >= COL_URL else "")
        if "t.co/" in text and tid and not existing.strip():
            targets.append((i, tid))
    print(f"対象: {len(targets)} 行（本文に t.co あり・AI 列が空）/ 課金目安 ${len(targets) * 0.001:.2f}")

    found = fetch_note_urls(token, [t for _, t in targets])
    updates = [(row, "\n".join(found[tid])) for row, tid in targets if tid in found]
    print(f"note.com を含む投稿: {len(updates)} 行")
    for row, val in updates[:15]:
        print(f"  行{row}: {val.splitlines()[0]}")
    if len(updates) > 15:
        print(f"  … 他 {len(updates) - 15} 行")

    if args.dry_run or not updates:
        print("（dry-run: 書き込みなし）" if args.dry_run else "（書き込み対象なし）")
        return 0

    ws.batch_update([{"range": f"AI{row}", "values": [[val]]} for row, val in updates],
                    value_input_option="RAW")
    print(f"✅ AI 列に {len(updates)} 行書き込みました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
