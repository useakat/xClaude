#!/bin/bash
# Threads 長期トークンの月次更新（60日失効対策）。App Secret 不要。
# cron: 0 4 1 * * /bin/bash /root/xClaude/scripts/run_threads_token_refresh.sh
export PATH="/usr/local/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO_ROOT/logs/threads_fetch.log"
mkdir -p "$REPO_ROOT/logs"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG"; }

log "Threads トークン更新 開始"
cd "$REPO_ROOT"
python3 scripts/threads_token_refresh.py >> "$LOG" 2>&1
rc=$?
log "Threads トークン更新 完了 (rc=$rc)"
