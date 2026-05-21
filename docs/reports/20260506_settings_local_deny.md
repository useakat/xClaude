---
title: settings.local.json への書き込みを全セッションで禁止
date: 2026-05-06
tags: [infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

`settings.local.json` は gitignore 対象のローカル個人設定ファイルで、`OPENAI_API_KEY` などの機密情報を `env` セクションで管理している。ローカルで動作する別の Claude Code セッション（reporter 系エージェント等）が permissions を更新する際に `env` セクションを含まない状態で上書きしてしまい、API キーが消えるトラブルが発生した。これを防ぐため、全セッションからの Write/Edit を禁止した。

## 実施内容

- `settings.json` の `permissions.deny` に `Write(.claude/settings.local.json)` と `Edit(.claude/settings.local.json)` を追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `permissions.deny` セクションを新設し2ルールを追加 |

## 設計判断

`settings.json`（git 管理・全セッション共通）に deny ルールを書くことで、ローカル・リモート問わず全セッションに適用される。`settings.local.json` 自体は gitignore 対象のため、このルールを git 経由で届けるには `settings.json` 側に書くしかない。

## 確認結果

`settings.json` に `deny` セクションが正しく追加されていることを Python で確認済み。

## 今後の課題

`settings.local.json` を手動編集する場合はテキストエディタで直接編集する運用となる。
