#!/bin/bash
# ワンポイント解説投稿 (毎朝6時)。投稿対象が無ければ X短文投稿(z01)を代替投稿する。
# cron: 0 6 * * * /bin/bash /root/xClaude/scripts/run_xonepoint_post.sh
DIR="$(dirname "$0")"
/bin/bash "$DIR/post_from_email.sh" "【ワンポイント解説】" W003 x_post_xonepoint.log
rc=$?
# rc=20 → 投稿対象なし。X短文投稿を代替投稿（rc=1 の投稿失敗時は代替しない）
if [ "$rc" -eq 20 ]; then
  /bin/bash "$DIR/post_from_email.sh" "【X短文投稿】" z01 x_post_short.log
fi
