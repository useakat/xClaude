#!/usr/bin/env python3
"""
note 導線ダッシュボード（claude.ai Artifact）用のデータを発信記録シートから CSV に書き出す。

書き出すもの（既定: logs/note_funnel/）:
  bio_clicks.csv      … bioクリック シート（経路別の人のクリック、日別）
  click_detail.csv    … 転送クリック明細 ＋ 記事タイトル・その日の記事 PV/スキ（note記事日次）・スキ累計（note投稿一覧）
  note_referrers.csv  … note流入元 シート
  pinned.csv          … 固定ポスト履歴 シート
  x_note_posts.csv    … X投稿一覧のうち noteURL がある行（数値はカンマ除去、記事ID を付与）
  articles.csv        … note 記事ごとの指標（note投稿一覧）＋ 転送クリック合計・導線数・X 投稿数・購入数（note購入記録）・CVR・販売係数・スキ購入係数・価格（note投稿一覧 N列。note_article_daily.py が公開 API から毎日更新。0 ＝ 無料記事）
  funnel_weekly.csv   … 週次ファネル（月曜始まり）: X bio / X 固定 / Threads bio / Threads 固定 の
                        インプ → リンク到達 → クリック → note 到達（到達は bio のみ）
  funnel_posts.csv    … 投稿ごとのファネル（累計）: X 本体＋セルフリプ / Threads 投稿＋セルフリプ の
                        本体 IMP → リンク到達（セルフリプ IMP）→ クリック。型（outputs シートの what_id、W001 など）付き。
                        X集計でリンククリックが未取込の投稿はクリックを空にする（0 と区別）。
                        地力IMP ＝ 直前 14 日の非 W001 親ポストの IMP 中央値（アカウントの拡散力の補正用）

ダッシュボード側のデータセット id は CSV のファイル名（拡張子なし）と同じ。
列名を変えるとダッシュボードの表・計算が壊れるので、変えるときはページも直す。

段階の定義（2026-10-10 計画）:
  週次（集計は FUNNEL_START ＝ 2026-10-09 から。それを含む週は開始日からの部分集計）
    X bio        インプ＝その週に投稿したポストの IMP 合計（X投稿一覧 K）／リンク到達＝プロフアクセス合計（同 Q）
                 ／クリック＝bioクリック X bio／到達＝note流入元 X bio
    X 固定       インプ＝プロフアクセス合計／リンク到達＝固定ポストの IMP の週増分（固定ポスト日次）
                 ／クリック＝固定期間中の xpost キーのクリック
    Threads bio  インプ＝アカウント views の週合計（日次記録 AE「threads views」）／リンク到達＝（取れない）
                 ／クリック＝bioクリック Threads bio／到達＝note流入元 Threads bio
    Threads 固定 インプ＝アカウント views／リンク到達＝固定投稿 views の週増分／クリック＝固定期間中の tpost キー
  投稿ごと
    本体 IMP（X投稿一覧 K / Threads投稿一覧 I）→ リンク到達（セルフリプ行の IMP。本体にリンクがあるときは本体 IMP）
    → クリック（転送クリック明細のビーコン累計。xpost 導入前の生 note リンクは X アナリティクスのリンククリック）
  元投稿の特定はリンク本文一致 → 固定ポスト履歴 の 2 段だけ（投稿キーの日付での推定はしない）。
  見つからないキーは「元投稿不明」の行にする。

使い方:
  python3 scripts/note_funnel_export.py            # logs/note_funnel/ に書き出す
  python3 scripts/note_funnel_export.py --out DIR  # 出力先を変える

Sheets の読み取りは scripts/sheets_values.py（サービスアカウント）経由。routine / ローカルの両方で動く。
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SHEETS_CLI = os.path.join(SCRIPT_DIR, "sheets_values.py")
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録
SS2 = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"  # outputs（投稿の型 what_id: W001 など）
DEFAULT_OUT = os.path.join(REPO_ROOT, "logs", "note_funnel")
ARTICLE_ID = re.compile(r"(n[0-9a-f]{10,16})")
JST = timezone(timedelta(hours=9))
FUNNEL_START = date(2026, 10, 9)  # 週次ファネルの集計開始日（よーん指示 2026-10-12）。案内ページ化（10/8 22:57）より前はスキャナが note 到達に混ざるため、10/8 までは含めない
WEEK_START = FUNNEL_START - timedelta(days=FUNNEL_START.weekday())  # 集計開始日を含む週の月曜（10/5）。この週は 10/9 からの集計
SCANNER_UNTIL = "2026-10-08"    # この日まで note 到達にスキャナが混入（ホスト直下の案内ページ化前）

# 転送ホスト → 経路名（bioクリック シートの列名と同じ）。redirects.json の column と一致させる
HOST_ROUTE = {
    "usephys.net": "X bio", "threads.usephys.net": "Threads bio",
    "xpost.usephys.net": "X 投稿", "tpost.usephys.net": "Threads 投稿",
    "note.usephys.net": "X 固定", "tnote.usephys.net": "Threads 固定",
}


def get(rng: str, ssid: str = SS3) -> list[list[str]]:
    out = subprocess.run([sys.executable, SHEETS_CLI, "get", ssid, rng], capture_output=True, text=True, check=True)
    return json.loads(out.stdout).get("values", [])


def get_optional(rng: str, ssid: str = SS3) -> list[list[str]]:
    try:
        return get(rng, ssid)
    except subprocess.CalledProcessError:
        print(f"警告: {rng} が読めない（未作成？）。空として扱う", file=sys.stderr)
        return []


def num(s) -> str:
    return str(s or "").replace(",", "").replace("%", "").strip()


def to_int(s) -> int:
    try:
        return int(float(num(s) or 0))
    except ValueError:
        return 0


def write(path: str, rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def short(title: str, n: int = 10) -> str:
    return title if len(title) <= n else title[:n] + "…"


def ymd(s: str) -> str:
    """'2026/10/08 9:18:31' / '2026-10-08 09:32' → '2026-10-08'"""
    s = (s or "").strip().replace("/", "-")[:10]
    p = s.split("-")
    return f"{p[0]}-{p[1]:>02}-{p[2]:>02}".replace(" ", "0") if len(p) == 3 else s


def parse_dt(s: str):
    """'2026/03/18 17:51:21' などを datetime に。読めなければ None"""
    s = (s or "").strip()
    for f in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], f)
        except ValueError:
            continue
    return None


def table(rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    """1 行目を見出しにし、各行を見出しの長さに揃える"""
    if not rows:
        return [], []
    hdr = rows[0]
    return hdr, [r + [""] * (len(hdr) - len(r)) for r in rows[1:]]


def col(hdr: list[str], name: str):
    return hdr.index(name) if name in hdr else None


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def week_label(mon: date) -> str:
    sun = mon + timedelta(days=6)
    return f"{mon.month}/{mon.day}〜{sun.month}/{sun.day}"


def fetch_prices(article_ids: list[str], cache_path: str) -> dict[str, int]:
    """note の公開 API（/api/v3/notes/<key>）から記事の価格を取る。0 ＝ 無料（有料部分なし）。
    価格はめったに変わらないので cache_path に 7 日キャッシュし、取れなかった記事は空（判定不能）のまま"""
    import time
    import urllib.request
    cache: dict = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, encoding="utf-8") as f:
                cache = json.load(f)
        except (OSError, ValueError):
            cache = {}
    now = time.time()
    out: dict[str, int] = {}
    for aid in article_ids:
        c = cache.get(aid)
        if c and now - c.get("at", 0) < 7 * 86400 and isinstance(c.get("price"), int):
            out[aid] = c["price"]
            continue
        try:
            req = urllib.request.Request(f"https://note.com/api/v3/notes/{aid}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                price = (json.load(r).get("data") or {}).get("price")
            if isinstance(price, int):
                out[aid] = price
                cache[aid] = {"price": price, "at": now}
        except Exception as e:  # noqa: BLE001
            print(f"⚠ 価格の取得に失敗 {aid}: {e}", file=sys.stderr)
            if c and isinstance(c.get("price"), int):
                out[aid] = c["price"]
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except OSError:
        pass
    return out


def find_link_row(host: str, key: str, media: str, pin: dict | None, x_rows, x_idx, t_rows, t_idx):
    """`ホスト/キー` を含む投稿行（X投稿一覧 / Threads投稿一覧）を返す。
    (1) リンク本文一致（X は noteURL と本文、Threads は本文）、(2) 固定ポスト履歴の投稿ID。どちらも無ければ None"""
    link = f"{host}/{key}"
    has_link = re.compile(re.escape(link) + r"(?![/A-Za-z0-9_-])").search  # /ID は /ID/キー に一致させない
    if media == "X":
        rows = [r for r in x_rows if has_link(r[x_idx["noteURL"]]) or has_link(r[x_idx["ポスト本文"]])]
        if not rows and pin:
            rows = [r for r in x_rows if r[x_idx["ポストURL"]].rstrip("/").endswith("/" + pin["投稿ID"])]
    else:
        rows = [r for r in t_rows if has_link(r[t_idx["本文"]])]
        if not rows and pin:
            rows = [r for r in t_rows if r[t_idx["投稿URL"]].rstrip("/").endswith("/" + pin["投稿ID"])]
    return rows[0] if rows else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    today = datetime.now(JST).date()

    # ---- 読み込み ----
    note_hdr, note_rows = table(get("note投稿一覧!A:N"))
    daily_rows = get_optional("note記事日次!A:E")
    bio = get("bioクリック!A:J")
    det = get("転送クリック明細!A:D")
    ref = get("note流入元!A:P")
    pinned_raw = get("固定ポスト履歴!A:H")
    x_hdr, x_rows = table(get("X投稿一覧!A1:AK"))
    t_hdr, t_rows = table(get("Threads投稿一覧!A:S"))
    buy_hdr, buy_rows = table(get_optional("note購入記録!A:G"))
    snap_hdr, snap_rows = table(get_optional("固定ポスト日次!A:F"))
    dr_hdr, dr_rows = table(get("日次記録!A:AE"))
    out_hdr, out_rows = table(get_optional("outputs!A:C", SS2))  # 日時, URL, what_id
    x_idx = {h: i for i, h in enumerate(x_hdr)}
    t_idx = {h: i for i, h in enumerate(t_hdr)}

    # ---- 記事マスタ ----
    articles: dict[str, dict] = {}
    for r in note_rows:
        m = ARTICLE_ID.search(r[1])
        if m:
            articles[m.group(1)] = {"title": r[2], "like_total": num(r[8]), "date": ymd(r[0]), "chars": num(r[3]),
                                    "view_total": num(r[7]), "like_rate": num(r[9]), "comments": num(r[11]), "sales": num(r[12]),
                                    "price": (r[13] if len(r) > 13 else "").strip()}
    daily: dict[tuple[str, str], tuple[str, str]] = {}
    for r in daily_rows[1:]:
        r = r + [""] * (5 - len(r))
        if r[0] and r[1]:
            daily[(r[0], r[1])] = (num(r[3]), num(r[4]))
            articles.setdefault(r[1], {"title": r[2], "like_total": ""})

    def title_of(aid: str, n: int = 10) -> str:
        if not aid:
            return ""
        t = articles.get(aid, {}).get("title", "")
        return short(t, n) if t else "（タイトル未取得）"

    # ---- bio_clicks / note_referrers / pinned（そのまま）----
    write(os.path.join(args.out, "bio_clicks.csv"), bio)
    write(os.path.join(args.out, "note_referrers.csv"), ref)
    write(os.path.join(args.out, "pinned.csv"), pinned_raw)
    pinned = [dict(zip(pinned_raw[0], r + [""] * (8 - len(r)))) for r in pinned_raw[1:] if r and r[0]]

    # ---- 転送クリック明細（＋記事タイトル・当日 PV/スキ・スキ累計）----
    det_rows = [r + [""] * (4 - len(r)) for r in det[1:] if r and r[0]]
    rows = [["id", "日付", "ホスト", "キー", "記事タイトル", "クリック", "記事PV（当日）", "記事スキ（当日）", "スキ（累計）"]]
    for r in det_rows:
        m = ARTICLE_ID.match(r[2])
        aid = m.group(1) if m else ""
        pv, like = daily.get((r[0], aid), ("", "")) if aid else ("", "")
        rows.append(["|".join(r[:3]), r[0], r[1], r[2], title_of(aid), num(r[3]), pv, like,
                     articles.get(aid, {}).get("like_total", "") if aid else ""])
    write(os.path.join(args.out, "click_detail.csv"), rows)

    # ---- x_note_posts ----
    xg = lambda r, k: r[x_idx[k]] if k in x_idx else ""  # noqa: E731
    tg = lambda r, k: r[t_idx[k]] if k in t_idx else ""  # noqa: E731
    x_note_count: dict[str, int] = {}
    rows = [["投稿日", "投稿日時", "ポストURL", "本文冒頭", "種類", "インプレッション", "いいね", "エンゲ率", "詳細表示",
             "リンククリック", "フォロー増", "noteURL", "記事ID", "バズスコア", "グレード"]]
    for r in x_rows:
        note_url = xg(r, "noteURL").strip()
        if not note_url:
            continue
        m = ARTICLE_ID.search(note_url)
        if m:
            x_note_count[m.group(1)] = x_note_count.get(m.group(1), 0) + 1
        rows.append([
            ymd(xg(r, "投稿日時")), xg(r, "投稿日時"), xg(r, "ポストURL"), xg(r, "ポスト本文").replace("\n", " ")[:60], xg(r, "ポスト種類"),
            num(xg(r, "インプレッション")), num(xg(r, "いいね")), num(xg(r, "エンゲ率")), num(xg(r, "詳細表示")), num(xg(r, "リンククリック")), num(xg(r, "フォロー増")),
            note_url, m.group(1) if m else "", xg(r, "バズスコア"), xg(r, "グレード"),
        ])
    write(os.path.join(args.out, "x_note_posts.csv"), rows)

    # ---- クリックの集計（キー別・記事別）----
    clicks_by_key: dict[tuple[str, str], int] = {}      # (ホスト, キー) → 累計
    clicks_by_key_day: dict[tuple[str, str, str], int] = {}  # (日付, ホスト, キー)
    clicks_by_article: dict[str, int] = {}
    last_click: dict[str, str] = {}
    link_count: dict[str, set] = {}
    for r in det_rows:
        c = to_int(r[3])
        clicks_by_key[(r[1], r[2])] = clicks_by_key.get((r[1], r[2]), 0) + c
        clicks_by_key_day[(r[0], r[1], r[2])] = clicks_by_key_day.get((r[0], r[1], r[2]), 0) + c
        m = ARTICLE_ID.match(r[2])
        if m:
            aid = m.group(1)
            clicks_by_article[aid] = clicks_by_article.get(aid, 0) + c
            last_click[aid] = max(last_click.get(aid, ""), r[0])
            link_count.setdefault(aid, set()).add((r[1], r[2]))

    # ---- articles（購入数・CVR・販売係数・スキ購入係数 付き）----
    # 販売係数 ＝ ビュー ÷ 購入数（何ビューで 1 本売れるか）、スキ購入係数 ＝ スキ ÷ 購入数（2026-10-12）
    purchases: dict[str, int] = {}
    title_to_id = {a["title"]: aid for aid, a in articles.items() if a.get("title")}
    for r in buy_rows:
        t = (r[col(buy_hdr, "購入")] if col(buy_hdr, "購入") is not None else "").strip()
        if not t:
            continue
        # 完全一致 → 記事題名が購入記録の題名で始まる（購入記録は「もしも空が赤かったら（後編）」のように副題を省く）
        # → 先頭 15 文字一致
        aid = (title_to_id.get(t)
               or next((i for ttl, i in title_to_id.items() if len(t) >= 8 and ttl.startswith(t)), "")
               or next((i for ttl, i in title_to_id.items() if ttl[:15] == t[:15]), ""))
        if aid:
            purchases[aid] = purchases.get(aid, 0) + 1
    rows = [["記事ID", "タイトル", "投稿日", "文字数", "ビュー（累計）", "スキ（累計）", "スキ率", "コメント", "売上",
             "転送クリック合計", "導線数", "X投稿数", "最終クリック日", "購入数", "CVR", "販売係数", "スキ購入係数", "価格"]]
    prices = {aid: to_int(a["price"]) for aid, a in articles.items() if a.get("price") != ""}
    missing = [aid for aid in articles if aid not in prices]
    if missing:  # シートに価格が無い記事だけ API（routine 環境では note.com に届かず空のまま）
        prices.update(fetch_prices(missing, os.path.join(args.out, "price_cache.json")))
    for aid, a in articles.items():
        if not a.get("date"):
            continue  # note記事日次 だけに現れた記事（note投稿一覧に無い）は除く
        views = to_int(a["view_total"])
        buys = purchases.get(aid, 0)
        likes = to_int(a["like_total"])
        rows.append([aid, a["title"], a["date"], a["chars"], a["view_total"], a["like_total"], a["like_rate"], a["comments"], a["sales"],
                     clicks_by_article.get(aid, 0), len(link_count.get(aid, ())), x_note_count.get(aid, 0), last_click.get(aid, ""),
                     buys, round(buys / views, 4) if views else "",
                     round(views / buys) if buys else "", round(likes / buys, 1) if buys else "", prices.get(aid, "")])
    rows[1:] = sorted(rows[1:], key=lambda r: (-r[9], -to_int(r[4]), r[2]))
    write(os.path.join(args.out, "articles.csv"), rows)

    # ---- funnel_posts（投稿ごと累計）----
    def pin_for(media: str, aid: str, post_key: str):
        return next((p for p in pinned if p["媒体"] == media and p["記事ID"] == aid and aid
                     and (p["投稿キー"] == post_key if p["投稿キー"] else not post_key)), None)

    def pin_text(p):
        return f"{p['開始日']}〜{p['終了日'] or ''}" if p else ""

    x_by_id = {}
    for r in x_rows:
        m = re.search(r"/status/(\d+)", xg(r, "ポストURL"))
        if m:
            x_by_id[m.group(1)] = r
    t_by_url = {tg(r, "投稿URL").rstrip("/"): r for r in t_rows}

    # 投稿の型（outputs シートの what_id。W001 ＝ 執念の物語の X 長文）を tweet ID で引く
    kind_by_tweet: dict[str, str] = {}
    for r in out_rows:
        m = re.search(r"/status/(\d+)", r[1] if len(r) > 1 else "")
        if m and len(r) > 2 and r[2].strip():
            kind_by_tweet[m.group(1)] = r[2].strip()

    # アカウントの地力：各 W001 投稿の直前 14 日に投稿した非 W001 の親ポスト（リプライでない行）の IMP の中央値。
    # 平均は 1 本のバズで桁が飛ぶので中央値、7 日では本数が足りない時期があるので 14 日
    BASE_DAYS = 14
    base_posts: list[tuple[datetime, int]] = []
    for r in x_rows:
        m = re.search(r"/status/(\d+)", xg(r, "ポストURL"))
        if not m or xg(r, "親ポストURL").strip() or kind_by_tweet.get(m.group(1)) == "W001":
            continue
        dt = parse_dt(xg(r, "投稿日時"))
        imp = to_int(xg(r, "インプレッション"))
        if dt and imp > 0:
            base_posts.append((dt, imp))

    def baseline(dt: datetime | None) -> str:
        if dt is None:
            return ""
        xs = sorted(imp for d, imp in base_posts if dt - timedelta(days=BASE_DAYS) <= d < dt)
        if not xs:
            return ""
        n = len(xs)
        return str(round((xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)))

    posts: dict[str, dict] = {}  # id → 行

    def add_post(media, body, link_row, link_pos, aid, key, clicks, src, xlc, pin, xlc_known=True):
        if media == "X":
            url, date_, text = xg(body, "ポストURL"), ymd(xg(body, "投稿日時")), xg(body, "ポスト本文")
            imp, reach = to_int(xg(body, "インプレッション")), to_int(xg(link_row, "インプレッション"))
        else:
            url, date_, text = tg(body, "投稿URL"), ymd(tg(body, "投稿日時")), tg(body, "本文")
            imp, reach = to_int(tg(body, "views")), to_int(tg(link_row, "views"))
        pid = f"{media}|{url}"
        p = posts.setdefault(pid, {"id": pid, "媒体": media, "投稿日": date_, "本体URL": url, "本文冒頭": text.replace("\n", " ")[:40],
                                   "記事ID": aid, "記事タイトル": title_of(aid), "本体IMP": imp, "リンク到達": 0, "リンク位置": link_pos,
                                   "クリック": 0, "クリックの出どころ": src, "Xリンククリック": 0, "固定期間": pin_text(pin), "キー": set(), "reach_rows": set(),
                                   "型": kind_by_tweet.get((re.search(r"/status/(\d+)", url) or [None, ""])[1], "") if media == "X" else "",
                                   "地力IMP": baseline(parse_dt(xg(body, "投稿日時"))) if media == "X" else "",
                                   "xlc_known": False})
        if xlc_known:
            p["xlc_known"] = True
        if id(link_row) not in p["reach_rows"]:
            p["reach_rows"].add(id(link_row))
            p["リンク到達"] += reach
            p["Xリンククリック"] += xlc
        p["クリック"] += clicks
        if key:
            p["キー"].add(key)
        if src == "ビーコン":
            p["クリックの出どころ"] = "ビーコン"
        if link_pos == "セルフリプ":
            p["リンク位置"] = "セルフリプ"

    def climb(row, parent_of):
        """親をたどって最上位（親の無い行）を返す。ツリー投稿では本体→続きのリプ→リンク付きリプと
        2 段以上になるので 1 段では足りない（10/9 ニューホライズンズ）。親が一覧に無ければその行を返す"""
        seen = {id(row)}
        while True:
            parent = parent_of(row)
            if parent is None or id(parent) in seen:
                return row
            seen.add(id(parent))
            row = parent

    # X: noteURL のある行（xpost / 生 note リンク）。リプライ行は親をたどって最上位を本体にする
    for r in x_rows:
        note_url = xg(r, "noteURL").strip()
        if not note_url:
            continue
        m = re.search(r"xpost\.usephys\.net/(n[0-9a-f]{10,16}(?:/[A-Za-z0-9_-]{1,32})?)", note_url)
        key = m.group(1) if m else ""
        aid = (ARTICLE_ID.search(note_url) or ARTICLE_ID.search(key or "")).group(1) if ARTICLE_ID.search(note_url) else ""
        body = climb(r, lambda row: (lambda pm: x_by_id.get(pm.group(1)) if pm else None)(
            re.search(r"/status/(\d+)", xg(row, "親ポストURL"))))
        pos = "セルフリプ" if body is not r else "本体"
        xlc_raw = xg(r, "リンククリック").strip()  # 空 ＝ X アナリティクス未取込（0 とは区別する）
        xlc = to_int(xlc_raw)
        if key:
            add_post("X", body, r, pos, aid, key, clicks_by_key.get(("xpost.usephys.net", key), 0), "ビーコン", xlc,
                     pin_for("X", aid, key.split("/", 1)[1] if "/" in key else ""))
        else:
            add_post("X", body, r, pos, aid, "", xlc, "X集計", xlc, None, xlc_known=xlc_raw != "")

    # Threads: tpost キーを持つクリック → 本文一致 → 固定ポスト履歴。リプライ行（親投稿URL あり）は親をたどって最上位を本体にする
    unknown = []
    for (host, key), c in clicks_by_key.items():
        if host != "tpost.usephys.net":
            continue
        m = ARTICLE_ID.match(key)
        aid = m.group(1) if m else ""
        post_key = key.split("/", 1)[1] if "/" in key else ""
        pin = pin_for("Threads", aid, post_key)
        link_row = find_link_row(host, key, "Threads", pin, x_rows, x_idx, t_rows, t_idx)
        if link_row is None:
            unknown.append(("Threads", host, key, aid, c, pin))
            continue
        body = climb(link_row, lambda row: t_by_url.get(tg(row, "親投稿URL").rstrip("/")))
        add_post("Threads", body, link_row, "セルフリプ" if body is not link_row else "本体",
                 aid, key, c, "ビーコン", 0, pin)
    # X の xpost キーで X投稿一覧に無いもの（テストキーなど）
    known_x_keys = {k for p in posts.values() if p["媒体"] == "X" for k in p["キー"]}
    for (host, key), c in clicks_by_key.items():
        if host == "xpost.usephys.net" and key not in known_x_keys:
            m = ARTICLE_ID.match(key)
            unknown.append(("X", host, key, m.group(1) if m else "", c, None))

    rows = [["id", "媒体", "投稿日", "本体URL", "本文冒頭", "記事ID", "記事タイトル", "本体IMP", "リンク到達", "リンク位置",
             "クリック", "クリックの出どころ", "Xリンククリック", "固定期間", "キー", "型", "地力IMP"]]
    for p in sorted(posts.values(), key=lambda p: p["投稿日"], reverse=True):
        # X集計の投稿でリンククリックが未取込（セルが空）なら、クリックは 0 ではなく空にする
        known = p["クリックの出どころ"] == "ビーコン" or p["xlc_known"]
        rows.append([p["id"], p["媒体"], p["投稿日"], p["本体URL"], p["本文冒頭"], p["記事ID"], p["記事タイトル"], p["本体IMP"], p["リンク到達"],
                     p["リンク位置"], p["クリック"] if known else "", p["クリックの出どころ"],
                     (p["Xリンククリック"] if p["xlc_known"] else "") if p["媒体"] == "X" else "", p["固定期間"], " ".join(sorted(p["キー"])), p["型"], p["地力IMP"]])
    for media, host, key, aid, c, pin in unknown:
        rows.append([f"{media}|{host}/{key}", media, "", "", "（元投稿不明）", aid, title_of(aid), "", "", "", c, "ビーコン", "", pin_text(pin), key, "", ""])
    write(os.path.join(args.out, "funnel_posts.csv"), rows)

    # ---- funnel_weekly（月曜始まり）----
    def weekly_sum(rows_, date_at, value_at):
        out: dict[date, int] = {}
        for r in rows_:
            d = ymd(date_at(r))
            try:
                day = date.fromisoformat(d)
            except ValueError:
                continue
            if day < FUNNEL_START:
                continue
            mon = monday(day)
            out[mon] = out.get(mon, 0) + value_at(r)
        return out

    x_imp = weekly_sum(x_rows, lambda r: xg(r, "投稿日時"), lambda r: to_int(xg(r, "インプレッション")))
    x_prof = weekly_sum(x_rows, lambda r: xg(r, "投稿日時"), lambda r: to_int(xg(r, "プロフアクセス")))
    t_views = weekly_sum([r for r in dr_rows if col(dr_hdr, "threads views") is not None and r[col(dr_hdr, "threads views")].strip()],
                         lambda r: r[0], lambda r: to_int(r[col(dr_hdr, "threads views")]))
    has_t_views = col(dr_hdr, "threads views") is not None
    bio_hdr, bio_rows = table(bio)
    bio_x = weekly_sum(bio_rows, lambda r: r[0], lambda r: to_int(r[col(bio_hdr, "X bio")]))
    bio_t = weekly_sum(bio_rows, lambda r: r[0], lambda r: to_int(r[col(bio_hdr, "Threads bio")]))
    ref_hdr, ref_rows = table(ref)
    ref_x = weekly_sum(ref_rows, lambda r: r[0], lambda r: to_int(r[col(ref_hdr, "X bio")])) if col(ref_hdr, "X bio") is not None else {}
    ref_t = weekly_sum(ref_rows, lambda r: r[0], lambda r: to_int(r[col(ref_hdr, "Threads bio")])) if col(ref_hdr, "Threads bio") is not None else {}

    def pinned_clicks(media: str):
        host = "xpost.usephys.net" if media == "X" else "tpost.usephys.net"
        out: dict[date, int] = {}
        for (d, h, key), c in clicks_by_key_day.items():
            if h != host:
                continue
            aid = (ARTICLE_ID.match(key) or [None])[0] if ARTICLE_ID.match(key) else ""
            post_key = key.split("/", 1)[1] if "/" in key else ""
            p = pin_for(media, aid, post_key)
            if p and p["開始日"] <= d and (not p["終了日"] or d <= p["終了日"]) and date.fromisoformat(d) >= FUNNEL_START:
                mon = monday(date.fromisoformat(d))
                out[mon] = out.get(mon, 0) + c
        return out

    pin_x, pin_t = pinned_clicks("X"), pinned_clicks("Threads")

    def pinned_reach(media: str):
        """固定ポストの IMP/views の週増分（週の最終スナップショット − 前週以前の最終スナップショット）。基準が無い週は None"""
        snaps: dict[str, list[tuple[str, int]]] = {}
        for r in snap_rows:
            if r[1] == media and r[0] and r[2] and ymd(r[0]) >= FUNNEL_START.isoformat():
                snaps.setdefault(r[2], []).append((r[0], to_int(r[3])))
        out: dict[date, int | None] = {}
        for pid, lst in snaps.items():
            lst.sort()
            by_week: dict[date, int] = {}
            for d, v in lst:
                by_week[monday(date.fromisoformat(d))] = v  # 週内の最後の値が残る
            prev = None
            for mon in sorted(by_week):
                if prev is not None:
                    out[mon] = (out.get(mon) or 0) + (by_week[mon] - prev)
                else:
                    out.setdefault(mon, None)
                prev = by_week[mon]
        return out

    reach_x, reach_t = pinned_reach("X"), pinned_reach("Threads")

    rows = [["id", "週", "週ラベル", "経路", "インプ", "リンク到達", "クリック", "note到達", "集計中", "備考"]]
    mon = WEEK_START
    while mon <= today:
        sun = mon + timedelta(days=6)
        live = sun >= today
        note_warn = "到達にスキャナ混入（10/8 まで）" if mon.isoformat() <= SCANNER_UNTIL and FUNNEL_START.isoformat() <= SCANNER_UNTIL else ""
        label = week_label(mon) if mon >= FUNNEL_START else week_label(mon).replace(f"{mon.month}/{mon.day}", f"{FUNNEL_START.month}/{FUNNEL_START.day}", 1)
        g = lambda d, k: d.get(k, 0)  # noqa: E731
        rx = reach_x.get(mon, None)
        rt = reach_t.get(mon, None)
        for route, imp, reach, clicks, arrive, note in [
            ("X bio", g(x_imp, mon), g(x_prof, mon), g(bio_x, mon), g(ref_x, mon), note_warn),
            ("X 固定", g(x_prof, mon), "" if rx is None else rx, g(pin_x, mon), "", "固定の到達は投稿と分けられない" + ("；IMP 増分は前週の記録待ち" if rx is None else "")),
            ("Threads bio", g(t_views, mon) if has_t_views else "", "", g(bio_t, mon), g(ref_t, mon), ("プロフ閲覧は API に無い" + ("；" + note_warn if note_warn else ""))),
            ("Threads 固定", g(t_views, mon) if has_t_views else "", "" if rt is None else rt, g(pin_t, mon), "", "固定の到達は投稿と分けられない" + ("；views 増分は前週の記録待ち" if rt is None else "")),
        ]:
            rows.append([f"{mon.isoformat()}|{route}", mon.isoformat(), label, route, imp, reach, clicks, arrive, "true" if live else "false", note])
        mon += timedelta(days=7)
    write(os.path.join(args.out, "funnel_weekly.csv"), rows)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(os.path.join(args.out, "exported_at.txt"), "w", encoding="utf-8") as f:
        f.write(stamp + "\n")
    print(f"✅ {args.out} に 8 ファイルを書き出し（{stamp}）: bio {len(bio)-1} 行 / 明細 {len(det_rows)} 行 / 記事 {len(articles)} 件 / "
          f"投稿ファネル {len(posts)}＋不明 {len(unknown)} 件 / 週次 {len(rows)-1} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
