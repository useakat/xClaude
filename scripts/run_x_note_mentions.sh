#!/bin/bash
# 他人が note 記事の URL を貼った X 投稿を週次で収集する (cron 実行)。
# 検索 API は直近7日分なので週1回で取りこぼしなし。結果は logs/x_note_mentions.csv に追記。
# cron: 0 7 * * 0 /bin/bash /root/xClaude/scripts/run_x_note_mentions.sh
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
cd "$REPO_ROOT" || exit 1
python3 "$DIR/x_note_mentions.py" "$@" >/dev/null 2>>"$REPO_ROOT/logs/x_note_mentions.log"
