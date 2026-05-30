---
title: cron 定期実行ジョブ
description: サーバー上で crontab に登録されている定期実行ジョブ一覧
---

`crontab -l` で確認できる定期実行ジョブの一覧。すべて `/bin/bash` 経由で `scripts/` のシェルスクリプトを呼び出す。

## 一覧

| スケジュール | 実行タイミング | スクリプト | 内容 |
|---|---|---|---|
| `0 6 * * *` | 毎日 6:00 | `run_xonepoint_post.sh` | ワンポイント解説を X に投稿 |
| `0 12 * * *` | 毎日 12:00 | `run_question_post.sh` | 質問回答を X に投稿 |
| `0 17 * * 1,4` | 月・木 17:00 | `run_xlong_post.sh` | 長文ストーリーを X に投稿 |
| `0 */6 * * *` | 6時間ごと | `run_mond_letter_reply.sh` | mond レター回答の Gmail 下書きを作成 |
| `0 2 * * *` | 毎日 2:00 | `check_auth.sh` | Google / X API の認証チェック |

## 変更手順

```bash
# 編集
crontab -e

# バックアップを取ってから適用する場合
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d).txt
crontab -l | sed '...' | crontab -
```
