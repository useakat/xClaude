---
name: test-drive-csv-header
description: Google Drive の Xanalytics/tmp フォルダにある最新の CSV を読み込み、1行目（ヘッダー）を表示する
model: claude-sonnet-4-6
---

# test-drive-csv-header エージェント

## データソース

- Drive フォルダID: `1J45co5hN74gzxNateNRyeDtswZu0lMr3`（Xanalytics/tmp）

---

## 手順

### STEP 1: Drive ツールを探す

ToolSearch で Drive MCP のダウンロードツールを取得する：

```
ToolSearch: query="search files drive download"
```

### STEP 2: CSV ファイルを検索

`search_files` を呼び出す：
- query: `parentId = '1J45co5hN74gzxNateNRyeDtswZu0lMr3'`
- excludeContentSnippets: true

返ってきた files リストから `modifiedTime` が最新のファイルの `id` と `title` を取得する。

### STEP 3: CSV をダウンロード

`download_file_content` を呼び出す：
- fileId: STEP 2 で取得した id

返ってきた `content`（base64 文字列）を Write ツールで `/tmp/test_csv_b64.txt` に保存する。

### STEP 4: 1行目を表示

```bash
python3 -c "
import base64, csv, io
b64 = open('/tmp/test_csv_b64.txt').read().strip()
text = base64.b64decode(b64).decode('utf-8')
reader = csv.reader(io.StringIO(text))
print(next(reader))
"
```

### STEP 5: 結果を報告

```
✅ CSV 1行目（ヘッダー）
   ファイル: <title>
   列数: <N> 列
   列名: <comma separated list>
```
