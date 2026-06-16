---
title: visual_infographic に既存 notebook 再利用分岐を追加（＋W003 図解6パターンテンプレート） — セッション履歴
date: 2026-06-16
sidebar:
  hidden: true
---

# セッション履歴

> 2026-06-16 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260616_visual_infographic_notebook_reuse/)

---

## よーん *(21:02 JST)*

visual_infographic skill で作る5パターンについておしえて

### Claude *(21:02 JST)*

*[ツール: `Read`]*

`visual_infographic` の「5パターン」は、**固定された5種類ではなく、渡したテキストの内容に最適なレイアウトを5つ選んで作り分ける**仕組みです（`/visual_infographic 5` で枚数指定）。

## パターンの選び方
内容・構造を見て、以下のような型から相性のよいものを5つ選びます（Step 3）。型は固定せず内容次第:

- **ステップ・フロー型** — プロセス／変化を時系列で
- **比較・対比型** — Before/After、2概念の対比
- **中心放射型** — 核を中央に、関連要素を周囲に（視線が左上→左下→右上→右下に流れるよう配置）
- **タイムライン型** — 歴史的経緯・時代の流れ
- **ピラミッド型** — 重要度の階層
- **チェックリスト型** — 要点の箇条書き

## 5枚すべてに共通する仕様
- **スタイル**: sketch-note（黒ペン画＋淡い水彩アクセント、白背景）、横向き、日本語
- **タイトル/サブタイトル**: テキストが「実は、」で始まれば冒頭1文をメインタイトルに採用
- **キャラ**: スーパーニャンコ（赤いハート・卒業帽・赤マントの青ネコ）を手書き風で必ず登場
- **文字**: 指定テキストを一言一句変えず描画
- **出力**: 1枚ごとに PNG＋プロンプト md を Drive（outputs/images）へ即アップロード → 完了後 Gmail 通知

---

## よーん *(21:07 JST)*

そこに挙げた６パターンについて、図解を生成するプロンプトのテンプレートを作成して、infographic_template フォルダに保存して

### Claude *(21:07 JST)*

*[ツール: `Bash`, `AskUserQuestion`, `Write`×6]*

w003 プロジェクト内（`projects/w003/infographic_template/`）に6パターンのテンプレートを作成しました（step_flow / compare_contrast / radial / timeline / pyramid / checklist）。各ファイルは visual_infographic スキルの本番テンプレートに準拠（共通のビジュアル指示＋パターン固有レイアウト＋差し込みプレースホルダ）。

---

## よーん *(21:10 JST)*

テンプレートファイ名先頭の番号は削除

### Claude *(21:10 JST)*

*[ツール: `Bash`]*

ファイル名先頭の番号を削除しました（`step_flow.md` / `compare_contrast.md` / `radial.md` / `timeline.md` / `pyramid.md` / `checklist.md`）。

---

## よーん *(21:51 JST)*

step 3 で作成したプロンプトはどうやって notebookLM に渡してるの？

### Claude *(21:51 JST)*

*[ツール: `Bash`, `Read`]*

渡し方は「**CLI 引数 `--instructions` → NotebookLM クライアントの `generate_infographic(instructions=...)`**」という流れです。原稿テキスト＋スーパーニャンコ参照画像は notebook の**ソース**として渡され、`instructions` は「どう描くか（レイアウト・配色・キャラ配置）」を指示する役割。

---

## よーん *(21:57 JST)*

step5 画像生成で、notebook を新規作成することになっているけど、もし、w003 以下のプロジェクトフォルダ (YYYY-MM-dd_[topics] 形式の名前のフォルダ）に、notebook_id.md がある場合は、それに書かれている ID の notebook で infographic を生成することはできる？

### Claude *(21:57 JST)*

*[ツール: `Bash`]*

はい、可能です。`notebooklm_manager.py` には `make-infographic`（新規作成）と `infographic <ID>`（既存notebookで生成）の2系統があり、`notebook-id.md` の ID を読めば全 N 枚を既存 notebook で生成できます。注意点として、既存 notebook に原稿テキストとスーパーニャンコ参照画像のソースが無いと内容が合わない／キャラが出ない可能性があるため、生成前に add-source が必要。先例 `visual_section-imager` は `notebook-id.md`（ハイフン）を使う設計。

---

## よーん *(22:04 JST)*

実装する。

* ファイル名はハイフン
* 1枚目のインフォグラフィックを作成する前に、原稿テキスト (infographic_source.txt) がないかどうか調べて、ない場合は add-source するようにする
これで実装計画を立てて。実装はまだしないで

### Claude *(22:04 JST)*

*[ツール: `Read`×3, `Bash`×4, `AskUserQuestion`×3, `Write`(plan), `ExitPlanMode`]*

計画モードで設計。ライブラリ（`vendor/notebooklm/_sources.py`）に `sources.list()`/`add_text()`/`add_file()` があり、`Source.title` も存在することを確認。CLI には未公開なのでサブコマンド追加が必要と判明。確認の結果、方針を確定：

- ファイル名 `notebook-id.md`（ハイフン）
- 再利用ブランチでは原稿テキスト＋スーパーニャンコ参照の両方を補う
- プロジェクトフォルダは `--file` パスから推定＋`--project-dir` 明示も可

計画を提示し承認を得た。

---

## よーん *(22:08 JST)*

（計画承認）

### Claude *(22:08 JST)*

*[ツール: `Bash`×2, `Edit`×5, `Bash`×2]*

実装完了。

**1. `scripts/notebooklm_manager.py`**（CLI サブコマンド3つ追加）
- `list-sources <id>` — ソースタイトルを1行ずつ出力（存在チェック用）
- `add-text <id> --file <path> [--title]` — テキストファイルをソース追加（`sources.add_text`）
- `add-source-file <id> --url <drive_url> [--title]` — Drive 画像を安定タイトルでファイルソース追加（`drive_get.sh`→`add_file`、既定 `super-nyanko-ref`）
- 既存コマンドの挙動は変更なし。構文・argparse 配線・登録を確認。

**2. `.claude/skills/visual_infographic/SKILL.md`**
- Step 1: `PROJECT_DIR` 解決を追加（`--project-dir` 明示／`--file` パスから推定／無ければ再利用しない）
- Step 5: ブランチ分岐（再利用ブランチ＝ソース不足分のみ追加→全 N 枚 `infographic`、新規作成なし／新規作成ブランチ＝従来）
- 注意事項・完了後の報告に再利用時の挙動を追記

検証：Python 構文チェック、3サブコマンドの登録・引数配線を確認。実際の生成・通し動作は NotebookLM 認証が必要なため実運用時に確認。
