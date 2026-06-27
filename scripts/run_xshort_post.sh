#!/bin/bash
# X短文投稿 (cron 実行)
# cron 例: 0 6 * * * /bin/bash /root/xClaude/scripts/run_xshort_post.sh
exec /bin/bash "$(dirname "$0")/post_from_email.sh" "【X短文投稿】" z01 x_post_short.log
