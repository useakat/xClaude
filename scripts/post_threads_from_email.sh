#!/bin/bash
# 【threads投稿】メールを1件拾って Threads に投稿し、outputs に記録する。
# post_from_email.sh の Threads 版（本文＝[投稿文]／画像＝[画像URL]／セルフリプ＝[リプ]／リプ画像＝[リプ画像URL]／元X投稿URL＝[XURL]（任意・日報のカテゴリ判定用））。
# Usage: bash post_threads_from_email.sh [--dry-run]
export PATH="/usr/local/bin:$PATH"
set -uo pipefail

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then DRY_RUN=1; shift; fi

SUBJECT_KEYWORD="【threads投稿】"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_PATH="$REPO_ROOT/logs/threads_post.log"
POSTED_LABEL_ID="Label_103"
mkdir -p "$REPO_ROOT/logs"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG_PATH"; }

log "開始 (threads)"
cd "$REPO_ROOT"

# STEP 1: 未処理スレッド取得（クエリ失敗と0件を区別しリトライ）
PARAMS=$(SUBJECT="$SUBJECT_KEYWORD" python3 -c "
import json, os
print(json.dumps({'userId':'me','q':f\"subject:{os.environ['SUBJECT']} in:inbox -label:投稿済み\",'maxResults':50}))")
THREAD_ID=""
QUERY_OK=0
for attempt in 1 2 3; do
  RAW=$(gws gmail users threads list --params "$PARAMS" 2>/dev/null)
  THREAD_ID=$(printf '%s' "$RAW" | python3 -c "
import json, sys
data = sys.stdin.read()
i = data.find('{')
if i < 0: sys.exit(2)
try: d = json.loads(data[i:])
except Exception: sys.exit(2)
if isinstance(d, dict) and 'error' in d: sys.exit(3)
ts = d.get('threads', [])
print(ts[-1]['id'] if ts else '')
")
  rc=$?
  if [ $rc -eq 0 ]; then QUERY_OK=1; break; fi
  log "Gmail クエリ失敗 (rc=$rc, 試行 $attempt/3)。5秒後にリトライ..."
  sleep 5
done
if [ $QUERY_OK -ne 1 ]; then log "⚠ Gmail クエリが3回とも失敗。中断（要確認）。"; exit 1; fi
if [ -z "$THREAD_ID" ]; then log "投稿対象メールなし。終了"; exit 20; fi
log "処理対象 thread_id=$THREAD_ID"

# STEP 2: 本文取得
BODY_JSON=$(bash scripts/get_gmail_body.sh "$THREAD_ID" 2>/dev/null)
if [ -z "$BODY_JSON" ]; then
  log "本文取得失敗。ラベル付与してスキップ"
  gws gmail users threads modify --params "{\"userId\":\"me\",\"id\":\"$THREAD_ID\"}" --json "{\"addLabelIds\":[\"$POSTED_LABEL_ID\"]}" 2>/dev/null >/dev/null
  exit 1
fi
BODY=$(echo "$BODY_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('body',''))")

TEXT=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py 投稿文 2>/dev/null || true)
IMG=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py 画像URL 2>/dev/null || true)
REP=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py リプ 2>/dev/null || true)
REPIMG=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py リプ画像URL 2>/dev/null || true)
XURL=$(printf '%s' "$BODY" | python3 scripts/extract_tag.py XURL 2>/dev/null || true)

if [ -z "$TEXT" ]; then
  log "[投稿文] タグなし／空 → ラベル付与のみ: $THREAD_ID"
  gws gmail users threads modify --params "{\"userId\":\"me\",\"id\":\"$THREAD_ID\"}" --json "{\"addLabelIds\":[\"$POSTED_LABEL_ID\"]}" 2>/dev/null >/dev/null
  exit 1
fi

ARGS=(--text "$TEXT")
[ -n "$IMG" ] && ARGS+=(--image-url "$IMG")
[ -n "$REP" ] && ARGS+=(--reply-text "$REP")
[ -n "$REPIMG" ] && ARGS+=(--reply-image-url "$REPIMG")

# DRY RUN
if [ $DRY_RUN -eq 1 ]; then
  log "[DRY RUN] 分割プレビュー:"
  python3 scripts/post_threads.py --dry-run "${ARGS[@]}" 2>&1 | tee -a "$LOG_PATH"
  log "[DRY RUN] ラベル付与・記録はスキップ"
  exit 0
fi

# STEP 3: 投稿
log "Threads 投稿実行..."
POST_OUTPUT=$(python3 scripts/post_threads.py "${ARGS[@]}" 2>&1)
POST_RC=$?
echo "$POST_OUTPUT" >> "$LOG_PATH"
PERMALINK=$(printf '%s' "$POST_OUTPUT" | sed -n 's/^PERMALINK=//p' | tail -1)

if [ $POST_RC -ne 0 ] || [ -z "$PERMALINK" ]; then
  log "Threads 投稿失敗。終了 (thread:$THREAD_ID)"
  exit 1
fi
log "投稿成功: $PERMALINK"

# STEP 4: ラベル付与＋INBOX解除、outputs 記録
gws gmail users threads modify \
  --params "{\"userId\":\"me\",\"id\":\"$THREAD_ID\"}" \
  --json "{\"addLabelIds\":[\"$POSTED_LABEL_ID\"],\"removeLabelIds\":[\"INBOX\"]}" 2>/dev/null >/dev/null

RECORD_ARGS=("$PERMALINK")
[ -n "$XURL" ] && RECORD_ARGS+=(--x-url "$XURL")
python3 scripts/record_output.py "${RECORD_ARGS[@]}" 2>&1 | tee -a "$LOG_PATH"
log "完了"
