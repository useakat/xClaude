#!/usr/bin/env python3
"""
note.com に記事を下書き保存するスクリプト。
使い方:
    python3 send_note_draft.py "タイトル" "本文（Markdown）"
    python3 send_note_draft.py "タイトル" < article.md
"""
import os
import sys
import uuid
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

NOTE_SESSION = os.getenv("NOTE_SESSION")  # .env に _note_session_v5 の値を設定


def md_to_note_html(md_text: str) -> str:
    """Markdown を note の内部 HTML 形式に変換する"""
    lines = md_text.strip().split("\n")
    parts = [
        f'<table-of-contents name="{uuid.uuid4()}" id="{uuid.uuid4()}"><br></table-of-contents>'
    ]
    in_code_block = False
    code_lines = []

    for line in lines:
        uid = str(uuid.uuid4())

        # コードブロック処理
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_html = "<br>".join(code_lines)
                parts.append(f'<pre name="{uid}" id="{uid}"><code>{code_html}</code></pre>')
            continue

        if in_code_block:
            code_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        if line.strip() == "":
            continue

        # インライン変換
        def convert_inline(text):
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
            return text

        if line.startswith("## "):
            parts.append(f'<h2 name="{uid}" id="{uid}">{convert_inline(line[3:])}</h2>')
        elif line.startswith("### "):
            parts.append(f'<h3 name="{uid}" id="{uid}">{convert_inline(line[4:])}</h3>')
        else:
            parts.append(f'<p name="{uid}" id="{uid}">{convert_inline(line)}</p>')

    return "\n".join(parts)


def create_draft(title: str, body_md: str) -> dict:
    """下書きを新規作成して本文を保存する"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"_note_session_v5={NOTE_SESSION}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }

    body_html = md_to_note_html(body_md)

    # ① 下書きを新規作成（ID を取得）
    r1 = requests.post(
        "https://note.com/api/v1/text_notes",
        headers=headers,
        json={"draft": True, "name": title},
    )
    r1.raise_for_status()
    note_id = r1.json()["data"]["id"]

    # ② 本文とタイトルを保存
    r2 = requests.post(
        f"https://note.com/api/v1/text_notes/draft_save?id={note_id}",
        headers=headers,
        json={"name": title, "body": body_html},
    )
    r2.raise_for_status()

    return {
        "note_id": note_id,
        "edit_url": f"https://note.com/notes/{note_id}/edit",
    }


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        title = sys.argv[1]
        body = sys.argv[2]
    elif len(sys.argv) == 2:
        title = sys.argv[1]
        body = sys.stdin.read().strip()
    else:
        print("Usage: python3 send_note_draft.py <title> [body]", file=sys.stderr)
        sys.exit(1)

    result = create_draft(title, body)
    print(json.dumps(result, ensure_ascii=False, indent=2))
