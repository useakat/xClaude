#!/bin/bash
# 初稿（ユーザーに最初に提示した版）の draft/draft.md を draft/first-draft.md として凍結する。
#
# 2つのモードを持ち、hook から2段階で呼ばれる:
#
#   --record  … PostToolUse(Write|Edit) から。stdin の JSON から書き込み先パスを読み、
#               それが投稿系プロジェクトの draft/draft.md なら記録簿に控える。
#   (引数なし) … Stop から。記録簿にある draft.md だけを凍結して記録簿を空にする。
#
# Stop（＝ユーザーに原稿を提示した瞬間）まで待ってから凍結するのは、w002 のように
# 執筆後に自動チェックを重ねてから提示するフローがあるため。書き込み時点では凍結しない。
#
# 「このセッションで実際に書いた draft.md」だけを対象にするので、過去記事を走査しない。
#
# 凍結する条件:
#   1. 記録簿にパスがある（＝自分で書いた draft.md）
#   2. draft/first-draft.md がまだ無い（初回のみ＝これが「初稿」の定義）
#
# z01 は draft/ を持たないため、パス条件から自然に外れる。

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEDGER="$REPO_ROOT/.claude/.draft-touched"

# --- 記録モード（PostToolUse から stdin で JSON を受け取る）---
if [ "${1:-}" = "--record" ]; then
  path="$(python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
p = (d.get("tool_input") or {}).get("file_path") or ""
print(p)
' 2>/dev/null)"

  case "$path" in
    */projects/w001/*/draft/draft.md|*/projects/w002/*/draft/draft.md|*/projects/w003/*/draft/draft.md)
      mkdir -p "$(dirname "$LEDGER")"
      grep -qxF "$path" "$LEDGER" 2>/dev/null || echo "$path" >> "$LEDGER"
      ;;
  esac
  exit 0
fi

# --- 凍結モード（Stop から）---
[ -f "$LEDGER" ] || exit 0

while IFS= read -r draft; do
  [ -n "$draft" ] || continue
  [ -f "$draft" ] || continue

  first="$(dirname "$draft")/first-draft.md"
  [ -f "$first" ] && continue   # 既に凍結済み

  cp "$draft" "$first"
  echo "✓ 初稿を凍結: ${first#$REPO_ROOT/}"
done < "$LEDGER"

: > "$LEDGER"
exit 0
