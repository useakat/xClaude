#!/bin/bash
# mcp-gsheets のローカル install（冪等・共通処理）。
# SessionStart hook（セッション開始時の事前ウォーム）と mcp_gsheets_launch.sh（MCP spawn 時）の
# 両方から呼ばれる。ロジックの二重管理を避けるためここに一本化する。
#
# 方式：バージョン固定のローカル prefix install。初回（キャッシュミス/新バージョン）だけ
#       online 解決し、以降は node で直接起動できる状態を作る。フレッシュなクラウドコンテナで
#       npm メタデータキャッシュが陳腐化していても ETARGET を踏まない（--prefer-offline を使わない）。
#
# SessionStart hook から同期実行されると、install 済み状態が「hook 完了後のコンテナキャッシュ」に
# 焼き込まれ、以降のセッションでは常にウォームな状態（0.02秒で skip）から始められる。
#
# パス解決は $HOME 決め打ちを避け、スクリプト自身の場所（BASH_SOURCE）からリポジトリルートを辿る
# （$HOME が repo の親ディレクトリと一致しない環境でも動作させるため）。
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$REPO_ROOT/logs/mcp_gsheets_launch.log"
mkdir -p "$REPO_ROOT/logs" 2>/dev/null || true

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] install: $*" >>"$LOG_FILE" 2>/dev/null || true; }

VERSION="1.8.1"
PKG_DIR="$HOME/.cache/mcp-gsheets/$VERSION"
MARKER="$PKG_DIR/.installed"

if [ -f "$MARKER" ]; then
  log "already warm ($VERSION) — skip"
  exit 0
fi

log "cold install start ($VERSION)"
# 中断された部分インストールを掴まないよう、毎回まっさらから入れ直す。
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"
# stdout（JSON-RPC 専用）を汚さないよう install 出力は全て stderr へ流す。
npm install --prefix "$PKG_DIR" --no-save --no-audit --no-fund --loglevel=error \
  "mcp-gsheets@$VERSION" 1>&2
touch "$MARKER"
log "cold install done ($VERSION)"
