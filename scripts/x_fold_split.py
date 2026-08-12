#!/usr/bin/env python3
"""X のタイムライン折り返し（さらに表示）位置で本文を分割する。

X は 280 weight を超える投稿をタイムラインで畳み、先頭 280 weight 分だけを表示する。
weight は全角文字=2 / 半角文字=1。添付画像の URL は文字数を消費しないため対象外。

使い方:
    python3 scripts/x_fold_split.py <本文ファイル>
    cat draft.md | python3 scripts/x_fold_split.py
    python3 scripts/x_fold_split.py <本文ファイル> --json

`/check-reader --fold` が可視ブロックを切り出すために使う。
"""
import argparse
import json
import re
import sys

LIMIT = 280


def char_weight(ch: str) -> int:
    """X の weighted length: 全角=2 / 半角=1"""
    o = ord(ch)
    if (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0x303E or 0x3041 <= o <= 0x33FF
            or 0x3400 <= o <= 0x4DBF or 0x4E00 <= o <= 0x9FFF or 0xA000 <= o <= 0xA4CF
            or 0xAC00 <= o <= 0xD7A3 or 0xF900 <= o <= 0xFAFF or 0xFE30 <= o <= 0xFE4F
            or 0xFF00 <= o <= 0xFF60 or 0xFFE0 <= o <= 0xFFE6 or o >= 0x20000):
        return 2
    return 1


def weight(s: str) -> int:
    return sum(char_weight(c) for c in s)


def split_at_fold(body: str, limit: int = LIMIT):
    """(可視ブロック, 畳まれる部分) を返す。折り返しが無ければ後者は空文字。"""
    w = 0
    for i, ch in enumerate(body):
        cw = char_weight(ch)
        if w + cw > limit:
            return body[:i], body[i:]
        w += cw
    return body, ''


def strip_meta(text: str) -> str:
    """見出し・ハッシュタグ行・t.co URL を除いた投稿本文を取り出す。"""
    lines = []
    for line in text.splitlines():
        if line.startswith('#') and not line.lstrip('#').startswith(' '):
            # 「#宇宙 #物理」のようなハッシュタグ行は本文に数えるので残す
            lines.append(line)
            continue
        if line.startswith('## ') or line.startswith('# '):
            continue
        lines.append(line)
    body = '\n'.join(lines)
    body = re.sub(r'\s*https://t\.co/\S+', '', body)
    return body.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description='X の折り返し位置で本文を分割する')
    ap.add_argument('file', nargs='?', help='本文ファイル（省略時は stdin）')
    ap.add_argument('--limit', type=int, default=LIMIT, help=f'折り返し weight（既定 {LIMIT}）')
    ap.add_argument('--json', action='store_true', help='JSON で出力する')
    ap.add_argument('--raw', action='store_true', help='見出し除去などの前処理をしない')
    args = ap.parse_args()

    text = open(args.file, encoding='utf-8').read() if args.file else sys.stdin.read()
    body = text.strip() if args.raw else strip_meta(text)

    visible, hidden = split_at_fold(body, args.limit)
    result = {
        'total_chars': len(body),
        'total_weight': weight(body),
        'folded': bool(hidden),
        'visible_chars': len(visible),
        'visible_weight': weight(visible),
        'visible': visible,
        'hidden': hidden,
        'cut_before': visible[-20:],
        'cut_after': hidden[:20],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"全文: {result['total_chars']}字 / {result['total_weight']}weight")
    if not hidden:
        print(f"折り返しなし（{args.limit} weight 以内）。--fold チェックはスキップしてよい")
        return 0
    print(f"可視: {result['visible_chars']}字 / {result['visible_weight']}weight")
    print(f"切れ目直前: ...{result['cut_before']}")
    print(f"畳まれる側: {result['cut_after']}...")
    print()
    print('--- 可視ブロック（読者役にはここだけを渡す）---')
    print(visible)
    return 0


if __name__ == '__main__':
    sys.exit(main())
