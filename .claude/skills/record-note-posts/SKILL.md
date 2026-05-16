---
name: record-note-posts
description: note.com の投稿情報（ビュー・スキ・スキ率・サムネ・ハッシュタグ）を取得して Google Sheets の「note投稿一覧」シートに記録・更新する。
tools: Bash, mcp__mcp-gsheets__sheets_get_values, mcp__mcp-gsheets__sheets_update_values, mcp__mcp-gsheets__sheets_append_values
---

note 投稿の統計データを取得し、Sheets に記録・更新するスキルです。

ユーザーからの依頼: $ARGUMENTS

---

## データソース

| 項目 | 値 |
|---|---|
| note クリエイター | `takaesu7431` |
| Sheets ID | `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c` |
| シート名 | `note投稿一覧` |
| ヘッダー行 | 1行目（A〜J列） |

### 列構成

| 列 | 項目 | 内容 |
|---|---|---|
| A | 投稿日時 | `YYYY-MM-DD HH:MM:SS` |
| B | 記事URL | `https://note.com/takaesu7431/n/{key}` |
| C | タイトル | 記事タイトル |
| D | 文字数 | `/api/v3/notes/{key}` の body から HTML 除去後の文字数 |
| E | ハッシュタグ | スペース区切り（`#宇宙 #物理`） |
| F | サムネURL | eyecatch 画像 URL |
| G | サムネプレビュー | `=IMAGE(F{行番号})` 数式 |
| H | ビュー | 累計 read_count |
| I | スキ | 累計 like_count |
| J | スキ率 | スキ ÷ ビュー（小数4桁） |

---

# STEP 1: note データ取得

`$ARGUMENTS` を解釈する：

| 入力 | 動作 |
|---|---|
| （空） | 過去1ヶ月の記事を対象 |
| `all` | 全記事を対象 |
| `--months 3` | 過去3ヶ月を対象 |

```bash
cd /root/xClaude
python3 scripts/fetch_note_stats.py [オプション]
```

- 空 or `--months N` → `python3 scripts/fetch_note_stats.py` or `--months N`
- `all` → `python3 scripts/fetch_note_stats.py --all`

取得結果（JSON 配列）を `NOTE_DATA` として記憶する。

---

# STEP 2: Sheets 既存データ取得

```
sheets_get_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="note投稿一覧!B:B"
)
```

B列（記事URL）の一覧を取得し、`EXISTING_URLS` として記憶する（行番号付き）。

---

# STEP 3: 新規 / 更新を振り分け

`NOTE_DATA` の各記事について：

- `url` が `EXISTING_URLS` に**ある** → **更新対象**（該当行の H・I・J列を上書き）
- `url` が `EXISTING_URLS` に**ない** → **新規追加対象**

---

# STEP 4: 既存行を更新

更新対象ごとに、該当行番号（`ROW`）に対して：

```
sheets_update_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="note投稿一覧!H{ROW}:J{ROW}",
  values=[[{view}, {like}, {likeRate}]]
)
```

---

# STEP 5: 新規行を追加

新規追加対象が存在する場合、1件ずつ末尾に追加する。

現在の最終行番号（`LAST_ROW`）を `EXISTING_URLS` の行数から算出する。

各記事について：

```
sheets_append_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="note投稿一覧!A:J",
  values=[[
    {publishAt},
    {url},
    {name},
    {charCount},
    {hashtags},
    {eyecatch},
    "=IMAGE(F{LAST_ROW+1})",
    {view},
    {like},
    {likeRate}
  ]]
)
```

追加のたびに `LAST_ROW` を +1 する。

---

# 完了報告

```
✅ note投稿一覧 更新完了
   更新: N件 / 新規追加: M件
   対象期間: YYYY-MM-DD 〜 YYYY-MM-DD
```
