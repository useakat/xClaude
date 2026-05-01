#!/usr/bin/env python3
"""
Gmail メールを送信する
Usage: python3 send_gmail.py --to <email> --subject <subject> --body-file <file>
Exit code 0: 成功
Exit code 1: エラー
"""
import base64
import argparse
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GCP_DIR = Path(__file__).parent.parent / "gcp"
TOKEN_PATH = GCP_DIR / "gmail_token.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", required=True)
    args = parser.parse_args()

    body = Path(args.body_file).read_text(encoding="utf-8")

    message = MIMEText(body, "plain", "utf-8")
    message["to"] = args.to
    message["subject"] = args.subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    sent = service.users().messages().send(
        userId="me",
        body={"raw": raw},
    ).execute()

    print(f"✓ 送信完了 (id: {sent['id']})")


if __name__ == "__main__":
    main()
