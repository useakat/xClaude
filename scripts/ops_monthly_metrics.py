#!/usr/bin/env python3
"""月次の発信運用振り返り（/reporter-monthly-ops）用の集計スクリプト。

outputs（SS2）× X投稿一覧（SS3）× 日次記録（SS3）を突合し、対象月と前2か月の
プロジェクト別実績・週ごとの運用遵守・0本日・月間インプ・ベースライン正規化倍率・
分散記録（W001 / z01）と、レポートに埋め込む SVG チャートを JSON で出す。
数値の判断（学び・方針）はスキル側が行う。このスクリプトは集計だけ。

Usage:
  python3 ops_monthly_metrics.py --month 2026-10            # 人間可読
  python3 ops_monthly_metrics.py --month 2026-10 --json     # JSON（スキルが読む）
  python3 ops_monthly_metrics.py --month 2026-10 --cache-dir DIR
      # DIR/outputs.json, xposts.json, daily.json（sheets_values.py get の出力）を使う

- 認証は sheets_values.py と同じ（GOOGLE_SERVICE_ACCOUNT_KEY か gcp/ の鍵）。読み取り専用
- IMP は X投稿一覧の値（投稿から最大8日分の累積）。未取得の投稿は None で返し n に数えない
- 倍率 = 当該投稿の IMP ÷ その投稿より前の「非W001・非リプライ」直近5本の IMP 中央値
"""

import argparse
import calendar
import csv
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

SS2 = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"  # outputs
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # X投稿一覧 / 日次記録
HALVING_START = date(2026, 7, 3)  # ベースライン半減後の起点（分散記録）
HOOK_CSV = os.path.join(REPO, "logs", "hook_records.csv")
PROJECT_LABEL = {"W001": "W001 長文ストーリー", "W003": "W003 ワンポイント", "z01": "z01 短文",
                 "W002": "W002 note 販促", "W006": "W006 質問回答", "W004": "W004 自己開示"}


# ---------------------------------------------------------------- utilities
def tweet_id(url):
    m = re.search(r"status/(\d+)", url or "")
    return m.group(1) if m else None


def to_int(s):
    if s is None:
        return None
    s = str(s).replace(",", "").strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def to_float(s):
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def parse_dt(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def cell(row, i):
    return row[i].strip() if i < len(row) and row[i] is not None else ""


def head(text, n=40):
    return re.sub(r"\s+", " ", (text or "").strip())[:n]


def median(xs):
    if not xs:
        return None
    m = statistics.median(xs)
    return int(round(m)) if all(isinstance(x, int) for x in xs) else round(m, 1)


def iqr_mean(xs):
    """IQR 外れ値除外平均。(平均, 除外した値のリスト)。n<4 は None。"""
    if len(xs) < 4:
        return None, []
    s = sorted(xs)
    q1, _, q3 = statistics.quantiles(s, n=4, method="inclusive")
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    kept = [x for x in s if lo <= x <= hi]
    out = [x for x in s if not (lo <= x <= hi)]
    return (round(sum(kept) / len(kept)) if kept else None), out


def month_range(ym):
    y, m = map(int, ym.split("-"))
    last = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last)


def shift_month(ym, k):
    y, m = map(int, ym.split("-"))
    m += k
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return f"{y}-{m:02d}"


def week_id(d):
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


# ---------------------------------------------------------------- loading
def load_sheets(cache_dir=None):
    if cache_dir:
        def rd(name):
            with open(os.path.join(cache_dir, name), encoding="utf-8") as f:
                return json.load(f)["values"]
        return rd("outputs.json"), rd("xposts.json"), rd("daily.json")
    from sheets_values import get_client, open_with_retry  # noqa: E402
    client = get_client()
    ss2 = open_with_retry(client, SS2)
    ss3 = open_with_retry(client, SS3)
    outputs = ss2.worksheet("outputs").get_all_values()
    xposts = ss3.worksheet("X投稿一覧").get_all_values()
    daily = ss3.worksheet("日次記録").get_all_values()
    return outputs, xposts, daily


def load_hooks():
    hooks = {}
    if not os.path.exists(HOOK_CSV):
        return hooks
    with open(HOOK_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            key = (r.get("冒頭15字") or "").strip()
            if key:
                hooks[key] = {"type": r.get("フック型", ""), "mystery": r.get("謎", ""), "self": r.get("自分事", "")}
    return hooks


# ---------------------------------------------------------------- core
class Data:
    def __init__(self, outputs, xposts, daily, hooks):
        self.hooks = hooks
        # --- X投稿一覧: tweet_id → metrics
        hdr = xposts[0]
        col = {name: i for i, name in enumerate(hdr)}
        self.x = {}
        self.x_rows = []  # (dt, tweet_id, kind)
        for r in xposts[1:]:
            tid = tweet_id(cell(r, col["ポストURL"]))
            dt = parse_dt(cell(r, col["投稿日時"]))
            if not tid or not dt:
                continue
            rec = {
                "dt": dt, "kind": cell(r, col["ポスト種類"]), "text": cell(r, col["ポスト本文"]),
                "imp": to_int(cell(r, col["インプレッション"])), "likes": to_int(cell(r, col["いいね"])),
                "bm": to_int(cell(r, col["ブックマーク"])), "eng_rate": to_float(cell(r, col["エンゲ率"])),
                "clicks": to_int(cell(r, col.get("リンククリック", 99))), "follows": to_int(cell(r, col.get("フォロー増", 99))),
                "profile": to_int(cell(r, col.get("プロフアクセス", 99))),
            }
            self.x[tid] = rec
            self.x_rows.append((dt, tid, rec["kind"]))
        self.x_rows.sort()
        # 投稿があった日（0本日の判定用）。outputs に記録されない投稿（手動投稿など）も X投稿一覧には載るのでこちらを正にする
        self.x_days = defaultdict(int)
        for dt, tid, kind in self.x_rows:
            if kind in ("通常ポスト", "引用RT"):
                self.x_days[dt.date()] += 1
        # --- outputs
        self.posts = []      # X 本体
        self.threads = []    # threads 行（転載含む）
        self.notes = []      # note 公開
        for r in outputs[1:]:
            dt = parse_dt(cell(r, 0))
            url = cell(r, 1)
            if not dt or not url:
                continue
            what = cell(r, 2)
            if "threads.com" in url or "threads.net" in url:
                self.threads.append({"dt": dt, "url": url, "repost": bool(cell(r, 7)), "what": what})
            elif "note.com" in url:
                self.notes.append({"dt": dt, "url": url, "what": what})
            else:
                tid = tweet_id(url)
                self.posts.append({"dt": dt, "url": url, "tid": tid, "what": what or "分類不明"})
        self.posts.sort(key=lambda p: p["dt"])
        self.w001_ids = {p["tid"] for p in self.posts if p["what"] == "W001"}
        # --- 日次記録
        hdr = daily[0]
        col = {name: i for i, name in enumerate(hdr)}
        self.daily = {}
        for r in daily[1:]:
            d = parse_dt(cell(r, 0))
            if not d:
                continue
            self.daily[d.date()] = {
                "posts": to_int(cell(r, col["ポスト数"])), "followers": to_int(cell(r, col["総フォロワ数"])),
                "imp": to_int(cell(r, col["インプ"])), "profile": to_int(cell(r, col["プロフ"])),
                "note_followers": to_int(cell(r, col.get("noteフォロワ数", 99))),
                "threads_followers": to_int(cell(r, col.get("threads フォロワ数", 99))),
                "weekly_imp": to_int(cell(r, col.get("週間インプ", 99))),
            }

    # 倍率の分母: 直前の非W001・非リプライ 5 本の IMP 中央値
    def baseline(self, dt):
        prev = []
        for d, tid, kind in reversed(self.x_rows):
            if d >= dt:
                continue
            if kind != "通常ポスト" or tid in self.w001_ids:
                continue
            imp = self.x[tid]["imp"]
            if imp:
                prev.append(imp)
            if len(prev) == 5:
                break
        return median(prev) if len(prev) >= 3 else None

    def enrich(self, p):
        rec = self.x.get(p["tid"]) or {}
        text = rec.get("text", "")
        imp = rec.get("imp")
        base = self.baseline(p["dt"]) if imp else None
        hk = self.hooks.get(re.sub(r"\s+", "", text)[:15]) or self.hooks.get(text[:15])
        return {
            "date": p["dt"].strftime("%Y-%m-%d"), "time": p["dt"].strftime("%H:%M"), "weekday": "月火水木金土日"[p["dt"].weekday()],
            "tweet_id": p["tid"], "what": p["what"], "head": head(text), "imp": imp, "likes": rec.get("likes"),
            "bm": rec.get("bm"), "eng_rate": rec.get("eng_rate"), "clicks": rec.get("clicks"), "follows": rec.get("follows"),
            "profile": rec.get("profile"),
            "baseline": base, "ratio": (round(imp / base, 1) if imp and base else None),
            "hook": hk,
        }

    def posts_between(self, d0, d1):
        return [p for p in self.posts if d0 <= p["dt"].date() <= d1]


def profile_follow_stats(ps):
    """プロフ率（プロフアクセス÷IMP）の中央値、フォロー増の合算指標。

    プロフ率は IMP≥100 の投稿だけ。フォロー増は 0 が大半で中央値が使えないため、
    フォロー増が取り込み済み（空欄でない）の投稿だけ合算して IMP・プロフアクセスで割る。
    """
    rates = [p["profile"] / p["imp"] for p in ps if p.get("imp") and p["imp"] >= 100 and p.get("profile") is not None]
    fp = [p for p in ps if p.get("follows") is not None and p.get("imp")]
    f_sum = sum(p["follows"] for p in fp)
    imp_sum = sum(p["imp"] for p in fp)
    prof_sum = sum(p["profile"] for p in fp if p.get("profile") is not None)
    return {
        "profile_rate_median": round(statistics.median(rates), 5) if rates else None, "n_profile_rate": len(rates),
        "n_follow_measured": len(fp), "follow_sum": f_sum if fp else None,
        "follow_per_10k": round(f_sum / imp_sum * 10000, 2) if fp and imp_sum else None,
        "follow_per_profile": round(f_sum / prof_sum, 3) if fp and prof_sum else None,
    }


def project_stats(posts):
    by = defaultdict(list)
    for p in posts:
        by[p["what"]].append(p)
    out = {}
    for what, ps in by.items():
        imps = [p["imp"] for p in ps if p["imp"]]
        mean_ex, outliers = iqr_mean(imps)
        ranked = sorted([p for p in ps if p["imp"]], key=lambda p: p["imp"], reverse=True)
        out[what] = {
            "label": PROJECT_LABEL.get(what, what), "n": len(ps), "n_measured": len(imps),
            "median": median(imps), "iqr_mean": mean_ex, "outliers": outliers, "max": max(imps) if imps else None,
            "values": imps if len(imps) < 4 else None,
            "ratio_median": median([p["ratio"] for p in ps if p["ratio"]]),
            "top": [{k: p[k] for k in ("date", "head", "imp", "ratio")} for p in ranked[:3]],
            "worst": [{k: p[k] for k in ("date", "head", "imp", "ratio")} for p in ranked[-3:][::-1]] if len(ranked) > 3 else [],
            "over_10k": sum(1 for v in imps if v >= 10000),
            **profile_follow_stats(ps),
        }
    return out


def month_summary(data, ym, enriched_cache):
    d0, d1 = month_range(ym)
    today = date.today()
    d_eff = min(d1, today)
    posts = [enriched_cache.setdefault(p["tid"], data.enrich(p)) for p in data.posts_between(d0, d1)]
    zero_days = [d for d in (d0 + timedelta(i) for i in range((d_eff - d0).days + 1)) if not data.x_days.get(d)]
    x_posts_all = sum(v for d, v in data.x_days.items() if d0 <= d <= d1)
    daily_imp = [{"date": d.strftime("%Y-%m-%d"), "imp": (data.daily.get(d) or {}).get("imp")} for d in (d0 + timedelta(i) for i in range((d1 - d0).days + 1))]
    imp_vals = [x["imp"] for x in daily_imp if x["imp"] is not None]
    prev_last = d0 - timedelta(days=1)
    last_rec = max((d for d in data.daily if d0 <= d <= d1 and data.daily[d].get("followers")), default=None)
    fw0 = (data.daily.get(prev_last) or {}).get("followers")
    fw1 = (data.daily.get(last_rec) or {}).get("followers") if last_rec else None
    threads = [t for t in data.threads if d0 <= t["dt"].date() <= d1]
    notes = [{"date": n["dt"].strftime("%Y-%m-%d"), "url": n["url"]} for n in data.notes if d0 <= n["dt"].date() <= d1]
    return {
        "month": ym, "start": str(d0), "end": str(d1), "partial": d_eff < d1, "days_counted": (d_eff - d0).days + 1,
        "x_posts": len(posts), "x_posts_all": x_posts_all, "by_project": project_stats(posts), "posts": posts,
        # 比較群: 非W001・非W004 の通常ポスト（H8 の比較基準）
        "baseline_profile": profile_follow_stats([p for p in posts if p["what"] not in ("W001", "W004")]),
        "w004_list": [{k: p[k] for k in ("date", "head", "imp", "profile", "follows")} for p in posts if p["what"] == "W004"],
        "w001_count": sum(1 for p in posts if p["what"] == "W001"),
        "w001_list": [{k: p[k] for k in ("date", "weekday", "time", "head", "imp", "ratio", "clicks")} for p in posts if p["what"] == "W001"],
        "note_published": notes, "threads_original": sum(1 for t in threads if not t["repost"]),
        "threads_repost": sum(1 for t in threads if t["repost"]),
        "zero_days": [str(d) for d in zero_days], "zero_day_count": len(zero_days),
        "monthly_imp": sum(imp_vals) if imp_vals else None, "imp_days": len(imp_vals),
        "daily_imp": daily_imp, "daily_imp_median": median(imp_vals),
        "profile_visits": sum(x for x in ((data.daily.get(d) or {}).get("profile") for d in (d0 + timedelta(i) for i in range((d1 - d0).days + 1))) if x) or None,
        "followers_start": fw0, "followers_end": fw1, "followers_diff": (fw1 - fw0) if fw0 is not None and fw1 is not None else None,
        "followers_end_date": str(last_rec) if last_rec else None,
    }


def week_rows(data, ym, enriched_cache):
    d0, d1 = month_range(ym)
    monday = d0 - timedelta(days=d0.weekday())
    today = date.today()
    rows = []
    while monday <= d1:
        sunday = monday + timedelta(days=6)
        wk = [enriched_cache.setdefault(p["tid"], data.enrich(p)) for p in data.posts_between(monday, sunday)]
        in_month_days = [monday + timedelta(i) for i in range(7) if d0 <= monday + timedelta(i) <= min(d1, today)]
        zero = [str(d) for d in in_month_days if not data.x_days.get(d)]
        w001 = [p for p in wk if p["what"] == "W001"]
        z01 = [p["imp"] for p in wk if p["what"] == "z01" and p["imp"]]
        notes = [n for n in data.notes if monday <= n["dt"].date() <= sunday]
        sun = data.daily.get(sunday) or {}
        wimp = sun.get("weekly_imp")
        if wimp is None:
            vals = [(data.daily.get(monday + timedelta(i)) or {}).get("imp") for i in range(7)]
            vals = [v for v in vals if v]
            wimp_prov = sum(vals) if vals else None
        else:
            wimp_prov = None
        wid = week_id(monday)
        rows.append({
            "week_id": wid, "monday": str(monday), "sunday": str(sunday),
            "days_in_month": len(in_month_days), "partial": len(in_month_days) < 7,
            "x_posts": len(wk), "w001": len(w001),
            "w001_slots": [f'{p["weekday"]} {p["date"][5:].replace("-", "/")} {p["time"]}' for p in w001],
            "w001_ok": len(w001) >= 2, "note": len(notes), "note_ok": len(notes) >= 1,
            "zero_days": zero, "zero_ok": len(zero) == 0,
            "z01_n": len(z01), "z01_median": median(z01),
            "weekly_imp": wimp, "weekly_imp_provisional": wimp_prov,
            "report_exists": os.path.exists(os.path.join(REPO, "docs", "reports", "ops-weekly", f"{wid}.md")),
        })
        monday += timedelta(days=7)
    return rows


def z01_weekly_series(data, ym, enriched_cache, weeks=13):
    _, d1 = month_range(ym)
    last_monday = d1 - timedelta(days=d1.weekday())
    series = []
    for k in range(weeks - 1, -1, -1):
        mon = last_monday - timedelta(days=7 * k)
        ps = [enriched_cache.setdefault(p["tid"], data.enrich(p)) for p in data.posts_between(mon, mon + timedelta(days=6)) if p["what"] == "z01"]
        imps = [p["imp"] for p in ps if p["imp"]]
        series.append({"week_id": week_id(mon), "monday": str(mon), "n": len(imps), "median": median(imps)})
    return series


def distribution(data, what, enriched_cache, since=HALVING_START):
    ps = [enriched_cache.setdefault(p["tid"], data.enrich(p)) for p in data.posts if p["what"] == what and p["dt"].date() >= since]
    pts = [(p["date"], p["imp"]) for p in ps if p["imp"]]
    imps = [v for _, v in pts]
    return {"since": str(since), "n": len(pts), "points": pts, "median": median(imps),
            "over_10k": sum(1 for v in imps if v >= 10000), "min": min(imps) if imps else None, "max": max(imps) if imps else None}


# ---------------------------------------------------------------- SVG charts（Starlight の CSS 変数のみ使用）
def svg_log_bars(points, label, lo, hi, median_line=None, W=720, H=250):
    ml, mr, mt, mb = 52, 10, 20, 28
    n = len(points)
    if n == 0:
        return ""
    def y(v):
        v = max(v, lo)
        return (H - mb) - (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (H - mb - mt)
    step = (W - ml - mr) / n
    bw = min(step * 0.62, 30)
    every = max(1, math.ceil(n / 26))
    P = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{label}" style="max-width:{W}px;font-family:inherit">']
    for v, lab in [(1000, "1,000"), (10000, "1万"), (100000, "10万")]:
        if lo < v < hi:
            yy = round(y(v), 1)
            P.append(f'<line x1="{ml}" x2="{W-mr}" y1="{yy}" y2="{yy}" style="stroke:var(--sl-color-gray-5);stroke-width:1"/>')
            P.append(f'<text x="{ml-6}" y="{yy+3.5}" text-anchor="end" style="fill:var(--sl-color-gray-3);font-size:11px">{lab}</text>')
    P.append(f'<line x1="{ml}" x2="{W-mr}" y1="{H-mb}" y2="{H-mb}" style="stroke:var(--sl-color-gray-4);stroke-width:1"/>')
    if median_line:
        yy = round(y(median_line), 1)
        P.append(f'<line x1="{ml}" x2="{W-mr}" y1="{yy}" y2="{yy}" style="stroke:var(--sl-color-orange);stroke-width:1.2;stroke-dasharray:4 3"/>')
        P.append(f'<text x="{W-mr}" y="{yy-4}" text-anchor="end" style="fill:var(--sl-color-orange);font-size:10px">中央値 {median_line:,.0f}</text>')
    for i, (d, v) in enumerate(points):
        x = ml + step * i + (step - bw) / 2
        yt = round(y(v), 1)
        h = round(H - mb - yt, 1)
        lab = d[5:].replace("-", "/").lstrip("0").replace("/0", "/")
        P.append(f'<rect x="{x:.1f}" y="{yt}" width="{bw:.1f}" height="{h}" rx="2" style="fill:var(--sl-color-accent)"><title>{lab}: {v:,}</title></rect>')
        if v >= 20000:
            P.append(f'<text x="{x+bw/2:.1f}" y="{yt-5}" text-anchor="middle" style="fill:var(--sl-color-gray-3);font-size:10px">{v:,}</text>')
        if i % every == 0:
            P.append(f'<text x="{x+bw/2:.1f}" y="{H-mb+14}" text-anchor="middle" style="fill:var(--sl-color-gray-3);font-size:9.5px">{lab}</text>')
    P.append("</svg>")
    return "\n".join(P)


def svg_linear_bars(points, label, W=720, H=220, accent_max=True, value_fmt="{:,}"):
    """points: [(label, value or None, note)] 線形スケール。None は「未取得」。"""
    ml, mr, mt, mb = 52, 10, 20, 28
    vals = [v for _, v, *_ in points if v]
    n = len(points)
    if n == 0 or not vals:
        return ""
    vmax = max(vals)
    def y(v):
        return (H - mb) - v / vmax * (H - mb - mt)
    step = (W - ml - mr) / n
    bw = min(step * 0.7, 40)
    every = max(1, math.ceil(n / 26))
    P = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{label}" style="max-width:{W}px;font-family:inherit">']
    for frac in (0.25, 0.5, 0.75, 1.0):
        v = vmax * frac
        yy = round(y(v), 1)
        P.append(f'<line x1="{ml}" x2="{W-mr}" y1="{yy}" y2="{yy}" style="stroke:var(--sl-color-gray-5);stroke-width:1"/>')
        P.append(f'<text x="{ml-6}" y="{yy+3.5}" text-anchor="end" style="fill:var(--sl-color-gray-3);font-size:11px">{value_fmt.format(round(v))}</text>')
    P.append(f'<line x1="{ml}" x2="{W-mr}" y1="{H-mb}" y2="{H-mb}" style="stroke:var(--sl-color-gray-4);stroke-width:1"/>')
    for i, pt in enumerate(points):
        lab, v = pt[0], pt[1]
        x = ml + step * i + (step - bw) / 2
        if v:
            yt = round(y(v), 1)
            h = round(H - mb - yt, 1)
            color = "var(--sl-color-accent)" if (accent_max and v == vmax) else "var(--sl-color-gray-4)"
            P.append(f'<rect x="{x:.1f}" y="{yt}" width="{bw:.1f}" height="{h}" rx="2" style="fill:{color}"><title>{lab}: {value_fmt.format(v)}</title></rect>')
        else:
            P.append(f'<text x="{x+bw/2:.1f}" y="{H-mb-4}" text-anchor="middle" style="fill:var(--sl-color-gray-4);font-size:9px">—</text>')
        if i % every == 0:
            P.append(f'<text x="{x+bw/2:.1f}" y="{H-mb+14}" text-anchor="middle" style="fill:var(--sl-color-gray-3);font-size:9.5px">{lab}</text>')
    P.append("</svg>")
    return "\n".join(P)


def build_charts(cur, w001d, z01d, z01w):
    daily_pts = [(x["date"][8:].lstrip("0"), x["imp"]) for x in cur["daily_imp"]]
    ym = cur["month"]
    return {
        "daily_imp": svg_linear_bars(daily_pts, f"{ym} の日次インプレッション"),
        "w001_dist": svg_log_bars(w001d["points"], f"W001 長文の実インプレッション（{w001d['since']} 以降・対数スケール）", 600, 300000),
        "z01_dist": svg_log_bars(z01d["points"], f"z01 短文の実インプレッション（{z01d['since']} 以降・対数スケール）", 400, 300000, median_line=z01d["median"]),
        "z01_weekly_median": svg_linear_bars([(s["week_id"][5:], s["median"]) for s in z01w], "z01 週中央値（直近13週）", accent_max=False),
    }


# ---------------------------------------------------------------- main
def run(ym, cache_dir=None):
    outputs, xposts, daily = load_sheets(cache_dir)
    data = Data(outputs, xposts, daily, load_hooks())
    cache = {}
    cur = month_summary(data, ym, cache)
    prev = [month_summary(data, shift_month(ym, -k), cache) for k in (1, 2)]
    for m in prev:  # 前月は要約だけ（投稿リストと日次は落とす）
        m.pop("posts", None); m.pop("daily_imp", None); m.pop("w001_list", None)
    weeks = week_rows(data, ym, cache)
    z01w = z01_weekly_series(data, ym, cache)
    w001d = distribution(data, "W001", cache)
    z01d = distribution(data, "z01", cache)
    caveats = [
        "IMP は X投稿一覧の値で、投稿から最大8日分の累積。月末に近い投稿は伸び切っていない可能性がある",
        "月間インプは日次記録の「インプ」列の合計（記入済みの日のみ。imp_days 参照）。週間インプは日曜行の値、未記入週は日次合計の暫定値",
        "倍率 = IMP ÷ 直前の非W001・非リプライ5本の IMP 中央値（分母が3本未満なら None）",
        "0本日は X投稿一覧の通常ポスト・引用RT の有無で判定（リプライのみ・threads 転載のみの日は 0本日）。当月が進行中なら今日までで数える。x_posts は outputs 記録の本数、x_posts_all は X投稿一覧の通常ポスト＋引用RT の本数",
        "IQR 外れ値除外平均は n≥4 のときだけ算出。n<4 は values に実値を列挙",
        "フック型は logs/hook_records.csv の制作時記録（冒頭15字で突合）。無い投稿は hook が None",
    ]
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "month": ym,
        "current": cur, "previous": prev, "weeks": weeks, "z01_weekly": z01w,
        "w001_distribution": w001d, "z01_distribution": z01d,
        "charts": build_charts(cur, w001d, z01d, z01w), "caveats": caveats,
    }


def fmt(v):
    return f"{v:,}" if isinstance(v, (int, float)) and v is not None else "—"


def pct(v):
    return f"{v * 100:.2f}%" if isinstance(v, (int, float)) else "—"


def print_human(res):
    c = res["current"]
    print(f"# {c['month']}（{c['start']}〜{c['end']}）{'※進行中' if c['partial'] else ''}  生成 {res['generated_at']}")
    print(f"月間インプ {fmt(c['monthly_imp'])}（{c['imp_days']}日分）／日次中央値 {fmt(c['daily_imp_median'])}／プロフ {fmt(c['profile_visits'])}")
    print(f"フォロワー {fmt(c['followers_start'])} → {fmt(c['followers_end'])}（{c['followers_diff']:+d}）" if c["followers_diff"] is not None else "フォロワー —")
    print(f"X 本体 {c['x_posts']} 本（X投稿一覧では {c['x_posts_all']} 本）／W001 {c['w001_count']}／note 公開 {len(c['note_published'])}／threads 転載 {c['threads_repost']}・独自 {c['threads_original']}／0本日 {c['zero_day_count']} 日 {c['zero_days']}")
    print("\n## プロジェクト別（当月）")
    for what, s in sorted(c["by_project"].items()):
        print(f"- {s['label']}: n={s['n']}（計測 {s['n_measured']}） 中央値 {fmt(s['median'])} 除外平均 {fmt(s['iqr_mean'])} 最大 {fmt(s['max'])} 倍率中央値 {s['ratio_median']} 1万超 {s['over_10k']} 除外 {s['outliers']} {('実値 ' + str(s['values'])) if s['values'] else ''}")
        print(f"    プロフ率中央値 {pct(s['profile_rate_median'])}（n={s['n_profile_rate']}） フォロー/1万IMP {s['follow_per_10k'] if s['follow_per_10k'] is not None else '—'} フォロー/プロフ {s['follow_per_profile'] if s['follow_per_profile'] is not None else '—'}（フォロー増取込 {s['n_follow_measured']} 本）")
        for t in s["top"][:2]:
            print(f"    top: {t['date']} {t['head'][:30]} {fmt(t['imp'])}（{t['ratio']}倍）")
    bp = c.get("baseline_profile") or {}
    print(f"比較群（非W001・非W004）: プロフ率中央値 {pct(bp.get('profile_rate_median'))}（n={bp.get('n_profile_rate')}） フォロー/1万IMP {bp.get('follow_per_10k')}（取込 {bp.get('n_follow_measured')} 本）")
    print("\n## 前月比")
    for m in res["previous"]:
        print(f"- {m['month']}: インプ {fmt(m['monthly_imp'])} X {m['x_posts']} 本 W001 {m['w001_count']} note {len(m['note_published'])} 0本日 {m['zero_day_count']} フォロワー {m['followers_diff']}")
        for what, s in sorted(m["by_project"].items()):
            print(f"    {s['label']}: n={s['n']} 中央値 {fmt(s['median'])} 最大 {fmt(s['max'])}")
    print("\n## 週ごとの運用遵守")
    for w in res["weeks"]:
        print(f"- {w['week_id']} {w['monday'][5:]}〜{w['sunday'][5:]}{'（部分）' if w['partial'] else ''}: W001 {w['w001']} {w['w001_slots']} / note {w['note']} / 0本日 {len(w['zero_days'])} {w['zero_days']} / z01 中央値 {fmt(w['z01_median'])}(n={w['z01_n']}) / 週間インプ {fmt(w['weekly_imp']) if w['weekly_imp'] else fmt(w['weekly_imp_provisional']) + '(暫定)'} / 週次レポート {'あり' if w['report_exists'] else 'なし'}")
    print("\n## W001 一覧（当月）")
    for p in c["w001_list"]:
        print(f"- {p['weekday']} {p['date']} {p['time']} {fmt(p['imp'])}（{p['ratio']}倍・クリック {fmt(p['clicks'])}） {p['head'][:30]}")
    d = res["w001_distribution"]; z = res["z01_distribution"]
    print(f"\n分散記録 W001: n={d['n']} 中央値 {fmt(d['median'])} 1万超 {d['over_10k']} / z01: n={z['n']} 中央値 {fmt(z['median'])} 1万超 {z['over_10k']}")
    print("z01 週中央値:", " / ".join(f"{s['week_id'][5:]}:{fmt(s['median'])}" for s in res["z01_weekly"]))
    print("\n## caveats")
    for cv in res["caveats"]:
        print("-", cv)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--json", action="store_true", help="JSON で出力（チャート SVG を含む）")
    ap.add_argument("--cache-dir", help="sheets_values.py get の出力 JSON を置いたディレクトリ（outputs.json / xposts.json / daily.json）")
    args = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}", args.month):
        sys.exit("--month は YYYY-MM")
    res = run(args.month, args.cache_dir)
    if args.json:
        json.dump(res, sys.stdout, ensure_ascii=False, indent=1)
    else:
        print_human(res)


if __name__ == "__main__":
    main()
