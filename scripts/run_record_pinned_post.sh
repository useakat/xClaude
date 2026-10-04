#!/bin/bash
# X の固定ポストを確認して「固定ポスト履歴」シートへ (cron 実行)。
# cron: 50 5 * * * /bin/bash /root/xClaude/scripts/run_record_pinned_post.sh
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
cd "$REPO_ROOT" || exit 1
mkdir -p "$REPO_ROOT/logs"
{
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 開始"
  python3 "$DIR/record_pinned_post.py" "$@"
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 完了 (exit=$?)"
} >> "$REPO_ROOT/logs/record_pinned_post.log" 2>&1
