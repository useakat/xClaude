---
title: visual_section-imager
description: "draft/image-plan_final.md（H2ごとに1案へ確定済み）を入力に、まず image/plan.md・image/brand.md を読み、写真以外の各セクションについて design-brief（image/design-brief_template.md がテンプレ・design-brief_example.md が例）を作成してユーザー承認を得る。承認後、その design-brief をもとに図解・イメージのプロンプトを作成して再度承認を得る。図解プロンプトは infographic_template.md を全体ベースに「図解の構成・レイアウト」を infographic_layout_* から選択（合わなければ自由記述）。最終承認後、図解は NotebookLM で各3枚生成、イメージは外部の画像生成AI（nano banana 等）で生成してもらう。写真画像案はスキップ。"
category: 画像・同期
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

draft/image-plan_final.md（H2ごとに1案へ確定済み）を入力に、まず image/plan.md・image/brand.md を読み、写真以外の各セクションについて design-brief（image/design-brief_template.md がテンプレ・design-brief_example.md が例）を作成してユーザー承認を得る。承認後、その design-brief をもとに図解・イメージのプロンプトを作成して再度承認を得る。図解プロンプトは infographic_template.md を全体ベースに「図解の構成・レイアウト」を infographic_layout_* から選択（合わなければ自由記述）。最終承認後、図解は NotebookLM で各3枚生成、イメージは外部の画像生成AI（nano banana 等）で生成してもらう。写真画像案はスキップ。

## 詳細内容

# visual_section-imager

`draft/image-plan_final.md`（各 H2 セクションを 1 案に確定済み）を入力に、まず写真以外の各セクションの **design-brief（デザイン指示書）を作成して承認を得**、その design-brief をもとに画像プロンプトを作成して**再度承認を得てから**画像を用意する。図解画像は NotebookLM で生成し、イメージ画像は外部の画像生成AIでユーザーに生成してもらう。

入力（`draft/image-plan_final.md` のパス。省略時は作業中プロジェクトの `draft/image-plan_final.md`）: $ARGUMENTS

## 目的

- 絞り込み済みの画像案を、design-brief → プロンプト → 実画像 の順に具体化する
- **`image/plan.md`・`image/brand.md` を読み、セクション画像の目的・トーンに沿わせる**
- **まず design-brief を作って承認を得て、それをもとにプロンプトを作って再度承認を得る**（各承認前に次へ進まない）
- 図解画像は NotebookLM に渡して各 3 枚生成する
- イメージ画像は、外部の画像生成AI（nano banana 等）でユーザーに生成してもらうため、プロンプトを提示する
- 「画像案 → design-brief → プロンプト → 実画像」工程を標準化し、note 記事の画像準備を完結させる

## 手順

ルートは `ROOT=$(git rev-parse --show-toplevel)`。

### 準備（フェーズ共通）

1. **認証確認**（初回のみ／図解生成で使う）。以下のどちらかが存在するか確認する：
   - `~/.notebooklm/storage_state.json`
   - `$ROOT/gcp/notebooklm_storage_state.json`

   どちらも無い場合、Drive MCP で取得する：
   1. `mcp__claude_ai_Google_Drive__search_files` で `notebooklm_storage_state.json` を検索
   2. `mcp__claude_ai_Google_Drive__read_file_content` で内容（JSON テキスト）を取得
   3. Write ツールで `$ROOT/gcp/notebooklm_storage_state.json` に書き込む

   Drive にも無ければ中断し、ローカルで `bash scripts/notebooklm_auth_push.sh` の実行を案内する。

2. **入力を特定する。** `$ARGUMENTS` がファイルパスならそれを、空なら作業中プロジェクトの `draft/image-plan_final.md` を使う。`PLAN` をそのパス、`PROJ` を `draft/` の親フォルダ（プロジェクトフォルダ）とする。`image-plan_final.md` が無ければ「先に各セクションの採用案を確定して `draft/image-plan_final.md` を作成してください」と伝えて中断する（`image-plan.md` にはフォールバックしない）。

3. **画像方針を読み込む。** プロジェクトの `image/plan.md`（セクション画像の目的・ターゲット・要件・KPI・失格条件）と `image/brand.md`（トーン・画像種類の方針・配色・禁止）を Read する。
   - `PROJ` のプロジェクトフォルダ（`draft/` の 2 つ上、例 `projects/w002/`）配下の `image/plan.md`・`image/brand.md` を読む。見つからなければ `$ROOT/projects/w002/image/` を読む。
   - 以降の design-brief・プロンプトは、この方針（目的・トーン・配色・禁止）に沿わせる。

4. **NOTEBOOK_ID を取得する。** `cat "$PROJ/notebook-id.md"` の 1 行を `NOTEBOOK_ID` とする。空・不正なら中断してユーザーに知らせる。

5. **`image-plan_final.md` を解析する。** `## ` 行で H2 セクションに分割し、各セクションの確定した 1 案から **画像種類**（図解 / イメージ / 写真）と **画像説明** を抽出する。`# 画像プランニング` などの見出しは無視する。

6. **写真画像はスキップ。** 画像種類が「写真」のセクションは生成せず、「スキップ: <セクション>（写真）」と記録する。

7. **保存先を用意する。** `mkdir -p "$PROJ/draft/images"`。

8. **ファイル名を安全化する。** `<safe>` は H2 セクションタイトルから `「」『』（）()`・空白・`/`・記号を `_` に置換／除去したもの。`<画像種類>` は `図解` / `イメージ`。

### フェーズ1：デザイン指示書（作成 → 承認）

9. **写真以外の各セクションについて design-brief を作る。** テンプレート `design-brief_template.md`、記入例 `design-brief_example.md`（いずれもステップ3で特定した `image/` フォルダ内）を Read し、各セクションの **`image-plan_final.md` の確定案（種類＋説明）＋ `draft.md` の該当セクション本文 ＋ `image/plan.md`・`image/brand.md`** をもとに、テンプレの章立て（媒体分類／目的／KPI／文字階層／構図／配色／禁止事項／レビュー基準）を埋める。
   - 図解＝ラベル文字あり前提で文字階層・構図を書く。イメージ＝「画像内に文字を入れない」前提で書く。
   - 本文・確定案にない事実を足さない（誇張・捏造をしない）。
   - 保存先：`draft/images/<safe>_design-brief.md`（セクション別）。

10. **design-brief の保存先パスを伝え、承認を待つ。** **本文はチャットに表示せず、保存先ファイルのパス一覧だけ**を伝え、ユーザーがファイルを確認して承認するのを待つ。承認前にプロンプト作成・生成へ進まない。修正要望があれば該当ファイルを直し、再度パスを伝える。

### フェーズ2：プロンプト作成（承認済み design-brief をもとに → 承認）

11. **承認された design-brief をもとに、種類別でプロンプトを作る。**
    - **図解画像（NotebookLM 用 instructions）**:
      1. **全体テンプレを読む。** `$ROOT/projects/visual_prompts/infographic_template.md` を必ず Read する（章立て：`# テーマ・全体像` / `# ビジュアル・レイアウトの指示` / `# 図解の構成・レイアウト`〔空〕 / `# 禁止事項` / `# Negative prompt`）。これを全体ベースにする。
      2. **レイアウトを選ぶ。** design-brief の「構図」に最も合う `infographic_layout_*` を `$ROOT/projects/visual_prompts/` から選ぶ：
         - `infographic_layout_compare-contrast.md` … 比較・対比（Before/After・2概念の対比）
         - `infographic_layout_timeline.md` … 歴史的経緯・時代の流れ
         - `infographic_layout_step-flow.md` … プロセス・変化を時系列で（手順・因果の流れ）
         - `infographic_layout_radial.md` … 中心概念＋周囲の関連要素
         - `infographic_layout_pyramid.md` … 重要度・階層構造
         - `infographic_layout_checklist.md` … 要点の箇条書き列挙
         - **どれも内容に合わなければ layout ファイルは使わず**、「# 図解の構成・レイアウト」を design-brief の構図に即して自由記述する。
      3. **合成する。** 選んだ layout の「# 図解の構成・レイアウト」本文を、全体テンプレの同セクション（空欄）に差し込む（先頭の `パターン: …` 行は含めない）。
      4. **埋める。** design-brief を各セクションへ写像して具体化する：文字階層→`# テーマ・全体像`（メインタイトル・サブタイトル）＋テキスト／配色→`# ビジュアル・レイアウトの指示`（背景・カラー）／被写体・装飾→ビジュアル指示／禁止事項→`# 禁止事項`＋`# Negative prompt`。テンプレの固定文（テキスト描写の厳守・白人間禁止など）はそのまま残す。design-brief・本文にない事実を足さない。
      5. **保存する。** `draft/images/<safe>_図解.md` に Write で保存する。使ったレイアウト名（または「自由記述」）を、ステップ12でパスと一緒に一言添える。
    - **イメージ画像（外部の画像生成AI 用プロンプト）**: design-brief の情景・トーン・配色・構図をもとに、情景を描いたイメージ画像のプロンプトを作る。**画像内に説明文・キャプション・ラベル・タイトルなどの文字を一切入れない**指示と、Negative prompt（`text, letters, captions, labels, watermark, logo` 等）を含める。`draft/images/<safe>_イメージ.md` に Write で保存する。

12. **プロンプトの保存先パスを伝え、承認を待つ。** **本文はチャットに表示せず、保存先ファイルのパス一覧だけ**（図解は使用レイアウト名も）を伝え、ユーザーがファイルを確認して承認するのを待つ。承認前に画像生成（NotebookLM 呼び出し）へ進まない。修正要望があれば該当ファイルを直し、再度パスを伝える。

### フェーズ3：生成（承認後）

13. **図解画像を生成する（NotebookLM・各3枚・失敗時リトライ付き）。** 承認された図解プロンプトを使い、連番 01〜03 を 1 枚ずつ生成する。各連番は、`--output` の PNG が生成されなければ**最大 2 回まで再実行**（合計 3 回試行、各リトライ前に `sleep 5`）する。3 回とも生成できなければ「失敗: <ファイル名>」と記録して次の連番へ進む（全体は止めない）。
    ```bash
    gen_one() {  # 引数: 出力PNGパス, instructionsファイルパス
      local out="$1" instr="$2" try
      for try in 1 2 3; do
        python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
          --instructions "$(cat "$instr")" \
          --language ja --orientation landscape --detail standard --style auto \
          --output "$out" && [ -f "$out" ] && return 0
        echo "retry $try failed: $(basename "$out")"; sleep 5
      done
      echo "FAILED: $(basename "$out")"; return 1
    }
    # 各連番で gen_one "<...>_図解_<連番>.png" "<...>_図解.md" を呼ぶ
    ```
    - notebook は新規作成しない（`make-infographic` ではなく `infographic`）。`NOTEBOOK_ID` を再利用する
    - キャラクター参照 URL（`--extra-source-url`）は付けない
    - 生成画像は `draft/images/<safe>_図解_<連番>.png`（連番 01〜03）に保存する

14. **イメージ画像は外部生成を案内する。** スキルは画像を生成しない。承認済みプロンプト（`draft/images/<safe>_イメージ.md`）を提示し、ユーザーに **外部の画像生成AI（nano banana / Gemini 2.5 Flash Image 等）で生成し、`draft/images/<safe>_イメージ_<連番>.png` として保存する**よう案内する。

15. **報告する。** 全セクション完了後、図解の生成結果・イメージの外部生成待ち・スキップを一覧で出力する。

## 出力形式

承認待ちの提示（フェーズ1・2）は、本文を貼らずに保存先パスの一覧だけを示す（図解は使用レイアウト名も）。
生成フェーズ後の最終報告は次の形式：

```
[画像生成結果]

## <H2タイトル1>（図解画像・NotebookLM 生成）
- draft/images/<safe>_図解_01.png
- draft/images/<safe>_図解_02.png
- draft/images/<safe>_図解_03.png

## <H2タイトル2>（イメージ画像・外部AIで生成してください）
- プロンプト: draft/images/<safe>_イメージ.md
  → nano banana 等で生成し draft/images/<safe>_イメージ_01.png … に保存

## スキップ
- <H2タイトルX>（写真）

[/画像生成結果]
```

## 禁止事項

- **design-brief の承認前にプロンプトを作らない。プロンプトの承認前に画像を生成しない**（NotebookLM 呼び出し・次フェーズへの進行を含む）
- **design-brief・プロンプトの本文をチャットに貼り付けない。** ファイルに保存し、保存先パスだけを伝えてユーザーにファイルで確認してもらう
- イメージ画像をスキル側で生成しない（外部の画像生成AIでユーザーに生成してもらう）
- 写真画像（Web取得）案を生成しない。スキップのみ
- 図解プロンプトは `projects/visual_prompts/infographic_template.md` を全体ベースに作り、「図解の構成・レイアウト」は `infographic_layout_*` から選んで差し込む（合わなければ自由記述）。テンプレの固定文（テキスト描写の厳守・白人間禁止）や `# 禁止事項`・`# Negative prompt` を勝手に削らない。`パターン:` 行は保存物に含めない
- スキルが独自に複数の切り口プロンプトを作らない。承認済み design-brief をもとにテンプレを埋め、design-brief・本文にない事実を足さない
- イメージ画像には説明文・キャプション・ラベル・タイトルの文字を入れさせない（図解はラベル文字あり可）
- notebook を新規作成・削除しない。`notebook-id.md` の既存 ID を使う
- キャラクター参照・スーパーニャンコ URL を付けない
- Drive アップロード・Gmail 送信をしない。ローカル保存のみ
- 図解は各セクション 3 枚を守る。過不足を出さない
