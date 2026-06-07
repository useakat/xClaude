---
title: mcp-gsheets リモート認証修正
date: 2026-06-07
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260607_20260607_mcp_gsheets_remote_auth_fix/)

## 背景・動機

2026-06-04 の「mcp-gsheets 認証を `GOOGLE_APPLICATION_CREDENTIALS` に統一」変更で、`.claude/settings.json` の `env` に `GOOGLE_APPLICATION_CREDENTIALS` が追加された。この値は `${HOME}/xClaude/gcp/...` というシェル変数未展開の文字列で、リモートセッションでは `gcp/` ディレクトリ自体が存在しない。

mcp-gsheets プロセスは Claude の子プロセスとして起動するため、`settings.json` の `env` に設定した `GOOGLE_APPLICATION_CREDENTIALS` をそのまま引き継ぐ。Google Auth Library は `GOOGLE_APPLICATION_CREDENTIALS` を最優先で確認するため、`.mcp.json` に `GOOGLE_SERVICE_ACCOUNT_KEY` が正しく設定されていても、先に `GOOGLE_APPLICATION_CREDENTIALS` のファイルを開こうとして失敗していた。

同セッションで、mcp__github__push_files 実行後に「master に push しました」と伝える報告を忘れるケースが続いたため、PostToolUse フックによるリマインドも追加した。

## 実施内容

- `.claude/settings.json` の `env` から `GOOGLE_APPLICATION_CREDENTIALS` を削除（`GOOGLE_PROJECT_ID` は維持）
- `.claude/settings.json` の `PostToolUse` フックに `mcp__github__push_files` のリマインドを追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `env.GOOGLE_APPLICATION_CREDENTIALS` を削除。`hooks.PostToolUse` に `mcp__github__push_files` フックを追加 |

## 設計判断

- **`.mcp.json` は変更不要**: すでに前セッションで `GOOGLE_SERVICE_ACCOUNT_KEY` に戻されており、修正済み
- **`GOOGLE_APPLICATION_CREDENTIALS` は settings.json からのみ除去**: ローカル環境で `sync_to_drive.py` が使う場合は `~/.bashrc` 等で個別に設定する
- **フックは `echo` のみ**: mcp__github__push_files の引数でブランチを判定する複雑な実装は避け、「master に push したら必ず伝えること」という単純なリマインドで十分と判断

## 確認結果

リモートセッションで mcp-gsheets ツール（`sheets_get_values` など）が `GOOGLE_SERVICE_ACCOUNT_KEY` で正常に認証されることを次回セッションで確認予定。
