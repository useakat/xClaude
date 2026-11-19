#!/usr/bin/env python3
"""postcal_import.py — scheduled-posts の予約ファイル(Markdown)を postcal.db に取り込む。

z01 フロー（projects/z01/spec.md STEP 6）は Gmail 下書きを作らず、確定稿を
`outputs/scheduled-posts/z01/*.md` に書いて master へ push する。このスクリプトは VPS で
systemd timer（postcal-import.timer）から定期実行され、次を行う:

  1. git pull --ff-only で最新の予約ファイルを取り込む（--no-pull で省略）
  2. outputs/scheduled-posts/**/*.md を走査し、front-matter と「## 投稿文」「## セルフリプ」を取り出す
  3. front-matter の uid をキーに postcal.db へ upsert:
       - 新規 uid → 週間短文パターンの「今日以降で最も近い空き短文枠」へ db.create()
       - 既知 uid かつ予約が queued/failed → 本文・リプ・note_url の変更を db.update()（枠は動かさない）
       - 既知 uid かつ予約が posted/posting → 触らない（投稿済みは確定）
  4. 取込状態（uid→post_id・本文ハッシュ）を postcal/data/import_state.json（git管理外）に保存

週間スケジュールの短文枠（よーん決定 2026-11-19）: 1短文の日は 6:00、2短文の日は 6:00→17:00。
  月[6] 火[6,17] 水[6] 木[6,17] 金[] 土[6] 日[6]

投稿は一切しない（予約の登録・更新のみ）。X 投稿は既存の 4 枠 cron（post_scheduled.py）が行う。
失敗（git pull・パース・DB 例外）は send_gmail.sh でよーんに通知する。
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from postcal import db, kinds  # noqa: E402

SCRIPTS = os.path.join(ROOT, "scripts")
SCHED_DIR = os.path.join(ROOT, "outputs", "scheduled-posts")
STATE_PATH = os.path.join(db.DATA_DIR, "import_state.json")
LOG_PATH = os.path.join(ROOT, "logs", "postcal_import.log")
MAIL_TO = "useakat@gmail.com"

# 週間短文パターン: weekday(月=0 … 日=6) -> 使う枠（昇順で近い方＝6 を先に埋める）
SHORT_SLOTS = {0: [6], 1: [6, 17], 2: [6], 3: [6, 17], 4: [], 5: [6], 6: [6]}
SEARCH_DAYS = 120  # 空き短文枠をこの日数先まで探す（事実上いつでも見つかる）

FM_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.S)
H_TEXT_RE = re.compile(r"^##[ \t]+投稿文[ \t]*$", re.M)
H_REPLY_RE = re.compile(r"^##[ \t]+セルフリプ[ \t]*$", re.M)
H_REC_RE = re.compile(r"^##[ \t]+記録[ \t]*$", re.M)
REPLY_SPLIT_RE = re.compile(r"^[ \t]*={3,}[ \t]*$", re.M)   # post_threads.py / postcal と同じ
NONE_WORDS = {"", "なし", "（なし）", "(なし)", "-", "—", "ー"}


def log(msg: str):
    line = f"[{db.now_jst()} JST] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def notify(subject: str, body: str):
    """send_gmail.sh でよーんに通知（失敗しても本処理は止めない）"""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(body)
        path = f.name
    try:
        subprocess.run(["bash", os.path.join(SCRIPTS, "send_gmail.sh"), "--to", MAIL_TO,
                        "--subject", subject, "--body-file", path],
                       capture_output=True, text=True, cwd=ROOT, timeout=120)
    except Exception as e:  # noqa: BLE001
        log(f"⚠ 通知メールを送れませんでした: {e}")
    finally:
        os.unlink(path)


# ---------------- 予約ファイルのパース ----------------

def parse_front_matter(text: str) -> dict:
    """先頭の YAML 風 front-matter を key: value（スカラーのみ）で読む。PyYAML には依存しない。"""
    m = FM_RE.search(text)
    if not m:
        return {}
    fm = {}
    for raw in m.group(1).splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        fm[key] = val
    return fm


def _section(text: str, start_re, *end_res) -> str | None:
    """start 見出しの次行から、最初に現れる end 見出し（なければ末尾）までを返す。見出しが無ければ None"""
    m = start_re.search(text)
    if not m:
        return None
    start = m.end()
    end = len(text)
    for er in end_res:
        em = er.search(text, start)
        if em and em.start() < end:
            end = em.start()
    return text[start:end].strip()


def parse_record(path: str) -> dict | None:
    """予約ファイルを読む。投稿可能（投稿文が非空）なら dict、そうでなければ None。"""
    with open(path, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    fm = parse_front_matter(text)
    uid = (fm.get("uid") or "").strip()
    if not uid:
        raise ValueError(f"{os.path.relpath(path, ROOT)}: front-matter に uid がありません")

    body = _section(text, H_TEXT_RE, H_REPLY_RE, H_REC_RE)
    post_text = (body or "").strip()
    if not post_text:
        return None  # 投稿文が空＝まだ投稿対象でない（スキップ）

    reply_block = _section(text, H_REPLY_RE, H_REC_RE)
    replies = []
    if reply_block and reply_block.strip() not in NONE_WORDS:
        replies = [s.strip() for s in REPLY_SPLIT_RE.split(reply_block) if s.strip() and s.strip() not in NONE_WORDS]

    kind = (fm.get("kind") or "short").strip()
    what_id = (fm.get("what_id") or kinds.KINDS.get(kind, ("", ""))[1] or "z01").strip()
    te = (fm.get("threads_enabled") or "true").strip().lower()
    threads_enabled = te not in ("false", "0", "no", "off", "")
    return {
        "uid": uid,
        "kind": kind,
        "what_id": what_id,
        "text": post_text,
        "replies": replies,
        "note_url": (fm.get("note_url") or "").strip(),
        "threads_enabled": threads_enabled,
        "path": os.path.relpath(path, ROOT),
    }


def content_hash(rec: dict) -> str:
    key = "\u0001".join([
        rec["text"],
        "\u0002".join(rec["replies"]),
        rec["note_url"],
        "1" if rec["threads_enabled"] else "0",
        rec["kind"],
        rec["what_id"],
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ---------------- 空き短文枠の探索 ----------------

def next_free_short_slot(con, after: datetime):
    """after（JST）以降で最も近い、週間パターンの空き短文枠 (post_date, slot) を返す。無ければ (None, None)"""
    for off in range(SEARCH_DAYS):
        day = (after + timedelta(days=off)).date()
        for slot in sorted(SHORT_SLOTS.get(day.weekday(), [])):
            if off == 0 and slot <= after.hour:
                continue  # 今日の枠は時刻未経過のものだけ（cron はその時刻にしか拾わない）
            ds = day.isoformat()
            if not db.slot_taken(con, ds, slot):
                return ds, slot
    return None, None


# ---------------- state ----------------

def load_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


# ---------------- git ----------------

def git_pull() -> bool:
    r = subprocess.run(["git", "pull", "--ff-only", "--quiet"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        log(f"⚠ git pull 失敗（既存ファイルのみ取り込む）: {err[-400:]}")
        notify("【postcal-import】git pull 失敗",
               f"postcal_import.py の git pull --ff-only が失敗しました。\n\n{err[-800:]}\n\n"
               f"手元で rebase/解消が要ります（VPS: {ROOT}）。")
        return False
    return True


# ---------------- メイン ----------------

def upsert(con, rec: dict, state: dict, now: datetime, dry_run: bool) -> str:
    """1 件の予約ファイルを DB に反映。戻り値は action（created/updated/skip/locked/requeued/error）"""
    uid = rec["uid"]
    h = content_hash(rec)
    st = state.get(uid)

    if st and st.get("post_id"):
        post = db.get(con, st["post_id"])
        if post is None:
            st = None  # DB から消えている → 新規として作り直す
        elif post["status"] in ("posted", "posting"):
            if st.get("hash") != h:
                state[uid]["hash"] = h  # 投稿済みは本文を変えないが、再評価を止めるため記録だけ更新
            return "locked"
        else:  # queued / failed / skipped
            if st.get("hash") == h:
                return "skip"
            if not dry_run:
                db.update(con, post["id"], {
                    "post_date": post["post_date"], "slot": post["slot"],
                    "kind": rec["kind"], "what_id": rec["what_id"],
                    "text": rec["text"], "replies": rec["replies"], "media": post["media"],
                    "threads_enabled": rec["threads_enabled"], "note_url": rec["note_url"],
                })
                if post["status"] == "failed":
                    db.set_status(con, post["id"], "queued", error="")
                state[uid]["hash"] = h
            log(f"更新 #{post['id']}（{post['post_date']} {post['slot']}時 / {rec['path']}）")
            return "requeued" if post["status"] == "failed" else "updated"

    # 新規
    ds, slot = next_free_short_slot(con, now)
    if ds is None:
        notify("【postcal-import】空き短文枠が見つかりません",
               f"{rec['path']} を登録する空き短文枠が {SEARCH_DAYS} 日先まで見つかりませんでした。")
        return "error"
    if dry_run:
        log(f"[DRY] 新規登録予定 → {ds} {slot}時 / {rec['kind']}→{rec['what_id']} / {rec['path']}")
        return "created"
    if db.slot_taken(con, ds, slot):  # 直前の取り合い対策で再確認
        ds, slot = next_free_short_slot(con, now)
        if ds is None:
            return "error"
    post_id = db.create(con, {
        "post_date": ds, "slot": slot, "kind": rec["kind"], "what_id": rec["what_id"],
        "text": rec["text"], "replies": rec["replies"],
        "threads_enabled": rec["threads_enabled"], "note_url": rec["note_url"],
    })
    state[uid] = {"post_id": post_id, "hash": h, "file": rec["path"], "post_date": ds, "slot": slot}
    log(f"登録 #{post_id}（{ds} {slot}時 / {rec['kind']}→{rec['what_id']} / {rec['path']}）")
    return "created"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pull", action="store_true", help="git pull をしない（手動・テスト用）")
    ap.add_argument("--dry-run", action="store_true", help="DB を変えず、登録予定だけ表示")
    args = ap.parse_args()

    if not args.no_pull and not args.dry_run:
        git_pull()

    files = sorted(glob.glob(os.path.join(SCHED_DIR, "**", "*.md"), recursive=True))
    if not files:
        log(f"予約ファイルなし（{os.path.relpath(SCHED_DIR, ROOT)}）")
        return 0

    state = load_state()
    now = datetime.now(db.JST)
    counts = {}
    con = db.connect()
    errors = []
    try:
        for path in files:
            try:
                rec = parse_record(path)
            except Exception as e:  # noqa: BLE001
                log(f"❌ パース失敗: {os.path.relpath(path, ROOT)}: {e}")
                errors.append(f"{os.path.relpath(path, ROOT)}: {e}")
                counts["error"] = counts.get("error", 0) + 1
                continue
            if rec is None:
                counts["empty"] = counts.get("empty", 0) + 1
                continue
            try:
                action = upsert(con, rec, state, now, args.dry_run)
            except Exception as e:  # noqa: BLE001
                log(f"❌ 取込失敗: {rec['path']}: {e}")
                errors.append(f"{rec['path']}: {e}")
                action = "error"
            counts[action] = counts.get(action, 0) + 1
    finally:
        con.close()

    if not args.dry_run:
        save_state(state)
    log("集計: " + " / ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts else "集計: 変更なし")
    if errors:
        notify("【postcal-import】取込エラー",
               "postcal_import.py で取り込めなかった予約ファイルがあります。\n\n" + "\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
