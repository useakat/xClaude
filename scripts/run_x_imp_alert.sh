#!/bin/bash
# X 投稿のインプ監視 (cron 実行)。投稿から3時間以内に1,000インプ到達でメール通知。
# cron: */10 * * * * /bin/bash /root/xClaude/scripts/run_x_imp_alert.sh
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
LOCK="/tmp/x_imp_alert.lock"

# 多重起動防止（前回の実行が終わっていなければスキップ）
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 前回の実行が継続中のためスキップ" >> "$REPO_ROOT/logs/x_imp_alert.log"
  exit 0
fi

cd "$REPO_ROOT" || exit 1
python3 "$DIR/x_imp_alert.py" "$@" >/dev/null 2>>"$REPO_ROOT/logs/x_imp_alert.log"
