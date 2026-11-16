#!/bin/bash
# postcal（X 投稿の予約カレンダー）をサーバーに配備する（要 root）。
#   1. systemd ユニット postcal.service を置いて起動（127.0.0.1:8787 で uvicorn）
#   2. Caddy に post.usephys.net の reverse_proxy（Basic 認証）を反映（redirect_build.py --apply）
# 前提:
#   - .env に POSTCAL_BASIC_AUTH='yohn:<caddy hash-password --plaintext <パスワード> の出力>' がある
#   - Cloudflare に post.usephys.net → 133.18.181.39 の A レコード（プロキシ OFF）がある
#     （無いと redirect_build.py がそのホストを除外して警告する。追加後にもう一度このスクリプトを実行）
# 使い方: bash scripts/postcal_install.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
UNIT_SRC="$REPO_ROOT/postcal/postcal.service"
UNIT_DST="/etc/systemd/system/postcal.service"

if [ "$(id -u)" -ne 0 ]; then echo "root で実行してください"; exit 1; fi

if ! grep -q '^POSTCAL_BASIC_AUTH=' "$REPO_ROOT/.env" 2>/dev/null; then
  echo "❌ .env に POSTCAL_BASIC_AUTH がありません。次で作って追記してください:"
  echo "   caddy hash-password --plaintext '<パスワード>'"
  echo "   → .env に POSTCAL_BASIC_AUTH='yohn:<出力>'（単引用符）"
  exit 1
fi

mkdir -p "$REPO_ROOT/postcal/data/media"
install -m 644 "$UNIT_SRC" "$UNIT_DST"
systemctl daemon-reload
systemctl enable --now postcal
sleep 1
systemctl --no-pager --lines=5 status postcal || true
if curl -fsS http://127.0.0.1:8787/healthz >/dev/null; then
  echo "✅ postcal が 127.0.0.1:8787 で応答しています"
else
  echo "❌ postcal が応答しません。journalctl -u postcal -n 50 を確認"; exit 1
fi

python3 "$DIR/redirect_build.py" --apply
echo "完了。https://post.usephys.net/ をブラウザで開いて Basic 認証を確認してください"
