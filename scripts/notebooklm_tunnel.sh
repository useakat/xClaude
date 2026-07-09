#!/usr/bin/env bash
#
# NotebookLM SOCKS トンネル管理ヘルパー
#
# この環境の IP は NotebookLM にブロックされているため、別の Windows server
# (133.18.136.38) へ SSH SOCKS トンネルを張り、その IP 経由でアクセスする。
# 鍵認証済みなのでパスワード不要。トンネルが既に生きていれば何もしない（冪等）。
#
# 使い方:
#   bash scripts/notebooklm_tunnel.sh          # トンネル確認＋なければ起動
#   bash scripts/notebooklm_tunnel.sh --check   # 疎通確認まで実施（出口IP表示）
#   bash scripts/notebooklm_tunnel.sh --restart # 張り直し（既存を落として再起動）
#
# トンネル起動後の NotebookLM 実行例:
#   NOTEBOOKLM_SOCKS_PROXY=socks5://127.0.0.1:1080 python3 scripts/notebooklm_manager.py list

set -euo pipefail

PORT=1080
SSH_HOST="nbtunnel@133.18.136.38"
PROXY="socks5://127.0.0.1:${PORT}"

is_up() {
  ss -ltn 2>/dev/null | grep -q ":${PORT} "
}

start_tunnel() {
  echo "→ トンネル起動: ${SSH_HOST} (SOCKS5 127.0.0.1:${PORT})"
  ssh -fND "${PORT}" \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=accept-new \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    "${SSH_HOST}"
  # LISTEN になるまで少し待つ
  for _ in $(seq 1 10); do
    is_up && break
    sleep 0.5
  done
}

stop_tunnel() {
  # ポート1080をフォワードしている ssh プロセスのみを落とす
  pkill -f "ssh -fND ${PORT} " 2>/dev/null || true
  sleep 1
}

case "${1:-}" in
  --restart)
    stop_tunnel
    start_tunnel
    ;;
  *)
    if is_up; then
      echo "✓ トンネルは既に稼働中 (127.0.0.1:${PORT})"
    else
      start_tunnel
    fi
    ;;
esac

if ! is_up; then
  echo "✗ トンネル起動に失敗しました" >&2
  exit 1
fi

if [ "${1:-}" = "--check" ]; then
  echo "→ 出口IP確認:"
  ip=$(ALL_PROXY="${PROXY}" curl -s --max-time 20 https://api.ipify.org || echo "取得失敗")
  echo "   プロキシ経由の出口IP: ${ip}"
  if [ "${ip}" = "133.18.136.38" ]; then
    echo "✓ 想定どおり Windows server 経由です"
  else
    echo "⚠ 出口IPが想定 (133.18.136.38) と異なります" >&2
  fi
fi

echo "実行例: NOTEBOOKLM_SOCKS_PROXY=${PROXY} python3 scripts/notebooklm_manager.py list"
