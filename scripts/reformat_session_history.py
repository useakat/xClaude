#!/usr/bin/env python3
"""既存の docs/history/*.md を読みやすい形式に再整形する（ワンタイム）。

連続する同一話者セクションを1つに統合し、ツール呼び出し行を集約、
セクション間の余分な区切り線を除去する。元 JSONL が残っていない過去
ファイルにも適用できるよう、生成済み Markdown をテキストとして整形する。

使い方:
  python3 reformat_session_history.py             # docs/history/*.md を全て上書き
  python3 reformat_session_history.py --dry-run   # 整形結果を stdout に出すだけ
  python3 reformat_session_history.py FILE...      # 指定ファイルのみ処理
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from save_session_history import render_body  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = REPO_ROOT / "docs" / "history"

TOOL_RE = re.compile(r"^\*\[ツール(?:呼び出し)?:\s*(.+?)\]\*$")
HEADING_RE = re.compile(r"^(##\s+よーん|###\s+Claude)(.*)$")


def content_to_items(content_lines):
    """セクション本文の行リストを ("text"/"tool", value) のリストに変換する。"""
    items = []
    text_buf = []

    def flush():
        if text_buf:
            t = "\n".join(text_buf).strip()
            if t:
                items.append(("text", t))
        text_buf.clear()

    for line in content_lines:
        stripped = line.strip()
        if stripped == "---":
            continue
        m = TOOL_RE.match(stripped)
        if m:
            flush()
            for tok in m.group(1).split(","):
                name = tok.strip().strip("`").strip()
                if name:
                    items.append(("tool", name))
        else:
            text_buf.append(line)
    flush()
    return items


def reformat(text):
    lines = text.split("\n")

    head_idx = None
    for i, line in enumerate(lines):
        if HEADING_RE.match(line):
            head_idx = i
            break
    if head_idx is None:
        return text  # 見出しが無い（想定外）ならそのまま返す

    header = lines[:head_idx]
    body_lines = lines[head_idx:]

    # 見出しごとにセクション分割
    sections = []  # [role, ts_suffix, content_lines]
    cur = None
    for line in body_lines:
        m = HEADING_RE.match(line)
        if m:
            if cur:
                sections.append(cur)
            role = "user" if "よーん" in m.group(1) else "assistant"
            cur = [role, m.group(2), []]
        elif cur is not None:
            cur[2].append(line)
    if cur:
        sections.append(cur)

    # 連続する同一話者のセクションを統合（最初の時刻を採用）
    blocks = []  # [role, ts_suffix, items]
    for role, ts, content in sections:
        items = content_to_items(content)
        # スキルプロンプト注入（"Base directory for this skill:" で始まるよーん発言）はスキップ
        if role == "user" and items and items[0][0] == "text" and items[0][1].startswith("Base directory for this skill:"):
            continue
        if blocks and blocks[-1][0] == role:
            blocks[-1][2].extend(items)
        else:
            blocks.append([role, ts, items])

    out = list(header)
    while out and out[-1] == "":
        out.pop()
    out.append("")  # header 末尾は ---（イントロ区切り）+ 空行で揃える

    for i, (role, ts, items) in enumerate(blocks):
        heading = ("## よーん" if role == "user" else "### Claude") + ts
        if role == "user" and i != 0:
            out.append("---")
            out.append("")
        out.append(heading)
        out.append("")
        out.append(render_body(items))
        out.append("")

    return "\n".join(out).rstrip("\n") + "\n"


def main():
    parser = argparse.ArgumentParser(description="既存セッション履歴を再整形")
    parser.add_argument("files", nargs="*", help="対象ファイル（省略時は docs/history/*.md）")
    parser.add_argument("--dry-run", action="store_true", help="書き込まず結果を表示")
    args = parser.parse_args()

    if args.files:
        targets = [Path(f) for f in args.files]
    else:
        targets = sorted(HISTORY_DIR.glob("*.md"))

    for path in targets:
        original = path.read_text()
        result = reformat(original)
        if args.dry_run:
            print(f"===== {path.name} =====")
            print(result)
            continue
        if result != original:
            path.write_text(result)
            print(f"整形: {path.relative_to(REPO_ROOT)}")
        else:
            print(f"変更なし: {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
