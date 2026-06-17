#!/bin/bash
# Usage: drive_get.sh <file-id> <output-path>
export PATH="/home/useakat/.npm-global/bin:/usr/local/bin:$PATH"
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

# 現行 gws は -o の出力先をカレントディレクトリ内に限定するため、
# 出力先ディレクトリに cd して basename で渡す（絶対パスは "outside the current directory" で弾かれる）
OUTDIR=$(cd "$(dirname "$OUTPUT")" && pwd)
OUTBASE=$(basename "$OUTPUT")
( cd "$OUTDIR" && gws drive files get \
  --params "{\"fileId\": \"$FILE_ID\", \"alt\": \"media\"}" \
  -o "$OUTBASE" 2>/dev/null > /dev/null )

if [ ! -f "$OUTPUT" ]; then
  echo "エラー: ダウンロード失敗" >&2
  exit 1
fi

echo "ダウンロード: $OUTPUT" >&2
