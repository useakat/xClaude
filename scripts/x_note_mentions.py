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

    # note流入元: 列は見出し名で引く（列の追加で位置が変わるため。sync_note_referrers.py の COLUMN_MAP 参照）
    ref_rows = ss.worksheet(SHEET_REFERRERS).get_all_values()
    hdr = {name: i for i, name in enumerate(ref_rows[0])}
    def col(name):
        return hdr.get(name)
    x_inflow = sum(_to_int(r[col("X")]) for r in ref_rows[1:] if len(r) > col("X") and r[0].startswith(month))
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

    est_inflow = round(mention_imp * ctr)
    def msum(name):
        idx = col(name)
        if idx is None:
            return 0
        return sum(_to_int(r[idx]) for r in ref_rows[1:] if len(r) > idx and r[0].startswith(month))
    threads, note_internal, direct = msum("Threads"), msum("note.com"), msum("直接・不明")
    bio_cols = [(n, msum(n)) for n in ("X bio", "Threads bio", "X 固定", "Threads 固定", "Threads 投稿") if col(n) is not None]
    visible = x_inflow + note_internal + threads
    # 推定内訳: 直接・不明（参照元が落ちた流入）を X : note : Threads の見えている比で配分する。
    # 前提は「参照元が落ちた流入は、見えている流入と同じ比率で3経路に分布している」の1点のみ。
    # 検索（Google 等）は参照元が落ちないので配分対象にしない。ベース分の差し引きや X の上限は置かない
    # （bio リンク・他人の投稿経由が X列に含まれる一方 X クリック数には含まれないため、クリック数で上限を切れない）。
    def alloc(v):
        return round(direct * v / visible) if visible else 0
    print(f"\n== note への X 経由流入の突合（{month}）==")
    print(f"生の数字（{ref_days}日分）: X列 {x_inflow} / note列 {note_internal} / Threads列 {threads} / 直接・不明 {direct}"
          + "".join(f" / {n} {v}" for n, v in bio_cols))
    print("推定内訳（直接・不明を X:note:Threads の見えている比で配分。前提: 参照元が落ちた流入は見えている流入と同じ比率で分布）")
    print(f"  X 経由      : {x_inflow + alloc(x_inflow):>6}（= {x_inflow} + {alloc(x_inflow)}）")
    print(f"  note 経由   : {note_internal + alloc(note_internal):>6}（= {note_internal} + {alloc(note_internal)}）")
    print(f"  Threads 経由: {threads + alloc(threads):>6}（= {threads} + {alloc(threads)}）")
    print(f"参考: 自分の note リンク投稿の X クリック {own_clicks:,} 件（noteURL 列あり {own_posts} 行。bio リンク・他人の投稿経由は含まない。X アナリティクス CSV の取込後に有効）")
    print(f"他人の note リンク投稿: {len(mentions)} 本 / IMP 合計 {mention_imp:,}"
          f"（その投稿からの流入は X からは取れない。推定 ≈ IMP × 想定CTR {ctr:.2%} = {est_inflow} 件、--ctr で変更可）")
    if mentions:
        print("  内訳:")
        for m in sorted(mentions, key=lambda m: -_to_int(m["impressions"]))[:10]:
            print(f"   {m['created_at_jst'][:10]} @{m['username']} IMP{_to_int(m['impressions']):,} {m['url']}")
    if own_clicks == 0:
        print("  ※ リンククリックが 0 です。当月の X アナリティクス CSV が未取込の可能性があります")

    # 投稿単位の突合: note リンク投稿を投稿日でまとめ、投稿日＋翌日の note（X列＋直接・不明）と比べる
    ref_by_day = {r[0][:10]: (_to_int(r[col("X")]), _to_int(r[col("直接・不明")]))
                  for r in ref_rows[1:] if r and r[0] and len(r) > max(col("X"), col("直接・不明"))}
    by_day: dict[str, list] = {}
    for r in post_rows[1:]:
        if len(r) >= 35 and r[0].startswith(ym) and r[34].strip() and len(r) > 27:
            d = r[0][:10].replace("/", "-")
            e = by_day.setdefault(d, [0, 0, r[2][:14].replace("\n", " ")])
            e[0] += _to_int(r[27]); e[1] += 1
    if by_day:
        print("\n  投稿単位（投稿日 | X クリック(本数) | note X+直接・不明[当日+翌日] | 比 | 投稿冒頭）")
        for d in sorted(by_day):
            clicks, n, head = by_day[d]
            dt = datetime.strptime(d, "%Y-%m-%d")
            nx = sum(sum(ref_by_day.get((dt + timedelta(i)).strftime("%Y-%m-%d"), (0, 0))) for i in range(2))
            ratio = f"{nx / clicks:.2f}" if clicks else "-"
            print(f"   {d} | {clicks}({n}) | {nx} | {ratio} | {head}")
        print("   ※ 同じ日に複数投稿があると note 側は合算。前日の投稿の流入が翌日に重なると比が大きく出る")

    print("  ※ 読み方: X クリック数は推定には使わず参考値。X列には bio リンク・他人の投稿経由が含まれ、"
          "クリック数には含まれないので、両者は同じものを測っていない。投稿単位の比（note X+直接 ÷ クリック）は "
          "2026-02〜07 が 0.26〜0.77、2026-08 以降が 0.7〜1.3 で、古い月ほど note 側の捕捉が不完全"
          "（note流入元は 9月導入の新ダッシュボードから遡って取得）。推定 X 経由がクリック数を大きく下回る月は、"
          "bio・他人経由の過大見積もりではなく note 側の捕捉不足を疑う。2026-03 は X 側 CSV に返信が無く検証不能")
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
