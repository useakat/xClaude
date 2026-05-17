---
name: update-x-analytics
description: Google Drive の Xanalytics/tmp フォルダにある X アナリティクス CSV を読み込み、X投稿一覧シートの 詳細表示・リンククリック・フォロー増 列を更新する
model: claude-sonnet-4-6
---

# update-x-analytics エージェント

| 役割 | 担当 |
|---|---|
| Drive CSV 検索・ダウンロード | スクリプト（fetch_x_analytics_csv.py） |
| CSV パース | スクリプト（fetch_x_analytics_csv.py） |
| Sheets B列 読み取り | スクリプト（fetch_x_b_col.py） |
| マッチング | スクリプト（Python） |
| Sheets AA:AC 書き込み | エージェント（mcp-gsheets） |

## データソース

| 項目 | 値 |
|---|---|
| スプレッドシートID | `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c` |
| シート名 | `X投稿一覧` |
| Drive フォルダID | `1J45co5hN74gzxNateNRyeDtswZu0lMr3`（Xanalytics/tmp） |

---

## 手順

### STEP 1: Drive CSV をダウンロードしてパース

```bash
python3 /home/user/xClaude/scripts/fetch_x_analytics_csv.py
```

スクリプトが Drive MCP プロキシに直接 HTTP POST し、base64 デコード・CSV パースまで完結させる。
成功すると `/tmp/x_analytics_map.json` が作成される。

> **注意**: Drive MCP の `download_file_content` をエージェントが直接呼ぶと base64（〜28,000トークン）がコンテキストに乗りパフォーマンスが著しく低下するため、スクリプト経由を使う。詳細: [docs/reports/20260517_drive_mcp_download_cost.md](../../docs/reports/20260517_drive_mcp_download_cost.md)

### STEP 2: Sheets B列を取得してファイルに保存

```bash
python3 /home/user/xClaude/scripts/fetch_x_b_col.py
```

スクリプトが Sheets API に直接 HTTP リクエストし、LLM を経由せずに `/tmp/x_analytics_b_col.json` を作成する。

> **警告**: `sheets_get_values` を呼び出してはならない。B列（386行）を LLM コンテキストに載せると大量のトークンを消費し、処理が著しく遅くなる。**必ずスクリプト経由を使うこと。** `sheets_get_values` および `cat` コマンドによる heredoc 保存は絶対に禁止。

### STEP 3: マッチング実行

```bash
python3 /home/user/xClaude/scripts/match_x_analytics.py
```

stdout に出力される JSON の `update_data` を記憶する。

### STEP 4: Sheets を一括更新

`sheets_batch_update_values` を **1回だけ** 呼び出す：

- spreadsheetId: `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c`
- data: STEP 3 の `update_data` をそのまま渡す

### STEP 5: 完了報告

```
✅ X投稿一覧 アナリティクス更新完了
   CSVファイル: <file>
   マッチ件数: <match_count> 件 / CSV総投稿数: <total_csv> 件
   更新列: 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）
```
