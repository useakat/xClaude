---
title: X インプ通知の条件変更（2 時間以内に 1,500 インプ）と Threads views 通知の新設
date: 2026-10-11
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261011_imp_alert_threshold_threads_views_alert/)

## 背景・動機

X 投稿のインプ監視（`x_imp_alert.py`）は 9/26 の新設時から「投稿から 3 時間以内に 1,000 インプ」で通知していた。伸びる投稿にもっと早く気づくため、よーんの指示で条件を「2 時間以内に 1,500 インプ」に変更した。

あわせて、Threads でも同じ通知が欲しいとの要望。Threads Graph API で投稿一覧（投稿日時付き）と投稿ごとの `views` が取れ、トークンと Gmail 送信は X 版と共用できるので、X 版と同じ作りで Threads 版を新設した。閾値は「まずは X と同じ」でよーんが決めた。

## 実施内容

- `scripts/x_imp_alert.py`：`THRESHOLD` 1000 → 1500、`WINDOW_HOURS` 3 → 2。cron 間隔（30 分おき）は変更なし
- `scripts/threads_views_alert.py`（新設）：`/{user_id}/threads?since=…` で時間窓内のトップ投稿を取り、投稿ごとに `/{media}/insights?metric=views,…` を確認。閾値到達で `send_gmail.sh` によりメール通知（1 投稿 1 回、通知済みは `logs/threads_views_alert_state.json` に 7 日間保持）。IPv4 固定（この VPS は IPv6 不通）。`--dry-run` / `--threshold` / `--hours` は X 版と同じ
- `scripts/run_threads_views_alert.sh`（新設）：flock による多重起動防止付きの cron ラッパー。ログは `logs/threads_views_alert.log`
- crontab に `*/30 * * * *` で追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/x_imp_alert.py` | 閾値 1,500・時間窓 2 時間に変更 |
| `scripts/run_x_imp_alert.sh` | コメントの条件表記を更新 |
| `scripts/threads_views_alert.py` | 新設。Threads 投稿の views 監視 |
| `scripts/run_threads_views_alert.sh` | 新設。cron 用ラッパー |

## 設計判断

- **Threads の一覧 API はリプライを返さない**ので、セルフリプが対象に入ることはなく、X 版のような `replied_to` 除外は不要
- **Threads API は無料で従量課金なし**。X 版で課金対策として入れた `start_time` 絞り込みは不要だが、`since` で同じ絞り込みをしておき、insights の呼び出し数を時間窓内の投稿分に抑えた
- Threads の views は X のインプより伸びやすい（10/9 ニューホライズンズは 2 日で 35,435）。閾値は様子を見て変える前提で X と同じ値から始めた

## 確認結果

- `x_imp_alert.py --dry-run`：正常終了（時間窓内 0 件）
- `threads_views_alert.py --dry-run --hours 48 --threshold 100`：10/8〜10/9 の 4 投稿を拾い、件名・本文が X 版と同じ形式で組み立てられることを確認。本番条件（2 時間・1,500）では 0 件
- 実メール送信は該当投稿が出たときが初回

## 今後の課題

- 配布用の GAS 版（`scripts/gas/`）は 1,000 インプ・3 時間のまま
- Threads の閾値は通知の頻度を見て調整する
