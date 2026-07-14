#!/usr/bin/env python3
"""X投稿一覧シートから未転載の投稿をランダムに1件選び、【threads投稿】形式の
Gmail 下書きを作成する。過去の X 投稿を Threads へ転載する運用の起点。

フロー:
  1. 発信記録スプレッドシートの「X投稿一覧」を全取得
  2. 候補抽出: ポスト種類=通常ツイート / 目的=有益 / 親ポストURL 空 / threads転載日 空 / 本文あり
  3. ランダムに --count 件選択(重複なし)
  4. セルフリプ(親ポストURL が選択投稿を指す行)があれば先頭1件を [リプ] に取り込む
  5. 【threads投稿】メール本文を組み立て([投稿文]/[画像URL]/[リプ]/[リプ画像URL]/[XURL])
     → create_gmail_draft.sh で Gmail 下書き作成。[XURL]=元X投稿URL(outputs の x_url 記録用)
  6. 成功したら選択行の「threads転載日」に当日日付を記録(重複防止マーク)

- この VPS は IPv6 が通らないため DNS を IPv4 固定する(gspread のハング回避)。
- 画像は pbs.twimg.com URL を [画像URL] タグで渡す(Threads はそのまま参照)。添付はしない。

Usage:
  python3 scripts/make_threads_draft.py [--dry-run] [--count N]
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from datetime import datetime

# --- IPv4 固定(IPv6 が通らない環境でのハング回避)---
_orig_getaddrinfo = __import__("socket").getaddrinfo
def _ipv4_only(*args, **kwargs):
    import socket
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
__import__("socket").getaddrinfo = _ipv4_only

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
SHEET_NAME = "X投稿一覧"
MARKER_HEADER = "threads転載日"
DRAFT_TO = "useakat@gmail.com"
CREATE_DRAFT_SH = os.path.join(ROOT, "scripts", "create_gmail_draft.sh")

# 期待するヘッダ名(列位置はヘッダ名で解決する)
COL = {
    "投稿日時": None, "ポストURL": None, "ポスト本文": None,
    "ポスト種類": None, "画像URL": None, "親ポストURL": None, "目的": None,
}


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def get_ws():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if key_json:
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
    else:
        sa = os.path.join(ROOT, "gcp", "charming-well-464402-u4-2cfb7bddf343.json")
        creds = Credentials.from_service_account_file(sa, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)


def status_id(url):
    """ツイート URL から status ID(数字)を抽出。突合用に URL 表記の揺れを吸収する。"""
    if not url:
        return ""
    m = re.search(r"status/(\d+)", url)
    return m.group(1) if m else url.strip()


def ensure_marker_col(ws, header):
    """threads転載日 列を確保し、その列番号(1-based)を返す。無ければ列を足してヘッダを書く。"""
    if MARKER_HEADER in header:
        return header.index(MARKER_HEADER) + 1
    marker_col = len(header) + 1
    if marker_col > ws.col_count:
        ws.add_cols(marker_col - ws.col_count)
    ws.update_cell(1, marker_col, MARKER_HEADER)
    log(f"'{MARKER_HEADER}' 列を新設(列 {marker_col})")
    return marker_col


def cell(row, idx):
    return row[idx].strip() if idx is not None and idx < len(row) and row[idx] else ""


def build_body(text, img, rep_text, rep_img, post_url):
    parts = [f"[投稿文]{text}[/投稿文]"]
    if img:
        parts.append(f"[画像URL]{img}[/画像URL]")
    if rep_text:
        parts.append(f"[リプ]{rep_text}[/リプ]")
        if rep_img:
            parts.append(f"[リプ画像URL]{rep_img}[/リプ画像URL]")
    if post_url:
        # 元X投稿URL。outputs の x_url(H) に記録され、日報のカテゴリ判定に使われる
        parts.append(f"[XURL]{post_url}[/XURL]")
    return "\n".join(parts) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="選択と本文を表示するだけで下書き作成・マークをしない")
    ap.add_argument("--count", type=int, default=1, help="作成する下書きの件数(重複なしで選択)")
    args = ap.parse_args()

    ws = get_ws()
    values = ws.get_all_values()
    if not values:
        log("シートが空です。終了。")
        return
    header = values[0]
    for name in COL:
        COL[name] = header.index(name) if name in header else None
    missing = [n for n in COL if COL[n] is None]
    if missing:
        log(f"必須列が見つかりません: {missing}。終了。")
        sys.exit(1)
    marker_col = ensure_marker_col(ws, header)
    marker_idx = marker_col - 1

    rows = values[1:]  # 2行目以降
    # 親ポストURL(status ID) → 子行リスト(セルフリプ探索用)
    children = {}
    for i, row in enumerate(rows, start=2):
        parent = status_id(cell(row, COL["親ポストURL"]))
        if parent:
            children.setdefault(parent, []).append((i, row))

    # 候補: 通常ツイート / 目的=有益 / 親ポストURL 空 / マーク空 / 本文あり
    candidates = []
    for i, row in enumerate(rows, start=2):
        if cell(row, COL["ポスト種類"]) != "通常ツイート":
            continue
        if cell(row, COL["目的"]) != "有益":
            continue
        if cell(row, COL["親ポストURL"]):
            continue
        if cell(row, marker_idx):
            continue
        if not cell(row, COL["ポスト本文"]):
            continue
        candidates.append((i, row))

    log(f"候補 {len(candidates)} 件(全 {len(rows)} 行中)")
    if not candidates:
        log("転載候補がありません(全件転載済みの可能性)。終了。")
        return

    count = min(args.count, len(candidates))
    if count < args.count:
        log(f"注記: 候補不足のため {args.count} 件中 {count} 件のみ作成します。")
    picks = random.sample(candidates, count)

    today = datetime.now().strftime("%Y-%m-%d")
    made = 0
    for row_no, row in picks:
        text = cell(row, COL["ポスト本文"])
        img = cell(row, COL["画像URL"])
        post_url = cell(row, COL["ポストURL"])
        sid = status_id(post_url)

        # セルフリプ: 選択投稿を親に持つ行を投稿日時昇順で並べ、先頭1件を取り込む
        rep_text = rep_img = ""
        kids = children.get(sid, [])
        if kids:
            kids_sorted = sorted(kids, key=lambda t: cell(t[1], COL["投稿日時"]))
            _, kid_row = kids_sorted[0]
            rep_text = cell(kid_row, COL["ポスト本文"])
            rep_img = cell(kid_row, COL["画像URL"])
            if len(kids) > 1:
                log(f"注記: セルフリプが {len(kids)} 件。先頭1件のみ取り込みます(v1 制約)。")

        body = build_body(text, img, rep_text, rep_img, post_url)
        subject = "【threads投稿】" + text.replace("\n", " ")[:20]

        log(f"選択: 行{row_no} {post_url}")
        log(f"  本文 {len(text)}字 / 画像 {'あり' if img else 'なし'} / セルフリプ {'あり' if rep_text else 'なし'}")

        if args.dry_run:
            print("SUBJECT:", subject)
            print("----- BODY -----")
            print(body)
            continue

        # Gmail 下書き作成
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

        # 重複防止マーク(選択行の threads転載日 に当日日付)
        ws.update_cell(row_no, marker_col, today)
        log(f"✓ マーク: 行{row_no} {MARKER_HEADER} = {today}")
        made += 1

    if args.dry_run:
        log(f"--- dry-run: {count} 件を選択(下書き作成・マークはしません) ---")
    else:
        log(f"✓ 完了: 下書き {made} 件作成")


if __name__ == "__main__":
    main()
