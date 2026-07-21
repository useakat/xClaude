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

# 結果ステータス: none=投稿対象なし / posted=投稿成功 / failed=投稿試行失敗
RESULT="none"

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
  # gws クエリを実行し「クエリ失敗」と「正常に0件」を区別する。
  # 失敗（JSONなし/不正JSON/APIエラー応答）は最大3回リトライし、それでもダメなら
  # 中断（RESULT=failed=exit 1）にして無言スキップ（=対象なし扱い）を防ぐ。
  THREAD_ID=""
  QUERY_OK=0
  for attempt in 1 2 3; do
    RAW=$(gws gmail users threads list --params "$PARAMS" 2>/dev/null)
    THREAD_ID=$(printf '%s' "$RAW" | python3 -c "
import json, sys
data = sys.stdin.read()
i = data.find('{')          # 先頭の非JSON行（keyring 情報等）を飛ばす
if i < 0:
    sys.exit(2)             # JSON が無い → クエリ失敗
try:
    d = json.loads(data[i:])
except Exception:
    sys.exit(2)             # 不正 JSON → クエリ失敗
if isinstance(d, dict) and 'error' in d:
    sys.exit(3)             # API エラー応答 → クエリ失敗
ts = d.get('threads', [])
print(ts[-1]['id'] if ts else '')   # 空出力 = 正常に0件
")
    rc=$?
    if [ $rc -eq 0 ]; then
      QUERY_OK=1
      break
    fi
    log "Gmail クエリ失敗 (rc=$rc, 試行 $attempt/3)。5秒後にリトライ..."
    sleep 5
  done

  if [ $QUERY_OK -ne 1 ]; then
    log "⚠ Gmail クエリが3回とも失敗。投稿対象の有無を判定できないため中断（要確認・投稿は行わない）。"
    RESULT="failed"
    break
  fi

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
    if [ "${MIRROR_THREADS:-0}" = "1" ]; then
      log "[DRY RUN] Threads 転載も実行予定（本文＋画像はX投稿後に pbs.twimg.com から取得）"
      python3 scripts/post_threads.py --dry-run --text "$POST_TEXT" ${REPLY_TEXT:+--reply-text "$REPLY_TEXT"} 2>&1 | tee -a "$LOG_PATH"
    fi
    log "[DRY RUN] ラベル付与・INBOX解除・record_output はスキップ"
    log "[DRY RUN] 1 ループで終了（同じメールが何度も処理されないように）"
    rm -f "$TMP_IMAGE"
    RESULT="posted"
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
    RESULT="failed"
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

  # 投稿記録（本文のネタマーカーがあれば neta_id/thought_id も記録）
  #   マーカー: [ネタID]{シート}[{番号}][/ネタID]（W003 等） または ソース: {シート}[{番号}]（z01）
  #   thoughts → thought_id 列に ID のみ（例 T007）
  #   それ以外（onePointNeta/noteNeta/newsTopics）→ neta_id 列にシート名付きトークン（例 onePointNeta[15]）
  SRC_ARGS=$(printf '%s' "$BODY" | python3 -c "
import re, sys, shlex
body = sys.stdin.read()
m = re.search(r'\[ネタID\]\s*([A-Za-z]+)\[([^\]]+)\]\s*\[/ネタID\]', body)
if not m:
    m = re.search(r'ソース[:：]\s*([A-Za-z]+)\[([^\]]+)\]', body)
if m:
    sheet, _id = m.group(1), m.group(2)
    if sheet == 'thoughts':
        print('--thought-id ' + shlex.quote(_id))
    else:
        print('--neta-id ' + shlex.quote(f'{sheet}[{_id}]'))
" 2>/dev/null || true)
  eval python3 scripts/record_output.py "$TWEET_URL" "$HOW_ID" $SRC_ARGS 2>&1 | tee -a "$LOG_PATH"

  # ---- Threads 転載（MIRROR_THREADS=1 のときだけ・非致命）----
  # X投稿を Threads にも転載する。画像は pbs.twimg.com URL を syndication API で取得。
  # 失敗しても X投稿は成功済みなので警告のみ（exit code は変えない）。
  if [ "${MIRROR_THREADS:-0}" = "1" ]; then
    log "Threads 転載開始..."
    TH_IMG_URLS=$(python3 scripts/fetch_tweet_media.py "$TWEET_ID" 2>/dev/null || true)
    TH_ARGS=(--text "$POST_TEXT")
    [ -n "$TH_IMG_URLS" ] && TH_ARGS+=(--image-url "$TH_IMG_URLS")
    [ -n "$REPLY_TEXT" ] && TH_ARGS+=(--reply-text "$REPLY_TEXT")
    TH_OUTPUT=$(python3 scripts/post_threads.py "${TH_ARGS[@]}" 2>&1)
    echo "$TH_OUTPUT" >> "$LOG_PATH"
    TH_PERMALINK=$(printf '%s' "$TH_OUTPUT" | sed -n 's/^PERMALINK=//p' | tail -1)
    if [ -n "$TH_PERMALINK" ]; then
      log "Threads 転載成功: $TH_PERMALINK"
      python3 scripts/record_output.py "$TH_PERMALINK" --x-url "$TWEET_URL" 2>&1 | tee -a "$LOG_PATH"
    else
      log "⚠ Threads 転載失敗（X投稿は成功済み）"
    fi
  fi

  rm -f "$TMP_IMAGE"

  # 1件処理したら終了（複数メールが溜まっていても最古の1件のみ投稿）
  log "1件処理完了。ループ終了"
  RESULT="posted"
  break
done

if [ $LOOP_COUNT -ge $MAX_LOOPS ]; then
  log "ループ上限 ($MAX_LOOPS) に到達したため終了"
fi

# 終了コード: 0=投稿成功 / 20=投稿対象なし（フォールバック合図）/ 1=投稿試行失敗
case "$RESULT" in
  posted) EXIT_CODE=0 ;;
  none)   EXIT_CODE=20 ;;
  failed) EXIT_CODE=1 ;;
  *)      EXIT_CODE=1 ;;
esac

log "完了 (result=$RESULT, exit=$EXIT_CODE)"
exit $EXIT_CODE
