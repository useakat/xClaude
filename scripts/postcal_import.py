#!/usr/bin/env python3
"""postcal_import.py — scheduled-posts の予約ファイル(Markdown)を postcal.db に取り込む。

z01 フロー（projects/z01/spec.md STEP 6）は Gmail 下書きを作らず、確定稿を
`outputs/scheduled-posts/z01/*.md` に書いて master へ push する。このスクリプトは VPS で
systemd timer（postcal-import.timer）から定期実行され、次を行う:

  1. git pull --ff-only で最新の予約ファイルを取り込む（--no-pull で省略）
  2. outputs/scheduled-posts/**/*.md を走査し、front-matter と「## 投稿文」「## セルフリプ」を取り出す
  3. front-matter の uid をキーに postcal.db へ upsert:
       - 新規 uid → **下書き（status=draft）**として db.create()。仮の日時は週間短文パターンの
         「今日以降で最も近い空き短文枠」（他の下書きの仮枠とも重ならないように選ぶ）。
         下書きは cron に拾われない＝よーんが画面（post.usephys.net）で内容を確認・修正し、
         「投稿予約」を押して初めて queued になり、枠の cron が投稿する（2026-11-21〜）
       - 既知 uid かつ予約が draft → ファイルの本文・リプ・note_url の変更を db.update()（枠は動かさない）。
         ただし画面で編集済みの下書きは上書きしない（画面の編集を正とする）
       - 既知 uid かつ予約が draft 以外（queued/failed/posted…）→ 触らない（予約・投稿後の本文変更は画面から行う）
  4. 取込状態（uid→post_id・本文ハッシュ）を postcal/data/import_state.json（git管理外）に保存
  5. 画面で削除された予約（postcal.db の deleted_posts に記録がある）の予約ファイルは、再登録せず、
     git から消して master に commit・push する（2026-11-27〜。それまではファイルが残っているかぎり
     次の取り込みで下書きが復活していた）。push できなかったときは元に戻し、次回の実行でやり直す。
     削除のあとに予約ファイルが書き換えられていた場合は、消さずに新しい下書きとして登録する

週間スケジュールの短文枠（よーん決定 2026-11-19）: 1短文の日は 6:00、2短文の日は 6:00→17:00。
  月[6] 火[6,17] 水[6] 木[6,17] 金[] 土[6] 日[6]

販促（kind: promo → W007）は短文パターンではなく「金曜 6:00」の最寄りの空き枠へ入れる（よーん決定 2026-11-19）。
リライト（kind: rewrite_short|rewrite_onepoint|rewrite_long → z01r/W003r/W001r）は「毎週土曜 20:00」の最寄りの空き枠へ入れる
（従来の Gmail 運用で 20 時枠が既定だったため踏襲。2026-11-21）。
front-matter に post_date（YYYY-MM-DD）と slot（6/12/17/20）を両方書いた場合は、それを優先する（新規登録時のみ有効）。

投稿は一切しない（予約の登録・更新のみ）。X 投稿は既存の 4 枠 cron（post_scheduled.py）が行う。
失敗（git pull・パース・DB 例外・予約ファイルの削除が 30 分続けてできない）は send_gmail.sh でよーんに通知する。
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
# 販促（kind: promo）の既定枠: 金曜(4) 6 時。埋まっていれば翌週の金曜へ
PROMO_SLOTS = {4: [6]}
# リライト（kind: rewrite_*）の既定枠: 毎週土曜(5) 20 時。埋まっていれば翌週の土曜へ（よーん決定 2026-11-26）
REWRITE_SLOTS = {5: [20]}
SEARCH_DAYS = 120  # 空き短文枠をこの日数先まで探す（事実上いつでも見つかる）

FM_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.S)
H_TEXT_RE = re.compile(r"^##[ \t]+投稿文[ \t]*$", re.M)
H_REPLY_RE = re.compile(r"^##[ \t]+セルフリプ[ \t]*$", re.M)
H_REC_RE = re.compile(r"^##[ \t]+記録[ \t]*$", re.M)
REPLY_SPLIT_RE = re.compile(r"^[ \t]*={3,}[ \t]*$", re.M)   # post_threads.py / postcal と同じ
NONE_WORDS = {"", "なし", "（なし）", "(なし)", "-", "—", "ー"}
# session_url として採用する形（原稿を作った Claude セッションへのリンク。画面に出すので claude.ai のものだけ許可する）
SESSION_URL_RE = re.compile(r"^https://claude\.ai/code/[A-Za-z0-9_-]+$")

# neta_id として採用する source の形。noteNeta/newsTopics は record_output.py が z01 投稿時に SS1 の
# 「短文最終使用日」を更新する紐付けキー。rewrite[ツイートID] はリライト元の記録（outputs の neta_id 列に入り、
# rewrite_pool.py の「リライト済み」判定に使われる）。それ以外の source は neta_id にしない
NETA_REF_RE = re.compile(r"^(?:(?:noteNeta|newsTopics)\[\d+\]|rewrite\[\d+\])$")


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
    source = (fm.get("source") or "").strip()
    neta_id = source if NETA_REF_RE.match(source) else ""   # シート参照のみ採用（投稿時に SS1 を更新）
    session_url = (fm.get("session_url") or "").strip()
    if not SESSION_URL_RE.match(session_url):
        session_url = ""   # 形が違うもの（claude.ai 以外など）は採用しない
    # 枠の明示指定（任意・両方そろった場合のみ有効）。無ければ種類ごとの既定枠で自動割当
    want_date = (fm.get("post_date") or "").strip()
    want_slot = (fm.get("slot") or "").strip()
    if want_date or want_slot:
        try:
            datetime.strptime(want_date, "%Y-%m-%d")
            slot_n = int(want_slot)
        except ValueError:
            raise ValueError(f"{os.path.relpath(path, ROOT)}: post_date は YYYY-MM-DD、slot は整数で両方指定してください")
        if slot_n not in kinds.SLOTS:
            raise ValueError(f"{os.path.relpath(path, ROOT)}: slot は {kinds.SLOTS} のいずれかです")
        want_slot = slot_n
    else:
        want_date, want_slot = "", None
    return {
        "uid": uid,
        "want_date": want_date,
        "want_slot": want_slot,
        "kind": kind,
        "what_id": what_id,
        "neta_id": neta_id,
        "session_url": session_url,
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
        rec["neta_id"],
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def post_hash(post: dict) -> str:
    """DB の予約行の内容ハッシュ。content_hash(rec) と同じ項目・同じ式なので、
    取り込み直後（画面で未編集）なら state の hash と一致し、画面で編集されていれば食い違う"""
    return content_hash({
        "text": post["text"], "replies": post["replies"], "note_url": post["note_url"],
        "threads_enabled": bool(post["threads_enabled"]), "kind": post["kind"],
        "what_id": post["what_id"], "neta_id": post["neta_id"],
    })


# ---------------- 空き短文枠の探索 ----------------

def next_free_slot(con, after: datetime, pattern: dict):
    """after（JST）以降で最も近い、pattern（weekday -> 枠のリスト）の空き枠 (post_date, slot) を返す。無ければ (None, None)"""
    for off in range(SEARCH_DAYS):
        day = (after + timedelta(days=off)).date()
        for slot in sorted(pattern.get(day.weekday(), [])):
            if off == 0 and slot <= after.hour:
                continue  # 今日の枠は時刻未経過のものだけ（cron はその時刻にしか拾わない）
            ds = day.isoformat()
            if not db.slot_taken(con, ds, slot, include_drafts=True):   # 他の下書きの仮枠とも重ねない
                return ds, slot
    return None, None


def next_free_short_slot(con, after: datetime):
    return next_free_slot(con, after, SHORT_SLOTS)


def pick_slot(con, rec: dict, now: datetime):
    """新規予約の (post_date, slot)。明示指定 > 販促の既定(金曜6時) > リライトの既定(毎日20時) > 短文パターン"""
    if rec.get("want_date") and rec.get("want_slot"):
        if db.slot_taken(con, rec["want_date"], rec["want_slot"], include_drafts=True):
            return None, None  # 指定枠が埋まっている（勝手に別枠へ動かさない）
        return rec["want_date"], rec["want_slot"]
    if rec["kind"] == "promo":
        return next_free_slot(con, now, PROMO_SLOTS)
    if rec["kind"].startswith("rewrite"):
        return next_free_slot(con, now, REWRITE_SLOTS)
    return next_free_short_slot(con, now)


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


def _git(*args):
    """ROOT で git を実行する。systemd から呼ばれても ~/.gitconfig（コミットの名義）を読めるよう HOME を補う"""
    env = dict(os.environ)
    env.setdefault("HOME", os.path.expanduser("~"))
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=180, env=env)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(["git", *args], 124, "", "timeout")


def remove_reservation_files(paths: list):
    """画面で削除された予約のファイルを git から消し、master に commit・push する。

    戻り値は (消せたパスの集合, 消せなかった理由)。失敗したときは作業ツリーを元に戻す（次回の実行でやり直す）。
      - ローカルの master が origin/master と一致しているときだけ行う
        （このリポジトリでは他のセッションも作業する。その未 push のコミットを一緒に push しないため）
      - 対象のパスだけを commit する（作業ツリーの他の変更・ステージ済みの変更は含めない）
      - 未コミットの変更がある／git 管理外の予約ファイルは消さない（誰かの作業中の可能性があるため）
    """
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    head = _git("rev-parse", "HEAD").stdout.strip()
    remote = _git("rev-parse", "origin/master").stdout.strip()
    if branch != "master" or not head or head != remote:
        return set(), f"ローカルが origin/master と一致していません（branch={branch} HEAD={head[:7]} origin/master={remote[:7]}）"

    clean, skipped = [], []
    for p in paths:
        tracked = _git("ls-files", "--error-unmatch", "--", p).returncode == 0
        dirty = _git("status", "--porcelain", "--", p).stdout.strip()
        (clean if tracked and not dirty else skipped).append(p)
    why = f"未コミットの変更がある／git 管理外のため消していません: {', '.join(skipped)}" if skipped else ""
    if not clean:
        return set(), why

    def restore():
        _git("restore", "--source=HEAD", "--staged", "--worktree", "--", *clean)

    r = _git("rm", "--quiet", "--", *clean)
    if r.returncode != 0:
        restore()
        return set(), f"git rm 失敗: {(r.stderr or r.stdout).strip()[-300:]}"
    msg = (f"postcal: 画面で削除した予約のファイルを削除（{len(clean)} 件）\n\n"
           + "\n".join(f"- {p}" for p in clean)
           + "\n\nscripts/postcal_import.py による自動コミット")
    r = _git("commit", "--quiet", "-m", msg, "--", *clean)
    if r.returncode != 0:
        restore()
        return set(), f"git commit 失敗: {(r.stderr or r.stdout).strip()[-300:]}"
    sha = _git("rev-parse", "HEAD").stdout.strip()
    r = _git("push", "--quiet", "origin", "HEAD:master")
    if r.returncode != 0:
        # push できなかったコミットを残すと、次回の git pull --ff-only が通らなくなる。自分のコミットだけを取り消す
        if _git("rev-parse", "HEAD").stdout.strip() == sha and _git("rev-parse", "HEAD~1").stdout.strip() == head:
            _git("reset", "--quiet", "--soft", head)
            restore()
        return set(), f"git push 失敗: {(r.stderr or r.stdout).strip()[-300:]}"
    return set(clean), why


# ---------------- メイン ----------------

def upsert(con, rec: dict, state: dict, now: datetime, dry_run: bool, deleted=frozenset()) -> str:
    """1 件の予約ファイルを DB に反映。戻り値は action（created/updated/skip/locked/edited/deleted/error）。
    deleted は画面で削除された予約の id（db.deleted_ids）"""
    uid = rec["uid"]
    h = content_hash(rec)
    st = state.get(uid)

    if st and st.get("post_id"):
        post = db.get(con, st["post_id"])
        if post is None and st["post_id"] in deleted:
            # 画面で削除された予約 → 再登録しない（ファイルの削除は main() がまとめて行う）
            if st.get("hash") == h:
                return "deleted"
            # 削除のあとに予約ファイルが書き換えられている（改稿）→ まだ誰も見ていない版なので、消さずに新しい下書きにする
            log(f"削除済み #{st['post_id']} の予約ファイルが書き換えられているため、新しい下書きとして登録します / {rec['path']}")
            st = None
        elif post is None:
            st = None  # 削除の記録が無いのに DB に無い（DB の作り直しなど）→ 新規として作り直す
        elif post["status"] != "draft":
            # 予約済み（queued）・投稿済み・失敗などは、ファイルが変わっても本文を動かさない
            # （投稿予約後・投稿後の修正は画面から行う）。再評価を止めるため記録だけ更新
            if st.get("hash") != h:
                if not dry_run:
                    state[uid]["hash"] = h
                log(f"スキップ #{post['id']}（status={post['status']} のため、ファイルの変更は反映しません / {rec['path']}）")
            return "locked"
        else:  # draft
            if st.get("hash") == h:
                return "skip"
            if post_hash(post) != st.get("hash"):
                # 画面で編集済みの下書き → 画面の編集を正とし、ファイルでは上書きしない
                if not dry_run:
                    state[uid]["hash"] = h
                log(f"スキップ #{post['id']}（画面で編集済みの下書きのため、ファイルの変更は反映しません / {rec['path']}）")
                return "edited"
            if not dry_run:
                db.update(con, post["id"], {
                    "post_date": post["post_date"], "slot": post["slot"],
                    "kind": rec["kind"], "what_id": rec["what_id"], "neta_id": rec["neta_id"],
                    "session_url": rec["session_url"] or post["session_url"],
                    "text": rec["text"], "replies": rec["replies"], "media": post["media"],
                    "threads_enabled": rec["threads_enabled"], "note_url": rec["note_url"],
                })
                state[uid]["hash"] = h
            log(f"更新 #{post['id']}（下書き {post['post_date']} {post['slot']}時 / {rec['path']}）")
            return "updated"

    # 新規
    ds, slot = pick_slot(con, rec, now)
    if ds is None:
        notify("【postcal-import】空き枠が見つかりません",
               f"{rec['path']} を登録する空き枠が見つかりませんでした"
               f"（kind={rec['kind']} / 指定={rec.get('want_date') or 'なし'} {rec.get('want_slot') or ''}）。")
        return "error"
    if dry_run:
        log(f"[DRY] 下書き登録予定 → 仮枠 {ds} {slot}時 / {rec['kind']}→{rec['what_id']} / {rec['path']}")
        return "created"
    if db.slot_taken(con, ds, slot, include_drafts=True):  # 直前の取り合い対策で再確認
        ds, slot = pick_slot(con, rec, now)
        if ds is None:
            return "error"
    post_id = db.create(con, {
        "post_date": ds, "slot": slot, "kind": rec["kind"], "what_id": rec["what_id"], "neta_id": rec["neta_id"],
        "session_url": rec["session_url"],
        "text": rec["text"], "replies": rec["replies"],
        "threads_enabled": rec["threads_enabled"], "note_url": rec["note_url"],
        "status": "draft",   # よーんが画面で「投稿予約」を押すまで cron は拾わない
    })
    state[uid] = {"post_id": post_id, "hash": h, "file": rec["path"], "post_date": ds, "slot": slot}
    log(f"下書き登録 #{post_id}（仮枠 {ds} {slot}時 / {rec['kind']}→{rec['what_id']} / {rec['path']}）"
        "→ 画面で確認して「投稿予約」を押すと投稿されます")
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
    seen = set()       # 今回の走査で読めた予約ファイルの uid
    to_remove = []     # 画面で削除された予約の (uid, 予約ファイルのパス)
    try:
        deleted = db.deleted_ids(con)
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
            seen.add(rec["uid"])
            try:
                action = upsert(con, rec, state, now, args.dry_run, deleted)
            except Exception as e:  # noqa: BLE001
                log(f"❌ 取込失敗: {rec['path']}: {e}")
                errors.append(f"{rec['path']}: {e}")
                action = "error"
            if action == "deleted":
                to_remove.append((rec["uid"], rec["path"]))
                continue
            counts[action] = counts.get(action, 0) + 1
    finally:
        con.close()

    # 画面で削除された予約の予約ファイルを消す（git rm → commit → push）
    if to_remove and args.dry_run:
        for _, p in to_remove:
            log(f"[DRY] 画面で削除済みの予約 → 予約ファイルを削除予定 / {p}")
        counts["remove_pending"] = len(to_remove)
    elif to_remove:
        removed, why = remove_reservation_files([p for _, p in to_remove])
        stuck = []
        for uid, p in to_remove:
            if p in removed:
                log(f"予約ファイルを削除（画面で削除済み #{state[uid]['post_id']} / {p}）→ master に push しました")
                del state[uid]   # 同じ uid のファイルがあとで作り直されたら、新規として登録する
                counts["removed"] = counts.get("removed", 0) + 1
            else:
                n = state[uid]["rm_fail"] = state[uid].get("rm_fail", 0) + 1
                counts["remove_pending"] = counts.get("remove_pending", 0) + 1
                if n == 3 or n % 144 == 0:   # 30 分続いたら知らせる。その後は 1 日に 1 回
                    stuck.append(f"{p}（{n} 回目）")
        if why:
            log(f"⚠ 予約ファイルを削除できませんでした（次回やり直します。下書きは復活しません）: {why}")
        if stuck:
            notify("【postcal-import】削除した予約のファイルを消せません",
                   "画面で削除した予約の予約ファイルを、git から消して master に push できない状態が続いています。\n"
                   "下書きが復活することはありませんが、ファイルはリポジトリに残っています。\n\n"
                   + "\n".join(stuck) + f"\n\n理由: {why}\n\nVPS: {ROOT}")

    if not args.dry_run:
        # 予約ファイルがもう無い「削除済み」の予約は、取込状態から外す
        for uid in [u for u, st in state.items()
                    if st.get("post_id") in deleted and u not in seen
                    and st.get("file") and not os.path.exists(os.path.join(ROOT, st["file"]))]:
            del state[uid]
        save_state(state)
    log("集計: " + " / ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts else "集計: 変更なし")
    if errors:
        notify("【postcal-import】取込エラー",
               "postcal_import.py で取り込めなかった予約ファイルがあります。\n\n" + "\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
