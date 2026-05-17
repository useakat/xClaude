---
name: update-x-analytics
description: Google Drive の Xanalytics/tmp フォルダにある X アナリティクス CSV を読み込み、X投稿一覧シートの 詳細表示・リンククリック・フォロー増 列を更新する
---

# update-x-analytics エージェント

Google Drive の `Xanalytics/tmp` フォルダにある X アナリティクス CSV を読み込み、
X投稿一覧シートの該当行に詳細表示・リンククリック・フォロー増 を書き込む。

## データソース

| 項目 | 値 |
|---|---|
| Drive フォルダID（Xanalytics/tmp） | `1J45co5hN74gzxNateNRyeDtswZu0lMr3` |
| スプレッドシートID | `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c` |
| シート名 | `X投稿一覧` |

### X投稿一覧 関連列

| 列 | 列番号 | 内容 |
|---|---|---|
| B | 2 | ポストURL（`https://twitter.com/i/web/status/{ID}`） |
| AA | 27 | 詳細表示 |
| AB | 28 | リンククリック |
| AC | 29 | フォロー増 |

### CSV 列レイアウト（インデックス）

| インデックス | 列名 |
|---|---|
| 3 | Post Link（`https://x.com/usephys/status/{ID}`） |
| 9 | New follows → フォロー増 |
| 13 | Detail Expands → 詳細表示 |
| 14 | URL Clicks → リンククリック |

---

## 手順

### STEP 1: CSV ファイルを検索

**Drive ツールは ToolSearch で検索してから使うこと。**
`search_files` や `download_file_content` のような Drive 操作ツールは、セッションごとに異なる名前（UUID形式）で登録されているため、ハードコードせず毎回 ToolSearch で探す。

```
ToolSearch("drive search files")   # → search_files ツールのスキーマを取得
ToolSearch("drive download file")  # → download_file_content ツールのスキーマを取得
```

取得したツールで Xanalytics/tmp フォルダ内のファイルを検索する：

```
search_files(
  query="'1J45co5hN74gzxNateNRyeDtswZu0lMr3' in parents and trashed=false"
)
```

見つかったファイルのうち最新のものを対象とする（ファイル名に日付が含まれる場合は最大日付）。
複数ある場合はファイル名を一覧表示して、最新1件のみを処理する。

### STEP 2 & 3: CSV 取得・パース

`download_file_content` で CSV を取得する。レスポンスは **base64 エンコード**されているため、
以下の Python スクリプトを `/tmp/parse_analytics.py` に書き出して実行する。

base64 文字列を `/tmp/x_analytics_b64.txt` に保存してから実行する：

```python
# /tmp/parse_analytics.py
import base64, csv, io, json, re, sys

b64 = open('/tmp/x_analytics_b64.txt').read().strip()
csv_text = base64.b64decode(b64).decode('utf-8')

reader = csv.reader(io.StringIO(csv_text))
next(reader)  # ヘッダースキップ

csv_map = {}
for row in reader:
    if len(row) <= 14:
        continue
    url = row[3]
    m = re.search(r'/status/(\d+)', url)
    if not m:
        continue
    try:
        csv_map[m.group(1)] = {
            "detail_expands": int(row[13] or 0),
            "url_clicks":     int(row[14] or 0),
            "new_follows":    int(row[9]  or 0),
        }
    except (ValueError, IndexError):
        continue

print(json.dumps(csv_map))
```

```bash
python3 /tmp/parse_analytics.py
```

出力 JSON を `CSV_MAP`（`{status_id: {detail_expands, url_clicks, new_follows}}`）として記憶する。

### STEP 4: X投稿一覧の B列（ポストURL）を取得

`analyze-x-posts` スキルと同じスプレッドシートを参照する（スプレッドシートID: `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c`）。

```
sheets_get_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="X投稿一覧!B:B"
)
```

取得結果を `SHEET_URLS`（行番号付きリスト）として記憶する。  
1行目はヘッダーなので行番号は 2 から始まる。

### STEP 5: status ID でマッチング

`SHEET_URLS` の各行について：

1. URL から status ID を抽出する（`twitter.com/i/web/status/{ID}` または `x.com/.../status/{ID}`）
2. `CSV_MAP` に同じ ID があれば **更新対象** としてリストに追加する

```python
import re

def extract_status_id(url):
    m = re.search(r'/status/(\d+)', str(url))
    return m.group(1) if m else None
```

更新対象リスト `UPDATE_LIST` = `[(row_number, detail_expands, url_clicks, new_follows), ...]`

### STEP 6: 一括更新

更新対象が存在する場合、**`sheets_batch_update_values` を1回だけ呼び出す**。
行番号が連続しているかどうかに関わらず、すべての行を `data` 配列に1エントリずつ含めて単一呼び出しにまとめること（複数回に分けない）。

```
sheets_batch_update_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  data=[
    {"range": "X投稿一覧!AA{ROW}:AC{ROW}", "values": [[detail_expands, url_clicks, new_follows]]},
    {"range": "X投稿一覧!AA{ROW}:AC{ROW}", "values": [[detail_expands, url_clicks, new_follows]]},
    ...  # UPDATE_LIST の全件を1つの data 配列に入れる
  ]
)
```

### STEP 7: 完了報告

```
✅ X投稿一覧 アナリティクス更新完了
   CSVファイル: <ファイル名>
   マッチ件数: N件 / CSV総投稿数: M件
   更新列: 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）
```
