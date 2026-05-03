#!/bin/bash
# database/ の CSV 変更のみを commit & push する（remote session 用）
set -e

REPO=$(git rev-parse --show-toplevel)

cd "$REPO"

if git diff --quiet HEAD -- database/ && git diff --cached --quiet -- database/; then
  echo "database/ に変更はありません"
  exit 0
fi

git add database/
git commit -m "data: update database CSV"
git push
echo "✓ database/ の変更を push しました"
