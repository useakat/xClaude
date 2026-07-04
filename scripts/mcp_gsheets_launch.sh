#!/bin/bash
# mcp-gsheets 起動ラッパー（ローカル/リモート両対応の認証を整える）
# - 親プロセスから混入する GOOGLE_APPLICATION_CREDENTIALS（${HOME}付き不正パス）を除去する。
#   Google Auth Library は GOOGLE_APPLICATION_CREDENTIALS を最優先で掴むため、
#   これが残っていると GOOGLE_SERVICE_ACCOUNT_KEY より先に開こうとして認証に失敗する。
# - GOOGLE_SERVICE_ACCOUNT_KEY が空ならローカルの gcp JSON から補完する
#   （リモート環境では gcp/ が無いので、継承された env の KEY をそのまま使う）。
# - パス解決は $HOME 前提にせず、本スクリプト自身の場所から辿る（環境によって
#   $HOME がリポジトリの親ディレクトリと一致しないケースがあるため）。呼び出しは
#   cwd 非依存（`.mcp.json` から絶対パスで起動する）。
unset GOOGLE_APPLICATION_CREDENTIALS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

KEY_FILE="$PROJECT_DIR/gcp/charming-well-464402-u4-2cfb7bddf343.json"
if [ -z "${GOOGLE_SERVICE_ACCOUNT_KEY:-}" ] && [ -f "$KEY_FILE" ]; then
  export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat "$KEY_FILE")"
fi

# install 本体（バージョン固定ローカル prefix install ＋ .installed マーカー管理）は
# scripts/mcp_gsheets_install.sh に共通化した（SessionStart hook からも同じものを呼ぶ）。
bash "$SCRIPT_DIR/mcp_gsheets_install.sh"

VERSION="1.8.1"
PKG_DIR="$HOME/.cache/mcp-gsheets/$VERSION"
ENTRY="$PKG_DIR/node_modules/mcp-gsheets/dist/index.js"
LOG="$PROJECT_DIR/logs/mcp_gsheets_launch.log"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] launch: exec node $ENTRY" >> "$LOG" 2>/dev/null || true

exec node "$ENTRY"
