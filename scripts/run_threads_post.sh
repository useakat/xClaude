#!/bin/bash
# 【threads投稿】メールを Threads に投稿する cron ラッパー（毎日 7/12/17/20 時）。
# cron: 0 7,12,17,20 * * * /bin/bash /root/xClaude/scripts/run_threads_post.sh
export PATH="/usr/local/bin:$PATH"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"

DIR="$(dirname "$0")"
exec /bin/bash "$DIR/post_threads_from_email.sh"
