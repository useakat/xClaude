---
title: 【threads投稿】メールを cron で Threads へ投稿する基盤を追加（分割スレッド・セルフリプ・画像対応）
date: 2026-07-11
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260711_threads_post_from_email/)

## 背景・動機

X の 【X短文投稿】 と同じ「Gmail メールを cron で拾って投稿」方式を Threads にも用意する。件名 **【threads投稿】** の INBOX メールを **毎日 7:00 / 12:00 / 17:00 / 20:00** に拾って Threads へ投稿し、outputs シートに `what_id="threads"` で記録する（07-08 に構築した Threads 取得基盤の投稿側）。

Threads は 1 投稿 500 文字上限なので、長い X 投稿はそのまま載らない。**超過分は返信チェーンでスレッド分割**し、X のセルフリプは本文スレッドの末尾に連結する。画像は X の CDN URL（`pbs.twimg.com`）をそのまま `image_url` に使う（公開URLなので再ホスト不要）。

## 実施内容

### Phase 0: スコープ追加・再認証
- Meta アプリに **`threads_content_publish`** 権限を追加し、`scope=threads_basic,threads_content_publish,threads_manage_insights` で再認証 → 長期トークンを `gcp/threads_token.json` に更新。
- 再認証用 `threads_token_exchange.py` に **IPv4 固定**を追加（IPv6 不通環境でのハング回避）。認可コードは短時間で失効するため、認可→交換を一気に行う運用に。

### Phase 1: 投稿スクリプト `scripts/post_threads.py`（新規）
- Threads 投稿 API（コンテナ作成 `POST /{user}/threads` → status=FINISHED 待ち → `threads_publish`）。
- **500字分割**: 段落→文→ハードの順で自然境界を優先して ≤500 字チャンクに分割。
- **スレッド化**: 1件目を publish→その id を次の `reply_to_id` に、と直前IDへ連結。画像は本文先頭に。
- **セルフリプ**（`--reply-text`/`--reply-image-url`）は本文末尾の投稿に `reply_to_id` で連結し、リプ画像はセルフリプ先頭に付与。
- 先頭投稿の permalink を `PERMALINK=` 行で出力（シェルが抽出）。

### Phase 2: `scripts/post_threads_from_email.sh`（新規）
- `post_from_email.sh` を雛形に、Gmail 検索（`subject:【threads投稿】 in:inbox -label:投稿済み`・クエリ失敗リトライ付き）→ `extract_tag.py` で `投稿文`/`画像URL`/`リプ`/`リプ画像URL` を抽出 → `post_threads.py` で投稿 → `投稿済み` ラベル＋INBOX 解除 → `record_output.py {permalink} threads` で記録。`--dry-run` で分割プレビューのみ。

### Phase 3: cron
- `scripts/run_threads_post.sh`（新規）を crontab に **`0 7,12,17,20 * * *`** で登録。

## 【threads投稿】メールのフォーマット
- 件名: `【threads投稿】{任意}`
- 本文タグ（任意タグは省略可）: `[投稿文]…[/投稿文]`（本文）/ `[画像URL]…[/画像URL]`（本文画像・先頭）/ `[リプ]…[/リプ]`（セルフリプ）/ `[リプ画像URL]…[/リプ画像URL]`（リプ画像）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/post_threads.py` | 新規。500字分割＋返信チェーン投稿（画像・セルフリプ対応） |
| `scripts/post_threads_from_email.sh` | 新規。【threads投稿】メール取り込み→投稿→ラベル→outputs 記録 |
| `scripts/run_threads_post.sh` | 新規。cron ラッパー（7/12/17/20） |
| `scripts/threads_token_exchange.py` | IPv4 固定を追加（再認証のハング回避） |
| （crontab） | `0 7,12,17,20 * * * run_threads_post.sh` を追加 |
| `record_output.py` | 無変更で流用（`{permalink} threads`。z01 専用処理は how_id=z01 のみ発火） |

## 設計判断

- **画像は X CDN URL をそのまま利用**（`pbs.twimg.com`）。Threads は image_url に公開URLを要求するため、過去 X 投稿の画像URLをメールに書けば再ホスト不要。
- **1本の返信チェーン**で本文＋セルフリプを表現（本文画像＝先頭、リプ画像＝リプ先頭）。
- 投稿バックエンドのみ Threads 化し、メール取り込み・ラベル・記録の骨格は X フロー（post_from_email.sh）を踏襲。record_output.py も無変更で流用。

## 確認結果

- 再認証後トークン有効（`/me` → username=usephys1、60日）。
- `post_threads.py --dry-run` で 500字分割（例: 780字→498+282／段落混じりの詰め込み）を確認。
- 全スクリプト構文チェック OK。cron 7/12/17/20 登録を確認。
- 実投稿の疎通確認（テキスト/画像）は、公開投稿かつ安全判定のため**ユーザーが `!` で実行**する手順を用意（本記録時点では未実施）。

## 今後の課題

- 実投稿テスト（テキスト/画像/スレッド分割/セルフリプ/`pbs.twimg.com` の Meta 取得可否）を次回実施。
- container status 待ち（画像）のタイムアウト実値の調整。
- 露出履歴のある Threads App Secret のリセット（未実施なら）。
