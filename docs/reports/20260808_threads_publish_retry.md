---
title: Threads転載の publish 一時エラー（素材が見つからない）をリトライするよう改修
date: 2026-08-08
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

8/7 朝のワンポイント解説（W003）の自動投稿は X 投稿・outputs 記録まで成功したが、**Threads 転載だけ失敗**していた（ログに `⚠ Threads 転載失敗`）。エラーは Threads API の **code 24 / subcode 4279009「素材が見つからない」**で、画像コンテナを作成した直後に publish（公開）しようとすると、そのコンテナがまだ見つからないという一時的な整合性遅延だった。

- 画像URL自体は正常（`pbs.twimg.com/...jpg` は後刻 HTTP 200）。画像の問題ではない。
- 失敗は開始6秒後の即エラー（90秒タイムアウトではない）＝publish 時のコンテナ未検出。
- X投稿の3秒後に転載しており、投稿直後の新しい画像＋作成直後のコンテナで Threads 側の処理が publish に間に合わなかった。
- 当時の `post_threads.py` は publish 失敗で即中断（`_api_post` が SystemExit）し、**リトライしなかった**ため転載が落ちた（X投稿は成功済みで非致命処理）。

## 実施内容

- **`scripts/post_threads.py` に publish リトライを追加**：
  - `_publish(token, user_id, creation_id, retries=5, wait=8)` を新設。publish が **一時エラー（本文に `4279009` / `"code":24` / `does not exist` / `"code":1` を含む）のときだけ** 8 秒間隔で最大5回リトライ。それ以外のエラーは従来どおり即中断。
  - `post_one()` の単一画像/テキスト・カルーセル両分岐で、コンテナ FINISHED 後に **3秒バッファ** を入れてから `_publish` を呼ぶよう変更。
- **8/7 分の手動再転載**：本文（X投稿一覧の該当行）＋画像（syndication の pbs URL）で `post_threads.py` を実行し Threads へ再投稿（`https://www.threads.com/@usephys1/post/DbwtcOokgsP`）、outputs に x_url 付きで記録。再転載時はリトライも発動せず一発成功（バッファのみで解消）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/post_threads.py` | `_publish`（一時エラー時リトライ）を追加、publish 前に3秒バッファ、両分岐の publish を `_publish` に置換 |

## 確認結果

- 構文チェック OK。
- 8/7 のワンポイント投稿を再転載し成功（permalink 取得・outputs 記録）。
- 一時エラー時はログに「publish 一時エラー、8秒後にリトライ (n/5)」を出す。恒久エラーは従来どおり中断。

## 今後の課題

- リトライしても解消しない恒久的な「素材が見つからない」（画像URLが本当に取得不能等）の場合は転載失敗のまま（非致命）。その場合は画像URLの propagate 待ちや別経路を検討。
- そもそも X 投稿の直後（数秒後）に転載しているのが一時エラーの一因。必要なら転載前に一定の待機を入れる案もあるが、今回はバッファ＋リトライで様子を見る。
