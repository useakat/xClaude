#!/bin/bash
# mcp-gsheets 起動ラッパー（ローカル/リモート両対応の認証を整える）
# - 親プロセスから混入する GOOGLE_APPLICATION_CREDENTIALS（${HOME}付き不正パス）を除去する。
#   Google Auth Library は GOOGLE_APPLICATION_CREDENTIALS を最優先で掴むため、
#   これが残っていると GOOGLE_SERVICE_ACCOUNT_KEY より先に開こうとして認証に失敗する。
# - GOOGLE_SERVICE_ACCOUNT_KEY が空ならローカルの gcp JSON から補完する
#   （リモート環境では gcp/ が無いので、継承された env の KEY をそのまま使う）。
# - 呼び出しは cwd 非依存にすること（`.mcp.json` から絶対パスで起動する）。本スクリプト内の
#   パスも $HOME 基準で cwd に依存しない。
unset GOOGLE_APPLICATION_CREDENTIALS

KEY_FILE="$HOME/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json"
if [ -z "${GOOGLE_SERVICE_ACCOUNT_KEY:-}" ] && [ -f "$KEY_FILE" ]; then
  export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat "$KEY_FILE")"
fi

# 起動方式（案2: 初回のみ online 取得 → 以降はローカルから直接起動）
#
# 旧方式は `npx --prefer-offline -y mcp-gsheets@1.8.1` だったが、フレッシュなクラウド
# コンテナでは npm メタデータキャッシュが陳腐化しており、transitive 依存が新しい版
# （例: qs@^6.15.2）を要求すると --prefer-offline が古いキャッシュを掴んで
# 「No matching version found（ETARGET）」で install ごと失敗し、サーバが起動せず
# MCP が "still connecting" のまま接続不能になっていた。--prefer-offline を単に外して
# `npx -y` にするだけでも ETARGET は避けられるが、再接続のたびに npx がレジストリを
# 引きに行く余地が残る（-32000 ハングの遠因）。
#
# ここではバージョン固定のローカル prefix にワンショット install し、以降は node で
# エントリを直接 exec する。
#   - 初回（＝キャッシュミス / 新バージョン）だけ online 解決するので、陳腐キャッシュ
#     問題を回避できる。
#   - 2回目以降の spawn/reconnect は npm/レジストリを一切介さず node 起動だけなので
#     速く、レジストリ不通でもハングしない（旧 --prefer-offline の狙いも満たす）。
#   - install の進捗ログは stderr に流し、stdout（JSON-RPC 専用）を汚さない。
VERSION="1.8.1"
PKG_DIR="$HOME/.cache/mcp-gsheets/$VERSION"
ENTRY="$PKG_DIR/node_modules/mcp-gsheets/dist/index.js"
MARKER="$PKG_DIR/.installed"

if [ ! -f "$MARKER" ]; then
  # 中断された部分インストールを掴まないよう、毎回まっさらから入れ直す。
  rm -rf "$PKG_DIR"
  mkdir -p "$PKG_DIR"
  # stdout を汚さないよう install 出力は全て stderr へ。
  npm install --prefix "$PKG_DIR" --no-save --no-audit --no-fund --loglevel=error \
    "mcp-gsheets@$VERSION" 1>&2
  touch "$MARKER"
fi

exec node "$ENTRY"
