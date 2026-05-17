#!/usr/bin/env python3
"""
X アナリティクス CSV を Drive から取得してパースし、
status_id → {detail_expands, url_clicks, new_follows} の JSON を出力する。
Sheets 更新はエージェント（Claude）が mcp-gsheets で行う。
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

# ── 設定 ───────────────────────────────────────────────
FOLDER_ID  = "1J45co5hN74gzxNateNRyeDtswZu0lMr3"  # Xanalytics/tmp
DRIVE_UUID = "960819bd-d145-4f2b-ad5c-e521cc86112e"
OUTPUT_PATH = "/tmp/x_analytics_map.json"

# ── Drive MCP プロキシ ────────────────────────────────
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
            if "structuredContent" in result:
                return result["structuredContent"]
            if result.get("content") and result["content"][0].get("text"):
                try:
                    return json.loads(result["content"][0]["text"])
                except json.JSONDecodeError:
                    return {"raw": result["content"][0]["text"]}
            return result
    raise RuntimeError(f"Unexpected response: {resp.text[:200]}")


# ── メイン処理 ──────────────────────────────────────────
def main():
    t0 = time.time()

    # STEP 1: Drive CSV 検索
    print("STEP 1: Drive CSV を検索中...", file=sys.stderr)
    drive_url, drive_headers = get_drive_config()
    result = drive_call(drive_url, drive_headers, "search_files",
                        {"query": f"parentId = '{FOLDER_ID}'",
                         "excludeContentSnippets": True})
    files = result.get("files", [])
    if not files:
        print("ERROR: CSV ファイルが見つかりません", file=sys.stderr)
        sys.exit(1)

    latest = sorted(files, key=lambda f: f.get("modifiedTime", ""), reverse=True)[0]
    file_id    = latest["id"]
    file_title = latest.get("title", file_id)
    print(f"  対象ファイル: {file_title}", file=sys.stderr)

    # STEP 2: CSV ダウンロード
    print("STEP 2: CSV をダウンロード中...", file=sys.stderr)
    dl_result = drive_call(drive_url, drive_headers, "download_file_content",
                           {"fileId": file_id})
    b64_content = dl_result.get("content")
    if not b64_content:
        print(f"ERROR: CSV コンテンツを取得できません: {str(dl_result)[:200]}", file=sys.stderr)
        sys.exit(1)
    csv_text = base64.b64decode(b64_content).decode("utf-8")

    # STEP 3: CSV パース
    print("STEP 3: CSV をパース中...", file=sys.stderr)
    csv_map = {}
    reader = csv.reader(io.StringIO(csv_text))
    next(reader)
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

    elapsed = time.time() - t0
    print(f"  CSV 投稿数: {len(csv_map)} 件（{elapsed:.1f}秒）", file=sys.stderr)

    # 結果を JSON ファイルに保存 & stdout に出力
    output = {"file": file_title, "csv_map": csv_map}
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, ensure_ascii=False)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
