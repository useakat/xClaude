#!/bin/bash
# bio 転送サイトのアクセスログを日次集計して「bioクリック」シートへ (cron 実行)。
# cron: 40 * * * * /bin/bash /root/xClaude/scripts/run_bio_clicks_ingest.sh   (毎時。引数なしなら今日と昨日を再集計。2026-11-21 日次→毎時)
export PATH="/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$DIR")"
cd "$REPO_ROOT" || exit 1
mkdir -p "$REPO_ROOT/logs"
{
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 開始"
  if [ "$#" -eq 0 ]; then
    # 今日（集計途中）と昨日（確定分の取りこぼし防止）を upsert する。日付単位で書き直すので何度走らせても同じ結果になる
    set -- --date "$(TZ=Asia/Tokyo date +%F)" --days 2
  fi
  python3 "$DIR/bio_clicks_ingest.py" "$@"
  echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] 完了 (exit=$?)"
} >> "$REPO_ROOT/logs/bio_clicks.log" 2>&1
