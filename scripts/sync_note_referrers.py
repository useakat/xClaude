#!/usr/bin/env python3
"""note の流入元（日別）を「発信記録」スプレッドシートの `note流入元` シートへ同期する。

新ダッシュボードの流入元グラフと同じデータを 1行=1日 の形で記録する。
主要ドメインは固定列、それ以外は「その他」に合算する（note 側の "other" バケットも含む）。
ドメイン単位の完全な内訳が要るときは fetch_note_referrers.py を直接使う。

Usage:
  python3 sync_note_referrers.py                 # 直近7日を upsert（cron 想定）
  python3 sync_note_referrers.py --period 28d
  python3 sync_note_referrers.py --full          # 取得可能な全期間を再構築
  python3 sync_note_referrers.py --period 2026-09-01:2026-09-30
  python3 sync_note_referrers.py --dry-run       # シートに書かず内容だけ表示

認証: Sheets はサービスアカウント（GOOGLE_SERVICE_ACCOUNT_KEY / gcp の鍵）、
      note は .env の NOTE_SESSION。
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_note_referrers import fetch  # noqa: E402
from sheets_values import get_client, open_with_retry  # noqa: E402

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録（SS3）
SHEET_NAME = "note流入元"

# データが存在する最初の日（これより前は空）
FIRST_DATE = "2025-08-31"

# (列見出し, まとめる流入元名) — ここに無いものはすべて「その他」へ
COLUMN_MAP = [
    ("X", ["X"]),
    ("Google", ["Google"]),
    ("note.com", ["note.com"]),
    ("直接・不明", ["no referrer"]),
    ("Yahoo", ["search.yahoo.co.jp"]),
    ("Bing", ["www.bing.com"]),
]
HEADER = ["日付", "合計"] + [c[0] for c in COLUMN_MAP] + ["その他"]
LAST_COL = chr(ord("A") + len(HEADER) - 1)  # 現状 I


def to_row(day):
    """fetch() の daily 1件を 1行の配列に変換する。"""
    refs = dict(day["referrers"])
    cells, used = [], set()
    for _, names in COLUMN_MAP:
        v = sum(refs.get(n, 0) for n in names)
        used.update(names)
        cells.append(v)
    other = sum(v for k, v in refs.items() if k not in used)
    return [day["date"], day["total"]] + cells + [other]


def get_sheet(client):
    ss = open_with_retry(client, SPREADSHEET_ID)
    try:
        return ss, ss.worksheet(SHEET_NAME)
    except Exception:
        ws = ss.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(HEADER) + 2)
        ws.update(values=[HEADER], range_name=f"A1:{LAST_COL}1",
                  value_input_option="USER_ENTERED")
        print(f"シート「{SHEET_NAME}」を新規作成しました", file=sys.stderr)
        return ss, ws


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--period", default="7d",
                    help="7d / 28d / 365d / YYYY-MM-DD / YYYY-MM-DD:YYYY-MM-DD（既定 7d）")
    ap.add_argument("--full", action="store_true",
                    help=f"{FIRST_DATE} から今日までを対象にする")
    ap.add_argument("--dry-run", action="store_true", help="シートに書き込まない")
    args = ap.parse_args()

    if args.full:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()
        period = f"{FIRST_DATE}:{today}"
    else:
        period = args.period

    result = fetch(period, include_daily=True)
    days = [d for d in result["daily"] if d["date"]]
    if not days:
        print("日別データが取得できませんでした（期間が長すぎて粒度が日でない可能性）",
              file=sys.stderr)
        sys.exit(1)

    rows = [to_row(d) for d in days]

    if args.dry_run:
        print("\t".join(HEADER))
        for r in rows:
            print("\t".join(str(c) for c in r))
        print(f"\n({len(rows)}日分 / {result['startDate']}〜{result['endDate']} / "
              f"集計時刻 {result['lastUpdatedAt']})", file=sys.stderr)
        return

    ss, ws = get_sheet(get_client())

    existing = ws.get(f"A2:A{ws.row_count}") or []
    date_to_row = {}
    for i, r in enumerate(existing):
        if r and r[0]:
            date_to_row[str(r[0]).strip()[:10]] = i + 2  # ヘッダ分 +2

    updates, appends = [], []
    for row in rows:
        r = date_to_row.get(row[0])
        if r:
            updates.append({"range": f"{SHEET_NAME}!A{r}:{LAST_COL}{r}", "values": [row]})
        else:
            appends.append(row)

    if updates:
        ss.values_batch_update({
            "valueInputOption": "USER_ENTERED",
            "data": updates,
        })
    if appends:
        appends.sort(key=lambda r: r[0])
        ss.values_append(
            f"{SHEET_NAME}!A:{LAST_COL}",
            params={"valueInputOption": "USER_ENTERED",
                    "insertDataOption": "INSERT_ROWS"},
            body={"values": appends},
        )

    print(json.dumps({
        "period": f"{result['startDate']}〜{result['endDate']}",
        "lastUpdatedAt": result["lastUpdatedAt"],
        "updated": len(updates),
        "appended": len(appends),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
