#!/usr/bin/env python3
import os
import sys
import json
import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def post_tweet(text: str) -> dict:
    auth = OAuth1(
        os.getenv("X_OAUTH_CONSUMER_KEY"),
        os.getenv("X_OAUTH_CONSUMER_SECRET"),
        os.getenv("X_OAUTH_ACCESS_TOKEN"),
        os.getenv("X_OAUTH_ACCESS_TOKEN_SECRET"),
    )
    resp = requests.post(
        "https://api.x.com/2/tweets",
        auth=auth,
        json={"text": text},
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
    result = post_tweet(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
