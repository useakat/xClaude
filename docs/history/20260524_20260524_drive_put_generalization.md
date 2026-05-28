---
title: drive_put.sh 汎用化：任意フォルダ対応・MIME 自動判定 — セッション履歴
date: 2026-05-24
sidebar:
  hidden: true
---

# セッション履歴

> 2026-05-24 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260524_drive_put_generalization/)

---

## よーん *(14:43 JST)*

gws を使って、google drive の特定のフォルダにファイルをアップロードしたい。そういうスクリプト作ってたっけ？

### Claude *(14:43 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Read`, `Bash`, `Bash`, `Read`]*

Drive アップロード専用スクリプトは作ってない。

現状あるのは：
- `scripts/sheets_manager.py` — Sheets API（gspread）でスプレッドシート操作。`drive` スコープは含まれてるけど Drive 操作は未実装
- `get-gws-tokens.py` — OAuth トークン取得用（drive スコープは未指定）
- `gcp/charming-well-464402-u4-*.json` — サービスアカウント鍵

ファイルアップロード用には `google-api-python-client` の `drive` サービスで `files().create(..., media_body=...)` を使う形になる。サービスアカウントで上げる場合、対象フォルダをそのサービスアカウントのメールアドレスに編集者で共有しておく必要がある。

作る？であれば仕様だけ確認させて：
1. 対象フォルダの Drive フォルダID
2. アップロードするファイルのパス（CLI 引数で受ける？固定？）
3. 認証はサービスアカウント（`gcp/charming-well-*.json`）で OK？それとも OAuth ユーザー認証（個人 Drive のマイドライブに上げたい）？

---

## よーん *(14:46 JST)*

gws でそういうスクリプト作って

### Claude *(14:46 JST)*

*[ツール: `ToolSearch`, `Bash`, `Bash`, `Bash`, `Write`, `Bash`, `Bash`, `Bash`, `Bash`]*

`scripts/drive_upload.py` を作った。サービスアカウント認証（sheets_manager.py と同じ鍵）。

使い方:
```bash
# フォルダID指定でアップロード
python3 scripts/drive_upload.py path/to/file.pdf -f <フォルダID>

# 環境変数で固定しておく
export GDRIVE_FOLDER_ID=<フォルダID>
python3 scripts/drive_upload.py path/to/file.pdf

# 別名で保存
python3 scripts/drive_upload.py file.pdf -f <ID> -n "アップロード後の名前.pdf"

# テキスト/CSVをGoogleドキュメント/スプレッドシートに変換して保存
python3 scripts/drive_upload.py memo.txt -f <ID> --gdoc
```

注意点（初回のみ）:
1. GCP プロジェクトで Google Drive API を有効化
2. 対象フォルダを `mcp-sheets-service@charming-well-464402-u4.iam.gserviceaccount.com` に「編集者」で共有

スコープは `drive.file`（このアプリで作成・指定したファイルのみアクセス可、最小権限）。共有ドライブも `supportsAllDrives=True` で対応済み。

---

## よーん *(14:48 JST)*

gws 認証でできないの？

### Claude *(14:48 JST)*

*[ツール: `Bash`, `Bash`, `Read`, `Read`, `Bash`, `Write`, `Bash`]*

OAuth ユーザー認証版に書き換えた。サービスアカウントみたいに「フォルダを共有」する必要なし、自分の Drive にそのまま上げられる。

**仕組み**
- 既存の `gcp/client_secret_*.json` を使う
- 初回だけブラウザ認証 → `gcp/drive_token.json` に refresh_token 保存
- 2回目以降は自動で refresh、ずっと再認証不要

**初回認証**
```bash
python3 scripts/drive_upload.py --auth
```
ローカルポートで待ち受け、URL が出るのでブラウザでアクセス → Google アカウントで承認。SSH 越しなら `ssh -L 8080:localhost:8080 ...` でポート転送するか、URL を手元のブラウザで開いて callback URL の `code` パラメータを処理させる。

**使い方（2回目以降）**
```bash
python3 scripts/drive_upload.py path/to/file.pdf -f <フォルダID>

export GDRIVE_FOLDER_ID=<フォルダID>
python3 scripts/drive_upload.py path/to/file.pdf
```

スコープは `drive.file`（このアプリで作ったファイルだけアクセス可、最小権限）。`drive_token.json` は **絶対 commit しないで**（client_secret も入ってる）。`.gitignore` に追加する？

---

## よーん *(14:52 JST)*

追加して

### Claude *(14:52 JST)*

*[ツール: `Bash`]*

`gcp/` フォルダごと既に ignore されてる。`drive_token.json` も `gcp/` に保存するから追加不要。安全。

---

## よーん *(14:54 JST)*

commit push して

### Claude *(14:54 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

push 完了 (`9f54b0f..bcabd54`)。リモートが force-update されてたから rebase してから push した。

⚠️ ただ、CLAUDE.md を改めて見たら気になる記述あり。**「Gmail・Drive の連携は gws CLI を使って実装する（bash スクリプト経由）」** とある。

`scripts/` には既に `drive_put.sh`, `drive_get.sh`, `sync_to_drive.sh` という gws CLI ベースの bash スクリプトがあるはず。よーんが言ってた「gws」は OAuth ユーザー認証じゃなくて **gws CLI ツール** のことだった可能性が高い。

確認したい：
- 既存の `drive_put.sh` で要件足りてる？（→ 今回追加したのは不要だった、revert する？）
- それとも `drive_put.sh` にない機能が欲しかった？（→ 何が足りない？）

---

## よーん *(14:56 JST)*

drive_put.sh はどういう機能があるの？

### Claude *(14:56 JST)*

*[ツール: `Bash`, `Read`]*

`drive_put.sh` の機能まとめ：

| 項目 | 仕様 |
|---|---|
| 用途 | ローカルファイルを **drafts-note フォルダ固定** にアップロード |
| フォルダ | `1j58LBOYgjiOf1RAGdwFcrQSmVKiT00BP`（ハードコード） |
| 同名処理 | 既存があれば **update**（リビジョン履歴に残る）、なければ新規作成 |
| 認証 | gws CLI（`~/.config/gws/`） |
| 出力 | `file_id<TAB>https://drive.google.com/file/d/<id>/view` |
| コンテンツタイプ | 更新時は `text/markdown` 固定 |

つまり drafts-note 専用。よーんの今回のニーズと違うのは：
- **フォルダがハードコード**（任意フォルダに上げられない）
- 更新時の MIME が markdown 固定

任意フォルダに上げたいなら、`drive_put.sh` をベースに「フォルダ引数化＋MIME 自動判定」した bash 版を作るのが、CLAUDE.md のルール（gws CLI 経由）に沿ったやり方。

どうする？選択肢：
1. `drive_put.sh` を一般化（フォルダID 引数追加、MIME 自動判定）→ 既存スクリプト破壊リスクあり
2. 新しく `drive_upload.sh` を作って gws CLI ベースに置き換え、今追加した `drive_upload.py` は削除
3. このまま `drive_upload.py`（OAuth Python版）も併存させる

---

## よーん *(14:58 JST)*

1

### Claude *(14:59 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Agent`, `Read`, `Write`, `ToolSearch`, `ExitPlanMode`, `Read`, `Write`, `Bash`, `Read`, `Edit`, `Edit`, `Bash`, `Bash`]*

push 完了 (`bcabd54..8d8dcf6`)。

変更まとめ:
- `scripts/drive_put.sh` — 第2引数 `[folder-id]` 追加（省略時 drafts-note）、更新時 MIME を `file --mime-type -b` で自動判定
- `scripts/drive_upload.py` — 削除（gws CLI 統一の方針に反するため）
- `CLAUDE.md` / `docs/scripts/index.md` — 説明を「md → ファイル（フォルダ指定可）」に更新

使い方:
```bash
# 従来通り drafts-note へ（既存スキル呼び出しは無影響）
bash scripts/drive_put.sh outputs/foo.md

# 任意フォルダ + PDF
bash scripts/drive_put.sh /path/to/report.pdf <FOLDER_ID>
```

---

## よーん *(15:08 JST)*

useakat@penguin:~/xClaude$ bash scripts/drive_put.sh ~/.notebooklm/storage_state.json 1dXm-s-L_FQk_TRyRwNZd7qJxHXEwPXuG
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/usr/lib/python3.11/json/__init__.py", line 293, in load
    return loads(fp.read(),
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/json/decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

### Claude *(15:08 JST)*

`gws drive files list` がエラーになって空を返したとき、python が空の stdin を JSON パースしようとして落ちてる。stdin が空なら空文字扱いにする修正を入れる。

*[ツール: `Read`, `Edit`, `Bash`, `Bash`]*

修正して push した。再度試してみて。

---

## よーん *(15:10 JST)*

エラーは出なくなったけど、ファイルはアップロードされていない

### Claude *(15:10 JST)*

`2>/dev/null` でエラーを隠してるのが原因の可能性が高い。まず実際のエラーを確認したい。

*[ツール: `Bash`, `Bash`, `Bash`]*

`gws` コマンド自体がこの環境にインストールされていない。`2>/dev/null` で全エラーが潰されてたから静かに失敗してた。

よーんの環境（ローカル PC や別の端末）では gws が使えてる？それとも、これは別環境（Chromebook/penguin）でもともと gws が入ってない環境？

`gws` がなければ、このスクリプトはこの環境では動かせない。選択肢：
1. **gws をインストール** — どこからインストールしてるか教えてもらえれば対応できる
2. **この環境用に代替手段** — `drive_upload.py`（OAuth Python版）に戻す
3. **gws が入ってる端末でだけ使う** — そちらで実行してもらう

---

## よーん *(15:12 JST)*

gws が入っているか確認する方法を教えて

### Claude *(15:12 JST)*

```bash
which gws
```

これで `/usr/local/bin/gws` などのパスが出れば入ってる。何も出なければ未インストール。

追加で詳しく確認したいなら：

```bash
gws version
```

---

## よーん *(15:12 JST)*

未インストールなので、インストールして

### Claude *(15:12 JST)*

*[ツール: `Bash`, `Agent`, `Bash`]*

npm がある。インストールする。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

glibc が 2.36、gws が 2.39 要求でバイナリが動かない。cargo でソースからビルドするのが確実。

*[ツール: `Bash`, `Bash`, `Bash`]*

動いた。認証の設定をする。

*[ツール: `Bash`]*

`gws 0.11.1` で動作確認できた。次に：

**1. PATH を更新**（drive_put.sh に npm グローバルのパスを追加）

*[ツール: `Edit`]*

**2. 認証が必要** — 以下を端末で実行して：

```bash
PATH="/home/useakat/.npm-global/bin:$PATH" gws auth login -s drive
```

ブラウザが開かない場合は URL が表示されるので、そのURLをブラウザで開いて Google アカウントで承認すれば OK。

認証が終わったら再度 `drive_put.sh` を試してみて。

---

## よーん *(15:15 JST)*

useakat@penguin:~/xClaude$ PATH="/home/useakat/.npm-global/bin:$PATH" gws auth login -s drive
{
  "error": {
    "code": 401,
    "message": "No OAuth client configured.\n\nEither:\n  1. Run `gws auth setup` to configure a GCP project and OAuth client\n  2. Download client_secret.json from Google Cloud Console and save it to:\n     /home/useakat/.config/gws/client_secret.json\n  3. Set env vars: GOOGLE_WORKSPACE_CLI_CLIENT_ID and GOOGLE_WORKSPACE_CLI_CLIENT_SECRET",
    "reason": "authError"
  }
}

### Claude *(15:15 JST)*

`gcp/` に client_secret がある。それを gws の設定ディレクトリにコピーすればいい。

*[ツール: `Bash`]*

準備できた。以下を端末で実行して：

```bash
PATH="/home/useakat/.npm-global/bin:$PATH" gws auth login -s drive
```

URL が表示されるのでブラウザで開いて、Google アカウントで承認してください。
