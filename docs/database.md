---
title: データベース構造
description: Google Sheets がデータの正。database/ の CSV は参照用アーカイブ。
---

データの実体は **Google Sheets**（mcp-gsheets 経由で読み書き）。`database/*.csv` は参照用アーカイブで更新不要。

## ファイル一覧

| ファイル | 用途 |
|---|---|
| `onePointNeta.csv` | X ワンポイント解説のネタ在庫 |
| `noteNeta.csv` | note 記事のネタ在庫 |
| `newsTopics.csv` | ニュース投稿のネタ |
| `persona.csv` | 想定ペルソナ定義 |
| `pain.csv` | 読者の悩み |
| `what.csv` | 提供価値 |
| `outputs.csv` | 生成済み投稿の記録 |

## onePointNeta.csv の列構成

| 列名 | 内容 |
|---|---|
| No | 連番 |
| テーマ | ネタのテーマ |
| 冒頭1行案 | 投稿の冒頭候補 |
| 身近さ接続 | 日常との接続ポイント |
| 仕組みのポイント | 科学的な説明のポイント |
| 感情的締め案 | 締め言葉の候補 |
| 難易度 | 易・中・難 |
| 出典メモ | 参照した情報源 |
| ステータス | 未使用 / 使用済み |

## ネタ管理（mcp-gsheets）

スプレッドシート SS1: `1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM`

| 操作 | mcp-gsheets ツール |
|---|---|
| 未使用ネタ一覧 | `sheets_get_values(spreadsheetId=SS1, range="onePointNeta!A:Z")` → I列=「未使用」でフィルタ |
| ネタを使用済みに更新 | `sheets_update_values(spreadsheetId=SS1, range="onePointNeta!I{行}", values=[["使用済み"]])` |
| ネタを追加 | `sheets_append_values(spreadsheetId=SS1, range="onePointNeta!A:A", values=[[...]])` |
