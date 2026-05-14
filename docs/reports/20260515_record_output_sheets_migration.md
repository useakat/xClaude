---
title: record_output.py を Google Sheets 書き込みに移行
date: 2026-05-15
tags: [infra, workflow]
---

← [変更ログへ](../changelog.md)

## 背景・動機

CLAUDE.md に「データベースの実体は Google Sheets、`database/*.csv` は参照用アーカイブで更新不要」と定義されているにもかかわらず、X投稿の記録先がローカル CSV のままになっていた。Sheets を正とする設計に揃えるため移行した。

## 実施内容

- `scripts/record_output.py` を gspread + サービスアカウント認証で Sheets に追記する実装に書き換え
- `database/outputs.csv` の既存18行を outputs シートに手動転記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/record_output.py` | CSV 追記から gspread 経由の Sheets `append_row` に変更。`GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数で認証 |

## 設計判断

cron から呼ばれるスクリプトは MCP ツールを使えないため、gspread を直接利用した。認証は既存の `GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数（mcp-gsheets と共用）をそのまま流用した。

## 確認結果

テスト行を Sheets に書き込み・削除して動作確認済み。既存データ18行の転記も完了。
