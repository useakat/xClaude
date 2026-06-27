---
title: z01 短文投稿の cron 自動化（投稿スクリプト新設・writer-xshort 周辺調整）
date: 2026-06-27
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260627_z01_xshort_post_cron/)

## 背景・動機

z01（X短文投稿）プロジェクトでは、`writer-xshort` が `【X短文投稿】` 件名で Gmail 下書きを作成する。これを既存の `post_from_email.sh` 方式（メール下書きを拾って X 投稿する cron 設計）に乗せ、定時自動投稿できるようにする。

既存の `run_xonepoint_post.sh`（`【ワンポイント解説】` / W003）と同型のラッパーを用意すれば、原稿作成（下書き）と投稿（cron）を分離した既存運用にそのまま統合できる。

## 実施内容

- `scripts/run_xshort_post.sh` を新設（`run_xonepoint_post.sh` と同型）。`post_from_email.sh "【X短文投稿】" z01 x_post_short.log` を実行し、`【X短文投稿】` 下書きを X へ投稿する。
- crontab に `0 7,13,19 * * *` で登録（毎日 7:00 / 13:00 / 19:00）。
- 下書き作成用 `scripts/run_xshort_draft.sh` を追加（`/writer-xshort` を `claude -p` で全自動実行 → Gmail 下書き作成）。当初 6:00〜22:00 毎時の cron を張ったが、運用方針変更で cron は削除し、スクリプトは手動実行用に残置。
- `writer-xshort` の説明文を「投稿は行わず Gmail 下書き作成のみ」と実態どおりに正確化。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/run_xshort_post.sh` | 新規。`post_from_email.sh "【X短文投稿】" z01 x_post_short.log` を exec するラッパー（cron 7/13/19時） |
| `scripts/run_xshort_draft.sh` | 新規。`/writer-xshort` を `claude -p --model opus` で実行し Gmail 下書きを作成（手動実行用・cron なし） |
| `.claude/skills/writer-xshort/SKILL.md` | description・冒頭文を「投稿せず下書き作成のみ」と正確化 |
| （crontab） | `0 7,13,19 * * * run_xshort_post.sh` を追加 |

## 設計判断

- **投稿スクリプト名は `run_xshort_post.sh`（"post" を含む）**：実際に X へ投稿する処理であり、兄弟（`run_xonepoint_post.sh` 等）と命名を揃えるのが正確。安全判定回避目的のリネームは行わない方針（過去に分類器が「回避目的の改名」をブロックした経緯あり）。
- **下書き作成（draft）と投稿（post）でスクリプトを分離**：原稿生成と X 投稿を別 cron・別ログで管理する既存運用に合わせた。

## 確認結果

- `run_xshort_draft.sh` を手動実行（よーんが `!` で実行）→ writer-xshort が noteNeta[33] を選び 138字を生成、Gmail 下書き作成まで完走を確認（exit 0）。
- `run_xshort_post.sh` は `bash -n` 構文チェック OK。crontab に 7/13/19 時で登録済みを確認。

## 今後の課題

- `run_xshort_post.sh` の実投稿は cron 初回稼働（次回 7:00/13:00/19:00）で確認予定。
- `run_xshort_draft.sh` は cron 未登録（手動運用）。定期下書き作成が必要になれば改めて cron 化を検討。
