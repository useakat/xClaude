---
title: W003 投稿フォルダ画像を Drive 保存・git 除外に移行
date: 2026-06-25
tags: [workflow, skill, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260625_w003_post_images_drive_and_git_pull_rule/)

## 背景・動機

W003 の投稿フォルダ（`projects/w003/YYYYMMDD_[topic]/`）には、draft の図解バリエーション5枚と output の完成画像が含まれ、1投稿あたり 20〜30MB の PNG が発生する。これらを git にコミットするとリポジトリが肥大していく。

すでに投稿フォルダは丸ごと Drive（`xClaude/projects/w003`）へアップロードする運用（`drive_put_folder.sh`、2026-06-21 導入）があるため、画像は Drive を正とし、git にはテキスト（`*.md`）のみを残す方針に統一した。

なお `.gitignore` には従来 `/projects/w003/*/draft/*.png`（draft のみ除外）があったが、ベテルギウス投稿の作業中に stash 復元（`git checkout stash^3 -- <path>`）経由で draft 画像が index に入りコミットされてしまった。これを機に、output 画像も含めた全画像を除外対象に拡張した。

## 実施内容

- `.gitignore` の除外ルールを `/projects/w003/*/draft/*.png` → **`/projects/w003/**/*.png`**（draft・output 含む全画像）に拡張。
- 誤ってコミット済みだった betelgeuse 投稿の画像6枚（draft 5＋output 1）を `git rm --cached` で管理外に（ローカル・Drive には残存）。
- `projects/w003/spec.md` の「その他」に、投稿フォルダ内画像は git にコミットせず Drive＋ローカルに保存する旨を明記。
- `daily-xonepoint` SKILL の STEP 6（画像生成）に、画像は git 管理外・誤って index に入ったら `git rm --cached` で外す旨の注記を追加。
- betelgeuse 投稿フォルダを Drive へアップロード（gws OAuth トークン失効のため Drive スコープ込みで再認証してから実行）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.gitignore` | W003 投稿フォルダ画像の除外を `**/*.png` に拡張（draft・output 全画像） |
| `projects/w003/spec.md` | 「その他」に画像は Drive 保存・git 除外の運用を明記 |
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 6 に画像 git 除外の注記を追加 |

## 設計判断

- 画像は Drive を正とし git にはテキストのみ残す方針にした。投稿フォルダは `drive_put_folder.sh` で丸ごと Drive に保存されるため、画像の保管先は Drive で担保される。git 履歴に過去画像は残るが、今後の肥大は防げる。
- 既存の他投稿フォルダ（20260615 等）の追跡済み画像は、Drive 保存の有無が未確認のため今回は untrack していない。

## 確認結果

- `git ls-files projects/w003/20260624_betelgeuse_siwarha` で画像が追跡対象外になったことを確認（`*.md` のみ残存）。
- `drive_put_folder.sh` 実行で draft・output 全ファイルが Drive にアップロード完了（`=== 完了 ===`）。
