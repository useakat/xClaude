#!/usr/bin/env python3
"""
Gmail から添付ファイルをダウンロードする。
Usage:
  python3 download_gmail_attachment.py <message_id> <output_path>

message_id が見つかった最初の画像添付ファイルを output_path に保存する。
添付がない場合は exit code 1 で終了。
"""

import base64
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GCP_DIR = Path(__file__).parent.parent / "gcp"
TOKEN_PATH = GCP_DIR / "gmail_token.json"
IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}


def get_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def download_attachment(message_id: str, output_path: str) -> bool:
    service = get_service()
    msg = service.users().messages().get(userId="me", id=message_id).execute()

    parts = msg.get("payload", {}).get("parts", [])

    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type not in IMAGE_MIME_TYPES:
            continue

        attachment_id = part.get("body", {}).get("attachmentId")
        if not attachment_id:
            continue

        attachment = service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=attachment_id
        ).execute()

        data = base64.urlsafe_b64decode(attachment["data"])
        Path(output_path).write_bytes(data)
        print(f"✓ 添付ファイルを保存: {output_path} ({mime_type})")
        return True

    print("添付画像なし")
    return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 download_gmail_attachment.py <message_id> <output_path>")
        sys.exit(1)

    success = download_attachment(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
