---
title: 日次記録シート V列に Threads フォロワ数を毎朝自動記録
date: 2026-07-25
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260725_threads_followers_daily_record/)

## 背景・動機

「日次記録」シート（発信記録スプレッドシート `1_0317…` のタブ）は、GAS `gas/DailyMetricsRecord.js` が毎朝、前日日付の行へ X フォロワ数・note フォロワ数などを書き込んでいる。V列（22列目）にはヘッダ「threads フォロワ数」が用意済みだが、記録元が無くデータが空だった。ここに Threads のフォロワ数を毎朝自動で埋めたい。

実装場所は **ローカル python + cron** を選択。Threads API は60日ローカルトークン（`gcp/threads_token.json`、月次で自動更新）で叩けるため、GAS 側にトークンを持たせる（60日ごとに手動更新が必要）方式より保守が楽。サービスアカウント（charming-well）は同スプレッドシートに書き込み権限があり（`fetch_threads_posts.py` 実績）、その IPv4固定＋gspread 認証パターンを流用できる。

## 実施内容

- **`scripts/record_threads_followers.py` を新規作成**:
  - Threads insights `GET /{user_id}/threads_insights?metric=followers_count` の `data[0].total_value.value` でフォロワ数を取得（`threads_token.json` の access_token/user_id を使用）。
  - サービスアカウントで「日次記録」シートを開き、**前日（JST）**の日付（`yyyy/MM/dd`）に一致する A列の行を探し、**V列(22)** にフォロワ数を書き込む（`update_cell`、冪等に上書き）。
  - 行が見つからない場合の保険として A=日付/B=曜日/V=値 の行を追記（GAS 5:00 → 本スクリプト 5:30 の順なので通常は既存行が見つかる）。
  - IPv4固定パッチ、`--dry-run`、`--date YYYY/MM/DD`。ログは `logs/threads_followers.log`。
- **`scripts/run_threads_followers.sh` を新規作成**（`GOOGLE_SERVICE_ACCOUNT_KEY` を export して python を実行する cron ラッパー）。
- **cron 追加**: `30 5 * * *`（GAS の後、5:30）。
- **`gas/DailyMetricsRecord.js`**: `setupDailyTrigger` の `.atHour(6)` を `.atHour(5)` に変更（GAS を先に走らせ前日行を用意するため。トリガーの実再設定は Apps Script 側で `setupDailyTrigger` 再実行が必要）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/record_threads_followers.py` | 新規（Threads insights→日次記録 V列(22)、前日行、冪等） |
| `scripts/run_threads_followers.sh` | 新規（cron ラッパー、5:30） |
| `gas/DailyMetricsRecord.js` | `setupDailyTrigger` の `.atHour(6)`→`.atHour(5)` |
| crontab | `30 5 * * * run_threads_followers.sh` を追加 |

## 確認結果

- dry-run: フォロワ数 46・前日 2026/07/24（行255）を検出、書き込みなし。
- 本実行: `日次記録!V255 = 46` を mcp-gsheets で確認（表示は「46.0」だが値は 46）。
- 冪等性: 再実行で A列の行数が 255→255 のまま（行の重複なし・V を上書きするだけ）。
- cron 追加を確認（5:00 run_threads_fetch → 5:30 run_threads_followers の並び）。

## 設計判断

- **GAS ではなくローカル python**: Threads トークンは60日で失効し月次でローカル自動更新される。GAS にトークンを置くと同期できず約60日ごとに手動更新が必要になるため、自動更新トークンを使えるローカル側に実装した。
- **前日行に現在値**: GAS が X フォロワ等を「前日行に当朝の現在値」で書く運用に合わせ、Threads フォロワ（スナップショット）も前日行に入れる。
- **順序の担保**: GAS が前日行を作ってから書くよう、GAS 5:00 → フォロワ 5:30 にした。

## 今後の課題

- GAS のトリガー実再設定（5:00）は Apps Script 側の操作が必要（コード変更だけではスケジュールは変わらない）。
- 将来 reporter-monthly に「Threads フォロワ純増」を追加するなら、この V列が入力源になる。
