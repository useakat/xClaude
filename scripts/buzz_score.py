#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X 投稿のバズスコア・グレードを計算し、X投稿一覧シートの AJ:AK に書き込む。

「投稿した結果をスコア化して、次の投稿作成に活かす」仕組みの土台。
各投稿を「その投稿が出た時点での、同プロジェクトのいつもの実力」と比べる
相対スコアなので、フォロワー増やアルゴリズム変動の影響を受けにくい。

定義:
- 対象: outputs シートで what_id（W001 / W003 / z01 など）が付いた X 投稿
- 基準値: 同プロジェクトで、その投稿より前 BASE_WINDOW_DAYS 日以内の投稿の中央値
  （IMP とエンゲ率それぞれ）。MIN_BASE 本未満ならそれ以前の全投稿を含める。
  それでも MIN_BASE 本未満なら採点しない
- スコア = W_IMP * log2(IMP / 基準IMP) + W_ER * log2(エンゲ率 / 基準エンゲ率)
  （+1 = いつもの2倍、+2 = 4倍、-1 = 半分）
- グレード: S >= 2 / A >= 1 / B >= -1 / C < -1
- 投稿から MIN_AGE_DAYS 日未満の投稿は IMP がまだ伸びるため採点しない（空欄）

出力:
- X投稿一覧の AJ 列（バズスコア）・AK 列（グレード）を全行ブロックで上書き
  （対象外の行は空欄）
- logs/buzz_scores.csv を毎回全件再生成（git で履歴を追える）

使い方:
  python3 scripts/buzz_score.py            # 計算してシート・CSV を更新
  python3 scripts/buzz_score.py --dry-run  # 集計サマリーだけ表示（書き込みなし）

呼び出し元: reporter-daily（毎日 21:00 JST の日報 routine）STEP 10.6
Sheets の読み書きは scripts/sheets_values.py（サービスアカウント認証）経由。
"""
import argparse
import csv
import json
import math
import os
import re
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SHEETS_CLI = os.path.join(SCRIPT_DIR, "sheets_values.py")
CSV_PATH = os.path.join(REPO_ROOT, "logs", "buzz_scores.csv")
SS2 = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"  # outputs
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # X投稿一覧
JST = timezone(timedelta(hours=9))

# ── スコア定義 ─────────────────────────────────────
BASE_WINDOW_DAYS = 56   # 基準値に使う直近期間（8週）
MIN_BASE = 5            # 基準値に必要な最小本数
MIN_AGE_DAYS = 2        # 採点に必要な投稿後日数
W_IMP, W_ER = 0.7, 0.3  # IMP とエンゲ率の重み
ER_FLOOR = 0.0005       # エンゲ率 0 の投稿の下限（log2 用）
GRADES = [(2.0, "S"), (1.0, "A"), (-1.0, "B")]  # それ未満は C

SCORE_COL, GRADE_COL = "AJ", "AK"
NUM_COLS = 32  # A..AF


def sheets_get(spreadsheet_id, rng):
    out = subprocess.run(
        [sys.executable, SHEETS_CLI, "get", spreadsheet_id, rng],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout).get("values", [])


def sheets_update(spreadsheet_id, rng, values):
    out = subprocess.run(
        [sys.executable, SHEETS_CLI, "update", spreadsheet_id, rng, "-"],
        input=json.dumps(values, ensure_ascii=False),
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def tweet_id(url):
    m = re.search(r"/status(?:es)?/(\d+)", url or "")
    return m.group(1) if m else None


def to_float(s):
    try:
        return float(str(s).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


def grade_of(score):
    for th, g in GRADES:
        if score >= th:
            return g
    return "C"


def load_posts():
    """outputs で what_id が付いた X 投稿を X投稿一覧の行順で返す"""
    proj = {}
    for row in sheets_get(SS2, "outputs!A:C")[1:]:
        row = row + [""] * (3 - len(row))
        tid = tweet_id(row[1])
        if tid and row[2].strip():
            proj[tid] = row[2].strip()

    xrows = sheets_get(SS3, f"X投稿一覧!A2:AF")
    posts = []
    for i, row in enumerate(xrows, start=2):
        row = row + [""] * (NUM_COLS - len(row))
        p = {"row": i, "tid": tweet_id(row[1]), "proj": None, "score": None, "grade": ""}
        posts.append(p)
        p["proj"] = proj.get(p["tid"])
        if not p["proj"]:
            continue
        try:
            p["dt"] = datetime.strptime(row[0].strip(), "%Y/%m/%d %H:%M:%S").replace(tzinfo=JST)
        except ValueError:
            p["proj"] = None
            continue
        imp, er = to_float(row[10]), to_float(row[17])
        if not imp or imp <= 0 or er is None:
            p["proj"] = None
            continue
        p["imp"], p["er"], p["head"] = imp, max(er, ER_FLOOR), row[2].replace("\n", " ")[:15]
    return posts


def score_posts(posts, now):
    scored = [p for p in posts if p["proj"]]
    for p in scored:
        if now - p["dt"] < timedelta(days=MIN_AGE_DAYS):
            continue
        prior = [q for q in scored if q["proj"] == p["proj"] and q["dt"] < p["dt"]]
        window = [q for q in prior if q["dt"] >= p["dt"] - timedelta(days=BASE_WINDOW_DAYS)]
        base = window if len(window) >= MIN_BASE else prior
        if len(base) < MIN_BASE:
            continue
        p["base_imp"] = statistics.median(q["imp"] for q in base)
        p["base_er"] = statistics.median(q["er"] for q in base)
        s = W_IMP * math.log2(p["imp"] / p["base_imp"]) + W_ER * math.log2(p["er"] / p["base_er"])
        p["score"] = round(s, 2)
        p["grade"] = grade_of(s)
    return [p for p in scored if p["score"] is not None]


def write_csv(scored):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tweet_id", "プロジェクト", "投稿日時", "IMP", "エンゲ率", "基準IMP", "基準エンゲ率", "スコア", "グレード", "冒頭15字"])
        for p in sorted(scored, key=lambda p: p["dt"]):
            w.writerow([p["tid"], p["proj"], p["dt"].strftime("%Y-%m-%d %H:%M"), int(p["imp"]), p["er"],
                        int(p["base_imp"]), round(p["base_er"], 4), p["score"], p["grade"],
                        p["head"].replace(",", "，")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    now = datetime.now(JST)

    posts = load_posts()
    scored = score_posts(posts, now)
    if not scored:
        print("採点対象なし")
        return 0

    by_proj = {}
    for p in scored:
        by_proj.setdefault(p["proj"], Counter())[p["grade"]] += 1
    print(f"採点: {len(scored)}本（対象 {sum(1 for p in posts if p['proj'])}本、投稿{MIN_AGE_DAYS}日未満・基準不足は除外）")
    for proj, c in sorted(by_proj.items()):
        print(f"  {proj}: n={sum(c.values())}  S/A/B/C = {c['S']}/{c['A']}/{c['B']}/{c['C']}")

    if args.dry_run:
        print("（dry-run: 書き込みなし）")
        return 0

    write_csv(scored)
    last_row = posts[-1]["row"] if posts else 1
    block = [["" if p["score"] is None else p["score"], p["grade"]] for p in posts]
    header = sheets_get(SS3, f"X投稿一覧!{SCORE_COL}1:{GRADE_COL}1")
    if not header or not header[0] or not header[0][0]:
        sheets_update(SS3, f"X投稿一覧!{SCORE_COL}1:{GRADE_COL}1", [["バズスコア", "グレード"]])
    res = sheets_update(SS3, f"X投稿一覧!{SCORE_COL}2:{GRADE_COL}{last_row}", block)
    print(f"✅ X投稿一覧 {SCORE_COL}:{GRADE_COL} を更新（{len(posts)}行） / {os.path.relpath(CSV_PATH, REPO_ROOT)} を再生成")
    print(f"   API応答: {res[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
