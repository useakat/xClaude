#!/bin/bash
# Gmail 下書きを作成する（gws CLI 版）
export PATH="/usr/local/bin:$PATH"
# Usage: bash create_gmail_draft.sh --to <email> --subject <subject> --body-file <file> [--attach <path>]...
# --attach は複数回指定可（添付ファイル、合計25MBまで）
# Exit code 0: 成功 / 1: エラー

set -uo pipefail

TO=""
SUBJECT=""
BODY_FILE=""
ATTACH_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to)        TO="$2"; shift 2 ;;
    --subject)   SUBJECT="$2"; shift 2 ;;
    --body-file) BODY_FILE="$2"; shift 2 ;;
    --attach)
      if [ ! -f "$2" ]; then
        echo "添付ファイルが存在しません: $2" >&2
        exit 1
      fi
      ATTACH_ARGS+=(--attach "$2"); shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$TO" ] || [ -z "$SUBJECT" ] || [ -z "$BODY_FILE" ]; then
  echo "Usage: $0 --to <email> --subject <subject> --body-file <file> [--attach <path>]..." >&2
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
  --body "$BODY" \
  "${ATTACH_ARGS[@]}" \
  --draft 2>&1)

RC=$?
if [ $RC -ne 0 ]; then
  echo "$RESULT" >&2
  exit 1
fi

DRAFT_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
echo "✓ 下書き作成完了 (id: $DRAFT_ID)"
