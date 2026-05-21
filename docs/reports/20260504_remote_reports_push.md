---
title: remote session での docs/reports/ push 許可
date: 2026-05-04
tags: [infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

reporter スキルは remote session で実行されるが、既存の `PreToolUse` フックがすべての `git commit` / `git push` をブロックしていたため、生成した日報・週報・月報を自動で push できなかった。

`docs/reports/` への書き込みはコンテンツ生成であり、コード変更と違ってレビュー不要で push してよい。一方でスキル定義・設定ファイルなどの変更は引き続き remote からはブロックしたい。ファイルパスで許可範囲を絞る仕組みが必要だった。

## 実施内容

- `scripts/hooks/git_guard.py` を新設
  - `git commit` 時: `git diff --cached --name-only` でステージ済みファイルを確認し、全て `docs/reports/` 配下なら許可
  - `git push` 時: `git log --name-only origin/master..HEAD` で未 push コミットのファイルを確認し、全て `docs/reports/` 配下なら許可
  - ブランチ作成は常にブロック
  - ローカルセッション（`CLAUDE_CODE_REMOTE != 'true'`）は対象外
- `settings.json` のフックコマンドをインライン Python から `python3 $(git rev-parse --show-toplevel)/scripts/hooks/git_guard.py` に変更
  - リポジトリパスを動的解決（ローカル `/root/xClaude`・remote `/home/user/xClaude` 両対応）
- スクリプト内の `REPO` も `__file__` からの相対パスで解決

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/hooks/git_guard.py` | 新設。パスベースの commit/push 可否判定ロジック |
| `.claude/settings.json` | フックコマンドをスクリプト外部化・動的パスに変更 |

## 設計判断

ステージ済みファイルを実際にチェックする方式を採用。`git commit -m` のコマンド文字列だけでは変更内容を判別できないため、サブプロセスで `git diff --cached` を実行して確認する。

## 確認結果

次回 remote session での reporter-daily 実行時に、`docs/reports/daily/` への commit・push が自動で通ることを確認予定。
