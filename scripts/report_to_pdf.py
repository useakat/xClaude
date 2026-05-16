"""
Markdown 報告書 → PDF 変換スクリプト
Usage: python3 scripts/report_to_pdf.py <input.md> <output.pdf>
"""

import re
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# --- フォント ---
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
SANS = "HeiseiKakuGo-W5"
SERIF = "HeiseiMin-W3"

# --- カラー ---
C_NAVY  = colors.HexColor("#1a1a2e")
C_BLUE  = colors.HexColor("#2980b9")
C_GRAY  = colors.HexColor("#555555")
C_LGRAY = colors.HexColor("#f5f5f5")
C_MGRAY = colors.HexColor("#cccccc")
C_RED   = colors.HexColor("#c0392b")
C_GREEN = colors.HexColor("#27ae60")
C_CODE_BG = colors.HexColor("#f0f0f0")
C_TABLE_HEAD = colors.HexColor("#2c3e50")
C_TABLE_EVEN = colors.HexColor("#ecf0f1")


def make_styles():
    base = ParagraphStyle("base", fontName=SERIF, fontSize=10, leading=17,
                          textColor=C_NAVY)
    return {
        "h1": ParagraphStyle("h1", fontName=SANS, fontSize=18, leading=26,
                              textColor=C_NAVY, spaceBefore=0, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontName=SANS, fontSize=13, leading=20,
                              textColor=C_BLUE, spaceBefore=16, spaceAfter=6,
                              borderPad=(0,0,2,0)),
        "h3": ParagraphStyle("h3", fontName=SANS, fontSize=11, leading=17,
                              textColor=C_NAVY, spaceBefore=12, spaceAfter=4),
        "h4": ParagraphStyle("h4", fontName=SANS, fontSize=10, leading=15,
                              textColor=C_GRAY, spaceBefore=8, spaceAfter=2),
        "body": base,
        "code": ParagraphStyle("code", fontName=SANS, fontSize=8, leading=13,
                                textColor=colors.HexColor("#2d2d2d"),
                                backColor=C_CODE_BG, borderPad=6,
                                leftIndent=8, rightIndent=4, spaceAfter=6),
        "bullet": ParagraphStyle("bullet", parent=base, leftIndent=14,
                                  spaceBefore=1, spaceAfter=1),
        "bullet2": ParagraphStyle("bullet2", parent=base, leftIndent=26,
                                   spaceBefore=1, spaceAfter=1, fontSize=9),
        "meta": ParagraphStyle("meta", fontName=SANS, fontSize=9, leading=14,
                                textColor=C_GRAY, spaceAfter=8),
        "note": ParagraphStyle("note", fontName=SANS, fontSize=8, leading=13,
                                textColor=C_GRAY, leftIndent=8,
                                backColor=colors.HexColor("#fffde7"),
                                borderPad=4, spaceAfter=6),
    }


def esc(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def inline(text: str) -> str:
    """インライン装飾: **bold**, `code`"""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`",
                  r'<font name="HeiseiKakuGo-W5" size="8" color="#c0392b">\1</font>',
                  text)
    return text


def parse_table(lines: list) -> list:
    """Markdown テーブル行リスト → [[cell,...], ...] (ヘッダー区切り行除外)"""
    rows = []
    for line in lines:
        if re.match(r"^\|[-| :]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def build_table_flowable(rows: list) -> Table:
    col_count = max(len(r) for r in rows)
    # 列幅を均等分割（A4 本文幅 ≈ 170mm）
    col_width = 170 * mm / col_count

    table_data = []
    for ri, row in enumerate(rows):
        # 列数を揃える
        while len(row) < col_count:
            row.append("")
        if ri == 0:
            cell_paras = [
                Paragraph(f"<b>{esc(c)}</b>",
                          ParagraphStyle("th", fontName=SANS, fontSize=9,
                                         textColor=colors.white, leading=13))
                for c in row
            ]
        else:
            cell_paras = [
                Paragraph(inline(esc(c)),
                          ParagraphStyle("td", fontName=SERIF, fontSize=9,
                                         textColor=C_NAVY, leading=13))
                for c in row
            ]
        table_data.append(cell_paras)

    t = Table(table_data, colWidths=[col_width] * col_count)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), C_TABLE_HEAD),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), SANS),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_TABLE_EVEN]),
        ("GRID",       (0, 0), (-1, -1), 0.4, C_MGRAY),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def md_to_flowables(md_text: str, styles: dict) -> list:
    story = []
    lines = md_text.split("\n")
    i = 0
    in_code = False
    code_buf = []
    table_buf = []
    in_table = False

    while i < len(lines):
        line = lines[i]

        # --- コードブロック ---
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
                i += 1
                continue
            else:
                in_code = False
                code_text = "\n".join(code_buf)
                wrapped = []
                for cl in code_text.split("\n"):
                    wrapped.extend([cl[j:j+78] for j in range(0, max(1, len(cl)), 78)])
                story.append(Paragraph(
                    esc("\n".join(wrapped)).replace("\n", "<br/>"),
                    styles["code"]
                ))
                i += 1
                continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # --- テーブル ---
        if line.startswith("|"):
            table_buf.append(line)
            i += 1
            continue
        else:
            if table_buf:
                rows = parse_table(table_buf)
                if rows:
                    story.append(Spacer(1, 4))
                    story.append(build_table_flowable(rows))
                    story.append(Spacer(1, 8))
                table_buf = []

        # --- 空行 ---
        if line.strip() == "":
            story.append(Spacer(1, 5))
            i += 1
            continue

        # --- 水平線 ---
        if re.match(r"^[-*_]{3,}$", line.strip()):
            story.append(HRFlowable(width="100%", thickness=0.5,
                                     color=C_MGRAY, spaceBefore=6, spaceAfter=6))
            i += 1
            continue

        # --- 見出し ---
        if line.startswith("# ") and not line.startswith("##"):
            story.append(Paragraph(esc(line[2:].strip()), styles["h1"]))
            i += 1
            continue
        if line.startswith("## ") and not line.startswith("###"):
            story.append(HRFlowable(width="100%", thickness=1.5,
                                     color=C_BLUE, spaceBefore=14, spaceAfter=4))
            story.append(Paragraph(esc(line[3:].strip()), styles["h2"]))
            i += 1
            continue
        if line.startswith("### ") and not line.startswith("####"):
            story.append(Paragraph(esc(line[4:].strip()), styles["h3"]))
            i += 1
            continue
        if line.startswith("#### "):
            story.append(Paragraph(esc(line[5:].strip()), styles["h4"]))
            i += 1
            continue

        # --- メタ情報（**key**: value 形式の冒頭行）---
        if line.startswith("**") and line.count("**") >= 2 and ":" in line:
            story.append(Paragraph(inline(esc(line)), styles["meta"]))
            i += 1
            continue

        # --- 注記（*italic*）---
        if line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            text = line[1:-1]
            story.append(Paragraph(inline(esc(text)), styles["note"]))
            i += 1
            continue

        # --- 箇条書き（2段） ---
        m2 = re.match(r"^  [-*+] (.*)", line)
        if m2:
            story.append(Paragraph("　• " + inline(esc(m2.group(1))), styles["bullet2"]))
            i += 1
            continue

        # --- 箇条書き（1段） ---
        m1 = re.match(r"^[-*+] (.*)", line)
        if m1:
            story.append(Paragraph("• " + inline(esc(m1.group(1))), styles["bullet"]))
            i += 1
            continue

        # --- 番号付きリスト ---
        mn = re.match(r"^(\d+)\. (.*)", line)
        if mn:
            story.append(Paragraph(
                f"{mn.group(1)}. {inline(esc(mn.group(2)))}",
                styles["bullet"]
            ))
            i += 1
            continue

        # --- 通常テキスト ---
        story.append(Paragraph(inline(esc(line)), styles["body"]))
        i += 1

    # 末尾テーブルのフラッシュ
    if table_buf:
        rows = parse_table(table_buf)
        if rows:
            story.append(build_table_flowable(rows))

    return story


def build_report_pdf(md_path: str, output_path: str):
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()

    styles = make_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title="X アルゴリズム解説報告書",
        author="Claude (xai-org/x-algorithm リポジトリより)",
    )

    story = md_to_flowables(md_text, styles)
    doc.build(story)
    print(f"✅ 報告書 PDF 生成完了: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 report_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    build_report_pdf(sys.argv[1], sys.argv[2])
