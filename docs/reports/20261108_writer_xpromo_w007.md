---
title: writer-xpromo を新設し、note 記事の 140 字販促投稿（W007）を投稿 cron に配線
date: 2026-11-08
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

W002 の公開済み note 記事へ X から誘導する投稿が、W001（長文）のセルフリプに限られていた。記事ごとに 140 字の販促投稿を作り、20 時枠の cron で定期的に流す仕組みを用意した。実装は 11/6（変更ログへの記載漏れを本日補完）。

## 実施内容

- `/writer-xpromo` を新設。W002 の公開済み記事から 1 本をランダムに選び（直近 14 日に販促した記事は除外）、記事正本 `output/index.md` を根拠に、別の場面・別のフック型で 3 案（本文 135〜140 字＋note 導線セルフリプ）を作る
- 本文に note への誘導を書かず、誘導はセルフリプ（1 文＋URL）に回す。採用案はよーんが選んでから、件名【note販促】の Gmail 下書きにする（X への投稿は行わない）
- `post_by_label.sh` に【note販促】→ W007 → `x_post_promo.log` を追加
- `run_xshort_post.sh`（20 時枠）の優先順を 【自己開示】→【note販促】→【X短文投稿】 に変更
- `ops_analyze-posts`・`reporter-daily` の型対応表に W007（note販促・短文）を追加、`metadata.yaml` に登録、Wiki ページ生成

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/writer-xpromo/SKILL.md` | 新規。候補プール作成・記事選択・3 案作成・提示と選択待ちの手順 |
| `.claude/skills/metadata.yaml` | writer-xpromo をコンテンツ制作に登録 |
| `scripts/post_by_label.sh` | 件名 6 種に【note販促】（W007）を追加 |
| `scripts/run_xshort_post.sh` | 20 時枠で W004 の次に W007 を検索 |
| `.claude/skills/ops_analyze-posts/SKILL.md` | 型対応表に W007 を追加 |
| `.claude/skills/reporter-daily/SKILL.md` | W007 を「note販促（短文）」として分類 |
| `docs/workflows/x-auto-post.md` | フロー図・枠の表に W007 を追記 |
| `docs/skills/writer-xpromo.md` | Wiki ページ（自動生成） |

## 確認結果

コミット `1f233ee`・`2220553` で反映済み。実投稿での動作確認は未実施（X 投稿は cron 以外で行わない規則のため）。
