#!/bin/bash
# ワンポイント解説投稿 (毎朝6時)
# cron: 0 6 * * * /bin/bash /root/xClaude/scripts/run_xonepoint_post.sh
exec /bin/bash "$(dirname "$0")/post_from_email.sh" "【ワンポイント解説】" W003 x_post_xonepoint.log
