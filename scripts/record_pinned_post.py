#!/usr/bin/env python3
"""
X の固定ポストを毎日確認し、変わっていたら「発信記録」の `固定ポスト履歴` シートに記録する。

固定ポストの note リンクは通常のセルフリプと同じ xpost.usephys.net/<記事ID>/<投稿キー>（投稿キー＝元ポストの
tweet ID）のままにし、「いつ・どの投稿が固定だったか」をこのシートで管理する。転送クリック明細のキー
<記事ID>/<投稿ID> と突き合わせれば固定ポストの日別クリックが分かる（2026-10-04）。

列: 開始日 / 終了日 / 媒体 / 投稿URL / 投稿ID / 記事ID / 投稿キー / メモ
  - X の行はこのスクリプトが自動で書く（固定が変わった日に前の行へ終了日を入れ、新しい行を追加）
  - Threads は API に固定情報が無いので、固定を変えたときに手で1行書く（媒体 = Threads）

あわせて、固定中（終了日が空）のポストの IMP / views といいねを毎日 `固定ポスト日次` シートに
スナップショットする（列: 日付 / 媒体 / 投稿ID / インプ / いいね / 取得日時）。週ごとの増分が
「固定ポストを見た人の数（リンク到達）」になる（note 導線ダッシュボードの週次ファネル。2026-10-10）。
  - X: GET /2/tweets/{id}?tweet.fields=public_metrics の impression_count / like_count
  - Threads: 投稿一覧（/{user_id}/threads）から permalink で media id を引き、/{id}/insights の views / likes

使い方:
  python3 scripts/record_pinned_post.py            # 確認して必要なら記録（cron 用）
  python3 scripts/record_pinned_post.py --dry-run  # シートに書かない

認証: X は .env の X_BEARER_TOKEN（ユーザー取得と固定ポスト 1 件の取得、1日1回）、
      Threads は gcp/threads_token.json、Sheets はサービスアカウント（sheets_values.py と同じ）
"""

import argparse
import json
import os
import re
import socket
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# --- IPv4 固定（graph.threads.net が IPv6 のみ返す環境でのハング回避。fetch_threads_posts.py と同じ）---
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):  # noqa: E302
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
socket.getaddrinfo = _ipv4_only  # noqa: E305

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from sheets_values import get_client, open_with_retry  # noqa: E402

load_dotenv(REPO_ROOT / ".env")

SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
SHEET_NAME = "固定ポスト履歴"
SNAPSHOT_SHEET = "固定ポスト日次"
POSTS_SHEET = "X投稿一覧"
USER_ID = "548606471"  # @usephys
HEADER = ["開始日", "終了日", "媒体", "投稿URL", "投稿ID", "記事ID", "投稿キー", "メモ"]
SNAPSHOT_HEADER = ["日付", "媒体", "投稿ID", "インプ", "いいね", "取得日時"]
THREADS_TOKEN = REPO_ROOT / "gcp" / "threads_token.json"
THREADS_API = "https://graph.threads.net/v1.0"
JST = timezone(timedelta(hours=9))

XPOST_RE = re.compile(r"xpost\.usephys\.net/(n[0-9a-f]{10,16})/([A-Za-z0-9_-]{1,32})")
NOTE_RE = re.compile(r"note\.com/takaesu7431/n/(n[0-9a-f]{10,16})")


def fetch_pinned_id(token: str) -> str:
    r = requests.get(f"https://api.x.com/2/users/{USER_ID}",
                     headers={"Authorization": f"Bearer {token}"},
                     params={"user.fields": "pinned_tweet_id"}, timeout=30)
    r.raise_for_status()
    return str((r.json().get("data") or {}).get("pinned_tweet_id") or "")


def find_link(ss, tweet_id: str) -> tuple[str, str, str]:
    """X投稿一覧から固定ポスト本文（優先）かそのセルフリプの note リンクを探し (記事ID, 投稿キー, メモ) を返す"""
    vals = ss.worksheet(POSTS_SHEET).get_all_values()
    h = vals[0]
    i_url, i_parent, i_note = h.index("ポストURL"), h.index("親ポストURL"), h.index("noteURL")
    cands = []
    for r in vals[1:]:
        if len(r) <= i_note or not r[i_note].strip():
            continue
        if tweet_id in (r[i_url] or ""):
            cands.append((0, r[i_note].strip()))
        elif tweet_id in (r[i_parent] or ""):
            cands.append((1, r[i_note].strip()))
    if not cands:
        return "", "", "X投稿一覧に note リンクが見つからない"
    cands.sort()
    url = cands[0][1].split("\n")[0]
    m = XPOST_RE.search(url)
    if m:
        return m.group(1), m.group(2), ""
    m = NOTE_RE.search(url)
    if m:
        return m.group(1), "", "生 note リンク（xpost 導入前）"
    return "", "", f"不明なリンク: {url}"


def x_metrics(token: str, tweet_id: str) -> tuple[int, int] | None:
    """固定ポストの (impression_count, like_count)。取れなければ None"""
    r = requests.get(f"https://api.x.com/2/tweets/{tweet_id}",
                     headers={"Authorization": f"Bearer {token}"},
                     params={"tweet.fields": "public_metrics"}, timeout=30)
    if r.status_code != 200:
        print(f"X ポスト取得に失敗 ({r.status_code}): {r.text[:200]}", file=sys.stderr)
        return None
    pm = (r.json().get("data") or {}).get("public_metrics") or {}
    return int(pm.get("impression_count") or 0), int(pm.get("like_count") or 0)


def threads_metrics(post_id: str) -> tuple[int, int] | None:
    """Threads の固定投稿（permalink 末尾の ID）の (views, likes)。media id は投稿一覧から permalink で引く"""
    if not THREADS_TOKEN.exists():
        print("gcp/threads_token.json が無いので Threads の固定投稿は取らない", file=sys.stderr)
        return None
    d = json.loads(THREADS_TOKEN.read_text(encoding="utf-8"))
    token, uid = d["access_token"], str(d["user_id"])
    media_id = None
    url = f"{THREADS_API}/{uid}/threads"
    params = {"fields": "id,permalink", "limit": 100, "access_token": token}
    for _ in range(5):  # 500 件まで遡る（固定は普通ごく最近の投稿）
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            print(f"Threads 投稿一覧の取得に失敗 ({r.status_code}): {r.text[:200]}", file=sys.stderr)
            return None
        body = r.json()
        for p in body.get("data", []):
            if (p.get("permalink") or "").rstrip("/").endswith("/" + post_id):
                media_id = p["id"]
                break
        if media_id or not body.get("paging", {}).get("next"):
            break
        url, params = body["paging"]["next"], None
    if not media_id:
        print(f"Threads 投稿 {post_id} が投稿一覧に見つからない", file=sys.stderr)
        return None
    r = requests.get(f"{THREADS_API}/{media_id}/insights", params={"metric": "views,likes", "access_token": token}, timeout=30)
    if r.status_code != 200:
        print(f"Threads insights の取得に失敗 ({r.status_code}): {r.text[:200]}", file=sys.stderr)
        return None
    out = {}
    for m in r.json().get("data", []):
        v = (m.get("values") or [{}])[0].get("value") if m.get("values") else (m.get("total_value") or {}).get("value")
        out[m.get("name")] = int(v or 0)
    return out.get("views", 0), out.get("likes", 0)


def snapshot_pinned(ss, x_token: str, vals: list[list[str]], today: str, dry_run: bool) -> None:
    """固定中（終了日が空）の各ポストの IMP / いいねを 固定ポスト日次 に 1 日 1 行で記録する"""
    open_posts = [(r[2].strip(), r[4].strip()) for r in vals[1:] if len(r) >= 5 and r[4].strip() and not r[1].strip()]
    if not open_posts:
        print("固定中のポストなし（スナップショットなし）")
        return
    try:
        ws = ss.worksheet(SNAPSHOT_SHEET)
        existing = ws.get_all_values()
    except Exception:  # noqa: BLE001  (WorksheetNotFound)
        ws, existing = None, []
    done = {(r[0], r[1], r[2]) for r in existing[1:] if len(r) >= 3}
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for media, pid in open_posts:
        if (today, media, pid) in done:
            print(f"スナップショット済み: {media} {pid}")
            continue
        m = x_metrics(x_token, pid) if media == "X" else threads_metrics(pid) if media == "Threads" else None
        if m is None:
            continue
        rows.append([today, media, pid, m[0], m[1], now])
        print(f"スナップショット: {media} {pid} インプ={m[0]} いいね={m[1]}")
    if dry_run or not rows:
        return
    if ws is None:
        ws = ss.add_worksheet(title=SNAPSHOT_SHEET, rows=2000, cols=len(SNAPSHOT_HEADER) + 2)
        ws.update(values=[SNAPSHOT_HEADER], range_name="A1:F1", value_input_option="RAW")
    ws.append_rows(rows, value_input_option="RAW")  # 投稿ID は 19 桁なので RAW（数値化で末尾が丸まる）
    print(f"✅ {SNAPSHOT_SHEET} に {len(rows)} 行追加")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        print("X_BEARER_TOKEN が未設定（.env を確認）", file=sys.stderr)
        return 1
    pinned = fetch_pinned_id(token)
    today = datetime.now(JST).date().isoformat()

    ss = open_with_retry(get_client(), SPREADSHEET_ID)
    try:
        ws = ss.worksheet(SHEET_NAME)
    except Exception:
        ws = None
    vals = ws.get_all_values() if ws else []
    first = len(vals) <= 1

    open_row = None  # (行番号, 投稿ID) — 媒体が X で終了日が空の行
    for i, r in enumerate(vals[1:], start=2):
        if len(r) >= 5 and r[2].strip() == "X" and not r[1].strip():
            open_row = (i, r[4].strip())

    if open_row and open_row[1] == pinned:
        print(f"変更なし: 固定ポスト {pinned}")
        snapshot_pinned(ss, token, vals, today, args.dry_run)
        return 0

    actions = []
    if open_row:
        actions.append(f"固定解除を記録: {open_row[1]}（終了日 {today}）")
    new_row = None
    if pinned:
        art, key, memo = find_link(ss, pinned)
        if first:
            memo = (memo + "；" if memo else "") + "初期登録（実際の固定開始日は不明）"
        new_row = [today, "", "X", f"https://x.com/usephys/status/{pinned}", pinned, art, key, memo]
        actions.append(f"固定ポストを記録: {pinned} 記事ID={art or '-'} 投稿キー={key or '-'} {memo}")
    else:
        actions.append("固定ポストなし")
    for a in actions:
        print(a)
    if args.dry_run:
        snapshot_pinned(ss, token, vals + ([new_row] if new_row else []), today, True)
        return 0

    if ws is None:
        ws = ss.add_worksheet(title=SHEET_NAME, rows=200, cols=len(HEADER) + 2)
        ws.update(values=[HEADER], range_name="A1:H1", value_input_option="RAW")
    if open_row:
        ws.update_cell(open_row[0], 2, today)
    if new_row:
        # 投稿ID は 19 桁。USER_ENTERED だと数値化されて末尾が丸まるので RAW で文字列のまま書く
        ws.append_row(new_row, value_input_option="RAW")
    print("✅ 固定ポスト履歴 を更新しました")
    # 新しい固定ポストも含めて今日のスナップショット（解除した行は終了日が入るので対象外）
    snapshot_pinned(ss, token, ws.get_all_values(), today, False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
