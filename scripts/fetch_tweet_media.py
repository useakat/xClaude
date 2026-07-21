#!/usr/bin/env python3
"""tweet_id から、そのツイートの画像（photo）の pbs.twimg.com 公開URLを取得する。

X投稿を Threads に転載する際、Threads API は公開URL（image_url）しか受け付けないため、
投稿直後のツイートの画像URLを認証不要の syndication API から取得する。

- 投稿直後はインデックス遅延で取れないことがあるため数回リトライする。
- 取得できなければ空出力で正常終了（＝画像なし扱い。呼び出し側はテキストのみ転載）。
- この VPS は IPv6 が通らないため DNS を IPv4 固定する。

Usage:
  python3 scripts/fetch_tweet_media.py <tweet_id>
  → photo の media_url_https を空白区切りで標準出力（無ければ何も出力しない）
"""
import json
import socket
import sys
import time
import urllib.error
import urllib.request

# --- IPv4 固定（IPv6 が通らない環境でのハング回避）---
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    v4 = [r for r in res if r[0] == socket.AF_INET]
    return v4 or res
socket.getaddrinfo = _ipv4_only

API = "https://cdn.syndication.twimg.com/tweet-result?id={sid}&lang=ja&token=a"
RETRIES = 6
RETRY_WAIT = 3


def fetch_photo_urls(tweet_id):
    url = API.format(sid=tweet_id)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TimeoutError):
        return None  # 取得不可（リトライ対象）
    if not isinstance(d, dict) or d.get("__typename") == "TweetTombstone":
        return None
    urls = []
    for m in d.get("mediaDetails") or []:
        if m.get("type") == "photo" and m.get("media_url_https"):
            urls.append(m["media_url_https"])
    return urls  # [] は「画像なしツイート」（リトライ不要）


def main():
    if len(sys.argv) != 2:
        print("Usage: fetch_tweet_media.py <tweet_id>", file=sys.stderr)
        sys.exit(2)
    tweet_id = sys.argv[1]
    for i in range(RETRIES):
        urls = fetch_photo_urls(tweet_id)
        if urls:  # 画像が取れた
            print(" ".join(urls))
            return
        if urls == []:  # ツイートは取れたが画像なし → 確定、リトライ不要
            return
        # urls is None（インデックス遅延・一時エラー）→ リトライ
        if i < RETRIES - 1:
            time.sleep(RETRY_WAIT)
    # 最後まで取れず（削除済み等）→ 空出力で終了


if __name__ == "__main__":
    main()
