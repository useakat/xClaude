---
title: ネタ選定を writer-xonepoint から daily-xonepoint に移動
date: 2026-06-01
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

`writer-xonepoint` はネタ選定（Sheets 読み込み・分野グループ選定・ステータス更新）と原稿生成の両方を担っていた。この構成では `writer-xonepoint` を「テーマ指定で単体呼び出し」することができず、柔軟性が低かった。  
また `daily-xonepoint` がネタ選定をスキップして `writer-xonepoint` に丸投げしていたため、フロー全体が見通しにくかった。

## 実施内容

- `daily-xonepoint` の STEP 2 にネタ選定ロジック（Sheets 読み込み・分野グループ選定・ステータス更新）を移植
- `writer-xonepoint` は「受け取ったネタ情報で原稿生成のみ行う」役割に限定
- `writer-xonepoint` をテーマ直接指定で単体呼び出しできるよう簡略化

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 2 にネタ選定ロジックを追加 |
| `.claude/skills/writer-xonepoint/SKILL.md` | ネタ選定ロジックを削除し、原稿生成専用に簡略化 |

## 設計判断

`writer-xonepoint` を「原稿生成専用」に絞ることで、他のスキル（`draft_xstory` 等）からも再利用しやすい構造になる。ネタ選定の責務は `daily-xonepoint` が持つことで、自動化フローの全体像が1スキルで把握できる。

## 確認結果

コミット `8fbfaba` で変更済み。`daily-xonepoint` の STEP 2 が Sheets からネタを選定し、`writer-xonepoint` に渡すフローになっていることを SKILL.md で確認。
