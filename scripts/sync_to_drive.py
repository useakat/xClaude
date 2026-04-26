#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "google-auth",
#   "google-auth-oauthlib",
#   "google-api-python-client",
# ]
# ///
"""outputs/ → Google Drive への一方向同期スクリプト（ユーザー OAuth）."""

import argparse
import json
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DRIVE_FOLDER_ID = "1tBSBTLNTcxrO_83z4Z-NN4i-cs47jZnn"
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
TOKEN_PATH = Path(__file__).parent.parent / "gcp" / "drive_token.json"
FLOW_STATE_PATH = Path(__file__).parent.parent / "gcp" / ".drive_flow_state.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}


def get_client_secret_path() -> str:
    return os.environ.get(
        "GOOGLE_OAUTH_CLIENT_SECRET",
        str(Path(__file__).parent.parent / "gcp" / "client_secret_598918260393-ac06gl6iaunh0lvvn7bdss5837je7cud.apps.googleusercontent.com.json"),
    )


def print_auth_url():
    """認証 URL を表示し、フロー状態を一時保存する。"""
    client_secret_path = get_client_secret_path()
    if not os.path.exists(client_secret_path):
        print("エラー: OAuth クライアントシークレットが見つかりません。", file=sys.stderr)
        sys.exit(1)
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_path, SCOPES, redirect_uri="http://localhost"
    )
    auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")

    # code_verifier を一時ファイルに保存（--auth-code で使用）
    FLOW_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FLOW_STATE_PATH.write_text(json.dumps({
        "state": state,
        "code_verifier": flow.code_verifier,
        "client_secret_path": client_secret_path,
    }))

    print("以下の URL をブラウザで開いて認証してください：")
    print(f"\n  {auth_url}\n")
    print("認証後、ブラウザが localhost にリダイレクトして「接続できない」画面になります。")
    print("そのときのアドレスバーの URL から code= の値をコピーして以下を実行してください：")
    print("  ! uv run scripts/sync_to_drive.py --auth-code <コード>")


def save_token(code: str):
    """認証コードをトークンに交換して保存する。"""
    if not FLOW_STATE_PATH.exists():
        print("エラー: フロー状態が見つかりません。先に --auth-url を実行してください。", file=sys.stderr)
        sys.exit(1)

    saved = json.loads(FLOW_STATE_PATH.read_text())
    flow = InstalledAppFlow.from_client_secrets_file(
        saved["client_secret_path"], SCOPES, redirect_uri="http://localhost"
    )
    flow.code_verifier = saved["code_verifier"]
    flow.fetch_token(code=code)

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(flow.credentials.to_json())
    FLOW_STATE_PATH.unlink(missing_ok=True)
    print(f"✓ トークンを保存しました: {TOKEN_PATH}")


def get_service():
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        else:
            print("認証が必要です。まず以下を実行してください：", file=sys.stderr)
            print("  ! uv run scripts/sync_to_drive.py --auth-url", file=sys.stderr)
            sys.exit(1)

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_drive_files(service) -> dict[str, str]:
    """Drive フォルダ内のファイル名 → ID の辞書を返す。"""
    results = service.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and trashed = false",
        fields="files(id, name)",
        pageSize=1000,
    ).execute()
    return {f["name"]: f["id"] for f in results.get("files", [])}


def upload_file(service, local_path: Path, mime_type: str) -> str:
    """ファイルをアップロードしてファイルIDを返す。"""
    metadata = {"name": local_path.name, "parents": [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)
    file = service.files().create(body=metadata, media_body=media, fields="id").execute()
    return file.get("id")


def main():
    if not OUTPUTS_DIR.exists():
        print("エラー: outputs/ ディレクトリが見つかりません。", file=sys.stderr)
        sys.exit(1)

    local_files = sorted(f for f in OUTPUTS_DIR.iterdir() if f.is_file())
    if not local_files:
        print("outputs/ は空です。")
        return

    print(f"ローカル: {len(local_files)}件")

    service = get_service()
    drive_files = list_drive_files(service)
    print(f"Drive 既存: {len(drive_files)}件\n")

    uploaded, skipped, failed = [], [], []

    for local_path in local_files:
        if local_path.name in drive_files:
            skipped.append(local_path.name)
            print(f"  スキップ (既存): {local_path.name}")
            continue

        mime_type = MIME_TYPES.get(local_path.suffix.lower(), "application/octet-stream")
        try:
            upload_file(service, local_path, mime_type)
            uploaded.append(local_path.name)
            print(f"  ✓ アップロード: {local_path.name}")
        except Exception as e:
            failed.append(local_path.name)
            print(f"  ✗ エラー ({local_path.name}): {e}", file=sys.stderr)

    print(f"\nアップロード: {len(uploaded)}件 / スキップ: {len(skipped)}件 / エラー: {len(failed)}件")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth-url", action="store_true", help="認証URLを表示して終了")
    parser.add_argument("--auth-code", metavar="CODE", help="認証コードを渡してトークンを保存")
    args = parser.parse_args()

    if args.auth_url:
        print_auth_url()
    elif args.auth_code:
        save_token(args.auth_code)
        print("次回から通常実行できます: uv run scripts/sync_to_drive.py")
    else:
        main()
