#!/bin/bash
# NotebookLM の認証情報を Google Drive にアップロードする
# リモート環境での利用前にローカルから実行する
# Usage: notebooklm_auth_push.sh
export PATH="/usr/local/bin:$PATH"

set -e

SRC="${HOME}/.notebooklm/storage_state.json"
UPLOAD_NAME="notebooklm_storage_state.json"

if [ ! -f "$SRC" ]; then
  echo "エラー: $SRC が見つかりません。先に 'notebooklm login' を実行してください。" >&2
  exit 1
fi

# 一時ファイルにリネームしてアップロード
TMP_DIR=$(mktemp -d)
cp "$SRC" "${TMP_DIR}/${UPLOAD_NAME}"

# 既存ファイルを検索
PARAMS=$(python3 -c "
import json
print(json.dumps({
    'q': \"name = 'notebooklm_storage_state.json' and trashed=false\",
    'fields': 'files(id,name)'
}))
")

EXISTING_ID=$(gws drive files list --params "$PARAMS" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); files=d.get('files',[]); print(files[0]['id'] if files else '')" 2>/dev/null || echo "")

cd "$TMP_DIR"

if [ -n "$EXISTING_ID" ]; then
  RESULT=$(gws drive files update \
    --params "{\"fileId\": \"$EXISTING_ID\"}" \
    --upload "$UPLOAD_NAME" \
    --upload-content-type "application/json" 2>/dev/null)
  FILE_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
  echo "✓ 更新: ${UPLOAD_NAME} (ID: ${FILE_ID})"
else
  RESULT=$(gws drive +upload "$UPLOAD_NAME" 2>/dev/null)
  FILE_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
  echo "✓ アップロード: ${UPLOAD_NAME} (ID: ${FILE_ID})"
fi

rm -rf "$TMP_DIR"

if [ -z "$FILE_ID" ]; then
  echo "エラー: ファイルIDが取得できませんでした" >&2
  exit 1
fi

echo "  Drive URL: https://drive.google.com/file/d/${FILE_ID}/view"
echo ""
echo "リモート環境で以下を実行してください:"
echo "  bash scripts/notebooklm_auth_pull.sh"
