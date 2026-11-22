#!/usr/bin/env python3
"""
過去の伸びた X 投稿からリライト元を選ぶ（/writer-xrewrite 用）。

Usage:
  python3 scripts/rewrite_pool.py list [--days 180] [--json]
  python3 scripts/rewrite_pool.py pick [--days 180] [--tweet-id ID]
  python3 scripts/rewrite_pool.py record --tweet-id ID --method 方式 --element 刺さった要素 \
         --new-what-id W001r --subject 件名 [--count N]

list   : 候補プール（IMP 1 万以上の上位 20）を表示
pick   : IMP 1 万以上の上位 20 本からランダムに 1 本選んで JSON を出力（グレードによる優先はしない。2026-11-22 変更）
         --tweet-id で元投稿を直接指定することもできる（プール外でも可。テスト用）
record : logs/rewrite_records.csv に 1 行追記（使い回し防止・方式別の効果集計用）

候補の条件:
  - X投稿一覧（1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c）の本体投稿
    （ポスト種類が「通常ポスト」「通常ツイート」、親ポストURL が空）
  - 投稿日が --days 日（既定 180）より前
  - 除外: what_id が W006 / W004 / W007 の投稿、質問回答（「ご質問ありがとうございます」等）、
          本文が URL だけ・20 字未満、
          リライト済み（logs/rewrite_records.csv の元tweet_id、または outputs の neta_id が rewrite[ID]）
          ※ リライト済みでも、最後のリライトから --days 日以上経っていれば再び候補になる（年 2 回まで）
  - グレード: X投稿一覧 AK 列（logs/buzz_scores.csv と同じ採点）
  - what_id: outputs シート（1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc）から tweet_id で突合。
    無い場合は本文 300 字以上を W001、未満を W003 とみなす（2〜3 月の無記録投稿向け）

出力 JSON（pick）の主なキー:
  tweet_id, url, date, text, imp, grade, what_id, what_id_source(outputs|length),
  new_what_id (元 what_id + "r"), rewrite_count (過去のリライト回数), prev_methods, prev_elements,
  method_candidates (この回で使える方式。回数順・未使用のもの), pool (IMP10K|MANUAL)
認証: sheets_values.py と同じ（GOOGLE_SERVICE_ACCOUNT_KEY または gcp/ の鍵）
"""

import argparse
import csv
import json
import os
import random
import re
import subprocess
import sys
from datetime import date, datetime, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEETS_CLI = os.path.join(REPO, "scripts", "sheets_values.py")
SA_FILE = os.path.join(REPO, "gcp", "charming-well-464402-u4-2cfb7bddf343.json")
X_SHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
X_RANGE = "X投稿一覧!A:AK"
SS2_ID = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"
OUTPUTS_RANGE = "outputs!A:H"
RECORDS_CSV = os.path.join(REPO, "logs", "rewrite_records.csv")
RECORDS_HEADER = ["日付", "元tweet_id", "元what_id", "元IMP", "元グレード", "回数", "方式", "刺さった要素", "新what_id", "件名"]

# 回数で決まる方式の順番（SKILL.md と一致させる）
METHOD_ORDER = ["①冒頭を変える", "④驚きの軸を変える", "②結末先行", "③主人公・視点を変える"]
# 元が執念の物語（W001 系）のときは「驚きの軸を変える」の余地が小さいので後ろに回す
METHOD_ORDER_STORY = ["①冒頭を変える", "②結末先行", "③主人公・視点を変える", "④驚きの軸を変える"]

EXCLUDE_WHAT = {"W006", "W004", "W007"}
MIN_IMP_TOP = 10000
TOP_N = 20
LONG_THRESHOLD = 300  # 字。これ以上なら W001 とみなす


def sheet_get(spreadsheet_id: str, rng: str):
    env = dict(os.environ)
    if not env.get("GOOGLE_SERVICE_ACCOUNT_KEY") and os.path.exists(SA_FILE):
        with open(SA_FILE, encoding="utf-8") as f:
            env["GOOGLE_SERVICE_ACCOUNT_KEY"] = f.read()
    out = subprocess.run(
        [sys.executable, SHEETS_CLI, "get", spreadsheet_id, rng],
        capture_output=True, text=True, env=env, check=True,
    ).stdout
    i = out.find("{")
    return json.loads(out[i:])["values"]


def to_int(s: str) -> int:
    try:
        return int(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0


def tweet_id_of(url: str) -> str:
    m = re.search(r"/status/(\d+)", url or "")
    return m.group(1) if m else ""


def parse_date(s: str):
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def load_records():
    rows = []
    if os.path.exists(RECORDS_CSV):
        with open(RECORDS_CSV, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    return rows


def load_outputs():
    """tweet_id → what_id と、rewrite[ID] の ID → 最終リライト投稿日 を返す"""
    what_by_id = {}
    rewritten_at = {}
    for r in sheet_get(SS2_ID, OUTPUTS_RANGE)[1:]:
        r = r + [""] * (8 - len(r))
        tid = tweet_id_of(r[1])
        if tid and r[2]:
            what_by_id.setdefault(tid, r[2])
        m = re.fullmatch(r"rewrite\[(\d+)\]", (r[3] or "").strip())
        if m:
            d = parse_date(r[0])
            if d and (m.group(1) not in rewritten_at or d > rewritten_at[m.group(1)]):
                rewritten_at[m.group(1)] = d
    return what_by_id, rewritten_at


def is_qa(text: str) -> bool:
    head = text[:60]
    return ("質問" in head and "ありがとう" in head) or head.startswith("ご質問")


def is_thin(text: str) -> bool:
    """URL だけ・リンク紹介（URL 付きで本文 120 字未満）・20 字未満を除く"""
    has_url = bool(re.search(r"https?://\S+", text))
    stripped = re.sub(r"https?://\S+", "", text).strip()
    if has_url and len(stripped) < 120:
        return True
    return len(stripped) < 20


def build_pools(days: int):
    today = datetime.now()
    cutoff = today - timedelta(days=days)
    what_by_id, rewritten_at = load_outputs()
    records = load_records()
    rec_by_id = {}
    for r in records:
        rec_by_id.setdefault(r["元tweet_id"], []).append(r)

    rows = sheet_get(X_SHEET_ID, X_RANGE)
    header = rows[0]
    col = {name: i for i, name in enumerate(header)}

    def cell(r, name):
        i = col.get(name)
        return r[i] if i is not None and i < len(r) else ""

    cands = []
    for r in rows[1:]:
        kind = cell(r, "ポスト種類")
        if kind not in ("通常ポスト", "通常ツイート"):
            continue
        if cell(r, "親ポストURL").strip():
            continue
        d = parse_date(cell(r, "投稿日時"))
        if not d or d >= cutoff:
            continue
        url = cell(r, "ポストURL")
        tid = tweet_id_of(url)
        text = cell(r, "ポスト本文")
        if not tid or is_qa(text) or is_thin(text):
            continue
        what_id = what_by_id.get(tid, "")
        if what_id in EXCLUDE_WHAT:
            continue
        # リライト済み判定（記録 CSV と outputs の両方）
        last_rw = rewritten_at.get(tid)
        for rec in rec_by_id.get(tid, []):
            rd = parse_date(rec["日付"])
            if rd and (last_rw is None or rd > last_rw):
                last_rw = rd
        if last_rw and last_rw >= cutoff:
            continue
        imp = to_int(cell(r, "インプレッション"))
        grade = cell(r, "グレード").strip()
        if what_id:
            what_src = "outputs"
        else:
            what_id = "W001" if len(text) >= LONG_THRESHOLD else "W003"
            what_src = "length"
        prev = rec_by_id.get(tid, [])
        cands.append({
            "tweet_id": tid,
            "url": f"https://x.com/i/web/status/{tid}",
            "date": d.strftime("%Y-%m-%d %H:%M"),
            "text": text,
            "chars": len(text),
            "imp": imp,
            "grade": grade,
            "what_id": what_id,
            "what_id_source": what_src,
            "new_what_id": what_id + "r",
            "rewrite_count": len(prev),
            "prev_methods": [p["方式"] for p in prev],
            "prev_elements": [p["刺さった要素"] for p in prev],
        })

    sa = [c for c in cands if c["grade"] in ("S", "A")]
    sa.sort(key=lambda c: (c["grade"] != "S", -c["imp"]))
    top = sorted([c for c in cands if c["imp"] >= MIN_IMP_TOP], key=lambda c: -c["imp"])[:TOP_N]
    return sa, top, cands


def add_method_candidates(c):
    order = METHOD_ORDER_STORY if c["what_id"].startswith("W001") else METHOD_ORDER
    used = set(c["prev_methods"])
    c["method_candidates"] = [m for m in order if m not in used] or order
    return c


def cmd_list(args):
    sa, top, cands = build_pools(args.days)
    if args.json:
        print(json.dumps({"IMP10K": top}, ensure_ascii=False, indent=1))
        return
    print(f"候補母集団: {len(cands)} 本（{args.days} 日より前・除外後）")
    print(f"\n[IMP {MIN_IMP_TOP:,} 以上上位 {TOP_N}（ここからランダムに選ぶ）] {len(top)} 本")
    for c in top:
        print(f"  {c['grade'] or '-'} {c['imp']:>9,} {c['date']} {c['what_id']:<5}({c['what_id_source'][0]}) rw{c['rewrite_count']} {c['text'][:28]!r}")


def cmd_pick(args):
    sa, top, cands = build_pools(args.days)
    if args.exclude:
        ex = set(args.exclude.split(","))
        top = [c for c in top if c["tweet_id"] not in ex]
    if args.tweet_id:
        pool = [c for c in cands if c["tweet_id"] == args.tweet_id]
        if not pool:
            # プール外（期間内など）でも指定されたら outputs/本文から組み立てる
            print(json.dumps({"error": f"tweet_id {args.tweet_id} は候補母集団にありません"}, ensure_ascii=False))
            sys.exit(2)
        c = dict(pool[0], pool="MANUAL")
    elif top:
        c = dict(random.choice(top), pool="IMP10K")
    else:
        print(json.dumps({"error": "候補なし", "imp10k": 0}, ensure_ascii=False))
        sys.exit(3)
    print(json.dumps(add_method_candidates(c), ensure_ascii=False, indent=1))


def cmd_record(args):
    sa, top, cands = build_pools(args.days) if not args.no_sheet else ([], [], [])
    c = next((x for x in cands if x["tweet_id"] == args.tweet_id), None)
    row = {
        "日付": date.today().isoformat(),
        "元tweet_id": args.tweet_id,
        "元what_id": args.what_id or (c["what_id"] if c else ""),
        "元IMP": str(args.imp if args.imp is not None else (c["imp"] if c else "")),
        "元グレード": args.grade if args.grade is not None else (c["grade"] if c else ""),
        "回数": str(args.count if args.count is not None else ((c["rewrite_count"] + 1) if c else 1)),
        "方式": args.method,
        "刺さった要素": args.element,
        "新what_id": args.new_what_id,
        "件名": args.subject.replace(",", "，"),
    }
    new_file = not os.path.exists(RECORDS_CSV)
    with open(RECORDS_CSV, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RECORDS_HEADER)
        if new_file:
            w.writeheader()
        w.writerow(row)
    print("✓ rewrite_records.csv に追記: " + json.dumps(row, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list")
    pl.add_argument("--days", type=int, default=180)
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(func=cmd_list)

    pp = sub.add_parser("pick")
    pp.add_argument("--days", type=int, default=180)
    pp.add_argument("--tweet-id", default="")
    pp.add_argument("--exclude", default="", help="候補から外す tweet_id（カンマ区切り。分解の結果リライトに向かないと判断したとき）")
    pp.set_defaults(func=cmd_pick)

    pr = sub.add_parser("record")
    pr.add_argument("--days", type=int, default=180)
    pr.add_argument("--tweet-id", required=True)
    pr.add_argument("--method", required=True)
    pr.add_argument("--element", required=True, help="刺さった要素: フック / 驚き / 展開 / 余韻")
    pr.add_argument("--new-what-id", required=True)
    pr.add_argument("--subject", required=True)
    pr.add_argument("--what-id", default="")
    pr.add_argument("--imp", type=int, default=None)
    pr.add_argument("--grade", default=None)
    pr.add_argument("--count", type=int, default=None)
    pr.add_argument("--no-sheet", action="store_true", help="シートを読まず引数だけで記録する")
    pr.set_defaults(func=cmd_record)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
