---
title: git_guard.py 削除・リモートセッションの git 操作制限を全廃
date: 2026-05-14
tags: [infra, workflow]
---

← [変更ログへ](../changelog/)

## 背景・動機

これまで `scripts/hooks/git_guard.py` を PreToolUse フックとして設定し、リモートセッションからの git 操作を制限していた。具体的には以下のルールが適用されていた：

- **ブランチ作成**：無条件ブロック（`git checkout -b` / `git switch -c` / `git branch`）
- **git commit**：ステージ済みファイルが全て `docs/reports/` 配下のみなら許可、それ以外はブロック
- **git push**：未 push コミットのファイルが全て `docs/reports/` 配下のみなら許可、それ以外はブロック

今後はリモートセッションでの変更を **feature ブランチで行い、master への反映を merge 段階で調整する**方針に切り替えた。ブランチ戦略でコントロールする方が柔軟性が高く、フックによる一律ブロックは不要になった。

## 実施内容

- **`scripts/hooks/git_guard.py` を削除** — リモートセッションの git 操作制限ロジックを全廃
- **`.claude/settings.json` の `PreToolUse` フックを全削除** — git_guard.py 呼び出しフック・`mcp__github__push_files` リマインドフックの両方を削除

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/hooks/git_guard.py` | ファイル削除 |
| `.claude/settings.json` | `PreToolUse` セクション全削除 |

## 設計判断

**なぜフックによる制限からブランチ戦略に切り替えたのか**：
- フックによる一律ブロックは、正当な操作まで阻害するケースが発生していた
- feature ブランチで作業 → merge 時に精査する方式の方が、変更の粒度・タイミングを柔軟にコントロールできる
- git_guard.py の回避策（mcp__github__push_files 経由の push など）が必要になっていたことから、そもそもルール設計の見直しが必要だった

## 確認結果

- `scripts/hooks/git_guard.py` が削除されていることを確認
- `.claude/settings.json` に `PreToolUse` セクションが存在しないことを確認
- リモートセッションでの git コマンド（commit・push・ブランチ作成）がブロックなく実行できる状態になった
