#!/usr/bin/env python3
"""note.com から takaesu7431 の記事一覧 + 統計を取得して JSON で出力する。

データソースは2つ:
  - REST  /api/v2/creators/.../contents, /api/v3/notes/{key}
      → タイトル・ハッシュタグ・サムネ・文字数
  - GraphQL（新ダッシュボード） https://graphql.note.com/graphql
      → ビュー(PV)・インプレッション・スキ・コメント・売上（記事別）

**数値は新ダッシュボード（GraphQL）を正とする**。REST の /api/v1/stats/pv は
旧ダッシュボードの API で、累計 read_count が GraphQL の pageViewCount と
一致しない（同一期間ならほぼ一致するが、累計では REST が 8% ほど大きい）。
出所の違う数値を混ぜないため、シートに記録するのは GraphQL 側だけにする。
    view / like / likeRate … GraphQL（--period の期間。既定は累計）
    viewRest / likeRest    … REST の累計（比較・検証用。シートには入れない）

GraphQL が取得できなかった場合のみ view / like は REST 値にフォールバックし、
stderr に WARN を出す（cron がシートを空で上書きしないため）。

Usage:
  python3 fetch_note_stats.py                 # 過去1ヶ月に公開した記事
  python3 fetch_note_stats.py --all           # 全記事
  python3 fetch_note_stats.py --months 3      # 過去3ヶ月に公開した記事
  python3 fetch_note_stats.py --all --period 28d          # 直近28日の数値で
  python3 fetch_note_stats.py --all --period 2026-09-01:2026-09-30
  python3 fetch_note_stats.py --all --no-charcount        # 文字数取得を省いて高速化
  python3 fetch_note_stats.py --no-gql        # GraphQL を使わず従来どおりの出力

Output (JSON array):
  publishAt, url, name, charCount, hashtags, eyecatch,
  view, like, likeRate, impression, pv, comment, sales
"""
import os
import sys
import json
import re
import html
import argparse
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from note_gql import NoteGraphQL, period_vars  # noqa: E402

load_dotenv(Path(__file__).parent.parent / ".env")

NOTE_SESSION = os.getenv("NOTE_SESSION")
URLNAME = "takaesu7431"

NOTE_LIST_QUERY = """
query($unit: DashboardPeriodUnit!, $date: Datetime!, $endDate: Datetime,
      $order: DashboardNoteListOrder, $first: Int!, $after: String) {
  dashboardNoteListConnection(unit: $unit, date: $date, endDate: $endDate,
                              order: $order, first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      note { title status publishedAt link { absoluteUrl } }
      metrics { pageViewCount impressionCount likeCount commentCount salesAmount }
    } }
  }
}
"""


def fetch_articles(headers):
    articles = []
    page = 1
    while True:
        r = requests.get(
            f"https://note.com/api/v2/creators/{URLNAME}/contents?kind=note&page={page}",
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()["data"]
        items = data.get("contents", [])
        if not items:
            break
        articles.extend(items)
        if data.get("isLastPage", True):
            break
        page += 1
    return articles


def fetch_stats(headers):
    stats_map = {}
    page = 1
    while True:
        r = requests.get(
            f"https://note.com/api/v1/stats/pv?filter=all&page={page}",
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        notes = data.get("note_stats", [])
        if not notes:
            break
        for n in notes:
            stats_map[n["key"]] = n
        if data.get("last_page", True):
            break
        page += 1
    return stats_map


def fetch_body_length(key, headers):
    """記事詳細 API から本文テキストの文字数を返す。取得失敗時は空文字。"""
    try:
        r = requests.get(
            f"https://note.com/api/v3/notes/{key}",
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        body = r.json().get("data", {}).get("body", "") or ""
        # HTML タグ除去 → HTML エンティティ展開 → 空白・改行を除いた文字数
        text = re.sub(r"<[^>]+>", "", body)
        text = html.unescape(text)
        text = re.sub(r"[\s　]", "", text)
        return len(text)
    except Exception:
        return ""


def fetch_dashboard_metrics(period):
    """新ダッシュボードの記事別メトリクスを {note_key: metrics} で返す。"""
    gql = NoteGraphQL()
    variables = {**period_vars(period), "order": "PUBLISHED_DATE_DESC"}
    nodes = gql.paginate(NOTE_LIST_QUERY, variables, "dashboardNoteListConnection")

    metrics = {}
    for n in nodes:
        url = ((n.get("note") or {}).get("link") or {}).get("absoluteUrl") or ""
        m = re.search(r"/n/([a-zA-Z0-9]+)", url)
        if m:
            metrics[m.group(1)] = n.get("metrics") or {}
    return metrics


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--all", action="store_true", help="全記事を対象にする")
    ap.add_argument("--months", type=int, default=1, help="過去N ヶ月に公開した記事（既定 1）")
    ap.add_argument("--period", default="all",
                    help="ダッシュボード指標の集計期間: all / 7d / 28d / 365d / "
                         "YYYY-MM-DD / YYYY-MM-DD:YYYY-MM-DD（既定 all）")
    ap.add_argument("--no-charcount", action="store_true", help="文字数の取得を省く")
    ap.add_argument("--no-gql", action="store_true",
                    help="GraphQL を使わない（impression/pv/comment/sales は空になる）")
    args = ap.parse_args()

    if not NOTE_SESSION:
        print("ERROR: NOTE_SESSION が .env に設定されていません", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Cookie": f"_note_session_v5={NOTE_SESSION}",
        "User-Agent": "Mozilla/5.0",
    }

    articles = fetch_articles(headers)
    stats_map = fetch_stats(headers)

    dash = {}
    if not args.no_gql:
        try:
            dash = fetch_dashboard_metrics(args.period)
        except Exception as e:
            # ダッシュボード側が落ちても従来の項目だけは返す
            print(f"WARN: ダッシュボード統計を取得できませんでした: {e}", file=sys.stderr)

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    cutoff = now - timedelta(days=30 * args.months)

    if not args.all:
        articles = [
            a for a in articles
            if datetime.fromisoformat(a["publishAt"]) >= cutoff
        ]

    results = []
    fallback_keys = []
    for a in articles:
        key = a["key"]
        s = stats_map.get(key, {})
        d = dash.get(key, {})
        tags = " ".join(
            h.get("hashtag", {}).get("name", "")
            for h in a.get("hashtags", [])
        )
        rest_view = s.get("read_count") or 0
        rest_like = s.get("like_count") or a.get("likeCount", 0)

        # ビュー・スキは GraphQL を正とし、取れなかったときだけ REST に退避する
        view = d["pageViewCount"] if d.get("pageViewCount") is not None else rest_view
        like = d["likeCount"] if d.get("likeCount") is not None else rest_like
        if not d:
            fallback_keys.append(key)
        like_rate = round(like / view, 4) if view > 0 else ""

        char_count = "" if args.no_charcount else fetch_body_length(key, headers)
        results.append({
            "publishAt": a["publishAt"][:19].replace("T", " "),
            "url": f"https://note.com/{URLNAME}/n/{key}",
            "name": a.get("name", ""),
            "charCount": char_count,
            "hashtags": tags,
            "eyecatch": a.get("eyecatch", ""),
            # 新ダッシュボード（--period の期間。機能提供前の期間は null → ""）
            "view": view,
            "like": like,
            "likeRate": like_rate,
            "impression": d.get("impressionCount") if d.get("impressionCount") is not None else "",
            "comment": d.get("commentCount") if d.get("commentCount") is not None else "",
            "sales": d.get("salesAmount") if d.get("salesAmount") is not None else "",
            # REST の累計（比較・検証用。シートには記録しない）
            "viewRest": rest_view,
            "likeRest": rest_like,
        })

    if fallback_keys:
        print(
            f"WARN: {len(fallback_keys)}件でダッシュボードの数値が取れず、"
            f"view/like を REST の累計にフォールバックしました（出所が混ざります）: "
            f"{', '.join(fallback_keys[:5])}",
            file=sys.stderr,
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
