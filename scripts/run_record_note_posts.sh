#!/bin/bash
export PATH="/usr/local/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_PATH="$REPO_ROOT/logs/record_note_posts.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG_PATH"; }

log "record-note-posts 開始"

cd "$REPO_ROOT"
claude -p --model opus "/record-note-posts" >> "$LOG_PATH" 2>&1

log "record-note-posts 完了"
