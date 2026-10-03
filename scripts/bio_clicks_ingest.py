#!/usr/bin/env python3
"""
転送サイト（Caddy）のアクセスログから、経路別の bio クリック数を日次で集計し、
「発信記録」スプレッドシートの `bioクリック` シートに upsert する。

列: 日付 / X bio / Threads bio / X 固定 / bot除外 / 合計（列は redirect/redirects.json の column 順）
対象: 各ホストの `/`（index.html）への 2xx リクエスト。bot・リンクプレビュー取得は UA で除外して別カウント。

使い方:
  python3 scripts/bio_clicks_ingest.py              # 前日（JST）を集計して書き込み（cron 用）
  python3 scripts/bio_clicks_ingest.py --date 2026-10-05
  python3 scripts/bio_clicks_ingest.py --days 7     # 直近7日分を再集計（ログのローテーション範囲内）
  python3 scripts/bio_clicks_ingest.py --dry-run

認証: Sheets はサービスアカウント（sheets_values.py と同じ）
"""

import argparse
import glob
import gzip
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from sheets_values import get_client, open_with_retry  # noqa: E402

CONF = REPO_ROOT / "redirect" / "redirects.json"
LOG_DIR = Path("/var/log/caddy")
SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
SHEET_NAME = "bioクリック"
JST = timezone(timedelta(hours=9))

# リンクプレビュー・クローラ。X/Threads/Slack/LINE 等がリンクを貼った瞬間に取りに来る分を人のクリックから除く
BOT_UA = re.compile(
    r"bot|crawler|spider|preview|fetch|facebookexternalhit|Twitterbot|Slackbot|Discordbot|LinkedInBot|"
    r"WhatsApp|TelegramBot|Applebot|Googlebot|bingbot|YandexBot|DuckDuckBot|Baiduspider|"
    r"line-poker|Line/|curl|wget|python-requests|Go-http-client|HeadlessChrome|Lighthouse",
    re.I,
)


def iter_log_lines(host: str):
    for path in sorted(glob.glob(str(LOG_DIR / f"{host}.log*"))):
        opener = gzip.open if path.endswith(".gz") else open
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    yield line
        except OSError:
            continue


def count_day(host: str, day: str) -> tuple[int, int]:
    """(人のクリック数, bot 除外数) を返す。day は 'YYYY-MM-DD'（JST）"""
    human = bot = 0
    for line in iter_log_lines(host):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = e.get("ts")
        if ts is None:
            continue
        d = datetime.fromtimestamp(float(ts), tz=timezone.utc).astimezone(JST).strftime("%Y-%m-%d")
        if d != day:
            continue
        req = e.get("request", {})
        uri = req.get("uri", "")
        status = e.get("status", 0)
        if not (200 <= int(status) < 300) or uri.split("?")[0] not in ("/", "/index.html"):
            continue
        ua = " ".join(req.get("headers", {}).get("User-Agent", []) or [])
        if BOT_UA.search(ua):
            bot += 1
        else:
            human += 1
    return human, bot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="集計日 YYYY-MM-DD（JST）。既定は前日")
    ap.add_argument("--days", type=int, default=1, help="--date から遡って何日分を集計するか")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conf = json.loads(CONF.read_text(encoding="utf-8"))
    hosts = conf["hosts"]  # 挿入順を列順として使う
    columns = [h["column"] for h in hosts.values()]
    header = ["日付"] + columns + ["bot除外", "合計"]

    end = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else (datetime.now(JST).date() - timedelta(days=1))
    days = [(end - timedelta(days=i)).isoformat() for i in range(args.days)][::-1]

    rows = []
    for day in days:
        counts, bots = [], 0
        for host in hosts:
            h, b = count_day(host, day)
            counts.append(h); bots += b
        rows.append([day] + counts + [bots, sum(counts)])

    for r in rows:
        print(" | ".join(f"{k}={v}" for k, v in zip(header, r)))
    if args.dry_run:
        return 0

    ss = open_with_retry(get_client(), SPREADSHEET_ID)
    try:
        ws = ss.worksheet(SHEET_NAME)
    except Exception:
        ws = ss.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(header) + 2)
    ws.update(values=[header], range_name=f"A1:{chr(64 + len(header))}1", value_input_option="USER_ENTERED")
    existing = {str(r[0]).strip()[:10]: i + 2 for i, r in enumerate(ws.get(f"A2:A{ws.row_count}") or []) if r and r[0]}
    updates, appends = [], []
    for r in rows:
        if r[0] in existing:
            updates.append({"range": f"{SHEET_NAME}!A{existing[r[0]]}:{chr(64 + len(header))}{existing[r[0]]}", "values": [r]})
        else:
            appends.append(r)
    if updates:
        ss.values_batch_update({"valueInputOption": "USER_ENTERED", "data": updates})
    if appends:
        ss.values_append(f"{SHEET_NAME}!A:{chr(64 + len(header))}",
                         params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
                         body={"values": appends})
    print(f"✅ {SHEET_NAME}: 更新 {len(updates)} 行 / 追加 {len(appends)} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
