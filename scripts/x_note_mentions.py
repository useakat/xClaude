#!/usr/bin/env python3
"""
他人が自分の note 記事の URL を貼った X 投稿を集計する。

目的: note流入元シートの「X」列には、自分のセルフリプ経由だけでなく、
      他人が本文に note の URL を貼った投稿からの流入も混ざる。
      その規模を把握し、「X列合計 − 自分の投稿のリンククリック」の残差
      （＝プロフ＋固定ポスト＋他人の投稿からの流入）の内訳を切り分ける。
      ただし他人の投稿のクリック数は X から取れない（自分の投稿のみ）。
      ここで集めるのは投稿の本数と IMP で、流入は IMP × 想定CTR の推定にとどまる。

使い方:
  python3 scripts/x_note_mentions.py                   # 直近7日を検索して CSV に追記（週次 cron 用）
  python3 scripts/x_note_mentions.py --dry-run         # 検索結果を表示するだけ（CSV に書かない）
  python3 scripts/x_note_mentions.py --reconcile 2026-09   # 月次の突合表を表示

出力: logs/x_note_mentions.csv（tweet_id で重複除去。列は CSV_HEADER 参照）
ログ: logs/x_note_mentions.log

課金: X API は従量課金。他人の投稿は $0.005/件（返ってきた投稿ごと）。
      `-is:retweet` で自分のセルフリプのリポストを除外しないと、その分まで課金される。
      検索 API（recent）は直近7日分なので、週1回の実行で取りこぼしなく拾える。

認証: X は .env の X_BEARER_TOKEN、Sheets はサービスアカウント（sheets_values.py と同じ）
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(Path(__file__).parent))

USERNAME = "usephys"                 # 自分の X アカウント
NOTE_CREATOR = "takaesu7431"         # note のクリエイターID（URL の note.com/<ここ>/n/...）
QUERY = f'url:"note.com/{NOTE_CREATOR}" -from:{USERNAME} -is:retweet'
MAX_RESULTS = 100

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
SHEET_REFERRERS = "note流入元"       # A=日付, C=X, D=Threads, G=直接・不明
SHEET_POSTS = "X投稿一覧"            # A=投稿日時, AB=リンククリック, AI=noteURL（本文中の note リンク）

CSV_PATH = REPO_ROOT / "logs" / "x_note_mentions.csv"
LOG_PATH = REPO_ROOT / "logs" / "x_note_mentions.log"
CSV_HEADER = ["fetched_at", "tweet_id", "created_at_jst", "username", "impressions",
              "likes", "retweets", "quotes", "url", "text"]

JST = timezone(timedelta(hours=9))


def log(msg: str) -> None:
    line = f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── 検索（週次） ─────────────────────────────────────

def search_mentions(token: str) -> list[dict]:
    url = "https://api.x.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "query": QUERY,
        "max_results": MAX_RESULTS,
        "tweet.fields": "created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "username",
    }
    results, users, next_token = [], {}, None
    while True:
        if next_token:
            params["next_token"] = next_token
        r = requests.get(url, headers=headers, params=params, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"X API エラー {r.status_code}: {r.text[:200]}")
        j = r.json()
        results += j.get("data", [])
        for u in j.get("includes", {}).get("users", []):
            users[u["id"]] = u["username"]
        next_token = j.get("meta", {}).get("next_token")
        if not next_token:
            break
    for t in results:
        t["username"] = users.get(t["author_id"], "")
    return results


def load_known_ids() -> set[str]:
    if not CSV_PATH.exists():
        return set()
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return {row["tweet_id"] for row in csv.DictReader(f)}


def append_rows(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists()
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if new_file:
            w.writeheader()
        for row in rows:
            w.writerow(row)


def to_row(t: dict, fetched_at: str) -> dict:
    pm = t["public_metrics"]
    created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")).astimezone(JST)
    return {
        "fetched_at": fetched_at,
        "tweet_id": t["id"],
        "created_at_jst": created.strftime("%Y-%m-%d %H:%M:%S"),
        "username": t["username"],
        "impressions": pm.get("impression_count", 0),
        "likes": pm.get("like_count", 0),
        "retweets": pm.get("retweet_count", 0),
        "quotes": pm.get("quote_count", 0),
        "url": f"https://x.com/{t['username']}/status/{t['id']}",
        "text": t.get("text", "").replace("\n", " ")[:200],
    }


def run_fetch(dry_run: bool) -> int:
    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        log("ERROR: X_BEARER_TOKEN が未設定（.env を確認）")
        return 1
    try:
        found = search_mentions(token)
    except Exception as e:  # noqa: BLE001
        log(f"ERROR: {e}")
        return 1
    fetched_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    known = load_known_ids()
    rows = [to_row(t, fetched_at) for t in found if t["id"] not in known]
    if dry_run:
        log(f"[dry-run] 検索ヒット {len(found)} 件 / 新規 {len(rows)} 件（課金目安: {len(found)} × $0.005）")
        for r in rows:
            log(f"[dry-run] {r['created_at_jst']} @{r['username']} IMP{r['impressions']} {r['url']} | {r['text'][:60]}")
        return 0
    if rows:
        append_rows(rows)
    log(f"完了: 検索ヒット {len(found)} 件 / 新規追記 {len(rows)} 件 → {CSV_PATH.name}")
    return 0


# ── 突合（月次） ─────────────────────────────────────

def _to_int(v) -> int:
    try:
        return int(str(v).replace(",", "").strip() or 0)
    except ValueError:
        return 0


def run_reconcile(month: str, ctr: float) -> int:
    """month = 'YYYY-MM'。note流入元の X 列・自分の note 導線クリック・他人の note リンク投稿を並べる。

    他人の投稿のクリック数は X から取れないため、本数と IMP を示し、流入は IMP × ctr で推定する。
    """
    from sheets_values import get_client, open_with_retry  # noqa: E402

    ss = open_with_retry(get_client(), SPREADSHEET_ID)

    # note流入元: X 列（C）の月間合計
    ref_rows = ss.worksheet(SHEET_REFERRERS).get_all_values()
    x_inflow = sum(_to_int(r[2]) for r in ref_rows[1:] if len(r) > 2 and r[0].startswith(month))
    ref_days = sum(1 for r in ref_rows[1:] if r and r[0].startswith(month))

    # 自分の note 導線クリック: X投稿一覧で AI 列「noteURL」が空でない行（本文に note.com の
    #   リンクを含む投稿・セルフリプ。GAS が entities から記録）の「リンククリック」(AB) を、
    #   投稿日時（A）が当月の行で合計する。outputs の note_url 記録に依存しないので手動リプの漏れが無い。
    post_rows = ss.worksheet(SHEET_POSTS).get_all_values()
    ym = month.replace("-", "/")
    own_clicks = 0
    own_posts = 0
    for r in post_rows[1:]:
        if len(r) >= 35 and r[0].startswith(ym) and r[34].strip():
            own_posts += 1
            own_clicks += _to_int(r[27])

    # 他人のリンク投稿（CSV）
    mentions = []
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8", newline="") as f:
            mentions = [m for m in csv.DictReader(f) if m["created_at_jst"].startswith(month)]
    mention_imp = sum(_to_int(m["impressions"]) for m in mentions)

    residual = x_inflow - own_clicks
    est_inflow = round(mention_imp * ctr)
    # 直接・不明（G列=index6）と Threads（D列=index3）。アプリ内ブラウザで参照元が落ちた分が「直接・不明」に入るため、
    # X / Threads からの流入は「列の値 〜 列の値＋直接・不明」の範囲で読む（直接・不明は両者で共有＝上限は重複）
    # 列順: A日付 B合計 C X D Threads E Google F note.com G 直接・不明 H Yahoo I Bing J その他
    direct = sum(_to_int(r[6]) for r in ref_rows[1:] if len(r) > 6 and r[0].startswith(month))
    threads = sum(_to_int(r[3]) for r in ref_rows[1:] if len(r) > 3 and r[0].startswith(month))
    print(f"\n== note への X 経由流入の突合（{month}）==")
    print(f"note流入元 X列 合計（note が数えた X からの流入）: {x_inflow:>6} 件（{ref_days}日分）")
    print(f"  X 経由の流入（範囲）     : {x_inflow} 〜 {x_inflow + direct} 件（＝X列 〜 X列＋直接・不明 {direct}）")
    print(f"  Threads 経由の流入（範囲）: {threads} 〜 {threads + direct} 件（＝Threads列 〜 Threads列＋直接・不明。直接・不明は X と共有）")
    print(f"自分の note リンク投稿のクリック合計              : {own_clicks:>6} 件（noteURL 列あり {own_posts} 行。X アナリティクス CSV の取込後に有効）")
    print(f"残差（プロフ＋固定ポスト＋他人の投稿からの流入）  : {residual:>6} 件")
    print(f"他人の note リンク投稿                           : {len(mentions):>6} 本 / IMP 合計 {mention_imp:,}")
    print(f"  └ その投稿からの流入は X からは取れない。推定 ≈ IMP × 想定CTR {ctr:.2%} = {est_inflow} 件（--ctr で変更可）")
    if mentions:
        print("  内訳:")
        for m in sorted(mentions, key=lambda m: -_to_int(m["impressions"]))[:10]:
            print(f"   {m['created_at_jst'][:10]} @{m['username']} IMP{_to_int(m['impressions']):,} {m['url']}")
    if own_clicks == 0:
        print("  ※ リンククリックが 0 です。当月の X アナリティクス CSV が未取込の可能性があります")
    print("  ※ X のクリック数と note の X 列は同じものではない（アプリ内ブラウザ等で参照元が落ちる）。"
          "2026-07 は note X列 ÷ X クリック ≒ 0.76。残差は目安として読む")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="検索結果を表示するだけ（CSV に書かない）")
    ap.add_argument("--reconcile", metavar="YYYY-MM", help="月次の突合表を表示する")
    ap.add_argument("--ctr", type=float, default=0.005,
                    help="他人の投稿からの流入を推定する想定CTR（既定 0.005 = 0.5%%。自分のセルフリプの実績 0.54%% に合わせた）")
    args = ap.parse_args()
    if args.reconcile:
        return run_reconcile(args.reconcile, args.ctr)
    return run_fetch(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
