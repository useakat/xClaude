#!/bin/bash
# Commit changes locally (push is handled via GitHub MCP)
# Usage: bash scripts/commit_and_sync.sh "commit message"

set -e

if [ -z "$1" ]; then
  echo "❌ commit message が必要です"
  echo "使用方法: bash scripts/commit_and_sync.sh \"commit message\""
  exit 1
fi

COMMIT_MSG="$1"
REPO_ROOT=$(git rev-parse --show-toplevel)

cd "$REPO_ROOT"

# ステージングと確認
if [ -z "$(git status --porcelain)" ]; then
  echo "✓ 変更なし"
  exit 0
fi

echo "📝 変更をステージング..."
git add -A

echo "💾 コミット: $COMMIT_MSG"
git commit -m "$COMMIT_MSG

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

echo "✓ コミット完了（push は GitHub MCP で行う）"
