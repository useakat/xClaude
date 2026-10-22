---
title: スクリプト一覧
description: scripts/ ディレクトリのスクリプト一覧
---

`scripts/` 以下の自動化スクリプト。Google サービス連携はすべて gws CLI 経由。

## Gmail 関連

| スクリプト | 用途 |
|---|---|
| `create_gmail_draft.sh` | Gmail 下書き作成 |
| `send_gmail.sh` | Gmail 送信 |
| `get_gmail_body.sh` | Gmail スレッド本文抽出 |
| `download_gmail_attachment.sh` | Gmail 添付画像ダウンロード |

## X 投稿関連

| スクリプト | 用途 |
|---|---|
| `post_from_email.sh` | メール起点 X 投稿（cron 実行） |
| `post_to_x.py` | X 投稿（直接実行） |
| `run_xonepoint_post.sh` | ワンポイント投稿の cron ラッパー |
| `run_question_post.sh` | 質問回答投稿の cron ラッパー |
| `run_xlong_post.sh` | 長文ストーリー投稿の cron ラッパー |
| `run_mond_letter_reply.sh` | mond レター回答の cron ラッパー |
| `check_auth.sh` | Google / X API 認証チェック |

## Google Drive 関連

| スクリプト | 用途 |
|---|---|
| `sync_to_drive.sh` | outputs/ → Drive 同期 |
| `drive_put.sh` | ローカルファイル → Drive アップロード/更新（フォルダ指定可） |
| `drive_get.sh` | Drive ファイル ID 指定でローカル DL |

## その他

| スクリプト | 用途 |
|---|---|
| `commit_and_sync.sh` | git commit & push |
| `notebooklm_manager.py` | NotebookLM クライアント |
| `send_note_draft.py` | note.com への下書き保存 |
| `note_article_daily.py` | note 記事ごとの日別 PV・スキを `note記事日次` に記録し、価格の変更を `note価格履歴` に区間として残す。価格設定ルール（200 PV で上げる／見直す／戻すか判断）の照合と改稿検知を行い、該当があればメールで知らせる（cron 05:55） |
| `note_funnel_export.py` | note 導線ダッシュボード用の CSV（記事 × 価格区間の CVR¥ を含む 9 本）を発信記録シートから書き出す |
| `note_funnel_measures.py` | note 導線 改善施策レジストリ（`docs/plans/note_funnel_measures.md`）の施策ごとに検証用の数値を出す（判定は reporter-weekly-ops） |
