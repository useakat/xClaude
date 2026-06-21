#!/bin/bash
# Usage: drive_put_folder.sh <local-dir> <parent-folder-id>
# ローカルフォルダを Drive に再帰アップロードする（サブフォルダ構造を再現）。
# 同名のサブフォルダ/ファイルが既にあれば再利用・更新する（idempotent）。
# ファイル単位のアップロードは drive_put.sh に委譲する。
export PATH="/home/useakat/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

set -euo pipefail

LOCAL_DIR="${1:-}"
PARENT_ID="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$LOCAL_DIR" ] || [ -z "$PARENT_ID" ]; then
  echo "Usage: drive_put_folder.sh <local-dir> <parent-folder-id>" >&2
  exit 1
fi
if [ ! -d "$LOCAL_DIR" ]; then
  echo "エラー: フォルダが見つかりません: $LOCAL_DIR" >&2
  exit 1
fi

# Drive 上で name のフォルダを親の下に取得（無ければ作成）し、その id を返す
get_or_create_folder() {
  local name="$1" parent="$2" params id

  params=$(python3 -c "
import json, sys
folder, name = sys.argv[1], sys.argv[2]
print(json.dumps({
    'q': f\"'{folder}' in parents and name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false\",
    'fields': 'files(id,name)'
}))
" "$parent" "$name")

  id=$(gws drive files list --params "$params" 2>/dev/null \
    | python3 -c "import json,sys; s=sys.stdin.read().strip(); d=json.loads(s) if s else {}; fs=d.get('files',[]); print(fs[0]['id'] if fs else '')")

  if [ -z "$id" ]; then
    local create_params
    create_params=$(python3 -c "
import json, sys
name, parent = sys.argv[1], sys.argv[2]
print(json.dumps({'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent]}))
" "$name" "$parent")
    id=$(gws drive files create --json "$create_params" 2>/dev/null \
      | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
    [ -n "$id" ] && echo "フォルダ作成: $name" >&2 || { echo "エラー: フォルダ作成失敗: $name" >&2; return 1; }
  else
    echo "フォルダ再利用: $name" >&2
  fi
  echo "$id"
}

# local_dir を parent_id の下に再帰アップロード
upload_dir() {
  local dir="$1" parent="$2" fid entry
  fid=$(get_or_create_folder "$(basename "$dir")" "$parent")
  [ -n "$fid" ] || { echo "エラー: フォルダID取得失敗: $dir" >&2; return 1; }

  shopt -s nullglob dotglob
  for entry in "$dir"/*; do
    if [ -d "$entry" ]; then
      upload_dir "$entry" "$fid"
    elif [ -f "$entry" ]; then
      bash "$SCRIPT_DIR/drive_put.sh" "$entry" "$fid" >/dev/null
      echo "  ✓ $(basename "$entry")" >&2
    fi
  done
  shopt -u nullglob dotglob
}

echo "=== Drive アップロード開始: $LOCAL_DIR → 親 $PARENT_ID ===" >&2
upload_dir "$LOCAL_DIR" "$PARENT_ID"
echo "=== 完了 ===" >&2
