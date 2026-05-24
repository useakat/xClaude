#!/usr/bin/env python3
"""Google Drive へファイルをアップロードする (OAuth ユーザー認証)。

初回実行時にブラウザで Google アカウント認証を行い、
gcp/drive_token.json に refresh_token を保存。以降は自動更新で再認証不要。
"""

import argparse
import mimetypes
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

GCP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gcp")
CLIENT_SECRET = os.path.join(
    GCP_DIR,
    "client_secret_598918260393-ac06gl6iaunh0lvvn7bdss5837je7cud.apps.googleusercontent.com.json",
)
TOKEN_PATH = os.path.join(GCP_DIR, "drive_token.json")


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        return creds

    if not os.path.exists(CLIENT_SECRET):
        print(f"エラー: OAuthクライアント設定が見つかりません: {CLIENT_SECRET}", file=sys.stderr)
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    # ヘッドレス環境向け: URL を表示してコードを貼り付ける方式
    creds = flow.run_local_server(
        port=0,
        open_browser=False,
        bind_addr="0.0.0.0",
    )
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    return creds


def upload(file_path, folder_id, name=None, convert_to_gdoc=False):
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}", file=sys.stderr)
        sys.exit(1)

    service = build("drive", "v3", credentials=get_credentials(), cache_discovery=False)
    mime, _ = mimetypes.guess_type(file_path)
    mime = mime or "application/octet-stream"

    metadata = {
        "name": name or os.path.basename(file_path),
        "parents": [folder_id],
    }
    if convert_to_gdoc:
        if mime.startswith("text/") or mime in ("application/rtf", "application/msword"):
            metadata["mimeType"] = "application/vnd.google-apps.document"
        elif mime in ("text/csv", "application/vnd.ms-excel"):
            metadata["mimeType"] = "application/vnd.google-apps.spreadsheet"

    media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
    f = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, webViewLink",
        supportsAllDrives=True,
    ).execute()

    print(f"アップロード完了: {f['name']}")
    print(f"  id:   {f['id']}")
    print(f"  link: {f.get('webViewLink', '(なし)')}")


def main():
    p = argparse.ArgumentParser(description="Google Drive アップロード (OAuth)")
    p.add_argument("file", nargs="?", help="アップロードするファイルのパス")
    p.add_argument(
        "-f", "--folder",
        default=os.environ.get("GDRIVE_FOLDER_ID"),
        help="アップロード先フォルダID (環境変数 GDRIVE_FOLDER_ID でも指定可)",
    )
    p.add_argument("-n", "--name", help="アップロード後のファイル名 (省略時は元ファイル名)")
    p.add_argument(
        "--gdoc", action="store_true",
        help="Google ドキュメント/スプレッドシート形式に変換してアップロード",
    )
    p.add_argument("--auth", action="store_true", help="認証だけ実行してトークンを保存")
    args = p.parse_args()

    if args.auth:
        get_credentials()
        print(f"認証完了: {TOKEN_PATH}")
        return

    if not args.file:
        p.error("file が必要です (認証だけなら --auth)")
    if not args.folder:
        print("エラー: --folder か環境変数 GDRIVE_FOLDER_ID でフォルダIDを指定してください", file=sys.stderr)
        sys.exit(1)

    upload(args.file, args.folder, name=args.name, convert_to_gdoc=args.gdoc)


if __name__ == "__main__":
    main()
