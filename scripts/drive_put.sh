#!/bin/bash
# Usage: drive_put.sh <local-file> [folder-id]
export PATH="/usr/local/bin:$PATH"
# ローカルファイルを Drive のフォルダにアップロード/更新
# folder-id 省略時は drafts-note フォルダ
# 同名ファイルが存在すれば更新（Drive のリビジョン履歴に残る）、なければ新規作成
# 標準出力: file_id<TAB>drive_url

set -e

LOCAL_FILE="$1"
FOLDER_ID="${2:-1j58LBOYgjiOf1RAGdwFcrQSmVKiT00BP}"

if [ -z "$LOCAL_FILE" ]; then
  echo "Usage: drive_put.sh <local-file> [folder-id]" >&2
  exit 1
fi

if [ ! -f "$LOCAL_FILE" ]; then
  echo "エラー: ファイルが見つかりません: $LOCAL_FILE" >&2
  exit 1
fi

FILENAME=$(basename "$LOCAL_FILE")
FILE_DIR=$(cd "$(dirname "$LOCAL_FILE")" && pwd)
MIME_TYPE=$(file --mime-type -b "$LOCAL_FILE")

# 既存ファイル検索
PARAMS=$(python3 -c "
import json, sys
folder, name = sys.argv[1], sys.argv[2]
print(json.dumps({
    'q': f\"'{folder}' in parents and name = '{name}' and trashed=false\",
    'fields': 'files(id,name)'
}))
" "$FOLDER_ID" "$FILENAME")

EXISTING_ID=$(gws drive files list --params "$PARAMS" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); files=d.get('files',[]); print(files[0]['id'] if files else '')")

cd "$FILE_DIR"

if [ -n "$EXISTING_ID" ]; then
  RESULT=$(gws drive files update \
    --params "{\"fileId\": \"$EXISTING_ID\"}" \
    --upload "$FILENAME" \
    --upload-content-type "$MIME_TYPE" 2>/dev/null)
  FILE_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
  echo "更新: $FILENAME" >&2
else
  RESULT=$(gws drive +upload "$FILENAME" --parent "$FOLDER_ID" 2>/dev/null)
  FILE_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
  echo "新規アップロード: $FILENAME" >&2
fi

if [ -z "$FILE_ID" ]; then
  echo "エラー: ファイルIDが取得できませんでした" >&2
  exit 1
fi

echo -e "${FILE_ID}\thttps://drive.google.com/file/d/${FILE_ID}/view"
