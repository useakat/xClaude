#!/usr/bin/env python3
"""
Google Drive ファイルダウンロード（リモートセッション専用）
Anthropic MCP プロキシ経由で Google Drive MCP サーバーにアクセスする。

⚠️ リモートセッション（Claude Code remote agent / routine）内でのみ動作する。
   ローカル環境では scripts/drive_get.sh <file-id> <output-path> を使うこと。

Usage:
  bash scripts/drivemcp_get_remote.sh <file-id> <output-path>
  bash scripts/drivemcp_get_remote.sh --search "parentId = 'FOLDER_ID'" <output-path>

Arguments:
  <file-id>          Drive ファイル ID
  --search <query>   Drive 検索クエリ（最終更新が最新のファイルをダウンロード）
  <output-path>      保存先パス

stdout: {"file_id": "...", "title": "...", "output": "..."} の JSON
stderr: 進捗メッセージ・エラー
exit:   0=成功 / 1=失敗
"""

import base64
import json
import os
import sys
import requests

DRIVE_UUID = "960819bd-d145-4f2b-ad5c-e521cc86112e"


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


def search_latest(drive_url, headers, query):
    """検索クエリで Drive を検索し、最終更新が最新のファイル ID とタイトルを返す。"""
    result = drive_call(drive_url, headers, "search_files",
                        {"query": query, "excludeContentSnippets": True})
    files = result.get("files", [])
    if not files:
        raise RuntimeError(f"ファイルが見つかりません: {query}")
    latest = sorted(files, key=lambda f: f.get("modifiedTime", ""), reverse=True)[0]
    return latest["id"], latest.get("title", latest["id"])


def download(drive_url, headers, file_id, output_path):
    """Drive ファイルをダウンロードして output_path に保存する。ファイルタイトルを返す。"""
    # メタデータ取得
    meta = drive_call(drive_url, headers, "get_file_metadata", {"fileId": file_id})
    title = meta.get("name") or meta.get("title") or file_id
    print(f"対象ファイル: {title}", file=sys.stderr)

    # コンテンツ取得
    dl = drive_call(drive_url, headers, "download_file_content", {"fileId": file_id})
    b64 = dl.get("content")
    if not b64:
        raise RuntimeError(f"コンテンツを取得できません: {str(dl)[:200]}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(b64))

    return title


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    # 引数パース
    if args[0] == "--search":
        if len(args) < 3:
            print("Usage: drivemcp_get_remote.sh --search <query> <output-path>", file=sys.stderr)
            sys.exit(1)
        query = args[1]
        output_path = args[2]
        file_id = None
    else:
        file_id = args[0]
        output_path = args[1]
        query = None

    try:
        drive_url, headers = get_drive_config()

        if query:
            print(f"Drive 検索中: {query}", file=sys.stderr)
            file_id, title = search_latest(drive_url, headers, query)
        else:
            title = None

        print(f"ダウンロード中: {file_id}", file=sys.stderr)
        title = download(drive_url, headers, file_id, output_path)

        result = {"file_id": file_id, "title": title, "output": output_path}
        print(json.dumps(result, ensure_ascii=False))

    except KeyError as e:
        print(f"エラー: 環境変数またはファイルが見つかりません: {e}", file=sys.stderr)
        print("このスクリプトはリモートセッション内でのみ動作します。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
