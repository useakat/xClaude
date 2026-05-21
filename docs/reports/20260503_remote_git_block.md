---
title: remote session での git 書き込み操作ブロック
date: 2026-05-03
tags: [infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

cloud session（Anthropic VM）では git push / commit / ブランチ作成を行わせたくない。ローカル session は従来通り許可したまま、remote のみ制限する必要があった。

## 実施内容

- `settings.json` に `PreToolUse` フックを追加
- Bash ツール実行前に `CLAUDE_CODE_REMOTE=true` を確認し、git 書き込み操作（push / commit / checkout -b / switch -c / branch 作成）であれば exit 2 でブロック
- ローカル session は `CLAUDE_CODE_REMOTE` が未設定のためスルー

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `PreToolUse` フックを追加。インライン Python でコマンドをパースしてブロック判定 |

## 設計判断

- **`permissions.deny` vs フック**：`deny` は全 session に適用されるため remote 専用制限には使えない。`CLAUDE_CODE_REMOTE` 環境変数を判定できるフック方式を採用。
- **スクリプトファイル vs インライン**：シンプルな1条件のためインライン Python で完結させ、別スクリプトファイルは不要と判断。

## 確認結果

設定を `settings.json` に記述し push 済み。cloud session 起動時にフックが読み込まれ、git push / commit 実行時に「Remote session: git push/commit/branch 作成は禁止されています。」と表示されてブロックされることを期待。
