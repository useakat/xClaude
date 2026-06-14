---
title: writer-xstory を「フォーカス→冒頭フック→本文」の3段階対話制作に再設計
date: 2026-06-14
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260614_writer_xstory_three_stage_interactive_session/)

## 背景・動機

X長文投稿では、(1) note 記事のどの一場面／テーマのどの切り口を入口にするか（フォーカス）、(2) 冒頭フックをどう書くか、が IMP を左右する最重要の創作判断である。これらを一括生成に任せず、候補を提示してよーんが選び、決めた冒頭に続けて本文を書く流れにしたかった。

この3段階プロセスは W001/SCEtoAUX 案件固有ではなく、すべての X長文投稿に共通する制作クラフトのため、案件固有の `spec.md` ではなく共通スキル `writer-xstory` に実装することにした。あわせて、note 記事を先に書かず noteNeta シートのテーマ先行で X長文を書くケースにも対応する必要があった。

## 実施内容

- `writer-xstory` の「## 手順」を3段階対話制作に再設計した。
  - 事前準備で**入力状況A（note記事あり）/B（テーマ先行）**を判定。
  - ステージ1: フォーカス候補3つ → `draft/focus-candidates.md` 保存 → 相談・回答待ち → 「## 決定」追記。
  - ステージ2: `hook-patterns.md` の5型すべてで各3案=計15案 → `draft/hook-candidates.md` 保存 → 相談・回答待ち → 「## 決定」追記。
  - ステージ3: 決定フックに続けて本文（直後に具体3点セット）→ 字数・完結チェック → 保存。
- `draft_xstory` を対話前提に修正。冒頭の「自動実行・ユーザー入力を待たない」を STEP 3 は3段階対話で相談する前提に改め、STEP 3 を状況B（テーマ先行）の3段階対話制作に更新（テーマ情報の引数渡しは維持、STEP 1・2・4〜6 は維持）。
- W001 の `spec.md` をスリム化。制作フローの番号飛び（1→3）を解消して連番化し、本文作成を `/writer-xstory` 参照に置換。Output に中間生成物（focus/hook候補）、Verification にフォーカス決定・フック決定の確認項目を追記。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/writer-xstory/SKILL.md` | 「## 手順」を3段階対話制作（事前準備＋ステージ1〜3）に再設計。冒頭フック節を参照用に整理、保存手順に中間生成物を明記 |
| `.claude/skills/draft_xstory/SKILL.md` | 冒頭の自律実行前提を STEP 3 対話前提に修正。STEP 3 を状況B の3段階対話制作に更新 |
| `projects/note-story/2026-05-30_SCEtoAUX/xstory/spec.md` | 制作フローを連番化し本文作成を /writer-xstory 参照にスリム化。Output・Verification に focus/hook 段階ファイルと決定確認項目を追記 |

## 設計判断

- 移植先を `spec.md` ではなく `writer-xstory` にしたのは、3段階の制作クラフトが案件横断で共通だから。spec.md は正本パス・出力命名・セルフリプ等の案件固有部分のみ残した。
- `draft_xstory`（自律ルーティンとして記述）は crontab・agents/・scripts のいずれにも未登録で、現状は手動呼び出し。よって対話化しても止まる自動運用はなく、対話前提への変更を選択した。
- フックは hook-patterns.md の5型すべて・各3案=15案を提示する方針（よーん確認済み）。

## 確認結果

- 3ファイルの編集が反映されていることを確認。`writer-xstory` の手順がステージ1〜3に、`draft_xstory` STEP 3 が3段階対話に、`spec.md` 制作フローが連番（番号飛びなし）かつ /writer-xstory 参照になっている。
- 実運用での通し確認（状況A の対話制作、状況B のテーマ先行、draft_xstory の通し）は次回の実制作時に行う。
