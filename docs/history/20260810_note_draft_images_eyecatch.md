---
title: note 記事の下書き保存を画像・サムネ込みで自動化（W002 フローに組み込み） — セッション履歴
date: 2026-08-10
sidebar:
  hidden: true
---

# セッション履歴

> 2026-08-10 のセッション作業ログ。

---
← [報告書へ戻る](../../reports/20260810_note_draft_images_eyecatch/)

---
## よーん *(08:56 JST)*

ステップ 15のネタ使用済み更新の次に、output/index.md の最終原稿を note に下書きとして保存するステップをついかして。あと、僕がnote 記事の公開URLを伝えたら、outputs シートと note投稿一覧シートに note 記事の投稿を記録するように、spec.md を修正して

### Claude *(08:56 JST)*

まず既存の関連実装（note下書き保存スクリプト、outputs/note投稿一覧への記録パターン）を確認します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

`.env` に `NOTE_SESSION` あり・実行可能な状態を確認できました。`spec.md` を修正します。

*[ツール: `Edit`]*

Verification セクションと「その他」への言及も、モードC の項目に揃えて追記します。

*[ツール: `Edit`]*

`spec.md` を修正しました。変更点は次の2つです。

**ステップ16「note に下書き保存」を新設**（旧16「Drive アップロード」→17、旧17「完了メール」→18 に繰り下げ）
- `output/index.md` の最終原稿を `scripts/send_note_draft.py`（既存スクリプト、`.env` の `NOTE_SESSION` で認証済み）で note.com に下書き保存
- 返ってきた `edit_url` をユーザーに提示
- 画像埋め込み・サムネ設定・有料エリア設定・最終公開は note.com 上でユーザーが手動で行う旨を明記（自動公開はしない）

**ステップ19「公開後の記録」を新設**（ユーザーから公開URLの共有を受けたらトリガー）
1. `outputs` シート（SS2）に `[記録日時, 公開URL, "W002", neta_id, "", "", "", ""]` を1行追加（neta_id はモードA/Cで `noteNeta[No]`、モードBは空欄。既存のW002行の実データパターンに合わせた形式）
2. `/record-note-posts` スキルを実行し、note投稿一覧シートにビュー・スキ・サムネ等を記録（同スキルは note API から新規記事を自動検出するため、URLを渡す必要はなく実行するだけでよい）

Verification にもこの2点の確認項目を追加しています。

なお `send_note_draft.py`／`.env` の `NOTE_SESSION` は既存のまま使う（新規作成・編集はしていません）ので、CLAUDE.md の「スクリプトの新規作成・編集は確認してから」には抵触しません。

このまま W002（モードC）の制作、C2〜C4（notebook継承 → 過去記事確認 → 構成案提示）に進めてよいですか？

---

## よーん *(09:04 JST)*

* 画像埋め込みとサムネ設定くらいは自動でできる？
* 公開後の記録なんだけど、record-note-posts が定期的に実行されて、新しい note 記事の投稿を検知したら、自動的に outputs シートにその note 投稿を記録するように変更できる？

### Claude *(09:04 JST)*

2つとも調べます。まず note API の画像・サムネ周りと、record-note-posts の定期実行状況を確認します。

*[ツール: `Bash`, `Read`, `Read`, `Bash`, `WebFetch`, `ToolSearch`, `WebSearch`, `WebSearch`, `WebFetch`, `WebFetch`, `WebFetch`]*

両方とも技術的に可能でした。まず自動記録（2点目）を実装します。

*[ツール: `Edit`, `Edit`, `Edit`]*

now w002/spec.md 側を、`note-record.md` の生成と公開後記録の自動化に合わせて更新します。

*[ツール: `Edit`, `Edit`, `Edit`]*

2点目（自動記録）は実装しました。1点目（画像・サムネの自動化）は調査結果をお伝えします。

## ① 画像埋め込み・サムネ設定の自動化 — **どちらも可能**です

非公開APIで実現できることが確認できました。ただし `send_note_draft.py` の編集が必要なので、着手前に確認させてください。

**サムネ（アイキャッチ）設定** — 比較的簡単です。
`POST /api/v1/image_upload/note_eyecatch` に multipart で `file`／`note_id`（下書きの数値ID）／`width`／`height` を送るだけ。下書き作成時に返る `note_id` をそのまま渡せるので、既存コードの流れに素直に乗ります。注意点は MIME タイプの明示が必須（省くと500エラー）という一点です。

**本文画像の埋め込み** — 3段階になり、やや手間です。
`POST /api/v3/images/upload/presigned_post` で S3 の presigned フォームを取得 → S3 へ multipart POST（`x-amz-security-token` を含む全フィールドが必須。欠けると403）→ 返ったキーで本文HTMLに `<figure name=UUID id=UUID><img src="https://assets.st-note.com/img/<KEY>" ...></figure>` を挿入。現在の `md_to_note_html()` に Markdown 画像記法 `![alt](path)` を拾ってアップロード＆figure化する処理を足す形になります。

**有料エリア設定**は下書き保存APIには無く、公開API（`PUT /api/v1/text_notes/{id}`）側の `free_body`／`pay_body`／`separator`／`price` で扱う構造でした。公開そのものを自動化することになるので、ここは手動のままが安全だと考えます。

実装するなら、サムネ設定と本文画像埋め込みの両方を `send_note_draft.py` に追加します。**スクリプト編集の許可をいただければ着手します**（非公開APIなので、仕様変更で壊れる前提の作りにします）。

## ② 公開後の outputs 自動記録 — 実装しました

`/record-note-posts` は毎日3:00にcronで動いているので、そこに STEP 6 を追加しました。

- note投稿一覧の更新後、outputs の B列（URL）と突き合わせて未記録の記事を抽出
- `[公開日時, URL, "W002", neta_id, "", "", "", ""]` を追記
- `neta_id` は W002 の記事フォルダに新設する `note-record.md`（title / what_id / neta_id を記録）をタイトル完全一致で grep して解決。**特定できなければ空欄にして完了報告に「neta_id 未解決」と出す**（推測で埋めない）
- F列 `note_url` は空欄固定にしました。ここは「X投稿がどのnoteへ誘導したか」の列で、note本体行に入れると `sync-x-note-analytics` の導線集計が二重計上するためです

w002 spec 側も、ステップ16で `note-record.md` を作る手順を追加し、ステップ19を「自動。公開当日に反映したい時だけ手動実行」に書き換えました。

画像・サムネ自動化に進めますか？

---

## よーん *(09:18 JST)*

進めて

### Claude *(09:18 JST)*

*[ツール: `Read`, `Write`, `Bash`, `Bash`]*

画像行の扱いに不備がありました（外部URL画像が壊れたリンクになる）。修正します。

*[ツール: `Edit`, `Edit`, `Bash`]*

spec.md のステップ16を、新しい引数に合わせて更新します。

*[ツール: `Edit`, `Bash`, `Edit`]*

画像・サムネの自動化を実装しました。

## `scripts/send_note_draft.py` の変更

**サムネ（アイキャッチ）の自動設定** — `--eyecatch <path>` で `POST /api/v1/image_upload/note_eyecatch` に multipart 送信します。下書き作成時に返る数値 note_id を同梱するので、これだけで下書きに紐づきます。MIME タイプは拡張子から判定して明示（省くと500エラーになる仕様のため）。画像サイズは Pillow で実寸を読んで送ります（インストール済みを確認、12.2.0）。

**本文画像の自動アップロード** — 本文中の `![alt](images/xxx.png)` を単独行で書いておくと、`POST /api/v3/images/upload/presigned_post` → S3 への multipart POST（`x-amz-security-token` を含む全フィールドをそのまま転送）→ `<figure><img src="https://assets.st-note.com/img/<KEY>" width height></figure>` として本文に埋め込みます。同じパスの重複アップロードはキャッシュで回避します。

**引数を argparse 化**：`--base-dir`（画像相対パスの基準）、`--eyecatch`、`--no-images`（API が壊れた時の退避用）。既存の `send_note_draft.py "タイトル" < article.md` の呼び方はそのまま動きます。

**変換の不備も1つ直しました**：従来 `![alt](url)` は `!<a href=...>alt</a>` という壊れたリンクになっていました。今は http(s) URL の画像はアップロードせず figure に直接埋め込み、解決できなかった画像は元の Markdown 記法をそのまま残す（壊れたリンクを作らない）ようにしています。失敗した画像は `failed_images` に集めて終了コード2で返します。

ローカルでの変換テストは通っています。ただし**note API への実通信はまだ未検証**です（外部への送信になるため、実際の記事制作時に初回実行することになります）。テスト用の下書きを1本作って疎通確認しておくこともできますが、note.com 上にゴミ下書きが1件残ります。

## spec.md の更新

ステップ16を「note に下書き保存（画像・サムネ込み）」に書き換え、`--base-dir`／`--eyecatch` 付きのコマンド例、画像記法の条件（単独行）、API が落ちた時の `--no-images` 退避を明記しました。手動が残るのは**有料エリアの設定と最終公開だけ**になります。

W002（モードC）の制作に進めますか？

---

