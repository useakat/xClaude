#!/bin/bash
# sheets_values.py が使う Python 依存（gspread / google-auth）のローカル install（冪等）。
# mcp_gsheets_install.sh と同じ方式：バージョン固定で $HOME/.cache 配下に入れ、
# マーカーで2回目以降をスキップする。SessionStart hook（リモート）からの
# 事前ウォームと、sheets_values.py からのオンデマンド実行の両方に対応する。
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$REPO_ROOT/logs/sheets_pydeps_install.log"
mkdir -p "$REPO_ROOT/logs" 2>/dev/null || true

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >>"$LOG_FILE" 2>/dev/null || true; }

# バージョンを上げたら PKG_DIR が変わり自動で入れ直しになる（sheets_values.py 側の定数と一致させること）
VERSION="2"
PKG_DIR="$HOME/.cache/xclaude-pydeps/$VERSION"
MARKER="$PKG_DIR/.installed"

if [ -f "$MARKER" ]; then
  log "already warm ($VERSION) — skip"
  exit 0
fi

log "cold install start ($VERSION)"
# 中断された部分インストールを掴まないよう、毎回まっさらから入れ直す。
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"
# stdout を汚さないよう install 出力は stderr へ。
# Debian 系の externally-managed 環境では --break-system-packages が要る（--target なので system は触らない）。
# cryptography も同梱する（コンテナのシステム版が壊れており、google-auth が掴むと落ちるため）
PKGS='gspread==6.1.2 google-auth==2.35.0 cryptography==43.0.1'
python3 -m pip install --target "$PKG_DIR" --no-cache-dir --quiet $PKGS 1>&2 \
  || python3 -m pip install --break-system-packages --target "$PKG_DIR" --no-cache-dir --quiet $PKGS 1>&2
touch "$MARKER"
log "cold install done ($VERSION)"
