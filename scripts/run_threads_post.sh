#!/bin/bash
# 【threads投稿】メールを Threads に投稿する cron ラッパー。
# cron: 0 9 * * * /bin/bash /root/xClaude/scripts/run_threads_post.sh （2026-11-12〜。再投稿の下書きを毎朝拾う）
# ほかに X 投稿 cron（06/12/17/20）が X に投稿が無かったときのフォールバックとしても呼ぶ。
export PATH="/usr/local/bin:$PATH"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"

DIR="$(dirname "$0")"
exec /bin/bash "$DIR/post_threads_from_email.sh"
