#!/usr/bin/env python3
"""
「X競合分析」のシートから、未送信で最も古い投稿を 1 件 Gmail 下書き（件名【自己開示】）として作り、
送信済み列に作成日を書く（毎日 1 件ずつ競合の投稿を読むための cron 用）。
下書きには空の [投稿文] [/投稿文] が付く。よーんが本文を書いて自分宛に送信すると、
既存の投稿 cron（post_by_label.sh / run_xshort_post.sh）が W004（自己開示）として投稿する。

使い方:
  python3 scripts/x_competitor_daily_mail.py --sheet "ossanworld 2026-05"
  python3 scripts/x_competitor_daily_mail.py --sheet "ossanworld 2026-05" --dry-run   # 作らず・書かず
  python3 scripts/x_competitor_daily_mail.py --sheet "ossanworld 2026-05" --mode send  # 下書きでなく送信（従来動作）

対象シートは fetch_x_user_posts.py が作った形（A 投稿日時 … J ツリー, K 会話ID, M 本文, N 送信済み）。
- 「単独」「ツリー先頭」の未送信行のうち最古のものを選ぶ。ツリー先頭なら同じ会話IDの
  「ツリー続き」行も同じメールに順に載せ、全行に送信日を書く
- 未送信が無くなったら「残りなし」を 1 回だけ（これは下書きでなく送信で）メールし、以後は何もしない
  （通知済みは logs/x_competitor_mail_state.json に記録）

認証: Sheets はサービスアカウント（sheets_values.py と同じ）、送信は send_gmail.sh・下書きは create_gmail_draft.sh（gws）
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from sheets_values import get_client, open_with_retry  # noqa: E402

SPREADSHEET_ID = "1OKQ6zoryoDAQvvKu5kWr9bJD20dO-zfnfrkufLl00tw"  # X競合分析
NOTIFY_TO = "useakat@gmail.com"
STATE_PATH = REPO_ROOT / "logs" / "x_competitor_mail_state.json"
LOG_PATH = REPO_ROOT / "logs" / "x_competitor_mail.log"
SEND_GMAIL = REPO_ROOT / "scripts" / "send_gmail.sh"
DRAFT_GMAIL = REPO_ROOT / "scripts" / "create_gmail_draft.sh"
JST = timezone(timedelta(hours=9))

COL_DATE, COL_ID, COL_URL, COL_IMP, COL_LIKE, COL_RT, COL_REPLY, COL_QUOTE, COL_BOOKMARK, \
    COL_TREE, COL_CONV, COL_FIRST, COL_TEXT, COL_SENT = range(14)
SENT_COL_LETTER = "N"


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
            pass
    return {"finished": {}}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def cell(row: list, i: int) -> str:
    return str(row[i]).strip() if i < len(row) and row[i] is not None else ""


def fmt_n(s: str) -> str:
    try:
        return f"{int(float(s)):,}"
    except ValueError:
        return s or "-"


def pick(rows: list[list]) -> tuple[list[int], list[list]] | None:
    """未送信で最古の単独／ツリー先頭と、その続き行（シート行番号 1-based と値）を返す。"""
    heads = [(i, r) for i, r in enumerate(rows) if cell(r, COL_TREE) != "ツリー続き" and not cell(r, COL_SENT)]
    if not heads:
        return None
    heads.sort(key=lambda ir: cell(ir[1], COL_DATE))
    hi, head = heads[0]
    conv = cell(head, COL_CONV)
    idx, vals = [hi], [head]
    if cell(head, COL_TREE) == "ツリー先頭" and conv:
        for i, r in enumerate(rows):
            if i != hi and cell(r, COL_TREE) == "ツリー続き" and cell(r, COL_CONV) == conv and not cell(r, COL_SENT):
                idx.append(i)
                vals.append(r)
    return [i + 2 for i in idx], vals  # +2: ヘッダー行と 0-based


def build_mail(sheet: str, username: str, vals: list[list], n_done: int, n_total: int, url: str) -> tuple[str, str]:
    head = vals[0]
    date = cell(head, COL_DATE)
    subject = f"【自己開示】@{username} {date[:10]}（{n_done + 1}/{n_total}）"
    lines = [
        f"@{username} の投稿（{sheet}、古い順 {n_done + 1}/{n_total}）",
        "",
        f"投稿日時: {date}",
        f"URL: {cell(head, COL_URL)}",
        f"IMP {fmt_n(cell(head, COL_IMP))} / いいね {fmt_n(cell(head, COL_LIKE))} / RT {fmt_n(cell(head, COL_RT))}"
        f" / リプ {fmt_n(cell(head, COL_REPLY))} / 引用 {fmt_n(cell(head, COL_QUOTE))} / ブクマ {fmt_n(cell(head, COL_BOOKMARK))}",
        f"種別: {cell(head, COL_TREE)}" + (f"（続き {len(vals) - 1} 件）" if len(vals) > 1 else ""),
        "",
        "────────",
        cell(head, COL_TEXT),
    ]
    for k, r in enumerate(vals[1:], start=2):
        lines += ["", f"── 続き {k}/{len(vals)}（{cell(r, COL_DATE)}・いいね {fmt_n(cell(r, COL_LIKE))}）──",
                  cell(r, COL_URL), "", cell(r, COL_TEXT)]
    lines += ["", "────────", f"残り {n_total - n_done - 1} 件", f"シート: {url}", "",
              "✍️ この投稿を参考に自己開示投稿を書くなら、下の [投稿文] に本文を書いて、このまま自分宛に送信してください"
              "（時刻ラベルを付ければその枠、付けなければ 20 時に投稿）。書かない日は下書きを消すか放置。",
              "", "[投稿文]", "", "[/投稿文]", ""]
    return subject, "\n".join(lines)


def send_mail(subject: str, body: str, mode: str = "send") -> bool:
    """mode=send: 自分宛に送信 / mode=draft: Gmail 下書きを作る。"""
    script, verb = (SEND_GMAIL, "メール送信") if mode == "send" else (DRAFT_GMAIL, "下書き作成")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(body)
        path = f.name
    try:
        r = subprocess.run(["bash", str(script), "--to", NOTIFY_TO, "--subject", subject, "--body-file", path],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            log(f"{verb}失敗: {r.stderr.strip()[:300]}")
            return False
        log(f"{verb}: {subject}")
        return True
    finally:
        os.unlink(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True, help="シート名（例: 'ossanworld 2026-05'）")
    ap.add_argument("--spreadsheet", default=SPREADSHEET_ID)
    ap.add_argument("--dry-run", action="store_true", help="下書き作成も送信済み記入もしない")
    ap.add_argument("--mode", choices=["draft", "send"], default="draft", help="競合投稿の通知を Gmail 下書きにする（既定）か送信するか")
    args = ap.parse_args()

    username = args.sheet.split()[0]
    try:
        ss = open_with_retry(get_client(), args.spreadsheet)
        ws = ss.worksheet(args.sheet)
        rows = ws.get_all_values()[1:]
    except Exception as e:  # noqa: BLE001
        log(f"ERROR: シート読み込み失敗: {e}")
        return 1
    sheet_url = f"https://docs.google.com/spreadsheets/d/{args.spreadsheet}/edit#gid={ws.id}"

    heads_all = [r for r in rows if cell(r, COL_TREE) != "ツリー続き"]
    n_total = len(heads_all)
    n_done = sum(1 for r in heads_all if cell(r, COL_SENT))
    picked = pick(rows)

    state = load_state()
    if picked is None:
        if state["finished"].get(args.sheet):
            log(f"残りなし（通知済み）: {args.sheet}")
            return 0
        subject = f"【競合投稿】@{username} 全 {n_total} 件を送り終えました"
        body = f"{args.sheet} の未送信はありません。次のアカウント・期間を取得する場合は fetch_x_user_posts.py で新しいシートを作り、cron の --sheet を変えてください。\n\nシート: {sheet_url}\n"
        if args.dry_run:
            log(f"[dry-run] {subject}")
            return 0
        if send_mail(subject, body):
            state["finished"][args.sheet] = datetime.now(JST).isoformat(timespec="seconds")
            save_state(state)
        return 0

    row_nums, vals = picked
    subject, body = build_mail(args.sheet, username, vals, n_done, n_total, sheet_url)
    if args.dry_run:
        log(f"[dry-run] {subject} 行={row_nums}")
        print(body)
        return 0
    if not send_mail(subject, body, args.mode):
        return 1
    today = datetime.now(JST).strftime("%Y-%m-%d")
    ws.batch_update([{"range": f"{SENT_COL_LETTER}{n}", "values": [[today]]} for n in row_nums],
                    value_input_option="RAW")
    log(f"送信済み（下書き作成日）記入: 行 {row_nums} ← {today}（{n_done + 1}/{n_total}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
