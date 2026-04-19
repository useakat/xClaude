#!/usr/bin/env python3
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

LIMIT = 4900  # LINE上限5000字の安全マージン

def send_line(message: str) -> list:
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    chunks = [message[i:i+LIMIT] for i in range(0, len(message), LIMIT)]
    results = []
    for i, chunk in enumerate(chunks):
        text = f"({i+1}/{len(chunks)})\n{chunk}" if len(chunks) > 1 else chunk
        resp = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=headers,
            json={"to": user_id, "messages": [{"type": "text", "text": text}]},
        )
        resp.raise_for_status()
        results.append({"chunk": i+1, "status": resp.status_code})
    return results

if __name__ == "__main__":
    message = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
    results = send_line(message)
    print(json.dumps(results, ensure_ascii=False, indent=2))
