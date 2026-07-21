---
title: cron の Threads 投稿を複数画像（カルーセル）対応にし、record_output.py の記録ハングを再修正
date: 2026-07-21
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260721_threads_carousel_and_record_ipv4/)

## 背景・動機

7/21 の Threads 投稿 cron（6/17/20時）が3回とも同じ下書き（複数画像の投稿）で失敗し続けていた。調査で2つの独立した不具合が判明した。

1. **複数画像の投稿が不可**: X投稿一覧の「画像URL」列は複数画像を**改行区切り**で保持しており、`make_threads_draft.py` はそれをそのまま `[画像URL]` タグに入れ、`post_threads.py` が連結された文字列を単一 `image_url` として Threads に渡していた。Threads は複数画像を**カルーセル**（item container → CAROUSEL container → publish）で投げる必要があり、連結URLは「素材ダウンロード失敗」で 400 エラーになる。

2. **outputs 記録のハング再発**: 投稿成功後の `record_output.py` が 60 秒超ハング。原因は 7/12 に追加した IPv4 固定パッチが、7/13–15 の x_url 対応リファクタ（`9be5617`）で**消失**していたこと。この VPS は IPv6 不通のため googleapis の AAAA 優先解決で gspread 接続がハングする（read は運で通るが write で顕在化）。

## 実施内容

- **`post_threads.py` をカルーセル対応に改修**:
  - `parse_urls()` を追加し `--image-url` / `--reply-image-url` を空白・改行区切りで複数URLに分解。
  - `post_one()` を `image_urls`（リスト）受け取りに変更。2枚以上なら各画像を `is_carousel_item=true` の item コンテナ化 → `media_type=CAROUSEL` + `children=` でまとめ → publish。1枚以下は従来の単一 IMAGE/TEXT。上限20枚（超過は切り詰めログ）。
  - `reply_to_id` はカルーセルコンテナにも付与（セルフリプのカルーセルにも対応）。dry-run は「◯枚/カルーセル」を表示。
- **`record_output.py` に IPv4 固定パッチを再追加**（`import gspread` の前、threads 系と同じ3行）。再発防止のためコメントで消失経緯（`9be5617`）を明記。
- **実投稿で検証**: 詰まっていた動物園の下書き（4枚画像）をカルーセルで投稿成功。ラベル付与・INBOX解除・outputs 記録（x_url 付き）まで完走を確認。二重投稿・二重記録なし。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/post_threads.py` | `parse_urls()` 追加、`post_one()` を複数画像→カルーセル対応に変更、dry-run 表示更新 |
| `scripts/record_output.py` | IPv4 固定パッチ（`socket.getaddrinfo` を IPv4 優先）を再追加 |

## 確認結果

- dry-run: 4枚→「本文画像4枚/カルーセル」、1枚→「本文画像1枚」を確認。
- 実投稿: 動物園4枚画像 → カルーセルで投稿成功（https://www.threads.com/@usephys1/post/DbDcokaHazV）。
- `record_output.py`: 修正後 60秒超ハング → **1.3秒**で記録成功。テスト行は削除済み。outputs は動物園1件のみ（x_url= 元Xポスト）。

## 教訓・今後の課題

- **既存スクリプトを別目的でリファクタするとき、IPv4 固定パッチのような「環境依存の必須3行」を落としやすい**。この VPS で googleapis / graph.threads.net を叩く python には IPv4 固定を標準装備とし、リファクタ時に残すことを徹底する（record_output.py は 7/12・7/21 と2度落ちた）。
- カルーセルは 2〜20枚。動画（VIDEO item）混在も同じ枠組みで拡張可能だが現状は画像のみ。
