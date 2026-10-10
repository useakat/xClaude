#!/usr/bin/env python3
"""
note 導線ダッシュボード（claude.ai Artifact）用のデータを発信記録シートから CSV に書き出す。

書き出すもの（既定: logs/note_funnel/）:
  bio_clicks.csv      … bioクリック シート（経路別の人のクリック、日別）
  click_detail.csv    … 転送クリック明細 ＋ 記事タイトル・その日の記事 PV/スキ（note記事日次）・スキ累計（note投稿一覧）
  note_referrers.csv  … note流入元 シート
  pinned.csv          … 固定ポスト履歴 シート
  x_note_posts.csv    … X投稿一覧のうち noteURL がある行（数値はカンマ除去、記事ID を付与）
  links.csv           … 導線（ホスト×キー＝貼ったリンク）ごとの一覧。経路（bio / 投稿 / 固定）、記事、
                        元の X / Threads 投稿（IMP・いいね・リンククリック）、クリック合計・初回・最終日
  articles.csv        … note 記事ごとの指標（note投稿一覧）＋ 転送クリック合計・導線数・X 投稿数
  article_daily.csv   … note記事日次（日付×記事の PV・スキ）＋ その日の転送クリック

ダッシュボード側のデータセット id は CSV のファイル名（拡張子なし）と同じ。
列名を変えるとダッシュボードの表・計算が壊れるので、変えるときはページも直す。

使い方:
  python3 scripts/note_funnel_export.py            # logs/note_funnel/ に書き出す
  python3 scripts/note_funnel_export.py --out DIR  # 出力先を変える

Sheets の読み取りは scripts/sheets_values.py（サービスアカウント）経由。routine / ローカルの両方で動く。
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SHEETS_CLI = os.path.join(SCRIPT_DIR, "sheets_values.py")
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
DEFAULT_OUT = os.path.join(REPO_ROOT, "logs", "note_funnel")
ARTICLE_ID = re.compile(r"(n[0-9a-f]{10,16})")


def get(rng: str) -> list[list[str]]:
    out = subprocess.run([sys.executable, SHEETS_CLI, "get", SS3, rng], capture_output=True, text=True, check=True)
    return json.loads(out.stdout).get("values", [])


def num(s) -> str:
    return str(s or "").replace(",", "").replace("%", "").strip()


def write(path: str, rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def short(title: str, n: int = 10) -> str:
    return title if len(title) <= n else title[:n] + "…"


# 転送ホスト → 経路名（bioクリック シートの列名と同じ）。redirects.json の column と一致させる
HOST_ROUTE = {
    "usephys.net": "X bio", "threads.usephys.net": "Threads bio",
    "xpost.usephys.net": "X 投稿", "tpost.usephys.net": "Threads 投稿",
    "note.usephys.net": "X 固定", "tnote.usephys.net": "Threads 固定",
}


def ymd(s: str) -> str:
    """'2026/10/08 9:18:31' / '2026-10-08 09:32' → '2026-10-08'"""
    s = (s or "").strip().replace("/", "-")[:10]
    p = s.split("-")
    return f"{p[0]}-{p[1]:>02}-{p[2]:>02}".replace(" ", "0") if len(p) == 3 else s


def build_links(det, articles, pinned, x_rows, x_idx, t_rows, t_idx):
    """転送クリック明細（日付, ホスト, キー, クリック）を導線（ホスト×キー）にまとめ、元の投稿と突き合わせる。

    投稿の特定: (1) X投稿一覧の noteURL / 本文、Threads投稿一覧の本文に `ホスト/キー` が含まれる投稿、
    (2) 無ければ固定ポスト履歴で記事ID・投稿キーが一致する投稿URL、
    (3) それも無ければ投稿キーが日付（YYYYMMDD）なら、その日の同じ媒体のトップ投稿（親なし）で表示回数が最大のもの
        （Threads はリンクをセルフリプに貼るとリプが投稿一覧に載らないため）。
    """
    agg: dict[tuple[str, str], dict] = {}
    for r in det[1:]:
        r = r + [""] * (4 - len(r))
        if not (r[0] and r[1] and r[2]):
            continue
        a = agg.setdefault((r[1], r[2]), {"clicks": 0, "first": r[0], "last": r[0]})
        a["clicks"] += int(num(r[3]) or 0)
        a["first"] = min(a["first"], r[0])
        a["last"] = max(a["last"], r[0])

    def x_g(r, k):
        return r[x_idx[k]] if k in x_idx and x_idx[k] < len(r) else ""

    def t_g(r, k):
        return r[t_idx[k]] if k in t_idx and t_idx[k] < len(r) else ""

    rows = [["id", "経路", "媒体", "種別", "ホスト", "キー", "記事ID", "記事タイトル", "投稿キー", "投稿日", "投稿URL", "本文冒頭",
             "インプレッション", "いいね", "リンククリック", "固定開始", "固定終了", "クリック合計", "初回クリック日", "最終クリック日"]]
    for (host, key), a in sorted(agg.items(), key=lambda kv: (kv[1]["last"], kv[0]), reverse=True):
        route = HOST_ROUTE.get(host, host)
        media = "Threads" if route.startswith("Threads") else "X"
        m = ARTICLE_ID.match(key)
        aid = m.group(1) if m else ""
        post_key = key.split("/", 1)[1] if aid and "/" in key else ""
        kind = "プロフ" if route.endswith("bio") else "投稿"
        link = f"{host}/{key}"
        has_link = re.compile(re.escape(link) + r"(?![/A-Za-z0-9_-])").search  # /ID は /ID/キー に一致させない
        pin = next((p for p in pinned if p["媒体"] == media and p["記事ID"] == aid and (p["投稿キー"] == post_key if p["投稿キー"] else not post_key) and aid), None)
        if pin:
            kind = "固定"
        post = None
        if media == "X":
            cand = [r for r in x_rows if has_link(x_g(r, "noteURL")) or has_link(x_g(r, "ポスト本文"))]
            if not cand and pin:
                cand = [r for r in x_rows if x_g(r, "ポストURL").rstrip("/").endswith(pin["投稿ID"])]
            if not cand and re.fullmatch(r"\d{8}", post_key):
                day = f"{post_key[:4]}-{post_key[4:6]}-{post_key[6:]}"
                cand = [r for r in x_rows if ymd(x_g(r, "投稿日時")) == day and not x_g(r, "親ポストURL")]
                cand.sort(key=lambda r: -int(num(x_g(r, "インプレッション")) or 0))
            if cand:
                r = cand[0]
                post = {"date": ymd(x_g(r, "投稿日時")), "url": x_g(r, "ポストURL"), "text": x_g(r, "ポスト本文"),
                        "imp": num(x_g(r, "インプレッション")), "like": num(x_g(r, "いいね")), "lc": num(x_g(r, "リンククリック"))}
        else:
            cand = [r for r in t_rows if has_link(t_g(r, "本文"))]
            if not cand and pin:
                cand = [r for r in t_rows if t_g(r, "投稿URL").rstrip("/").endswith(pin["投稿ID"])]
            if not cand and re.fullmatch(r"\d{8}", post_key):
                day = f"{post_key[:4]}-{post_key[4:6]}-{post_key[6:]}"
                cand = [r for r in t_rows if ymd(t_g(r, "投稿日時")) == day and not t_g(r, "親投稿URL")]
                cand.sort(key=lambda r: -int(num(t_g(r, "views")) or 0))
            if cand:
                r = cand[0]
                post = {"date": ymd(t_g(r, "投稿日時")), "url": t_g(r, "投稿URL"), "text": t_g(r, "本文"),
                        "imp": num(t_g(r, "views")), "like": num(t_g(r, "いいね")), "lc": ""}
        if post is None and pin:
            post = {"date": pin["開始日"], "url": pin["投稿URL"], "text": "", "imp": "", "like": "", "lc": ""}
        post = post or {"date": "", "url": "", "text": "", "imp": "", "like": "", "lc": ""}
        title = short(articles.get(aid, {}).get("title", "")) if aid else ""
        if aid and not title:
            title = "（タイトル未取得）"
        rows.append([f"{host}|{key}", route, media, kind, host, key, aid, title, post_key, post["date"], post["url"],
                     post["text"].replace("\n", " ")[:40], post["imp"], post["like"], post["lc"],
                     pin["開始日"] if pin else "", pin["終了日"] if pin else "",
                     a["clicks"], a["first"], a["last"]])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # 記事マスタ: note投稿一覧（タイトル・スキ累計）
    articles: dict[str, dict] = {}
    posts = get("note投稿一覧!A:M")
    for r in posts[1:]:
        r = r + [""] * (13 - len(r))
        m = ARTICLE_ID.search(r[1])
        if m:
            articles[m.group(1)] = {"title": r[2], "like_total": num(r[8]), "date": ymd(r[0]), "chars": num(r[3]),
                                    "view_total": num(r[7]), "like_rate": num(r[9]), "comments": num(r[11]), "sales": num(r[12])}

    # 記事日次: note記事日次（日付×記事ID → PV・スキ）
    daily: dict[tuple[str, str], tuple[str, str]] = {}
    try:
        for r in get("note記事日次!A:E")[1:]:
            r = r + [""] * (5 - len(r))
            if r[0] and r[1]:
                daily[(r[0], r[1])] = (num(r[3]), num(r[4]))
                articles.setdefault(r[1], {"title": r[2], "like_total": ""})
    except subprocess.CalledProcessError:
        print("警告: note記事日次 シートが読めない（未作成？）。当日 PV/スキは空欄にする", file=sys.stderr)

    # bio_clicks
    bio = get("bioクリック!A:J")
    write(os.path.join(args.out, "bio_clicks.csv"), bio)

    # click_detail
    det = get("転送クリック明細!A:D")
    rows = [["id", "日付", "ホスト", "キー", "記事タイトル", "クリック", "記事PV（当日）", "記事スキ（当日）", "スキ（累計）"]]
    for r in det[1:]:
        r = r + [""] * (4 - len(r))
        m = ARTICLE_ID.match(r[2])
        aid = m.group(1) if m else ""
        a = articles.get(aid, {}) if aid else {}
        pv, like = daily.get((r[0], aid), ("", "")) if aid else ("", "")
        title = short(a.get("title", "")) if aid else ""
        if aid and not a.get("title"):
            title = "（タイトル未取得）"
        rows.append(["|".join(r[:3]), r[0], r[1], r[2], title, num(r[3]), pv, like, a.get("like_total", "") if aid else ""])
    write(os.path.join(args.out, "click_detail.csv"), rows)

    # note_referrers
    write(os.path.join(args.out, "note_referrers.csv"), get("note流入元!A:P"))

    # pinned
    pinned_raw = get("固定ポスト履歴!A:H")
    write(os.path.join(args.out, "pinned.csv"), pinned_raw)
    pinned = [dict(zip(pinned_raw[0], r + [""] * (8 - len(r)))) for r in pinned_raw[1:] if r and r[0]]

    # x_note_posts
    hdr = get("X投稿一覧!A1:AK1")[0]
    idx = {h: i for i, h in enumerate(hdr)}
    rows = [["投稿日", "投稿日時", "ポストURL", "本文冒頭", "種類", "インプレッション", "いいね", "エンゲ率", "詳細表示",
             "リンククリック", "フォロー増", "noteURL", "記事ID", "バズスコア", "グレード"]]
    x_rows = [r + [""] * (len(hdr) - len(r)) for r in get("X投稿一覧!A2:AK")]
    x_note_count: dict[str, int] = {}
    for r in x_rows:
        note_url = r[idx["noteURL"]].strip() if "noteURL" in idx else ""
        if not note_url:
            continue
        m = ARTICLE_ID.search(note_url)
        if m:
            x_note_count[m.group(1)] = x_note_count.get(m.group(1), 0) + 1
        g = lambda k: r[idx[k]] if k in idx else ""  # noqa: E731
        rows.append([
            g("投稿日時").replace("/", "-")[:10], g("投稿日時"), g("ポストURL"), g("ポスト本文").replace("\n", " ")[:60], g("ポスト種類"),
            num(g("インプレッション")), num(g("いいね")), num(g("エンゲ率")), num(g("詳細表示")), num(g("リンククリック")), num(g("フォロー増")),
            note_url, m.group(1) if m else "", g("バズスコア"), g("グレード"),
        ])
    write(os.path.join(args.out, "x_note_posts.csv"), rows)

    # links: 導線（ホスト×キー）ごと
    t_raw = get("Threads投稿一覧!A:S")
    t_idx = {h: i for i, h in enumerate(t_raw[0])} if t_raw else {}
    t_rows = [r + [""] * (len(t_raw[0]) - len(r)) for r in t_raw[1:]] if t_raw else []
    links = build_links(det, articles, pinned, x_rows, idx, t_rows, t_idx)
    write(os.path.join(args.out, "links.csv"), links)

    # article_daily: note記事日次 ＋ その日の転送クリック
    clicks_by_day_article: dict[tuple[str, str], int] = {}
    clicks_by_article: dict[str, int] = {}
    last_click: dict[str, str] = {}
    link_count: dict[str, set] = {}
    for r in det[1:]:
        r = r + [""] * (4 - len(r))
        m = ARTICLE_ID.match(r[2])
        if not (r[0] and m):
            continue
        aid = m.group(1)
        c = int(num(r[3]) or 0)
        clicks_by_day_article[(r[0], aid)] = clicks_by_day_article.get((r[0], aid), 0) + c
        clicks_by_article[aid] = clicks_by_article.get(aid, 0) + c
        last_click[aid] = max(last_click.get(aid, ""), r[0])
        link_count.setdefault(aid, set()).add((r[1], r[2]))
    rows = [["id", "日付", "記事ID", "タイトル", "PV", "スキ", "転送クリック"]]
    for (day, aid), (pv, like) in sorted(daily.items()):
        rows.append([f"{day}|{aid}", day, aid, short(articles.get(aid, {}).get("title", ""), 14), pv, like, clicks_by_day_article.get((day, aid), 0)])
    write(os.path.join(args.out, "article_daily.csv"), rows)

    # articles: 記事ごと
    rows = [["記事ID", "タイトル", "投稿日", "文字数", "ビュー（累計）", "スキ（累計）", "スキ率", "コメント", "売上",
             "転送クリック合計", "導線数", "X投稿数", "最終クリック日"]]
    for aid, a in articles.items():
        if not a.get("date"):
            continue  # note記事日次 だけに現れた記事（note投稿一覧に無い）は除く
        rows.append([aid, a["title"], a["date"], a["chars"], a["view_total"], a["like_total"], a["like_rate"], a["comments"], a["sales"],
                     clicks_by_article.get(aid, 0), len(link_count.get(aid, ())), x_note_count.get(aid, 0), last_click.get(aid, "")])
    rows[1:] = sorted(rows[1:], key=lambda r: (-r[9], -int(r[4] or 0), r[2]))
    write(os.path.join(args.out, "articles.csv"), rows)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(os.path.join(args.out, "exported_at.txt"), "w", encoding="utf-8") as f:
        f.write(stamp + "\n")
    print(f"✅ {args.out} に 8 ファイルを書き出し（{stamp}）: bio {len(bio)-1} 行 / 明細 {len(det)-1} 行 / 記事日次 {len(daily)} 件 / 導線 {len(links)-1} 件 / 記事 {len(rows)-1} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
