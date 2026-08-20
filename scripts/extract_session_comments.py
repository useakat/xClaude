#!/usr/bin/env python3
"""セッション履歴（.jsonl）からユーザーの発言（人間のテキスト入力）だけを抽出する。

原稿チェック agent（/check-yohn）のペルソナ蒸留用コーパス作成に使う。
各ユーザー発言に、直前のアシスタント発言の末尾（文脈）を添えて Markdown で出力する。

Usage:
    python3 scripts/extract_session_comments.py <output.md> <session1.jsonl> [<session2.jsonl> ...]
"""
import json
import re
import sys

CONTEXT_TAIL = 400  # 直前アシスタント発言の末尾を何文字添えるか

SKIP_PATTERNS = (
    "<task-notification",
    "<command-name>",
    "<local-command",
    "[Request interrupted",
)


def clean_text(text: str) -> str:
    """system-reminder ブロックを除去して整形する。"""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    return text.strip()


def extract_user_text(content) -> str | None:
    """user メッセージの content から人間のテキストを取り出す（tool_result は除外）。"""
    if isinstance(content, str):
        return clean_text(content)
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return clean_text("\n".join(parts)) if parts else None
    return None


def extract_assistant_text(content) -> str | None:
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(parts).strip() or None
    if isinstance(content, str):
        return content.strip() or None
    return None


def process_file(path: str, out) -> int:
    count = 0
    last_assistant = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("isSidechain"):
                continue  # サブエージェントのやり取りは対象外
            if d.get("type") == "assistant":
                text = extract_assistant_text(d.get("message", {}).get("content"))
                if text:
                    last_assistant = text
                continue
            if d.get("type") != "user":
                continue
            if d.get("isMeta"):
                continue
            origin = d.get("origin") or {}
            if origin.get("kind") not in (None, "human"):
                continue  # hook・自動注入は対象外
            text = extract_user_text(d.get("message", {}).get("content"))
            if not text:
                continue
            if any(p in text for p in SKIP_PATTERNS):
                continue
            count += 1
            ts = (d.get("timestamp") or "")[:16].replace("T", " ")
            out.write(f"### [{ts}] {path.rsplit('/', 1)[-1][:8]}#{count}\n\n")
            if last_assistant:
                tail = last_assistant[-CONTEXT_TAIL:]
                out.write(f"**直前のアシスタント発言（末尾）**:\n> {tail}\n\n".replace("\n> \n", "\n"))
            out.write(f"**ユーザー**:\n{text}\n\n---\n\n")
    return count


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out_path, files = sys.argv[1], sys.argv[2:]
    total = 0
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("# セッション履歴 ユーザー発言コーパス\n\n")
        for path in files:
            out.write(f"## {path}\n\n")
            n = process_file(path, out)
            total += n
            print(f"{path}: {n} messages")
    print(f"total: {total} messages -> {out_path}")


if __name__ == "__main__":
    main()
