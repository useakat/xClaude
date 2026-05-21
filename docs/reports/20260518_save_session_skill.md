---
title: save-session スキル新設
date: 2026-05-18
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

セッション作業ログ（JSONL）は `.claude/projects/` 以下に自動保存されるが、検索・参照しやすい形式での蓄積手段がなかった。
特に複雑な実装セッションの経緯を後から追いたいとき、JSONL を直接読むのはコストが高い。
Markdown に変換して `docs/history/` に保存・Git 管理することで、Wiki や報告書から参照しやすい形式で作業ログを残せる。

## 実施内容

- `save-session/SKILL.md` を新設（`.claude/skills/` 配下）
  - STEP 1: `save_session_history.py --list` で JSONL 一覧を確認
  - STEP 2: タイトルとスラグをよーんに確認してから進む（ユーザー確認ステップ）
  - STEP 3: `save_session_history.py` で JSONL → Markdown 変換・保存
  - STEP 4: 関連報告書へのセッション履歴リンク追記（任意）
  - STEP 5: コミット・GitHub MCP push
- `scripts/save_session_history.py` を新設
  - JSONL を読み込み、ユーザー/アシスタントのターンを Markdown 形式で出力
  - `--list` オプションでセッション一覧表示
  - `--title`・`--slug` でファイル名とタイトルを指定
  - 出力先: `docs/history/YYYYMMDD_<slug>.md`
- `.claude/skills/metadata.yaml` に `save-session: category: 運用・記録` を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/save-session/SKILL.md` | スキル定義を新規作成 |
| `scripts/save_session_history.py` | JSONL→Markdown 変換スクリプトを新規作成 |
| `.claude/skills/metadata.yaml` | `save-session` エントリを追加 |

## 確認結果

スキルが `/save-session` で呼び出せることを確認。`save_session_history.py --list` でセッション一覧が表示されること、`update-x-analytics 高速化リファクタリング` のセッションを変換して `docs/history/` に保存できることを確認済み（`20260517_update_x_analytics_refactoring_session.md`）。
