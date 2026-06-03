#!/bin/bash
# 認証トークン一括チェック。問題があれば LINE → Gmail → ログ の順で通知。
# cron: 0 2 * * * /bin/bash /root/xClaude/scripts/check_auth.sh
export PATH="/usr/local/bin:$PATH"

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/logs/check_auth.log"
ERRORS=()

mkdir -p "$REPO/logs"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG"; }

log "--- 認証チェック開始 ---"

# --- 1. gws ---
GWS_VALID=$(gws auth status 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin).get('token_valid', False))" 2>/dev/null)
if [ "$GWS_VALID" = "True" ]; then
  log "✅ gws: OK"
else
  log "❌ gws: トークン切れ（再認証: gws auth login -s gmail）"
  ERRORS+=("gws OAuth トークン切れ → gws auth login -s gmail")
fi

# --- 2. Drive token ---
DRIVE_OK=$(python3 -c "
import json
from pathlib import Path
try:
    d = json.loads(Path('$REPO/gcp/drive_token.json').read_text())
    print('ok' if d.get('refresh_token') else 'no_refresh_token')
except Exception as e:
    print(f'error: {e}')
" 2>/dev/null)
if [ "$DRIVE_OK" = "ok" ]; then
  log "✅ Drive token: OK"
else
  log "❌ Drive token: $DRIVE_OK"
  ERRORS+=("Drive OAuth トークン切れ（gcp/drive_token.json を確認）")
fi

# --- 3. X API ---
X_OK=$(python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('$REPO/.env')
import tweepy
try:
    tweepy.Client(
        consumer_key=os.getenv('X_OAUTH_CONSUMER_KEY'),
        consumer_secret=os.getenv('X_OAUTH_CONSUMER_SECRET'),
        access_token=os.getenv('X_OAUTH_ACCESS_TOKEN'),
        access_token_secret=os.getenv('X_OAUTH_ACCESS_TOKEN_SECRET'),
    ).get_me()
    print('ok')
except Exception as e:
    print(f'error: {e}')
" 2>/dev/null)
if [ "$X_OK" = "ok" ]; then
  log "✅ X API: OK"
else
  log "❌ X API: $X_OK"
  ERRORS+=("X API トークン無効（.env の X_OAUTH_* を確認）")
fi

# --- 4. LINE token（ping 兼チェック）---
LINE_OK=$(python3 "$REPO/scripts/send_line.py" \
  "[xClaude] 認証チェック ping $(date '+%m/%d %H:%M')" 2>/dev/null \
  && echo "ok" || echo "error")
if [ "$LINE_OK" = "ok" ]; then
  log "✅ LINE: OK"
else
  log "❌ LINE: トークン無効（.env の LINE_CHANNEL_ACCESS_TOKEN を確認）"
  ERRORS+=("LINE トークン無効（.env の LINE_CHANNEL_ACCESS_TOKEN を確認）")
fi

# --- LINE 通知（エラーがある場合のみ）---
if [ ${#ERRORS[@]} -gt 0 ] && [ "$LINE_OK" = "ok" ]; then
  LINE_MSG="[xClaude] 認証トークン切れ $(date '+%Y-%m-%d %H:%M JST')"$'\n'
  for e in "${ERRORS[@]}"; do LINE_MSG+="・$e"$'\n'; done
  python3 "$REPO/scripts/send_line.py" "$LINE_MSG" 2>/dev/null \
    || log "LINE 通知失敗"
fi

# --- Gmail 通知（常に送信）---
if [ ${#ERRORS[@]} -gt 0 ]; then
  MAIL_SUBJECT="⚠️ [xClaude] 認証チェック — エラーあり $(date '+%Y-%m-%d %H:%M JST')"
else
  MAIL_SUBJECT="✅ [xClaude] 認証チェック完了 $(date '+%Y-%m-%d %H:%M JST')"
fi

MAIL_BODY="認証チェック結果 $(date '+%Y-%m-%d %H:%M JST')

gws        : $([ "$GWS_VALID" = "True" ] && echo "✅ OK" || echo "❌ トークン切れ")
Drive token: $([ "$DRIVE_OK" = "ok" ] && echo "✅ OK" || echo "❌ $DRIVE_OK")
X API      : $([ "$X_OK" = "ok" ] && echo "✅ OK" || echo "❌ $X_OK")
LINE       : $([ "$LINE_OK" = "ok" ] && echo "✅ OK" || echo "❌ トークン無効")
"

if [ ${#ERRORS[@]} -gt 0 ]; then
  MAIL_BODY+=$'\n'"--- エラー詳細 ---"$'\n'
  for e in "${ERRORS[@]}"; do MAIL_BODY+="・$e"$'\n'; done
fi

python3 "$REPO/scripts/send_gmail_direct.py" \
  --subject "$MAIL_SUBJECT" --body "$MAIL_BODY" 2>/dev/null \
  && log "✅ Gmail 送信完了" \
  || log "❌ Gmail 送信失敗"

log "チェック完了 (エラー数: ${#ERRORS[@]})"
