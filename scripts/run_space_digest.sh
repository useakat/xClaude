#!/bin/bash
# 毎朝の宇宙ダイジェスト（cron 06:45 JST）
#   ① space_digest_fetch.py で新着を集めて候補ファイルを書く
#   ② claude -p "/space-digest <候補>" が選別・要約して本文ファイルを書く
#   ③ send_gmail.sh で本文を送る
# Usage: bash run_space_digest.sh [--dry-run]   # --dry-run: 状態を更新せず、メールも送らない
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_PATH="$REPO_ROOT/logs/space_digest.log"
OUT_DIR="$REPO_ROOT/logs/space_digest"
MAIL_TO="useakat@gmail.com"
DRY=""
[ "${1:-}" = "--dry-run" ] && DRY="--dry-run"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG_PATH"; }

exec 9>/tmp/space_digest.lock
if ! flock -n 9; then
  log "前回の実行が終わっていないので中止"
  exit 0
fi

cd "$REPO_ROOT" || exit 1
mkdir -p "$OUT_DIR"
TODAY="$(date '+%Y-%m-%d')"
DOW="$(python3 -c "import datetime;print('月火水木金土日'[datetime.date.today().weekday()])")"
CAND="$OUT_DIR/${TODAY}_candidates.md"
DIGEST="$OUT_DIR/${TODAY}_digest.txt"

send_mail() {  # $1 = 件名, $2 = 本文ファイル
  if [ -n "$DRY" ]; then
    log "dry-run: 送信しない（件名: $1）"
    return 0
  fi
  if bash "$REPO_ROOT/scripts/send_gmail.sh" --to "$MAIL_TO" --subject "$1" --body-file "$2" >> "$LOG_PATH" 2>&1; then
    log "送信完了: $1"
  else
    log "送信失敗: $1"
    return 1
  fi
}

log "宇宙ダイジェスト 開始 $DRY"

# ① 収集
python3 "$REPO_ROOT/scripts/space_digest_fetch.py" $DRY --out "$CAND" >> "$LOG_PATH" 2>&1
RC=$?
if [ "$RC" -eq 1 ]; then
  log "収集失敗（全ソース）"
  printf '【宇宙ダイジェスト】%s（%s）\n収集に失敗しました（全ソース取得不可）。logs/space_digest.log を確認してください。\n\n%s\n' \
    "$TODAY" "$DOW" "$(tail -n 30 "$LOG_PATH")" > "$DIGEST"
  send_mail "【宇宙ダイジェスト】${TODAY}（${DOW}）収集失敗" "$DIGEST"
  exit 1
fi
if [ "$RC" -eq 20 ]; then
  log "新着なし"
  printf '【宇宙ダイジェスト】%s（%s）\n新着なし（直近 48 時間に未読の新着がありませんでした）\n' "$TODAY" "$DOW" > "$DIGEST"
  send_mail "【宇宙ダイジェスト】${TODAY}（${DOW}）新着なし" "$DIGEST"
  exit 0
fi

# ② 選別・要約（claude -p）
rm -f "$DIGEST"
timeout 900 claude -p --model opus "/space-digest $CAND" >> "$LOG_PATH" 2>&1
log "claude -p 終了 rc=$?"
if [ ! -s "$DIGEST" ]; then
  log "本文ファイルが無い: $DIGEST"
  printf '【宇宙ダイジェスト】%s（%s）\n要約に失敗しました（本文ファイルが生成されませんでした）。候補は %s にあります。\n' \
    "$TODAY" "$DOW" "$CAND" > "$DIGEST"
  send_mail "【宇宙ダイジェスト】${TODAY}（${DOW}）要約失敗" "$DIGEST"
  exit 1
fi

# ③ 送信（件名 ＝ 1 行目 ＋ 2 行目の件数）
COUNTS="$(sed -n 2p "$DIGEST" | sed 's/（候補.*//; s/プレスリリース/プレス/')"
SUBJECT="【宇宙ダイジェスト】${TODAY}（${DOW}）${COUNTS}"
send_mail "$SUBJECT" "$DIGEST" || exit 1

# 60 日より古い日次ファイルを消す
find "$OUT_DIR" -type f -mtime +60 -delete 2>/dev/null

log "宇宙ダイジェスト 完了"
