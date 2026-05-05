---
title: check-fact への GPT ファクトチェック統合
date: 2026-05-06
tags: [skill, bugfix]
---

← [変更ログへ](../changelog.md)

## 背景・動機

`check-fact` スキルは Claude 自身によるレビューのみだったが、事実確認の精度を上げるため外部モデル（GPT-5.4-mini）を使ったファクトチェックを組み込むことになった。また、サブエージェント（`context: fork`）として呼び出された際に `$ARGUMENTS` が空になるケースで動作が止まる問題と、`OPENAI_API_KEY` が `chatgpt_factcheck.py` 内で上書きされてしまう問題も同時に修正した。

## 実施内容

- `scripts/chatgpt_factcheck.py` を新規作成し、GPT-5.4-mini へテキストを送ってファクトチェック結果を返すスクリプトを実装
- `SKILL.md` のチェック方法に「GPT ファクトチェック」ステップを追加（最大5回ループの先頭で実行）
- `OPENAI_API_KEY` を `chatgpt_factcheck.py` 内で直接セットしていた処理を削除し、環境変数から読む形に修正
- `$ARGUMENTS` が空の場合に会話コンテキストからチェック対象を取得する入力モード自動判定を追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/check-fact/SKILL.md` | GPT ファクトチェック手順・入力モード自動判定・チェックサマリー出力形式を追加 |
| `scripts/chatgpt_factcheck.py` | GPT-5.4-mini へテキストを送るスクリプトを新規作成（環境変数で認証） |

## 設計判断

GPT スクリプトがエラーを返した場合は Claude 自身が代行する設計にした。外部 API への依存を必須にせず、エラー時にスキルが止まらないようにするため。

## 確認結果

`/check-fact` でテキストを渡したとき、GPT ファクトチェック → Claude レビュー → 修正案の順で出力されることを確認。サブエージェントとして呼び出した際も引数なしで正常動作することを確認。
