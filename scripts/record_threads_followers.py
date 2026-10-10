#!/usr/bin/env python3
"""Threads の現在のフォロワ数を取得し、「日次記録」シートの前日行 V列(22) に記録する。

日次記録シートは GAS（gas/DailyMetricsRecord.js）が毎朝 X/note のフォロワ数などを
前日日付の行に書き込む。V列「threads フォロワ数」だけ空だったので、Threads Graph API
（insights の followers_count）で取得してローカル cron で埋める。

- Threads トークン: gcp/threads_token.json（月次で自動更新）。
- シート書き込み: サービスアカウント（同スプレッドシートに書込権限あり）。
- この VPS は IPv6 不通のため DNS を IPv4 固定する。

あわせて user insights の `views`（API の説明は「プロフィールが閲覧された回数」。実際の値は投稿の表示
回数の合計に近く、アカウント全体の表示として扱う）を AE列(31)「threads views」に記録する（2026-10-10、
note 導線ファネルの Threads bio / 固定 の「インプ」用）。API の日次バケットは end_time が 07:00 UTC
（16:00 JST）で区切られるので、対象日 D には end_time の日付が D のバケット（前日 16:00〜当日 16:00 JST）を使う。

Usage:
  python3 scripts/record_threads_followers.py [--dry-run] [--date YYYY/MM/DD]
"""
import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# --- IPv4 固定（IPv6 が通らない環境でのハング回避）---
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
socket.getaddrinfo = _ipv4_only

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(ROOT, "gcp", "threads_token.json")
API = "https://graph.threads.net/v1.0"
SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
SHEET_NAME = "日次記録"
FOLLOWERS_COL = 22  # V列「threads フォロワ数」
VIEWS_COL = 31      # AE列「threads views」
VIEWS_HEADER = "threads views"
DATE_COL = 1        # A列 日付
DAY_COL = 2         # B列 曜日
JST = timezone(timedelta(hours=9))
DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def log(msg):
    print(f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}", flush=True)


def _load_token():
    with open(TOKEN_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return d["access_token"], str(d["user_id"])


def fetch_followers(token, user_id):
    url = f"{API}/{user_id}/threads_insights?" + urllib.parse.urlencode(
        {"metric": "followers_count", "access_token": token})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Threads API エラー ({e.code}): {e.read().decode()}")
    data = d.get("data") or []
    if not data:
        raise SystemExit("followers_count が取得できませんでした（data 空）")
    return int(data[0]["total_value"]["value"])


def fetch_views(token, user_id, target_dt):
    """対象日のアカウント views（end_time の日付が対象日のバケット）。取れなければ None"""
    import calendar
    day0 = datetime(target_dt.year, target_dt.month, target_dt.day)
    since = calendar.timegm((day0 - timedelta(days=2)).timetuple())
    until = calendar.timegm((day0 + timedelta(days=2)).timetuple())
    url = f"{API}/{user_id}/threads_insights?" + urllib.parse.urlencode(
        {"metric": "views", "since": since, "until": until, "access_token": token})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        log(f"⚠ views の取得に失敗 ({e.code}): {e.read().decode()[:200]}")
        return None
    want = target_dt.strftime("%Y-%m-%d")
    for m in d.get("data") or []:
        if m.get("name") != "views":
            continue
        for v in m.get("values") or []:
            if str(v.get("end_time", "")).startswith(want):
                return int(v.get("value") or 0)
    log(f"⚠ views に {want} のバケットが無い")
    return None


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


def norm_date(s):
    """A列セルの日付表記を yyyy/MM/dd に正規化して突合しやすくする。"""
    s = (s or "").strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y/%m/%d")
        except ValueError:
            pass
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="取得値と対象行を表示するだけで書き込まない")
    ap.add_argument("--date", default="", help="対象日 YYYY/MM/DD（既定=前日 JST）")
    args = ap.parse_args()

    target_dt = None
    if args.date:
        target_dt = datetime.strptime(args.date, "%Y/%m/%d")
    else:
        target_dt = datetime.now(JST) - timedelta(days=1)
    target = target_dt.strftime("%Y/%m/%d")

    token, user_id = _load_token()
    followers = fetch_followers(token, user_id)
    views = fetch_views(token, user_id, target_dt)
    log(f"Threads フォロワ数 = {followers} / views = {views if views is not None else '取得不可'} / 対象日 = {target}")

    ws = get_ws()
    col_a = ws.col_values(DATE_COL)  # ヘッダ含む
    target_row = None
    for i, v in enumerate(col_a, start=1):
        if i == 1:
            continue
        if norm_date(v) == target:
            target_row = i
            break
    header_ok = ws.cell(1, VIEWS_COL).value == VIEWS_HEADER

    if args.dry_run:
        log(f"--- dry-run: 対象行={target_row or '(未検出→新規作成予定)'} / V列に {followers}（--date 指定時は空セルのみ）、AE列に {views} を書く予定"
            f"{'' if header_ok else '（AE1 に見出しを作る）'} ---")
        return

    if not header_ok:
        ws.update_cell(1, VIEWS_COL, VIEWS_HEADER)
    if target_row:
        # フォロワ数は「今の値」なので、--date で過去日を指定したときは空セルにしか書かない
        # （過去行を今日の値で上書きしない。2026-10-10 に 11 日分を上書きしてログから復旧した）
        write_followers = not args.date or not (ws.cell(target_row, FOLLOWERS_COL).value or "").strip()
        if write_followers:
            ws.update_cell(target_row, FOLLOWERS_COL, followers)
        if views is not None:
            ws.update_cell(target_row, VIEWS_COL, views)
        log(f"✓ 記録: 行{target_row} V列 = {followers if write_followers else '（既存値を保持）'}, AE列 = {views}")
    else:
        # GAS が前日行を作れていない保険。A=日付, B=曜日, V=値, AE=views の行を追記。
        row = [""] * VIEWS_COL
        row[DATE_COL - 1] = target
        # Python weekday(): Mon=0..Sun=6 → GAS getDay(): Sun=0..Sat=6
        row[DAY_COL - 1] = DAY_NAMES[(target_dt.weekday() + 1) % 7]
        row[FOLLOWERS_COL - 1] = followers
        if views is not None:
            row[VIEWS_COL - 1] = views
        ws.append_row(row, value_input_option="USER_ENTERED")
        log(f"⚠ 前日行が未検出のため新規追記（A={target}, V={followers}, AE={views}）")


if __name__ == "__main__":
    main()
