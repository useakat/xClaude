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
| `post_from_email.sh` | メール起点 X 投稿（cron 実行）。`--label <時刻ラベル>` でそのラベル付きだけを探し、無指定時は時刻ラベル付き（6時投稿 など）を除外する |
| `post_by_label.sh` | 投稿時間帯ラベル（`<時>時投稿`）が付いたメールを件名を問わずその枠で投稿する。各 `run_*_post.sh` が従来の件名検索の前に呼ぶ |
| `post_to_x.py` | X 投稿（直接実行） |
| `run_xonepoint_post.sh` | ワンポイント投稿の cron ラッパー |
| `run_question_post.sh` | 質問回答投稿の cron ラッパー |
| `run_xlong_post.sh` | 長文ストーリー投稿の cron ラッパー |
| `run_xshort_post.sh` | X短文投稿の cron ラッパー（20 時） |
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
| `note_price_rule.py` | note 記事の価格設定ルールの判定（200 PV で上げる／見直す／戻すか判断）。`note_article_daily.py` と `note_funnel_export.py` が共用 |
| `note_funnel_export.py` | note 導線ダッシュボード用の CSV（記事 × 価格区間の CVR¥ を含む 9 本）を発信記録シートから書き出す |
| `x_threads_corr.py` | X 投稿と Threads 同時転載の反応の相関を出す（outputs で結合、Spearman ρ・中央値・残差・散布図。X API は呼ばない）。`--since YYYY-MM-DD` で Threads 投稿日以降のペアに絞る（9/24 の配信変化より後だけを見るとき） |
| `note_funnel_measures.py` | note 導線 改善施策レジストリ（`docs/plans/note_funnel_measures.md`）の施策ごとに検証用の数値を出す（判定は reporter-weekly-ops） |
