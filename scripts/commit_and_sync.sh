#!/bin/bash
# Commit changes locally (push is handled via GitHub MCP)
#
# Usage:
#   bash scripts/commit_and_sync.sh "commit message" <path> [<path>...]   # 対象限定（推奨）
#   bash scripts/commit_and_sync.sh "commit message"                      # 全変更（非推奨）
#
# 対象パスを渡すと、そのファイルだけをステージしてコミットする。
# 渡さない場合は従来どおり git add -A で全変更をステージするが、
# 複数セッションが同じリポジトリで動いていると他セッションの未コミット作業を
# 巻き込むため、警告を出す（2026-08-14 に /record で実際に発生。過去も再発多数）。

set -e

if [ -z "$1" ]; then
  echo "❌ commit message が必要です"
  echo "使用方法: bash scripts/commit_and_sync.sh \"commit message\" <path> [<path>...]"
  exit 1
fi

COMMIT_MSG="$1"
shift
PATHS=("$@")

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

if [ ${#PATHS[@]} -gt 0 ]; then
  echo "📝 対象をステージング: ${PATHS[*]}"
  git add -- "${PATHS[@]}"
else
  echo "⚠ 対象パス未指定のため全変更をステージします。"
  echo "  他セッションの未コミット作業を巻き込む恐れがあります。"
  echo "  対象を絞るには: bash scripts/commit_and_sync.sh \"msg\" <path> [<path>...]"
  if [ -z "$(git status --porcelain)" ]; then
    echo "✓ 変更なし"
    exit 0
  fi
  echo "📝 変更をステージング..."
  git add -A
fi

# ステージ結果の確認（対象指定時に差分が無いケースを拾う）
if git diff --cached --quiet; then
  echo "✓ 変更なし（ステージされたものがありません）"
  exit 0
fi

echo "💾 コミット: $COMMIT_MSG"
echo "   含まれるファイル:"
git diff --cached --name-only | sed 's/^/     /'

git commit -m "$COMMIT_MSG

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"

echo "✓ コミット完了（push は GitHub MCP で行う）"
