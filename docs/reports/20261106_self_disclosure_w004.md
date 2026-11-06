---
title: 自己開示投稿（W004）を X 投稿の仕組みに組み込む
date: 2026-11-06
tags: [workflow, skill, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261106_self_disclosure_w004/)

## 背景・動機

2026-11-05 によーんが「自己開示系の投稿を始める」と決定した。目的はアカウントに人間味の温度を加えて共感を得ること。KPI は投稿からのプロフアクセス率とフォロー率。文章はよーんが全文手書きし、AI は書かない（brand.md の「想像で心情を捏造しない」と両立）。

既存の仕組みでは次が足りなかった。
- 11/1 の自己開示投稿（修士論文の思い出）は手動投稿で outputs に what_id が無く、日報では「その他」、週次・月次では「分類不明」になっていた
- X投稿一覧にはプロフアクセス・プロフ率・フォロー増の列があるが、週次・月次の集計がプロフ系の列を使っていなかった
- 自己開示用のメール件名（what_id を決める）が無かった

## 実施内容

- 競合投稿メール（毎朝 07:15）を、送信ではなく **Gmail 下書き**（件名【自己開示】）にした。本文は競合投稿の情報（タグ外）と、末尾の空の `[投稿文]` `[/投稿文]`。よーんが本文を書いて自分宛に送ると既存の投稿 cron が拾う。`--mode send` で従来の送信に戻せる
- `post_by_label.sh` の件名一覧に【自己開示】→ W004 を追加。20:00 枠のラベル無し時は【自己開示】を【X短文投稿】（z01）より先に探す
- `ops_monthly_metrics.py` に W004 ラベル、プロフアクセスの読込、`profile_rate_median` / `follow_per_10k` / `follow_per_profile`、比較群 `baseline_profile`、`w004_list` を追加
- `monetization_metrics.py` の型ラベルに W004「自己開示」を追加
- reporter-daily（対応表・並び順）、reporter-weekly-ops（取得列・W004 の KPI 小表・仮説 H8・テンプレート）、reporter-monthly-ops（W004 行・H8 総括）、ops_analyze-posts（HOW_ID 表）を更新
- `projects/w020/plan.md` を新規作成（目的・KPI・運用・書き方の注意）。ワークフロー 2 本とスクリプト一覧を更新
- SS2 の `what` シートに W004 を追記し、11/1 の投稿を `outputs` シートに遡って記録（日時 2026-11-01 22:15:00）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/x_competitor_daily_mail.py` | 送信 → 下書き作成（`--mode`）、件名【自己開示】、本文に案内と空の `[投稿文]` |
| `scripts/post_by_label.sh` | 件名に【自己開示】→ W004 を追加 |
| `scripts/run_xshort_post.sh` | ラベル無し時に【自己開示】を先に探す |
| `scripts/ops_monthly_metrics.py` | W004 ラベル、プロフアクセス読込、フォロー率などの指標、比較群 |
| `scripts/monetization_metrics.py` | 型ラベルに W004 |
| `.claude/skills/reporter-daily/SKILL.md` | 対応表・並び順 |
| `.claude/skills/reporter-weekly-ops/SKILL.md` | 取得列、W004 の KPI 小表、H8、テンプレート |
| `.claude/skills/reporter-monthly-ops/SKILL.md` | W004 行、H8 総括 |
| `.claude/skills/ops_analyze-posts/SKILL.md` | HOW_ID 表に W004 |
| `projects/w020/plan.md` | 新規 |
| `docs/workflows/x-auto-post.md`、`docs/workflows/x-competitor-daily-mail.md`、`docs/scripts/index.md` | 更新 |

## 設計判断

- フォロー増は投稿単位だと 0 が大半で中央値が使えないため、AC が取り込み済みの投稿だけ合算して IMP・プロフアクセスで割る。AC が空欄の投稿は 0 とせず「未取得」と書く
- 下書き方式にしたのは、W001・W003・z01 と同じ「cron が下書きを作り、よーんが送信する」型に揃え、返信の解析や新しいラベルを不要にするため
- 空の `[投稿文]` のまま送信しても、既存挙動（タグなし／空 → ラベル付与のみ）で投稿されない

## 確認結果

- `x_competitor_daily_mail.py --dry-run` で件名と本文（競合投稿がタグ外、末尾に空の `[投稿文]`）を確認
- `ops_monthly_metrics.py --month 2026-11` で W004 に n=1、プロフ率 0.55%、比較群 0.21% が出ることを確認。フォロー増は未取り込みのため「未取得」
- 未実施：下書きの本実行（明朝 07:15 の cron が最初の 1 件を作る）、送信後の `post_from_email.sh --dry-run` による検出確認（X への投稿は cron のみ）
- 次回確認：次の週次振り返り（W45、11/9）で W004 行・KPI 小表・H8 が入ること
