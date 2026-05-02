---
title: データベース構造
description: database/ 以下の CSV ファイルの構造と用途
---

データの実体は `database/*.csv`。`scripts/sync_to_sheets.sh` で Google Sheets に一方向同期する。

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

## ネタ管理スクリプト

```bash
# 未使用ネタ一覧を表示
python3 scripts/csv_reader.py list one-point --unused-only --full

# ネタを使用済みに更新
python3 scripts/update_neta_status.py one-point [No番号] 使用済み

# ネタを追加
python3 scripts/sheets_manager.py add-one-point --theme "..." --hook "..."
```
