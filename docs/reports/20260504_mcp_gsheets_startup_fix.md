---
title: mcp-gsheets 起動設定の修正
date: 2026-05-04
tags: [infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

mcp-gsheets をリモートセッションで使えるよう設定を進める中で、起動しない・認証エラーになるといった問題が連続して発生した。試行錯誤を経て安定した構成に落ち着いた。

## 実施内容

- `args` に `--stdio` を追加（後に不要と判明し削除）
- `settings.json` への移行を試みた（command 型は `.mcp.json` でのみ remote session で起動することが判明し差し戻し）
- `env` から `GOOGLE_APPLICATION_CREDENTIALS`（ローカルファイルパス）を削除し、`GOOGLE_SERVICE_ACCOUNT_KEY` のみに統一
  - `GOOGLE_APPLICATION_CREDENTIALS` が設定されていると mcp-gsheets がファイル認証を先に試み、ファイルが存在しないリモートで「No authentication method provided」になることが判明
- `~/.bashrc` にローカル用の `GOOGLE_SERVICE_ACCOUNT_KEY` 自動設定を追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.mcp.json` | `env` を `GOOGLE_SERVICE_ACCOUNT_KEY` のみに統一、`--stdio` を削除 |
| `.claude/settings.json` | mcp-gsheets の一時移行エントリを削除（xmcp のみ残す） |
| `~/.bashrc` | `GOOGLE_SERVICE_ACCOUNT_KEY=$(cat gcp/*.json)` を追加（ローカル認証用） |

## 設計判断

- command 型 MCP サーバーは `.mcp.json` に定義した場合のみ remote session で自動起動する（`settings.json` の `mcpServers` では起動しない）
- ローカル・リモート共通で `GOOGLE_SERVICE_ACCOUNT_KEY` を使う構成に統一。ローカルは `~/.bashrc` で自動設定、リモートは claude.ai/code の環境変数 UI で設定

## 確認結果

`GOOGLE_SERVICE_ACCOUNT_KEY=$(cat gcp/*.json) timeout 5 npx -y mcp-gsheets@latest --stdio` でローカル起動を確認。リモートセッションでの動作確認は次回セッションで実施予定。
