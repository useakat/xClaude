#!/usr/bin/env python3
"""ポストネタ管理ツール（database/ CSV ファイルを読み書き）."""

import argparse
import csv
import os
import sys
from datetime import date
from pathlib import Path

DB_DIR = Path(__file__).parent.parent / "database"

ONE_POINT_FILE = DB_DIR / "onePointNeta.csv"
NOTE_NETA_FILE = DB_DIR / "noteNeta.csv"
NEWS_FILE = DB_DIR / "newsTopics.csv"

ONE_POINT_HEADERS = ["No", "テーマ", "冒頭1行案", "身近さ接続", "仕組みのポイント", "感情的締め案", "難易度", "出典メモ", "ステータス", "追加日"]
NOTE_NETA_HEADERS = ["No", "タイトル案", "主人公(ミッション名)", "時代・背景", "危機の内容", "逆転のポイント", "科学的見どころ", "人間ドラマの核心", "記事展開のヒント", "難易度", "出典メモ", "ステータス", "追加日"]
NEWS_HEADERS = ["No", "カテゴリ", "タイトル", "概要", "ポイント", "ソース", "ステータス", "追加日"]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], headers: list[str]):
    DB_DIR.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def next_no(rows: list[dict]) -> int:
    nums = [int(r["No"]) for r in rows if str(r.get("No", "")).isdigit()]
    return max(nums) + 1 if nums else 1


def cmd_add_one_point(args):
    rows = read_csv(ONE_POINT_FILE)
    no = next_no(rows)
    rows.append({
        "No": no, "テーマ": args.theme, "冒頭1行案": args.hook,
        "身近さ接続": args.connection, "仕組みのポイント": args.mechanism,
        "感情的締め案": args.closing, "難易度": args.difficulty,
        "出典メモ": args.source, "ステータス": "未使用", "追加日": str(date.today()),
    })
    write_csv(ONE_POINT_FILE, rows, ONE_POINT_HEADERS)
    print(f"✓ onePointNeta に追加: No.{no} 「{args.theme}」")


def cmd_add_note_neta(args):
    rows = read_csv(NOTE_NETA_FILE)
    no = next_no(rows)
    rows.append({
        "No": no, "タイトル案": args.title, "主人公(ミッション名)": args.mission,
        "時代・背景": args.era, "危機の内容": args.crisis,
        "逆転のポイント": args.turning_point, "科学的見どころ": args.science,
        "人間ドラマの核心": args.drama, "記事展開のヒント": args.structure,
        "難易度": args.difficulty, "出典メモ": args.source,
        "ステータス": "未使用", "追加日": str(date.today()),
    })
    write_csv(NOTE_NETA_FILE, rows, NOTE_NETA_HEADERS)
    print(f"✓ noteNeta に追加: No.{no} 「{args.title}」")


def cmd_add_news(args):
    rows = read_csv(NEWS_FILE)
    no = next_no(rows)
    rows.append({
        "No": no, "カテゴリ": args.category, "タイトル": args.title,
        "概要": args.summary, "ポイント": args.point, "ソース": args.source,
        "ステータス": "未使用", "追加日": str(date.today()),
    })
    write_csv(NEWS_FILE, rows, NEWS_HEADERS)
    print(f"✓ newsTopics に追加: No.{no} 「{args.title}」")


def cmd_list(args):
    file_map = {"one-point": ONE_POINT_FILE, "note-neta": NOTE_NETA_FILE, "news": NEWS_FILE}
    path = file_map.get(args.sheet)
    rows = read_csv(path)
    if not rows:
        print(f"{args.sheet}: データなし")
        return
    for r in rows:
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


def cmd_mark_used(args):
    file_map = {"one-point": ONE_POINT_FILE, "note-neta": NOTE_NETA_FILE, "news": NEWS_FILE}
    headers_map = {
        "one-point": ONE_POINT_HEADERS,
        "note-neta": NOTE_NETA_HEADERS,
        "news": NEWS_HEADERS,
    }
    path = file_map.get(args.sheet)
    rows = read_csv(path)
    for r in rows:
        if str(r.get("No")) == str(args.no):
            r["ステータス"] = "使用済み"
            write_csv(path, rows, headers_map[args.sheet])
            print(f"✓ No.{args.no} を「使用済み」に更新しました")
            return
    print(f"エラー: No.{args.no} が見つかりません")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="ポストネタ管理ツール")
    sub = parser.add_subparsers(dest="command")

    p1 = sub.add_parser("add-one-point")
    p1.add_argument("--theme", required=True)
    p1.add_argument("--hook", required=True)
    p1.add_argument("--connection", required=True)
    p1.add_argument("--mechanism", required=True)
    p1.add_argument("--closing", required=True)
    p1.add_argument("--difficulty", default="易")
    p1.add_argument("--source", default="")

    p2 = sub.add_parser("add-note-neta")
    p2.add_argument("--title", required=True)
    p2.add_argument("--mission", required=True)
    p2.add_argument("--era", required=True)
    p2.add_argument("--crisis", required=True)
    p2.add_argument("--turning-point", required=True)
    p2.add_argument("--science", required=True)
    p2.add_argument("--drama", required=True)
    p2.add_argument("--structure", required=True)
    p2.add_argument("--difficulty", default="中")
    p2.add_argument("--source", default="")

    p3 = sub.add_parser("add-news")
    p3.add_argument("--category", required=True)
    p3.add_argument("--title", required=True)
    p3.add_argument("--summary", required=True)
    p3.add_argument("--point", required=True)
    p3.add_argument("--source", default="")

    p4 = sub.add_parser("list")
    p4.add_argument("sheet", choices=["one-point", "note-neta", "news"])
    p4.add_argument("--unused-only", action="store_true")
    p4.add_argument("--full", action="store_true")

    p5 = sub.add_parser("mark-used")
    p5.add_argument("sheet", choices=["one-point", "note-neta", "news"])
    p5.add_argument("no", type=int)

    args = parser.parse_args()
    cmd_map = {
        "add-one-point": cmd_add_one_point,
        "add-note-neta": cmd_add_note_neta,
        "add-news": cmd_add_news,
        "list": cmd_list,
        "mark-used": cmd_mark_used,
    }
    if args.command not in cmd_map:
        parser.print_help()
        return
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
