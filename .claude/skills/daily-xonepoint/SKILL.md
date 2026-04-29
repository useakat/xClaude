# daily-xonepoint

ワンポイント解説 X投稿の原稿作成から保存・メール通知までを一括実行する。

## 手順

### STEP 1+2: ネタ選定 & 投稿原稿作成

/writer-xonepoint を実行する。

### STEP 3: 品質チェック

上で作成した【本文】に対して /check を実行する。

### STEP 4: ファイル保存

以下をすべて実行する：

1. 今日の日付（YYYYMMDD形式）と時刻（HH:mm:ss 形式）で `outputs/drafts/YYYYMMDD-HH:mm:ss_xonepoint.md` に出力全体を保存する（drafts/ ディレクトリがなければ作成）
2. 以下のスクリプトでリポジトリに保存・mainブランチに同期する：
```bash
bash $(git rev-parse --show-toplevel)/scripts/commit_and_sync.sh "daily: xonepoint 原稿 YYYYMMDD-HH:mm:ss"
```

### STEP 5: メール通知

保存した `outputs/drafts/YYYYMMDD-HH:mm:ss_xonepoint.md` の内容を読み込み、Gmail の MCP ツールを使って以下の内容でメールの下書きを作成する：

- 宛先: useakat@gmail.com
- 件名: 【ワンポイント解説】YYYYMMDD HH:mm:ss の原稿ができました
- 本文: `outputs/drafts/YYYYMMDD-HH:mm:ss_xonepoint.md` の内容をそのまま貼り付け、末尾に以下を追加する：
```
[投稿文]

[/投稿文]
```

下書き作成後、可能であればそのまま送信する。

> YYYYMMDDやHH:mm:ss は実行日の実際の日付や時刻に置き換えること。
