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

## Google Drive / Sheets 関連

| スクリプト | 用途 |
|---|---|
| `sync_to_drive.sh` | outputs/ → Drive 同期 |
| `drive_put.sh` | ローカル md → Drive アップロード/更新 |
| `drive_get.sh` | Drive ファイル ID 指定でローカル DL |
| `sync_to_sheets.sh` | database/ → Sheets 同期 |

## データ管理

| スクリプト | 用途 |
|---|---|
| `csv_reader.py` | ネタ一覧取得 |
| `update_neta_status.py` | ネタのステータス更新 |
| `sheets_manager.py` | ローカル CSV 管理（add/list/mark-used） |
| `record_output.py` | 投稿記録を outputs.csv に追記 |

## その他

| スクリプト | 用途 |
|---|---|
| `commit_and_sync.sh` | git commit & push |
| `notebooklm_manager.py` | NotebookLM クライアント |
| `send_note_draft.py` | note.com への下書き保存 |
