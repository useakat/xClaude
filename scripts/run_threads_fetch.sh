#!/bin/bash
# Threads 投稿一覧の日次取得（毎朝5:00 cron）。fetch_threads_posts.py で API 取得→シート upsert。
# cron: 0 5 * * * /bin/bash /root/xClaude/scripts/run_threads_fetch.sh
export PATH="/usr/local/bin:$PATH"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO_ROOT/logs/threads_fetch.log"
mkdir -p "$REPO_ROOT/logs"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG"; }

log "Threads 取得 開始"
cd "$REPO_ROOT"
python3 scripts/fetch_threads_posts.py >> "$LOG" 2>&1
rc=$?
log "Threads 取得 完了 (rc=$rc)"
