#!/bin/bash
# Gmail メールを X に投稿する汎用スクリプト
# Usage: bash post_from_email.sh <件名キーワード> <howID> <ログファイル名>
# Example: bash post_from_email.sh "【ワンポイント解説】" W003 x_post_xonepoint.log

set -e

SUBJECT_KEYWORD="$1"
HOW_ID="$2"
LOG_FILE="${3:-x_post.log}"

if [ -z "$SUBJECT_KEYWORD" ] || [ -z "$HOW_ID" ]; then
  echo "Usage: bash post_from_email.sh <件名キーワード> <howID> <ログファイル名>"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DATE=$(date '+%Y-%m-%d %H:%M:%S JST')
LOG_PATH="$REPO_ROOT/logs/$LOG_FILE"

mkdir -p "$REPO_ROOT/logs"
echo "[$LOG_DATE] 開始 (subject:$SUBJECT_KEYWORD, howID:$HOW_ID)" | tee -a "$LOG_PATH"

cd "$REPO_ROOT"

/usr/bin/claude -p "
以下の手順をループで実行してください。投稿が完了するか、対象メールがなくなるまで繰り返します。

## ループ処理

### STEP 1: 未処理メールを検索
Gmail MCP で以下のクエリで検索する（全件取得）：
クエリ: subject:$SUBJECT_KEYWORD -label:投稿済み

### STEP 2: メールがなければ終了
投稿対象メールが見つからなければ「投稿対象メールなし」と出力してループを終了する。

### STEP 3: 最古のスレッドを確認
検索結果の中で受信日時が最も古い1件（internalDate が最小のもの）を選択し：

1. 本文から [投稿文] と [/投稿文] で囲まれたテキストを抽出する

2. [投稿文] タグが存在しない、または中身が空の場合：
   - 「投稿文タグなし、スキップ: <件名>」と出力する
   - 以下のコマンドで「投稿済み」ラベルのみ付与する（アーカイブはしない。THREAD_ID はそのスレッドのID）：
     gws gmail users threads modify --params \"{\\\"userId\\\": \\\"me\\\", \\\"id\\\": \\\"THREAD_ID\\\"}\" --json '{\"addLabelIds\": [\"Label_103\"]}'
   - STEP 1 に戻る

3. [投稿文] が存在する場合は以降のステップへ進む

4. 本文から [リプ] と [/リプ] で囲まれたテキストを抽出する（タグがなければリプなし）

5. メッセージIDを取得し、以下のコマンドで添付画像をダウンロードする（exit code 0 なら画像あり、1 なら画像なし）：
python3 $REPO_ROOT/scripts/download_gmail_attachment.py <message_id> /tmp/xpost_image.png

### STEP 4a: [投稿文] を X に投稿し、tweet_id を取得
画像あり（上記コマンドが成功）の場合：
python3 $REPO_ROOT/scripts/post_to_x.py --text \"（抽出したテキスト）\" --image /tmp/xpost_image.png

画像なしの場合：
python3 $REPO_ROOT/scripts/post_to_x.py --text \"（抽出したテキスト）\"

投稿完了後、出力に含まれる tweet URL から tweet_id を取得する（URLの末尾の数字）。

### STEP 4b: [リプ] があればセルフリプとして投稿
STEP 3 で [リプ] テキストが抽出されていた場合のみ実行する：
python3 $REPO_ROOT/scripts/post_to_x.py --text \"（リプテキスト）\" --reply-to <tweet_id>

### STEP 5: 「投稿済み」ラベルを付与してアーカイブ
以下のコマンドを実行する（THREAD_ID は STEP 3 で取得したスレッドID）：
gws gmail users threads modify --params \"{\\\"userId\\\": \\\"me\\\", \\\"id\\\": \\\"THREAD_ID\\\"}\" --json '{\"addLabelIds\": [\"Label_103\"], \"removeLabelIds\": [\"INBOX\"]}'

### STEP 6: 投稿記録
以下のコマンドで投稿を記録する（<X投稿URL> は STEP 4 で取得したURL）：
python3 $REPO_ROOT/scripts/record_output.py \"<X投稿URL>\" $HOW_ID

### STEP 7: 完了（ループ終了）
投稿した X の URL とメールの件名を出力してループを終了する。
" --allowedTools "Bash,mcp__claude_ai_Gmail__search_threads,mcp__claude_ai_Gmail__get_thread" 2>&1 | tee -a "$LOG_PATH"

echo "[$LOG_DATE] 完了" | tee -a "$LOG_PATH"
