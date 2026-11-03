#!/bin/bash
# 競合アカウントの投稿を毎日 1 件メールする (cron 実行)。対象シートは SHEET で指定。
# cron: 15 7 * * * /bin/bash /root/xClaude/scripts/run_x_competitor_daily_mail.sh
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
SHEET="ossanworld 2026-05"
LOCK="/tmp/x_competitor_daily_mail.lock"

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 前回の実行が継続中のためスキップ" >> "$REPO_ROOT/logs/x_competitor_mail.log"
  exit 0
fi

cd "$REPO_ROOT" || exit 1
python3 "$DIR/x_competitor_daily_mail.py" --sheet "$SHEET" "$@" >/dev/null 2>>"$REPO_ROOT/logs/x_competitor_mail.log"
