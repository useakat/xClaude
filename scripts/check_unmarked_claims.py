#!/usr/bin/env python3
"""参照マーカー [N] の付いていない事実主張を検出する。

W002 の原稿は事実主張に [N] を付ける運用のため、「マーカーの無い文」は
統計的な異常値として扱える。ただしマーカーの無い文の大半は一般的な科学の
説明と語り手の地の文であり、出典は不要。そこで「特定の人物・機関が、特定の
時点に、何をしたか」を述べた文だけを高スコアで拾う。

由来: 2026-09-27。チャンドラセカール記事で「片づけたのは、その計算を発表する
よう勧めた当人だった」という一文が、マーカー無しのまま4種類の検品を通過し、
かつ事実として誤っていた。推敲中に既出の事実（研究を励ました）を圧縮する際、
一段強い新しい主張（発表を勧めた）に滑ったことが原因。

Usage:
    python3 scripts/check_unmarked_claims.py <draft.md> [--top N] [--emit]
"""
import argparse
import re
import sys
from pathlib import Path

MARKER = re.compile(r'\[\d+(?:\s*,\s*\d+)*\]')

# 行単位で本文から除外するもの
SKIP_LINE = re.compile(r'^\s*(?:#|\||>|!\[|<!--|---|\*\*図|#\S)')

# 機関・組織・賞など、固有の主体を示す語
INSTITUTION = re.compile(
    r'王立天文学会|王立協会|国際天文学連合|ノーベル|トリニティ|ケンブリッジ|シカゴ大学|'
    r'ヤーキス|コレージュ・ド・フランス|天文台|カレッジ|ブルース賞|金メダル|学会|大学'
)

# 推量・呼びかけ・主観（出典を要さない）
HEDGE = re.compile(
    r'だろう|かもしれない|はずだ|はずである|ほしい|みよう|想像し|思い浮かべ|'
    r'ではないか|のだろうか|と思う|気がする|に見える|かのようだ'
)

# 一般論の主語（科学の説明）
GENERIC_SUBJECT = re.compile(
    r'^(?:星|恒星|電子|原子|物質|光|重力|核融合|白色矮星|中性子星|ブラックホール|宇宙|'
    r'これ|それ|つまり|だが|しかし|ところが|なぜ|もし)'
)

# 断定の過去・完了（出来事の記述）
PAST_ASSERT = re.compile(r'(?:した|された|だった|であった|いた|なった|れた|きた|えた|った)。?$')

# 「〜した当人」「〜してきた相手」など、人を指す語を過去の行為で修飾する形。
# 人名を書かずに特定人物の行為を主張する文を拾うための手がかり。
ACTOR_CLAUSE = re.compile(
    r'(?:た|ていた|てきた)(?:当人|本人|人物|相手|男|友人|同僚|恩師|師)'
)


def load_body(path: Path) -> list[tuple[int, str]]:
    """本文の行を (行番号, 本文) で返す。参考情報以降と除外行は落とす。"""
    out = []
    for i, line in enumerate(path.read_text(encoding='utf-8').split('\n'), 1):
        if line.startswith('## 参考情報'):
            break
        s = line.strip()
        if not s or SKIP_LINE.match(s):
            continue
        out.append((i, s))
    return out


def split_sentences(text: str) -> list[str]:
    """。で分割する。ただし「」の内側では切らない。"""
    sents, buf, depth = [], '', 0
    for ch in text:
        buf += ch
        if ch in '「『':
            depth += 1
        elif ch in '」』':
            depth = max(0, depth - 1)
        elif ch == '。' and depth == 0:
            sents.append(buf.strip())
            buf = ''
    if buf.strip():
        sents.append(buf.strip())
    return [s for s in sents if s]


# 固有名詞として扱わない一般カタカナ語
NOT_ACTOR = {
    'インタビュー', 'ブラックホール', 'エネルギー', 'スピード', 'バランス', 'タイミング',
    'メートル', 'キロメートル', 'グラム', 'パターン', 'イメージ', 'テーマ', 'メッセージ',
    'スケール', 'データ', 'モデル', 'ガス', 'コア', 'レベル', 'ケース', 'ポイント',
}


def collect_actors(lines: list[tuple[int, str]]) -> set[str]:
    """本文に2回以上現れるカタカナ4文字以上の連なりを固有名詞とみなす。

    一般名詞は NOT_ACTOR で除く。人名の判定は本来 形態素解析が要るが、
    「2回以上出現する長いカタカナ語」でも実用上は人名・地名・機関名に絞り込める。
    """
    text = '\n'.join(s for _, s in lines)
    counts: dict[str, int] = {}
    for m in re.findall(r'[ァ-ヴー]{4,}', text):
        counts[m] = counts.get(m, 0) + 1
    return {k for k, v in counts.items() if v >= 2 and k not in NOT_ACTOR}


def score(sent: str, actors: set[str], density: float = 0.0) -> tuple[int, list[str]]:
    pts, why = 0, []
    if ACTOR_CLAUSE.search(sent):
        pts += 4
        why.append('人物への行為の帰属')
    if density >= 0.4:
        pts += 3
        why.append(f'周囲の出典密度{density:.0%}')
    if any(a in sent for a in actors):
        pts += 4
        why.append('固有名詞')
    if INSTITUTION.search(sent):
        pts += 4
        why.append('機関名')
    if re.search(r'\d{4}年', sent):
        pts += 3
        why.append('年号')
    elif re.search(r'\d+(?:月|日|歳|年|回|人|倍)', sent):
        pts += 2
        why.append('数値')
    if PAST_ASSERT.search(sent):
        pts += 2
        why.append('断定の過去')
    if HEDGE.search(sent):
        pts -= 5
        why.append('推量/呼びかけ')
    if GENERIC_SUBJECT.match(sent):
        pts -= 3
        why.append('一般論の主語')
    return pts, why


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('draft')
    ap.add_argument('--top', type=int, default=20, help='表示する件数（既定20）')
    ap.add_argument('--threshold', type=int, default=5, help='報告するスコアの下限（既定5）')
    ap.add_argument('--emit', action='store_true',
                    help='draft/unmarked-claims.md に判定表の雛形を書き出す')
    args = ap.parse_args()

    path = Path(args.draft)
    if not path.exists():
        print(f'エラー: {path} が見つかりません', file=sys.stderr)
        return 1

    lines = load_body(path)
    actors = collect_actors(lines)

    # 先に全文を並べ、各文の周囲（前後3文）のマーカー密度を出す
    seq: list[tuple[int, str, bool]] = []
    for lineno, line in lines:
        for sent in split_sentences(line):
            seq.append((lineno, sent, bool(MARKER.search(sent))))

    total = len(seq)
    marked = sum(1 for _, _, m in seq if m)
    flagged = []
    for i, (lineno, sent, is_marked) in enumerate(seq):
        if is_marked:
            continue
        lo, hi = max(0, i - 3), min(len(seq), i + 4)
        neighbours = [m for j, (_, _, m) in enumerate(seq[lo:hi], lo) if j != i]
        density = (sum(neighbours) / len(neighbours)) if neighbours else 0.0
        pts, why = score(sent, actors, density)
        if pts >= args.threshold:
            flagged.append((pts, lineno, sent, why))

    flagged.sort(key=lambda x: (-x[0], x[1]))

    print(f'本文の文数: {total}  マーカーあり: {marked}  '
          f'マーカー無しで要確認: {len(flagged)} 件（しきい値 {args.threshold}）')
    print(f'固有名詞として検出: {", ".join(sorted(actors)) or "（なし）"}')
    print()
    for pts, lineno, sent, why in flagged[:args.top]:
        print(f'[score {pts:2d}] L{lineno}  ({"/".join(why)})')
        print(f'    {sent}')
    if len(flagged) > args.top:
        print(f'\n… 他 {len(flagged) - args.top} 件（--top で増やせます）')

    if args.emit:
        out = path.parent / 'unmarked-claims.md'
        rows = ['# 参照マーカーの無い事実主張 — 判定表', '',
                f'> `scripts/check_unmarked_claims.py {path}` の出力。',
                '> 各行を3択で判定し、**「既出の言い換え」を選ぶときは参照先の `[N]` を必ず書く**。',
                '> 書けない場合は、それは既出の言い換えではなく新しい主張である。', '',
                '| L | 文 | score | 判定（要出典／既出の言い換え→[N]／地の文） | 対応 |',
                '|---|---|---|---|---|']
        for pts, lineno, sent, _ in flagged:
            s = sent.replace('|', '\\|')
            rows.append(f'| {lineno} | {s} | {pts} |  |  |')
        out.write_text('\n'.join(rows) + '\n', encoding='utf-8')
        print(f'\n判定表を書き出しました: {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
