#!/bin/bash
# mcp-gsheets 起動ラッパー（ローカル/リモート両対応の認証を整える）
# - 親プロセスから混入する GOOGLE_APPLICATION_CREDENTIALS（${HOME}付き不正パス）を除去する。
#   Google Auth Library は GOOGLE_APPLICATION_CREDENTIALS を最優先で掴むため、
#   これが残っていると GOOGLE_SERVICE_ACCOUNT_KEY より先に開こうとして認証に失敗する。
# - GOOGLE_SERVICE_ACCOUNT_KEY が空ならローカルの gcp JSON から補完する
#   （リモート環境では gcp/ が無いので、継承された env の KEY をそのまま使う）。
unset GOOGLE_APPLICATION_CREDENTIALS

KEY_FILE="$HOME/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json"
if [ -z "${GOOGLE_SERVICE_ACCOUNT_KEY:-}" ] && [ -f "$KEY_FILE" ]; then
  export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat "$KEY_FILE")"
fi

# @latest は spawn/reconnect のたびにレジストリ問い合わせを強制し、レジストリ不通時にハングして
# Claude Code 側の初期化タイムアウト（-32000 / Failed to reconnect）を招く。
# バージョン固定 + --prefer-offline でキャッシュ優先起動にし、再接続を高速・堅牢にする。
exec npx --prefer-offline -y mcp-gsheets@1.8.1
