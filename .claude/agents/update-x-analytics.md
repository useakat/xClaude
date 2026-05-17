---
name: update-x-analytics
description: Google Drive の Xanalytics/tmp フォルダにある X アナリティクス CSV を読み込み、X投稿一覧シートの 詳細表示・リンククリック・フォロー増 列を更新する
model: claude-sonnet-4-6
---

# update-x-analytics エージェント

| 役割 | 担当 |
|---|---|
| Drive CSV 検索・ダウンロード | エージェント（Drive MCP） |
| CSV パース | スクリプト（Python） |
| Sheets B列 読み取り | エージェント（mcp-gsheets） |
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

### STEP 1: Drive CSV をダウンロードして保存

ToolSearch で Drive MCP のツール名を取得する（UUID はセッション固有のため毎回検索する）:

```
ToolSearch: query="search files drive download"
```

取得したツール名を使って以下を実行する：

**1-a. CSV ファイルを検索**

`search_files` を呼び出す：
- query: `parentId = '1J45co5hN74gzxNateNRyeDtswZu0lMr3'`
- excludeContentSnippets: true

返ってきた files リストを `modifiedTime` の降順でソートし、最新ファイルの `id` と `title`（または `name`）を記憶する。

**1-b. CSV をダウンロード**

`download_file_content` を呼び出す：
- fileId: 1-a で取得した id

返ってきた `content` フィールドの base64 文字列を **Write ツール** で `/tmp/x_analytics_b64.txt` に保存する（Bash の echo は長い文字列を壊すため必ず Write ツールを使う）。

### STEP 2: CSV をパース

```bash
python3 /home/user/xClaude/scripts/parse_x_analytics_csv.py
```

成功すると `/tmp/x_analytics_map.json` が作成される。

### STEP 3: Sheets B列を取得してファイルに保存

`sheets_get_values` で B列を取得し、結果の `values` を `/tmp/x_analytics_b_col.json` に保存する：

```bash
cat > /tmp/x_analytics_b_col.json << 'EOF'
<sheets_get_values の values をそのまま貼り付ける>
EOF
```

sheets_get_values のパラメータ：
- spreadsheetId: `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c`
- range: `X投稿一覧!B:B`

### STEP 4: マッチング実行

```bash
python3 /home/user/xClaude/scripts/match_x_analytics.py
```

stdout に出力される JSON の `update_data` を記憶する。

### STEP 5: Sheets を一括更新

`sheets_batch_update_values` を **1回だけ** 呼び出す：

- spreadsheetId: `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c`
- data: STEP 4 の `update_data` をそのまま渡す

### STEP 6: 完了報告

```
✅ X投稿一覧 アナリティクス更新完了
   CSVファイル: <file>
   マッチ件数: <match_count> 件 / CSV総投稿数: <total_csv> 件
   更新列: 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）
```
