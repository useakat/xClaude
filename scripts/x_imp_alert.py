#!/usr/bin/env python3
"""
X 投稿のインプレッション監視。投稿から WINDOW_HOURS 時間以内に THRESHOLD インプに
達した投稿があれば Gmail で通知する（1投稿につき1回）。

対象: 自分のオリジナル投稿＋引用RT（リポストと自分のリプライは除外）
状態: logs/x_imp_alert_state.json に通知済み tweet_id を保存（二重通知防止）
ログ: logs/x_imp_alert.log

使い方:
  python3 scripts/x_imp_alert.py                 # 通常実行（cron 用）
  python3 scripts/x_imp_alert.py --dry-run       # 送信・状態保存をせず判定だけ表示
  python3 scripts/x_imp_alert.py --threshold 500 --hours 6   # 閾値・時間窓の一時変更

認証: リポジトリ直下の .env の X_BEARER_TOKEN（post_to_x.py と同じ）
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── 設定 ─────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

USER_ID = "548606471"           # @usephys
USERNAME = "usephys"
THRESHOLD = 1000                # インプ閾値
WINDOW_HOURS = 3                # 投稿からの時間窓
NOTIFY_TO = "useakat@gmail.com"
MAX_RESULTS = 20                # 取得する直近投稿数（時間窓内の投稿を十分に含む数）
STATE_KEEP_DAYS = 7             # 通知済み記録の保持日数

STATE_PATH = REPO_ROOT / "logs" / "x_imp_alert_state.json"
LOG_PATH = REPO_ROOT / "logs" / "x_imp_alert.log"
SEND_GMAIL = REPO_ROOT / "scripts" / "send_gmail.sh"

JST = timezone(timedelta(hours=9))


def log(msg: str) -> None:
    line = f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log("警告: state ファイルが壊れているため初期化します")
    return {"notified": {}}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def prune_state(state: dict, now: datetime) -> None:
    cutoff = now - timedelta(days=STATE_KEEP_DAYS)
    for tid, info in list(state["notified"].items()):
        try:
            if datetime.fromisoformat(info["notified_at"]) < cutoff:
                del state["notified"][tid]
        except (KeyError, ValueError):
            del state["notified"][tid]


def fetch_recent_posts(token: str) -> list[dict]:
    url = f"https://api.x.com/2/users/{USER_ID}/tweets"
    params = {
        "max_results": MAX_RESULTS,
        "exclude": "retweets",
        "tweet.fields": "created_at,public_metrics,referenced_tweets,text",
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"X API エラー {r.status_code}: {r.text[:200]}")
    return r.json().get("data", [])


def is_target(tweet: dict) -> bool:
    """オリジナル投稿と引用RTを対象にし、自分のリプライは除外する"""
    for ref in tweet.get("referenced_tweets", []) or []:
        if ref.get("type") == "replied_to":
            return False
    return True


def build_mail(tweet: dict, posted_at: datetime, age: timedelta) -> tuple[str, str]:
    pm = tweet["public_metrics"]
    tid = tweet["id"]
    kind = "引用RT" if any(r.get("type") == "quoted" for r in tweet.get("referenced_tweets", []) or []) else "オリジナル"
    mins = int(age.total_seconds() // 60)
    age_str = f"{mins // 60}時間{mins % 60}分"
    text_head = tweet.get("text", "").replace("\n", " ")[:100]

    subject = f"【Xインプ通知】投稿から{age_str}で{pm['impression_count']:,}インプ到達"
    body = "\n".join([
        f"投稿から{WINDOW_HOURS:g}時間以内に{THRESHOLD:,}インプに達した投稿があります。",
        "",
        f"URL: https://x.com/{USERNAME}/status/{tid}",
        f"種類: {kind}",
        f"投稿時刻: {posted_at.astimezone(JST).strftime('%Y-%m-%d %H:%M JST')}",
        f"経過時間: {age_str}",
        "",
        f"インプレッション: {pm['impression_count']:,}",
        f"いいね: {pm['like_count']:,} / リポスト: {pm['retweet_count']:,} / 引用: {pm['quote_count']:,}",
        f"リプライ: {pm['reply_count']:,} / ブックマーク: {pm.get('bookmark_count', 0):,}",
        "",
        f"本文冒頭: {text_head}",
    ])
    return subject, body


def send_mail(subject: str, body: str) -> bool:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_file = f.name
    try:
        result = subprocess.run(
            ["bash", str(SEND_GMAIL), "--to", NOTIFY_TO, "--subject", subject, "--body-file", body_file],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            log(f"メール送信失敗: {result.stderr.strip()[:300]}")
            return False
        log(f"メール送信: {result.stdout.strip()}")
        return True
    finally:
        os.unlink(body_file)


def main() -> int:
    global THRESHOLD, WINDOW_HOURS
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="送信・状態保存をしない")
    parser.add_argument("--threshold", type=int, default=THRESHOLD)
    parser.add_argument("--hours", type=float, default=WINDOW_HOURS)
    args = parser.parse_args()
    THRESHOLD, WINDOW_HOURS = args.threshold, args.hours

    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        log("ERROR: X_BEARER_TOKEN が未設定（.env を確認）")
        return 1

    now = datetime.now(timezone.utc)
    state = load_state()
    prune_state(state, now)

    try:
        tweets = fetch_recent_posts(token)
    except Exception as e:  # noqa: BLE001
        log(f"ERROR: {e}")
        return 1

    window = timedelta(hours=WINDOW_HOURS)
    checked = 0
    notified = 0
    for t in tweets:
        if not is_target(t):
            continue
        posted_at = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        age = now - posted_at
        if age > window:
            continue
        checked += 1
        imp = t["public_metrics"]["impression_count"]
        tid = t["id"]
        if imp < THRESHOLD:
            if args.dry_run:
                log(f"[dry-run] {tid} 経過{int(age.total_seconds()//60)}分 {imp:,}インプ（未達）")
            continue
        if tid in state["notified"]:
            continue
        subject, body = build_mail(t, posted_at, age)
        if args.dry_run:
            log(f"[dry-run] 通知対象: {tid} {imp:,}インプ\n--- 件名: {subject}\n{body}\n---")
            continue
        if send_mail(subject, body):
            state["notified"][tid] = {
                "notified_at": now.isoformat(),
                "impressions": imp,
                "age_minutes": int(age.total_seconds() // 60),
            }
            notified += 1
            log(f"通知: https://x.com/{USERNAME}/status/{tid} {imp:,}インプ")

    if not args.dry_run:
        save_state(state)
    log(f"完了: 時間窓内{checked}件を確認、通知{notified}件"
        + ("（dry-run）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
