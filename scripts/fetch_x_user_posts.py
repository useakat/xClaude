#!/usr/bin/env python3
"""
指定した X アカウントの投稿を期間指定で取得し、「X競合分析」スプレッドシートに
新しいシートを作って記録する（競合アカウントの観察用）。

使い方:
  python3 scripts/fetch_x_user_posts.py --username ossanworld --start 2026-05-01 --end 2026-05-31
  python3 scripts/fetch_x_user_posts.py --username ossanworld --start 2026-05-01 --end 2026-05-31 --dry-run
      # X API から取るだけでシートには書かない（JSON を logs/x_user_posts/ に残す）
  --sheet-name NAME   シート名（既定: "<username> YYYY-MM"。既にあれば中止）
  --from-json PATH    X API を呼ばず、保存済み JSON からシートを作る（dry-run の後に使う）
  --overwrite         同名シートがあれば中身を消して書き直す（送信済み列も消える）

取得する投稿:
  リポスト（RT）と他人へのリプライは除外。自分のスレッドの続き（自分の投稿への返信）は
  「ツリー続き」として残す（galileo_fun 2026-08 シートと同じ扱い）。ただし本文が
  「@相手」で始まるもの（他人との会話の中の自己返信）は除外する。
  長文投稿は note_tweet の全文を使う。

シート列:
  A 投稿日時 / B ツイートID / C URL / D IMP / E いいね / F RT / G リプライ / H 引用RT /
  I ブックマーク / J ツリー（単独・ツリー先頭・ツリー続き） / K 会話ID / L 冒頭1文 /
  M 本文（全文） / N 送信済み（x_competitor_daily_mail.py が送信日を書く）
  古い順に並べる（毎日のメールが古い順に 1 件ずつ送るため）。

認証: X は .env の X_BEARER_TOKEN、Sheets はサービスアカウント（sheets_values.py と同じ）
課金: X API は従量課金（返ってきた投稿 1 件ごと）。start_time / end_time で期間内だけ取る。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(Path(__file__).parent))
from sheets_values import get_client, open_with_retry  # noqa: E402

SPREADSHEET_ID = "1OKQ6zoryoDAQvvKu5kWr9bJD20dO-zfnfrkufLl00tw"  # X競合分析
OUT_DIR = REPO_ROOT / "logs" / "x_user_posts"
JST = timezone(timedelta(hours=9))
HEADER = ["投稿日時", "ツイートID", "URL", "IMP", "いいね", "RT", "リプライ", "引用RT",
          "ブックマーク", "ツリー", "会話ID", "冒頭1文", "本文（全文）", "送信済み"]
API = "https://api.x.com/2"


def log(msg: str) -> None:
    print(f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}", flush=True)


# ── X API ────────────────────────────────────────────

def get_user(token: str, username: str) -> dict:
    r = requests.get(f"{API}/users/by/username/{username}",
                     headers={"Authorization": f"Bearer {token}"},
                     params={"user.fields": "public_metrics,created_at"}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"X API ユーザー取得エラー {r.status_code}: {r.text[:200]}")
    return r.json()["data"]


def fetch_timeline(token: str, user_id: str, start: datetime, end: datetime) -> list[dict]:
    """期間内の投稿を全ページ取得（RT は API 側で除外。リプライは後で選別）。"""
    url = f"{API}/users/{user_id}/tweets"
    params = {
        "max_results": 100,
        "exclude": "retweets",
        "start_time": start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tweet.fields": "created_at,public_metrics,referenced_tweets,conversation_id,"
                        "in_reply_to_user_id,text,note_tweet",
    }
    out: list[dict] = []
    page = 0
    while True:
        page += 1
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"X API タイムライン取得エラー {r.status_code}: {r.text[:200]}")
        j = r.json()
        data = j.get("data", [])
        out.extend(data)
        log(f"ページ {page}: {len(data)} 件（累計 {len(out)}）")
        token_next = j.get("meta", {}).get("next_token")
        if not token_next or not data:
            break
        params["pagination_token"] = token_next
    return out


# ── 整形 ─────────────────────────────────────────────

def full_text(t: dict) -> str:
    nt = t.get("note_tweet") or {}
    return (nt.get("text") or t.get("text") or "").replace("\r", "")


def first_sentence(text: str) -> str:
    s = text.strip().split("\n", 1)[0]
    m = re.split(r"(?<=[。！？!?])", s, maxsplit=1)
    s = m[0] if m and m[0] else s
    return s[:60]


def select_rows(tweets: list[dict], user_id: str, username: str) -> list[list]:
    kept = []
    for t in tweets:
        refs = t.get("referenced_tweets") or []
        if any(r.get("type") == "retweeted" for r in refs):
            continue
        is_reply = any(r.get("type") == "replied_to" for r in refs)
        if is_reply and t.get("in_reply_to_user_id") != user_id:
            continue  # 他人へのリプライ
        if re.match(r"@(?!%s\b)" % re.escape(username), t.get("text", ""), re.I):
            continue  # 他人との会話の続き（本文が @相手 で始まる）。参照先が消えた返信は
            #           referenced_tweets が無いので、返信フラグに頼らず本文で判定する
        kept.append(t)

    heads = {t["id"] for t in kept if t.get("conversation_id") == t["id"]}
    conv_count: dict[str, int] = {}
    for t in kept:
        conv_count[t["conversation_id"]] = conv_count.get(t["conversation_id"], 0) + 1

    kept.sort(key=lambda t: t["created_at"])
    rows = []
    for t in kept:
        cid = t.get("conversation_id", t["id"])
        if t["id"] in heads:
            tree = "ツリー先頭" if conv_count.get(cid, 0) > 1 else "単独"
        else:
            tree = "ツリー続き"
        pm = t.get("public_metrics", {})
        dt = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")).astimezone(JST)
        text = full_text(t)
        rows.append([
            dt.strftime("%Y-%m-%d %H:%M"),
            t["id"],
            f"https://x.com/{username}/status/{t['id']}",
            pm.get("impression_count", 0), pm.get("like_count", 0), pm.get("retweet_count", 0),
            pm.get("reply_count", 0), pm.get("quote_count", 0), pm.get("bookmark_count", 0),
            tree, cid, first_sentence(text), text, "",
        ])
    return rows


# ── Sheets ───────────────────────────────────────────

def write_sheet(spreadsheet_id: str, sheet_name: str, rows: list[list], overwrite: bool = False) -> str:
    ss = open_with_retry(get_client(), spreadsheet_id)
    existing = [ws for ws in ss.worksheets() if ws.title == sheet_name]
    if existing and not overwrite:
        raise RuntimeError(f"シート '{sheet_name}' は既にあります。--sheet-name で別名を指定するか --overwrite")
    if existing:
        ws = existing[0]
        ws.clear()
        ws.resize(rows=len(rows) + 10, cols=len(HEADER))
    else:
        ws = ss.add_worksheet(title=sheet_name, rows=len(rows) + 10, cols=len(HEADER))
    ws.update(range_name="A1", values=[HEADER] + rows, value_input_option="RAW")
    ws.freeze(rows=1)
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={ws.id}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--username", required=True)
    ap.add_argument("--start", required=True, help="YYYY-MM-DD（JST、この日を含む）")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD（JST、この日を含む）")
    ap.add_argument("--sheet-name", default=None)
    ap.add_argument("--spreadsheet", default=SPREADSHEET_ID)
    ap.add_argument("--dry-run", action="store_true", help="シートに書かない")
    ap.add_argument("--from-json", default=None, help="保存済み JSON から作る（X API を呼ばない）")
    ap.add_argument("--overwrite", action="store_true", help="同名シートを消して書き直す")
    args = ap.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=JST)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=JST) + timedelta(days=1)
    sheet_name = args.sheet_name or f"{args.username} {start.strftime('%Y-%m')}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / f"{args.username}_{args.start}_{args.end}.json"

    if args.from_json:
        saved = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
        user, tweets = saved["user"], saved["tweets"]
        log(f"JSON から読み込み: {len(tweets)} 件（{args.from_json}）")
    else:
        token = os.getenv("X_BEARER_TOKEN", "").strip()
        if not token:
            log("ERROR: X_BEARER_TOKEN が未設定（.env を確認）")
            return 1
        user = get_user(token, args.username)
        log(f"@{user['username']} id={user['id']} 総投稿 {user['public_metrics']['tweet_count']:,}")
        tweets = fetch_timeline(token, user["id"], start, end)
        json_path.write_text(json.dumps({"user": user, "tweets": tweets}, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        log(f"取得 {len(tweets)} 件 → {json_path}")

    rows = select_rows(tweets, user["id"], user["username"])
    n_head = sum(1 for r in rows if r[9] != "ツリー続き")
    log(f"記録対象 {len(rows)} 行（単独・ツリー先頭 {n_head}、ツリー続き {len(rows) - n_head}、除外 {len(tweets) - len(rows)}）")
    if not rows:
        log("記録する投稿がありません")
        return 20
    if args.dry_run:
        for r in rows[:5]:
            log(f"  {r[0]} {r[9]} IMP={r[3]} {r[11]}")
        log(f"dry-run: シート '{sheet_name}' には書かない")
        return 0
    url = write_sheet(args.spreadsheet, sheet_name, rows, overwrite=args.overwrite)
    log(f"シート '{sheet_name}' に {len(rows)} 行を記録: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
