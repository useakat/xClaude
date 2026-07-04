#!/bin/bash
# mcp-gsheets のバージョン固定ローカル install（冪等）。
# mcp_gsheets_launch.sh と SessionStart hook の両方から呼ばれる共通処理として切り出した。
# SessionStart hook（同期実行）から呼ぶことで、Claude Code on the web のコンテナ状態
# キャッシュに install 済み状態を焼き込み、次回以降のセッションでの
# 「フレッシュコンテナのコールド install が MCP 接続タイムアウトに間に合わない」
# レースコンディションを避ける狙い。
# パス解決は $HOME 前提にせず、本スクリプト自身の場所から辿る（環境によって
# $HOME がリポジトリの親ディレクトリと一致しないケースがあるため）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

VERSION="1.8.1"
PKG_DIR="$HOME/.cache/mcp-gsheets/$VERSION"
MARKER="$PKG_DIR/.installed"
LOG="$PROJECT_DIR/logs/mcp_gsheets_launch.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] install: $1" >> "$LOG" 2>/dev/null || true; }

if [ -f "$MARKER" ]; then
  log "already warm ($PKG_DIR)"
  exit 0
fi

log "start (cold cache, $PKG_DIR)"
# 中断された部分インストールを掴まないよう、毎回まっさらから入れ直す。
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"
# stdout を汚さないよう install 出力は全て stderr へ。
npm install --prefix "$PKG_DIR" --no-save --no-audit --no-fund --loglevel=error \
  "mcp-gsheets@$VERSION" 1>&2
touch "$MARKER"
log "done"
