#!/bin/bash
# Threads 低 views 期（7/24〜9/23）の投稿を順番に再投稿するための【threads投稿】下書きを 1 本作る cron ラッパー。
# cron: 0 18 * * * /bin/bash /root/xClaude/scripts/run_threads_repost_draft.sh
# 投稿は 09:00 の run_threads_post.sh（と X 投稿が無い時のフォールバック）が受信箱の【threads投稿】を拾って行う。
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
LOG_PATH="$REPO_ROOT/logs/threads_repost_draft.log"
LOCK="/tmp/threads_repost_draft.lock"
MAIL_TO="useakat@gmail.com"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat "$REPO_ROOT/gcp/charming-well-464402-u4-2cfb7bddf343.json" 2>/dev/null)"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" >> "$LOG_PATH"; }

exec 9>"$LOCK"
if ! flock -n 9; then
  log "前回の実行が継続中のためスキップ"
  exit 0
fi

cd "$REPO_ROOT" || exit 1
python3 "$DIR/make_threads_repost_draft.py" "$@" >> "$LOG_PATH" 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then
  log "下書き作成に失敗 (rc=$RC)。エラー通知を送信"
  BODY="$(mktemp)"
  printf 'Threads 再投稿の下書き作成に失敗しました (rc=%s)。\n\n直近のログ:\n%s\n' "$RC" "$(tail -n 30 "$LOG_PATH")" > "$BODY"
  bash "$REPO_ROOT/scripts/send_gmail.sh" --to "$MAIL_TO" --subject "【threads再投稿】下書き作成失敗" --body-file "$BODY" >> "$LOG_PATH" 2>&1
  rm -f "$BODY"
fi
exit $RC
