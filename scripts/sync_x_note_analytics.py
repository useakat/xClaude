#!/usr/bin/env python3
"""
X→note 導線分析シート（Xnote導線記録）を再生成する。

データソース:
- outputs (SS2)        : 投稿記録（A=日時, B=URL, C=what_id, F=note_url）
- X投稿一覧 (SS3)        : X 指標（B=ポストURL, C=本文, K=IMP, AB=リンククリック）
- note投稿一覧 (SS3)     : note 指標（B=記事URL, C=タイトル, H=ビュー, I=スキ）
- note購入記録 (SS3)     : 購入生データ（E=記事タイトル, F=価格）

書き込み先:
- Xnote導線記録 (SS3) : A〜O 列を全件上書き

サービスアカウント JWT 認証で Sheets API を直接呼ぶ。LLM コンテキストを通さない。
"""

import base64
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests

SS2 = "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"  # outputs
SS3 = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"  # 発信記録

SCOPES = "https://www.googleapis.com/auth/spreadsheets"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SA_FILE = Path(__file__).parent.parent / "gcp" / "charming-well-464402-u4-2cfb7bddf343.json"


def b64u(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def get_access_token(key_data: dict) -> str:
    now = int(time.time())
    header = b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = b64u(json.dumps({
        "iss": key_data["client_email"],
        "scope": SCOPES,
        "aud": TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
    }).encode())
    msg = header + b"." + payload
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(key_data["private_key"])
        tmpkey = f.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", tmpkey],
            input=msg, capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"openssl error: {result.stderr.decode()}")
        sig = b64u(result.stdout)
    finally:
        os.unlink(tmpkey)
    jwt_token = (msg + b"." + sig).decode()
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def sheets_get(token: str, ss_id: str, rng: str):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{ss_id}/values/{rng}"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    return r.json().get("values", [])


def sheets_update(token: str, ss_id: str, rng: str, values: list):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{ss_id}/values/{rng}"
        f"?valueInputOption=USER_ENTERED"
    )
    r = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"values": values},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def sheets_clear(token: str, ss_id: str, rng: str):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{ss_id}/values/{rng}:clear"
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()


def tweet_id(url: str) -> str:
    """ポストURLから tweet ID（status/以降の数字）を抽出"""
    if not url:
        return ""
    m = re.search(r"status/(\d+)", url)
    return m.group(1) if m else ""


def parse_int(s) -> int:
    if not s:
        return 0
    try:
        return int(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return 0


def load_key():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if raw:
        return json.loads(raw)
    if SA_FILE.exists():
        return json.loads(SA_FILE.read_text())
    print(f"ERROR: service account key not found ({SA_FILE} or GOOGLE_SERVICE_ACCOUNT_KEY)", file=sys.stderr)
    sys.exit(1)


def main():
    print("STEP 1: 認証...", file=sys.stderr)
    token = get_access_token(load_key())

    # 1. outputs から W001 抽出
    print("STEP 2: outputs (W001) 取得...", file=sys.stderr)
    outputs = sheets_get(token, SS2, "outputs!A:F")
    if not outputs:
        print("outputs が空です", file=sys.stderr)
        sys.exit(0)
    header_o = outputs[0]
    w001_rows = []
    for r in outputs[1:]:
        if len(r) < 3 or r[2] != "W001":
            continue
        dt = r[0] if len(r) > 0 else ""
        url = r[1] if len(r) > 1 else ""
        note_url = r[5] if len(r) > 5 else ""
        w001_rows.append({"dt": dt, "url": url, "note_url": note_url, "tid": tweet_id(url)})
    print(f"  W001 件数: {len(w001_rows)}", file=sys.stderr)

    # 2. X投稿一覧 取得（A:R + AA:AC を別々に取って結合）
    print("STEP 3: X投稿一覧 取得...", file=sys.stderr)
    x_basic = sheets_get(token, SS3, "X投稿一覧!A:R")
    x_link = sheets_get(token, SS3, "X投稿一覧!AA:AC")  # AA=詳細, AB=リンククリック, AC=フォロー増
    x_by_tid = {}
    for i, row in enumerate(x_basic[1:], start=1):  # skip header
        if len(row) < 2:
            continue
        tid = tweet_id(row[1])
        if not tid:
            continue
        link_click = ""
        if i < len(x_link):
            ab = x_link[i] if i < len(x_link) else []
            link_click = ab[1] if len(ab) > 1 else ""
        x_by_tid[tid] = {
            "body": row[2] if len(row) > 2 else "",
            "imp": parse_int(row[10] if len(row) > 10 else 0),  # K = index 10
            "link_click": parse_int(link_click),
        }
    print(f"  X 投稿数: {len(x_by_tid)}", file=sys.stderr)

    # 3. note投稿一覧 取得
    print("STEP 4: note投稿一覧 取得...", file=sys.stderr)
    note_list = sheets_get(token, SS3, "note投稿一覧!A:J")
    note_by_url = {}
    note_by_title = {}
    for row in note_list[1:]:
        if len(row) < 3:
            continue
        url = row[1]
        title = row[2]
        view = parse_int(row[7] if len(row) > 7 else 0)
        like = parse_int(row[8] if len(row) > 8 else 0)
        note_by_url[url] = {"title": title, "view": view, "like": like}
        note_by_title[title] = {"url": url, "view": view, "like": like}
    print(f"  note 記事数: {len(note_by_url)}", file=sys.stderr)

    # 4. note購入記録 を記事タイトル別に集計
    print("STEP 5: note購入記録 集計...", file=sys.stderr)
    purchases = sheets_get(token, SS3, "note購入記録!A:G")
    sales_by_title = defaultdict(lambda: {"count": 0, "revenue": 0, "prices": []})
    for row in purchases[1:]:
        if len(row) < 6:
            continue
        title = row[4]  # E = 購入(記事名)
        price = parse_int(row[5])  # F = 価格
        if not title:
            continue
        sales_by_title[title]["count"] += 1
        sales_by_title[title]["revenue"] += price
        if price > 0:
            sales_by_title[title]["prices"].append(price)
    print(f"  購入のある記事数: {len(sales_by_title)}", file=sys.stderr)

    # 5. Xnote導線記録 行を構築
    print("STEP 6: 集計行構築...", file=sys.stderr)
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for w in w001_rows:
        body = ""
        imp = 0
        link_click = 0
        x = x_by_tid.get(w["tid"])
        if x:
            body = x["body"][:20] if x["body"] else ""
            imp = x["imp"]
            link_click = x["link_click"]
        ctr = round(link_click / imp, 4) if imp > 0 else ""

        note_url = w["note_url"]
        note_title = ""
        note_view = 0
        note_like = 0
        if note_url and note_url in note_by_url:
            n = note_by_url[note_url]
            note_title = n["title"]
            note_view = n["view"]
            note_like = n["like"]

        sales = sales_by_title.get(note_title, {"count": 0, "revenue": 0, "prices": []})
        purchase_count = sales["count"]
        revenue = sales["revenue"]
        # 価格 = 売上 ÷ 購入数（実勢平均）。購入なしのときは空
        price = round(revenue / purchase_count) if purchase_count > 0 else ""
        cvr = round(purchase_count / link_click, 4) if link_click > 0 else ""

        rows.append([
            w["dt"],          # A 投稿日
            w["url"],         # B W001 ポストURL
            body,             # C テーマ冒頭20字
            note_url,         # D note 記事URL
            note_title,       # E note 記事タイトル
            price,            # F note 価格 (実勢平均)
            imp,              # G X IMP
            link_click,       # H X リンククリック
            ctr,              # I リンクCTR
            note_view,        # J note ビュー
            note_like,        # K note スキ
            purchase_count,   # L note 購入数
            revenue,          # M note 売上 (実勢)
            cvr,              # N 購入CVR
            today,            # O 計測日
        ])

    # 6. Xnote導線記録 を全件上書き（ヘッダー以降）
    print("STEP 7: Xnote導線記録 書き込み...", file=sys.stderr)
    sheets_clear(token, SS3, "Xnote導線記録!A2:O1000")
    if rows:
        sheets_update(token, SS3, f"Xnote導線記録!A2:O{1 + len(rows)}", rows)

    # サマリー
    total_imp = sum(r[6] for r in rows if isinstance(r[6], int))
    total_click = sum(r[7] for r in rows if isinstance(r[7], int))
    total_purchases = sum(r[11] for r in rows if isinstance(r[11], int))
    total_revenue = sum(r[12] for r in rows if isinstance(r[12], int))
    avg_ctr = (total_click / total_imp) if total_imp else 0
    avg_cvr = (total_purchases / total_click) if total_click else 0

    print()
    print(f"✅ Xnote導線記録 更新完了 ({len(rows)}件)")
    print(f"   平均CTR: {avg_ctr*100:.2f}%  平均CVR: {avg_cvr*100:.2f}%  累計売上: ¥{total_revenue:,}")


if __name__ == "__main__":
    main()
