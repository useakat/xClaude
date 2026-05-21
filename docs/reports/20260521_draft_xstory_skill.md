---
title: draft_xstory スキル新設
date: 2026-05-21
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../history/20260521_draft_xstory_skill_session/)

## 背景・動機

X長文ストーリー投稿（what_id W001）の制作フローが手動で分散していた。`daily-xonepoint` と同様に、ネタ選定〜Gmail下書き作成までを1コマンドで自律実行するスキルが必要だった。

## 実施内容

- `daily-xonepoint` スキルを参考に `draft_xstory` スキルを新設
- スキル名は当初 `daily-xstory` で作成したが、毎日投稿ではないため `draft_xstory` にリネーム
- STEP 1a（ネタ補充）・STEP 7（インフォグラフィック作成）のうち、STEP 7 はスコープ外として削除
- `metadata.yaml` に `draft_xstory: category: コンテンツ制作` を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/draft_xstory/SKILL.md` | スキル新規作成（6 STEP 構成） |
| `.claude/skills/metadata.yaml` | `draft_xstory` エントリを追記 |

## 設計判断

- **ネタソース**: `onePointNeta` ではなく `noteNeta` シート（SS1）の L列をステータス管理列として使用
- **トンマナ参照**: `daily-xonepoint` が `style/style-xonepoint.md` を参照するのに対し、`writer-xstory` のスタイルガイドは SKILL.md 内に定義されているため、`.claude/skills/writer-xstory/SKILL.md` を直接参照する方式を採用
- **STEP 7 削除**: インフォグラフィック生成はストーリー投稿固有のニーズではなく、必要時に `make-infographic` スキルを別途呼ぶ形が適切と判断

## 確認結果

スキルが `/draft_xstory` で呼び出せることを確認。`metadata.yaml` への追記によりシステムリマインダーに `draft_xstory` が表示されることを確認。

## フロー概要

| STEP | 内容 |
|------|------|
| 1 | `noteNeta` シートから未使用ネタ数確認（5件未満なら自動補充） |
| 2 | 未使用ネタから1件選定（No順） |
| 3 | `/writer-xstory` を呼び出して約800文字のストーリー原稿を生成 |
| 4 | `/check-fact` でファクトチェック → トンマナ調整 |
| 5 | `noteNeta` シートの L列を「使用済み」に更新 |
| 6 | Gmail下書き作成（件名: `【Xストーリー】YYYYMMDD HH:MM:SS の原稿ができました`） |
