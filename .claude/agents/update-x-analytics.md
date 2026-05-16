---
name: update-x-analytics
description: Google Drive の analytics_tmp フォルダにある X アナリティクス CSV を読み込み、X投稿一覧シートの 詳細表示・リンククリック・フォロー増 列を更新する
---

# update-x-analytics エージェント

Google Drive の `analytics_tmp` フォルダにある X アナリティクス CSV を読み込み、
X投稿一覧シートの該当行に詳細表示・リンククリック・フォロー増 を書き込む。

## データソース

| 項目 | 値 |
|---|---|
| Drive フォルダID（analytics_tmp） | `1HlkV8woi9LHz9bCKI184_w6KJRHvLR72` |
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

`mcp__claude_ai_Google_Drive__search_files` で analytics_tmp フォルダ内の CSV を検索する：

```
search_files(
  query="'1HlkV8woi9LHz9bCKI184_w6KJRHvLR72' in parents and mimeType='text/csv' and trashed=false"
)
```

見つかったファイルのうち最新のものを対象とする（ファイル名に日付が含まれる場合は最大日付）。

複数ある場合はファイル名を一覧表示して、最新1件のみを処理する。

### STEP 2: CSV 内容を取得

`mcp__claude_ai_Google_Drive__read_file_content` で CSV テキストを取得し、`CSV_TEXT` として記憶する。

```
read_file_content(file_id="<STEP1で取得したID>")
```

### STEP 3: CSV をパースして投稿データマップを作成

以下の Python スクリプトを Bash で実行する。`CSV_TEXT` の内容を stdin に渡すか、
`/tmp/x_analytics.csv` に書き出してから処理する。

```python
import re, json, sys

csv_text = sys.stdin.read()

# Post Link 列以降の数値フィールドを正規表現で一括抽出
# 列順: Post id, Date, Post text, Post Link, Impressions, Likes, Engagements,
#        Bookmarks, Shares, New follows(9), Replies, Reposts, Profile visits,
#        Detail Expands(13), URL Clicks(14), ...
pattern = re.compile(
    r'https://x\.com/usephys/status/(\d+)'   # group(1): status ID
    r',(\d+),(\d+),(\d+),(\d+),(\d+)'        # Impressions,Likes,Eng,Bookmarks,Shares,NewFollows(6)
    r',(\d+),(\d+),(\d+)'                    # Replies,Reposts,ProfileVisits
    r',(\d+),(\d+)'                          # DetailExpands(10), URLClicks(11)
)

csv_map = {}
for m in pattern.finditer(csv_text):
    sid            = m.group(1)
    new_follows    = int(m.group(6))   # CSV col 9
    detail_expands = int(m.group(10))  # CSV col 13
    url_clicks     = int(m.group(11))  # CSV col 14
    csv_map[sid] = {
        "detail_expands": detail_expands,
        "url_clicks": url_clicks,
        "new_follows": new_follows
    }

print(json.dumps(csv_map))
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

更新対象が存在する場合、`sheets_batch_update_values` で AA:AC 列を一括更新する。

行番号が連続している場合は1回の呼び出しにまとめる。
連続していない場合は連続する範囲ごとにまとめて呼び出す。

```
sheets_batch_update_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  data=[
    {
      "range": "X投稿一覧!AA{START}:AC{END}",
      "values": [
        [detail_expands, url_clicks, new_follows],  # 各行
        ...
      ]
    }
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
