#!/usr/bin/env python3
"""マネタイズ月報用の数値集計エンジン。

対象月＋前2ヶ月（3ヶ月）について、次を集計して JSON 出力する：
  A. X 投稿の型別成績（本数 / IMP / エンゲージ / リンククリック / フォロー増）
  B. threads 投稿の型別成績（本数 / views / エンゲージ）
  C. note マネタイズ（売上・記事別・月次推移、記事のビュー/スキ）
  D. note 導線（note_url 付き全投稿：型別に IMP→クリック(CTR)→購入(CVR)→売上）

型（what_id）は outputs シートで判定：
  - X: outputs.B(URL) の tweet_id ↔ X投稿一覧.B で突合し what_id を付与
  - threads: Threads投稿一覧.H(元X投稿URL) の tweet_id → outputs の what_id を解決

- SA 認証（GOOGLE_SERVICE_ACCOUNT_KEY or gcp/charming-well-...json）＋ IPv4 固定。
- 読み取り専用（シートは一切書き換えない）。

Usage:
  python3 scripts/monetization_metrics.py [--month YYYY-MM] [--json | --dry-run]
"""
import argparse
import json
import os
import re
import socket
import sys
from datetime import datetime

# --- IPv4 固定（IPv6 が通らない環境でのハング回避）---
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
socket.getaddrinfo = _ipv4_only

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS_HASSHIN = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録（X/Threads/note 各一覧）
SS_OUTPUTS = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"  # outputs

TYPE_LABEL = {
    "W001": "長文ストーリー",
    "W003": "ワンポイント解説",
    "W006": "質問回答",
    "z01": "短文",
    "W002": "note記事",
}
UNREC_X = "(未記録)"       # outputs に無い X 投稿
UNREC_TH = "(元投稿不明)"  # x_url から型を解決できない threads 投稿


def label_of(what_id):
    if not what_id:
        return UNREC_X
    return TYPE_LABEL.get(what_id, f"その他({what_id})")


def get_client():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if key_json:
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
    else:
        sa = os.path.join(ROOT, "gcp", "charming-well-464402-u4-2cfb7bddf343.json")
        creds = Credentials.from_service_account_file(sa, scopes=scopes)
    return gspread.authorize(creds)


def ws_values(client, ss_id, sheet_name):
    return client.open_by_key(ss_id).worksheet(sheet_name).get_all_values()


def tweet_id(url):
    if not url:
        return ""
    m = re.search(r"status/(\d+)", url)
    return m.group(1) if m else ""


def parse_int(s):
    if not s:
        return 0
    try:
        return int(float(str(s).replace(",", "").strip()))
    except (ValueError, TypeError):
        return 0


def parse_float(s):
    if not s:
        return 0.0
    try:
        return float(str(s).replace(",", "").replace("¥", "").replace("円", "").strip())
    except (ValueError, TypeError):
        return 0.0


def ym(s):
    """日付文字列 → 'YYYY-MM'。解釈できなければ ''。"""
    s = (s or "").strip()
    if not s:
        return ""
    m = re.match(r"(\d{4})[/-](\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return ""


def months_window(target):
    """target 'YYYY-MM' と前2ヶ月を新しい順で返す。"""
    y, mo = int(target[:4]), int(target[5:7])
    out = []
    for _ in range(3):
        out.append(f"{y}-{mo:02d}")
        mo -= 1
        if mo == 0:
            mo = 12
            y -= 1
    return out  # [target, target-1, target-2]


def platform_of(url):
    u = (url or "").lower()
    if "x.com" in u or "twitter.com" in u:
        return "X"
    if "threads" in u:
        return "threads"
    return "other"


def new_bucket_x():
    return {"count": 0, "imp": 0, "eng": 0, "click": 0, "follow": 0, "imps": []}


def new_bucket_th():
    return {"count": 0, "views": 0, "eng": 0, "views_list": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default="", help="対象月 YYYY-MM（既定=前月）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.month:
        target = args.month
    else:
        now = datetime.now()
        y, mo = now.year, now.month - 1
        if mo == 0:
            mo, y = 12, y - 1
        target = f"{y}-{mo:02d}"
    win = months_window(target)
    winset = set(win)

    gc = get_client()
    outputs = ws_values(gc, SS_OUTPUTS, "outputs")
    x_rows = ws_values(gc, SS_HASSHIN, "X投稿一覧")
    th_rows = ws_values(gc, SS_HASSHIN, "Threads投稿一覧")
    note_rows = ws_values(gc, SS_HASSHIN, "note投稿一覧")
    buy_rows = ws_values(gc, SS_HASSHIN, "note購入記録")

    # --- outputs から tweet_id→what_id、note_url 付き投稿を作る ---
    tid_to_what = {}
    note_link_rows = []  # note_url 付き全投稿
    for r in outputs[1:]:
        dt = r[0] if len(r) > 0 else ""
        url = r[1] if len(r) > 1 else ""
        what = r[2] if len(r) > 2 else ""
        note_url = r[5] if len(r) > 5 else ""
        tid = tweet_id(url)
        if tid and what:
            tid_to_what.setdefault(tid, what)
        if note_url:
            note_link_rows.append({"dt": dt, "url": url, "what": what, "note_url": note_url,
                                    "tid": tid, "platform": platform_of(url)})

    # --- X投稿一覧 索引（tweet_id → 指標）---
    # 列: A=0投稿日時 B=1URL K=10IMP P=15エンゲージ AB=27リンククリック AC=28フォロー増
    x_by_tid = {}
    for r in x_rows[1:]:
        tid = tweet_id(r[1] if len(r) > 1 else "")
        if not tid:
            continue
        x_by_tid[tid] = {
            "ym": ym(r[0] if len(r) > 0 else ""),
            "imp": parse_int(r[10]) if len(r) > 10 else 0,
            "eng": parse_int(r[15]) if len(r) > 15 else 0,
            "click": parse_int(r[27]) if len(r) > 27 else 0,
            "follow": parse_int(r[28]) if len(r) > 28 else 0,
        }

    # --- A. X 型別成績（月×型）---
    x_stat = {m: {} for m in win}
    for tid, x in x_by_tid.items():
        m = x["ym"]
        if m not in winset:
            continue
        lab = label_of(tid_to_what.get(tid))
        b = x_stat[m].setdefault(lab, new_bucket_x())
        b["count"] += 1
        b["imp"] += x["imp"]; b["eng"] += x["eng"]
        b["click"] += x["click"]; b["follow"] += x["follow"]
        b["imps"].append(x["imp"])

    # --- Threads投稿一覧 索引 & B. threads 型別成績 ---
    # 列: A=0投稿日時 B=1投稿URL H=7 X投稿URL I=8 views O=14 エンゲージ合計
    th_by_permalink = {}
    th_stat = {m: {} for m in win}
    for r in th_rows[1:]:
        permalink = r[1] if len(r) > 1 else ""
        xurl = r[7] if len(r) > 7 else ""
        views = parse_int(r[8]) if len(r) > 8 else 0
        eng = parse_int(r[14]) if len(r) > 14 else 0
        m = ym(r[0] if len(r) > 0 else "")
        if permalink:
            th_by_permalink[permalink] = {"views": views}
        if m not in winset:
            continue
        tid = tweet_id(xurl)
        lab = label_of(tid_to_what.get(tid)) if tid and tid_to_what.get(tid) else UNREC_TH
        b = th_stat[m].setdefault(lab, new_bucket_th())
        b["count"] += 1
        b["views"] += views; b["eng"] += eng
        b["views_list"].append(views)

    # --- note投稿一覧 索引（URL→ビュー/スキ/タイトル、タイトル→URL）---
    # 列: B=1記事URL C=2タイトル H=7ビュー I=8スキ
    note_by_url = {}
    for r in note_rows[1:]:
        url = r[1] if len(r) > 1 else ""
        if not url:
            continue
        note_by_url[url] = {
            "title": r[2] if len(r) > 2 else "",
            "views": parse_int(r[7]) if len(r) > 7 else 0,
            "likes": parse_int(r[8]) if len(r) > 8 else 0,
        }

    # --- note購入記録（月×売上、記事別）---
    # 列: A=0日付 E=4記事名 F=5価格
    note_sales = {m: {"sales": 0.0, "count": 0, "by_title": {}} for m in win}
    sales_by_title_all = {}  # 全期間（導線用）
    for r in buy_rows[1:]:
        m = ym(r[0] if len(r) > 0 else "")
        title = (r[4] if len(r) > 4 else "").strip()
        price = parse_float(r[5]) if len(r) > 5 else 0.0
        if title:
            t = sales_by_title_all.setdefault(title, {"sales": 0.0, "count": 0})
            t["sales"] += price; t["count"] += 1
        if m in winset:
            ns = note_sales[m]
            ns["sales"] += price; ns["count"] += 1
            bt = ns["by_title"].setdefault(title, {"sales": 0.0, "count": 0})
            bt["sales"] += price; bt["count"] += 1

    # --- D. note 導線（note_url 付き全投稿、月×型）---
    # 送信元投稿の IMP・クリック（X）/ views（threads）と、note 側の購入・売上（記事別・重複排除）を集計
    funnel = {m: {} for m in win}
    for w in note_link_rows:
        m = ym(w["dt"])
        if m not in winset:
            continue
        lab = label_of(w["what"])
        f = funnel[m].setdefault(lab, {
            "posts": 0, "imp": 0, "click": 0, "th_views": 0,
            "purchases": 0, "sales": 0.0, "_notes": set(),
        })
        f["posts"] += 1
        if w["platform"] == "X":
            x = x_by_tid.get(w["tid"])
            if x:
                f["imp"] += x["imp"]; f["click"] += x["click"]
        elif w["platform"] == "threads":
            th = th_by_permalink.get(w["url"])
            if th:
                f["th_views"] += th["views"]
        # note 側（記事は型内で重複排除して売上二重計上を防ぐ）
        note = note_by_url.get(w["note_url"])
        if note and w["note_url"] not in f["_notes"]:
            f["_notes"].add(w["note_url"])
            s = sales_by_title_all.get(note["title"])
            if s:
                f["purchases"] += s["count"]; f["sales"] += s["sales"]

    # --- 整形して出力 ---
    def fmt_x(stat):
        out = {}
        for m in win:
            types = {}
            for lab, b in stat[m].items():
                imps = sorted(b["imps"])
                avg = round(b["imp"] / b["count"]) if b["count"] else 0
                types[lab] = {"count": b["count"], "imp": b["imp"], "imp_avg": avg,
                              "eng": b["eng"], "eng_avg": round(b["eng"] / b["count"]) if b["count"] else 0,
                              "click": b["click"], "follow": b["follow"]}
            out[m] = types
        return out

    def fmt_th(stat):
        out = {}
        for m in win:
            types = {}
            for lab, b in stat[m].items():
                types[lab] = {"count": b["count"], "views": b["views"],
                              "views_avg": round(b["views"] / b["count"]) if b["count"] else 0,
                              "eng": b["eng"]}
            out[m] = types
        return out

    funnel_out = {}
    for m in win:
        types = {}
        for lab, f in funnel[m].items():
            ctr = round(f["click"] / f["imp"] * 100, 2) if f["imp"] else None
            cvr = round(f["purchases"] / f["click"] * 100, 2) if f["click"] else None
            types[lab] = {"posts": f["posts"], "imp": f["imp"], "click": f["click"],
                          "ctr_pct": ctr, "th_views": f["th_views"],
                          "purchases": f["purchases"], "sales": round(f["sales"]),
                          "cvr_pct": cvr, "notes": len(f["_notes"])}
        funnel_out[m] = types

    result = {
        "target_month": target,
        "months": win,
        "type_labels": TYPE_LABEL,
        "x_by_type": fmt_x(x_stat),
        "threads_by_type": fmt_th(th_stat),
        "note_sales": {m: {"sales": round(note_sales[m]["sales"]), "count": note_sales[m]["count"],
                            "by_title": {t: {"sales": round(v["sales"]), "count": v["count"]}
                                         for t, v in note_sales[m]["by_title"].items()}}
                       for m in win},
        "note_articles": {u: n for u, n in note_by_url.items()},
        "funnel_by_type": funnel_out,
        "caveats": [
            "outputs 未記録の投稿は型別・導線の集計対象外（型は (未記録)/(元投稿不明) に計上）。",
            "threads はリンククリック指標が無いため note 導線 CTR/CVR を算出できない（th_views のみ）。",
            "導線の売上/購入は note 記事単位（型内で重複排除）。複数型が同じ記事へ誘導する場合、型をまたいだ二重計上があり得る。月次の総売上は note_sales（note購入記録の実勢合計）を正とする。",
            "W001 の note リンクはセルフリプ側にあり、本体ポスト行のリンククリックには計上されないため、導線 CTR は過小に出る（構造的制約）。",
            "下書き転載の threads は元 X 投稿が outputs 未記録のことが多く、型が (元投稿不明) になりやすい。",
        ],
    }

    if args.dry_run:
        print(f"=== マネタイズ集計 対象月 {target}（3ヶ月: {', '.join(win)}）===")
        print(f"\n[A] X 型別成績（{target}）")
        for lab, v in sorted(result["x_by_type"][target].items(), key=lambda kv: -kv[1]["imp"]):
            print(f"  {lab}: {v['count']}本 IMP計{v['imp']:,}(平均{v['imp_avg']:,}) "
                  f"エンゲ計{v['eng']:,} クリック{v['click']} フォロー増{v['follow']}")
        print(f"\n[B] threads 型別成績（{target}）")
        for lab, v in sorted(result["threads_by_type"][target].items(), key=lambda kv: -kv[1]["views"]):
            print(f"  {lab}: {v['count']}本 views計{v['views']:,}(平均{v['views_avg']:,}) エンゲ計{v['eng']:,}")
        print(f"\n[C] note 売上")
        for m in win:
            ns = result["note_sales"][m]
            print(f"  {m}: {ns['sales']:,}円 / {ns['count']}件")
        print(f"    {target} 記事別:")
        for t, v in result["note_sales"][target]["by_title"].items():
            print(f"      {t}: {v['sales']:,}円 x{v['count']}")
        print(f"\n[D] note 導線（{target}・型別）")
        for lab, v in result["funnel_by_type"][target].items():
            print(f"  {lab}: {v['posts']}投稿 IMP{v['imp']:,} クリック{v['click']} "
                  f"CTR{v['ctr_pct']}% 購入{v['purchases']} 売上{v['sales']:,}円 CVR{v['cvr_pct']}% (th_views{v['th_views']:,})")
        print("\n[!] 制約:")
        for c in result["caveats"]:
            print("  -", c)
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
