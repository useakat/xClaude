---
title: note 本文画像アップロードを API 仕様変更に追従（filename・埋め込みURL） — セッション履歴
date: 2026-08-12
sidebar:
  hidden: true
---

# セッション履歴

> 2026-08-12 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260812_note_body_image_upload_api_fix/)

---

## よーん *(11:32 JST)*

次のステップは？

### Claude *(11:32 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

残っているのは spec.md のフロー **16（note への下書き保存）** です。ここが飛んでいます。

**現状の確認結果**

- `output/index.md` に**画像の埋め込み記法 `![...](images/...)` が1つも入っていない** — 画像12点は `output/images/` に揃っているものの、本文に配置されていません。この状態で下書き保存すると文字だけの記事になります
- `note-record.md` が未作成 — 公開後の自動記録（フロー19）が neta_id を引けません
- フロー18（完了メール）は前セッションで送信済み

**次にやること**

1. **`output/index.md` に画像12点を埋め込む** — `draft/image-plan_final.md` の配置指示どおり、各 H2 セクションの該当位置に単独行で挿入（②は写真2枚、④は写真2枚を章前半・後半に分ける、⑤はイメージ＋写真2枚を砂嵐の描写と「最後のデータ」直後に置く、など）。写真にはクレジットのキャプションも添える
2. **note に下書き保存** — `python3 scripts/send_note_draft.py "90日の命と言われた探査車、オポチュニティ。火星の砂と生きた15年の物語" --base-dir "$ART/output" --eyecatch "images/thumbnail.png"`。返ってきた編集URLを提示します
3. **`note-record.md` を作成**（モードBなので neta_id は空欄）
4. **Drive の `output/index.md` を更新**（画像埋め込み後の版に差し替え）

有料エリアの設定（③から有料）と公開は note.com 上でよーんが手動で行う想定です。

まず 1 の画像埋め込みから進めてよいですか？

---

## よーん *(11:35 JST)*

進めて

### Claude *(11:35 JST)*

*[ツール: `Read`, `Read`, `Bash`, `Bash`, `Bash`, `Bash`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Bash`]*

画像11点を本文に配置しました（12点目の `thumbnail.png` はアイキャッチ）。続いて note に下書き保存します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

原因が特定できました。note の非公開 API の仕様変更です。

**判明したこと**

1. **`file_name` → `filename` にパラメータ名が変わった**（旧名だと `invalid_param` で 400）。11枚すべてがこれで弾かれていました
2. あわせて、レスポンスに `url` が入るようになっており、現行スクリプトの `src` 組み立て（`.../img/` ＋ `key`）は **`img/` が重複**して壊れたURLになります（`key` の値自体が `img/xxx.png` のため）

アイキャッチだけ成功したのは、別エンドポイント（`/api/v1/image_upload/note_eyecatch`）を使っていて仕様変更の影響を受けなかったためです。

**下書きは作成済み**（本文とサムネのみ・本文画像なし）：https://note.com/notes/174469281/edit

**修正したい内容**（`scripts/send_note_draft.py`・`upload_body_image` 内の2箇所）

```python
# ① リクエストのキー名
-        json={"content_type": mime, "file_name": path.name},
+        json={"content_type": mime, "filename": path.name},

# ② 埋め込みURLはレスポンスの url をそのまま使う
-    key = fields.get("key", "")
     width, height = _image_size(path)
     return {
-        "src": f"https://assets.st-note.com/img/{key}",
+        "src": data["url"],
```

スクリプトの編集は確認を取る決まりなので、この2箇所を修正してよいですか？

修正後に再実行すると**新しい下書きが作られます**（このスクリプトは既存下書きの更新に対応していないため）。先ほどの画像なしの下書き 174469281 は、note 上で削除するかどうかをよーんに判断していただく形になります。

---

## よーん *(12:13 JST)*

修正

### Claude *(12:13 JST)*

*[ツール: `Read`, `Edit`, `Edit`, `Edit`, `Bash`, `Write`, `Bash`, `Bash`, `Bash`, `Bash`]*

note への下書き保存が完了しました。

**下書き（画像込み・こちらが最終版）**
https://note.com/notes/174474109/edit

- 本文画像 **11点すべてアップロード成功**（`failed_images` は空）
- アイキャッチにサムネイル（1280×672）を設定済み
- アップロード後のURLが実際に配信されていることを HEAD で確認（200 / 474KB）

**スクリプトの修正**（`scripts/send_note_draft.py`・`upload_body_image`）

```python
- json={"content_type": mime, "file_name": path.name},
+ json={"content_type": mime, "filename": path.name},

- key = fields.get("key", "")
- "src": f"https://assets.st-note.com/img/{key}",
+ "src": data["url"],
```

仕様変更の経緯をドックストリングにも追記しました。

**その他の更新**

- `note-record.md` を作成（モードBのため neta_id は空欄）。公開後は毎日3:00の cron が自動でシートに記録します
- Drive の `output/index.md` を画像埋め込み版に更新、`note-record.md` を追加

**よーんの手元での作業**

1. **有料エリアの設定** — H2-3「火星の冬を、斜面にもたれて越える」から有料（980円）
2. **公開設定** — お題タグ `#最近の学び` `#スキしてみて` は公開設定画面から別枠で設定
3. **画像なしの下書き 174469281 の削除** — 最初の失敗時にできたものです（本文とサムネのみ）。note 上で削除するかご判断ください

これで spec.md のフロー19（公開後の自動記録）を除く全工程が完了です。スクリプト修正を含むので、`/record` で記録を残しますか？

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

**変更ログ候補（未記録）**

以下の変更が記録されていません。記録するものを選んでください（複数選択可）：

1. **note 本文画像アップロードが API 仕様変更で全滅していたのを修正** — `presigned_post` のキー名変更（`file_name`→`filename`）と埋め込みURLの二重 `img/` を修正
   - 関連コミット: なし（**未コミット**・本セッションで修正）
   - 変更ファイル: `scripts/send_note_draft.py`
   - 関連する過去の変更: 「note 記事の下書き保存を画像・サムネ込みで自動化（W002 フローに組み込み）」（2026-08-10）の後続バグ修正。前回実装以降に note 側の仕様が変わり、本文画像11点すべてが 400 で失敗していた（アイキャッチは別エンドポイントのため無事）

2. **図・サムネイルの最小文字サイズルールを W002 に新設（画像幅の2.19%＝1280px幅で28px）** — スマホ表示での可読性の下限を比率で規定
   - 関連コミット: `e3c7d4d content(w002): note「90日の命と言われた探査車、オポチュニティ」を制作`（記事制作コミットに同梱）
   - 変更ファイル: `projects/w002/image/brand.md`, `projects/w002/thumbnail_template/brand.md`, `2026-07-23_opportunity/reference/3d/make_structure_fig.py`（`MIN_FONT = round(CW * 0.0219)` のクランプ実装）
   - 関連する過去の変更: なし

（記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。）

なお 1 は未コミットです。記録する場合は、報告書の前に実装をコミットします（`/record` の STEP 4.7・docs だけ先行コミットの防止）。

---

## よーん *(14:57 JST)*

1,2

### Claude *(14:57 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Write`, `Bash`, `Write`, `Bash`]*
