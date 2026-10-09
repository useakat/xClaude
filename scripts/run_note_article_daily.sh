#!/bin/bash
# note 記事ごとの「その日の PV・スキ」を note記事日次 シートに記録する (cron 実行)。
# cron: 55 5 * * * /bin/bash /root/xClaude/scripts/run_note_article_daily.sh
# 前日分に加え、転送クリック明細にある未取得の日付も埋める（--fill-detail）。
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
cd "$REPO_ROOT" || exit 1
mkdir -p "$REPO_ROOT/logs"
{
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 開始"
  flock -n /tmp/note_article_daily.lock python3 "$DIR/note_article_daily.py" --fill-detail "$@"
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 完了 (exit=$?)"
} >> "$REPO_ROOT/logs/note_article_daily.log" 2>&1
