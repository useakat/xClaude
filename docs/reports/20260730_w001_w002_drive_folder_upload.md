---
title: w001/w002 に Drive フォルダ一式アップロード工程を追加し画像を Drive-only 化（w003 方式に統一）
date: 2026-07-30
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md#2026-07-30) ｜ [セッション履歴→](../../history/20260730_w001_w002_drive_folder_upload/)

## 背景・動機

カッシーニ販促投稿の完了後、「Drive にもフォルダ一式をアップロードしたか」の確認があった。調査の結果：

- w001（X長文）・w002（note記事）の spec には Drive アップロード工程が**存在しなかった**（w002 は運用意図はあったが spec 未記載）
- 一方 **w003 spec にはフロー11 として確立済みのパターンがあった**：`scripts/drive_put_folder.sh <dir> <folder-id>` でフォルダ丸ごと構造再現アップロード（再帰・冪等）＋「画像は git にコミットせず Drive のみ」（`.gitignore` で除外・リポジトリ肥大防止）

当初 w001/w002 に「gws でサブフォルダ作成＋ファイルごとに drive_put.sh」という手順を書いたが、ユーザーの指摘で w003 spec を確認し、既存の `drive_put_folder.sh` を使う簡潔な方式に修正した（車輪の再発明の回避）。画像の git 除外も w003 方式に合わせて統一した。

## 実施内容

- **w001 spec.md**: フロー15「投稿フォルダを Drive へアップロード」新設（`bash scripts/drive_put_folder.sh projects/w001/YYYYMMDD_[topic] 1ZXvs-h0GngSsCOwX6fbB0rBsqO-jUaOW`）。「画像は git にコミットしない」ルールと Verification 2項目を追加。
- **w002 spec.md**: フロー16 同様に新設（親フォルダ `1AonY-bLf61duFKZ6dBsPq7mSQASD_HGn`。Drive 上の w001 と同階層の既存フォルダを gws で辿って特定）。完了メール送信は 17 に繰り下げ。同ルール＋Verification 追加。
- **`.gitignore`**: `/projects/w001/**/*.png`・`/projects/w002/**/*.png` を追加（w003 の既存行と同書式）。
- **追跡中の png 39件を `git rm --cached`**（ローカルファイルは残存。過去コミット履歴の画像はそのまま＝履歴書き換えなし）。
- **過去フォルダ8件を Drive へ遡及アップロード**: w001×4（ボイジャー再点火・はやぶさ2トリフネ・ボイジャーアルミホイル・カッシーニ噴水販促）＋ w002×4（SCEtoAUX・ボイジャー再点火・kepler-k2-revival・opportunity）。`drive_put_folder.sh` の冪等動作（同名フォルダ再利用・同名ファイル更新）も実地確認。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w001/spec.md` | フロー15（Drive アップロード）新設・画像非コミットルール・Verification 追加 |
| `projects/w002/spec.md` | フロー16 新設（メールは17へ）・画像非コミットルール・Verification 追加 |
| `.gitignore` | w001/w002 の `**/*.png` 除外を追加 |
| （39 png ファイル） | git 追跡解除（`git rm --cached`） |

## 設計判断

- **w003 の確立済みパターンへの統一**：3プロジェクトで Drive アップロードと画像管理の方式が揃い、`drive_put_folder.sh` 1コマンドで完結する。独自手順の温存より保守性を優先。
- **履歴の書き換えはしない**：過去コミットの画像は履歴に残るが、`git filter-repo` 等は共有リポジトリへの影響が大きいため実施しない。今後の肥大だけを止める。

## 確認結果

- カッシーニフォルダで `drive_put_folder.sh` を再実行し「フォルダ再利用・同名ファイル更新」の冪等動作を確認
- 遡及アップロード8件すべて「=== 完了 ===」で正常終了
- `git rm --cached` 後もローカル画像の残存を確認
- Drive 親フォルダ構成: `xClaude/projects/` 配下に w001（`1ZXvs…`）・w002（`1AonY…`）・w003（`1DTPE…`）が同階層で整合

## 今後の課題

- 次回の w001/w002 制作で、新フロー（Drive アップロード工程）が spec どおり実行されることを確認する。
