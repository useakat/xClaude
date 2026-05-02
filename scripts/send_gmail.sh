#!/bin/bash
# Gmail メールを送信する（gws CLI 版）
# Usage: bash send_gmail.sh --to <email> --subject <subject> --body-file <file>
# Exit code 0: 成功 / 1: エラー

set -uo pipefail

TO=""
SUBJECT=""
BODY_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to)        TO="$2"; shift 2 ;;
    --subject)   SUBJECT="$2"; shift 2 ;;
    --body-file) BODY_FILE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$TO" ] || [ -z "$SUBJECT" ] || [ -z "$BODY_FILE" ]; then
  echo "Usage: $0 --to <email> --subject <subject> --body-file <file>" >&2
  exit 1
fi

if [ ! -f "$BODY_FILE" ]; then
  echo "ファイルが存在しません: $BODY_FILE" >&2
  exit 1
fi

BODY=$(cat "$BODY_FILE")

RESULT=$(gws gmail +send \
  --to "$TO" \
  --subject "$SUBJECT" \
  --body "$BODY" 2>&1)

RC=$?
if [ $RC -ne 0 ]; then
  echo "$RESULT" >&2
  exit 1
fi

MSG_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
echo "✓ 送信完了 (id: $MSG_ID)"
