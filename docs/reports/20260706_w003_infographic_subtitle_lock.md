---
title: W003 図解テンプレートのサブタイトルを鉤括弧＋念押しで一字一句固定
date: 2026-07-06
tags: [style, wiki]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260706_w003_infographic_subtitle_lock/)

## 背景・動機

W003投稿のインフォグラフィック生成で、メインタイトルはプロンプト指定通り一言一句正確に再現される一方、サブタイトルだけがAI（NotebookLM）によって「〜の仕組みを解説する。」のような説明文に言い換えられる事象が複数の投稿（胃の使い捨て戦略・RTG無充電電源）で繰り返し発生していた。

原因は、サブタイトルが「概要を説明する普通の文」の形をしているため、AIが（メインタイトルのような「引用すべき決まり文句」ではなく）「言い換えてよい内容説明」だと解釈してしまうこと。プロンプト内の「テキスト描写の厳守」という一般指示だけでは、サブタイトル箇所に対する制約が弱かった。

## 実施内容

- `projects/w003/infographic_template/` 配下の全6テンプレート（`checklist.md`・`compare_contrast.md`・`pyramid.md`・`radial.md`・`step_flow.md`・`timeline.md`）のサブタイトル指定行を統一的に修正：
  - 変更前: `* サブタイトル（概要）：[サブタイトル]`
  - 変更後: `* サブタイトル（概要）：「[サブタイトル]」（この文字列を一字一句そのまま使用。要約・言い換え禁止）`
- 鉤括弧で囲み、制約をテキストのすぐ隣に置くことで、離れた場所にある一般指示より優先して認識されるようにした
- RTG無充電電源投稿での再生成（infographic_06〜08）で、サブタイトルが指定通り一字一句正確に再現されることを確認

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w003/infographic_template/checklist.md` | サブタイトル行を鉤括弧＋念押し形式に変更 |
| `projects/w003/infographic_template/compare_contrast.md` | 同上 |
| `projects/w003/infographic_template/pyramid.md` | 同上 |
| `projects/w003/infographic_template/radial.md` | 同上 |
| `projects/w003/infographic_template/step_flow.md` | 同上 |
| `projects/w003/infographic_template/timeline.md` | 同上 |

## 確認結果

RTG無充電電源投稿で `infographic_02.md`（step_flow型）のサブタイトル行を新形式に更新し、`infographic_06〜08.png` を再生成。3枚ともサブタイトルが「スマホが1日で切れる電源とは違う、原子力電池という発電方式」と指定通り一言一句正確に描画されることを確認した（修正前は同一プロンプトでも「〜の仕組みと驚異的な寿命を解説する。」等に変化していた）。

## 今後の課題

メインタイトルは常に正確だったため今回は対象外としたが、他の自由記述プレースホルダ（各ステップの一言説明等）でも同様の言い換えが将来発生した場合は、同じ鉤括弧＋念押し方式を横展開する。
