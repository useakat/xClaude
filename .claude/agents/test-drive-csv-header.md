---
name: test-drive-csv-header
description: Google Drive の Xanalytics/tmp フォルダにある最新の CSV をダウンロードし、ファイル名とダウンロード完了を報告する（base64デコードは行わない）
model: claude-sonnet-4-6
---

# test-drive-csv-header エージェント

## データソース

- Drive フォルダID: `1J45co5hN74gzxNateNRyeDtswZu0lMr3`（Xanalytics/tmp）

---

## 手順

### STEP 1: Drive ツールを探す

ToolSearch で Drive MCP の search_files と download_file_content ツールを取得する：

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

ダウンロードが完了したら、base64 デコードは**行わない**。

### STEP 4: 結果を報告

```
✅ ダウンロード完了
   ファイル名: <title>
   content の先頭 100 文字: <content の最初の 100 文字>
```
