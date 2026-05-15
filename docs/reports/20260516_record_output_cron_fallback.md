---
title: record_output.py に cron 用サービスアカウントファイル fallback を追加
date: 2026-05-16
tags: [bugfix, infra]
---

← [変更ログへ](../changelog.md)

## 背景・動機

5/15 に `record_output.py` を Google Sheets 書き込みに移行した後、cron で実行された X 投稿（5/15 06:00 ワンポイント、17:00 X長文）の記録が outputs シートに反映されていないことを発見。

ログを確認したところ、`RuntimeError: GOOGLE_SERVICE_ACCOUNT_KEY が設定されていません` で記録が失敗していた。原因は cron は `.bashrc` を読み込まないため、インタラクティブセッションでは設定されている `GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数が cron 実行時には未設定になること。

## 実施内容

- `scripts/record_output.py` の `get_client()` に fallback 分岐を追加：
  - `GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数があれば → 現状通り環境変数の JSON を使用
  - なければ → `gcp/charming-well-464402-u4-2cfb7bddf343.json` を `from_service_account_file` で直接読む
- 環境変数なしの状態（`env -i ...`）で動作確認
- 5/15 の未記録 2 件（xonepoint 06:00、xlong 17:00）を Sheets に手動追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/record_output.py` | `get_client()` にサービスアカウント JSON ファイル fallback を追加 |

## 設計判断

検討した代替案：
- **A**: crontab に `GOOGLE_SERVICE_ACCOUNT_KEY` を直書き — JSON が長いため非現実的
- **B**: `run_*.sh` で `source ~/.bashrc` — 副作用のリスクあり
- **C**（採用）: スクリプト内で fallback — 他スクリプトや crontab への影響ゼロで最小修正

## 確認結果

`env -i PATH=... python3 scripts/record_output.py ...` で環境変数なし状態でも記録成功。テスト行は削除済み。次回 cron 実行で本番動作確認予定。
