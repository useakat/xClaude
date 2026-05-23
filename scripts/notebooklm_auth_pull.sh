#!/bin/bash
# NotebookLM の認証情報を Google Drive からダウンロードする
# リモート環境で /visual_infographic スキルを使う前に実行する
# Usage: notebooklm_auth_pull.sh
export PATH="/usr/local/bin:$PATH"

set -e

ROOT=$(git rev-parse --show-toplevel)
DEST="${ROOT}/gcp/notebooklm_storage_state.json"
SEARCH_NAME="notebooklm_storage_state.json"

# Drive でファイルを検索
PARAMS=$(python3 -c "
import json
print(json.dumps({
    'q': \"name = 'notebooklm_storage_state.json' and trashed=false\",
    'fields': 'files(id,name)'
}))
")

FILE_ID=$(gws drive files list --params "$PARAMS" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); files=d.get('files',[]); print(files[0]['id'] if files else '')")

if [ -z "$FILE_ID" ]; then
  echo "エラー: Drive に ${SEARCH_NAME} が見つかりません。" >&2
  echo "ローカル環境で 'bash scripts/notebooklm_auth_push.sh' を先に実行してください。" >&2
  exit 1
fi

mkdir -p "${ROOT}/gcp"
bash "${ROOT}/scripts/drive_get.sh" "$FILE_ID" "$DEST"

if [ -s "$DEST" ]; then
  echo "✓ 認証情報を保存: ${DEST}"
  echo "  notebooklm_manager.py が自動的にこのファイルを使用します"
else
  echo "エラー: ダウンロードされたファイルが空です" >&2
  rm -f "$DEST"
  exit 1
fi
