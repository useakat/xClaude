#!/usr/bin/env python3
"""
カレントセッションの JSONL 履歴を Markdown に変換して docs/history/ に保存する。

使い方:
  python3 save_session_history.py --title "タイトル" --slug "slug_name"
  python3 save_session_history.py --title "タイトル" --slug "slug_name" --jsonl /path/to/session.jsonl
  python3 save_session_history.py --list  # 最近の JSONL 一覧を表示
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JSONL_DIR = Path.home() / ".claude" / "projects" / ("-" + str(REPO_ROOT).strip("/").replace("/", "-"))
HISTORY_DIR = REPO_ROOT / "docs" / "history"
JST = timezone(timedelta(hours=9))


def find_latest_jsonl():
    files = sorted(JSONL_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"JSONL ファイルが見つかりません: {JSONL_DIR}")
    return files[0]


def list_jsonls():
    files = sorted(JSONL_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files[:10]:
        mtime = datetime.fromtimestamp(f.stat().st_mtime, JST).strftime("%Y-%m-%d %H:%M JST")
        size_kb = f.stat().st_size // 1024
        print(f"  {mtime}  {size_kb:5d}KB  {f.name}")


def format_tool_line(names):
    """ツール名のリストを1行のツール呼び出し表記にまとめる。"""
    return "*[ツール: " + ", ".join(f"`{n}`" for n in names) + "]*"


def render_body(items):
    """items（("text", str) / ("tool", name) のリスト）を本文 Markdown に整形する。

    連続するツール呼び出しは1行に集約する。
    """
    parts = []
    pending = []
    for kind, val in items:
        if kind == "tool":
            pending.append(val)
        else:
            if pending:
                parts.append(format_tool_line(pending))
                pending = []
            text = val.strip()
            if text:
                parts.append(text)
    if pending:
        parts.append(format_tool_line(pending))
    return "\n\n".join(parts)


def render_blocks(blocks, title, today):
    """blocks（[role, ts, items] のリスト）から履歴 Markdown 全文を組み立てる。

    区切り線（---）はよーんの発言（ターン境界）の前にのみ入れる。
    """
    lines = [
        "---",
        f"title: {title} — セッション履歴",
        f"date: {today}",
        "sidebar:",
        "  hidden: true",
        "---",
        "",
        "# セッション履歴",
        "",
        f"> {today} のセッション作業ログ。",
        "",
        "---",
        "",
    ]

    for i, (role, ts, items) in enumerate(blocks):
        ts_label = f" *({ts} JST)*" if ts else ""
        if role == "user":
            if i != 0:
                lines.append("---")
                lines.append("")
            lines.append(f"## よーん{ts_label}")
        else:
            lines.append(f"### Claude{ts_label}")
        lines.append("")
        lines.append(render_body(items))
        lines.append("")

    return "\n".join(lines)


def jsonl_to_markdown(jsonl_path: Path, title: str) -> str:
    today = datetime.now(JST).strftime("%Y-%m-%d")
    raw = []  # (role, ts, items)

    with open(jsonl_path) as f:
        for line in f:
            obj = json.loads(line)
            t = obj.get("type")
            msg = obj.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")
            ts_str = obj.get("timestamp", "")

            ts = ""
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    ts = dt.astimezone(JST).strftime("%H:%M")
                except Exception:
                    pass

            if t == "user" and role == "user":
                if isinstance(content, str) and content.strip():
                    stripped = content.strip()
                    if not stripped.startswith("<") and not stripped.startswith("Tool:"):
                        raw.append(("user", ts, [("text", stripped)]))
                elif isinstance(content, list):
                    texts = [
                        b.get("text", "").strip()
                        for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                        and not b.get("text", "").strip().startswith("<")
                    ]
                    if texts:
                        raw.append(("user", ts, [("text", "\n".join(texts))]))

            elif t == "assistant" and role == "assistant":
                if isinstance(content, list):
                    items = []
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                txt = block.get("text", "").strip()
                                if txt:
                                    items.append(("text", txt))
                            elif block.get("type") == "tool_use":
                                items.append(("tool", block.get("name", "unknown")))
                    if items:
                        raw.append(("assistant", ts, items))

    # 連続する同一話者のメッセージを1つのブロックに統合
    blocks = []
    for role, ts, items in raw:
        if blocks and blocks[-1][0] == role:
            blocks[-1][2].extend(items)
        else:
            blocks.append([role, ts, list(items)])

    return render_blocks(blocks, title, today)


def main():
    parser = argparse.ArgumentParser(description="セッション履歴を Markdown に変換")
    parser.add_argument("--title", help="履歴のタイトル（日本語）")
    parser.add_argument("--slug", help="ファイル名スラグ（英語スネークケース）")
    parser.add_argument("--jsonl", help="JSONL ファイルパス（省略時は最新）")
    parser.add_argument("--list", action="store_true", help="JSONL ファイル一覧を表示")
    parser.add_argument("--date", help="日付プレフィックス YYYYMMDD（省略時は今日）")
    args = parser.parse_args()

    if args.list:
        print("最近の JSONL ファイル:")
        list_jsonls()
        return

    if not args.title or not args.slug:
        parser.error("--title と --slug は必須です")

    jsonl_path = Path(args.jsonl) if args.jsonl else find_latest_jsonl()
    if not jsonl_path.exists():
        print(f"ERROR: {jsonl_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    date_prefix = args.date or datetime.now(JST).strftime("%Y%m%d")
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = HISTORY_DIR / f"{date_prefix}_{args.slug}.md"

    # バージョン番号付与（既存ファイルと重複しない）
    if out_path.exists():
        v = 2
        while True:
            candidate = HISTORY_DIR / f"{date_prefix}_{args.slug}_v{v}.md"
            if not candidate.exists():
                out_path = candidate
                break
            v += 1

    print(f"変換中: {jsonl_path.name}", file=sys.stderr)
    md = jsonl_to_markdown(jsonl_path, args.title)
    out_path.write_text(md)

    msg_count = md.count("\n## よーん") + md.count("\n### Claude")
    print(f"✅ 保存完了")
    print(f"   ファイル: {out_path.relative_to(REPO_ROOT)}")
    print(f"   メッセージ数: {msg_count}")
    print(out_path)  # 最終行にパスだけ出力（スキルが参照する）


if __name__ == "__main__":
    main()
