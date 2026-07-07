---
title: Threads 投稿一覧の API 取得・記録基盤を新規構築
date: 2026-07-08
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260708_threads_posts_api_integration/)

## 背景・動機

X と同様に、Threads（Meta の SNS）の自分の投稿一覧とメトリクスを記録・分析したい。調査の結果、**Threads 公式 API（`graph.threads.net`）で投稿一覧・インサイトを取得可能**（無料・自分のデータはテスターモードで即時利用・App Review 不要）と判明したため、取得〜記録の基盤を構築した。記録先は「発信記録」スプレッドシート（`1_0317…`。既存「X投稿一覧」あり）に新設した「Threads投稿一覧」シート。スコープは取得・記録のみ（投稿はしない）。

X はアナリティクス CSV の手動取り込みが必要だが、Threads は API 直取得のため**より自動化度が高い**。

## 実施内容

### Phase 0: 認証（OAuth・一度きり）
- Instagram をクリエイター（プロフェッショナル）化 → Meta 開発者アプリ作成（Threads ユースケース）→ 自分をテスター登録。
- OAuth（`threads_basic`+`threads_manage_insights`）で認可コード取得 → 長期トークン（60日）に交換し `gcp/threads_token.json`（gitignore 済み）に保存。
- ハマりどころ: リダイレクトURIは localhost 不可（`https://httpbin.org/get` を使用）、`threads.net`→`threads.com` リダイレクトで client_id が落ちるため **`www.threads.com/oauth/authorize` を直接使用**、`client_id` は **Threads App ID**（アプリ全体の App ID とは別）。

### Phase 1: シート新設
- 「Threads投稿一覧」（19列）: 投稿日時／投稿URL(permalink)／本文／種類／文字数／画像URL／親投稿URL／**X投稿URL(手動)**／views／いいね／リプライ／リポスト／引用／シェア／エンゲージメント合計／エンゲ率／いいね率／リポスト率／最終更新。

### Phase 2: 取得スクリプト
- `scripts/fetch_threads_posts.py`: `GET /me/threads`（全ページ）→ 各投稿 `id` で `GET /{id}/insights`（views/likes/replies/reposts/quotes/shares）→ **permalink 突合で upsert**（既存行はメトリクス更新、新規は追記）。**H列「X投稿URL」は手動列として非上書き**。

### Phase 3: 自動化
- `run_threads_fetch.sh`（日次取得）を **毎朝5:00 cron**、`run_threads_token_refresh.sh`（`th_refresh_token`・secret 不要）を **月次 cron（1日4:00）** に登録。

## 重要な技術ポイント

- **IPv4 固定**: この VPS は IPv6 が不通で、`graph.threads.net` が IPv6 のみ解決される環境のため、python の `socket.getaddrinfo` を IPv4 に固定してハングを回避（`fetch_threads_posts.py`／`threads_token_refresh.py`）。curl は `-4` で回避。
- **トークン更新は secret 不要**: `th_refresh_token` はトークン自身で延長できるため、初回交換後は App Secret を保持しない。
- **クラウド routine ではなくローカル cron**: トークン `gcp/threads_token.json` は gitignore でクラウド checkout に無いため、取得はローカル cron で行う。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/fetch_threads_posts.py` | 新規。投稿＋インサイト取得→シート permalink 突合 upsert（IPv4固定） |
| `scripts/threads_token_refresh.py` | 新規。長期トークンを `th_refresh_token` で月次延長 |
| `scripts/threads_token_exchange.py` | 新規。認可コード→長期トークン交換（初回セットアップ用） |
| `scripts/run_threads_fetch.sh` | 新規。日次取得 cron ラッパー（5:00） |
| `scripts/run_threads_token_refresh.sh` | 新規。月次トークン更新 cron ラッパー |
| （発信記録スプレッドシート） | 「Threads投稿一覧」シート新設（19列） |
| （crontab） | `0 5 * * *` 取得・`0 4 1 * *` トークン更新 を追加 |

## 確認結果

- トークン疎通: `/me` → username=usephys1、`/me/threads` で投稿取得を確認。
- `fetch_threads_posts.py --dry-run` で 17 件取得を確認 → 本実行で 17 件をシートに追記。
- **upsert 冪等性**: 再実行で「新規0・既存17更新」＝重複しないことを確認。
- `run_threads_fetch.sh` テスト実行 rc=0。cron 2本の構文チェック・登録を確認。

## 今後の課題

- 露出した Threads App Secret のリセット（ユーザー作業。今のトークン運用・更新は secret 不要のため影響なし）。
- 親投稿URL（返信/引用元）は現状空。必要なら quoted_post/replied_to のフィールド取得を追加。
- 分析（`ops_analyze-posts` 等）を Threads にも使う場合は列マッピングの調整が必要。
- `threads_token_exchange.py` は初回用ユーティリティ（IPv6 環境では curl -4 での交換を推奨。今回は手動 curl で実施）。
