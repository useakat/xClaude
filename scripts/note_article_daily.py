#!/usr/bin/env python3
"""
note 記事ごとの「その日の PV・スキ」を note の新ダッシュボード（GraphQL）から取り、
発信記録シートの `note記事日次` に 1日×1記事 = 1行で記録する。

note 側は期間指定で記事別の PV・スキを返すので、スナップショットを取り続けなくても
過去日を後から埋められる。クリック → 到達（note流入元）→ 記事の PV・スキ（このシート）の
日別の突き合わせに使う（note 導線ダッシュボード）。

列: 日付, 記事ID, タイトル, PV, スキ, 取得日時
  - 日付の行がすでにあれば、その日付の行を全部書き直す（--force 時）か、スキップする（既定）
  - 1日分 = 全記事分（PV・スキが 0 の記事も書く。「取得済みの日」が分かるようにするため）

使い方:
  python3 scripts/note_article_daily.py                   # 前日分（JST）
  python3 scripts/note_article_daily.py --date 2026-10-09 # 指定日
  python3 scripts/note_article_daily.py --date 2026-10-09 --days 3   # 10/7〜10/9
  python3 scripts/note_article_daily.py --fill-detail     # 転送クリック明細にある未取得の日付も埋める
  python3 scripts/note_article_daily.py --force           # 取得済みの日も取り直す
  python3 scripts/note_article_daily.py --dry-run

依存: scripts/fetch_note_stats.py（NOTE_SESSION を .env から読む）、scripts/sheets_values.py（サービスアカウント）
cron: 毎朝 05:55 JST（run_note_article_daily.sh）。bio クリック集計（05:40）の後、
      ダッシュボード更新 routine（06:30）の前。
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import sheets_values as sv  # noqa: E402

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
SHEET_NAME = "note記事日次"
DETAIL_SHEET = "転送クリック明細"
HEADER = ["日付", "記事ID", "タイトル", "PV", "スキ", "取得日時"]
FETCH = SCRIPT_DIR / "fetch_note_stats.py"
MAX_FETCH_DAYS = 10  # 1回の実行で取りに行く日数の上限（1日あたり 30〜60 秒かかる）
JST = timezone(timedelta(hours=9))


def log(msg: str) -> None:
    print(f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}", flush=True)


def fetch_day(day: str) -> list[dict]:
    """その日の全記事の {id, name, view, like} を返す。GraphQL が取れなかった記事は除く"""
    r = subprocess.run(
        [sys.executable, str(FETCH), "--all", "--no-charcount", "--period", f"{day}:{day}"],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        raise RuntimeError(f"fetch_note_stats 失敗: {r.stderr.strip()[-300:]}")
    # GraphQL が取れず REST 累計にフォールバックした記事（WARN 行に記事ID が列挙される）は
    # 「その日の値」ではないので捨てる
    fallback: set[str] = set()
    for line in r.stderr.splitlines():
        if "WARN" in line and "フォールバック" in line:
            fallback |= set(re.findall(r"n[0-9a-f]{10,16}", line))
            log(f"  {day}: {line.strip()[:160]}")
    rows = []
    for x in json.loads(r.stdout):
        aid = x["url"].rstrip("/").split("/")[-1]
        if aid in fallback:
            continue
        rows.append({"id": x["url"].rstrip("/").split("/")[-1], "name": x.get("name", ""),
                     "view": int(x.get("view") or 0), "like": int(x.get("like") or 0)})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="対象日 YYYY-MM-DD（JST）。既定は前日")
    ap.add_argument("--days", type=int, default=1, help="--date から遡って何日分か")
    ap.add_argument("--fill-detail", action="store_true", help="転送クリック明細にある未取得の日付も対象に加える")
    ap.add_argument("--force", action="store_true", help="取得済みの日付も取り直す")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    end = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else (datetime.now(JST).date() - timedelta(days=1))
    targets = {(end - timedelta(days=i)).isoformat() for i in range(args.days)}

    client = sv.get_client()
    ss = sv.open_with_retry(client, SPREADSHEET_ID)
    try:
        ws = ss.worksheet(SHEET_NAME)
        values = ws.get_all_values()
    except Exception:  # noqa: BLE001  (WorksheetNotFound)
        ws = None
        values = []
    if not values:
        values = [HEADER]
    existing_days = {r[0] for r in values[1:] if r and r[0]}

    if args.fill_detail:
        det = ss.worksheet(DETAIL_SHEET).get_all_values()
        targets |= {r[0] for r in det[1:] if r and r[0] and r[0] not in existing_days}

    if not args.force:
        targets = {d for d in targets if d not in existing_days}
    today = datetime.now(JST).date().isoformat()
    targets = sorted(d for d in targets if d < today)[-MAX_FETCH_DAYS:]
    if not targets:
        log("取得対象の日付なし（すべて取得済み）")
        return 0
    log(f"取得対象: {', '.join(targets)}")

    fetched_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    new_rows: dict[str, list[list]] = {}
    for day in targets:
        rows = fetch_day(day)
        new_rows[day] = [[day, x["id"], x["name"], x["view"], x["like"], fetched_at] for x in rows]
        nz = [x for x in rows if x["view"] or x["like"]]
        log(f"  {day}: {len(rows)} 記事（PV/スキ>0 は {len(nz)} 件: " + ", ".join(f"{x['name'][:10]} PV{x['view']}/スキ{x['like']}" for x in nz[:5]) + ("…" if len(nz) > 5 else "") + "）")

    if args.dry_run:
        log("dry-run: シートには書き込まない")
        return 0

    # 対象日の既存行を落として新しい行を足し、日付・記事ID順で全体を書き直す
    body = [r for r in values[1:] if r and r[0] not in new_rows]
    for day in new_rows:
        body += new_rows[day]
    body.sort(key=lambda r: (r[0], r[1]))
    if ws is None:
        ws = ss.add_worksheet(title=SHEET_NAME, rows=max(2000, len(body) + 100), cols=len(HEADER) + 2)
    ws.clear()
    ws.update(range_name="A1", values=[HEADER] + body, value_input_option="RAW")
    log(f"✅ {SHEET_NAME}: {len(new_rows)} 日分を書き込み（全 {len(body)} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
