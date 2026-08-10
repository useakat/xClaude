---
title: note 記事の下書き保存を画像・サムネ込みで自動化（W002 フローに組み込み）
date: 2026-08-10
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260810_note_draft_images_eyecatch/)

## 背景・動機

W002（執念の物語の note 記事）の制作フローは、最終原稿 `output/index.md` を作るところで終わっていた。そこから先——note.com を開いて本文を貼り、セクション画像を1枚ずつ挿入し、サムネイルを設定する——は毎回すべて手作業だった。記事1本あたり画像は5〜7枚あり、貼り付け順の間違いも起きやすい。

`scripts/send_note_draft.py`（下書き保存スクリプト）は以前から存在したが、フローに組み込まれておらず（spec.md からも他スキルからも参照されていなかった）、かつ**テキストのみ**の対応で画像は扱えなかった。

調べたところ、note の非公開 API で**アイキャッチ設定も本文画像アップロードも実現可能**と分かったため、スクリプトを拡張してフローに組み込むことにした。

## 実施内容

**`send_note_draft.py` の拡張**

- **アイキャッチ（サムネ）設定**: `POST /api/v1/image_upload/note_eyecatch` に multipart で `file` / `note_id`（下書きの数値ID）/ `width` / `height` を送る。下書き作成時に返る note_id を同梱するため、`draft_save` 側での指定は不要。**MIME タイプの明示が必須**（省くと 500）なので拡張子から判定して付与する。画像サイズは Pillow で実寸を読む。
- **本文画像のアップロード**: 3段階。`POST /api/v3/images/upload/presigned_post` で S3 の presigned フォームを取得 → 返ったフィールドを**そのまま全て**含めて S3 へ multipart POST（`x-amz-security-token` が欠けると 403）→ 返ったキーで `<figure name=UUID id=UUID><img src="https://assets.st-note.com/img/<KEY>" width height></figure>` を本文 HTML に挿入。同一パスの重複アップロードはキャッシュで回避する。
- **CLI を argparse 化**: `--base-dir`（画像相対パスの基準）/ `--eyecatch` / `--no-images`（API 変更時の退避用）。既存の `send_note_draft.py "タイトル" < article.md` の呼び方は維持。
- **既存バグの修正**: 従来 `![alt](url)` は `!<a href=...>alt</a>` という壊れたリンクに変換されていた。http(s) の画像はアップロードせず figure に直接埋め込み、解決できなかった画像は元の Markdown 記法をそのまま残す（壊れたリンクを作らない）ようにした。失敗した画像は `failed_images` に集約し終了コード 2 で返す。

**W002 制作フローへの組み込み**

- `projects/w002/spec.md` にフロー16「note に下書き保存（画像・サムネ込み）」を新設（旧16 Drive アップロード→17、旧17 完了メール→18 に繰り下げ）。
- セクション画像は `output/index.md` に `![alt](images/<file>.png)` を**単独行**で書いておけば自動でアップロード＆figure 化される旨を明記（単独行でないと変換されない）。
- Verification に「note に下書き保存済み（`edit_url` を取得しユーザーに提示している）」を追加。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/send_note_draft.py` | アイキャッチ設定（`upload_eyecatch`）・本文画像アップロード（`upload_body_image`）を新規追加。`md_to_note_html` に `image_resolver` 引数を追加して figure 変換に対応。CLI を argparse 化（`--base-dir` / `--eyecatch` / `--no-images`）。画像記法が壊れたリンクになるバグを修正 |
| `projects/w002/spec.md` | フロー16「note に下書き保存（画像・サムネ込み）」を新設し以降を繰り下げ。Verification に下書き保存の項目を追加 |

## 設計判断

**なぜ公開まで自動化しなかったか**
有料エリア（`free_body` / `pay_body` / `separator` / `price`）は下書き保存 API ではなく公開 API（`PUT /api/v1/text_notes/{id}`）側の管轄で、これを触ると「公開そのものの自動化」になる。課金ラインの位置は記事ごとに判断が要る上、誤って公開してしまう事故のコストが高い。**下書き保存までを自動化し、有料エリア設定と公開は手動**という線引きにした。

**なぜ画像行を「単独行のみ」変換にしたか**
段落の途中に現れる画像記法まで figure 化すると、note のブロック構造（1ブロック＝1要素）が壊れる。W002 の画像はすべてセクション区切りに単独で置くため、単独行に限定するのが実態に合っている。

## 確認結果

- Markdown → note HTML 変換をローカルで検証。ローカル画像は `<figure><img src=... width height></figure>`、http(s) 画像はアップロードせず figure に直接埋め込み、解決失敗した画像は元の記法のまま残ることを確認した。
- `python3 -m py_compile` と `--help` で CLI の構文・引数を確認。Pillow 12.2.0 がインストール済みであることも確認。
- **note API への実通信は未検証**（外部への送信になるため、次回の記事制作時が初回実行になる）。仕様変更で落ちた場合は `--no-images` で本文のみ保存に退避できる。

## 今後の課題

- note API 実通信の初回検証（次回 W002 記事の制作時）。
- 非公開 API のため、note 側の仕様変更で壊れうる。壊れた場合は `--no-images` で退避しつつエンドポイントを再調査する。
