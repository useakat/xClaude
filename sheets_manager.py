#!/usr/bin/env python3
"""Google Sheets manager for ポストネタ管理."""

import argparse
import os
import sys
from datetime import date

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ONE_POINT_SHEET = "onePointNeta"
NOTE_NETA_SHEET = "noteNeta"
NEWS_SHEET = "newsTopics"

ONE_POINT_HEADERS = ["No", "テーマ", "冒頭1行案", "身近さ接続", "仕組みのポイント", "感情的締め案", "難易度", "出典メモ", "ステータス", "追加日"]
NOTE_NETA_HEADERS = ["No", "タイトル案", "主人公(ミッション名)", "時代・背景", "危機の内容", "逆転のポイント", "科学的見どころ", "人間ドラマの核心", "記事展開のヒント", "難易度", "出典メモ", "ステータス", "追加日"]
NEWS_HEADERS = ["No", "カテゴリ", "タイトル", "概要", "ポイント", "ソース", "ステータス", "追加日"]


def get_client():
    creds_path = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcp", "charming-well-464402-u4-a7fefbac9372.json"),
    )
    if not os.path.exists(creds_path):
        print(f"エラー: 認証ファイルが見つかりません: {creds_path}", file=sys.stderr)
        print("セットアップ方法: SHEETS_SETUP.md を参照してください", file=sys.stderr)
        sys.exit(1)
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_sheet(spreadsheet, name, headers):
    try:
        ws = spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(headers))
        ws.append_row(headers)
        print(f"シート '{name}' を作成しました")
    return ws


def next_no(ws):
    values = ws.col_values(1)
    nums = [int(v) for v in values[1:] if str(v).isdigit()]
    return max(nums) + 1 if nums else 1


def cmd_add_one_point(args):
    client = get_client()
    ss = client.open_by_key(SPREADSHEET_ID)
    ws = get_or_create_sheet(ss, ONE_POINT_SHEET, ONE_POINT_HEADERS)
    no = next_no(ws)
    row = [
        no,
        args.theme,
        args.hook,
        args.connection,
        args.mechanism,
        args.closing,
        args.difficulty,
        args.source,
        "未使用",
        str(date.today()),
    ]
    ws.append_row(row)
    print(f"✓ onePointNeta に追加: No.{no} 「{args.theme}」")


def cmd_add_note_neta(args):
    client = get_client()
    ss = client.open_by_key(SPREADSHEET_ID)
    ws = get_or_create_sheet(ss, NOTE_NETA_SHEET, NOTE_NETA_HEADERS)
    no = next_no(ws)
    row = [
        no,
        args.title,
        args.mission,
        args.era,
        args.crisis,
        args.turning_point,
        args.science,
        args.drama,
        args.structure,
        args.difficulty,
        args.source,
        "未使用",
        str(date.today()),
    ]
    ws.append_row(row)
    print(f"✓ noteNeta に追加: No.{no} 「{args.title}」")


def cmd_add_news(args):
    client = get_client()
    ss = client.open_by_key(SPREADSHEET_ID)
    ws = get_or_create_sheet(ss, NEWS_SHEET, NEWS_HEADERS)
    no = next_no(ws)
    row = [
        no,
        args.category,
        args.title,
        args.summary,
        args.point,
        args.source,
        "未使用",
        str(date.today()),
    ]
    ws.append_row(row)
    print(f"✓ newsTopics に追加: No.{no} 「{args.title}」")


def cmd_list(args):
    client = get_client()
    ss = client.open_by_key(SPREADSHEET_ID)
    sheet_map = {
        "one-point": ONE_POINT_SHEET,
        "note-neta": NOTE_NETA_SHEET,
        "news": NEWS_SHEET,
    }
    sheet_name = sheet_map.get(args.sheet)
    if not sheet_name:
        print(f"エラー: 不明なシート '{args.sheet}'. one-point / note-neta / news を指定してください")
        sys.exit(1)
    try:
        ws = ss.worksheet(sheet_name)
        records = ws.get_all_records()
        if not records:
            print(f"{sheet_name}: データなし")
            return
        for r in records:
            status = r.get("ステータス", "")
            if args.unused_only and status != "未使用":
                continue
            no = r.get("No", "?")
            if getattr(args, "full", False):
                print(f"\n--- No.{no} [{status}] ---")
                for k, v in r.items():
                    if k not in ("No", "ステータス", "追加日") and v:
                        print(f"{k}: {v}")
            else:
                title = r.get("タイトル案") or r.get("テーマ") or r.get("タイトル") or "?"
                print(f"No.{no} [{status}] {title}")
    except gspread.WorksheetNotFound:
        print(f"シート '{sheet_name}' が見つかりません")


def cmd_mark_used(args):
    client = get_client()
    ss = client.open_by_key(SPREADSHEET_ID)
    sheet_map = {
        "one-point": ONE_POINT_SHEET,
        "note-neta": NOTE_NETA_SHEET,
        "news": NEWS_SHEET,
    }
    sheet_name = sheet_map.get(args.sheet)
    if not sheet_name:
        print(f"エラー: 不明なシート '{args.sheet}'")
        sys.exit(1)
    try:
        ws = ss.worksheet(sheet_name)
        headers = ws.row_values(1)
        status_col = headers.index("ステータス") + 1
        no_col = headers.index("No") + 1
        no_values = ws.col_values(no_col)
        for i, v in enumerate(no_values):
            if str(v) == str(args.no):
                row_idx = i + 1
                ws.update_cell(row_idx, status_col, "使用済み")
                print(f"✓ No.{args.no} を「使用済み」に更新しました")
                return
        print(f"エラー: No.{args.no} が見つかりません")
        sys.exit(1)
    except gspread.WorksheetNotFound:
        print(f"シート '{sheet_name}' が見つかりません")
        sys.exit(1)


def cmd_migrate(args):
    """既存ファイルからスプレッドシートへ移行."""
    import csv
    import re

    base = os.path.dirname(os.path.abspath(__file__))
    client = get_client()
    ss = client.open_by_key(SPREADSHEET_ID)

    # --- onePointNeta.md ---
    one_point_path = os.path.join(base, "onePointNeta.md")
    if os.path.exists(one_point_path):
        ws = get_or_create_sheet(ss, ONE_POINT_SHEET, ONE_POINT_HEADERS)
        existing = ws.col_values(2)[1:]  # テーマ列
        with open(one_point_path, encoding="utf-8") as f:
            content = f.read()
        blocks = re.split(r"\n---\n", content)
        count = 0
        for block in blocks:
            if "**ネタ [" not in block:
                continue
            def g(field):
                m = re.search(rf"{field}: (.+)", block)
                return m.group(1).strip() if m else ""
            theme = g("テーマ")
            if not theme or theme in existing:
                continue
            no = next_no(ws)
            ws.append_row([
                no, theme, g("冒頭1行案"), g("身近さ接続"),
                g("仕組みのポイント"), g("感情的締め案"), g("難易度"),
                g("出典メモ"), "未使用", str(date.today()),
            ])
            existing.append(theme)
            count += 1
        print(f"✓ onePointNeta: {count}件 移行完了")

    # --- noteNeta.md ---
    note_neta_path = os.path.join(base, "noteNeta.md")
    if os.path.exists(note_neta_path):
        ws = get_or_create_sheet(ss, NOTE_NETA_SHEET, NOTE_NETA_HEADERS)
        existing = ws.col_values(2)[1:]  # タイトル案列
        with open(note_neta_path, encoding="utf-8") as f:
            content = f.read()
        blocks = re.split(r"\n---\n", content)
        count = 0
        for block in blocks:
            if "**ネタ " not in block:
                continue
            def g(field):
                m = re.search(rf"{re.escape(field)}: (.+)", block)
                return m.group(1).strip() if m else ""
            title = g("タイトル案")
            if not title or title in existing:
                continue
            no = next_no(ws)
            ws.append_row([
                no, title,
                g("主人公（ミッション名）"),
                g("時代・背景"),
                g("危機の内容"),
                g("逆転のポイント"),
                g("科学的見どころ"),
                g("人間ドラマの核心"),
                g("記事展開のヒント"),
                g("難易度（記事化）"),
                g("出典メモ"),
                "未使用", str(date.today()),
            ])
            existing.append(title)
            count += 1
        print(f"✓ noteNeta: {count}件 移行完了")

    # --- news-topics.csv ---
    news_path = os.path.join(base, "news-topics.csv")
    if os.path.exists(news_path):
        ws = get_or_create_sheet(ss, NEWS_SHEET, NEWS_HEADERS)
        existing_titles = ws.col_values(3)[1:]  # タイトル列
        count = 0
        with open(news_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get("タイトル", "")
                if not title or title in existing_titles:
                    continue
                no = next_no(ws)
                ws.append_row([
                    no,
                    row.get("カテゴリ", ""),
                    title,
                    row.get("概要", ""),
                    row.get("ポイント", ""),
                    row.get("ソース", ""),
                    "未使用",
                    str(date.today()),
                ])
                existing_titles.append(title)
                count += 1
        print(f"✓ newsTopics: {count}件 移行完了")

    print("\n移行完了！")


def main():
    parser = argparse.ArgumentParser(description="ポストネタ Google Sheets 管理ツール")
    sub = parser.add_subparsers(dest="command")

    # add one-point
    p1 = sub.add_parser("add-one-point", help="科学トリビアネタを追加")
    p1.add_argument("--theme", required=True, help="テーマ（例: スマホGPS × 相対性理論）")
    p1.add_argument("--hook", required=True, help="冒頭1行案")
    p1.add_argument("--connection", required=True, help="身近さ接続")
    p1.add_argument("--mechanism", required=True, help="仕組みのポイント")
    p1.add_argument("--closing", required=True, help="感情的締め案")
    p1.add_argument("--difficulty", default="易", help="難易度: 易/中/難")
    p1.add_argument("--source", default="", help="出典メモ")

    # add note-neta
    p2 = sub.add_parser("add-note-neta", help="note記事ネタを追加")
    p2.add_argument("--title", required=True, help="タイトル案")
    p2.add_argument("--mission", required=True, help="主人公(ミッション名)")
    p2.add_argument("--era", required=True, help="時代・背景")
    p2.add_argument("--crisis", required=True, help="危機の内容")
    p2.add_argument("--turning-point", required=True, help="逆転のポイント")
    p2.add_argument("--science", required=True, help="科学的見どころ")
    p2.add_argument("--drama", required=True, help="人間ドラマの核心")
    p2.add_argument("--structure", required=True, help="記事展開のヒント")
    p2.add_argument("--difficulty", default="中", help="難易度: 易/中/難")
    p2.add_argument("--source", default="", help="出典メモ")

    # add news
    p3 = sub.add_parser("add-news", help="ニュースネタを追加")
    p3.add_argument("--category", required=True, help="カテゴリ")
    p3.add_argument("--title", required=True, help="タイトル")
    p3.add_argument("--summary", required=True, help="概要")
    p3.add_argument("--point", required=True, help="ポイント")
    p3.add_argument("--source", default="", help="ソース(URL)")

    # list
    p4 = sub.add_parser("list", help="ネタ一覧を表示")
    p4.add_argument("sheet", choices=["one-point", "note-neta", "news"], help="シート名")
    p4.add_argument("--unused-only", action="store_true", help="未使用のみ表示")
    p4.add_argument("--full", action="store_true", help="全フィールドを表示")

    # mark-used
    p5 = sub.add_parser("mark-used", help="ネタを使用済みにする")
    p5.add_argument("sheet", choices=["one-point", "note-neta", "news"], help="シート名")
    p5.add_argument("no", type=int, help="No番号")

    # migrate
    sub.add_parser("migrate", help="既存ファイルからシートへ一括移行")

    args = parser.parse_args()
    if args.command == "add-one-point":
        cmd_add_one_point(args)
    elif args.command == "add-note-neta":
        cmd_add_note_neta(args)
    elif args.command == "add-news":
        cmd_add_news(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "mark-used":
        cmd_mark_used(args)
    elif args.command == "migrate":
        cmd_migrate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
