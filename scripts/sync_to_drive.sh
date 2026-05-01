#!/bin/bash
# outputs/ → Google Drive への一方向同期（gws CLI使用）
# Drive に同名ファイルが存在する場合はスキップ（上書きしない）

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUTS_DIR="$REPO_ROOT/outputs"
DRIVE_FOLDER_ID="1tBSBTLNTcxrO_83z4Z-NN4i-cs47jZnn"

if [ ! -d "$OUTPUTS_DIR" ]; then
  echo "エラー: outputs/ が見つかりません。" >&2
  exit 1
fi

mapfile -t local_files < <(find "$OUTPUTS_DIR" -maxdepth 1 -type f | sort)

if [ ${#local_files[@]} -eq 0 ]; then
  echo "outputs/ は空です。"
  exit 0
fi

echo "ローカル: ${#local_files[@]}件"

# Drive 既存ファイル名一覧を取得
PARAMS=$(python3 -c "import json; print(json.dumps({'q': \"'$DRIVE_FOLDER_ID' in parents and trashed=false\", 'fields': 'files(name)', 'pageSize': 1000}))")
DRIVE_FILES=$(gws drive files list --params "$PARAMS" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('\n'.join(f['name'] for f in d.get('files',[])))")

drive_count=$(echo "$DRIVE_FILES" | grep -c . 2>/dev/null || true)
echo "Drive 既存: ${drive_count}件"
echo ""

uploaded=0; skipped=0; failed=0

for filepath in "${local_files[@]}"; do
  filename=$(basename "$filepath")

  if echo "$DRIVE_FILES" | grep -qxF "$filename" 2>/dev/null; then
    echo "  スキップ (既存): $filename"
    skipped=$((skipped + 1))
    continue
  fi

  result=$(gws drive +upload "$filepath" --parent "$DRIVE_FOLDER_ID" 2>/dev/null || echo "{}")
  file_id=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)

  if [ -n "$file_id" ]; then
    echo "  ✓ アップロード: $filename"
    uploaded=$((uploaded + 1))
  else
    echo "  ✗ エラー: $filename" >&2
    failed=$((failed + 1))
  fi
done

echo ""
echo "アップロード: ${uploaded}件 / スキップ: ${skipped}件 / エラー: ${failed}件"
[ "$failed" -eq 0 ] || exit 1
