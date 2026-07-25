#!/usr/bin/env python3
"""
Google Sheets の値を読み書きする汎用 CLI（サービスアカウント認証）。

mcp-gsheets（MCP ツール）の代替として、routine / cron から Bash 経由で使う。
リモート（クラウド）環境では MCP ツールの許可プロンプトを設定ファイルで
抑止できないため（2026-07-18 判明）、無人実行のシート読み書きはこのスクリプトを使う。

Usage:
  python3 sheets_values.py get    <spreadsheetId> <range>
  python3 sheets_values.py append <spreadsheetId> <range> '<values-json>'
  python3 sheets_values.py update <spreadsheetId> <range> '<values-json>'

  <values-json> は行の配列の JSON（例: '[["2026/07/18","abc"],["b","c"]]'）。
  「-」を指定すると標準入力から読む（大きなデータ向け）。

- 認証: GOOGLE_SERVICE_ACCOUNT_KEY 環境変数（JSON 文字列）を優先し、
  無ければ gcp/ のサービスアカウント鍵ファイルを使う（record_output.py と同じ）
- 出力: JSON（get は {"range", "values", "rowCount"}、append/update は API レスポンス要約）
- 依存: gspread / google-auth。未インストールなら scripts/sheets_pydeps_install.sh を
  自動実行し、$HOME/.cache/xclaude-pydeps 配下の固定バージョンを使う
"""

import json
import os
import subprocess
import sys
import time

# --- IPv4 固定(IPv6 が通らない環境でのハング回避)---
_orig_getaddrinfo = __import__("socket").getaddrinfo
def _ipv4_only(*args, **kwargs):
    import socket
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
__import__("socket").getaddrinfo = _ipv4_only

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sheets_pydeps_install.sh の VERSION と一致させること
PYDEPS_DIR = os.path.expanduser("~/.cache/xclaude-pydeps/2")
SA_FILE = os.path.join(SCRIPT_DIR, "..", "gcp", "charming-well-464402-u4-2cfb7bddf343.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _import_deps():
    global gspread, Credentials
    import gspread
    from google.oauth2.service_account import Credentials


try:
    _import_deps()
except ImportError:
    if os.path.isdir(PYDEPS_DIR):
        sys.path.insert(0, PYDEPS_DIR)
    try:
        _import_deps()
    except ImportError:
        subprocess.run(
            ["bash", os.path.join(SCRIPT_DIR, "sheets_pydeps_install.sh")],
            check=True, stdout=sys.stderr,
        )
        sys.path.insert(0, PYDEPS_DIR)
        _import_deps()


def get_client():
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if key_json:
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(os.path.abspath(SA_FILE), scopes=SCOPES)
    return gspread.authorize(creds)


def open_with_retry(client, spreadsheet_id):
    """
    セッション初回コールドスタート時に `open_by_key` が 404 を返すことがあるため
    1 秒待って 1 回だけリトライする（2026-07-24 に本番 routine で観測）。
    2 回目も 404 なら真の権限問題なので通常どおり例外を上げる。
    """
    try:
        return client.open_by_key(spreadsheet_id)
    except gspread.exceptions.SpreadsheetNotFound as e:
        resp = getattr(e, "response", None)
        status = getattr(resp, "status_code", None)
        body = ""
        try:
            body = resp.text[:500] if resp is not None else ""
        except Exception:
            pass
        print(
            f"[sheets_values] 404 on open_by_key(attempt 1) id={spreadsheet_id} "
            f"status={status} body={body!r} — retrying after 1s",
            file=sys.stderr,
        )
        time.sleep(1)
        return client.open_by_key(spreadsheet_id)


def load_values(arg: str):
    raw = sys.stdin.read() if arg == "-" else arg
    values = json.loads(raw)
    if not isinstance(values, list) or not all(isinstance(r, list) for r in values):
        raise ValueError("values は行の配列の JSON で指定する（例: [[\"a\",\"b\"]]）")
    return values


def main():
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        sys.exit(2)

    command, spreadsheet_id, rng = sys.argv[1], sys.argv[2], sys.argv[3]
    ss = open_with_retry(get_client(), spreadsheet_id)

    if command == "get":
        resp = ss.values_get(rng)
        values = resp.get("values", [])
        out = {"range": resp.get("range", rng), "rowCount": len(values), "values": values}
    elif command in ("append", "update"):
        if len(sys.argv) < 5:
            print("append / update には <values-json> が必要です", file=sys.stderr)
            sys.exit(2)
        values = load_values(sys.argv[4])
        params = {"valueInputOption": "USER_ENTERED"}
        body = {"values": values}
        if command == "append":
            resp = ss.values_append(rng, params=params, body=body)
            updates = resp.get("updates", {})
            out = {
                "updatedRange": updates.get("updatedRange"),
                "updatedRows": updates.get("updatedRows"),
                "updatedCells": updates.get("updatedCells"),
            }
        else:
            resp = ss.values_update(rng, params=params, body=body)
            out = {
                "updatedRange": resp.get("updatedRange"),
                "updatedRows": resp.get("updatedRows"),
                "updatedCells": resp.get("updatedCells"),
            }
    else:
        print(f"不明なコマンド: {command}（get / append / update）", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
