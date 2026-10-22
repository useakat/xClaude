#!/usr/bin/env python3
"""
note 導線 改善施策レジストリ（docs/plans/note_funnel_measures.md）の施策ごとに、
検証用の数値を funnel CSV と発信記録シートから出す。判定はしない（reporter-weekly-ops STEP 5.7 が行う）。

数値の出どころ:
  funnel CSV … scripts/note_funnel_export.py が発信記録シートから書き出す 8 本。毎朝の routine は
               ダッシュボードのアセットにしか置かないので、既定では実行のたびに --out で一時フォルダに
               書き出してから読む（--data DIR で既存の CSV を指定すると書き出しを飛ばす）
  シート     … note記事日次（日付, 記事ID, タイトル, PV, スキ）、note購入記録（日付, 購入者, …, 購入, 価格）、
               日次記録 U「noteフォロワ数」を scripts/sheets_values.py 経由で読む（article_cvr / note_profile_weekly の時だけ）

指標キー（レジストリの順位表「指標キー」列。カンマ区切りで複数、":" の後ろは記事ID）:
  w001_selfreply_ctr          X・W001・セルフリプ: CTR ＝ Xリンククリック ÷ リンク到達（副: ビーコン ÷ リンク到達）
  w001_reach_rate             X・W001: 到達率 ＝ リンク到達 ÷ 本体IMP
  threads_post_clicks_weekly  tpost の週クリック合計、note流入元 Threads 列の週合計
  pinned_clicks_weekly        固定期間内の xpost / tpost キーの週クリック合計（媒体別）
  x_bio_weekly                X bio: プロフ・note到達・フォローの窓合算と率
  threads_bio_weekly          Threads bio: views・クリック・note到達・フォローの窓合算
  note_profile_weekly         note: フォロワー数（日次記録 U）の週純増、note流入元 note.com 列の週合計
  article_cvr:<記事ID>,...    記事ごとに価格区間（note価格履歴）別の PV・購入数・CVR¥（article_price_cvr.csv）。
                              実施日があれば現在価格の区間の中だけで before / after に分ける（区間をまたぐ比較はしない）
  price_cvr_compare:<記事ID>,... 同一記事の価格区間を並べ、CVR¥・販売係数・1,000 PV あたりの売上を比べる（N10）
  price_band_coeff            価格帯別の販売係数（ビュー ÷ 購入数）の中央値（累計・参考）

before / after の窓: 実施日（順位表）があればその前日までを before、当日以降を after。無ければ全期間を before。
週単位の指標（x_bio_weekly / threads_bio_weekly / note_profile_weekly）で実施日を含む週は、実施日が土日ならその週を before、
月火なら after、水〜金なら混在として除外する（2026-10-22）。週次 bio の窓は BIO_START（2026-09-07 の週）から。
クリック・note 到達は FUNNEL_START（2026-10-09）より前が空欄なので、到達を使う率はその週だけで計算する。
拡散週 VIRAL_WEEKS（9/14・9/21・9/28 の週。円周率の投稿）は N1〜N3 の窓から外す。
投稿単位の指標は現体制の開始日（2026-06-13）以降だけを使う。

使い方:
  python3 scripts/note_funnel_measures.py                  # 実施中の施策だけ、今週（月曜）基準
  python3 scripts/note_funnel_measures.py --week 2026-10-12
  python3 scripts/note_funnel_measures.py --all            # 状態に関係なく全施策
  python3 scripts/note_funnel_measures.py --data DIR       # 書き出し済み CSV を使う
  python3 scripts/note_funnel_measures.py --json           # JSON で出す（既定は Markdown 表）
"""

import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
EXPORT = os.path.join(SCRIPT_DIR, "note_funnel_export.py")
SHEETS_CLI = os.path.join(SCRIPT_DIR, "sheets_values.py")
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
DEFAULT_REGISTRY = os.path.join(REPO_ROOT, "docs", "plans", "note_funnel_measures.md")
REGIME_START = date(2026, 6, 13)   # 現体制の開始日（reporter-weekly-ops H6 と同じ）
FUNNEL_START = date(2026, 10, 9)   # 週次 bio ファネルのクリック・到達の集計開始日（note_funnel_export.py と同じ）
BIO_START = date(2026, 9, 7)       # 週次 bio ファネルの インプ・プロフ・フォロー の開始週（同上。よーん指示 2026-10-22）
# 拡散週（月曜）。娘の円周率の投稿（9/19 1,125 万 IMP・9/21 957 万・9/29 98 万）でプロフアクセスが 5,427・4,419・744 に跳ねた週。
# 宇宙探査と無関係の客層なので、N1〜N3（x_bio_weekly / threads_bio_weekly / note_profile_weekly）の窓から外す（よーん指示 2026-10-22）
VIRAL_WEEKS = {date(2026, 9, 14), date(2026, 9, 21), date(2026, 9, 28)}


# ---- 共通 -----------------------------------------------------------------
def num(s) -> float | None:
    s = str(s or "").replace(",", "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def to_date(s: str) -> date | None:
    s = str(s or "").strip().replace("/", "-")[:10]
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def split_weeks(rows, start: date | None, week_of):
    """週単位の行を before / after に分ける。実施日を含む週は、実施日が土日なら before、月火なら after、水〜金なら除外（混在）"""
    if not start:
        return list(rows), []
    before, after = [], []
    for r in rows:
        w = week_of(r)
        if w < monday(start):
            before.append(r)
        elif w > monday(start):
            after.append(r)
        elif start.weekday() >= 5:
            before.append(r)
        elif start.weekday() <= 1:
            after.append(r)
    return before, after


def median(xs: list[float]) -> float | None:
    return statistics.median(xs) if xs else None


def pct(x: float | None, digits: int = 2) -> str:
    return "" if x is None else f"{x * 100:.{digits}f}%"


def read_csv(data_dir: str, name: str) -> list[dict]:
    with open(os.path.join(data_dir, name + ".csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sheet(rng: str) -> list[list[str]]:
    out = subprocess.run([sys.executable, SHEETS_CLI, "get", SS3, rng], capture_output=True, text=True, check=True).stdout
    return json.loads(out).get("values", [])


# ---- レジストリ -----------------------------------------------------------
def read_registry(path: str) -> list[dict]:
    """順位表（| 順位 | ID | 施策 | 段階 | 状態 | 実施日 | 指標キー | 直近判定 |）を行パースする"""
    rows = []
    in_table = False
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("## 順位表"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0] in ("順位", "") or set(cells[0]) <= {"-"}:
            continue
        rows.append({"順位": cells[0], "ID": cells[1], "施策": cells[2], "段階": cells[3], "状態": cells[4],
                     "実施日": to_date(cells[5]), "指標キー": [k.strip() for k in cells[6].split(",") if k.strip()] if "," in cells[6] and ":" not in cells[6] else [cells[6]],
                     "直近判定": cells[7] if len(cells) > 7 else ""})
    return rows


# ---- 指標 -----------------------------------------------------------------
def split_window(items: list[tuple[date, dict]], start: date | None):
    """実施日で before / after に分ける。実施日が無ければ全部 before"""
    if start is None:
        return [x for _, x in items], []
    return [x for d, x in items if d < start], [x for d, x in items if d >= start]


def w001_posts(data: dict, selfreply_only: bool) -> list[tuple[date, dict]]:
    out = []
    for r in data["funnel_posts"]:
        if r["媒体"] != "X" or r["型"] != "W001":
            continue
        if selfreply_only and r["リンク位置"] != "セルフリプ":
            continue
        d = to_date(r["投稿日"])
        if d is None or d < REGIME_START:
            continue
        out.append((d, r))
    return sorted(out, key=lambda x: x[0])


def m_w001_selfreply_ctr(data, start, week):
    posts = w001_posts(data, selfreply_only=True)
    def row(r):
        reach, xlc, beacon = num(r["リンク到達"]), num(r["Xリンククリック"]), num(r["クリック"]) if r["クリックの出どころ"] == "ビーコン" else None
        return {"投稿日": r["投稿日"], "本文冒頭": r["本文冒頭"][:20], "リンク到達": reach, "Xリンククリック": xlc,
                "CTR": (xlc / reach) if reach and xlc is not None else None,
                "ビーコンCTR": (beacon / reach) if reach and beacon is not None else None, "地力IMP": num(r["地力IMP"])}
    before, after = split_window([(d, row(r)) for d, r in posts], start)
    def summary(rows):
        ctrs = [x["CTR"] for x in rows if x["CTR"] is not None]
        return {"n": len(ctrs), "CTR中央値": median(ctrs), "地力IMP中央値": median([x["地力IMP"] for x in rows if x["地力IMP"]])}
    bm = summary(before)["CTR中央値"]
    s_after = summary(after)
    s_after["before中央値超の本数"] = sum(1 for x in after if x["CTR"] is not None and bm is not None and x["CTR"] > bm)
    return {"before": summary(before), "after": s_after,
            "内訳": [x for x in after] or before[-5:],
            "表示": f"before n={summary(before)['n']} 中央値 {pct(bm)} → after n={s_after['n']} 中央値 {pct(s_after['CTR中央値'])}"
                    + (f"（before 超 {s_after['before中央値超の本数']}/{s_after['n']}）" if after else "")}


def m_w001_reach_rate(data, start, week):
    posts = w001_posts(data, selfreply_only=False)
    def row(r):
        imp, reach = num(r["本体IMP"]), num(r["リンク到達"])
        return {"投稿日": r["投稿日"], "本文冒頭": r["本文冒頭"][:20], "本体IMP": imp, "リンク到達": reach,
                "リンク位置": r["リンク位置"], "到達率": (reach / imp) if imp and reach is not None else None}
    before, after = split_window([(d, row(r)) for d, r in posts], start)
    def summary(rows):
        rates = [x["到達率"] for x in rows if x["到達率"] is not None]
        return {"n": len(rates), "到達率中央値": median(rates), "0.5%未満": sum(1 for v in rates if v < 0.005)}
    sb, sa = summary(before), summary(after)
    return {"before": sb, "after": sa, "内訳": after or before[-5:],
            "表示": f"before n={sb['n']} 中央値 {pct(sb['到達率中央値'], 1)} → after n={sa['n']} 中央値 {pct(sa['到達率中央値'], 1)}（0.5%未満 {sa['0.5%未満']} 本）"}


def weekly_clicks(data, host_filter, key_filter=None) -> dict[date, int]:
    out: dict[date, int] = {}
    for r in data["click_detail"]:
        d = to_date(r["日付"])
        if d is None or not host_filter(r["ホスト"]):
            continue
        if key_filter and not key_filter(d, r["ホスト"], r["キー"]):
            continue
        out[monday(d)] = out.get(monday(d), 0) + int(num(r["クリック"]) or 0)
    return out


def weekly_referrers(data, column: str) -> dict[date, int]:
    out: dict[date, int] = {}
    for r in data["note_referrers"]:
        d = to_date(r["日付"])
        if d is None:
            continue
        out[monday(d)] = out.get(monday(d), 0) + int(num(r.get(column)) or 0)
    return out


def weeks_between(a: date, b: date) -> list[date]:
    w, out = monday(a), []
    while w <= b:
        out.append(w)
        w += timedelta(days=7)
    return out


def m_threads_post_clicks_weekly(data, start, week):
    clicks = weekly_clicks(data, lambda h: h == "tpost.usephys.net")
    arrive = weekly_referrers(data, "Threads 投稿")
    first = date(2026, 10, 4)
    def window(w):
        if not start:
            return "before"
        if w == monday(start) and start.weekday() != 0:
            return "混在"  # 実施日を含む週は before/after のどちらにも入れない
        return "after" if w >= monday(start) else "before"
    rows = [{"週": w.isoformat(), "tpostクリック": clicks.get(w, 0), "note到達(Threads投稿)": arrive.get(w, 0), "窓": window(w)}
            for w in weeks_between(first, week)]
    before = [r["tpostクリック"] for r in rows if r["窓"] == "before"]
    after = [r["tpostクリック"] for r in rows if r["窓"] == "after" and r["週"] != week.isoformat()]  # 集計中の週は除く
    mixed = [f"{r['週']}: {r['tpostクリック']}" for r in rows if r["窓"] == "混在"]
    return {"週別": rows, "before": {"週数": len(before), "中央値": median(before), "実数": before},
            "after": {"週数": len(after), "中央値": median(after), "実数": after}, "混在": mixed,
            "表示": f"before 週クリック {before} → after {after}（当週 {clicks.get(week, 0)} は集計中"
                    + (f"；実施日を含む週 {mixed} は除外" if mixed else "") + "）"}


def m_pinned_clicks_weekly(data, start, week):
    pins = []
    for p in data["pinned"]:
        s, e = to_date(p["開始日"]), to_date(p["終了日"])
        pins.append((p["媒体"], s, e, p["記事ID"], p["投稿キー"]))
    def in_pin(media):
        def f(d, host, key):
            aid = key.split("/", 1)[0]
            pk = key.split("/", 1)[1] if "/" in key else ""
            return any(m == media and s and s <= d and (not e or d <= e) and a == aid and (not k or k == pk) for m, s, e, a, k in pins)
        return f
    out = {}
    for media, host in (("X", "xpost.usephys.net"), ("Threads", "tpost.usephys.net")):
        wk = weekly_clicks(data, lambda h, host=host: h == host, in_pin(media))
        rows = [{"週": w.isoformat(), "クリック": wk.get(w, 0)} for w in weeks_between(FUNNEL_START, week)]
        done = [r["クリック"] for r in rows if r["週"] != week.isoformat()]
        out[media] = {"週別": rows, "中央値（集計済み週）": median(done), "当週（集計中）": wk.get(week, 0)}
    return {**out, "表示": "; ".join(f"{m} 週クリック {[r['クリック'] for r in out[m]['週別']]}（中央値 {out[m]['中央値（集計済み週）']}）" for m in out)}


def bio_window(data, route, start, week):
    rows = [r for r in data["funnel_weekly"] if r["経路"] == route and to_date(r["週"]) not in VIRAL_WEEKS]
    def agg(sel):
        tot = {k: sum(int(num(r[k]) or 0) for r in sel) for k in ("インプ", "リンク到達", "クリック", "note到達", "フォロー")}
        prof = tot["リンク到達"]
        tot["週数"] = len(sel)
        # 到達・クリックは FUNNEL_START より前の週が空欄なので、それを使う率は到達のある週だけで計算する
        arr = [r for r in sel if str(r.get("note到達", "")).strip() != ""]
        tot["到達週数"] = len(arr)
        tot["到達週プロフ"] = sum(int(num(r["リンク到達"]) or 0) for r in arr)
        tot["到達週インプ"] = sum(int(num(r["インプ"]) or 0) for r in arr)
        tot["到達週クリック"] = sum(int(num(r["クリック"]) or 0) for r in arr)
        if route == "X bio":
            tot["CTR"] = tot["note到達"] / tot["到達週プロフ"] if tot["到達週プロフ"] else None
            tot["フォロー率"] = tot["フォロー"] / prof if prof else None
            tot["週別フォロー率"] = [pct((int(num(r["フォロー"]) or 0) / int(num(r["リンク到達"])) if num(r["リンク到達"]) else None), 0) for r in sel]
        else:
            tot["到達率"] = tot["note到達"] / tot["到達週クリック"] if tot["到達週クリック"] else None
            tot["到達/万views"] = tot["note到達"] / tot["到達週インプ"] * 10000 if tot["到達週インプ"] else None
            vw = [r for r in sel if str(r.get("インプ", "")).strip() != ""]  # views の取れる週だけ（日次記録 threads views は 9/28 週から）
            tot["views週フォロー"] = sum(int(num(r["フォロー"]) or 0) for r in vw)
            tot["フォロー/万views"] = tot["views週フォロー"] / tot["インプ"] * 10000 if tot["インプ"] else None
        return tot
    before, after = split_weeks(rows, start, lambda r: to_date(r["週"]))
    return {"週別": rows, "before": agg(before), "after": agg(after)}


def m_x_bio_weekly(data, start, week):
    w = bio_window(data, "X bio", start, week)
    b, a = w["before"], w["after"]
    def one(x):
        return (f"{x['週数']}週 プロフ {x['リンク到達']} フォロー {x['フォロー']}（フォロー率 {pct(x['フォロー率'], 0)}、週別 {x['週別フォロー率']}）"
                f" / 到達のある {x['到達週数']}週 プロフ {x['到達週プロフ']} → 到達 {x['note到達']}（CTR {pct(x['CTR'], 0)}）")
    w["表示"] = f"before {one(b)}" + (f" / after {one(a)}" if a["週数"] else "")
    return w


def m_threads_bio_weekly(data, start, week):
    w = bio_window(data, "Threads bio", start, week)
    b, a = w["before"], w["after"]
    def one(x):
        return (f"{x['週数']}週 views {x['インプ']} フォロー {x['フォロー']}（views のある週 {x['views週フォロー']}、{x['フォロー/万views'] if x['フォロー/万views'] is None else round(x['フォロー/万views'], 2)}/万views）"
                f" / 到達のある {x['到達週数']}週 views {x['到達週インプ']} クリック {x['到達週クリック']} 到達 {x['note到達']}（{x['到達/万views'] if x['到達/万views'] is None else round(x['到達/万views'], 2)}/万views）")
    w["表示"] = f"before {one(b)}" + (f" / after {one(a)}" if a["週数"] else "")
    return w


def m_note_profile_weekly(data, start, week, cache: dict):
    """note フォロワー数の週純増（日次記録 U、週末値 − 前週末値）と note.com 内部流入の週合計"""
    if "daily_rec" not in cache:
        cache["daily_rec"] = sheet("日次記録!A:U")
    fol = {}
    for r in cache["daily_rec"][1:]:
        d = to_date(r[0]) if r else None
        v = num(r[20]) if len(r) > 20 else None
        if d and v is not None:
            fol[d] = int(v)
    def week_end_val(mon):
        for i in range(6, -1, -1):
            v = fol.get(mon + timedelta(days=i))
            if v is not None:
                return v
        return None
    ref = {}
    for r in data["note_referrers"]:
        d = to_date(r.get("日付", ""))
        if d and d >= BIO_START:
            ref[monday(d)] = ref.get(monday(d), 0) + int(num(r.get("note.com")) or 0)
    rows = []
    for w in weeks_between(BIO_START, week):
        cur, prev = week_end_val(w), week_end_val(w - timedelta(days=7))
        rows.append({"週": w.isoformat(), "noteフォロワ純増": (cur - prev) if cur is not None and prev is not None else None,
                     "noteフォロワ数": cur, "note.com流入": ref.get(w, 0), "集計中": w == week})
    def agg(sel):
        inc = [r["noteフォロワ純増"] for r in sel if r["noteフォロワ純増"] is not None]
        return {"週数": len(sel), "フォロワ純増中央値": median(inc), "フォロワ純増合計": sum(inc), "note.com流入合計": sum(r["note.com流入"] for r in sel)}
    rows = [r for r in rows if to_date(r["週"]) not in VIRAL_WEEKS]
    before, after = split_weeks(rows, start, lambda r: to_date(r["週"]))
    b, a = agg(before), agg(after)
    disp = (f"before {b['週数']}週 noteフォロワ純増 {[r['noteフォロワ純増'] for r in before]}（中央値 {b['フォロワ純増中央値']}）note.com流入 {[r['note.com流入'] for r in before]}"
            + (f" / after {a['週数']}週 純増 {[r['noteフォロワ純増'] for r in after]}（中央値 {a['フォロワ純増中央値']}）note.com流入 {[r['note.com流入'] for r in after]}" if a["週数"] else ""))
    return {"週別": rows, "before": b, "after": a, "表示": disp}


def load_article_sheets(cache: dict):
    if "daily" not in cache:
        cache["daily"] = sheet("note記事日次!A:E")
        cache["buy"] = sheet("note購入記録!A:G")
    return cache["daily"], cache["buy"]


def _segments(data, aid):
    return sorted([r for r in data["article_price_cvr"] if r["記事ID"] == aid], key=lambda r: r["開始日"])


def _seg_label(r):
    pv, buys = int(num(r["PV"]) or 0), int(num(r["購入数"]) or 0)
    cvr = (buys / pv) if pv else None
    incomplete = int(num(r["PV取得日数"]) or 0) < int(num(r["日数"]) or 0)
    return f"¥{r['価格']}（{r['開始日']}〜{r['終了日'] or ''}）PV {pv:,}{'※' if incomplete else ''} 購入 {buys}（CVR¥{r['価格']} {pct(cvr)}）"


def m_article_cvr(data, start, week, article_ids: list[str], cache: dict):
    """記事ごとに価格区間別の PV・購入・CVR¥。実施日（改稿日）があれば、現在価格の区間の中で before / after に分ける。
    ※ ＝ 区間の日別 PV が揃っていない（バックフィル前）"""
    daily, buy = load_article_sheets(cache)
    titles = {r["記事ID"]: r["タイトル"] for r in data["articles"]}
    out = {}
    for aid in article_ids:
        if aid == "new":
            continue
        segs = _segments(data, aid)
        cur = next((r for r in segs if not r["終了日"]), None)
        item = {"タイトル": titles.get(aid, "")[:20], "価格区間": [{k: r[k] for k in ("価格", "開始日", "終了日", "日数", "PV", "購入数", "CVR", "販売係数", "売上", "PV取得日数")} for r in segs]}
        if start and cur:
            seg_start = to_date(cur["開始日"])
            title = titles.get(aid, "")
            pv = [(to_date(r[0]), int(num(r[3]) or 0)) for r in daily[1:] if len(r) > 3 and r[1] == aid and to_date(r[0])]
            purchases = [to_date(r[0]) for r in buy[1:] if len(r) > 4 and to_date(r[0]) and title and
                         ((r[4].strip() == title) or title.startswith(r[4].strip()) or title[:15] == r[4].strip()[:15])]
            def agg(cond):
                p = sum(v for d, v in pv if d >= seg_start and cond(d))
                n = sum(1 for d in purchases if d >= seg_start and cond(d))
                return {"PV": p, "購入": n, "CVR": (n / p) if p else None}
            item["現価格区間の before"] = agg(lambda d: d < start)
            item["現価格区間の after"] = agg(lambda d: d >= start)
            item["注記"] = f"before / after は現在価格 ¥{cur['価格']} の区間（{cur['開始日']}〜）の中だけ。改稿と値上げを同時にしない"
        out[aid] = item
    def disp(aid, v):
        segs = _segments(data, aid)
        s_ = f"{v['タイトル'][:10]}: " + "; ".join(_seg_label(r) if int(num(r["価格"]) or 0) > 0 else f"無料（{r['開始日']}〜{r['終了日'] or ''}）PV {int(num(r['PV']) or 0):,}{'※' if int(num(r['PV取得日数']) or 0) < int(num(r['日数']) or 0) else ''}" for r in segs)
        if "現価格区間の after" in v:
            b, a = v["現価格区間の before"], v["現価格区間の after"]
            s_ += f" ／ 現価格区間 before PV {b['PV']} 購入 {b['購入']}（{pct(b['CVR'])}）→ after PV {a['PV']} 購入 {a['購入']}（{pct(a['CVR'])}）"
        return s_
    return {"記事": out, "表示": " | ".join(disp(aid, v) for aid, v in out.items()) or "対象記事なし（new は公開後に記事IDを登録）"}


def m_price_cvr_compare(data, start, week, article_ids: list[str], cache: dict):
    """同一記事の価格区間を並べて、CVR¥・販売係数・1,000 PV あたりの売上を比べる（N10 価格帯の検証）"""
    titles = {r["記事ID"]: r["タイトル"] for r in data["articles"]}
    out, disp = {}, []
    for aid in article_ids:
        rows = []
        for r in _segments(data, aid):
            price, pv, buys = int(num(r["価格"]) or 0), int(num(r["PV"]) or 0), int(num(r["購入数"]) or 0)
            if price <= 0:
                continue
            rows.append({"価格": price, "期間": f"{r['開始日']}〜{r['終了日'] or ''}", "日数": int(num(r["日数"]) or 0), "PV": pv, "購入数": buys,
                         "CVR": (buys / pv) if pv else None, "販売係数": (pv / buys) if buys and pv else None,
                         "売上/1000PV": (buys * price / pv * 1000) if pv else None, "PV取得日数": int(num(r["PV取得日数"]) or 0),
                         "比較可": pv >= 300})
        out[aid] = {"タイトル": titles.get(aid, "")[:20], "価格区間": rows}
        disp.append(f"{titles.get(aid, '')[:10]}: " + "; ".join(
            f"¥{x['価格']} PV {x['PV']:,}{'' if x['PV取得日数'] >= x['日数'] else '※'} 購入 {x['購入数']} CVR¥{x['価格']} {pct(x['CVR'])} 売上/1000PV {x['売上/1000PV']:.0f}円{'' if x['比較可'] else '（PV<300）'}"
            if x["売上/1000PV"] is not None else f"¥{x['価格']} PV 0" for x in rows))
    return {"記事": out, "表示": " | ".join(disp) or "対象記事なし"}


def m_price_band_coeff(data, start, week):
    bands: dict[str, list] = {}
    for r in data["articles"]:
        price = num(r.get("価格"))
        if not price:
            continue
        band = f"¥{int(price)}"
        bands.setdefault(band, []).append({"記事ID": r["記事ID"], "ビュー": num(r["ビュー（累計）"]), "購入数": num(r["購入数"]), "販売係数": num(r["販売係数"])})
    summary = {b: {"記事数": len(v), "購入合計": int(sum(x["購入数"] or 0 for x in v)), "販売係数中央値": median([x["販売係数"] for x in v if x["販売係数"]])} for b, v in sorted(bands.items())}
    return {"価格帯": summary, "内訳": bands,
            "表示": "; ".join(f"{b} 記事 {s['記事数']}・購入 {s['購入合計']}・販売係数中央値 {s['販売係数中央値']}" for b, s in summary.items())}


METRICS = {
    "w001_selfreply_ctr": m_w001_selfreply_ctr,
    "w001_reach_rate": m_w001_reach_rate,
    "threads_post_clicks_weekly": m_threads_post_clicks_weekly,
    "pinned_clicks_weekly": m_pinned_clicks_weekly,
    "x_bio_weekly": m_x_bio_weekly,
    "threads_bio_weekly": m_threads_bio_weekly,
    "price_band_coeff": m_price_band_coeff,
}


# ---- main -----------------------------------------------------------------
def export_csvs() -> str:
    out = tempfile.mkdtemp(prefix="note_funnel_")
    r = subprocess.run([sys.executable, EXPORT, "--out", out], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"note_funnel_export.py 失敗: {r.stderr.strip()[-300:]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="基準週の月曜（YYYY-MM-DD）。既定は今週")
    ap.add_argument("--registry", default=DEFAULT_REGISTRY)
    ap.add_argument("--data", help="書き出し済み funnel CSV のフォルダ（省略時は note_funnel_export.py で一時フォルダに書き出す）")
    ap.add_argument("--all", action="store_true", help="状態に関係なく全施策を出す")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    week = monday(to_date(args.week) or date.today())
    measures = read_registry(args.registry)
    targets = measures if args.all else [m for m in measures if m["状態"].startswith("実施中")]
    if not targets:
        print("対象の施策がありません（実施中が 0 件。--all で全施策）")
        return 0

    data_dir = args.data or export_csvs()
    data = {name: read_csv(data_dir, name) for name in ("funnel_posts", "funnel_weekly", "click_detail", "pinned", "articles", "note_referrers", "article_price_cvr")}
    cache: dict = {}
    results = []
    for m in targets:
        for key in m["指標キー"]:
            name, _, arg = key.partition(":")
            try:
                if name == "article_cvr":
                    res = m_article_cvr(data, m["実施日"], week, [a.strip() for a in arg.split(",") if a.strip()], cache)
                elif name == "price_cvr_compare":
                    res = m_price_cvr_compare(data, m["実施日"], week, arg.split(","), cache)
                elif name == "note_profile_weekly":
                    res = m_note_profile_weekly(data, m["実施日"], week, cache)
                elif name in METRICS:
                    res = METRICS[name](data, m["実施日"], week)
                else:
                    res = {"表示": f"未対応の指標キー: {key}"}
            except Exception as e:  # noqa: BLE001
                res = {"表示": f"取得失敗: {type(e).__name__}: {e}"}
            results.append({"ID": m["ID"], "施策": m["施策"], "段階": m["段階"], "状態": m["状態"],
                            "実施日": m["実施日"].isoformat() if m["実施日"] else "", "指標キー": key, "値": res})

    if args.json:
        print(json.dumps({"週": week.isoformat(), "data_dir": data_dir, "結果": results}, ensure_ascii=False, indent=1, default=str))
        return 0
    print(f"基準週: {week.isoformat()}（月曜）  CSV: {data_dir}\n")
    print("| ID | 施策 | 段階 | 状態 | 指標キー | 今週の値（before→after, n） |")
    print("|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['ID']} | {r['施策']} | {r['段階']} | {r['状態']}{'（' + r['実施日'] + '〜）' if r['実施日'] else ''} | {r['指標キー']} | {r['値'].get('表示', '')} |")
    print("\n（判定は reporter-weekly-ops STEP 5.7 がレジストリの判定条件と照合して行う。詳細は --json）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
