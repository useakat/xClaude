---
title: git_guard.py のガードロジック反転（デフォルトブロック化）
date: 2026-05-06
tags: [infra]
---

← [変更ログへ](../changelog.md)

## 背景・動機

従来の git_guard.py は `CLAUDE_CODE_REMOTE=true` の場合にブランチ作成・commit・push をブロックする設計だった。しかし `CLAUDE_CODE_REMOTE=true` が設定されるのは `/schedule` で起動する cron エージェントのみで、「New Session」などの他の非インタラクティブ起動では変数が設定されずガードをスルーしてしまう問題があった。

## 実施内容

ガードのロジックを反転し、「明示的にローカルと判定できる場合だけ通す（デフォルトブロック）」に変更した。

- **変更前**：`CLAUDE_CODE_REMOTE != 'true'` → 通す（remote 以外は全て許可）
- **変更後**：`CLAUDE_CODE_LOCAL == 'true'` → 通す（ローカルと明示された場合のみ許可）

ローカル判定のフラグ `CLAUDE_CODE_LOCAL=true` は `.claude/settings.local.json`（git 非管理）の `env` に設定する。インタラクティブシェルから起動したセッションだけがこの変数を持つ。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/hooks/git_guard.py` | line 8-9: 条件を `CLAUDE_CODE_REMOTE != 'true'` → `CLAUDE_CODE_LOCAL == 'true'` に変更 |
| `.claude/settings.local.json` | `env.CLAUDE_CODE_LOCAL=true` を追加（git 非管理・手動設定） |

## 設計判断

「ブロックしたいものを列挙」より「通したいものを列挙」の方が、想定外の起動方式でのスルーを防げる。セキュリティのデフォルトは deny が原則。

## 確認結果

`settings.local.json` 設定後、ローカルセッションから `git checkout -b test/sandbox` が通ることを確認。
