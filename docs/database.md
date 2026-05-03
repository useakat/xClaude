---
title: データベース構造
description: Google Sheets がデータの正。database/ の CSV は参照用アーカイブ。
---

データの実体は **Google Sheets**（mcp-gsheets 経由で読み書き）。`database/*.csv` は参照用アーカイブで更新不要。

## スプレッドシート

| 変数 | スプレッドシート ID | 用途 | シート |
|---|---|---|---|
| SS1 | `1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM` | コンテンツ制作 | onePointNeta, noteNeta, newsTopics, outputs |
| SS2 | `1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc` | ターゲット設計 | persona, pain, what |

---

## SS1: コンテンツ制作シート

### onePointNeta（X ワンポイント解説ネタ）

| 列 | 列名 | 内容 |
|---|---|---|
| A | No | 連番 |
| B | テーマ | ネタのテーマ |
| C | 冒頭1行案 | 投稿の冒頭候補 |
| D | 身近さ接続 | 日常との接続ポイント |
| E | 仕組みのポイント | 科学的な説明のポイント |
| F | 感情的締め案 | 締め言葉の候補 |
| G | 難易度 | 易・中・難 |
| H | 出典メモ | 参照した情報源 |
| **I** | **ステータス** | **未使用 / 使用済み** |

### noteNeta（note 記事ネタ）

| 列 | 列名 | 内容 |
|---|---|---|
| A | No | 連番 |
| B | タイトル案 | 記事タイトル候補 |
| C | 主人公(ミッション名) | 主人公・ミッション名 |
| D | 時代・背景 | 時代・背景 |
| E | 危機の内容 | 危機の内容 |
| F | 逆転のポイント | 逆転のポイント |
| G | 科学的見どころ | 科学的な見どころ |
| H | 人間ドラマの核心 | 人間ドラマの核心 |
| I | 記事展開のヒント | 記事の展開ヒント |
| J | 難易度 | 易・中・難 |
| K | 出典メモ | 参照した情報源 |
| **L** | **ステータス** | **未使用 / 使用済み** |
| M | 追加日 | 追加日 |

### newsTopics（ニュース投稿ネタ）

| 列 | 列名 | 内容 |
|---|---|---|
| A | No | 連番 |
| B | カテゴリ | ネタのカテゴリ |
| C | タイトル | ネタのタイトル |
| D | 概要 | 概要 |
| E | ポイント | 注目ポイント |
| F | ソース | 参照ソース |
| **G** | **ステータス** | **未使用 / 使用済み** |
| H | 追加日 | 追加日 |

### outputs（投稿記録）

| 列 | 列名 | 内容 |
|---|---|---|
| A | dateTime | 投稿日時（YYYY-MM-DD HH:MM:SS） |
| B | URL | 投稿 URL |
| C | howID | how_id（提供価値 ID） |

---

## SS2: ターゲット設計シート

### persona（想定ペルソナ）

| 列名 | 内容 |
|---|---|
| persona_id | ペルソナ ID |
| label | ラベル |
| pain_domain | 悩みドメイン |
| awareness_level | 認知レベル |
| channel_affinity | チャンネル親和性 |
| description | 説明 |

### pain（読者の悩み）

| 列名 | 内容 |
|---|---|
| id | 悩み ID |
| title | タイトル |
| domain | ドメイン |
| severity | 深刻度 (1-5) |
| affected_scope | 対象範囲 |
| persona_ids | 対象ペルソナ ID |

### what（提供価値）

| 列名 | 内容 |
|---|---|
| id | how_id |
| pain_id | 関連する悩み ID |
| title | タイトル |
| description | 説明 |

---

## mcp-gsheets 操作リファレンス

### 読み取り

```
sheets_get_values(spreadsheetId=<ID>, range="シート名!A:Z")
```

未使用ネタのフィルタは Claude がステータス列の値を見て行う。

### ステータス更新（使用済みに変更）

行番号は `sheets_get_values` の結果から No で特定する。

| シート | 操作 |
|---|---|
| onePointNeta | `sheets_update_values(spreadsheetId=SS1, range="onePointNeta!I{行}", values=[["使用済み"]])` |
| noteNeta | `sheets_update_values(spreadsheetId=SS1, range="noteNeta!L{行}", values=[["使用済み"]])` |
| newsTopics | `sheets_update_values(spreadsheetId=SS1, range="newsTopics!G{行}", values=[["使用済み"]])` |

### 追記

```
sheets_append_values(spreadsheetId=<ID>, range="シート名!A:A", values=[[列1, 列2, ...]])
```

---

## database/ CSV（参照用アーカイブ）

`database/*.csv` は Google Sheets 移行前のスナップショット。読み取り専用で更新不要。
