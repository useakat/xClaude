#!/usr/bin/env python3
"""
X / Threads の本体投稿について、投稿後 24 時間のインプ（views）推移を記録する。

間隔: 投稿から FINE_HOURS 時間までは 15 分刻み、以降 24 時間までは 1 時間刻み（1 投稿 34 点）
cron:  */15 * * * *（run_imp_timeline.sh 経由）
保存:  logs/imp_timeline/x_YYYY-MM.csv / threads_YYYY-MM.csv（月別・追記のみ・git 管理外）
ログ:  logs/imp_timeline.log

費用（X は従量課金・返却投稿 1 件ごと）:
  :15/:30/:45 の tick は start_time = now − FINE_HOURS − 余裕 で 3h 以内の投稿だけ取り、
  :00 の tick だけ 24h 以内の全投稿を取る。exclude=retweets,replies で本体投稿のみ。
  → 4 本/日なら月 約 $4（Owned Read $0.001/件）。Threads API は無料。

使い方:
  python3 scripts/imp_timeline.py                   # 通常実行（cron 用）
  python3 scripts/imp_timeline.py --dry-run         # CSV に書かず取得結果だけ表示
  python3 scripts/imp_timeline.py --platform x      # x / threads のどちらかだけ
  python3 scripts/imp_timeline.py --force-full      # 分に関わらず 24h 窓で取る（手動確認用）

認証: X は .env の X_BEARER_TOKEN、Threads は gcp/threads_token.json（既存スクリプトと同じ）
"""

import argparse
import csv
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# --- IPv4 固定（この VPS は IPv6 不通。Threads API がハングするため）---
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
socket.getaddrinfo = _ipv4_only

# ── 設定 ─────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

X_USER_ID = "548606471"          # @usephys
X_USERNAME = "usephys"
THREADS_API = "https://graph.threads.net/v1.0"
THREADS_TOKEN_PATH = REPO_ROOT / "gcp" / "threads_token.json"
THREADS_INSIGHT_METRICS = "views,likes,replies,reposts,quotes,shares"

TOTAL_HOURS = 24                 # 記録する期間（投稿からの時間）
FINE_HOURS = 3                   # ここまでは 15 分刻み、以降は 1 時間刻み
FINE_HOURS_THREADS = FINE_HOURS  # Threads は無料なので 24 にすれば 15 分刻みを 24h 続けられる
START_MARGIN_MIN = 10            # 取得窓の余裕（分）。時計ずれ対策。窓外はスクリプト側でも除外
X_MAX_RESULTS = 20

OUT_DIR = REPO_ROOT / "logs" / "imp_timeline"
LOG_PATH = REPO_ROOT / "logs" / "imp_timeline.log"
COLUMNS = ["記録時刻JST", "投稿ID", "投稿時刻JST", "経過分",
           "インプ", "いいね", "RP", "リプ", "引用", "ブクマ", "URL"]

JST = timezone(timedelta(hours=9))


def log(msg: str) -> None:
    line = f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def window_hours(now: datetime, fine_hours: float, force_full: bool) -> float:
    """この tick で取りに行く窓。毎時 :00 の tick だけ 24h、それ以外は fine_hours"""
    if force_full or now.minute < 15:
        return TOTAL_HOURS
    return fine_hours


def fmt_jst(dt: datetime) -> str:
    return dt.astimezone(JST).strftime("%Y-%m-%d %H:%M:%S")


# ── X ────────────────────────────────────────────────
def fetch_x(token: str, now: datetime, hours: float) -> list[dict]:
    """窓内の本体投稿（リポスト・リプライ除外）を public_metrics 付きで取る"""
    start_time = now - timedelta(hours=hours, minutes=START_MARGIN_MIN)
    params = {
        "max_results": X_MAX_RESULTS,
        "exclude": "retweets,replies",
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tweet.fields": "created_at,public_metrics",
    }
    r = requests.get(f"https://api.x.com/2/users/{X_USER_ID}/tweets",
                     headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"X API エラー {r.status_code}: {r.text[:200]}")
    rows = []
    for t in r.json().get("data", []):
        posted_at = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        pm = t.get("public_metrics") or {}
        rows.append({
            "id": t["id"], "posted_at": posted_at,
            "imp": pm.get("impression_count", 0), "like": pm.get("like_count", 0),
            "rp": pm.get("retweet_count", 0), "reply": pm.get("reply_count", 0),
            "quote": pm.get("quote_count", 0), "bm": pm.get("bookmark_count", 0),
            "url": f"https://x.com/{X_USERNAME}/status/{t['id']}",
        })
    return rows


# ── Threads ──────────────────────────────────────────
def threads_get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Threads API エラー {e.code}: {e.read().decode()[:200]}")


def fetch_threads(now: datetime, hours: float) -> list[dict]:
    """窓内のトップ投稿（一覧 API はリプライを返さない）の insights を取る"""
    d = json.loads(THREADS_TOKEN_PATH.read_text(encoding="utf-8"))
    token, uid = d["access_token"], str(d["user_id"])
    since = now - timedelta(hours=hours, minutes=START_MARGIN_MIN)
    url = f"{THREADS_API}/{uid}/threads?" + urllib.parse.urlencode({
        "fields": "id,permalink,timestamp", "limit": 25,
        "since": int(since.timestamp()), "access_token": token,
    })
    rows = []
    for p in threads_get(url).get("data", []):
        try:
            posted_at = datetime.strptime(p["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        except (KeyError, ValueError):
            continue
        ins_url = f"{THREADS_API}/{p['id']}/insights?" + urllib.parse.urlencode(
            {"metric": THREADS_INSIGHT_METRICS, "access_token": token})
        ins = {}
        for m in threads_get(ins_url).get("data", []):
            val = 0
            if m.get("values"):
                val = m["values"][0].get("value", 0)
            elif isinstance(m.get("total_value"), dict):
                val = m["total_value"].get("value", 0)
            ins[m.get("name")] = int(val or 0)
        rows.append({
            "id": p["id"], "posted_at": posted_at,
            "imp": ins.get("views", 0), "like": ins.get("likes", 0),
            "rp": ins.get("reposts", 0), "reply": ins.get("replies", 0),
            "quote": ins.get("quotes", 0), "bm": ins.get("shares", 0),
            "url": p.get("permalink", ""),
        })
    return rows


# ── 記録 ─────────────────────────────────────────────
def should_record(age_min: int, hours_fetched: float, fine_hours: float) -> bool:
    """FINE_HOURS 以内は毎 tick、それ以降は 24h 窓で取った tick（毎時 :00）だけ記録"""
    if age_min > TOTAL_HOURS * 60:
        return False
    if age_min <= fine_hours * 60:
        return True
    return hours_fetched >= TOTAL_HOURS


def append_rows(platform: str, now: datetime, rows: list[dict], dry_run: bool) -> int:
    path = OUT_DIR / f"{platform}_{now.astimezone(JST).strftime('%Y-%m')}.csv"
    new_file = not path.exists()
    written = 0
    out = []
    for r in rows:
        out.append([fmt_jst(now), r["id"], fmt_jst(r["posted_at"]), r["age_min"],
                    r["imp"], r["like"], r["rp"], r["reply"], r["quote"], r["bm"], r["url"]])
    if dry_run:
        for row in out:
            log(f"[dry-run] {platform} {row[1]} 経過{row[3]}分 インプ{row[4]:,}")
        return len(out)
    if not out:
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(COLUMNS)
        for row in out:
            w.writerow(row)
            written += 1
    return written


def run_platform(platform: str, now: datetime, args) -> None:
    fine = FINE_HOURS if platform == "x" else FINE_HOURS_THREADS
    hours = window_hours(now, fine, args.force_full)
    try:
        if platform == "x":
            token = os.getenv("X_BEARER_TOKEN", "").strip()
            if not token:
                raise RuntimeError("X_BEARER_TOKEN が未設定（.env を確認）")
            rows = fetch_x(token, now, hours)
        else:
            rows = fetch_threads(now, hours)
    except Exception as e:  # noqa: BLE001
        log(f"ERROR {platform}: {e}")
        return
    keep = []
    for r in rows:
        r["age_min"] = int((now - r["posted_at"]).total_seconds() // 60)
        if should_record(r["age_min"], hours, fine):
            keep.append(r)
    n = append_rows(platform, now, keep, args.dry_run)
    log(f"{platform}: 窓{hours:g}h で {len(rows)} 件取得、{n} 件記録"
        + ("（dry-run）" if args.dry_run else ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="CSV に書かない")
    parser.add_argument("--platform", choices=["x", "threads"], help="片方だけ実行")
    parser.add_argument("--force-full", action="store_true", help="分に関わらず 24h 窓で取る")
    args = parser.parse_args()

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    platforms = [args.platform] if args.platform else ["x", "threads"]
    for p in platforms:
        run_platform(p, now, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
