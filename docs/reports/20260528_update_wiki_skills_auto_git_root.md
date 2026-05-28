---
title: update_wiki_skills.py：git root を自動検出に改善
date: 2026-05-28
tags: [infra, wiki]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

PostToolUse hook が `git -C /root/xClaude commit *` で設定されていたため、ローカル環境（`/home/user/xClaude`）では hook が発動せず、スキル新規作成時に wiki が自動更新されていませんでした。

スクリプトをハードコード前提の設計から、環境に依存しない自動検出方式に改善することで、ローカル・リモートの両環境で hook が確実に動作するようにします。

## 実施内容

- `update_wiki_skills.py` の `main()` 関数冒頭で `git rev-parse --show-toplevel` を使用して git root を自動検出
- `GIT_WORK_TREE` 環境変数が設定されている場合はそれを優先、未設定時のみ自動検出
- `git` コマンド実行失敗時は `/root/xClaude` へ fallback（互換性維持）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/update_wiki_skills.py` | `main()` 関数の repo_root 取得ロジックを git 自動検出方式に変更 |

## 設計判断

**git rev-parse --show-toplevel を選択した理由**

複数の方式を検討：

1. **settings.json の hook matcher を両方のパスに対応** — シンプルだが、環境が増えるたびに設定を追加する必要
2. **スクリプト側で git 自動検出** — 一度修正すれば全環境に対応。スクリプト再利用性が高い（推奨）

2を選択した理由：
- hook matcher の複数条件管理は保守負荷が高い
- スクリプト側の修正で「環境非依存化」という根本解を達成
- routine/agent など新しい実行環境でも自動対応

## 確認結果

- 修正後の スクリプトを実行して、環境変数未設定時に `/home/user/xClaude` を正しく検出することを確認
- `GIT_WORK_TREE=/home/user/xClaude python scripts/update_wiki_skills.py` 実行後、wiki が全35スキルで正しく更新されたことを確認
- 環境変数がない場合も `python scripts/update_wiki_skills.py` だけで動作することを確認

## 今後の課題

PostToolUse hook の matcher を改善して、複数環境に対応した条件を設定することを検討（必須ではなく、スクリプト側の自動検出で当面は対応可能）。
