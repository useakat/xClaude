"""postcal の SQLite 層。Web アプリと cron ランナーが同時に書くので WAL + busy_timeout。

テーブル posts:
  post_date   'YYYY-MM-DD'（JST）   slot 6|12|17|20
  kind        postcal.kinds.KINDS のキー   what_id 記録用
  text        本文   replies_json  セルフリプの配列（X では順に返信チェーン、Threads は ===== 連結）
  media_json  [{"name": "<uuid>.<ext>", "kind": "image"|"video", "orig": "元ファイル名"}]
  threads_enabled 0/1   note_url 任意
  status      queued → posting → posted | failed（skipped は手動用）
  x_url / threads_url / error / posted_at   ランナーが書く
同一 post_date・slot は queued/posting/posted で 1 件まで（枠 = 1 投稿）。
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "postcal", "data")
MEDIA_DIR = os.path.join(DATA_DIR, "media")
DB_PATH = os.path.join(DATA_DIR, "postcal.db")
JST = timezone(timedelta(hours=9))

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_date TEXT NOT NULL,
  slot INTEGER NOT NULL,
  kind TEXT NOT NULL,
  what_id TEXT NOT NULL,
  text TEXT NOT NULL,
  replies_json TEXT NOT NULL DEFAULT '[]',
  media_json TEXT NOT NULL DEFAULT '[]',
  threads_enabled INTEGER NOT NULL DEFAULT 1,
  note_url TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'queued',
  x_url TEXT NOT NULL DEFAULT '',
  threads_url TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  posted_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_posts_date_slot ON posts(post_date, slot);
"""


def now_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


def connect() -> sqlite3.Connection:
    os.makedirs(MEDIA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=5000")
    con.executescript(SCHEMA)
    return con


def _row(r):
    if r is None:
        return None
    d = dict(r)
    d["replies"] = json.loads(d.pop("replies_json") or "[]")
    d["media"] = json.loads(d.pop("media_json") or "[]")
    return d


def list_range(con, start_date: str, end_date: str):
    """start_date <= post_date <= end_date の行（日付・枠順）"""
    cur = con.execute(
        "SELECT * FROM posts WHERE post_date BETWEEN ? AND ? ORDER BY post_date, slot, id",
        (start_date, end_date))
    return [_row(r) for r in cur.fetchall()]


def get(con, post_id: int):
    return _row(con.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone())


def slot_taken(con, post_date: str, slot: int, exclude_id=None):
    """同じ日・枠に有効な予約（queued/posting/posted）があれば その行を返す"""
    q = "SELECT * FROM posts WHERE post_date=? AND slot=? AND status IN ('queued','posting','posted')"
    args = [post_date, slot]
    if exclude_id is not None:
        q += " AND id<>?"
        args.append(exclude_id)
    return _row(con.execute(q, args).fetchone())


def create(con, d: dict) -> int:
    ts = now_jst()
    cur = con.execute(
        "INSERT INTO posts (post_date, slot, kind, what_id, text, replies_json, media_json, threads_enabled, "
        "note_url, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,'queued',?,?)",
        (d["post_date"], d["slot"], d["kind"], d["what_id"], d["text"], json.dumps(d.get("replies", []), ensure_ascii=False),
         json.dumps(d.get("media", []), ensure_ascii=False), 1 if d.get("threads_enabled", True) else 0,
         d.get("note_url", ""), ts, ts))
    con.commit()
    return cur.lastrowid


def update(con, post_id: int, d: dict):
    con.execute(
        "UPDATE posts SET post_date=?, slot=?, kind=?, what_id=?, text=?, replies_json=?, media_json=?, "
        "threads_enabled=?, note_url=?, updated_at=? WHERE id=?",
        (d["post_date"], d["slot"], d["kind"], d["what_id"], d["text"], json.dumps(d.get("replies", []), ensure_ascii=False),
         json.dumps(d.get("media", []), ensure_ascii=False), 1 if d.get("threads_enabled", True) else 0,
         d.get("note_url", ""), now_jst(), post_id))
    con.commit()


def set_status(con, post_id: int, status: str, **fields):
    cols = ["status=?", "updated_at=?"]
    args = [status, now_jst()]
    for k, v in fields.items():
        cols.append(f"{k}=?")
        args.append(v)
    args.append(post_id)
    con.execute(f"UPDATE posts SET {', '.join(cols)} WHERE id=?", args)
    con.commit()


def delete(con, post_id: int):
    con.execute("DELETE FROM posts WHERE id=?", (post_id,))
    con.commit()


def claim_due(con, post_date: str, slot: int):
    """その日・枠の queued 行を 1 件、原子的に posting にして返す（cron 重複時の二重投稿防止）。無ければ None"""
    r = con.execute(
        "SELECT id FROM posts WHERE post_date=? AND slot=? AND status='queued' ORDER BY id LIMIT 1",
        (post_date, slot)).fetchone()
    if not r:
        return None
    cur = con.execute("UPDATE posts SET status='posting', updated_at=? WHERE id=? AND status='queued'",
                      (now_jst(), r["id"]))
    con.commit()
    if cur.rowcount != 1:
        return None
    return get(con, r["id"])
