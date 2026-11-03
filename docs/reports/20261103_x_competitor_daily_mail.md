---
title: 競合アカウントの投稿を期間指定で X競合分析シートに記録し、毎日 1 件ずつ古い順にメールする
date: 2026-11-03
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261103_x_competitor_daily_mail/)

## 背景・動機

よーんの依頼：@ossanworld（数値流体力学研究者。研究生活のドラマを長文で書く、発信軸に近いアカウント）の投稿を 6 か月前から 1 か月分取得して「X競合分析」に新しいシートを作り、毎日古いものから 1 件ずつメールで読む。一度送った投稿には送信済みマークを付ける。

競合の投稿は 2026-08 に @galileo_fun の全件を X API で取得してシート化した前例がある（折り返し位置の設計に使った）が、その場限りのコードで、再利用できる形にはなっていなかった。今回は「取得してシートを作る」と「毎日 1 件送る」を汎用スクリプトにし、次のアカウント・期間に切り替えられるようにした。

よーんの決定：期間 2026-05-01〜05-31／送信 07:15／スレッドは 1 通にまとめる。

## 実施内容

- **取得** `scripts/fetch_x_user_posts.py --username ossanworld --start 2026-05-01 --end 2026-05-31`：X API（`users/by/username` → `users/{id}/tweets`、`start_time`/`end_time`、100 件ページング、従量課金）で 302 件を取得し、生データを `logs/x_user_posts/` に保存。リポスト・他人へのリプライ・**本文が「@相手」で始まる投稿**を除外し、自分の投稿への返信は「ツリー続き」として残す（galileo_fun シートと同じ）。長文は `note_tweet` の全文。「X競合分析」に新シート `ossanworld 2026-05` を作成（14 列・古い順・188 行：単独／ツリー先頭 154、ツリー続き 34）
- **メール** `scripts/x_competitor_daily_mail.py --sheet "ossanworld 2026-05"`：N 列「送信済み」が空の単独／ツリー先頭のうち最古を選び、ツリー先頭なら同じ会話IDの続き行も「── 続き 2/5 ──」で同じメールに並べ、全行に送信日を書く。件名 `【競合投稿】@ossanworld 2026-05-01（1/154）`。全件送り終えたら「送り終えました」を 1 回だけ送り（`logs/x_competitor_mail_state.json`）、以後は何もしない
- **cron** `scripts/run_x_competitor_daily_mail.sh`：07:15、flock、対象シートは冒頭の `SHEET` で切り替え

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/fetch_x_user_posts.py` | 新規：X API 取得・選別・シート作成（`--dry-run` / `--from-json` / `--overwrite`） |
| `scripts/x_competitor_daily_mail.py` | 新規：未送信最古を 1 件メール・送信済み記入・完了通知 |
| `scripts/run_x_competitor_daily_mail.sh` | 新規：cron ラッパー |
| `docs/workflows/x-competitor-daily-mail.md`、`docs/scripts/index.md` | 新規・3 行追加 |
| `.gitignore` | `/logs/x_user_posts/` を追加 |
| crontab | `15 7 * * * run_x_competitor_daily_mail.sh` を追加 |

## 設計判断

- **他人との会話の自己返信を本文で判定**：参照先が消えた返信は X API が `referenced_tweets` と `in_reply_to_user_id` を返さず、返信フラグだけでは「@dobumead 上に書いたように…」のような会話の続きがツリー続きに混ざった（初回 221 行 → 修正後 188 行）。X は返信本文の先頭に @相手 を付けるので、本文が自分以外の @ で始まるものを一律で除外した
- **シートは RAW で書く**：ツイートID を USER_ENTERED で入れると数値扱いで精度が落ちるため
- **生データを JSON に残す**：従量課金なので取り直さずに `--from-json --overwrite` でシートを作り直せるようにした（今回の修正でも使った）
- **1 通の単位はスレッド**：1 行＝1 通だと長文スレッドが日をまたいで途切れる

## 確認結果

- 取得 302 件 → 記録 188 行。X API 4 ページ、約 3 秒
- `x_competitor_daily_mail.py --dry-run` で 1 通目（5/1「ヴァンリア教授は…」、IMP 8,391）の本文を確認
- よーんの承認後に 1 通目を実送信し、N2 に `2026-11-01` が書かれたことを確認。crontab に登録（翌朝は 2 通目から）

## 今後の課題

- 全 154 通（約 5 か月）を送り終えたら次のアカウント・期間を決めて `SHEET` を切り替える
- 自分の投稿への返信でも「ツリー続き」判定が甘いものが少数残る可能性がある（会話の途中で他人のリプライに答えた本文に @ が付かないケース）
