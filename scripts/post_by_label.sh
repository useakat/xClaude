#!/bin/bash
# 投稿時間帯ラベル（<時>時投稿）が付いたメールを、件名を問わずその枠で X に投稿する。
# 各枠の cron ラッパー（run_*_post.sh）が従来の件名検索の前に呼ぶ。
# Usage: bash post_by_label.sh [--dry-run] <時>      例: bash post_by_label.sh 17
# 終了コード: 0=投稿成功 / 20=ラベル付きの投稿対象なし / 1=投稿試行失敗
# 件名 4 種を順に探し、最初に見つかった 1 件だけ投稿する（howID・ログは件名で決まる）。
export PATH="/usr/local/bin:$PATH"

DRY=""
if [ "${1:-}" = "--dry-run" ]; then
  DRY="--dry-run"
  shift
fi
HOUR="${1:-}"
case "$HOUR" in
  6|12|17|20) ;;
  *) echo "Usage: bash post_by_label.sh [--dry-run] <6|12|17|20>"; exit 1 ;;
esac
MY_LABEL="${HOUR}時投稿"
DIR="$(dirname "$0")"

# 件名キーワード|howID|ログファイル名
TARGETS='【ワンポイント解説】|W003|x_post_xonepoint.log
【質問回答】|W006|x_post_question.log
【X長文】|W001|x_post_xlong.log
【X短文投稿】|z01|x_post_short.log'

rc=20
while IFS='|' read -r SUBJECT HOW_ID LOG_FILE; do
  [ -z "$SUBJECT" ] && continue
  # shellcheck disable=SC2086
  /bin/bash "$DIR/post_from_email.sh" $DRY --label "$MY_LABEL" "$SUBJECT" "$HOW_ID" "$LOG_FILE"
  rc=$?
  # 0=投稿した / 1=失敗 → ここで終える（1 枠 1 件・失敗時は次に進まない）
  if [ "$rc" -ne 20 ]; then
    exit $rc
  fi
done <<< "$TARGETS"
exit 20
