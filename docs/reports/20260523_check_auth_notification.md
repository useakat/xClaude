---
title: 認証トークン切れ通知スクリプト新設
date: 2026-05-23
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../history/20260523_check_auth_notification_session/)

## 背景・動機

gws の OAuth トークンが期限切れになると、全メール投稿・下書き作成 cron が「投稿対象メールなし」で静かに失敗する。エラーは `2>/dev/null` で捨てられているため、よーんは翌日まで気付けない。今回 gws トークン切れが原因で 1 日分の質問回答投稿が欠落したことをきっかけに、プロジェクト全体の認証監視の仕組みを作ることにした。

通知チャネルは Google 系が全滅しても独立して動く LINE を第一候補とし、LINE も切れた場合は Gmail API（`gcp/gmail_token.json`、gws とは別の OAuth トークン）にフォールバックする二段構成にした。

## 実施内容

- `scripts/check_auth.sh` を新設。gws・Drive token・X API・LINE の 4 トークンを毎日チェックし、異常があれば LINE → Gmail の順で通知
- `scripts/send_gmail_direct.py` を新設。`gcp/gmail_token.json`（`gmail.modify` スコープ、refresh_token あり）で Gmail API 認証し、gws とは独立してメールを送信
- cron に `0 2 * * *`（02:00 UTC = 11:00 JST）を追加。既存の他 cron より先に実行

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/check_auth.sh`（新規） | gws・Drive・X API・LINE を順にチェック。エラー時は LINE 通知 → Gmail フォールバック → ログのみ |
| `scripts/send_gmail_direct.py`（新規） | `gcp/gmail_token.json` で Gmail API 認証し `useakat@gmail.com` へ送信。uv run スクリプト形式 |
| `crontab` | `0 2 * * * /bin/bash /root/xClaude/scripts/check_auth.sh` を追加 |

## 設計判断

**通知チャネルを LINE ファーストにした理由**: gws・Drive・Gmail の OAuth が同時に切れるケースを想定すると、Google 系の手段は全て使えない可能性がある。LINE は Bearer token 方式で Google 認証とは完全に独立しており、最も信頼性が高い。

**LINE チェックを「ping 送信」で行う理由**: ステータス確認 API が存在しないため、実際にメッセージを送信して成否を判定する。毎日 11:00 JST に ping が届くことで「監視が正常に動いている」ことの確認にもなる。

**Drive token チェックを「refresh_token の有無」で行う理由**: `google-auth` ライブラリを使った実際のトークン検証はネットワーク通信が必要でシェルスクリプト内では重い。`drive_token.json` に `refresh_token` が存在すれば `sync_to_drive.py` 実行時に自動更新されるため、有無チェックで十分と判断した。

## 確認結果

`bash scripts/check_auth.sh` を実行し、gws・Drive・X API すべて正常 OK、LINE ping が届いた（エラー数 0）ことを確認。
