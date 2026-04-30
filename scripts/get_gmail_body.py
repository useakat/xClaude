#!/usr/bin/env python3
"""
Gmail スレッドの最新メッセージ本文と message_id を JSON で出力する
Usage: python3 get_gmail_body.py <thread_id>
Output: {"message_id": "...", "body": "..."}
Exit code 1: エラー
"""
import sys
import json
import base64
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GCP_DIR = Path(__file__).parent.parent / "gcp"
TOKEN_PATH = GCP_DIR / "gmail_token.json"


def decode_body(payload):
    """メッセージペイロードから text/plain 本文を再帰的に取得"""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if mime_type.startswith("multipart/"):
        for part in payload.get("parts", []):
            result = decode_body(part)
            if result:
                return result
    return ""


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <thread_id>", file=sys.stderr)
        sys.exit(1)

    thread_id = sys.argv[1]

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()

    messages = thread.get("messages", [])
    if not messages:
        print(json.dumps({"error": "no messages"}))
        sys.exit(1)

    latest = max(messages, key=lambda m: int(m.get("internalDate", "0")))
    message_id = latest["id"]
    body = decode_body(latest.get("payload", {}))

    print(json.dumps({"message_id": message_id, "body": body}, ensure_ascii=False))


if __name__ == "__main__":
    main()
