---
title: W003 制作フローに投稿フォルダの Drive アップロードを追加（drive_put_folder.sh 新設）
date: 2026-06-21
tags: [workflow, skill, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260621_w003_post_folder_drive_upload/)

## 背景・動機

W003 ワンポイント解説の制作は Gmail 下書き作成までで終わっており、完成した投稿一式（原稿・図解バリエーション・完成図解・プロンプト）はローカルの `projects/w003/YYYYMMDD_[topic]/` にしか残っていなかった。直前の変更で、重い draft 図解画像（11枚・約50MB）は git に含めない方針にしたため、これらを残す受け皿が必要だった。

よーんの依頼: 「Gmail 下書きまで終わったら、投稿フォルダを Google Drive の `xClaude/projects/w003`（ID: `1DTPEzOmWd-kWQElyBByuVHjSantTl7-g`）にアップロードして保存する」ことを標準フローにする。git に置かない代わりに、Drive にフォルダ構造ごと完全アーカイブを残す。

## 実施内容

- **新規スクリプト `scripts/drive_put_folder.sh`** を追加。ローカルフォルダを Drive に再帰アップロードし、サブフォルダ構造を再現する。
  - `get_or_create_folder(name, parent)`: `gws drive files list` で同名フォルダを検索し、無ければ `gws drive files create` で作成して id を返す（idempotent）。
  - `upload_dir(dir, parent)`: フォルダを get-or-create し、配下を走査。ディレクトリは再帰、ファイルは既存の `scripts/drive_put.sh` に委譲してアップロード（同名は更新）。
- **`projects/w003/spec.md`**: 制作フローに「9. 投稿フォルダを Drive へアップロード」を追加。Verification に「投稿フォルダが Drive にアップロード済み」を追加。
- **`.claude/skills/daily-xonepoint/SKILL.md`**: 画像生成（STEP 7）の後に「STEP 8: 投稿フォルダを Drive へアップロード」を追加。完了判定を「STEP 1〜8」に更新し、報告項目に「✅ Drive アップロード完了」を追加。
- 今回の W003（`20260620_血管総延長`）を実際にアップロードし、27ファイルが Drive 上にローカルと同一構成で保存されたことを確認。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/drive_put_folder.sh` | 新規。Drive へフォルダを再帰アップロード（フォルダ get-or-create ＋ `drive_put.sh` 委譲） |
| `projects/w003/spec.md` | 制作フローに Step 9・Verification に1行追加 |
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 8（Drive アップロード）追加・完了判定/報告を更新 |

## 設計判断

- **`gws drive files create` のメタデータは `--json`（リクエストボディ）で渡す**。当初 `--params`（URL/クエリパラメータ）で `name`/`parents` を渡したところ無視され、無題ファイルがマイドライブ直下に作られた。`files create` の help で `--params`=クエリ、`--json`=ボディ、`--upload`=メディアと判明し、`--json` に修正して解決。
- フォルダ作成スクリプトは未整備だったため新設したが、ファイル単位の処理は既存の `drive_put.sh` を再利用し重複実装を避けた。
- 範囲は「テーマフォルダ丸ごと（draft 画像含む・約57MB）」。git では draft 画像を除外する代わりに Drive に完全アーカイブする住み分け。

## 確認結果

- `gws drive files list` で `1DTPEzOmWd-...`（"w003"）配下に `20260620_血管総延長` が1つだけ作成され、その下に `notebook-id.md`・`draft`（23ファイル）・`output`（3ファイル）の計27ファイルが揃うことを確認（ローカルと一致）。
- 同名フォルダ検索が機能し、再実行で重複フォルダを作らない（idempotent）ことを確認。
- 失敗時に生じた無題ファイル等の残骸はゴミ箱へ移動して掃除済み。

## 今後の課題

- routine/agent で無人実行する場合は `permissions.allow` に `drive_put_folder.sh` と `gws drive files create` を事前登録する必要がある（現状の daily-xonepoint は対話実行のため必須ではない）。
- リモート環境（gws 不在）向けの Drive MCP 版フォルダアップロードは未対応。
