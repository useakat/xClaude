#!/usr/bin/env python3
"""
note.com から takaesu7431 の記事一覧 + 累計ビュー数を取得して JSON で出力する。

Usage:
  python3 fetch_note_stats.py           # 過去1ヶ月の記事
  python3 fetch_note_stats.py --all     # 全記事
  python3 fetch_note_stats.py --months 3  # 過去3ヶ月

Output (JSON array):
  publishAt, url, hashtags, eyecatch, view, like, likeRate
"""
import os, sys, json, requests, re, html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

NOTE_SESSION = os.getenv("NOTE_SESSION")
URLNAME = "takaesu7431"


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


def main():
    if not NOTE_SESSION:
        print("ERROR: NOTE_SESSION が .env に設定されていません", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Cookie": f"_note_session_v5={NOTE_SESSION}",
        "User-Agent": "Mozilla/5.0",
    }

    fetch_all = "--all" in sys.argv
    months = 1
    if "--months" in sys.argv:
        idx = sys.argv.index("--months")
        months = int(sys.argv[idx + 1])

    articles = fetch_articles(headers)
    stats_map = fetch_stats(headers)

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    cutoff = now - timedelta(days=30 * months)

    if not fetch_all:
        articles = [
            a for a in articles
            if datetime.fromisoformat(a["publishAt"]) >= cutoff
        ]

    results = []
    for a in articles:
        s = stats_map.get(a["key"], {})
        tags = " ".join(
            h.get("hashtag", {}).get("name", "")
            for h in a.get("hashtags", [])
        )
        view = s.get("read_count") or 0
        like = s.get("like_count") or a.get("likeCount", 0)
        like_rate = round(like / view, 4) if view > 0 else ""

        char_count = fetch_body_length(a["key"], headers)
        results.append({
            "publishAt": a["publishAt"][:19].replace("T", " "),
            "url": f"https://note.com/{URLNAME}/n/{a['key']}",
            "name": a.get("name", ""),
            "charCount": char_count,
            "hashtags": tags,
            "eyecatch": a.get("eyecatch", ""),
            "view": view,
            "like": like,
            "likeRate": like_rate,
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
