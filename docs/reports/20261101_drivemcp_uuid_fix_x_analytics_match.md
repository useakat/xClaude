---
title: Drive MCP の DRIVE_UUID を設定キー "Google_Drive" に修正、X アナリティクスマッチングスクリプトを追加
date: 2026-11-01
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

※実装は 2026-10-25 のリモートセッション（コミット `d3bfe5b`）。記録が漏れていたため本日付で報告書を作成。

## 背景・動機

リモート環境の Drive MCP プロキシ設定は、以前の UUID ベースのキーから接続名ベースのキー（`"Google_Drive"`）に変わっていたが、`drivemcp_get_remote.sh` と `fetch_x_analytics_csv.py` には古い UUID `960819bd-…` がハードコードされたままで、リモート（routine / agent）からの Drive ファイル取得が設定を見つけられず失敗していた。

また、X アナリティクス CSV の取込（update-x-analytics エージェント）では、CSV と X投稿一覧シートの突合・更新データ生成を Claude が都度組み立てており、スクリプト化による確実化（CLAUDE.md のスクリプト化原則）が必要だった。

## 実施内容

- `drivemcp_get_remote.sh` / `fetch_x_analytics_csv.py` の `DRIVE_UUID` をハードコード UUID から設定キー `"Google_Drive"` に置き換え
- `match_x_analytics.py`（新規）: `fetch_x_analytics_csv.py` の出力（`/tmp/x_analytics_map.json`）と X投稿一覧 B列（`/tmp/x_analytics_b_col.json`）を tweet ID で突合し、`sheets_batch_update_values` 用の `update_data`（`X投稿一覧!AA<row>:AC<row>` ＝ 詳細表示・リンククリック・フォロー増）を JSON で stdout に出力する

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/drivemcp_get_remote.sh` | DRIVE_UUID を設定キー "Google_Drive" に修正 |
| `scripts/fetch_x_analytics_csv.py` | 同上 |
| `scripts/match_x_analytics.py` | 新規。CSV × B列の突合と batch update データ生成 |

## 確認結果

- コミット `d3bfe5b`（2026-10-25）として実装済み・push 済み。update-x-analytics エージェントがこのスクリプト群を使用する

## 関連する過去の変更

- [drivemcp_get_remote の新設](20260524_drivemcp_get_remote/)
- [X アナリティクス取込の urllib 化](20261011_x_analytics_fetch_urllib/)
