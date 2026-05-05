---
title: git_guard.py のローカルセッション判定と settings.local.json 設定
date: 2026-05-06
tags: [infra, bugfix]
---

← [変更ログへ](../changelog.md)

## 背景・動機

ローカルセッションで Claude がブランチ作成を試みたところ `git_guard.py` にブロックされた。調査の結果、`CLAUDE_CODE_LOCAL=true` が Claude Code プロセスに引き継がれていないことが原因と判明。

あわせて、`new session`（Claude Code の「New Session」起動）では `CLAUDE_CODE_REMOTE=true` が自動設定されないため、git_guard.py がローカルセッションと区別できないことも確認した。

## git_guard.py の想定動作

| 起動方式 | `CLAUDE_CODE_LOCAL` | `CLAUDE_CODE_REMOTE` | git_guard.py の判定 |
|---|---|---|---|
| ローカル CLI（`claude` コマンド） | `true`（settings.local.json で設定） | 未設定 | 許可（line 9-10） |
| `/schedule` cron エージェント | 未設定 | `true`（自動設定） | ブロック |
| New Session | 未設定 | 未設定 | **ローカル扱いでスルー**（意図しない動作） |

New Session は `CLAUDE_CODE_REMOTE=true` が設定されないため、ブランチ作成・commit・push がブロックされない。現状は「実害がない」範囲にとどまっているが、設計上の穴として記録する。

## 実施内容

- `~/.bashrc` の `CLAUDE_CODE_LOCAL=true` は Claude Code プロセスに引き継がれないことを確認
- `.claude/settings.local.json`（git 非管理）に `env.CLAUDE_CODE_LOCAL=true` を追加することで、ローカル CLI セッションにのみ環境変数を渡す構成を確立
- `settings.json`（チーム共通・git 管理）に書くとリモートエージェントにも適用されてしまうため NG と確認

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.local.json` | `env.CLAUDE_CODE_LOCAL=true` を追加（git 非管理・手動設定） |

## 今後の課題

New Session で `CLAUDE_CODE_REMOTE=true` を付与する手段がないか検討する。
選択肢：New Session の起動設定（あれば）に環境変数を追加する。
