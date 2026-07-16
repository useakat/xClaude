#!/usr/bin/env python3
"""X投稿一覧シートの「親ポストURL」(J列) を X syndication API で補完する。

セルフリプ検出（make_threads_draft.py）は親ポストURL頼りだが、大半の行が未記入のため、
リプライ関係が紐づかない問題があった。各行のツイートを認証不要の syndication API で引き、
`in_reply_to_status_id_str` が返れば親ポストURLを書き込む（空欄のみ補完・既存値は上書きしない）。

- リプライでない/取得不可(削除済み等)だった ID は logs/parent_backfill_cache.json に
  記録し、再実行時はスキップする（毎朝の cron 前段で走らせても新規行しか叩かない）。
- この VPS は IPv6 が通らないため DNS を IPv4 固定する。

Usage:
  python3 scripts/backfill_x_parent_urls.py [--dry-run] [--limit N]
"""
import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
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
CACHE_PATH = os.path.join(ROOT, "logs", "parent_backfill_cache.json")
API = "https://cdn.syndication.twimg.com/tweet-result?id={sid}&lang=ja&token=a"


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
    m = re.search(r"status/(\d+)", url or "")
    return m.group(1) if m else ""


def load_cache():
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return set(json.load(f))
    except (OSError, ValueError):
        return set()


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(cache), f)


def fetch_parent_id(sid):
    """親ツイートIDを返す。リプライでなければ ""、取得不可なら None。"""
    req = urllib.request.Request(API.format(sid=sid), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TimeoutError):
        return None
    if not isinstance(d, dict) or d.get("__typename") == "TweetTombstone":
        return None
    return d.get("in_reply_to_status_id_str") or ""


def col_letter(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="書き込まず対応表を表示")
    ap.add_argument("--limit", type=int, default=0, help="API 呼び出し数の上限(テスト用)")
    args = ap.parse_args()

    ws = get_ws()
    values = ws.get_all_values()
    header = values[0]
    url_i = header.index("ポストURL")
    parent_i = header.index("親ポストURL")
    parent_col = col_letter(parent_i + 1)

    cache = load_cache()
    targets = []
    for row_no, row in enumerate(values[1:], start=2):
        url = row[url_i].strip() if url_i < len(row) else ""
        parent = row[parent_i].strip() if parent_i < len(row) else ""
        sid = status_id(url)
        if sid and not parent and sid not in cache:
            targets.append((row_no, sid))

    log(f"対象: {len(targets)} 行(親ポストURL空・キャッシュ外) / キャッシュ済み {len(cache)} 件")
    if args.limit:
        targets = targets[: args.limit]

    updates = []
    misses = 0
    for row_no, sid in targets:
        pid = fetch_parent_id(sid)
        if pid:
            purl = f"https://twitter.com/i/web/status/{pid}"
            updates.append({"range": f"{parent_col}{row_no}", "values": [[purl]]})
            log(f"  行{row_no}: 親={pid}")
        else:
            # リプライでない("") も取得不可(None) も再照会不要としてキャッシュ
            cache.add(sid)
            misses += 1
        time.sleep(0.3)

    if args.dry_run:
        log(f"--- dry-run: 補完 {len(updates)} 件 / 非リプライ・取得不可 {misses} 件(書き込み・キャッシュ保存なし) ---")
        return

    if updates:
        ws.batch_update(updates, value_input_option="USER_ENTERED")
    save_cache(cache)
    log(f"✓ 完了: 親ポストURL補完 {len(updates)} 件 / キャッシュ追加 {misses} 件")


if __name__ == "__main__":
    main()
