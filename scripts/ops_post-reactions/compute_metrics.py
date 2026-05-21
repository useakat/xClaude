#!/usr/bin/env python3
"""
反応者データを集計し、ペルソナ別指標を /tmp/metrics_output.json に保存。
Sheets アクセスなし（純粋な計算のみ）。

入力:
  --reactors FILE    : all_reactors.json（各要素: username, parent_tweet_id, persona, is_follower）
  --nf_results GLOB  : 非フォロワー LLM 分類結果ファイル群（"*.json"）
  --persona FILE     : follower_persona_llm.json（username, persona フィールドを含む）

出力形式 /tmp/metrics_output.json:
  {
    "summary": { "total_followers": N, "total_reactors": N, "follower_reactors": N, "nf_reactors": N },
    "persona": [
      { "p": 1, "name": "...", "total_f": N, "f_react": N, "nf_react": N,
        "f_react_rate": 0.0, "sensitivity": 0.0, "density": 0.0 },
      ...
    ]
  }
"""

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

OUTPUT_PATH = "/tmp/metrics_output.json"

PERSONA_NAMES = {
    1:  "物理・科学に憧れる文系会社員",
    2:  "技術系エンジニア・IT職",
    3:  "育児中の母親・主婦",
    4:  "60代以上シニア男性",
    5:  "文系就職した元理系学生",
    6:  "教師・塾講師・教育職",
    7:  "50-60代女性・文学派",
    8:  "量子・物理専門ITエンジニア",
    9:  "医療職",
    10: "起業家・経営者",
    11: "物理計算・理論大好き派",
    12: "ユーモア・宇宙ライトファン",
    13: "その他・分類困難",
    14: "技術検証・独自仮説派",
    15: "AI関連",
    16: "クリエイター",
    17: "SF・サブカル・アニメ",
    18: "学生",
    19: "不明",
}


def load_reactors(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_nf_results(pattern: str) -> dict:
    """非フォロワー LLM 分類: username → persona の辞書を返す"""
    nf_persona: dict[str, int] = {}
    for filepath in glob.glob(pattern):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                username = item.get("username", "").lstrip("@")
                persona = item.get("persona", 13)
                try:
                    persona = int(persona)
                except (TypeError, ValueError):
                    persona = 13
                nf_persona[username.lower()] = persona
    return nf_persona


def load_follower_personas(path: str) -> tuple[dict, dict]:
    """フォロワーペルソナJSON: (username→persona辞書, ペルソナ別フォロワー数辞書) を返す"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    follower_map: dict[str, int] = {}
    persona_count: dict[int, int] = defaultdict(int)

    for item in data:
        username = str(item.get("username", "")).lstrip("@").lower()
        persona = item.get("persona", 13)
        try:
            persona = int(persona)
        except (TypeError, ValueError):
            persona = 13
        follower_map[username] = persona
        persona_count[persona] += 1

    return follower_map, dict(persona_count)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reactors", required=True)
    parser.add_argument("--nf_results", default="")
    parser.add_argument("--persona", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.reactors):
        print(f"ERROR: {args.reactors} が見つかりません", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.persona):
        print(f"ERROR: {args.persona} が見つかりません", file=sys.stderr)
        sys.exit(1)

    print("STEP 1: フォロワーペルソナ読み込み...", file=sys.stderr)
    follower_map, persona_f_count = load_follower_personas(args.persona)
    total_followers = len(follower_map)
    print(f"  フォロワー総数: {total_followers}", file=sys.stderr)

    print("STEP 2: 非フォロワー分類結果読み込み...", file=sys.stderr)
    nf_persona_map: dict[str, int] = {}
    if args.nf_results:
        nf_persona_map = load_nf_results(args.nf_results)
    print(f"  非フォロワー分類済み: {len(nf_persona_map)}件", file=sys.stderr)

    print("STEP 3: 反応者データ読み込み...", file=sys.stderr)
    reactors = load_reactors(args.reactors)
    print(f"  反応件数（延べ）: {len(reactors)}", file=sys.stderr)

    # ペルソナ別集計
    # f_reactors[persona] = set of follower usernames
    # nf_reactors[persona] = set of non-follower usernames
    # reaction_rows[persona] = total reaction rows（密度計算用）
    f_reactors: dict[int, set] = defaultdict(set)
    nf_reactors: dict[int, set] = defaultdict(set)
    reaction_rows: dict[int, int] = defaultdict(int)

    follower_reactor_names: set[str] = set()
    nf_reactor_names: set[str] = set()

    for item in reactors:
        username = str(item.get("username", "")).lstrip("@").lower()
        if not username:
            continue

        # フォロワー判定
        if username in follower_map:
            persona = follower_map[username]
            f_reactors[persona].add(username)
            follower_reactor_names.add(username)
        else:
            persona = nf_persona_map.get(username, 13)
            nf_reactors[persona].add(username)
            nf_reactor_names.add(username)

        reaction_rows[persona] += 1

    total_reactors = len(follower_reactor_names) + len(nf_reactor_names)
    total_f_reactors = len(follower_reactor_names)

    print(f"  フォロワー反応者: {total_f_reactors}人", file=sys.stderr)
    print(f"  非フォロワー反応者: {len(nf_reactor_names)}人", file=sys.stderr)
    print(f"  反応者合計: {total_reactors}人", file=sys.stderr)

    # ペルソナ別指標計算
    all_personas = sorted(set(
        list(persona_f_count.keys()) +
        list(f_reactors.keys()) +
        list(nf_reactors.keys())
    ))

    persona_metrics = []
    for p in all_personas:
        total_f = persona_f_count.get(p, 0)
        f_react = len(f_reactors.get(p, set()))
        nf_react = len(nf_reactors.get(p, set()))
        total_react_rows = reaction_rows.get(p, 0)
        unique_reactors = f_react + nf_react

        f_react_rate = (f_react / total_f) if total_f > 0 else 0.0

        # 反応感度 = (F反応数/F反応合計) / (全F数/全フォロワー)
        if total_f_reactors > 0 and total_followers > 0 and total_f > 0:
            sensitivity = (f_react / total_f_reactors) / (total_f / total_followers)
        else:
            sensitivity = 0.0

        # 反応密度 = 延べ反応数 / ユニーク反応者数
        density = (total_react_rows / unique_reactors) if unique_reactors > 0 else 0.0

        persona_metrics.append({
            "p": p,
            "name": PERSONA_NAMES.get(p, f"P{p:02d}"),
            "total_f": total_f,
            "f_react": f_react,
            "nf_react": nf_react,
            "f_react_rate": round(f_react_rate, 4),
            "sensitivity": round(sensitivity, 4),
            "density": round(density, 2),
        })

    # 反応感度降順ソート（反応者0のペルソナは末尾に）
    persona_metrics.sort(key=lambda x: (-x["sensitivity"], -x["f_react"]))

    output = {
        "summary": {
            "total_followers": total_followers,
            "total_reactors": total_reactors,
            "follower_reactors": total_f_reactors,
            "nf_reactors": len(nf_reactor_names),
        },
        "persona": persona_metrics,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ {OUTPUT_PATH} に保存しました")


if __name__ == "__main__":
    main()
