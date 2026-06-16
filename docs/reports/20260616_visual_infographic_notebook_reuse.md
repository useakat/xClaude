---
title: visual_infographic に既存 notebook 再利用分岐を追加（＋W003 図解6パターンテンプレート）
date: 2026-06-16
tags: [skill, infra]
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260616_visual_infographic_notebook_reuse/)

## 背景・動機

`visual_infographic` は Step 5 で必ず NotebookLM の notebook を**新規作成**（`make-infographic`）してから図解を生成していた。一方、Deep Research（`research_setup-sources` 等）で作成済みの notebook を図解生成にも使い回したいケースがある。

プロジェクトフォルダ（`projects/w003/<YYYYMMDD_topic>/`）に `notebook-id.md`（先例 `visual_section-imager` と同じハイフン区切り）を置けば、その ID の notebook を使って図解生成できるようにした。再利用時は、図解の土台となる原稿テキストとキャラクター（スーパーニャンコ）参照画像のソースが notebook に揃っているかを確認し、不足分のみ補う。

あわせて、図解レイアウトを素早く組めるよう、W003 用に6パターンのプロンプトテンプレートを新設した。

## 実施内容

- `notebooklm_manager.py` に既存 notebook 操作用の CLI サブコマンドを3つ追加（既存のクライアントメソッドの薄いラッパー）：
  - `list-sources <id>` — ソースタイトルを1行ずつ出力（存在チェック用）
  - `add-text <id> --file <path> [--title]` — テキストファイルをソース追加（`sources.add_text`）
  - `add-source-file <id> --url <drive_url> [--title]` — Drive 画像を**安定タイトル**でファイルソース追加（`drive_get.sh`→`add_file`、既定 `super-nyanko-ref`）
- `visual_infographic/SKILL.md` を改修：
  - Step 1 に `PROJECT_DIR` 解決を追加（`--project-dir` 明示指定、または `--file` パスから `projects/w003/<日付_topic>` を推定。特定不可なら再利用しない）
  - Step 5 をブランチ化：`notebook-id.md` があれば**再利用ブランチ**（ソース不足分のみ追加→全 N 枚を `infographic` で生成、新規作成・削除なし）、無ければ**新規作成ブランチ**（従来動作）
  - 注意事項・完了後の報告に再利用時の挙動を追記
- `projects/w003/infographic_template/` に6パターンのプロンプトテンプレートを新設（`step_flow` / `compare_contrast` / `radial` / `timeline` / `pyramid` / `checklist`）。各ファイルは visual_infographic 本番テンプレート準拠（共通のビジュアル指示＋パターン固有レイアウト＋差し込みプレースホルダ）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_manager.py` | `list-sources` / `add-text` / `add-source-file` の3関数・parser・cmd_map を追加。既存コマンドは不変 |
| `.claude/skills/visual_infographic/SKILL.md` | Step 1 にプロジェクトフォルダ解決、Step 5 に再利用／新規作成ブランチ、注意事項・報告を追記 |
| `projects/w003/infographic_template/*.md` | 6パターンの図解プロンプトテンプレートを新設 |

## 設計判断

- **ソース存在チェックを安定タイトルで行う**：`add_file` はファイル名をソースタイトルにするため、Drive 画像を `super-nyanko-ref<ext>` という名前でダウンロードして追加し、次回 `list-sources` で部分一致検出できるようにした。原稿は `infographic_source.txt` というタイトルで検出。
- **フォルダ特定は `--file` 推定＋`--project-dir` 明示の二段**：daily 経由ではドラフトの `--file` から自動判定でき、手動でも明示指定できる。テキスト直接渡しでは特定不可のため従来の新規作成にフォールバック。

## 確認結果

- `notebooklm_manager.py` の Python 構文チェック、3サブコマンドの登録・argparse 配線（`-h`）を確認。
- ライブラリ（`vendor/notebooklm/_sources.py`）に `sources.list()` / `add_text()` / `add_file()` が存在し、`Source.title` 属性があることを確認。
- 実際の `list-sources`/`add-text`/`add-source-file` 実行とスキル通し動作は、NotebookLM 認証・ネットワークが必要なため未実施（ユーザー承認後の実運用で確認）。

## 今後の課題

- 既存 notebook に原稿以外のソース（Deep Research 文献等）があると図解内容に混ざる可能性（再利用は「その notebook の内容で図解してよい」前提）。
- レガシー notebook（ニャンコを旧 `make-infographic` の一時名タイトルで追加済み）は `super-nyanko-ref` として検出できず再追加で重複する可能性（生成への実害は小）。
