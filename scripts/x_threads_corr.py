#!/usr/bin/env python3
"""
X 投稿と Threads 転載の反応の相関を調べる（1 回限りの分析用。定期実行はしない）。

- outputs シート（SS2）の Threads 行（B=permalink, H=x_url）で X ⇄ Threads を結合
- X投稿一覧（SS3）: K インプ, L いいね, M リポスト, N リプライ, O ブクマ
- Threads投稿一覧（SS3）: I views, J いいね, K リプライ, L リポスト, M 引用, N シェア（G 親投稿URL が空の本体のみ）
- 同時転載（X 投稿から 1 日以内の Threads 投稿）を主標本、後日転載は参考枝
- X 側は投稿後 8 日で更新が止まるため、投稿後 9 日以上の X 投稿だけを使う
- 量は log10、相関は Spearman ρ を主、log 値の Pearson r を添える
- 時期の影響を外す補助分析: 同じ型の直前 56 日（8 週）の中央値との比（log2）

Usage:
  python3 scripts/x_threads_corr.py [--out outputs/reports/x_threads_corr] [--min-age-days 9]

出力: pairs.csv / corr.md / scatter_*.png
X API は呼ばない（シートの値だけを使う）。
"""
import argparse
import csv
import math
import os
import re
import statistics
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from monetization_metrics import (SS_HASSHIN, SS_OUTPUTS, get_client, ws_values,  # noqa: E402
                                  tweet_id, parse_int)

ROOT = os.path.dirname(SCRIPT_DIR)
BASE_WINDOW_DAYS = 56
MIRROR_MAX_LAG_DAYS = 1.0
MIN_BASE = 3
# Threads の views が投稿あたり 10〜50 から数百〜数千に跳ねた境目（週次中央値: 9/14 週 14 → 9/21 週 133（9/22・23 は 16・17、9/24 から 437〜）→ 9/28 週 984）。
# それ以前は Threads 側に配信がほぼ無く、相関を測れる水準にない
REGIME_START = datetime(2026, 9, 24)


def parse_dt(s):
    s = (s or "").strip()
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M",
                "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    m = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def col(r, i):
    return r[i] if len(r) > i else ""


def rate(num, den):
    return num / den if den else float("nan")


def load(gc):
    outputs = ws_values(gc, SS_OUTPUTS, "outputs")
    x_rows = ws_values(gc, SS_HASSHIN, "X投稿一覧")
    th_rows = ws_values(gc, SS_HASSHIN, "Threads投稿一覧")

    tid_to_what = {}
    th_links = []  # (permalink, x_url)
    for r in outputs[1:]:
        url, what, x_url = col(r, 1), col(r, 2), col(r, 7)
        tid = tweet_id(url)
        if tid and what:
            tid_to_what.setdefault(tid, what)
        if ("threads.com" in url or "threads.net" in url) and x_url:
            th_links.append((url.strip(), x_url.strip()))

    x_by_tid = {}
    for r in x_rows[1:]:
        tid = tweet_id(col(r, 1))
        if not tid:
            continue
        x_by_tid[tid] = {
            "dt": parse_dt(col(r, 0)), "text": col(r, 2).replace("\n", " "), "kind": col(r, 3),
            "imp": parse_int(col(r, 10)), "like": parse_int(col(r, 11)), "rp": parse_int(col(r, 12)),
            "reply": parse_int(col(r, 13)), "bm": parse_int(col(r, 14)),
            "parent": col(r, 9).strip(),
        }

    th_by_perma = {}
    for r in th_rows[1:]:
        perma = col(r, 1).strip()
        if not perma:
            continue
        th_by_perma[perma] = {
            "dt": parse_dt(col(r, 0)), "parent": col(r, 6).strip(),
            "views": parse_int(col(r, 8)), "like": parse_int(col(r, 9)), "reply": parse_int(col(r, 10)),
            "rp": parse_int(col(r, 11)), "quote": parse_int(col(r, 12)), "share": parse_int(col(r, 13)),
        }
    return tid_to_what, th_links, x_by_tid, th_by_perma


def build_pairs(tid_to_what, th_links, x_by_tid, th_by_perma, today, min_age_days):
    cands = {}  # tid → list of candidate pairs
    skipped = {"x_missing": 0, "th_missing": 0, "th_reply": 0, "no_dt": 0}
    for perma, x_url in th_links:
        tid = tweet_id(x_url)
        x = x_by_tid.get(tid)
        th = th_by_perma.get(perma)
        if not x:
            skipped["x_missing"] += 1
            continue
        if not th:
            skipped["th_missing"] += 1
            continue
        if th["parent"]:
            skipped["th_reply"] += 1
            continue
        if not x["dt"] or not th["dt"]:
            skipped["no_dt"] += 1
            continue
        lag = (th["dt"] - x["dt"]).total_seconds() / 86400
        cands.setdefault(tid, []).append((perma, lag))

    pairs = []
    for tid, lst in cands.items():
        x = x_by_tid[tid]
        # 同時転載があればそれを採る（複数なら lag 最小）。無ければ後日転載の最初の 1 件
        lst.sort(key=lambda t: abs(t[1]))
        perma, lag = lst[0]
        th = th_by_perma[perma]
        group = "mirror" if abs(lag) <= MIRROR_MAX_LAG_DAYS else "late"
        x_age = (today - x["dt"]).days
        th_age = (today - th["dt"]).days
        x_eng = x["like"] + x["rp"] + x["reply"] + x["bm"]
        th_eng = th["like"] + th["reply"] + th["rp"] + th["quote"] + th["share"]
        pairs.append({
            "tid": tid, "what": tid_to_what.get(tid, ""), "group": group,
            "x_dt": x["dt"], "th_dt": th["dt"], "lag_days": round(lag, 2),
            "x_age": x_age, "th_age": th_age, "text": x["text"][:25],
            "x_url": f"https://x.com/i/web/status/{tid}", "th_url": perma,
            "x_imp": x["imp"], "x_like": x["like"], "x_rp": x["rp"], "x_reply": x["reply"], "x_bm": x["bm"],
            "x_eng": x_eng, "x_er": rate(x_eng, x["imp"]), "x_lr": rate(x["like"], x["imp"]),
            "th_views": th["views"], "th_like": th["like"], "th_reply": th["reply"],
            "th_rp": th["rp"] + th["quote"], "th_share": th["share"],
            "th_eng": th_eng, "th_er": rate(th_eng, th["views"]), "th_lr": rate(th["like"], th["views"]),
            "usable": x_age >= min_age_days and x["imp"] > 0 and th["views"] > 0,
            "n_th_rows": len(lst),
        })
    pairs.sort(key=lambda p: p["x_dt"])
    return pairs, skipped


def add_baseline_ratio(pairs):
    """同じ型・同じ群の直前 56 日の中央値との比（log2）。基準が MIN_BASE 件未満なら NaN。"""
    for p in pairs:
        base = [q for q in pairs if q is not p and q["what"] == p["what"] and q["group"] == p["group"]
                and q["usable"] and 0 < (p["x_dt"] - q["x_dt"]).days <= BASE_WINDOW_DAYS]
        if len(base) >= MIN_BASE:
            bi = statistics.median(q["x_imp"] for q in base)
            bv = statistics.median(q["th_views"] for q in base)
            p["x_imp_ratio"] = math.log2(p["x_imp"] / bi) if bi and p["x_imp"] else float("nan")
            p["th_views_ratio"] = math.log2(p["th_views"] / bv) if bv and p["th_views"] else float("nan")
            p["n_base"] = len(base)
        else:
            p["x_imp_ratio"] = float("nan")
            p["th_views_ratio"] = float("nan")
            p["n_base"] = len(base)


METRICS = [
    ("インプ vs views（log10）", "x_imp", "th_views", True),
    ("いいね vs いいね（log10）", "x_like", "th_like", True),
    ("リプライ vs リプライ", "x_reply", "th_reply", False),
    ("リポスト vs リポスト＋引用", "x_rp", "th_rp", False),
    ("エンゲ率 vs エンゲ率", "x_er", "th_er", False),
    ("いいね率 vs いいね率", "x_lr", "th_lr", False),
    ("直前 8 週中央値との比（log2）", "x_imp_ratio", "th_views_ratio", False),
]


def corr(xs, ys, log):
    a = np.array(xs, dtype=float)
    b = np.array(ys, dtype=float)
    ok = ~(np.isnan(a) | np.isnan(b))
    a, b = a[ok], b[ok]
    n = len(a)
    if n < 4:
        return n, float("nan"), float("nan"), float("nan")
    rho, p = stats.spearmanr(a, b)
    if log:
        a = np.log10(a + 1)
        b = np.log10(b + 1)
    r = float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else float("nan")
    return n, float(rho), float(p), r


def fmt(v, nd=2):
    return "—" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{nd}f}"


def strata(pairs):
    use = [p for p in pairs if p["usable"]]
    mir = [p for p in use if p["group"] == "mirror"]
    after = [p for p in mir if p["x_dt"] >= REGIME_START]
    return [
        ("全体（同時転載）", mir),
        (f"{REGIME_START:%m/%d} 以降", after),
        (f"{REGIME_START:%m/%d} 以降 z01", [p for p in after if p["what"] == "z01"]),
        (f"{REGIME_START:%m/%d} より前", [p for p in mir if p["x_dt"] < REGIME_START]),
        ("参考：後日転載", [p for p in use if p["group"] == "late"]),
    ]


def write_corr_md(pairs, skipped, today, out_dir, min_age_days):
    lines = []
    lines.append(f"# X × Threads 反応の相関（{today:%Y-%m-%d} 取得）\n")
    tot = len(pairs)
    mir = [p for p in pairs if p["group"] == "mirror"]
    late = [p for p in pairs if p["group"] == "late"]
    lines.append(f"- 結合できたペア: {tot}（同時転載 {len(mir)}、後日転載 {len(late)}）。"
                 f"結合できなかった outputs 行: X投稿一覧に無い {skipped['x_missing']}、Threads投稿一覧に無い {skipped['th_missing']}、"
                 f"Threads 側がリプライ {skipped['th_reply']}")
    use_mir = [p for p in mir if p["usable"]]
    lines.append(f"- 使用条件: X 投稿後 {min_age_days} 日以上・インプ>0・views>0 → 同時転載 {len(use_mir)} 件"
                 f"（型別: " + ", ".join(f"{w} {sum(1 for p in use_mir if p['what']==w)}"
                                         for w in sorted({p['what'] for p in use_mir})) + "）")
    th_ages = [p["th_age"] for p in use_mir]
    if th_ages:
        lines.append(f"- Threads 側の経過日数（取得日まで）: 中央値 {statistics.median(th_ages):.0f} 日、"
                     f"範囲 {min(th_ages)}〜{max(th_ages)} 日")
    lines.append("")
    lines.append("## 相関表（Spearman ρ / p / log Pearson r）\n")
    strata_list = strata(pairs)
    lines.append("| 指標 | " + " | ".join(name for name, _ in strata_list) + " |")
    lines.append("|---|" + "---|" * len(strata_list))
    for label, kx, ky, log in METRICS:
        cells = []
        for _, ps in strata_list:
            n, rho, p, r = corr([q[kx] for q in ps], [q[ky] for q in ps], log)
            cells.append(f"n={n} ρ={fmt(rho)} p={fmt(p, 3)} r={fmt(r)}")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")
    # 経過日数との相関（測定窓の偏りの確認）
    lines.append("## 測定窓の偏りの確認（同時転載・使用分）\n")
    n, rho, p, _ = corr([q["th_age"] for q in use_mir], [q["th_views"] for q in use_mir], False)
    lines.append(f"- Threads 経過日数 × views: n={n} ρ={fmt(rho)} p={fmt(p,3)}（正なら古い投稿ほど views が多い＝累積の偏り）")
    n, rho, p, _ = corr([q["x_age"] for q in use_mir], [q["x_imp"] for q in use_mir], False)
    lines.append(f"- X 経過日数 × インプ: n={n} ρ={fmt(rho)} p={fmt(p,3)}（時期の傾向。負なら新しい投稿ほど伸びている）")
    n, rho, p, _ = corr([q["x_age"] for q in use_mir], [q["th_views"] for q in use_mir], False)
    lines.append(f"- X 経過日数 × Threads views: n={n} ρ={fmt(rho)} p={fmt(p,3)}")
    lines.append("")
    # 中央値
    lines.append("## 中央値（同時転載・使用分）\n")
    lines.append("| 型 | n | X インプ | Th views | views/インプ | X いいね率 | Th いいね率 | X エンゲ率 | Th エンゲ率 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for name, ps in strata_list[:4]:
        if not ps:
            continue
        med = lambda k: statistics.median(q[k] for q in ps)  # noqa: E731
        lines.append(f"| {name} | {len(ps)} | {med('x_imp'):,.0f} | {med('th_views'):,.0f} | "
                     f"{statistics.median(q['th_views']/q['x_imp'] for q in ps):.2f} | "
                     f"{med('x_lr')*100:.2f}% | {med('th_lr')*100:.2f}% | {med('x_er')*100:.2f}% | {med('th_er')*100:.2f}% |")
    lines.append("")
    # 残差
    use_mir = [q for q in use_mir if q["x_dt"] >= REGIME_START]
    lines.append(f"## 残差（log10 views − log10 インプ の回帰からのずれ。同時転載・{REGIME_START:%m/%d} 以降）\n")
    a = np.log10(np.array([q["x_imp"] for q in use_mir], dtype=float))
    b = np.log10(np.array([q["th_views"] for q in use_mir], dtype=float))
    if len(a) >= 4:
        slope, intercept = np.polyfit(a, b, 1)
        for q, av, bv in zip(use_mir, a, b):
            q["resid"] = float(bv - (slope * av + intercept))
        lines.append(f"回帰: log10(views) = {slope:.2f} × log10(インプ) + {intercept:.2f}\n")
        ranked = sorted(use_mir, key=lambda q: q["resid"], reverse=True)
        for title, sel in (("Threads で相対的に伸びた 5 件", ranked[:5]), ("X に比べて Threads で伸びなかった 5 件", ranked[-5:][::-1])):
            lines.append(f"### {title}\n")
            lines.append("| 投稿日 | 型 | 本文 | X インプ | Th views | 残差 |")
            lines.append("|---|---|---|---|---|---|")
            for q in sel:
                lines.append(f"| {q['x_dt']:%m/%d} | {q['what']} | {q['text']} | {q['x_imp']:,} | {q['th_views']:,} | {q['resid']:+.2f} |")
            lines.append("")
    path = os.path.join(out_dir, "corr.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def write_pairs_csv(pairs, out_dir):
    path = os.path.join(out_dir, "pairs.csv")
    keys = ["x_dt", "th_dt", "lag_days", "what", "group", "usable", "x_age", "th_age", "text",
            "x_imp", "x_like", "x_rp", "x_reply", "x_bm", "x_eng", "x_er", "x_lr",
            "th_views", "th_like", "th_reply", "th_rp", "th_share", "th_eng", "th_er", "th_lr",
            "x_imp_ratio", "th_views_ratio", "n_base", "resid", "n_th_rows", "x_url", "th_url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for p in pairs:
            row = []
            for k in keys:
                v = p.get(k, "")
                if isinstance(v, datetime):
                    v = v.strftime("%Y-%m-%d %H:%M")
                elif isinstance(v, float):
                    v = "" if math.isnan(v) else f"{v:.4f}"
                row.append(v)
            w.writerow(row)
    return path


def scatter(pairs, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Noto Sans CJK JP"
    colors = {"z01": "#1f77b4", "W001": "#d62728", "W003": "#2ca02c", "W006": "#9467bd"}
    use = [p for p in pairs if p["usable"] and p["group"] == "mirror"]
    specs = [
        ("scatter_imp_views.png", "x_imp", "th_views", "X インプレッション（log）", "Threads views（log）", True),
        ("scatter_like_rate.png", "x_lr", "th_lr", "X いいね率", "Threads いいね率", False),
        ("scatter_ratio.png", "x_imp_ratio", "th_views_ratio", "X インプ ÷ 直前8週中央値（log2）", "Threads views ÷ 直前8週中央値（log2）", False),
    ]
    paths = []
    for fname, kx, ky, lx, ly, log in specs:
        fig, ax = plt.subplots(figsize=(7, 7))
        n = 0
        xs, ys = [], []
        for p in use:
            xv, yv = p[kx], p[ky]
            if any(isinstance(v, float) and math.isnan(v) for v in (xv, yv)):
                continue
            if log and (xv <= 0 or yv <= 0):
                continue
            n += 1
            xs.append(xv); ys.append(yv)
            pre = p["x_dt"] < REGIME_START
            ax.scatter(xv, yv, s=28, facecolors="none" if pre else colors.get(p["what"], "#7f7f7f"),
                       edgecolors=colors.get(p["what"], "#7f7f7f"), alpha=0.8)
            ax.annotate(p["text"][:8], (xv, yv), fontsize=6, alpha=0.6, xytext=(3, 2), textcoords="offset points")
        if log:
            ax.set_xscale("log"); ax.set_yscale("log")
        # 縦軸・横軸の目盛り範囲を揃える（同じ値が対角線に乗る）
        if xs:
            lo, hi = min(xs + ys), max(xs + ys)
            if log:
                lo, hi = lo / 1.5, hi * 1.5
            else:
                pad = (hi - lo) * 0.05 or 1
                lo, hi = lo - pad, hi + pad
            ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
            ax.plot([lo, hi], [lo, hi], color="#999", lw=0.8, ls="--", label="X ＝ Threads")
            ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel(lx); ax.set_ylabel(ly)
        ax.set_title(f"{lx} × {ly}（同時転載 n={n}）", fontsize=10)
        for w, c in colors.items():
            if any(p["what"] == w for p in use):
                ax.scatter([], [], color=c, label=w)
        ax.scatter([], [], facecolors="none", edgecolors="#555", label=f"白抜き: {REGIME_START:%m/%d} より前")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        path = os.path.join(out_dir, fname)
        fig.savefig(path, dpi=130)
        plt.close(fig)
        paths.append(path)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs", "reports", "x_threads_corr"))
    ap.add_argument("--min-age-days", type=int, default=9)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    today = datetime.now()

    gc = get_client()
    tid_to_what, th_links, x_by_tid, th_by_perma = load(gc)
    pairs, skipped = build_pairs(tid_to_what, th_links, x_by_tid, th_by_perma, today, args.min_age_days)
    add_baseline_ratio(pairs)
    md = write_corr_md(pairs, skipped, today, args.out, args.min_age_days)
    csv_path = write_pairs_csv(pairs, args.out)
    pngs = scatter(pairs, args.out)
    print(open(md, encoding="utf-8").read())
    print("出力:", csv_path, *pngs, sep="\n  ")


if __name__ == "__main__":
    main()
