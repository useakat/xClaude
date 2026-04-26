# daily-xonepoint

ワンポイント解説 X投稿の原稿作成から保存・メール通知までを一括実行する。

## 手順

### STEP 1+2: ネタ選定 & 投稿原稿作成

/writer-xonepoint を実行する。

### STEP 3: 品質チェック

上で作成した【本文】に対して /check を実行する。

### STEP 4: ファイル保存

以下をすべて実行する：

1. 今日の日付（YYYYMMDD形式）で `outputs/drafts/YYYYMMDD_xonepoint.md` に出力全体を保存する（drafts/ ディレクトリがなければ作成）
2. `git add -A && git commit -m "Add daily post draft (YYYYMMDD)" && git push` でリポジトリに保存する

### STEP 5: メール通知

保存した `outputs/drafts/YYYYMMDD_xonepoint.md` の内容を読み込み、Gmail の MCP ツールを使って以下の内容でメールの下書きを作成する：

- 宛先: useakat@gmail.com
- 件名: 【ワンポイント解説】YYYYMMDD の原稿ができました
- 本文: `outputs/drafts/YYYYMMDD_xonepoint.md` の内容をそのまま貼り付ける

下書き作成後、可能であればそのまま送信する。

> YYYYMMDD は実行日の実際の日付に置き換えること。
