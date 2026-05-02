#!/bin/bash
# Gmail メッセージから画像添付ファイルをダウンロードする（gws CLI 版）
# Usage: bash download_gmail_attachment.sh <message_id> <output_path>
# Exit code 0: 添付保存成功 / 1: 添付なし or エラー

set -uo pipefail

MSG_ID="${1:-}"
OUT="${2:-}"

if [ -z "$MSG_ID" ] || [ -z "$OUT" ]; then
  echo "Usage: $0 <message_id> <output_path>" >&2
  exit 1
fi

# メッセージから画像添付の attachmentId を取得
ATT_INFO=$(gws gmail users messages get \
  --params "{\"userId\":\"me\",\"id\":\"$MSG_ID\"}" 2>/dev/null \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
parts = d.get('payload', {}).get('parts', [])
IMAGE_MIMES = {'image/png','image/jpeg','image/jpg','image/gif','image/webp'}
for p in parts:
    mime = p.get('mimeType', '')
    if mime in IMAGE_MIMES:
        att_id = p.get('body', {}).get('attachmentId', '')
        if att_id:
            print(f'{mime}\t{att_id}')
            sys.exit(0)
")

if [ -z "$ATT_INFO" ]; then
  echo "添付画像なし" >&2
  exit 1
fi

MIME=$(echo "$ATT_INFO" | cut -f1)
ATT_ID=$(echo "$ATT_INFO" | cut -f2)

# 添付を取得して base64 デコードして保存
gws gmail users messages attachments get \
  --params "{\"userId\":\"me\",\"messageId\":\"$MSG_ID\",\"id\":\"$ATT_ID\"}" 2>/dev/null \
  | OUT="$OUT" python3 -c "
import os, json, sys, base64
d = json.load(sys.stdin)
data = d.get('data', '')
if not data:
    sys.exit(1)
open(os.environ['OUT'], 'wb').write(base64.urlsafe_b64decode(data + '=='))
"

RC=$?
if [ $RC -ne 0 ]; then
  echo "添付データ取得失敗" >&2
  exit 1
fi

echo "✓ 添付ファイルを保存: $OUT ($MIME)"
