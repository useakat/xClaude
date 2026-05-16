#!/bin/bash
# Gmail スレッドの最新メッセージから本文と message_id を JSON で出力する（gws CLI 版）
export PATH="/usr/local/bin:$PATH"
# Usage: bash get_gmail_body.sh <thread_id>
# Output: {"message_id": "...", "body": "..."}
# Exit code 1: エラー

set -uo pipefail

THREAD_ID="${1:-}"
if [ -z "$THREAD_ID" ]; then
  echo "Usage: $0 <thread_id>" >&2
  exit 1
fi

gws gmail users threads get \
  --params "{\"userId\":\"me\",\"id\":\"$THREAD_ID\",\"format\":\"full\"}" 2>/dev/null \
  | python3 -c "
import json, sys, base64

def decode_body(payload):
    mime = payload.get('mimeType', '')
    if mime == 'text/plain':
        data = payload.get('body', {}).get('data', '')
        if data:
            return base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='replace')
    if mime.startswith('multipart/'):
        for part in payload.get('parts', []):
            r = decode_body(part)
            if r:
                return r
    return ''

d = json.load(sys.stdin)
msgs = d.get('messages', [])
if not msgs:
    print(json.dumps({'error': 'no messages'}))
    sys.exit(1)

latest = max(msgs, key=lambda m: int(m.get('internalDate', '0')))
body_text = decode_body(latest.get('payload', {}))
body_text = body_text.replace('\r\n', '\n')
print(json.dumps({
    'message_id': latest['id'],
    'body': body_text,
}, ensure_ascii=False))
"
