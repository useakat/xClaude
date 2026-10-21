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
  python3 scripts/note_article_daily.py --prices-only    # 価格の更新だけ
  python3 scripts/note_article_daily.py --date 2026-10-03 --from 2026-09-14 --max-days 20  # 遡って埋める（バックフィル）
  python3 scripts/note_article_daily.py --init-price-history [--dry-run]  # note価格履歴 の初期行を購入記録から推定して作る

あわせて note投稿一覧 の N列「価格」を note の公開 API（/api/v3/notes/<key>、0 ＝ 無料）で毎日更新する
（2026-10-12）。ダッシュボード更新 routine の実行環境からは note.com に届かない（プロキシ 403）ので、
価格はこのローカル cron でシートに持たせ、note_funnel_export.py はシートから読む。

価格が変わったら `note価格履歴`（記事ID, タイトル, 価格, 開始日, 終了日, 出典）に区間として残す（2026-10-21）。
終了日が空の行がその記事の現在価格。無料化（0）も 1 区間。記事ごと・価格ごとの CVR（CVR¥）の分母・分子を
この区間で切るために使う（note_funnel_export.py の article_price_cvr.csv）。

依存: scripts/fetch_note_stats.py（NOTE_SESSION を .env から読む）、scripts/sheets_values.py（サービスアカウント）
cron: 毎朝 05:55 JST（run_note_article_daily.sh）。bio クリック集計（05:40）の後、
      ダッシュボード更新 routine（06:30）の前。
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import sheets_values as sv  # noqa: E402

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
SHEET_NAME = "note記事日次"
DETAIL_SHEET = "転送クリック明細"
POSTS_SHEET = "note投稿一覧"
PRICE_COL = 14           # N列「価格」
PRICE_HEADER = "価格"
HEADER = ["日付", "記事ID", "タイトル", "PV", "スキ", "取得日時"]
PRICE_HIST_SHEET = "note価格履歴"
PRICE_HIST_HEADER = ["記事ID", "タイトル", "価格", "開始日", "終了日", "出典"]
BUY_SHEET = "note購入記録"
FETCH = SCRIPT_DIR / "fetch_note_stats.py"
MAX_FETCH_DAYS = 10  # 1回の実行で取りに行く日数の上限（1日あたり数秒〜1 分）
FETCH_INTERVAL_SEC = 3  # 日と日の間の待ち（バックフィルで連続取得すると note が非 JSON を返して拒否する。2026-10-21）
JST = timezone(timedelta(hours=9))


def log(msg: str) -> None:
    print(f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}", flush=True)


def fetch_day(day: str) -> list[dict]:
    """その日の全記事の {id, name, view, like} を返す。
    GraphQL はその日に PV も表示も無かった記事を返さない。その記事は fetch_note_stats が REST の累計を
    view/like に入れて gql=False を付けるので、ここでは 0 として書く（累計を日別に混ぜない。2026-10-21。
    それまでは WARN 行の先頭 5 件だけを除外していたため、6 件目以降の累計値が日別に混入していた）"""
    for attempt, wait in enumerate((0, 30, 90, 180)):  # note 側が一時的に非 JSON を返す（連続取得で拒否）ことがあるので待って再試行
        if wait:
            log(f"  {day}: 取得に失敗。{wait} 秒待って再試行（{attempt}/3）")
            time.sleep(wait)
        r = subprocess.run(
            [sys.executable, str(FETCH), "--all", "--no-charcount", "--period", f"{day}:{day}"],
            capture_output=True, text=True, timeout=600,
        )
        if r.returncode == 0:
            break
    if r.returncode != 0:
        raise RuntimeError(f"fetch_note_stats 失敗: {r.stderr.strip()[-300:]}")
    rows = []
    n_gql = 0
    for x in json.loads(r.stdout):
        aid = x["url"].rstrip("/").split("/")[-1]
        ok = x.get("gql", True)
        n_gql += 1 if ok else 0
        rows.append({"id": aid, "name": x.get("name", ""),
                     "view": int(x.get("view") or 0) if ok else 0, "like": int(x.get("like") or 0) if ok else 0})
    if rows and n_gql == 0:
        raise RuntimeError(f"{day}: ダッシュボードの記事別データが 1 件も取れない（全件 REST 累計）。書き込まない")
    return rows


def fetch_price(key: str) -> int | None:
    """note の公開 API から記事の価格（円）。0 ＝ 無料（有料部分なし）。取れなければ None"""
    import urllib.request
    try:
        req = urllib.request.Request(f"https://note.com/api/v3/notes/{key}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            price = (json.load(r).get("data") or {}).get("price")
        return price if isinstance(price, int) else None
    except Exception as e:  # noqa: BLE001
        log(f"  ⚠ 価格の取得に失敗 {key}: {e}")
        return None


def update_prices(ss, dry_run: bool) -> None:
    """note投稿一覧 の各記事の価格を N列に書く（変わった記事・空の記事だけ更新）"""
    ws = ss.worksheet(POSTS_SHEET)
    values = ws.get_all_values()
    if not values:
        return
    header_ok = len(values[0]) >= PRICE_COL and values[0][PRICE_COL - 1] == PRICE_HEADER
    updates = []
    if not header_ok:
        updates.append({"range": f"{chr(64 + PRICE_COL)}1", "values": [[PRICE_HEADER]]})
    changed = 0
    changes: list[dict] = []  # 価格履歴に残す変更
    for i, r in enumerate(values[1:], start=2):
        url = r[1] if len(r) > 1 else ""
        m = re.search(r"/n/(n[0-9a-f]{10,16})", url)
        if not m:
            continue
        cur = (r[PRICE_COL - 1] if len(r) >= PRICE_COL else "").strip()
        price = fetch_price(m.group(1))
        if price is None or cur == str(price):
            continue
        updates.append({"range": f"{chr(64 + PRICE_COL)}{i}", "values": [[price]]})
        changed += 1
        changes.append({"id": m.group(1), "title": r[2] if len(r) > 2 else "", "old": cur, "new": price,
                        "published": (r[0] if r else "")[:10]})
    if dry_run:
        log(f"dry-run: 価格の更新 {changed} 件（書き込まない）" + "".join(f"\n    {c['id']} {c['old'] or '（空）'} → {c['new']}" for c in changes))
        return
    if updates:
        ws.batch_update(updates, value_input_option="RAW")
    log(f"✅ {POSTS_SHEET} 価格: {changed} 件更新")
    if changes:
        try:
            record_price_changes(ss, changes)
        except Exception as e:  # noqa: BLE001
            log(f"⚠ {PRICE_HIST_SHEET} の更新に失敗（価格の更新自体は済み）: {e}")


def _hist_ws(ss, create: bool):
    try:
        return ss.worksheet(PRICE_HIST_SHEET)
    except Exception:  # noqa: BLE001  (WorksheetNotFound)
        if not create:
            return None
        ws = ss.add_worksheet(title=PRICE_HIST_SHEET, rows=200, cols=len(PRICE_HIST_HEADER) + 2)
        ws.update(range_name="A1", values=[PRICE_HIST_HEADER], value_input_option="RAW")
        return ws


def record_price_changes(ss, changes: list[dict]) -> None:
    """価格が変わった記事について、note価格履歴 の開いている行（終了日が空）を前日で閉じ、新しい区間を足す。
    履歴に無い記事（初回）は 開始日 ＝ 公開日 で 1 行だけ足す"""
    ws = _hist_ws(ss, create=True)
    values = ws.get_all_values()
    today = datetime.now(JST).date()
    yesterday = (today - timedelta(days=1)).isoformat()
    updates, appends = [], []
    for c in changes:
        open_rows = [i for i, r in enumerate(values[1:], start=2) if r and r[0] == c["id"] and (len(r) < 5 or not r[4].strip())]
        if open_rows:
            for i in open_rows:
                updates.append({"range": f"E{i}", "values": [[yesterday]]})
            appends.append([c["id"], c["title"], c["new"], today.isoformat(), "", "API"])
            log(f"  {PRICE_HIST_SHEET}: {c['id']} {c['old']} → {c['new']}（{today.isoformat()}〜）")
        else:
            appends.append([c["id"], c["title"], c["new"], c["published"] or today.isoformat(), "", "API（初回）"])
            log(f"  {PRICE_HIST_SHEET}: {c['id']} 初回 {c['new']}（{c['published'] or today.isoformat()}〜）")
    if updates:
        ws.batch_update(updates, value_input_option="RAW")
    if appends:
        ws.append_rows(appends, value_input_option="RAW")


def _parse_date(s: str):
    s = (s or "").strip().replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:19] if " " in s else s[:10], fmt).date()
        except ValueError:
            continue
    return None


def init_price_history(ss, dry_run: bool) -> int:
    """note価格履歴 を note購入記録（購入時の価格）と note投稿一覧（現在価格・公開日）から推定して作る。
    すでに行があるシートには何もしない。
    区間の切り方：購入記録を日付順に並べ、価格が変わった最初の購入日を新区間の開始日とする（実際の変更日は
    前の価格の最後の購入日の翌日〜その日の間。出典列に幅を書く）。現在価格が最後の購入価格と違えば、
    最後の購入日の翌日を開始日の推定値にする。購入の無い記事は現在価格 1 区間（開始日 ＝ 公開日）"""
    ws = _hist_ws(ss, create=False)
    if ws is not None and len([r for r in ws.get_all_values()[1:] if r and r[0]]) > 0:
        log(f"{PRICE_HIST_SHEET} に既に行があるので初期化しない")
        return 0
    posts = ss.worksheet(POSTS_SHEET).get_all_values()
    articles = {}
    for r in posts[1:]:
        m = re.search(r"/n/(n[0-9a-f]{10,16})", r[1] if len(r) > 1 else "")
        if not m:
            continue
        articles[m.group(1)] = {"title": r[2] if len(r) > 2 else "", "published": _parse_date(r[0] if r else ""),
                                "price": (r[PRICE_COL - 1] if len(r) >= PRICE_COL else "").strip()}
    title_to_id = {a["title"]: aid for aid, a in articles.items() if a["title"]}
    buys: dict[str, list] = {}
    for r in ss.worksheet(BUY_SHEET).get_all_values()[1:]:
        t = (r[4] if len(r) > 4 else "").strip()
        d = _parse_date(r[0] if r else "")
        price = (r[5] if len(r) > 5 else "").strip()
        if not t or not d or not price.isdigit():
            continue
        aid = (title_to_id.get(t)
               or next((i for ttl, i in title_to_id.items() if len(t) >= 8 and ttl.startswith(t)), "")
               or next((i for ttl, i in title_to_id.items() if ttl[:15] == t[:15]), ""))
        if aid:
            buys.setdefault(aid, []).append((d, int(price)))
    rows = []
    for aid, a in articles.items():
        if not a["price"].isdigit():
            continue
        cur = int(a["price"])
        pub = a["published"]
        segs = []  # [価格, 開始日, 出典]
        last_d = None
        for d, p in sorted(buys.get(aid, [])):
            if not segs:
                segs.append([p, pub or d, "購入記録（公開日から）"])
            elif p != segs[-1][0]:
                lo = min(last_d + timedelta(days=1), d)
                segs.append([p, d, f"購入記録から推定（変更は {lo.isoformat()}〜{d.isoformat()} の間）"])
            last_d = d
        if not segs:
            segs.append([cur, pub, "投稿一覧（現在価格・購入なし）"])
        elif segs[-1][0] != cur:
            segs.append([cur, last_d + timedelta(days=1), f"投稿一覧から推定（{(last_d + timedelta(days=1)).isoformat()} 以降に変更）"])
        for i, (p, start, src) in enumerate(segs):
            end = (segs[i + 1][1] - timedelta(days=1)).isoformat() if i + 1 < len(segs) and segs[i + 1][1] else ""
            rows.append([aid, a["title"], p, start.isoformat() if start else "", end, src])
    rows.sort(key=lambda r: (r[1], r[3]))
    for r in rows:
        log(f"  {r[0]} {r[1][:14]} ¥{r[2]} {r[3]}〜{r[4] or ''}  {r[5]}")
    if dry_run:
        log(f"dry-run: {PRICE_HIST_SHEET} に {len(rows)} 行（書き込まない）")
        return 0
    ws = _hist_ws(ss, create=True)
    ws.append_rows(rows, value_input_option="RAW")
    log(f"✅ {PRICE_HIST_SHEET}: {len(rows)} 行を作成")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="対象日 YYYY-MM-DD（JST）。既定は前日")
    ap.add_argument("--days", type=int, default=1, help="--date から遡って何日分か")
    ap.add_argument("--fill-detail", action="store_true", help="転送クリック明細にある未取得の日付も対象に加える")
    ap.add_argument("--force", action="store_true", help="取得済みの日付も取り直す")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prices-only", action="store_true", help="note投稿一覧 の価格だけ更新する")
    ap.add_argument("--from", dest="from_date", help="--date からこの日まで遡る（バックフィル用。--days より優先）")
    ap.add_argument("--max-days", type=int, default=MAX_FETCH_DAYS, help=f"1 回で取りに行く日数の上限（既定 {MAX_FETCH_DAYS}）")
    ap.add_argument("--init-price-history", action="store_true", help="note価格履歴 を購入記録から推定して作る（既に行があれば何もしない）")
    args = ap.parse_args()

    end = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else (datetime.now(JST).date() - timedelta(days=1))
    if args.from_date:
        start = datetime.strptime(args.from_date, "%Y-%m-%d").date()
        targets = {(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)}
    else:
        targets = {(end - timedelta(days=i)).isoformat() for i in range(args.days)}

    client = sv.get_client()
    ss = sv.open_with_retry(client, SPREADSHEET_ID)
    if args.init_price_history:
        return init_price_history(ss, args.dry_run)
    try:
        update_prices(ss, args.dry_run)
    except Exception as e:  # noqa: BLE001
        log(f"⚠ 価格の更新に失敗（日次の取得は続行）: {e}")
    if args.prices_only:
        return 0
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
    targets = sorted(d for d in targets if d < today)[:args.max_days] if args.from_date else sorted(d for d in targets if d < today)[-args.max_days:]
    if not targets:
        log("取得対象の日付なし（すべて取得済み）")
        return 0
    log(f"取得対象: {', '.join(targets)}")

    fetched_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    new_rows: dict[str, list[list]] = {}
    for i, day in enumerate(targets):
        if i:
            time.sleep(FETCH_INTERVAL_SEC)  # 連続取得で note に拒否されないよう間を空ける
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
