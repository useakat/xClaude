#!/usr/bin/env python3
"""
Post text (and optional image) to X (Twitter).
Usage:
  python3 post_to_x.py --text "投稿テキスト"
  python3 post_to_x.py --text "投稿テキスト" --image /path/to/image.png
  python3 post_to_x.py --dry-run --text "テスト" --image /path/to/image.png
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

def post_to_x(text: str, image_path: str = None, dry_run: bool = False) -> bool:
    import tweepy

    api_key        = os.getenv("X_OAUTH_CONSUMER_KEY")
    api_secret     = os.getenv("X_OAUTH_CONSUMER_SECRET")
    access_token   = os.getenv("X_OAUTH_ACCESS_TOKEN")
    access_secret  = os.getenv("X_OAUTH_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("❌ X API の認証情報が .env に不足しています")
        sys.exit(1)

    if dry_run:
        print("--- DRY RUN ---")
        print(f"テキスト: {text}")
        if image_path:
            print(f"画像: {image_path}")
        print("--- (実際には投稿しません) ---")
        return True

    # v1.1 API（メディアアップロード用）
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api_v1 = tweepy.API(auth)

    # v2 Client（ツイート投稿用）
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )

    media_ids = []
    if image_path:
        print(f"📷 画像アップロード中: {image_path}")
        media = api_v1.media_upload(filename=image_path)
        media_ids.append(media.media_id)
        print(f"✓ メディアID: {media.media_id}")

    print("📤 X に投稿中...")
    response = client.create_tweet(
        text=text,
        media_ids=media_ids if media_ids else None,
    )

    tweet_id = response.data["id"]
    print(f"✓ 投稿完了: https://x.com/i/web/status/{tweet_id}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="投稿テキスト")
    parser.add_argument("--image", help="画像ファイルパス（省略可）")
    parser.add_argument("--dry-run", action="store_true", help="実際には投稿しない")
    args = parser.parse_args()

    post_to_x(args.text, args.image, args.dry_run)
