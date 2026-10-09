#!/usr/bin/env python3
"""
note 導線ダッシュボード（claude.ai Artifact）用のデータを発信記録シートから CSV に書き出す。

書き出すもの（既定: logs/note_funnel/）:
  bio_clicks.csv      … bioクリック シート（経路別の人のクリック、日別）
  click_detail.csv    … 転送クリック明細 ＋ 記事タイトル・その日の記事 PV/スキ（note記事日次）・スキ累計（note投稿一覧）
  note_referrers.csv  … note流入元 シート
  pinned.csv          … 固定ポスト履歴 シート
  x_note_posts.csv    … X投稿一覧のうち noteURL がある行（数値はカンマ除去、記事ID を付与）

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # 記事マスタ: note投稿一覧（タイトル・スキ累計）
    articles: dict[str, dict] = {}
    posts = get("note投稿一覧!A:I")
    for r in posts[1:]:
        r = r + [""] * (9 - len(r))
        m = ARTICLE_ID.search(r[1])
        if m:
            articles[m.group(1)] = {"title": r[2], "like_total": num(r[8])}

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
    write(os.path.join(args.out, "pinned.csv"), get("固定ポスト履歴!A:H"))

    # x_note_posts
    hdr = get("X投稿一覧!A1:AK1")[0]
    idx = {h: i for i, h in enumerate(hdr)}
    rows = [["投稿日", "投稿日時", "ポストURL", "本文冒頭", "種類", "インプレッション", "いいね", "エンゲ率", "詳細表示",
             "リンククリック", "フォロー増", "noteURL", "記事ID", "バズスコア", "グレード"]]
    for r in get("X投稿一覧!A2:AK"):
        r = r + [""] * (len(hdr) - len(r))
        note_url = r[idx["noteURL"]].strip() if "noteURL" in idx else ""
        if not note_url:
            continue
        m = ARTICLE_ID.search(note_url)
        g = lambda k: r[idx[k]] if k in idx else ""  # noqa: E731
        rows.append([
            g("投稿日時").replace("/", "-")[:10], g("投稿日時"), g("ポストURL"), g("ポスト本文").replace("\n", " ")[:60], g("ポスト種類"),
            num(g("インプレッション")), num(g("いいね")), num(g("エンゲ率")), num(g("詳細表示")), num(g("リンククリック")), num(g("フォロー増")),
            note_url, m.group(1) if m else "", g("バズスコア"), g("グレード"),
        ])
    write(os.path.join(args.out, "x_note_posts.csv"), rows)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(os.path.join(args.out, "exported_at.txt"), "w", encoding="utf-8") as f:
        f.write(stamp + "\n")
    print(f"✅ {args.out} に 5 ファイルを書き出し（{stamp}）: bio {len(bio)-1} 行 / 明細 {len(det)-1} 行 / 記事日次 {len(daily)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
