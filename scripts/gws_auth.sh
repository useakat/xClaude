#!/bin/bash
# gws auth login のラッパー。SSH トンネルコマンドと認証 URL を整形して出力する。
# 使い方: bash scripts/gws_auth.sh [--scopes "scope1,scope2,..."]
#
# Claude Code 向け: ブラウザ認証が必要な場面ではこのスクリプトを使い、
# 出力内容をそのままよーんに伝えること。

export PATH="/usr/local/bin:$PATH"

DEFAULT_SCOPES="email,profile,openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/gmail.modify"

SCOPES="$DEFAULT_SCOPES"
if [ "${1:-}" = "--scopes" ] && [ -n "${2:-}" ]; then
  SCOPES="$2"
fi

TMP_LOG=$(mktemp /tmp/gws_auth_XXXXXX.log)

# gws をバックグラウンド起動
gws auth login --scopes "$SCOPES" > "$TMP_LOG" 2>&1 &
GWS_PID=$!

# URL が出力されるまで待機（最大15秒）
AUTH_URL=""
PORT=""
for i in $(seq 1 30); do
  sleep 0.5
  AUTH_URL=$(grep -oE 'https://accounts\.google\.com/o/oauth2/auth[^ ]+' "$TMP_LOG" 2>/dev/null | head -1)
  if [ -n "$AUTH_URL" ]; then
    PORT=$(echo "$AUTH_URL" | grep -oE 'redirect_uri=http://localhost:([0-9]+)' | grep -oE '[0-9]+$')
    break
  fi
done

if [ -z "$AUTH_URL" ] || [ -z "$PORT" ]; then
  echo "❌ gws auth login の起動に失敗しました。ログ:"
  cat "$TMP_LOG"
  rm -f "$TMP_LOG"
  exit 1
fi

# VPS 公開 IP を取得
VPS_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || curl -s --max-time 5 icanhazip.com 2>/dev/null || echo "<VPS_IP>")

echo ""
echo "================================================"
echo "ブラウザ認証が必要です"
echo "================================================"
echo ""
echo "① よーんのターミナルで SSH トンネルを張る:"
echo "   ssh -L ${PORT}:localhost:${PORT} root@${VPS_IP}"
echo ""
echo "② ブラウザでこの URL を開く:"
echo "   ${AUTH_URL}"
echo ""
echo "トンネルを張って URL を開いたら、承認後に自動完了します。"
echo "================================================"
echo ""

# gws の完了を待機
wait $GWS_PID
GWS_RC=$?

rm -f "$TMP_LOG"

if [ $GWS_RC -eq 0 ]; then
  # トークンキャッシュをクリア
  rm -f ~/.config/gws/token_cache.json
  echo "✅ 認証完了。トークンキャッシュをクリアしました。"
  echo "   次のステップ: git commit -m \"infra: gws OAuth 再認証 ($(date '+%Y-%m-%d')\""
else
  echo "❌ gws auth login が異常終了しました (exit code: $GWS_RC)"
  exit 1
fi
