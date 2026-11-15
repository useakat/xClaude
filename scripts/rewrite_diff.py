#!/usr/bin/env python3
"""
rewrite_diff.py — リライト原稿と元原稿を文単位で突き合わせ、「変更箇所」を機械的に出す

使い方:
  python3 scripts/rewrite_diff.py <元原稿ファイル> <新原稿ファイル> [--threshold 0.6] [--json]

出力:
  - 字数（改行・空白を除く）: 元 / 新 / 比率。新が元より長ければ exit 1（避けたいこと⑤）
  - 文数: 元 / 新 / 完全一致 / 微修正（threshold 以上一致）/ 新規
  - 【チェック対象】新原稿の文のうち、次のどれかに当たるもの（番号付き・原文）
      新規   … 元のどの文とも threshold 未満の一致（冒頭差し替え・書き足し）
      微修正 … 元の文に近いが同一ではない（語句を変えた・短くした）
      削除前後 … 元にあった文が消えた位置の直前・直後にある文（削ったことで読みが詰まりやすい）
  - 【元から消えた文】新原稿に対応する文が無い元の文（刺さった数字・固有名詞を落としていないか確認用）

writer-xrewrite の STEP 5/6 で使う。読者役などのチェック指摘のうち、ここに挙がった文に
掛かるものだけを反映し、それ以外（元投稿由来）は未反映で証跡に残す。
"""
import argparse
import difflib
import json
import re
import sys

# 句点・疑問符・感嘆符・三点リーダの直後、または改行で切る（」は文中の引用を壊すので対象外）
SPLIT_RE = re.compile(r"(?<=[。？！…])\s*|\n+")


def split_sentences(text: str):
    return [s.strip() for s in SPLIT_RE.split(text) if s and s.strip()]


def nchars(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("orig")
    ap.add_argument("new")
    ap.add_argument("--threshold", type=float, default=0.6, help="この一致率以上なら「元の文の微修正」とみなす（既定 0.6）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    o_text = open(args.orig, encoding="utf-8").read()
    n_text = open(args.new, encoding="utf-8").read()
    so, sn = split_sentences(o_text), split_sentences(n_text)

    # 新の各文 → 最も近い元の文
    match = []  # (best_idx, ratio)
    for s in sn:
        best_i, best_r = -1, 0.0
        for i, t in enumerate(so):
            r = difflib.SequenceMatcher(None, s, t, autojunk=False).ratio()
            if r > best_r:
                best_i, best_r = i, r
        match.append((best_i, best_r))

    kinds = []
    for (i, r) in match:
        if r >= 0.999:
            kinds.append("同一")
        elif r >= args.threshold:
            kinds.append("微修正")
        else:
            kinds.append("新規")

    # 元の文で、新に対応（threshold 以上）が無いもの = 削除
    covered = {i for (i, r), k in zip(match, kinds) if k != "新規"}
    deleted = [i for i in range(len(so)) if i not in covered]

    # 削除位置の前後: 削除された元文の直前/直後の元文に対応する新文を「削除前後」に
    ctx = set()
    for d in deleted:
        for nb in (d - 1, d + 1):
            if 0 <= nb < len(so) and nb in covered:
                for j, ((i, r), k) in enumerate(zip(match, kinds)):
                    if i == nb and k != "新規":
                        ctx.add(j)

    targets = []
    for j, (s, k) in enumerate(zip(sn, kinds)):
        tags = []
        if k != "同一":
            tags.append(k)
        if j in ctx and k == "同一":
            tags.append("削除前後")
        elif j in ctx:
            tags.append("削除前後")
        if tags:
            targets.append({"no": j + 1, "kind": "・".join(dict.fromkeys(tags)), "text": s})

    co, cn = nchars(o_text), nchars(n_text)
    result = {
        "chars": {"orig": co, "new": cn, "ratio": round(cn / co, 3) if co else None, "not_longer": cn <= co},
        "sentences": {
            "orig": len(so), "new": len(sn),
            "same": kinds.count("同一"), "minor": kinds.count("微修正"), "added": kinds.count("新規"),
            "deleted": len(deleted),
        },
        "targets": targets,
        "deleted": [{"no": i + 1, "text": so[i]} for i in deleted],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        c, s = result["chars"], result["sentences"]
        print(f"字数: 元 {c['orig']} 字 → 新 {c['new']} 字 ({c['ratio']*100:.0f}%)  {'OK 元より長くない' if c['not_longer'] else 'NG 元より長い'}")
        print(f"文数: 元 {s['orig']} / 新 {s['new']} / 同一 {s['same']} / 微修正 {s['minor']} / 新規 {s['added']} / 元から消えた {s['deleted']}")
        print(f"\n【チェック対象】{len(targets)} 文（新原稿の文番号）")
        for t in targets:
            print(f"  {t['no']:>2} [{t['kind']}] {t['text']}")
        print(f"\n【元から消えた文】{len(deleted)} 文")
        for d in result["deleted"]:
            print(f"  {d['no']:>2} {d['text']}")
    sys.exit(0 if result["chars"]["not_longer"] else 1)


if __name__ == "__main__":
    main()
