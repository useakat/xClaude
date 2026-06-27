#!/bin/bash
# z01 X短文投稿の Gmail 下書き作成 (cron 実行)
# projects/z01/spec.md の制作フロー（STEP 1〜7）を無人で回し、
# 【X短文投稿】件名の Gmail 下書きを1件作成する（投稿はしない）。
# cron 例: 0 8 * * * /bin/bash /root/xClaude/scripts/run_xshort_draft.sh
export PATH="/usr/local/bin:$PATH"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_PATH="$REPO_ROOT/logs/xshort_draft.log"
mkdir -p "$REPO_ROOT/logs"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG_PATH"; }

log "z01 短文下書き作成 開始"

cd "$REPO_ROOT"
claude -p --model opus "projects/z01/spec.md を Read し、作業フォルダを projects/z01 として、その制作フロー（STEP 1〜7）に完全自動で従って X短文投稿の Gmail 下書きを1件作成して。ユーザー確認・承認は不要。" >> "$LOG_PATH" 2>&1

log "z01 短文下書き作成 完了"
