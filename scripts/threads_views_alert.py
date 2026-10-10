#!/usr/bin/env python3
"""
Threads 投稿の views 監視。投稿から WINDOW_HOURS 時間以内に THRESHOLD views に
達した投稿があれば Gmail で通知する（1投稿につき1回）。x_imp_alert.py の Threads 版。

対象: 自分のトップ投稿（一覧 API はリプライを返さないので、リプライは自然に除外される）
状態: logs/threads_views_alert_state.json に通知済み media_id を保存（二重通知防止）
ログ: logs/threads_views_alert.log

使い方:
  python3 scripts/threads_views_alert.py                 # 通常実行（cron 用）
  python3 scripts/threads_views_alert.py --dry-run       # 送信・状態保存をせず判定だけ表示
  python3 scripts/threads_views_alert.py --threshold 500 --hours 6   # 閾値・時間窓の一時変更

認証: gcp/threads_token.json（fetch_threads_posts.py と同じ）。Threads API は無料で従量課金なし。
この VPS は IPv6 不通のため DNS を IPv4 固定する。
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --- IPv4 固定（IPv6 が通らない環境でのハング回避）---
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
socket.getaddrinfo = _ipv4_only

# ── 設定 ─────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
API = "https://graph.threads.net/v1.0"
TOKEN_PATH = REPO_ROOT / "gcp" / "threads_token.json"
THRESHOLD = 1500                # views 閾値（X 版と同じ値で開始。2026-10-10）
WINDOW_HOURS = 2                # 投稿からの時間窓
NOTIFY_TO = "useakat@gmail.com"
START_MARGIN_MIN = 10           # since の余裕（分）。窓外の投稿はスクリプト側でも除外する
STATE_KEEP_DAYS = 7             # 通知済み記録の保持日数
POST_FIELDS = "id,text,permalink,timestamp,is_quote_post"
INSIGHT_METRICS = "views,likes,replies,reposts,quotes,shares"

STATE_PATH = REPO_ROOT / "logs" / "threads_views_alert_state.json"
LOG_PATH = REPO_ROOT / "logs" / "threads_views_alert.log"
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
    for mid, info in list(state["notified"].items()):
        try:
            if datetime.fromisoformat(info["notified_at"]) < cutoff:
                del state["notified"][mid]
        except (KeyError, ValueError):
            del state["notified"][mid]


def load_token() -> tuple[str, str]:
    with open(TOKEN_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return d["access_token"], str(d["user_id"])


def api_get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Threads API エラー {e.code}: {e.read().decode()[:200]}")


def fetch_recent_posts(token: str, user_id: str, now: datetime, window_hours: float) -> list[dict]:
    """時間窓内のトップ投稿を取得する（since で API 側も絞る）"""
    since = now - timedelta(hours=window_hours, minutes=START_MARGIN_MIN)
    url = f"{API}/{user_id}/threads?" + urllib.parse.urlencode({
        "fields": POST_FIELDS, "limit": 25,
        "since": int(since.timestamp()), "access_token": token,
    })
    return api_get(url).get("data", [])


def fetch_insights(token: str, media_id: str) -> dict:
    url = f"{API}/{media_id}/insights?" + urllib.parse.urlencode(
        {"metric": INSIGHT_METRICS, "access_token": token})
    out = {}
    for m in api_get(url).get("data", []):
        val = 0
        if m.get("values"):
            val = m["values"][0].get("value", 0)
        elif isinstance(m.get("total_value"), dict):
            val = m["total_value"].get("value", 0)
        out[m.get("name")] = val or 0
    return out


def parse_ts(s: str) -> datetime:
    # 例: 2026-10-09T05:12:34+0000
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


def build_mail(post: dict, ins: dict, posted_at: datetime, age: timedelta) -> tuple[str, str]:
    mins = int(age.total_seconds() // 60)
    age_str = f"{mins // 60}時間{mins % 60}分"
    kind = "引用" if post.get("is_quote_post") else "オリジナル"
    text_head = (post.get("text") or "").replace("\n", " ")[:100]
    views = ins.get("views", 0)

    subject = f"【Threads views通知】投稿から{age_str}で{views:,} views到達"
    body = "\n".join([
        f"投稿から{WINDOW_HOURS:g}時間以内に{THRESHOLD:,} views に達した Threads 投稿があります。",
        "",
        f"URL: {post.get('permalink', '')}",
        f"種類: {kind}",
        f"投稿時刻: {posted_at.astimezone(JST).strftime('%Y-%m-%d %H:%M JST')}",
        f"経過時間: {age_str}",
        "",
        f"views: {views:,}",
        f"いいね: {ins.get('likes', 0):,} / リポスト: {ins.get('reposts', 0):,} / 引用: {ins.get('quotes', 0):,}",
        f"返信: {ins.get('replies', 0):,} / シェア: {ins.get('shares', 0):,}",
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

    try:
        token, user_id = load_token()
    except (OSError, KeyError, json.JSONDecodeError) as e:
        log(f"ERROR: Threads トークンが読めません ({e})")
        return 1

    now = datetime.now(timezone.utc)
    state = load_state()
    prune_state(state, now)

    try:
        posts = fetch_recent_posts(token, user_id, now, WINDOW_HOURS)
    except Exception as e:  # noqa: BLE001
        log(f"ERROR: {e}")
        return 1

    window = timedelta(hours=WINDOW_HOURS)
    checked = 0
    notified = 0
    for p in posts:
        try:
            posted_at = parse_ts(p["timestamp"])
        except (KeyError, ValueError):
            continue
        age = now - posted_at
        if age > window:
            continue
        checked += 1
        mid = p["id"]
        if mid in state["notified"]:
            continue
        try:
            ins = fetch_insights(token, mid)
        except Exception as e:  # noqa: BLE001
            log(f"ERROR: insights {mid}: {e}")
            continue
        views = int(ins.get("views", 0) or 0)
        if views < THRESHOLD:
            if args.dry_run:
                log(f"[dry-run] {mid} 経過{int(age.total_seconds()//60)}分 {views:,} views（未達）")
            continue
        subject, body = build_mail(p, ins, posted_at, age)
        if args.dry_run:
            log(f"[dry-run] 通知対象: {mid} {views:,} views\n--- 件名: {subject}\n{body}\n---")
            continue
        if send_mail(subject, body):
            state["notified"][mid] = {
                "notified_at": now.isoformat(),
                "views": views,
                "age_minutes": int(age.total_seconds() // 60),
            }
            notified += 1
            log(f"通知: {p.get('permalink', mid)} {views:,} views")

    if not args.dry_run:
        save_state(state)
    log(f"完了: 時間窓内{checked}件を確認、通知{notified}件"
        + ("（dry-run）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
