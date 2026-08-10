---
title: record-note-posts
description: "note.com の投稿情報（ビュー・スキ・スキ率・サムネ・ハッシュタグ）を取得して Google Sheets の「note投稿一覧」シートに記録・更新する。新規記事を検知したら outputs シートにも自動記録する。"
category: 運用・記録
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

note.com の投稿情報（ビュー・スキ・スキ率・サムネ・ハッシュタグ）を取得して Google Sheets の「note投稿一覧」シートに記録・更新する。新規記事を検知したら outputs シートにも自動記録する。

## 詳細内容

note 投稿の統計データを取得し、Sheets に記録・更新するスキルです。
**新規記事を検知した場合は `outputs` シートにも自動で投稿記録を追加します**（STEP 6）。

ユーザーからの依頼: $ARGUMENTS

---

## データソース

| 項目 | 値 |
|---|---|
| note クリエイター | `takaesu7431` |
| Sheets ID | `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c`（SS3） |
| シート名 | `note投稿一覧` |
| ヘッダー行 | 1行目（A〜J列） |
| outputs シート（STEP 6） | SS2 `1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc` / シート名 `outputs` |

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

# STEP 6: outputs シートへ新規投稿を自動記録

**note投稿一覧への新規追加の有無にかかわらず、`NOTE_DATA` の全記事について実施する**（note投稿一覧に既存でも outputs に無い記事があり得るため）。

## 6-1. outputs の既存 note URL を取得

```
sheets_get_values(
  spreadsheetId="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc",
  range="outputs!A:H"
)
```

B列（URL）の一覧を `OUTPUTS_URLS` として記憶する。

## 6-2. 未記録の記事を抽出

`NOTE_DATA` のうち、`url` が `OUTPUTS_URLS` に**含まれないもの**を「outputs 未記録」として抽出する。1件も無ければ STEP 6 は完了（何もしない）。

**ワークフロー外の記事を除外する（重要）**：outputs は W002（執念の物語の note 記事）を記録するシートであり、**W002 ワークフロー以前・ワークフロー外の note 記事（技術メモ・数学入門など）を W002 として記録してはならない**。未記録記事のうち、次のどちらも満たさないものは**記録せず、完了報告に「ワークフロー外として除外」として列挙する**：

- `projects/w002/*/note-record.md` にタイトル一致の記録ファイルがある、**または**
- 公開日時が**実行時点から30日以内**（＝この cron が回り始めてからの新規公開）

※ `$ARGUMENTS` に `all` や `--months N`（N≧2）を指定して実行すると過去記事が大量に未記録として挙がるため、このガードが無いと旧記事が W002 として一括投入されてしまう（2026-08-10 に実データで確認：未記録16件中15件が2026年2月以前の旧記事だった）。

## 6-3. neta_id を解決

各未記録記事について、記事フォルダに置かれた記録ファイルからネタ番号を引く。

```bash
cd /root/xClaude
grep -l "^title: <記事タイトル>$" projects/w002/*/note-record.md 2>/dev/null
```

- ヒットしたファイルの `neta_id:` の値を使う（例 `noteNeta[151]`）。
- タイトル完全一致でヒットしない場合は、`grep -rn "neta_id" projects/w002/*/note-record.md` で一覧を出し、タイトルが類似する記事フォルダを探す。
- それでも特定できなければ **neta_id は空欄**にし、完了報告に「neta_id 未解決」として記事名を挙げる（後でよーんが手当てできるようにする。**推測で埋めない**）。

## 6-4. outputs に追記

未記録記事ごとに1行追加する。

```
sheets_append_values(
  spreadsheetId="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc",
  range="outputs!A:H",
  insertDataOption="INSERT_ROWS",
  values=[[
    {publishAt},   # A 日時（note の公開日時）
    {url},         # B URL（note 記事URL）
    "W002",        # C what_id（note 記事は W002 固定）
    {neta_id},     # D neta_id（解決できなければ ""）
    "",            # E thought_id
    "",            # F note_url（W001 の販促投稿側が使う列。note 本体行は空欄）
    "",            # G img-pattern_id
    ""             # H x_url
  ]]
)
```

**注意**：F列 `note_url` は「X投稿がどの note へ誘導したか」を記録する列であり、note 記事本体の行では**空欄のまま**にする（`sync-x-note-analytics` の導線集計が二重計上しないため）。

---

# 完了報告

```
✅ note投稿一覧 更新完了
   更新: N件 / 新規追加: M件
   対象期間: YYYY-MM-DD 〜 YYYY-MM-DD

✅ outputs シート同期
   新規記録: K件
   （neta_id 未解決: 記事名A, 記事名B）※あれば
```
