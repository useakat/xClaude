#!/bin/bash
# X長文投稿 (毎日17時)
# cron: 0 17 * * * /bin/bash /root/xClaude/scripts/run_xlong_post.sh
exec /bin/bash "$(dirname "$0")/post_from_email.sh" "【X長文】" W001 x_post_xlong.log
