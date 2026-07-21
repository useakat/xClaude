#!/bin/bash
# X長文投稿 (毎日17時)。投稿対象が無ければ X短文投稿(z01)を代替投稿する。
# cron: 0 17 * * * /bin/bash /root/xClaude/scripts/run_xlong_post.sh
export MIRROR_THREADS=1  # X投稿を Threads にも転載する
DIR="$(dirname "$0")"
/bin/bash "$DIR/post_from_email.sh" "【X長文】" W001 x_post_xlong.log
rc=$?
# rc=20 → 投稿対象なし。X短文投稿を代替投稿（rc=1 の投稿失敗時は代替しない）
if [ "$rc" -eq 20 ]; then
  /bin/bash "$DIR/post_from_email.sh" "【X短文投稿】" z01 x_post_short.log
  rc=$?
fi
# X投稿が一切なかった（rc=20）→ Threads 下書きをフォールバック投稿
if [ "$rc" -eq 20 ]; then
  /bin/bash "$DIR/run_threads_post.sh"
fi
