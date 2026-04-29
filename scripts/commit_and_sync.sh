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
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-master}

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

# デフォルトブランチでない場合、マージ
if [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
  echo "🔄 現在のブランチ ($CURRENT_BRANCH) を $DEFAULT_BRANCH にmerge..."
  git checkout "$DEFAULT_BRANCH"
  git pull origin "$DEFAULT_BRANCH"
  git merge "$CURRENT_BRANCH" --no-edit

  echo "🗑️  ブランチを削除..."
  git branch -d "$CURRENT_BRANCH"
  git push origin --delete "$CURRENT_BRANCH" 2>/dev/null || true
fi

echo "🚀 リモートにpush..."
git push origin "$DEFAULT_BRANCH"

echo "✓ 同期完了"
