#!/bin/bash
# 質問回答投稿 (毎日12時)
# cron: 0 12 * * * /bin/bash /root/xClaude/scripts/run_question_post.sh
exec /bin/bash "$(dirname "$0")/post_from_email.sh" "【質問回答】" W006 x_post_question.log
