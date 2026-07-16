#!/bin/bash
# X投稿一覧からランダム6件を選び【threads投稿】Gmail下書きを作る cron ラッパー(毎日 8時)。
# cron: 0 8 * * * /bin/bash /root/xClaude/scripts/run_threads_draft.sh
export PATH="/usr/local/bin:$PATH"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"

DIR="$(dirname "$0")"
cd "$DIR/.." || exit 1
# 前段: 親ポストURL(J列)の補完（セルフリプ紐づけ用。キャッシュにより新規行のみ照会）
python3 scripts/backfill_x_parent_urls.py >> logs/threads_draft.log 2>&1
python3 scripts/make_threads_draft.py --count 6 >> logs/threads_draft.log 2>&1
