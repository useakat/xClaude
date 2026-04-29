#!/usr/bin/env python3
"""
Gmail OAuth 認証のセットアップ（初回のみ）
Usage: python3 scripts/gmail_auth.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

GCP_DIR = Path(__file__).parent.parent / "gcp"
CLIENT_SECRET = GCP_DIR / "client_secret_598918260393-ac06gl6iaunh0lvvn7bdss5837je7cud.apps.googleusercontent.com.json"
TOKEN_PATH = GCP_DIR / "gmail_token.json"

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET), SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    print(f"\n以下のURLをブラウザで開いて認証してください：\n\n{auth_url}\n")
    code = input("認証後に表示されたコードを貼り付けてください: ").strip()
    flow.fetch_token(code=code)
    creds = flow.credentials
    TOKEN_PATH.write_text(creds.to_json())
    print(f"✓ 認証完了: {TOKEN_PATH}")

if __name__ == "__main__":
    main()
