#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "google-auth",
#   "google-auth-oauthlib",
#   "google-api-python-client",
# ]
# ///
# Usage: python3 send_gmail_direct.py --subject "..." --body "..."
# gcp/gmail_token.json で Gmail API 認証。gws とは独立しているため gws が切れていても動く。

import argparse
import base64
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = Path(__file__).parent.parent / "gcp" / "gmail_token.json"
TO = "useakat@gmail.com"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", required=True)
    args = ap.parse_args()

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())

    svc = build("gmail", "v1", credentials=creds)
    msg = MIMEText(args.body)
    msg["to"] = TO
    msg["subject"] = args.subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    print("✓ Gmail 送信完了")


if __name__ == "__main__":
    main()
