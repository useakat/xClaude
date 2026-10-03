#!/bin/bash
# bio 転送サイトのアクセスログを日次集計して「bioクリック」シートへ (cron 実行)。
# cron: 40 5 * * * /bin/bash /root/xClaude/scripts/run_bio_clicks_ingest.sh
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
cd "$REPO_ROOT" || exit 1
mkdir -p "$REPO_ROOT/logs"
{
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 開始"
  python3 "$DIR/bio_clicks_ingest.py" "$@"
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 完了 (exit=$?)"
} >> "$REPO_ROOT/logs/bio_clicks.log" 2>&1
