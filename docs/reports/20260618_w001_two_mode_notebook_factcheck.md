---
title: W001 X長文制作を2モード対応化＋両モードを NotebookLM ソースで担保
date: 2026-06-18
tags: [workflow, skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260618_w001_two_mode_notebook_factcheck/)

## 背景・動機

W001（X長文ストーリー）の投稿制作には、題材の入手元によって2つのパターンがある。

- **モードA（ネタ先行）**: `noteNeta` シートから未使用ネタを選んで作る
- **モードB（note記事あり）**: w002 で執筆済みの note 記事を元に作る

従来の spec.md はモードB（note記事あり）だけを前提にしていたため、モードA に対応できなかった。また、モードA はネタ情報だけが起点となるため、**本文の事実が裏付けのないまま書かれるリスク**があった。

そこで spec.md を2モード対応にしたうえで、w002（note記事制作）と同じ設計を踏襲し、両モードとも NotebookLM の notebook を根拠にして `/check-fact-lim`（ソース限定ファクトチェック）で事実を担保することにした。

## 実施内容

- **2モード対応**: 起動時に冒頭でモードを1回確認するフローを追加。モード判定後の題材確定までを分岐させ、それ以降（本文作成・各種チェック・保存）は両モード共通に統一。
- **モードB のフォルダ指定**: note 記事プロジェクトは `../../w002/` 配下にあり、ユーザーがフォルダを指定する。正確なフォルダ名でなく、**フォルダ名に含まれる単語だけの指定**にも対応（1件一致は採用／複数一致は候補提示／一致なしは一覧提示）。
- **モード名の統一**: spec の「モードA/B」を writer-xstory の「状況A/B」と一致させた（モードA＝状況A＝テーマ先行、モードB＝状況B＝note記事あり）。これに伴い `writer-xstory` と `draft_xstory` の状況A/B 表記も入れ替え。
- **NotebookLM ソース担保**: 制作フローに「投稿フォルダ作成」「notebook の準備」ステップを追加。モードAは `/research_setup-sources` で notebook を新規作成＋Deep Research でソース収集、モードBは w002 側の `notebook-id.md` を再利用。使う notebook ID は `{投稿フォルダ}/notebook-id.md` に保存。
- **ファクトチェックを切替**: 原則 `/check-fact-lim <notebook_id>`（notebook ソース限定）に変更。モードBで w002 側に notebook-id.md が無い古い記事のみ `/check-fact`（テキスト）にフォールバック。
- **パス修正**: 投稿フォルダパスの誤り（`projects/w003/` → `projects/w001/`）を修正。
- **Verification 更新**: notebook 整合・notebook-id.md 保存・フォーカスの両モード対応を反映。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w001/spec.md` | 入力モード（2パターン）セクション新設、制作フローを9→11ステップに再構成（フォルダ作成・notebook準備を追加、ファクトチェックを check-fact-lim へ）、Output に notebook-id.md 追加、Verification 更新、投稿フォルダパス修正 |
| `.claude/skills/writer-xstory/SKILL.md` | 状況A/B の定義を入れ替え（状況A＝テーマ先行、状況B＝note記事あり） |
| `.claude/skills/draft_xstory/SKILL.md` | STEP3 の「状況B（テーマ先行）」を「状況A（テーマ先行）」に修正 |

## 設計判断

- **「ソースだけを根拠に書く」の担保方法**: writer-xstory に notebook を参照させて執筆時に縛る案も検討したが、(1) websearch を切るだけではモデルの学習知識で書けてしまい縛りにならない、(2) 執筆中の notebook 逐次問い合わせは遅く物語執筆に不向き、という理由から、**執筆は自由に行い、`/check-fact-lim` で事実を notebook ソースに照合する案**を採用。w002 の writer_note-story も notebook を取らず spec＋check-fact-lim で担保する設計であり、これに統一した。
- **モードB の notebook**: 元の note 記事は w002 で notebook を作って書かれているため、新規作成せず w002 側の notebook を再利用する。

## 確認結果

- 修正後の spec.md を通読し、モードA/B のフローが題材確定→フォルダ作成→notebook準備→本文→check-fact-lim の順で一貫していることを確認。
- 参照スキル名・引数が実在の定義と一致することを確認（`research_setup-sources`＝テーマ引数、`check-fact-lim`＝第1引数 notebook_id）。
- notebook-id.md の保存書式（ID 1行）が w002 実例（`projects/w002/2026-05-30_SCEtoAUX/notebook-id.md`）と揃っていることを確認。

## 今後の課題

- モードA の実走で `{投稿フォルダ}/notebook-id.md` が生成され `/check-fact-lim` がその ID で動作するかの実地確認。
