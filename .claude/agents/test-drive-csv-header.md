---
name: test-drive-csv-header
description: Google Drive の Xanalytics/tmp フォルダにある最新の CSV のファイル名を返す
model: claude-sonnet-4-6
---

# test-drive-csv-header エージェント

## データソース

- Drive フォルダID: `1J45co5hN74gzxNateNRyeDtswZu0lMr3`（Xanalytics/tmp）

---

## 手順

### STEP 1: Drive ツールを探す

ToolSearch で Drive MCP の search_files ツールを取得する：

```
ToolSearch: query="search files drive"
```

### STEP 2: CSV ファイルを検索

`search_files` を呼び出す：
- query: `parentId = '1J45co5hN74gzxNateNRyeDtswZu0lMr3'`
- excludeContentSnippets: true

返ってきた files リストから `modifiedTime` が最新のファイルの `title`（または `name`）を取得する。

### STEP 3: 結果を報告

```
✅ 最新ファイル名: <title>
```
