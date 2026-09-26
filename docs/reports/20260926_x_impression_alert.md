---
title: X投稿のインプ監視を新設（投稿から3時間以内に1,000インプでGmail通知）
date: 2026-09-26
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260926_x_impression_alert/)

## 背景・動機

「伸びている投稿」に投稿直後に気づく手段が無かった。日次記録・日報は翌日以降の集計で、9/19 の円周率バズ（1,098万インプ）でも、初動6〜12時間にリプが6割集中していたのに対し、リプ返しの中央値は投稿から32.6時間後だった（同日のバズ分析より）。伸び始めた投稿に早く反応（リプ返し・セルフリプでの導線）できるよう、閾値到達を自動でメール通知する仕組みが欲しかった。

X API v2 の `GET /2/users/:id/tweets` は `public_metrics.impression_count` を bearer token だけで返し、レート上限も 10,000 回/15分と十分だったため、cron ポーリングで実現できると判断した。

## 実施内容

- `scripts/x_imp_alert.py` を新規作成
  - 直近20件の自分の投稿を取得（`exclude=retweets`）。`referenced_tweets` に `replied_to` を持つ自分のリプライ（セルフリプ）は除外し、オリジナル投稿と引用RTを対象にする
  - 投稿から **3時間以内** かつ **1,000インプ以上** の投稿があれば `scripts/send_gmail.sh` で useakat@gmail.com に通知（件名例: `【Xインプ通知】投稿から3時間18分で451インプ到達`、本文は URL・種類・投稿時刻・経過時間・インプ／いいね／RT／引用／リプ／ブクマ・本文冒頭100字）
  - 通知済み tweet_id を `logs/x_imp_alert_state.json` に保存して二重通知を防止（7日で自動掃除）
  - `--dry-run`（送信・状態保存なし）、`--threshold`、`--hours` で一時的に条件を変えられる
  - 認証はリポジトリ直下 `.env` の `X_BEARER_TOKEN`（`post_to_x.py` と同じ読み方）
- `scripts/run_x_imp_alert.sh` を新規作成（cron 用ラッパー。`flock` で多重起動防止、ログは `logs/x_imp_alert.log`）
- VPS の crontab に `*/10 * * * * /bin/bash /root/xClaude/scripts/run_x_imp_alert.sh` を登録

よーんの指定で、**引用RTも対象に含め**、当初案にあった「3時間経過時点の最終値の通知」は採用しなかった。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/x_imp_alert.py` | 新規。インプ取得・判定・通知・状態管理 |
| `scripts/run_x_imp_alert.sh` | 新規。cron ラッパー（flock・ログ） |
| crontab（VPS、git 管理外） | `*/10 * * * *` を追加 |

`logs/x_imp_alert.log` と `logs/x_imp_alert_state.json` は実行時に生成される（未コミット）。

## 確認結果

- `--dry-run` で API 取得・対象判定・本文書式を確認（時間窓内0件で正常終了）
- `--dry-run --threshold 100 --hours 48` で直近3投稿が通知対象として整形されることを確認
- ラッパー経由の実行で状態ファイル・ログが生成されることを確認
- `--threshold 100 --hours 48` で実送信テストを行い、3通とも Gmail 送信成功（`send_gmail.sh` 経由）。3件は通知済みとして記録され、本番条件で再通知されないことを状態ファイルで確認

## 設計判断

- **通知はメール**（Claude Code のプッシュ通知ではなく）: cron から無人で動き、既存の `send_gmail.sh`（gws）をそのまま使えるため
- **10分ポーリング**: 検知遅れは最大10分＋X側の集計ラグ。レート上限（10,000回/15分）に対して1回/10分は無視できる負荷
- **状態ファイルで1投稿1回**: 閾値通過後も毎回通知しないため。閾値を段階化（5,000・1万）したくなった場合は state のキーを `tweet_id:threshold` にすれば拡張できる

## 今後の課題

- 閾値 1,000／3時間は最初の仮置き。通知が多すぎる・少なすぎる場合はスクリプト冒頭の `THRESHOLD` / `WINDOW_HOURS` で調整する
- 通知を受けた後の行動（リプ返し・セルフリプ導線の追加）は手動。バズ分析で提案した「バズ文脈に接続した導線をセルフリプで早く出す」運用と組み合わせて使う
