#!/usr/bin/env python3
"""Threads の低 views 期（2026/07/24〜09/23）の本体投稿を古い順に 1 本ずつ再投稿するため、
【threads投稿】形式の Gmail 下書きを作る。毎日 18:00 の cron から 1 本ずつ。

背景: この期間は本体投稿 98 本がすべて 2 桁 views に抑えられていた（9/24 から回復）。
      同じ内容を順番に再投稿して本来の反応を取り直す（2026-11-11 計画）。

フロー:
  1. キュー logs/threads_repost_queue.csv を読む（無ければ --init で Threads投稿一覧から生成）
  2. 再投稿済みの検出: キュー開始日以降の本体投稿のうち本文冒頭 60 字が一致する行を
     「再投稿URL」に書く（元 views と再投稿 views を後から比べるため）
  3. 「下書き作成日」が空の先頭 1 行を選ぶ
  4. 続きのセルフリプ（親投稿URL が本体に連なる自分のリプ）を時系列に集め、
     http を含むものを除外し、複数なら「=====」行で連結（post_threads.py がそこで切って返信チェーンにする）
  5. [メモ]（タグ外。post_threads_from_email.sh は無視）＋ [投稿文]/[画像URL]/[リプ]/[リプ画像URL]
     を create_gmail_draft.sh で下書きにする。[XURL] は付けない（X の投稿ではない）
  6. キューの「下書き作成日」に当日日付を書く

画像: シートの F 列（Instagram CDN の署名付き URL、約 4 日で失効。毎朝 05:00 の fetch が更新する）を
      下書き作成時点の値で渡す。失効して投稿に失敗したら --redo N で作り直す。
      CAROUSEL_ALBUM は 1 枚分の URL しか無いので 1 枚画像として投稿する（メモに注記）。

Usage:
  python3 scripts/make_threads_repost_draft.py            # cron: 次の 1 本の下書きを作る
  python3 scripts/make_threads_repost_draft.py --init     # キューを生成（既存があれば何もしない）
  python3 scripts/make_threads_repost_draft.py --redo 5   # 順番 5 の下書きを作り直す
  python3 scripts/make_threads_repost_draft.py --dry-run  # 件名・本文を表示するだけ
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_threads_draft import CREATE_DRAFT_SH, DRAFT_TO, build_body, cell  # noqa: E402  (IPv4 固定もここで入る)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
SHEET_NAME = "Threads投稿一覧"
QUEUE_PATH = os.path.join(ROOT, "logs", "threads_repost_queue.csv")
QUEUE_COLS = ["順番", "元投稿URL", "元投稿日時", "種類", "画像", "元views", "下書き作成日", "再投稿URL"]

PERIOD_FROM = "2026/07/24"
PERIOD_TO = "2026/09/23"
SPLIT_MARKER = "====="
MATCH_HEAD = 60      # 再投稿の突合に使う本文冒頭の字数
TIME_WORDS = ["今日", "今夜", "今朝", "昨日", "明日", "今週", "今月", "先週", "先月", "速報", "さっき", "現在", "この夏", "この冬"]

COL = {"投稿日時": None, "投稿URL": None, "本文": None, "種類": None, "画像URL": None, "親投稿URL": None, "views": None}


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def get_rows():
    import json
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if key_json:
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
    else:
        sa = os.path.join(ROOT, "gcp", "charming-well-464402-u4-2cfb7bddf343.json")
        creds = Credentials.from_service_account_file(sa, scopes=scopes)
    ws = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    values = ws.get_all_values()
    if not values:
        log("シートが空です。終了。")
        sys.exit(1)
    header = values[0]
    for name in COL:
        COL[name] = header.index(name) if name in header else None
    missing = [n for n in COL if COL[n] is None]
    if missing:
        log(f"必須列が見つかりません: {missing}。終了。")
        sys.exit(1)
    return values[1:]


def load_queue():
    if not os.path.exists(QUEUE_PATH):
        return []
    with open(QUEUE_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_queue(queue):
    with open(QUEUE_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=QUEUE_COLS)
        w.writeheader()
        w.writerows(queue)


def init_queue(rows, dry_run):
    if os.path.exists(QUEUE_PATH):
        log(f"キューは既にあります（{QUEUE_PATH}）。--init は何もしません。")
        return
    tops = [r for r in rows
            if PERIOD_FROM <= cell(r, COL["投稿日時"])[:10] <= PERIOD_TO and not cell(r, COL["親投稿URL"])]
    tops.sort(key=lambda r: cell(r, COL["投稿日時"]))
    queue = []
    for i, r in enumerate(tops, start=1):
        queue.append({
            "順番": str(i), "元投稿URL": cell(r, COL["投稿URL"]), "元投稿日時": cell(r, COL["投稿日時"]),
            "種類": cell(r, COL["種類"]), "画像": "あり" if cell(r, COL["画像URL"]) else "",
            "元views": cell(r, COL["views"]), "下書き作成日": "", "再投稿URL": "",
        })
    log(f"キュー候補 {len(queue)} 件（{PERIOD_FROM}〜{PERIOD_TO} の本体投稿）")
    for q in queue:
        print(f"  {q['順番']:>3} {q['元投稿日時']} {q['種類']:<14} 画像{q['画像'] or 'なし'} views={q['元views']}")
    if dry_run:
        log("--- dry-run: キューは書きません ---")
        return
    save_queue(queue)
    log(f"✓ キュー作成: {QUEUE_PATH}")


def collect_replies(url, by_parent, by_url):
    """本体 url に連なる自分の続きリプを時系列で返す（リプへのリプも辿る）。"""
    out = []
    stack = [url]
    seen = set()
    while stack:
        p = stack.pop()
        kids = sorted(by_parent.get(p, []), key=lambda r: cell(r, COL["投稿日時"]))
        for k in kids:
            ku = cell(k, COL["投稿URL"])
            if ku in seen:
                continue
            seen.add(ku)
            out.append(k)
            stack.append(ku)
    return sorted(out, key=lambda r: cell(r, COL["投稿日時"]))


def mark_reposted(queue, rows):
    """キュー開始日以降の本体投稿を本文冒頭で突き合わせ、再投稿URL を埋める。"""
    started = min((q["下書き作成日"] for q in queue if q["下書き作成日"]), default="")
    if not started:
        return 0
    by_url = {cell(r, COL["投稿URL"]): r for r in rows}
    recent = [r for r in rows
              if cell(r, COL["投稿日時"])[:10].replace("/", "-") >= started and not cell(r, COL["親投稿URL"])]
    n = 0
    for q in queue:
        if q["再投稿URL"] or not q["下書き作成日"]:
            continue
        orig = by_url.get(q["元投稿URL"])
        if orig is None:
            continue
        head = cell(orig, COL["本文"])[:MATCH_HEAD]
        for r in recent:
            if cell(r, COL["投稿URL"]) != q["元投稿URL"] and cell(r, COL["本文"])[:MATCH_HEAD] == head:
                q["再投稿URL"] = cell(r, COL["投稿URL"])
                log(f"再投稿を検出: 順番{q['順番']} → {q['再投稿URL']}（views={cell(r, COL['views'])}）")
                n += 1
                break
    return n


def build_draft(q, rows, total):
    by_url = {cell(r, COL["投稿URL"]): r for r in rows}
    by_parent = {}
    for r in rows:
        p = cell(r, COL["親投稿URL"])
        if p:
            by_parent.setdefault(p, []).append(r)

    orig = by_url.get(q["元投稿URL"])
    if orig is None:
        log(f"元投稿がシートに見つかりません: {q['元投稿URL']}")
        sys.exit(1)
    text = cell(orig, COL["本文"])
    img = cell(orig, COL["画像URL"])
    kind = cell(orig, COL["種類"])

    reps = collect_replies(q["元投稿URL"], by_parent, by_url)
    rep_texts, rep_img, dropped = [], "", 0
    for k in reps:
        t = cell(k, COL["本文"])
        if "http" in t.lower():
            dropped += 1
            continue
        rep_texts.append(t)
        if not rep_img:
            rep_img = cell(k, COL["画像URL"])
    rep_text = f"\n\n{SPLIT_MARKER}\n\n".join(rep_texts)

    notes = [f"順番 {q['順番']}/{total}", f"元投稿: {q['元投稿URL']}",
             f"元投稿日時: {q['元投稿日時']} / 元views: {q['元views']}"]
    hit = [w for w in TIME_WORDS if w in text or w in rep_text]
    if hit:
        notes.append("時期依存の語あり（要確認）: " + "・".join(hit))
    if kind == "CAROUSEL_ALBUM":
        notes.append("元は複数枚画像。シートには 1 枚目の URL しか無いので 1 枚で投稿")
    if rep_texts:
        # メモ内にタグ文字列（[リプ] など）を書くと extract_tag.py が誤って拾うので書かない
        notes.append(f"続きリプ {len(rep_texts)} 件をセルフリプとして連結" + (f"（リンク入り {dropped} 件は除外）" if dropped else ""))
    elif dropped:
        notes.append(f"続きリプはリンク入りのみ {dropped} 件のため付けない")
    memo = "[メモ]\n" + "\n".join(notes) + "\n[/メモ]\n\n"

    body = memo + build_body(text, img, rep_text, rep_img, "")
    subject = "【threads投稿】" + text.replace("\n", " ")[:20]
    return subject, body, {"text": text, "img": img, "reps": len(rep_texts)}


def create_draft(subject, body):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_file = f.name
    try:
        res = subprocess.run(
            ["bash", CREATE_DRAFT_SH, "--to", DRAFT_TO, "--subject", subject, "--body-file", body_file],
            capture_output=True, text=True,
        )
        if res.returncode != 0:
            log(f"下書き作成に失敗: {res.stderr.strip() or res.stdout.strip()}")
            sys.exit(1)
        log(res.stdout.strip())
    finally:
        os.unlink(body_file)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true", help="キューを Threads投稿一覧 から生成する")
    ap.add_argument("--redo", type=int, default=0, help="順番 N の下書きを作り直す")
    ap.add_argument("--dry-run", action="store_true", help="下書き作成・キュー更新をしない")
    args = ap.parse_args()

    rows = get_rows()
    if args.init:
        init_queue(rows, args.dry_run)
        return

    queue = load_queue()
    if not queue:
        log(f"キューがありません。先に --init を実行してください（{QUEUE_PATH}）")
        sys.exit(1)

    n = mark_reposted(queue, rows)
    if n and not args.dry_run:
        save_queue(queue)

    if args.redo:
        picks = [q for q in queue if q["順番"] == str(args.redo)]
        if not picks:
            log(f"順番 {args.redo} はキューにありません")
            sys.exit(1)
    else:
        picks = [q for q in queue if not q["下書き作成日"]][:1]
        if not picks:
            log("未作成の行がありません（全件の下書き作成済み）。終了")
            return
    q = picks[0]

    subject, body, info = build_draft(q, rows, len(queue))
    log(f"選択: 順番{q['順番']} {q['元投稿日時']} {q['元投稿URL']}")
    log(f"  本文 {len(info['text'])}字 / 画像 {'あり' if info['img'] else 'なし'} / 続きリプ {info['reps']} 件")

    if args.dry_run:
        print("SUBJECT:", subject)
        print("----- BODY -----")
        print(body)
        log("--- dry-run: 下書き作成・キュー更新はしません ---")
        return

    create_draft(subject, body)
    q["下書き作成日"] = datetime.now().strftime("%Y-%m-%d")
    save_queue(queue)
    log(f"✓ 完了: 順番{q['順番']} の下書きを作成、キュー更新")


if __name__ == "__main__":
    main()
