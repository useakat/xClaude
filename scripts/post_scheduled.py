#!/usr/bin/env python3
"""
postcal（予約カレンダー）の予約を、cron の枠で X と Threads に投稿する。

使い方（run_xonepoint_post.sh 等の先頭から呼ぶ。Gmail キューより先）:
  python3 scripts/post_scheduled.py <6|12|17|20> [--dry-run] [--date YYYY-MM-DD]

流れ（post_from_email.sh L205-300 と同じ順序）:
  1. 今日（JST）の枠で status=queued の行を 1 件、原子的に posting にする。無ければ exit 20
  2. X: post_to_x.py --text 本文 [--image f …]|[--video f] → stdout の https://x.com/i/web/status/<id> を取る
     セルフリプは 1 段ずつ --reply-to <直前の id> で返信チェーン（note リンクは post_to_x.py が xpost.usephys.net に変換）
  3. record_output.py <tweet_url> <what_id> --neta-id "postcal[<id>]" [--note-url …]
  4. Threads（threads_enabled かつ MIRROR_THREADS=1・非致命）: post_threads.py --text 本文
     [--image-url <公開URL …>]|[--video-url <公開URL>] [--reply-text "段1\n=====\n段2"]
     note.com を含むリプ段は Threads に載せない（2026-10-02 のルール）。PERMALINK= を取って
     record_output.py <permalink> --x-url <tweet_url>
  5. 行を posted / failed に更新。失敗時は send_gmail.sh でよーんに通知
終了コード: 0 投稿した / 20 投稿対象なし / 1 失敗（ラッパーは 20 のときだけ Gmail キューへ進む）
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from postcal import db, kinds  # noqa: E402

SCRIPTS = os.path.join(ROOT, "scripts")
LOG_PATH = os.path.join(ROOT, "logs", "post_scheduled.log")
MAIL_TO = "useakat@gmail.com"
JST = ZoneInfo("Asia/Tokyo")
TWEET_URL_RE = re.compile(r"https://x\.com/i/web/status/[0-9]+")
PY = sys.executable or "python3"


def log(msg: str):
    line = f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd: list, dry_run: bool) -> tuple[int, str]:
    """サブプロセスを実行して (rc, 出力) を返す。dry-run はコマンドを表示するだけ"""
    shown = " ".join(_q(c) for c in cmd)
    if dry_run:
        log(f"[DRY RUN] {shown}")
        return 0, ""
    log(f"$ {shown[:300]}")
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    out = (p.stdout or "") + (p.stderr or "")
    for ln in out.rstrip().splitlines():
        log("  " + ln)
    return p.returncode, out


def _q(s: str) -> str:
    s = str(s)
    if "\n" in s or " " in s:
        return "'" + s.replace("\n", "\\n")[:80] + ("…'" if len(s) > 80 else "'")
    return s


def notify_failure(post: dict, error: str, dry_run: bool):
    if dry_run:
        return
    body = (f"postcal の予約 #{post['id']}（{post['post_date']} {post['slot']}時 / {post['what_id']}）の投稿に失敗しました。\n\n"
            f"{error}\n\n本文冒頭: {post['text'][:80]}\n\nhttps://post.usephys.net/posts/{post['id']}\n")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(body)
        path = f.name
    try:
        subprocess.run(["bash", os.path.join(SCRIPTS, "send_gmail.sh"), "--to", MAIL_TO,
                        "--subject", f"【postcal】投稿失敗 #{post['id']} {post['post_date']} {post['slot']}時",
                        "--body-file", path], capture_output=True, text=True, cwd=ROOT, timeout=120)
    except Exception as e:  # 通知の失敗は本処理を止めない
        log(f"⚠ 失敗通知メールを送れませんでした: {e}")
    finally:
        os.unlink(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slot", type=int, choices=kinds.SLOTS)
    ap.add_argument("--dry-run", action="store_true", help="投稿せずコマンド列を表示。行の状態も変えない")
    ap.add_argument("--date", default="", help="対象日（既定: 今日 JST）。テスト用")
    args = ap.parse_args()

    today = args.date or datetime.now(JST).strftime("%Y-%m-%d")
    con = db.connect()
    try:
        if args.dry_run:
            r = con.execute("SELECT id FROM posts WHERE post_date=? AND slot=? AND status='queued' ORDER BY id LIMIT 1",
                            (today, args.slot)).fetchone()
            post = db.get(con, r["id"]) if r else None
        else:
            post = db.claim_due(con, today, args.slot)
        if not post:
            log(f"{today} {args.slot}時: 予約なし")
            return 20
        log(f"予約 #{post['id']} を処理（{post['post_date']} {post['slot']}時 / {post['kind']} → {post['what_id']} / "
            f"メディア{len(post['media'])} / リプ{len(post['replies'])} / Threads={'ON' if post['threads_enabled'] else 'OFF'}）")

        # ---- X 本文 ----
        images = [os.path.join(db.MEDIA_DIR, m["name"]) for m in post["media"] if m["kind"] == "image"]
        videos = [os.path.join(db.MEDIA_DIR, m["name"]) for m in post["media"] if m["kind"] == "video"]
        missing = [p for p in images + videos if not os.path.exists(p)]
        if missing:
            err = f"メディアファイルが見つかりません: {', '.join(os.path.basename(m) for m in missing)}"
            log("❌ " + err)
            if not args.dry_run:
                db.set_status(con, post["id"], "failed", error=err)
                notify_failure(post, err, args.dry_run)
            return 1

        cmd = [PY, os.path.join(SCRIPTS, "post_to_x.py"), "--text", post["text"]]
        for p in images[:kinds.MAX_IMAGES]:
            cmd += ["--image", p]
        if videos:
            cmd += ["--video", videos[0]]
        rc, out = run(cmd, args.dry_run)
        tweet_url = (TWEET_URL_RE.findall(out) or ["https://x.com/i/web/status/DRYRUN"])[-1] if (args.dry_run or rc == 0) else ""
        if rc != 0 or not tweet_url:
            err = f"X 投稿失敗 (rc={rc}): {out.strip()[-500:]}"
            log("❌ " + err)
            if not args.dry_run:
                db.set_status(con, post["id"], "failed", error=err)
                notify_failure(post, err, args.dry_run)
            return 1
        tweet_id = tweet_url.rsplit("/", 1)[-1]
        log(f"✓ X 投稿: {tweet_url}")

        # ---- X セルフリプ（返信チェーン） ----
        reply_errors = []
        prev_id = tweet_id
        for i, rep in enumerate(post["replies"], 1):
            rc, out = run([PY, os.path.join(SCRIPTS, "post_to_x.py"), "--text", rep, "--reply-to", prev_id], args.dry_run)
            urls = TWEET_URL_RE.findall(out)
            if args.dry_run:
                prev_id = f"DRYRUN{i}"
            elif rc != 0 or not urls:
                reply_errors.append(f"リプ{i} 失敗 (rc={rc}): {out.strip()[-300:]}")
                log(f"⚠ {reply_errors[-1]}")
                break  # 以降の段は親が無いので止める
            else:
                prev_id = urls[-1].rsplit("/", 1)[-1]
                log(f"✓ リプ{i}: {urls[-1]}")

        # ---- 記録（X） ----
        # neta_id が元シート参照（noteNeta[..] 等）なら それを使う（record_output.py が z01 の
        # SS1「短文最終使用日」を更新できる）。無ければ従来どおり予約 id を記録する。
        neta_id = post.get("neta_id") or f"postcal[{post['id']}]"
        rec = [PY, os.path.join(SCRIPTS, "record_output.py"), tweet_url, post["what_id"], "--neta-id", neta_id]
        if post["note_url"]:
            rec += ["--note-url", post["note_url"]]
        run(rec, args.dry_run)

        # ---- Threads 転載（非致命） ----
        threads_url = ""
        th_note = ""
        if post["threads_enabled"] and os.environ.get("MIRROR_THREADS", "0") == "1":
            th = [PY, os.path.join(SCRIPTS, "post_threads.py"), "--text", post["text"]]
            if images:
                th += ["--image-url", " ".join(kinds.media_url(os.path.basename(p)) for p in images)]
            elif videos:
                th += ["--video-url", kinds.media_url(os.path.basename(videos[0]))]
            th_replies = [r for r in post["replies"] if "note.com" not in r]
            dropped = len(post["replies"]) - len(th_replies)
            if dropped:
                log(f"Threads: note リンクを含むリプ {dropped} 段は転載しない")
            if th_replies:
                th += ["--reply-text", "\n=====\n".join(th_replies)]
            rc, out = run(th, args.dry_run)
            m = re.findall(r"^PERMALINK=(\S+)", out, re.M)
            if args.dry_run:
                threads_url = "(dry-run)"
            elif rc == 0 and m:
                threads_url = m[-1]
                log(f"✓ Threads 転載: {threads_url}")
                run([PY, os.path.join(SCRIPTS, "record_output.py"), threads_url, "--x-url", tweet_url], args.dry_run)
            else:
                th_note = f"Threads 転載失敗 (rc={rc}): {out.strip()[-300:]}"
                log("⚠ " + th_note + "（X 投稿は成功済み）")
        elif post["threads_enabled"]:
            log("Threads: MIRROR_THREADS が未設定のため転載しない")

        if not args.dry_run:
            note = "\n".join(reply_errors + ([th_note] if th_note else []))
            db.set_status(con, post["id"], "posted", x_url=tweet_url, threads_url=threads_url if threads_url != "(dry-run)" else "",
                          error=note, posted_at=db.now_jst())
            if note:
                notify_failure(post, "X 本文は投稿済み。以下は部分的な失敗:\n" + note, args.dry_run)
        log(f"✓ 予約 #{post['id']} 完了")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
