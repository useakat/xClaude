#!/bin/bash
# mcp-gsheets 接続待機（SessionStart hook 用・リモート専用）
#
# コンテナ起動直後は MCP サーバー（node .../mcp-gsheets/dist/index.js）の起動が
# cold install（約14秒）で遅れ、その間に routine が最初の Sheets 呼び出しをすると
# 許可ルールと突合できず許可プロンプトが出る（2026-07-17 判明）。
# SessionStart hook は完了までセッション開始をブロックし、MCP spawn は hook と
# 並行で走るため、ここでサーバープロセスの起動を待ってからセッションを開始させる。
#
# - プロセス検出後、handshake 用に BUFFER 秒待って正常終了
# - TIMEOUT 秒待っても検出できない場合も正常終了する（セッション開始を壊さない）
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$REPO_ROOT/logs/mcp_gsheets_launch.log"
mkdir -p "$REPO_ROOT/logs" 2>/dev/null || true
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] wait: $*" >>"$LOG_FILE" 2>/dev/null || true; }

TIMEOUT=45
BUFFER=3

for i in $(seq 1 "$TIMEOUT"); do
  if pgrep -f 'mcp-gsheets/dist/index\.js' >/dev/null 2>&1; then
    log "server process up after ${i}s — buffer ${BUFFER}s"
    sleep "$BUFFER"
    exit 0
  fi
  sleep 1
done

log "server process not detected within ${TIMEOUT}s — continue anyway"
exit 0
