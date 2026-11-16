#!/usr/bin/env python3
"""
Post text (and optional media) to X (Twitter).
Usage:
  python3 post_to_x.py --text "投稿テキスト"
  python3 post_to_x.py --text "投稿テキスト" --image /path/to/image.png [--image 2枚目 …]   # 最大 4 枚
  python3 post_to_x.py --text "投稿テキスト" --video /path/to/video.mp4                      # 動画 1 本（画像と併用不可）
  python3 post_to_x.py --text "リプ文" --reply-to <tweet_id>
  python3 post_to_x.py --dry-run --text "テスト" --image /path/to/image.png
出力: 成功時に `https://x.com/i/web/status/<id>` を含む行を出す（post_from_email.sh / post_scheduled.py が抽出する）
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# 自分の note 記事リンクは転送ホスト（xpost.usephys.net/<記事ID>/<投稿キー>）経由にする（2026-10-04）。
# クリック数がビーコンで日次記録され、note の流入元に「X 投稿」として立つ（アプリ内ブラウザで参照元が落ちない）。
# 投稿キーは投稿ごとに違えばよく、セルフリプなら元ポストの tweet ID（X投稿一覧の行とそのまま結合できる）、
# 本文内リンクなら投稿日時（JST, YYYYMMDD-HHMM）にする。固定ポストもこの URL のままで、どの投稿が固定かは
# 「固定ポスト履歴」シートで管理する。
# 転送先の ?sub_rt=share_sb は転送側が付けるので、ここでは元 URL のパラメータを捨てる。
NOTE_LINK_RE = re.compile(r"https?://(?:www\.)?note\.com/takaesu7431/n/(n[0-9a-f]{10,16})(?:\?[A-Za-z0-9_=&%.\-]*)?")
XPOST_HOST = "https://xpost.usephys.net/"
JST = timezone(timedelta(hours=9))
MAX_IMAGES = 4
VIDEO_WAIT_MAX = 300  # 動画の処理完了待ちの上限（秒）


def post_key(reply_to: str = None, now: datetime = None) -> str:
    if reply_to:
        return str(reply_to).strip()
    return (now or datetime.now(JST)).strftime("%Y%m%d-%H%M")


def to_xpost_links(text: str, key: str) -> str:
    return NOTE_LINK_RE.sub(lambda m: f"{XPOST_HOST}{m.group(1)}/{key}", text)


def upload_video(api_v1, video_path: str):
    """チャンク分割アップロード（media_category=tweet_video）。X 側の非同期処理が終わるまで待ち、media_id を返す。
    tweepy の wait は failed で黙って返るので、ここで状態を見て失敗を明示する。"""
    print(f"🎬 動画アップロード中: {video_path}")
    media = api_v1.chunked_upload(filename=video_path, media_category="tweet_video", wait_for_async_finalize=False)
    media_id = media.media_id
    info = getattr(media, "processing_info", None) or {}
    waited = 0
    while info.get("state") in ("pending", "in_progress"):
        wait = int(info.get("check_after_secs", 5)) or 5
        if waited + wait > VIDEO_WAIT_MAX:
            print(f"❌ 動画処理が {VIDEO_WAIT_MAX} 秒以内に終わりませんでした（state={info.get('state')}）")
            sys.exit(1)
        time.sleep(wait)
        waited += wait
        status = api_v1.get_media_upload_status(media_id)
        info = getattr(status, "processing_info", None) or {}
        print(f"  …処理中 state={info.get('state')} ({waited}s)")
    if info.get("state") == "failed":
        err = info.get("error", {})
        print(f"❌ 動画の処理に失敗: {err.get('name', '')} {err.get('message', '')}")
        sys.exit(1)
    print(f"✓ メディアID: {media_id}")
    return media_id


def post_to_x(text: str, image_paths=None, reply_to: str = None, dry_run: bool = False, video_path: str = None) -> bool:
    import tweepy

    if isinstance(image_paths, str):
        image_paths = [image_paths]
    image_paths = [p for p in (image_paths or []) if p]
    if len(image_paths) > MAX_IMAGES:
        print(f"❌ 画像は {MAX_IMAGES} 枚までです（{len(image_paths)} 枚指定）")
        sys.exit(1)
    if image_paths and video_path:
        print("❌ 画像と動画は同時に付けられません")
        sys.exit(1)
    for p in image_paths + ([video_path] if video_path else []):
        if not os.path.exists(p):
            print(f"❌ メディアファイルがありません: {p}")
            sys.exit(1)

    rewritten = to_xpost_links(text, post_key(reply_to))
    if rewritten != text:
        print("🔗 note リンクを xpost.usephys.net 経由に書き換えました")
        text = rewritten

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
        for p in image_paths:
            print(f"画像: {p}")
        if video_path:
            print(f"動画: {video_path}")
        if reply_to:
            print(f"リプ先: {reply_to}")
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
    for p in image_paths:
        print(f"📷 画像アップロード中: {p}")
        media = api_v1.media_upload(filename=p)
        media_ids.append(media.media_id)
        print(f"✓ メディアID: {media.media_id}")
    if video_path:
        media_ids.append(upload_video(api_v1, video_path))

    print("📤 X に投稿中...")
    response = client.create_tweet(
        text=text,
        media_ids=media_ids if media_ids else None,
        in_reply_to_tweet_id=reply_to if reply_to else None,
    )

    tweet_id = response.data["id"]
    print(f"✓ 投稿完了: https://x.com/i/web/status/{tweet_id}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="投稿テキスト")
    parser.add_argument("--image", action="append", help="画像ファイルパス（繰り返し指定で最大 4 枚）")
    parser.add_argument("--video", help="動画ファイルパス（mp4/mov・1 本・画像と併用不可）")
    parser.add_argument("--reply-to", help="リプライ先のtweetID")
    parser.add_argument("--dry-run", action="store_true", help="実際には投稿しない")
    args = parser.parse_args()

    post_to_x(args.text, args.image, args.reply_to, args.dry_run, args.video)
