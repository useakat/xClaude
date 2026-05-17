---
name: update-x-analytics
description: Google Drive の Xanalytics/tmp フォルダにある X アナリティクス CSV を読み込み、X投稿一覧シートの 詳細表示・リンククリック・フォロー増 列を更新する
model: claude-sonnet-4-6
---

# update-x-analytics エージェント

| 役割 | 担当 |
|---|---|
| Drive CSV 取得・パース | スクリプト（Python） |
| Sheets B列 読み取り | エージェント（mcp-gsheets） |
| マッチング | スクリプト（Python） |
| Sheets AA:AC 書き込み | エージェント（mcp-gsheets） |

## データソース

| 項目 | 値 |
|---|---|
| スプレッドシートID | `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c` |
| シート名 | `X投稿一覧` |

---

## 手順

### STEP 1: Drive CSV 取得・パース

```bash
python3 /home/user/xClaude/scripts/fetch_x_analytics_csv.py
```

成功すると `/tmp/x_analytics_map.json` が作成される。

### STEP 2: Sheets B列を取得してファイルに保存

`sheets_get_values` で B列を取得し、結果の `values` を `/tmp/x_analytics_b_col.json` に保存する：

```bash
cat > /tmp/x_analytics_b_col.json << 'EOF'
<sheets_get_values の values をそのまま貼り付ける>
EOF
```

sheets_get_values のパラメータ：
- spreadsheetId: `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c`
- range: `X投稿一覧!B:B`

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
