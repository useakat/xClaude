#!/bin/bash
# 毎朝6時に Gmail の【ワンポイント解説】メールを X に投稿する
# cron: 0 6 * * * /bin/bash /root/xClaude/scripts/run_x_post.sh >> /root/xClaude/logs/x_post.log 2>&1

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DATE=$(date '+%Y-%m-%d %H:%M:%S JST')

echo "[$LOG_DATE] x-post-from-email 開始"

cd "$REPO_ROOT"

/usr/bin/claude -p "
以下の手順を実行してください。

## 手順

### STEP 1: 未処理メールを検索
Gmail MCP で以下のクエリで検索する：
クエリ: subject:【ワンポイント解説】 -label:投稿済み

### STEP 2: メールがなければ終了
投稿対象メールが見つからなければ「投稿対象メールなし」と出力して終了する。

### STEP 3: 本文と添付画像を取得
最新1件のスレッドを取得し：
1. 本文から [投稿文] と [/投稿文] で囲まれたテキストを抽出する
2. 添付画像（PNG/JPG）があれば /tmp/xpost_image.png に保存する

### STEP 4: X に投稿
画像ありの場合：
python3 $REPO_ROOT/scripts/post_to_x.py --text \"（抽出したテキスト）\" --image /tmp/xpost_image.png

画像なしの場合：
python3 $REPO_ROOT/scripts/post_to_x.py --text \"（抽出したテキスト）\"

### STEP 5: 「投稿済み」ラベルを付与
Gmail MCP で対象メールに「投稿済み」ラベルを付ける。
ラベルが存在しない場合は先に作成してから付ける。

### STEP 6: 完了
投稿した X の URL とメールの件名を出力する。
" --allowedTools "Bash,mcp__claude_ai_Gmail__search_threads,mcp__claude_ai_Gmail__get_thread,mcp__claude_ai_Gmail__list_labels,mcp__claude_ai_Gmail__create_label,mcp__claude_ai_Gmail__label_message,mcp__claude_ai_Gmail__label_thread"

echo "[$LOG_DATE] x-post-from-email 完了"
