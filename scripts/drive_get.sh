#!/bin/bash
# Usage: drive_get.sh <file-id> <output-path>
# Drive のファイル ID を指定してローカルにダウンロード

set -e

FILE_ID="$1"
OUTPUT="$2"

if [ -z "$FILE_ID" ] || [ -z "$OUTPUT" ]; then
  echo "Usage: drive_get.sh <file-id> <output-path>" >&2
  exit 1
fi

# 出力先ディレクトリを作成
mkdir -p "$(dirname "$OUTPUT")"

gws drive files get \
  --params "{\"fileId\": \"$FILE_ID\", \"alt\": \"media\"}" \
  -o "$OUTPUT" 2>/dev/null > /dev/null

if [ ! -f "$OUTPUT" ]; then
  echo "エラー: ダウンロード失敗" >&2
  exit 1
fi

echo "ダウンロード: $OUTPUT" >&2
