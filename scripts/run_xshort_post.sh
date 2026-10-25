#!/bin/bash
# X短文投稿 (cron 実行)。X投稿を Threads にも転載する。投稿対象が無ければ Threads 下書きを代替投稿。
# cron: 0 20 * * * /bin/bash /root/xClaude/scripts/run_xshort_post.sh
export MIRROR_THREADS=1  # X投稿を Threads にも転載する
DIR="$(dirname "$0")"
# 投稿時間帯ラベル（20時投稿）が付いたメールを件名を問わず先に投稿する
/bin/bash "$DIR/post_by_label.sh" 20
rc=$?
if [ "$rc" -ne 20 ]; then exit $rc; fi   # 投稿した／失敗 → 従来の件名検索に進まない
# 従来の件名検索（post_from_email.sh は時刻ラベル付きのメールを除外する）
/bin/bash "$DIR/post_from_email.sh" "【X短文投稿】" z01 x_post_short.log
rc=$?
# X投稿が一切なかった（rc=20）→ Threads 下書きをフォールバック投稿
if [ "$rc" -eq 20 ]; then
  /bin/bash "$DIR/run_threads_post.sh"
fi
