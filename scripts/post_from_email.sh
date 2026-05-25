#!/bin/bash
# Gmail メールを X に投稿する汎用スクリプト（全 shell 化版）
export PATH="/usr/local/bin:$PATH"
# Usage: bash post_from_email.sh [--dry-run] <件名キーワード> <howID> <ログファイル名>
# Example:
#   bash post_from_email.sh "【ワンポイント解説】" W003 x_post_xonepoint.log
#   bash post_from_email.sh --dry-run "【ワンポイント解説】" W003 x_post_xonepoint.log

set -uo pipefail

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi

SUBJECT_KEYWORD="${1:-}"
HOW_ID="${2:-}"
LOG_FILE="${3:-x_post.log}"

if [ -z "$SUBJECT_KEYWORD" ] || [ -z "$HOW_ID" ]; then
  echo "Usage: bash post_from_email.sh <件名キーワード> <howID> <ログファイル名>"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_PATH="$REPO_ROOT/logs/$LOG_FILE"
POSTED_LABEL_ID="Label_103"
TMP_IMAGE="/tmp/xpost_image.png"

mkdir -p "$REPO_ROOT/logs"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG_PATH"
}

if [ $DRY_RUN -eq 1 ]; then
  log "開始 [DRY RUN] (subject:$SUBJECT_KEYWORD, howID:$HOW_ID)"
else
  log "開始 (subject:$SUBJECT_KEYWORD, howID:$HOW_ID)"
fi

cd "$REPO_ROOT"

LOOP_COUNT=0
MAX_LOOPS=20

while [ $LOOP_COUNT -lt $MAX_LOOPS ]; do
  LOOP_COUNT=$((LOOP_COUNT + 1))

  # STEP 1: 未処理スレッド一覧を取得
  PARAMS=$(SUBJECT="$SUBJECT_KEYWORD" python3 -c "
import json, os
print(json.dumps({
    'userId': 'me',
    'q': f\"subject:{os.environ['SUBJECT']} in:inbox -label:投稿済み\",
    'maxResults': 50,
}))")
  THREADS_JSON=$(gws gmail users threads list --params "$PARAMS" 2>/dev/null)

  THREAD_ID=$(echo "$THREADS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ts = d.get('threads', [])
print(ts[-1]['id'] if ts else '')
")

  if [ -z "$THREAD_ID" ]; then
    log "投稿対象メールなし。ループ終了"
    break
  fi

  log "処理対象 thread_id=$THREAD_ID"

  # STEP 2: 本文と message_id を取得
  BODY_JSON=$(bash scripts/get_gmail_body.sh "$THREAD_ID" 2>/dev/null)
  if [ -z "$BODY_JSON" ]; then
    log "本文取得失敗。スキップしてラベル付与: $THREAD_ID"
    gws gmail users threads modify \
      --params "{\"userId\":\"me\",\"id\":\"$THREAD_ID\"}" \
      --json "{\"addLabelIds\":[\"$POSTED_LABEL_ID\"]}" 2>/dev/null >/dev/null
    continue
  fi
  MESSAGE_ID=$(echo "$BODY_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('message_id',''))")
  BODY=$(echo "$BODY_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('body',''))")

  # [投稿文] タグ抽出
  POST_TEXT=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py 投稿文 2>/dev/null || true)

  if [ -z "$POST_TEXT" ]; then
    log "[投稿文] タグなし／空 → ラベル付与のみ: $THREAD_ID"
    gws gmail users threads modify \
      --params "{\"userId\":\"me\",\"id\":\"$THREAD_ID\"}" \
      --json "{\"addLabelIds\":[\"$POSTED_LABEL_ID\"]}" 2>/dev/null >/dev/null
    continue
  fi

  # [リプ] タグ抽出（任意）
  REPLY_TEXT=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py リプ 2>/dev/null || true)

  # [ネタ番号] タグ抽出（任意・daily-xonepoint の下書きのみ存在）
  NETA_ID=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py ネタ番号 2>/dev/null || true)

  # 添付画像 DL
  HAS_IMAGE=0
  if bash scripts/download_gmail_attachment.sh "$MESSAGE_ID" "$TMP_IMAGE" >/dev/null 2>&1; then
    HAS_IMAGE=1
    log "添付画像あり"
  fi

  # ---- DRY RUN 分岐 ----
  if [ $DRY_RUN -eq 1 ]; then
    log "[DRY RUN] 投稿テキスト ($(echo -n "$POST_TEXT" | wc -m)字):"
    echo "----- POST_TEXT -----" | tee -a "$LOG_PATH"
    echo "$POST_TEXT" | tee -a "$LOG_PATH"
    echo "---------------------" | tee -a "$LOG_PATH"
    if [ -n "$REPLY_TEXT" ]; then
      log "[DRY RUN] リプテキスト ($(echo -n "$REPLY_TEXT" | wc -m)字):"
      echo "----- REPLY_TEXT -----" | tee -a "$LOG_PATH"
      echo "$REPLY_TEXT" | tee -a "$LOG_PATH"
      echo "----------------------" | tee -a "$LOG_PATH"
    fi
    if [ $HAS_IMAGE -eq 1 ]; then
      python3 scripts/post_to_x.py --dry-run --text "$POST_TEXT" --image "$TMP_IMAGE" 2>&1 | tee -a "$LOG_PATH"
    else
      python3 scripts/post_to_x.py --dry-run --text "$POST_TEXT" 2>&1 | tee -a "$LOG_PATH"
    fi
    log "[DRY RUN] ラベル付与・INBOX解除・record_output はスキップ"
    log "[DRY RUN] 1 ループで終了（同じメールが何度も処理されないように）"
    rm -f "$TMP_IMAGE"
    break
  fi
  # ---- DRY RUN 分岐おわり ----

  # X 投稿
  log "X 投稿実行..."
  if [ $HAS_IMAGE -eq 1 ]; then
    POST_OUTPUT=$(python3 scripts/post_to_x.py --text "$POST_TEXT" --image "$TMP_IMAGE" 2>&1)
  else
    POST_OUTPUT=$(python3 scripts/post_to_x.py --text "$POST_TEXT" 2>&1)
  fi
  POST_RC=$?
  echo "$POST_OUTPUT" >> "$LOG_PATH"

  TWEET_URL=$(echo "$POST_OUTPUT" | grep -oE 'https://x\.com/i/web/status/[0-9]+' | tail -1)
  TWEET_ID="${TWEET_URL##*/}"

  if [ $POST_RC -ne 0 ] || [ -z "$TWEET_URL" ]; then
    log "X 投稿失敗。ループ終了 (thread:$THREAD_ID)"
    rm -f "$TMP_IMAGE"
    break
  fi

  log "投稿成功: $TWEET_URL"

  # リプライ投稿
  if [ -n "$REPLY_TEXT" ] && [ -n "$TWEET_ID" ]; then
    log "リプ投稿実行..."
    REPLY_OUTPUT=$(python3 scripts/post_to_x.py --text "$REPLY_TEXT" --reply-to "$TWEET_ID" 2>&1)
    echo "$REPLY_OUTPUT" >> "$LOG_PATH"
  fi

  # ラベル付与＋INBOX削除
  gws gmail users threads modify \
    --params "{\"userId\":\"me\",\"id\":\"$THREAD_ID\"}" \
    --json "{\"addLabelIds\":[\"$POSTED_LABEL_ID\"],\"removeLabelIds\":[\"INBOX\"]}" 2>/dev/null >/dev/null

  # 投稿記録
  python3 scripts/record_output.py "$TWEET_URL" "$HOW_ID" "$NETA_ID" 2>&1 | tee -a "$LOG_PATH"

  rm -f "$TMP_IMAGE"

  # 1件処理したら終了（複数メールが溜まっていても最古の1件のみ投稿）
  log "1件処理完了。ループ終了"
  break
done

if [ $LOOP_COUNT -ge $MAX_LOOPS ]; then
  log "ループ上限 ($MAX_LOOPS) に到達したため終了"
fi

log "完了"
