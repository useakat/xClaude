---
title: Drive ツール修正（drive_get.sh 現行 gws 対応・add-source-file のローカルファイル対応）
date: 2026-06-17
tags: [infra, bugfix]
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260617_visual_infographic_template_based_prompts/)

## 背景・動機

図解生成（visual_infographic）でスーパーニャンコ参照画像の Drive ダウンロードが失敗し、生成がブロックされた。調査の結果、原因は2つ:

1. `drive_get.sh` の `gws drive files get -o <絶対パス>` が、現行 gws の「出力先はカレントディレクトリ内に限る」制約に抵触し検証エラー（exit 3）になっていた。
2. 現在 gws はサービスアカウント（`mcp-sheets-service@…`）で動作しており、ユーザー個人 Drive のスーパーニャンコ画像が未共有で 404。共有済み Sheets やアップロード先フォルダは見えるが、個人ファイルの取得はできない。

スーパーニャンコ画像はローカル `references/スーパーニャンコアイコン.png` に保存されているため、Drive を介さずローカルファイルから notebook にソース追加できる経路を用意し、あわせて drive_get.sh の出力先不具合も解消する。

## 実施内容

- `drive_get.sh`: `-o` に渡すパスがカレント外（絶対パス /tmp 等）だと弾かれる問題を、**出力先ディレクトリに cd して basename を渡す**方式に修正。
- `notebooklm_manager.py` の `add-source-file`: **`--file <ローカルパス>` を追加**。ローカル画像を安定タイトル（`<title><ext>`）でコピーして `sources.add_file` する。`--url`（Drive）も従来どおり利用可。これにより Drive 認証（サービスアカウント）に依存せずスーパーニャンコ参照を notebook に追加できる。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/drive_get.sh` | `-o` 出力先のカレント外パス拒否を、cd＋basename 方式で回避 |
| `scripts/notebooklm_manager.py` | `add-source-file` に `--file`（ローカルファイル）対応を追加。`--url` は任意化（どちらか必須） |

## 設計判断

- 根本原因（gws のサービスアカウント運用で個人 Drive ファイルが 404）は再認証/共有が必要だが、画像はローカルに存在するため、ローカルファイル経路を用意するのが最短で確実と判断。Drive 認証復旧は別途。

## 確認結果

- `add-source-file <id> --file references/スーパーニャンコアイコン.png --title super-nyanko-ref` で notebook にソース追加成功。`list-sources` で `super-nyanko-ref.png` を確認。
- このローカル経路を使い、図解5枚（および編集版プロンプトから各3枚）を生成完了。
- `drive_get.sh` は exit 3（検証エラー）が解消され、出力先パス制約をクリア（残る 404 はアカウント共有の問題で別件）。

## 今後の課題

- gws のサービスアカウント運用で個人 Drive の取得・アップロードが必要な場合は、対象ファイル/フォルダをサービスアカウントへ共有するか、gws をユーザーアカウントへ再認証する必要がある。
