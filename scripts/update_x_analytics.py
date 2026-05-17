#!/usr/bin/env python3
"""
X アナリティクス CSV を Drive から取得し、X投稿一覧シートを更新するスクリプト。
LLM・エージェント不要で直接 API を呼び出す。
"""

import base64
import csv
import io
import json
import os
import re
import sys
import time
import requests
import rsa

# ── 設定 ───────────────────────────────────────────────
FOLDER_ID     = "1J45co5hN74gzxNateNRyeDtswZu0lMr3"  # Xanalytics/tmp
SPREADSHEET_ID = "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
SHEET_NAME    = "X投稿一覧"
DRIVE_UUID    = "960819bd-d145-4f2b-ad5c-e521cc86112e"

# ── Drive MCP プロキシ設定 ────────────────────────────────
def get_drive_config():
    session_id = os.environ["CLAUDE_CODE_REMOTE_SESSION_ID"]
    config_path = f"/tmp/mcp-config-{session_id}.json"
    config = json.load(open(config_path))
    drive = config["mcpServers"][DRIVE_UUID]
    ingress_token = open("/home/claude/.claude/remote/.session_ingress_token").read().strip()
    headers = {
        **drive["headers"],
        "Authorization": f"Bearer {ingress_token}",
        "Content-Type": "application/json",
    }
    return drive["url"], headers


def drive_call(url, headers, tool_name, arguments):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool_name, "arguments": arguments}}
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    for line in resp.text.splitlines():
        if line.startswith("data:"):
            data = json.loads(line[5:].strip())
            result = data["result"]
            if result.get("isError"):
                raise RuntimeError(result["content"][0]["text"])
            # structuredContent があればそちらを優先
            if "structuredContent" in result:
                return result["structuredContent"]
            # content[0].text をパース
            if result.get("content") and result["content"][0].get("text"):
                text = result["content"][0]["text"]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw": text}
            return result
    raise RuntimeError(f"Unexpected response: {resp.text[:200]}")


# ── Google Sheets API 認証（サービスアカウント JWT） ───────────────
def get_sheets_token():
    import subprocess, tempfile
    key_json = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"])
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    claim = {
        "iss": key_json["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud": "https://oauth2.googleapis.com/token",
        "exp": now + 3600,
        "iat": now,
    }
    def b64url(data):
        return base64.urlsafe_b64encode(json.dumps(data, separators=(",",":")).encode()).rstrip(b"=").decode()
    signing_input = f"{b64url(header)}.{b64url(claim)}"

    # openssl で RS256 署名
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False, mode="w") as kf:
        kf.write(key_json["private_key"])
        key_path = kf.name
    with tempfile.NamedTemporaryFile(delete=False) as sf:
        sf.write(signing_input.encode())
        sig_input_path = sf.name

    result = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", key_path, sig_input_path],
        capture_output=True
    )
    os.unlink(key_path)
    os.unlink(sig_input_path)
    if result.returncode != 0:
        raise RuntimeError(f"openssl sign failed: {result.stderr.decode()}")

    signature = base64.urlsafe_b64encode(result.stdout).rstrip(b"=").decode()
    jwt_token = f"{signing_input}.{signature}"

    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def sheets_get(token, range_):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{range_}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("values", [])


def sheets_batch_update(token, data):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values:batchUpdate"
    payload = {"valueInputOption": "USER_ENTERED", "data": data}
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}",
                                       "Content-Type": "application/json"},
                         json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── メイン処理 ──────────────────────────────────────────
def main():
    t0 = time.time()

    # STEP 1: Drive CSV 検索
    print("STEP 1: Drive CSV を検索中...")
    drive_url, drive_headers = get_drive_config()
    result = drive_call(drive_url, drive_headers, "search_files",
                        {"query": f"parentId = '{FOLDER_ID}'",
                         "excludeContentSnippets": True})
    files = result.get("files", [])

    if not files:
        print("ERROR: CSV ファイルが見つかりません", file=sys.stderr)
        sys.exit(1)

    # 最新ファイルを選択
    latest = sorted(files, key=lambda f: f.get("modifiedTime", ""), reverse=True)[0]
    file_id = latest["id"]
    file_title = latest.get("title", file_id)
    print(f"  対象ファイル: {file_title}")

    # STEP 2: CSV ダウンロード
    print("STEP 2: CSV をダウンロード中...")
    dl_result = drive_call(drive_url, drive_headers, "download_file_content",
                           {"fileId": file_id})
    b64_content = dl_result.get("content")
    if not b64_content:
        print(f"ERROR: CSV コンテンツを取得できません。レスポンス: {str(dl_result)[:200]}", file=sys.stderr)
        sys.exit(1)
    csv_text = base64.b64decode(b64_content).decode("utf-8")

    # STEP 3: CSV パース
    print("STEP 3: CSV をパース中...")
    csv_map = {}
    reader = csv.reader(io.StringIO(csv_text))
    next(reader)  # ヘッダースキップ
    for row in reader:
        if len(row) <= 14:
            continue
        m = re.search(r"/status/(\d+)", row[3])
        if not m:
            continue
        try:
            csv_map[m.group(1)] = {
                "detail_expands": int(row[13] or 0),
                "url_clicks":     int(row[14] or 0),
                "new_follows":    int(row[9]  or 0),
            }
        except (ValueError, IndexError):
            continue
    print(f"  CSV 投稿数: {len(csv_map)} 件")

    # STEP 4: Sheets B列取得
    print("STEP 4: Sheets の投稿URL一覧を取得中...")
    token = get_sheets_token()
    rows = sheets_get(token, f"{SHEET_NAME}!B:B")

    # STEP 5: マッチング
    print("STEP 5: status ID でマッチング中...")
    update_data = []
    for i, row in enumerate(rows[1:], start=2):  # 1行目はヘッダー
        url = row[0] if row else ""
        m = re.search(r"/status/(\d+)", url)
        if m and m.group(1) in csv_map:
            v = csv_map[m.group(1)]
            update_data.append({
                "range": f"{SHEET_NAME}!AA{i}:AC{i}",
                "values": [[v["detail_expands"], v["url_clicks"], v["new_follows"]]],
            })
    print(f"  マッチ件数: {len(update_data)} 件")

    # STEP 6: バッチ更新
    if update_data:
        print("STEP 6: Sheets を一括更新中...")
        sheets_batch_update(token, update_data)
    else:
        print("STEP 6: 更新対象なし")

    elapsed = time.time() - t0
    print(f"""
✅ X投稿一覧 アナリティクス更新完了
   CSVファイル  : {file_title}
   マッチ件数   : {len(update_data)} 件 / CSV総投稿数: {len(csv_map)} 件
   更新列       : 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）
   実行時間     : {elapsed:.1f}秒
""")


if __name__ == "__main__":
    main()
