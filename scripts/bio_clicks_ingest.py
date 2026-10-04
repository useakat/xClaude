#!/usr/bin/env python3
"""
転送サイト（Caddy）のアクセスログから、経路別の bio クリック数を日次で集計し、
「発信記録」スプレッドシートの `bioクリック` シートに upsert する。

列: 日付 / X bio / Threads bio / X 固定 / Threads 固定 / 除外(bot・スキャナ) / 合計 / うち参照元がX/Threads
    （経路列は redirect/redirects.json の column 順）
対象: 各ホストの `/`（index.html）への 2xx リクエストのうち、実ブラウザと判定できるもの
    （UA が bot でない・Accept-Language あり・Accept が text/html・Sec-Fetch-Dest が document）。
    証明書発行直後から来るスキャナはブラウザ風 UA でも Accept-Language を送らないので除外される。

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


REFERRER_HOSTS = re.compile(r"(^|\.)(t\.co|x\.com|twitter\.com|threads\.(net|com)|l\.threads\.com|instagram\.com)$", re.I)


def is_human(headers: dict) -> bool:
    """ブラウザからの人のアクセスか。
    新しい証明書が透明性ログに載った直後からスキャナが大量に来る（UA はブラウザ風だが
    Accept-Language や Sec-Fetch-* を送らない）ため、UA の bot 判定だけでは足りない。
    実ブラウザが必ず送るヘッダの有無で判定する。"""
    h = {k.lower(): " ".join(v) if isinstance(v, list) else str(v) for k, v in headers.items()}
    ua = h.get("user-agent", "")
    if not ua or BOT_UA.search(ua) or "mozilla" not in ua.lower():
        return False
    if "accept-language" not in h:
        return False
    if "text/html" not in h.get("accept", "") and "*/*" not in h.get("accept", ""):
        return False
    if "sec-fetch-dest" in h and h["sec-fetch-dest"] != "document":
        return False
    if "sec-fetch-mode" in h and h["sec-fetch-mode"] != "navigate":
        return False
    return True


def count_day(host: str, day: str) -> tuple[dict[str, int], int, int]:
    """(キー別の人のクリック数, 除外数, うち参照元が X/Threads のもの) を返す。day は 'YYYY-MM-DD'（JST）

    人のクリック ＝ 転送ページの JS が送るビーコン `/hit?k=<key>`（204）の件数。キー無しのページは `_root`。
    スキャナは JS を実行しないのでページ取得（`/`）は多くても `/hit` には来ない。
    除外数 ＝ ページ取得のうち bot・スキャナ判定の件数（参考）。
    参照元が X/Threads ＝ ページ取得に t.co / threads 等の Referer が付いていた件数（参考。
    X アプリ内ブラウザは Referer を付けないことがあるので、人のクリックの下限にすぎない）。
    """
    by_key: dict[str, int] = {}
    excluded = with_ref = 0
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
        path, _, query = uri.partition("?")
        status = int(e.get("status", 0))
        headers = req.get("headers", {}) or {}
        ua = " ".join(headers.get("User-Agent", []) or [])
        if path == "/hit" and 200 <= status < 300:
            if BOT_UA.search(ua):
                excluded += 1
            else:
                key = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("k", "_root") or "_root"
                by_key[key] = by_key.get(key, 0) + 1
            continue
        if 200 <= status < 300 and (path in ("/", "/index.html") or path.endswith("/") or path.count("/") == 1):
            if not is_human(headers):
                excluded += 1
            ref = " ".join(headers.get("Referer", []) or [])
            ref_host = ref.split("/")[2] if ref.startswith("http") and ref.count("/") >= 2 else ""
            if ref_host and REFERRER_HOSTS.search(ref_host):
                with_ref += 1
    return by_key, excluded, with_ref


DETAIL_SHEET = "転送クリック明細"


def write_detail(ss, days: list[str], detail: list[list]) -> None:
    """キー別の明細を upsert する。対象日の既存行は削除して書き直す（キーの増減に追従）。"""
    header = ["日付", "ホスト", "キー", "クリック"]
    try:
        ws = ss.worksheet(DETAIL_SHEET)
    except Exception:
        ws = ss.add_worksheet(title=DETAIL_SHEET, rows=2000, cols=6)
    ws.update(values=[header], range_name="A1:D1", value_input_option="USER_ENTERED")
    existing = ws.get_all_values()[1:]
    kept = [r for r in existing if r and r[0][:10] not in days]
    new = kept + [[str(c) for c in d] for d in detail]
    new.sort(key=lambda r: (r[0], r[1], r[2]))
    ws.batch_clear([f"A2:D{max(len(existing) + 1, 2)}"])
    if new:
        ws.update(values=new, range_name=f"A2:D{len(new) + 1}", value_input_option="USER_ENTERED")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="集計日 YYYY-MM-DD（JST）。既定は前日")
    ap.add_argument("--days", type=int, default=1, help="--date から遡って何日分を集計するか")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conf = json.loads(CONF.read_text(encoding="utf-8"))
    hosts = conf["hosts"]  # 挿入順を列順として使う
    columns = [h["column"] for h in hosts.values()]
    header = ["日付"] + columns + ["除外(bot・スキャナ)", "合計", "うち参照元がX/Threads"]

    end = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else (datetime.now(JST).date() - timedelta(days=1))
    days = [(end - timedelta(days=i)).isoformat() for i in range(args.days)][::-1]

    rows = []
    detail = []  # 転送クリック明細: 日付 / ホスト / キー / クリック
    for day in days:
        counts, excluded, refs = [], 0, 0
        for host in hosts:
            by_key, x, r = count_day(host, day)
            counts.append(sum(by_key.values())); excluded += x; refs += r
            for key, n in sorted(by_key.items()):
                detail.append([day, host, key, n])
        rows.append([day] + counts + [excluded, sum(counts), refs])

    for r in rows:
        print(" | ".join(f"{k}={v}" for k, v in zip(header, r)))
    for d in detail:
        print(f"   明細: {d[0]} {d[1]} /{d[2]} = {d[3]}")
    if args.dry_run:
        return 0

    ss = open_with_retry(get_client(), SPREADSHEET_ID)
    write_detail(ss, days, detail)
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
