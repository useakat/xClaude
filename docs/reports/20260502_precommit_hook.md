---
title: git commit 前の settings.json 確認フック追加
date: 2026-05-02
tags: [infra]
---

← [変更ログへ](../changelog.md#git-commit-前の確認フックを追加)

## 背景・動機

CLAUDE.md に「コミット前に新規実行許可を settings.json に追記する」ルールがあるが、今回の Wiki 構築作業でこれを失念し複数回コミットしてしまった。ルールを Claude に自動で思い出させる仕組みが必要だった。

## 実施内容

- `settings.json` に `PreToolUse` フックを追加
- `git commit` を含む Bash コマンド実行前に確認メッセージを Claude の文脈に挿入する

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `hooks.PreToolUse` セクションを新規追加 |

## 設計判断

**jq ではなく Python を使った理由**：サーバーに `jq` がインストールされていなかったため、`python3` で JSON をパースする方式にした。`python3` はプロジェクト全体で使用済みのため依存を増やさない。

**`systemMessage` で通知する理由**：フックでコミットをブロック（`continue: false`）するのではなく、メッセージを表示するだけにした。確認作業をするかどうかは Claude が判断できるため、強制ブロックは過剰。

## 確認結果

パイプテストで `git commit` を含むコマンド検知時に `systemMessage` が正しく出力されることを確認。
