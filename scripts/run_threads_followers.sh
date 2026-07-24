#!/bin/bash
# Threads フォロワ数を「日次記録」シートの前日行 V列に記録する cron ラッパー（毎朝5:30・GAS 5:00 の後）。
# cron: 30 5 * * * /bin/bash /root/xClaude/scripts/run_threads_followers.sh
export PATH="/usr/local/bin:$PATH"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"

DIR="$(dirname "$0")"
cd "$DIR/.." || exit 1
python3 scripts/record_threads_followers.py >> logs/threads_followers.log 2>&1
