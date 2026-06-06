#!/usr/bin/env python3
"""
Google Drive ファイルアップロード（リモートセッション専用）
Anthropic MCP プロキシ経由で Google Drive MCP サーバーにアクセスする。

⚠️ リモートセッション（Claude Code remote agent / routine）内でのみ動作する。
   ローカル環境では scripts/drive_put.sh <local-file> [folder-id] を使うこと。

Usage:
  bash scripts/drivemcp_put_remote.sh <local-file> [folder-id]

Arguments:
  <local-file>   アップロードするローカルファイルパス
  [folder-id]    アップロード先フォルダ ID（省略時は drafts-note フォルダ）

stdout: file_id<TAB>drive_url
stderr: 進捗メッセージ・エラー
exit:   0=成功 / 1=失敗
"""

import base64
import json
import mimetypes
import os
import sys
import requests

DRIVE_UUID = "960819bd-d145-4f2b-ad5c-e521cc86112e"
DEFAULT_FOLDER_ID = "1j58LBOYgjiOf1RAGdwFcrQSmVKiT00BP"


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


def upload(drive_url, headers, local_file, folder_id):
    filename = os.path.basename(local_file)
    mime_type = mimetypes.guess_type(local_file)[0] or "application/octet-stream"

    with open(local_file, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    print(f"アップロード中: {filename} ({mime_type})", file=sys.stderr)

    result = drive_call(drive_url, headers, "create_file", {
        "name": filename,
        "content": content_b64,
        "mimeType": mime_type,
        "parents": [folder_id],
    })

    file_id = result.get("id") or result.get("fileId")
    if not file_id:
        raise RuntimeError(f"ファイルIDが取得できません: {str(result)[:200]}")

    return file_id


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    local_file = args[0]
    folder_id = args[1] if len(args) > 1 else DEFAULT_FOLDER_ID

    if not os.path.isfile(local_file):
        print(f"エラー: ファイルが見つかりません: {local_file}", file=sys.stderr)
        sys.exit(1)

    try:
        drive_url, headers = get_drive_config()
        file_id = upload(drive_url, headers, local_file, folder_id)
        result_url = f"https://drive.google.com/file/d/{file_id}/view"
        print(f"{file_id}\t{result_url}")
        print(f"✓ アップロード完了: {result_url}", file=sys.stderr)

    except KeyError as e:
        print(f"エラー: 環境変数またはファイルが見つかりません: {e}", file=sys.stderr)
        print("このスクリプトはリモートセッション内でのみ動作します。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
