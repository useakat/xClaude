"""
会話 JSONL → PDF 変換スクリプト
Usage: python3 scripts/conv_to_pdf.py <jsonl_path> <output_pdf>
"""

import json
import sys
import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

# --- フォント登録 ---
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

FONT_SANS = "HeiseiKakuGo-W5"
FONT_SERIF = "HeiseiMin-W3"

# --- スタイル定義 ---
def make_styles():
    user_style = ParagraphStyle(
        "user",
        fontName=FONT_SANS,
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#1a1a2e"),
        backColor=colors.HexColor("#e8f4fd"),
        borderPad=6,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=4,
    )
    assistant_style = ParagraphStyle(
        "assistant",
        fontName=FONT_SERIF,
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "code",
        fontName=FONT_SANS,
        fontSize=8,
        leading=13,
        textColor=colors.HexColor("#2d2d2d"),
        backColor=colors.HexColor("#f4f4f4"),
        borderPad=5,
        leftIndent=8,
        rightIndent=4,
        spaceAfter=4,
    )
    label_user = ParagraphStyle(
        "label_user",
        fontName=FONT_SANS,
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#2980b9"),
        spaceBefore=10,
        spaceAfter=2,
    )
    label_assistant = ParagraphStyle(
        "label_assistant",
        fontName=FONT_SANS,
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#27ae60"),
        spaceBefore=10,
        spaceAfter=2,
    )
    title_style = ParagraphStyle(
        "title",
        fontName=FONT_SANS,
        fontSize=16,
        leading=22,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        fontName=FONT_SANS,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#666666"),
        spaceAfter=16,
    )
    return {
        "user": user_style,
        "assistant": assistant_style,
        "code": code_style,
        "label_user": label_user,
        "label_assistant": label_assistant,
        "title": title_style,
        "subtitle": subtitle_style,
    }


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def render_markdown_to_paragraphs(text: str, styles: dict) -> list:
    """Markdown テキストを Paragraph リストに変換（簡易実装）"""
    paragraphs = []
    lines = text.split("\n")
    in_code = False
    code_buf = []
    style = styles["assistant"]
    code_style = styles["code"]

    i = 0
    while i < len(lines):
        line = lines[i]

        # コードブロック
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                code_text = "\n".join(code_buf)
                # 長い行を折り返す
                wrapped_lines = []
                for cl in code_text.split("\n"):
                    if len(cl) > 80:
                        wrapped_lines.extend(textwrap.wrap(cl, 80))
                    else:
                        wrapped_lines.append(cl)
                code_escaped = escape_xml("\n".join(wrapped_lines))
                code_escaped = code_escaped.replace("\n", "<br/>")
                paragraphs.append(Paragraph(code_escaped, code_style))
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # 空行
        if line.strip() == "":
            paragraphs.append(Spacer(1, 4))
            i += 1
            continue

        # 見出し
        if line.startswith("### "):
            text_content = escape_xml(line[4:].strip())
            h_style = ParagraphStyle(
                "h3", parent=style,
                fontSize=11, leading=16,
                textColor=colors.HexColor("#2c3e50"),
                fontName=FONT_SANS,
                spaceBefore=8, spaceAfter=4,
            )
            paragraphs.append(Paragraph(f"<b>{text_content}</b>", h_style))
            i += 1
            continue

        if line.startswith("## "):
            text_content = escape_xml(line[3:].strip())
            h_style = ParagraphStyle(
                "h2", parent=style,
                fontSize=12, leading=18,
                textColor=colors.HexColor("#1a252f"),
                fontName=FONT_SANS,
                spaceBefore=10, spaceAfter=4,
            )
            paragraphs.append(Paragraph(f"<b>{text_content}</b>", h_style))
            i += 1
            continue

        if line.startswith("# "):
            text_content = escape_xml(line[2:].strip())
            h_style = ParagraphStyle(
                "h1", parent=style,
                fontSize=13, leading=20,
                textColor=colors.HexColor("#1a1a2e"),
                fontName=FONT_SANS,
                spaceBefore=12, spaceAfter=6,
            )
            paragraphs.append(Paragraph(f"<b>{text_content}</b>", h_style))
            i += 1
            continue

        # 水平線
        if line.strip() in ("---", "***", "___"):
            paragraphs.append(HRFlowable(width="100%", thickness=0.5,
                                          color=colors.HexColor("#cccccc"),
                                          spaceAfter=4, spaceBefore=4))
            i += 1
            continue

        # テーブル（簡易：行ごとにそのまま出力）
        if line.startswith("|"):
            # ヘッダー区切り行はスキップ
            if set(line.replace("|", "").replace("-", "").replace(" ", "")) == set():
                i += 1
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            row_text = "　　".join(escape_xml(c) for c in cells)
            table_style = ParagraphStyle(
                "table_row", parent=style,
                fontSize=9, leading=14,
                fontName=FONT_SANS,
                backColor=colors.HexColor("#fafafa"),
                borderPad=3,
                leftIndent=4,
            )
            paragraphs.append(Paragraph(row_text, table_style))
            i += 1
            continue

        # 箇条書き
        if line.startswith(("- ", "* ", "+ ")):
            text_content = line[2:].strip()
            text_content = apply_inline_styles(escape_xml(text_content))
            bullet_style = ParagraphStyle(
                "bullet", parent=style,
                leftIndent=12,
                bulletIndent=0,
                spaceBefore=1,
                spaceAfter=1,
            )
            paragraphs.append(Paragraph(f"• {text_content}", bullet_style))
            i += 1
            continue

        # 番号付きリスト
        import re
        num_match = re.match(r"^(\d+)\.\s+(.*)", line)
        if num_match:
            num = num_match.group(1)
            text_content = apply_inline_styles(escape_xml(num_match.group(2)))
            bullet_style = ParagraphStyle(
                "numbul", parent=style,
                leftIndent=16,
                spaceBefore=1,
                spaceAfter=1,
            )
            paragraphs.append(Paragraph(f"{num}. {text_content}", bullet_style))
            i += 1
            continue

        # 通常テキスト
        text_content = apply_inline_styles(escape_xml(line))
        paragraphs.append(Paragraph(text_content, style))
        i += 1

    return paragraphs


def apply_inline_styles(text: str) -> str:
    """インラインの **bold** と `code` を変換"""
    import re
    # **bold**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # `code`
    text = re.sub(r"`([^`]+)`", r'<font name="HeiseiKakuGo-W5" size="8" color="#c0392b">\1</font>', text)
    return text


def extract_text_from_content(content) -> str:
    """assistant メッセージの content からテキストを抽出"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                # thinking, tool_use, tool_result はスキップ
        return "\n".join(parts)
    return ""


def extract_user_text(content) -> str:
    """user メッセージからテキストを抽出"""
    if isinstance(content, str):
        # system-reminder タグなどを除去
        import re
        text = re.sub(r"<system-reminder>.*?</system-reminder>", "", content, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text", "")
                import re
                t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.DOTALL)
                t = re.sub(r"<[^>]+>", "", t)
                parts.append(t.strip())
        return "\n".join(p for p in parts if p)
    return ""


def parse_conversation(jsonl_path: str, start_after_uuid: str = None) -> list:
    """JSONL から (role, text, timestamp) のリストを返す。
    start_after_uuid が指定された場合、そのUUIDのメッセージ（含む）以降のみ返す。
    """
    messages = []
    seen_uuids = set()
    collecting = (start_after_uuid is None)

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type")
            uuid = obj.get("uuid", "")

            # 開始 UUID に達したら収集開始
            if not collecting and uuid == start_after_uuid:
                collecting = True

            if not collecting:
                continue

            # 重複排除
            if uuid and uuid in seen_uuids:
                continue
            if uuid:
                seen_uuids.add(uuid)

            if msg_type == "user":
                if obj.get("isMeta"):
                    continue
                content = obj.get("message", {}).get("content", "")
                text = extract_user_text(content)
                if not text or text.startswith("/"):
                    continue
                if not any(c.isalnum() for c in text):
                    continue
                ts = obj.get("timestamp", "")
                messages.append(("user", text, ts))

            elif msg_type == "assistant":
                content = obj.get("message", {}).get("content", [])
                text = extract_text_from_content(content)
                if not text.strip():
                    continue
                ts = obj.get("timestamp", "")
                messages.append(("assistant", text, ts))

    return messages


def build_pdf(messages: list, output_path: str, title: str = "X アルゴリズム解説セッション"):
    styles = make_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    story = []

    # タイトル
    story.append(Paragraph(title, styles["title"]))
    story.append(Paragraph(f"生成日: 2026-05-16　　会話数: {len(messages)} ターン", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2980b9"), spaceAfter=12))

    for i, (role, text, ts) in enumerate(messages):
        if role == "user":
            label = Paragraph("▶ よーん", styles["label_user"])
            content_paras = [Paragraph(escape_xml(text), styles["user"])]
            block = [label] + content_paras + [Spacer(1, 2)]
        else:
            label = Paragraph("◀ Claude", styles["label_assistant"])
            content_paras = render_markdown_to_paragraphs(text, styles)
            block = [label] + content_paras + [Spacer(1, 6)]

        story.extend(block)

    doc.build(story)
    print(f"✅ PDF 生成完了: {output_path}")
    print(f"   ターン数: {len(messages)}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 conv_to_pdf.py <jsonl_path> <output.pdf>")
        sys.exit(1)

    jsonl_path = sys.argv[1]
    output_path = sys.argv[2]

    start_uuid = sys.argv[3] if len(sys.argv) >= 4 else None
    print(f"解析中: {jsonl_path}")
    messages = parse_conversation(jsonl_path, start_after_uuid=start_uuid)
    print(f"抽出ターン数: {len(messages)}")

    build_pdf(messages, output_path)
