---
title: check-fact の openai モジュール依存を curl に変更
date: 2026-05-06
tags: [skill, bugfix, infra]
---

← [変更ログへ](../changelog.md)

## 背景・動機

`chatgpt_factcheck.py` は Python の `openai` パッケージを使っていたが、remote 環境（`/schedule` で起動する cron エージェント）にはパッケージがインストールされていないため `ModuleNotFoundError` が発生し、GPT ファクトチェックが常に Claude 代行になっていた。ローカル・remote 問わず動作させるため、標準ライブラリのみで実装する必要があった。

## 実施内容

- `scripts/chatgpt_factcheck.py` を `openai` パッケージ依存から `curl` + `json` + `subprocess`（全て標準ライブラリ）に書き直し
- OpenAI API を `curl -s -f` で直接呼び出す形に変更
- モデル名を誤って `gpt-4.1-mini` に変更してしまったため、正しい `gpt-5.4-mini` に戻す修正を追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/chatgpt_factcheck.py` | `openai` パッケージ → `curl` + `subprocess` に全面書き直し |
| `.claude/skills/check-fact/SKILL.md` | モデル名を `gpt-5.4-mini` に戻す |

## 設計判断

`pip install openai` をスクリプトの冒頭で自動実行する案もあったが、remote 環境で毎回インストールが走るのは非効率。`curl` は全環境に存在するため依存なしで確実に動く。

## 確認結果

`echo "地球の半径は10mです" | python3 scripts/chatgpt_factcheck.py` でファクトチェック結果が正常に返ることをローカルで確認。
