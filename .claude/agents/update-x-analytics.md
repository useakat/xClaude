---
name: update-x-analytics
description: Google Drive の Xanalytics/tmp フォルダにある X アナリティクス CSV を読み込み、X投稿一覧シートの 詳細表示・リンククリック・フォロー増 列を更新する
model: claude-sonnet-4-6
---

# update-x-analytics エージェント

X アナリティクス CSV の取得・パースはスクリプトが担当。
エージェントは Sheets の読み書きのみを mcp-gsheets で行う。

## データソース

| 項目 | 値 |
|---|---|
| スプレッドシートID | `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c` |
| シート名 | `X投稿一覧` |

### X投稿一覧 関連列

| 列 | 列番号 | 内容 |
|---|---|---|
| B | 2 | ポストURL |
| AA | 27 | 詳細表示 |
| AB | 28 | リンククリック |
| AC | 29 | フォロー増 |

---

## 手順

### STEP 1: スクリプトを実行して CSV_MAP を取得

```bash
python3 /home/user/xClaude/scripts/update_x_analytics.py
```

出力 JSON の `csv_map`（`{status_id: {detail_expands, url_clicks, new_follows}}`）と
`file`（CSVファイル名）を記憶する。

### STEP 2: X投稿一覧の B列（ポストURL）を取得

```
sheets_get_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="X投稿一覧!B:B"
)
```

### STEP 3: status ID でマッチング

各行の URL から `/status/(\d+)` で status ID を抽出し、
`csv_map` に存在する行を更新対象リストに追加する。

### STEP 4: 一括更新

**`sheets_batch_update_values` を1回だけ呼び出す。**
全件を `data` 配列に含めて単一呼び出しにまとめること。

```
sheets_batch_update_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  data=[
    {"range": "X投稿一覧!AA{ROW}:AC{ROW}", "values": [[detail_expands, url_clicks, new_follows]]},
    ...
  ]
)
```

### STEP 5: 完了報告

```
✅ X投稿一覧 アナリティクス更新完了
   CSVファイル: <ファイル名>
   マッチ件数: N件 / CSV総投稿数: M件
   更新列: 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）
```
