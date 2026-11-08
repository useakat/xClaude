#!/bin/bash
# X / Threads 本体投稿の 24h インプ推移を記録 (cron 実行)。投稿から 3h は 15 分刻み、以降 1h 刻み。
# cron: */15 * * * * /bin/bash /root/xClaude/scripts/run_imp_timeline.sh
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
LOCK="/tmp/imp_timeline.lock"

# 多重起動防止（前回の実行が終わっていなければスキップ）
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 前回の実行が継続中のためスキップ" >> "$REPO_ROOT/logs/imp_timeline.log"
  exit 0
fi

cd "$REPO_ROOT" || exit 1
python3 "$DIR/imp_timeline.py" "$@" >/dev/null 2>>"$REPO_ROOT/logs/imp_timeline.log"
