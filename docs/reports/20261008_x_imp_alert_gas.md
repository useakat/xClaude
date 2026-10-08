---
title: X インプ監視の GAS 版（配布用）を作成
date: 2026-10-08
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261008_x_imp_alert_gas/)

## 背景・動機

X投稿のインプ監視（投稿から3時間以内に1,000インプでメール通知）を欲しいという人がいたが、その人は Claude Code どころか自分の PC を持っていない。よーんが代わりにホストする案は「僕の代行はだめ」で却下。本人のスマホだけで設定でき、本人の Google アカウントで動く形が必要だった。

Google Apps Script（GAS）なら、ブラウザだけでコードを貼り付けて時間トリガーを設定でき、`UrlFetchApp` で X API を叩き `MailApp` で Gmail に送れる。サーバーも課金も不要（X API の従量課金のみ）。同種の既製サービス（Hypefury / Tweet Hunter / Typefully の auto-plug）はエンゲージメント閾値で自動セルフリプする機能で、インプ閾値のメール通知そのものを提供するサービスは見つからなかった。

## 実施内容

- `scripts/gas/x_imp_alert.gs` を新規作成（Python 版 `x_imp_alert.py` の移植）
  - 冒頭の `CONFIG` に `X_BEARER_TOKEN` / `X_USERNAME` / `NOTIFY_TO` / `THRESHOLD`（1,000）/ `WINDOW_HOURS`（3）/ `CHECK_INTERVAL_MIN`（30）をまとめ、利用者はここだけ書き換える
  - 利用者が実行する関数: `setup()`（設定検証 → ユーザー ID 解決 → 時間トリガー登録）、`teardown()`（トリガー削除）、`testRun()`（送信なしの判定確認）、`sendTestMail()`（メール疎通）、`check()`（トリガーから呼ばれる本体）
  - 判定は Python 版と同じ: `start_time` で時間窓内の投稿だけ取得（従量課金対策）、`exclude=retweets`、自分のリプライは除外、オリジナル投稿と引用RTが対象、1投稿1回のみ通知
  - ユーザー名 → ID の解決結果を Script Properties にキャッシュ（毎回 `/2/users/by/username` を叩かない）
  - 通知済み状態は Script Properties の `STATE` に保存し、7日で掃除
  - API エラー（401 トークン不正 / 402 クレジット切れ / 403 権限 / 429 レート）は原因のヒント付きで**1回だけ**メール通知し、復旧したらリセット（毎回エラーメールが来るのを防ぐ）
  - 時間トリガーは GAS の制約で 1 / 5 / 10 / 15 / 30 分のいずれかに丸める
- `scripts/gas/README.md` を新規作成（配布用セットアップ手順）
  - 費用の目安表（10投稿/日・30分チェックで月 約 $2）
  - X Developer 登録 → Bearer Token 発行 → クレジット購入の手順（利用目的の英文テンプレ付き）
  - GAS への貼り付け → CONFIG 編集 → `setup` 実行 → 権限許可 → `testRun` / `sendTestMail` で確認 → 止めるときは `teardown`
  - トラブルシューティング（届かない・エラーメールの読み方）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/gas/x_imp_alert.gs` | 新規。GAS 版の本体（約 260 行） |
| `scripts/gas/README.md` | 新規。スマホだけで設定するための手順書 |

## 設計判断

- **GAS を選んだ理由**: 利用者側に必要なのは Google アカウントと X アカウントだけ。VPS・Claude・PC が不要で、よーんがホストしない（トークンも利用者本人が持つ）
- **メールは MailApp**: Gmail API の OAuth 設定が不要で、スクリプト実行者の Gmail から送られる。1日の送信上限（無料アカウント 100 通）は通知頻度からして十分
- **エラー通知は1回だけ**: 30分ごとの実行で毎回エラーメールが来ると使い物にならない。復旧時にフラグを消して、次のエラーでまた1回通知する
- **ユーザー ID のキャッシュ**: `/2/users/by/username` も従量課金の対象になりうるため、初回だけ解決して保存する

## 確認結果

- Node.js で `UrlFetchApp` / `MailApp` / `PropertiesService` / `ScriptApp` のモックを用意し、`run_` の判定ロジック（時間窓・閾値・リプライ除外・二重通知防止・状態の掃除・エラー通知の1回制限）が Python 版と同じ結果になることを確認
- 実際の GAS 環境での実行は未確認（よーん自身は Python 版を VPS で運用しているため）。利用者に渡す際は README の `testRun` → `sendTestMail` の手順で疎通を確認してもらう

## 今後の課題

- 実際の利用者が GAS 環境で `setup` を通したときの権限ダイアログや X Developer 登録の詰まりどころを README に反映する
- 閾値の段階化（5,000・1万）が欲しくなった場合は、状態キーを `tweet_id:threshold` にすれば拡張できる（Python 版と同じ設計）
