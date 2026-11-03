#!/usr/bin/env python3
"""毎朝の宇宙ダイジェスト：新着の収集（RSS / Atom / arXiv API）

空間探査・宇宙物理・宇宙開発・素粒子物理の新着を scripts/space_digest_sources.json の
ソースから集め、既読（logs/space_digest_state.json）と時間窓で絞って候補ファイルを書く。
要約・選別は /space-digest スキル（claude -p）が行う。X API も Claude API も呼ばない。

Usage:
  python3 scripts/space_digest_fetch.py [--dry-run] [--since-hours N] [--out PATH] [--date YYYY-MM-DD]

終了コード: 0 = 候補あり / 20 = 候補なし / 1 = 全ソース取得失敗
"""
import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_PATH = os.path.join(ROOT, "scripts", "space_digest_sources.json")
STATE_PATH = os.path.join(ROOT, "logs", "space_digest_state.json")
OUT_DIR = os.path.join(ROOT, "logs", "space_digest")
STATE_KEEP_DAYS = 30
JST = timezone(timedelta(hours=9))
KIND_LABEL = {"press": "プレスリリース", "news": "ニュース・配信", "paper": "論文"}


def log(msg):
    print(f"[{datetime.now(JST):%Y-%m-%d %H:%M:%S JST}] {msg}", flush=True)


# ---------- 状態ファイル（x_imp_alert.py と同じ形） ----------

def load_state():
    if not os.path.exists(STATE_PATH):
        return {"seen": {}}
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            st = json.load(f)
        st.setdefault("seen", {})
        return st
    except Exception as e:  # noqa: BLE001
        log(f"警告: 状態ファイルを読めないので初期化します: {e}")
        return {"seen": {}}


def prune_state(st, now):
    cutoff = (now - timedelta(days=STATE_KEEP_DAYS)).isoformat()
    st["seen"] = {k: v for k, v in st["seen"].items() if v.get("seen_at", "") >= cutoff}


def save_state(st):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


# ---------- 文字列ユーティリティ ----------

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(s, limit):
    if not s:
        return ""
    s = html.unescape(TAG_RE.sub(" ", s))
    s = WS_RE.sub(" ", s).strip()
    return s[:limit] + ("…" if len(s) > limit else "")


def norm_link(u):
    u = (u or "").strip()
    u = re.sub(r"[?&](utm_[a-z]+|af|ref)=[^&]*", "", u)
    u = re.sub(r"\?$", "", u)
    return u.rstrip("/")


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    for fn in (lambda x: parsedate_to_datetime(x),
               lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))):
        try:
            d = fn(s)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d
        except Exception:  # noqa: BLE001
            continue
    return None


def local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def kw_matcher(strong, weak):
    """text → (score, 一致語リスト)。強キーワード 3 点、弱キーワード 1 点。score 0 なら不一致"""
    def compile_(kw):
        if kw.isascii():
            return re.compile(r"(?<![A-Za-z0-9])" + re.escape(kw) + r"(?![A-Za-z0-9])", re.I)
        return re.compile(re.escape(kw))
    pats = [(kw, compile_(kw), 3) for kw in strong] + [(kw, compile_(kw), 1) for kw in weak]

    def match(text):
        score, hits = 0, []
        for kw, p, w in pats:
            if p.search(text):
                score += w
                hits.append(kw)
        return score, hits
    return match


# ---------- フィード解析（名前空間を剥がして item / entry を読む） ----------

def parse_feed(xml_bytes):
    root = parse_xml(xml_bytes)
    items = []
    for el in root.iter():
        if not isinstance(el.tag, str) or local(el.tag) not in ("item", "entry"):
            continue
        title = link = date = summary = ""
        for c in el:
            if not isinstance(c.tag, str):
                continue
            t = local(c.tag)
            txt = (c.text or "").strip()
            if t == "title" and not title:
                title = txt
            elif t == "link":
                href = c.get("href")
                if href:
                    rel = c.get("rel", "alternate")
                    if rel == "alternate" and not link:
                        link = href
                elif txt and not link:
                    link = txt
            elif t in ("pubDate", "date", "published", "updated", "coverDate") and not date:
                date = txt
            elif t in ("description", "summary") and not summary:
                summary = txt
            elif t in ("encoded", "content") and not summary:
                summary = txt
        if not link:
            link = el.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", "") or ""
            if not link:
                for c in el:
                    if local(c.tag) == "id" and (c.text or "").startswith("http"):
                        link = c.text.strip()
        items.append({"title": clean_text(title, 300), "link": norm_link(link),
                      "date": parse_date(date), "summary": summary})
    return items


def fetch_url(url, ua, timeout=40):
    """curl で取得（--max-time で全体の所要時間を打ち切れる。requests の timeout は無通信時間しか見ない）"""
    import subprocess
    r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", ua,
                        "-H", "Accept: application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
                        "-w", "\n__HTTP__%{http_code}", url],
                       capture_output=True, timeout=timeout + 10)
    body, _, code = r.stdout.rpartition(b"\n__HTTP__")
    code = code.decode(errors="ignore").strip()
    if r.returncode != 0:
        raise RuntimeError(f"curl rc={r.returncode}（timeout {timeout}s）")
    if code != "200":
        raise RuntimeError(f"HTTP {code}")
    return body


def parse_xml(xml_bytes):
    # 属性の間の空白抜け（science.nasa.gov: xmlns:apod="…"xmlns:media=）をルート要素の範囲で直す
    head, tail = xml_bytes[:3000], xml_bytes[3000:]
    head = re.sub(rb'"(xmlns[:=])', rb'" \1', head)
    xml_bytes = head + tail
    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError:
        from lxml import etree  # 壊れた XML（JPL など）は lxml の recover で読む
        root = etree.fromstring(xml_bytes, parser=etree.XMLParser(recover=True, huge_tree=True))
        if root is None:
            raise
        return root


# ---------- arXiv ----------

ARXIV_API = "http://export.arxiv.org/api/query"


def fetch_arxiv(cfg, ua, since, match, limit_chars):
    cats = "+OR+".join(f"cat:{c}" for c in cfg["categories"])
    url = (f"{ARXIV_API}?search_query={cats}&sortBy=submittedDate&sortOrder=descending"
           f"&max_results={cfg.get('max_results', 300)}")
    data = fetch_url(url, ua, timeout=60)
    root = ET.fromstring(data)
    out, total, in_window = [], 0, 0
    for el in root.iter():
        if local(el.tag) != "entry":
            continue
        total += 1
        d = {"title": "", "link": "", "summary": "", "date": None, "cats": []}
        for c in el:
            t = local(c.tag)
            if t == "id":
                d["link"] = (c.text or "").strip()
            elif t == "title":
                d["title"] = clean_text(c.text, 300)
            elif t == "summary":
                d["summary"] = c.text or ""
            elif t == "published":
                d["date"] = parse_date(c.text)
            elif t == "primary_category":
                d["cats"].insert(0, c.get("term", ""))
            elif t == "category":
                d["cats"].append(c.get("term", ""))
        if not d["date"] or d["date"] < since:
            continue
        in_window += 1
        score, hits = match(d["title"] + " " + d["summary"])
        if not score:
            continue
        aid = re.sub(r"v\d+$", "", d["link"].rsplit("/", 1)[-1])
        out.append({"key": f"arxiv:{aid}", "title": d["title"], "link": f"https://arxiv.org/abs/{aid}",
                    "date": d["date"], "summary": clean_text(d["summary"], limit_chars),
                    "source": f"arXiv {d['cats'][0] if d['cats'] else ''}".strip(), "kind": "paper", "lang": "en",
                    "score": score, "hit": "、".join(hits[:6])})
    return out, total, in_window


# ---------- メイン ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="状態ファイルを更新しない")
    ap.add_argument("--since-hours", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--date", default=None, help="候補ファイル名の日付（既定: 今日 JST）")
    args = ap.parse_args()

    with open(SOURCES_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    now = datetime.now(timezone.utc)
    since_hours = args.since_hours or cfg.get("since_hours", 48)
    since = now - timedelta(hours=since_hours)
    ua = cfg.get("user_agent", "xClaude-space-digest")
    limit_chars = cfg.get("summary_chars", 600)
    per_max = cfg.get("per_source_max", 10)
    match = kw_matcher(cfg.get("keywords_strong", []), cfg.get("keywords", []))
    excl = [e.lower() for e in cfg.get("exclude_titles", [])]
    seen_titles = set()

    st = load_state()
    prune_state(st, now)
    seen = st["seen"]

    cands, stats, failures = [], [], 0
    n_sources = len(cfg["sources"]) + 1

    # 取得は並列（遅いサーバーがあるため）。解析・絞り込みは順に行う
    def _get(src):
        try:
            return src, parse_feed(fetch_url(src["url"], ua)), None
        except Exception as e:  # noqa: BLE001
            return src, None, f"{type(e).__name__}: {str(e)[:120]}"

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as ex:
        fetched = list(ex.map(_get, cfg["sources"]))

    for src, items, err in fetched:
        if err:
            failures += 1
            stats.append(f"{src['name']}: 取得失敗 {err}")
            log(stats[-1])
            continue
        kept, n_win, n_undated, n_seen, n_kw, n_ex = [], 0, 0, 0, 0, 0
        for it in items:
            if not it["date"]:
                n_undated += 1
                continue
            if it["date"] < since:
                continue
            n_win += 1
            key = it["link"]
            if not key or key in seen:
                n_seen += 1
                continue
            text = it["title"] + " " + clean_text(it["summary"], 2000)
            tkey = re.sub(r"[^\w]", "", it["title"].lower())
            if any(e in it["title"].lower() for e in excl) or (tkey and tkey in seen_titles):
                n_ex += 1
                continue
            score, hits = match(text)
            if src.get("keyword_filter") and not score:
                n_kw += 1
                continue
            seen_titles.add(tkey)
            kept.append({"key": key, "title": it["title"], "link": it["link"], "date": it["date"],
                         "summary": clean_text(it["summary"], limit_chars), "source": src["name"],
                         "kind": src["kind"], "lang": src["lang"], "score": score,
                         "hit": "、".join(hits[:6]) if src.get("keyword_filter") else None})
        kept.sort(key=lambda d: d["date"], reverse=True)
        kept = kept[: src.get("max", per_max)]
        cands.extend(kept)
        stats.append(f"{src['name']}: 全{len(items)} 窓内{n_win} 既読{n_seen} 除外語{n_ex} KW落ち{n_kw} 日付無し{n_undated} → {len(kept)}")
        log(stats[-1])

    try:
        ax, ax_total, ax_win = fetch_arxiv(cfg["arxiv"], ua, since, match, limit_chars)
        ax = [a for a in ax if a["key"] not in seen]
        n_hit = len(ax)
        ax.sort(key=lambda d: (-d["score"], -d["date"].timestamp()))  # 強キーワードの多い順
        ax = ax[: cfg["arxiv"].get("max_keep", 25)]
        cands.extend(ax)
        stats.append(f"arXiv: 全{ax_total} 窓内{ax_win} KW一致（未読）{n_hit} → 上位 {len(ax)}")
    except Exception as e:  # noqa: BLE001
        failures += 1
        stats.append(f"arXiv: 取得失敗 {type(e).__name__}: {str(e)[:120]}")
    log(stats[-1])
    if failures >= n_sources:
        log("全ソースの取得に失敗")
        return 1

    # 種別順（press → paper → news）で全体上限。news から削られる
    order = {"press": 0, "paper": 1, "news": 2}
    cands.sort(key=lambda d: (order[d["kind"]], -(d["score"] if d["kind"] == "paper" else 0), -d["date"].timestamp()))
    dropped = max(0, len(cands) - cfg.get("max_total", 60))
    cands = cands[: cfg.get("max_total", 60)]

    date_str = args.date or f"{datetime.now(JST):%Y-%m-%d}"
    out_path = args.out or os.path.join(OUT_DIR, f"{date_str}_candidates.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    lines = [f"# 宇宙ダイジェスト 候補 {date_str}（取得 {datetime.now(JST):%Y-%m-%d %H:%M JST}、直近 {since_hours} 時間、未読のみ）", ""]
    counts = {k: sum(1 for c in cands if c["kind"] == k) for k in KIND_LABEL}
    lines.append(f"候補 {len(cands)} 件（プレスリリース {counts['press']}・ニュース {counts['news']}・論文 {counts['paper']}）"
                 + (f"。上限超過で {dropped} 件省略" if dropped else "")
                 + (f"。取得失敗 {failures} ソース" if failures else ""))
    lines.append("")
    if not cands:
        lines.append("NO_CANDIDATES")
    for kind in ("press", "news", "paper"):
        group = [c for c in cands if c["kind"] == kind]
        if not group:
            continue
        lines.append(f"## {KIND_LABEL[kind]}（{len(group)} 件）")
        lines.append("")
        for i, c in enumerate(group, 1):
            lines.append(f"### {kind}-{i}: {c['title']}")
            lines.append(f"- 出典: {c['source']}（{c['lang']}） {c['date'].astimezone(JST):%Y-%m-%d %H:%M}")
            lines.append(f"- URL: {c['link']}")
            if c.get("hit"):
                lines.append(f"- 一致キーワード: {c['hit']}（スコア {c['score']}）")
            lines.append(f"- 要旨: {c['summary'] or '（要旨なし）'}")
            lines.append("")
    lines.append("## 取得状況")
    lines.extend(f"- {s}" for s in stats)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"候補 {len(cands)} 件 → {out_path}")

    if not args.dry_run:
        ts = now.isoformat()
        for c in cands:
            seen[c["key"]] = {"seen_at": ts, "title": c["title"][:80]}
        save_state(st)
    return 0 if cands else 20


if __name__ == "__main__":
    sys.exit(main())
