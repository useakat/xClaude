#!/bin/bash
# Commit changes and sync to main branch
# Usage: bash scripts/commit_and_sync.sh "commit message"

set -e

if [ -z "$1" ]; then
  echo "❌ commit message が必要です"
  echo "使用方法: bash scripts/commit_and_sync.sh \"commit message\""
  exit 1
fi

COMMIT_MSG="$1"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
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

# mainブランチでない場合、mainにmerge
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
  echo "🔄 現在のブランチ ($CURRENT_BRANCH) をmainにmerge..."
  git checkout main
  git pull origin main
  git merge "$CURRENT_BRANCH" --no-edit
fi

echo "🚀 リモートにpush..."
git push origin main

echo "✓ 同期完了"
