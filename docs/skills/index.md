---
title: スキル一覧
description: Claude Code で使用できるスキルの一覧
---

スキルは `.claude/skills/` に定義されており、チャットで `/スキル名` と入力して呼び出す。

## コンテンツ制作

| スキル | 用途 |
|---|---|
| `/writer-xonepoint` | X ワンポイント解説投稿を作成 |
| `/writer-note` | note 記事（執念の物語形式）を執筆 |
| `/writer-xnews` | X ニュース投稿を作成 |
| `/writer-xstory` | X ストーリー投稿を作成 |
| `/note-quick` | スタイルだけ適用してチャットに本文出力（軽量版） |
| `/daily-xonepoint` | ワンポイント投稿の全工程を全自動実行 |

## リサーチ

| スキル | 用途 |
|---|---|
| `/research` | 一般調査 |
| `/research-plan` | Deep Research プロンプト設計 |
| `/deep-research` | 調査プロンプトを基に Web 深掘り調査 |
| `/research-trivia` | ワンポイントネタ発掘 |
| `/research-note-projectx` | note 記事ネタ発掘 |
| `/analyze-target` | persona / pain / what 設計 |

## 品質チェック

| スキル | 用途 |
|---|---|
| `/check` | 一般品質レビュー |
| `/check-fact` | ファクトチェック付き品質レビュー |

## 画像・同期

| スキル | 用途 |
|---|---|
| `/make-infographic` | NotebookLM でインフォグラフィック生成 |
| `/notebooklm` | NotebookLM 操作 |
| `/sync-to-drive` | outputs/ → Drive 同期 |
| `/sync-to-sheets` | database/CSV → Sheets 同期 |
| `/hashtag-note` | note ハッシュタグ選定 |
