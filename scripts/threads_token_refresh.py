#!/usr/bin/env python3
"""Threads 長期トークンを th_refresh_token で延長し gcp/threads_token.json を更新する。
App Secret は不要（トークン自身で更新）。トークンは発行から24時間以上経過している必要がある。
IPv6 が通らない環境向けに DNS を IPv4 固定する。
"""
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

_orig = socket.getaddrinfo
socket.getaddrinfo = lambda *a, **k: [r for r in _orig(*a, **k) if r[0] == socket.AF_INET] or _orig(*a, **k)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "gcp", "threads_token.json")


def main():
    d = json.load(open(P, encoding="utf-8"))
    url = "https://graph.threads.net/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "th_refresh_token", "access_token": d["access_token"]}
    )
    try:
        r = json.load(urllib.request.urlopen(url, timeout=30))
    except urllib.error.HTTPError as e:
        sys.exit(f"APIエラー ({e.code}): {e.read().decode()}")
    if "access_token" not in r:
        sys.exit(f"更新失敗: {r}")
    d["access_token"] = r["access_token"]
    d["expires_in"] = r.get("expires_in")
    d["obtained_at"] = int(time.time())
    json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"✓ トークン更新。有効日数≈{(r.get('expires_in') or 0)//86400}")


if __name__ == "__main__":
    main()
