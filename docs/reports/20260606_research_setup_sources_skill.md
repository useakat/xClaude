---
title: research_setup-sources スキル新設
date: 2026-06-06
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260606_20260606_research_setup_sources_skill/)

## 背景・動機

`research_trivia-source` はノートブック作成〜Deep Research〜トリビア選定〜解説文生成まで一気通貫で行うが、「ノートブック作成＋ソース収集だけ」を他スキル（`check-fact-lim` など）から再利用したいケースが発生した。Steps 0〜3 を独立スキルとして切り出すことで、notebook_id を後続スキルに渡すビルディングブロックとして使えるようにした。

## 実施内容

- `.claude/skills/research_setup-sources/SKILL.md` を新規作成
  - Step 0: 認証確認
  - Step 1: テーマ取得（`$ARGUMENTS`）
  - Step 2: `notebooklm_manager.py create` でノートブック作成
  - Step 3: `notebooklm_manager.py deep-research` でソース自動収集
  - Step 4: notebook_id を完了報告として表示して終了
- `.claude/skills/metadata.yaml` に `research_setup-sources: category: リサーチ・分析` を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/research_setup-sources/SKILL.md` | 新規作成 |
| `.claude/skills/metadata.yaml` | `research_setup-sources` エントリを追記 |

## 設計判断

`research_trivia-source` 本体はリファクタせず、新スキルを独立して作成した。既存スキルの動作を維持しつつ、新スキルを徐々に普及させる方針。Deep Research クエリの情報源フィルタ（査読論文優先・企業ページ除外）は汎用性が高いのでそのまま継承した。

## 確認結果

`/research_setup-sources` がスキル一覧に表示されることを確認。
