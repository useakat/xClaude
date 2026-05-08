#!/bin/bash
export PATH="/usr/local/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_PATH="$REPO_ROOT/logs/mond_letter_reply.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG_PATH"; }

log "mond-letter-reply 開始"

cd "$REPO_ROOT"
claude -p --model opus "/mond-letter-reply" >> "$LOG_PATH" 2>&1

log "mond-letter-reply 完了"
