---
title: note 本文画像アップロードを API 仕様変更に追従（filename・埋め込みURL）
date: 2026-08-12
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260812_note_body_image_upload_api_fix/)

## 背景・動機

2026-08-10 に「note 記事の下書き保存を画像・サムネ込みで自動化」（`send_note_draft.py`）を整備し、W002 spec のフロー16 に組み込んだ。手作業は有料エリア設定と公開だけに縮小したはずだった。

ところが今回（オポチュニティ記事）で初めて**実運用の記事**を通したところ、本文画像11点が**すべて失敗**した。

```
"failed_images": [
  "images/砂の星に降りた_太陽で生きる機械_図解_01.png（HTTPError: 400 Client Error:
   Bad Request for url: https://note.com/api/v3/images/upload/presigned_post）",
  ... 11件すべて同じ 400
]
```

アイキャッチ（サムネ）は成功していた。両者はエンドポイントが違う（本文＝`/api/v3/images/upload/presigned_post`、アイキャッチ＝`/api/v1/image_upload/note_eyecatch`）ため、**本文側のエンドポイントだけが仕様変更を受けていた**。

note の非公開 API を叩いている以上こうした変更は起こりうる。spec にも「仕様変更で画像アップロードが落ちることがある。その場合は `--no-images` で本文だけ保存」というフォールバックを書いてあったが、画像を手で11枚貼り直す運用に戻るため、原因を特定して追従することにした。

## 実施内容

エラーメッセージは `{"error":{"message":"不正なリクエストです","type":"invalid_param"}}` だけで、どのパラメータが不正かは返らない。そこで送信内容を変えながら切り分けた。

1. **日本語ファイル名を疑って切り分け** — ASCII 名（`test_ascii.png`）でも 400。ファイル名の文字種は無関係と確認
2. **エンドポイントの存在確認** — `/api/v1|v2/images/upload/presigned_post` は 404、`/api/v3/...` は 400。エンドポイント自体は生きており、パラメータ検証で弾かれていると確定
3. **パラメータ名・形状を総当たり** — `contentType`/`fileName`（キャメル）、`note_id` 追加、`kind`/`purpose`/`type`、`file_size`、ネスト（`{"image":{...}}`）、form-encoded、いずれも 400。**`{"filename": ..., "content_type": ...}` のみ 200**
4. **200 レスポンスの形状を確認** — `url` / `path` / `action` / `post` が返る。`post.key` の値が `img/1786502410-....png` と **`img/` を含む**ため、従来の `f"https://assets.st-note.com/img/{key}"` では `/img/img/...` と重複する。レスポンスの `url` をそのまま使えばよい

判明した2点を `upload_body_image()` に反映した。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/send_note_draft.py` | presigned_post のリクエストキーを `file_name` → `filename` に変更。埋め込み `src` を `data["url"]` に変更（`post.key` からの組み立てをやめる）。仕様変更の経緯を docstring に追記 |
| `projects/w002/2026-07-23_opportunity/output/index.md` | 本文に画像11点を単独行の Markdown 記法で配置（写真はクレジット行を添える） |
| `projects/w002/2026-07-23_opportunity/note-record.md` | 公開後の自動記録用。モードB のため `neta_id` は空欄 |

## 設計判断

**`src` を `post.key` から組み立てず、レスポンスの `url` を使う。** 修正前は `key` を連結して URL を作っていた。今回 `key` が `img/` 込みの値に変わったため二重連結になったが、これは「サーバが返した完成品の URL があるのに、内部表現から自前で組み立て直していた」ことが原因。`url` をそのまま使えば、今後 CDN ドメインやパス構成が変わっても壊れない。

**エラーの切り分けは本番の記事画像ではなく、パラメータだけを変えた presigned 要求で行った。** presigned 要求は URL を発行するだけで S3 への転送を伴わないため、総当たりしてもゴミの画像資産が残らない。

## 確認結果

- 修正後に再実行し、**本文画像11点すべてアップロード成功**（`failed_images` は空・終了コード 0）
- 生成された埋め込み URL に対する HEAD が `200 / 474,532 bytes` を返し、実体が配信されていることを確認（`/img/img/` の重複が無いことも確認）
- アイキャッチ（1280×672）も設定済み
- 下書き: https://note.com/notes/174474109/edit

## 今後の課題

- **失敗した1回目の下書き（`174469281`）が note 上に残っている。** このスクリプトは常に新規下書きを作る仕様のため、リトライすると下書きが増える。既存下書きの更新（`--note-id` で `draft_save` のみ実行）に対応させると、画像だけ失敗したときに作り直さずに済む
- **画像アップロードの失敗が終了コード 2 で返るだけで、記事フローは進行してしまう。** 今回は目視で気づけたが、フロー16 の実行時に `failed_images` が空でなければ止める仕立てにしておくと取りこぼしが無い
