---
name: x-post-from-email
description: Gmail の「【ワンポイント解説】」メールを読み取り、[投稿文] セクションと添付画像を X に投稿する
---

# x-post-from-email エージェント

Gmail で「【ワンポイント解説】」を含む未処理メールを検索し、X（Twitter）に投稿する。

## 手順

### STEP 1: 未処理メールを検索

Gmail MCP で以下の条件で検索する：
- クエリ: `subject:【ワンポイント解説】 -label:投稿済み`

### STEP 2: メールがない場合

投稿対象メールが見つからなければ「投稿対象メールなし」とログ出力して終了する。

### STEP 3: メール本文と添付画像を取得

見つかったメール（最新1件）のスレッドを取得し：
1. 本文から `[投稿文]` と `[/投稿文]` に囲まれたテキストを抽出する
2. 添付画像（PNG/JPG）があれば `/tmp/xpost_image.png` に保存する

### STEP 4: X に投稿

```bash
# 画像ありの場合
python3 $(git rev-parse --show-toplevel)/scripts/post_to_x.py \
  --text "（抽出したテキスト）" \
  --image /tmp/xpost_image.png

# 画像なしの場合
python3 $(git rev-parse --show-toplevel)/scripts/post_to_x.py \
  --text "（抽出したテキスト）"
```

### STEP 5: メールに「投稿済み」ラベルを付与

Gmail MCP で対象メールに `投稿済み` ラベルを付ける。
（ラベルが存在しない場合は先に作成する）

### STEP 6: 完了ログ

投稿した X の URL と対象メールの件名をログ出力して終了する。
