---
title: daily-xonepoint メール下書き作成の MCP 化
date: 2026-05-03
tags: [skill, bugfix]
---

← [変更ログへ](../changelog/)

## 関連する過去の変更

- **daily-xonepoint 自動化改善**（2026-05-02）— STEP 5 のメール下書き作成を gws CLI スクリプトに変更した際の実装。[→報告書](./20260502_daily_xonepoint_improvement/)

## 背景・動機

`daily-xonepoint` ルーティンエージェントの STEP 5（Gmail 下書き作成）が `gws: command not found` で失敗していた。

原因の調査で以下が判明した：
- エージェント実行環境はホストとは異なるコンテナで動作しており、`/usr/local/bin/gws` が存在しない
- PATH を補正しても、gws CLI の OAuth 認証情報（`~/.config/gws/credentials.enc` 等）もコンテナ内に存在しない
- 認証情報ファイルをコンテナに持ち込む手段がなく、gws CLI ベースの実装はエージェント環境では根本的に動作しない

MCP ツール（`mcp__claude_ai_Gmail__create_draft`）はクラウド側で認証を管理するため、エージェント環境でもバイナリ・認証情報なしに使用できる。

## 実施内容

- `SKILL.md` の `tools` フロントマターに `mcp__claude_ai_Gmail__create_draft` を追加
- STEP 5 の実装を `bash scripts/create_gmail_draft.sh` 呼び出しから `mcp__claude_ai_Gmail__create_draft` ツール直接呼び出しに変更
- 成功判定を「exit code 0 + draft ID 表示」→「レスポンスに draft ID が含まれること」に変更

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 5 を MCP ツール呼び出しに変更、tools フロントマターに MCP ツールを追加 |

## 設計判断

`create_gmail_draft.sh` は変更せず残した。ターミナルから手動実行する場合は gws CLI が使えるため、スクリプトとしての価値はある。エージェント環境でのみ MCP を使う棲み分けとした。

## 確認結果

次回の daily-xonepoint ルーティン実行時に STEP 5 が通ることで確認予定。

## 今後の課題

他のスキル・エージェントでも gws CLI を呼ぶ処理がある場合、同様の問題が起きる可能性がある。エージェント環境から呼ぶ処理は MCP または API ベースの実装を選ぶ方針とする。
