#!/bin/bash
# mcp-gsheets 起動ラッパー（ローカル/リモート両対応の認証を整える）
# - 親プロセスから混入する GOOGLE_APPLICATION_CREDENTIALS（${HOME}付き不正パス）を除去する。
#   Google Auth Library は GOOGLE_APPLICATION_CREDENTIALS を最優先で掴むため、
#   これが残っていると GOOGLE_SERVICE_ACCOUNT_KEY より先に開こうとして認証に失敗する。
# - GOOGLE_SERVICE_ACCOUNT_KEY が空ならローカルの gcp JSON から補完する
#   （リモート環境では gcp/ が無いので、継承された env の KEY をそのまま使う）。
# - install は mcp_gsheets_install.sh に一本化（SessionStart hook と共通）。ここでは
#   install を確実に済ませてから node でエントリを直接 exec するだけ。
# - 呼び出しは cwd 非依存（`.mcp.json` から絶対パスで起動する）。本スクリプト内のパスは
#   $HOME 決め打ちを避け、スクリプト自身の場所（BASH_SOURCE）からリポジトリルートを辿る。
set -u
unset GOOGLE_APPLICATION_CREDENTIALS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$REPO_ROOT/logs/mcp_gsheets_launch.log"
mkdir -p "$REPO_ROOT/logs" 2>/dev/null || true
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] launch: $*" >>"$LOG_FILE" 2>/dev/null || true; }

KEY_FILE="$REPO_ROOT/gcp/charming-well-464402-u4-2cfb7bddf343.json"
if [ -z "${GOOGLE_SERVICE_ACCOUNT_KEY:-}" ] && [ -f "$KEY_FILE" ]; then
  export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat "$KEY_FILE")"
fi

VERSION="1.8.1"
ENTRY="$HOME/.cache/mcp-gsheets/$VERSION/node_modules/mcp-gsheets/dist/index.js"

# install を確実に済ませる（ウォームなら即 skip）。出力は install 側で stderr に流れる。
log "ensure install"
bash "$SCRIPT_DIR/mcp_gsheets_install.sh"

log "node exec: $ENTRY"
exec node "$ENTRY"
