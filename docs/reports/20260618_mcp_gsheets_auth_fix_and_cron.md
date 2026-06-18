---
title: mcp-gsheets 認証修正・record-note-posts cron 追加
date: 2026-06-14
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260618_mcp_gsheets_auth_fix_and_cron/)

## 背景・動機

リモート環境（routine / agent）から `/record-note-posts` を実行した際に Google Sheets への書き込みが失敗するという報告があった。

原因を追うと、`settings.json` に `GOOGLE_APPLICATION_CREDENTIALS`（ファイルパス形式）が設定されており、Google Auth Library の優先順位によってこれが `GOOGLE_SERVICE_ACCOUNT_KEY`（JSON 内容形式）より優先されていた。リモート環境では `gcp/` フォルダが存在しないため、ファイルパスが無効になり認証エラーが発生していた。

また `/record-note-posts` スキルを毎朝自動実行するための cron ジョブが未設定だったため、手動実行が必要な状態だった。

## 実施内容

- `settings.json` から `GOOGLE_APPLICATION_CREDENTIALS` を削除（`GOOGLE_SERVICE_ACCOUNT_KEY` のみに統一）
- `scripts/run_record_note_posts.sh` を新設。cron 向けに `GOOGLE_SERVICE_ACCOUNT_KEY` を明示的に export するラッパースクリプト
- `scripts/run_mond_letter_reply.sh` にも同様の `GOOGLE_SERVICE_ACCOUNT_KEY` export を追加
- `run_record_note_posts.sh` を cron に登録（毎日 3:00 JST）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `GOOGLE_APPLICATION_CREDENTIALS` を削除 |
| `scripts/run_record_note_posts.sh` | 新規作成。GOOGLE_SERVICE_ACCOUNT_KEY export + `claude -p "/record-note-posts"` 実行 |
| `scripts/run_mond_letter_reply.sh` | `GOOGLE_SERVICE_ACCOUNT_KEY` export を追加 |

## 設計判断

`GOOGLE_APPLICATION_CREDENTIALS`（ファイルパス）は Google Auth Library で最優先されるため、ローカルでのみ有効。リモートでは `GOOGLE_SERVICE_ACCOUNT_KEY`（JSON 文字列）が必要。両者を共存させると環境依存が生まれるため、`settings.json` からはファイルパス形式を完全に除去し、個別の cron スクリプトで明示的に JSON 文字列を export する方針とした。

## 確認結果

cron スクリプト手動実行でリモート環境と同等の条件でテストし、Google Sheets への書き込みが成功することを確認。

## 今後の課題

この問題が過去に2回発生している（2026-05-23 check_auth 新設時・2026-06-04 auth 統一時・2026-06-07 リモート修正時）。`settings.json` へのファイルパス形式 auth 追記が再発リスクの根本原因。CLAUDE.md の実装ルールに「settings.json には GOOGLE_APPLICATION_CREDENTIALS を書かない」旨を明記することを検討。
