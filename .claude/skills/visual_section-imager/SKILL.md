---
name: visual_section-imager
description: draft/image-plan.md（H2ごとに1案へ絞り込み済み）を入力に、図解・イメージ各セクションのプロンプトをまず作成して draft/images に保存し、ユーザー承認を得る。承認後、図解画像は notebook-id.md の NotebookLM notebook に渡して各3枚生成し draft/images に保存。イメージ画像は外部の画像生成AI（nano banana 等）で生成してもらうため、プロンプトを提示する（スキルは生成しない）。写真画像案はスキップ。
---

# visual_section-imager

`draft/image-plan.md`（各 H2 セクションを 1 案に絞り込み済み）を入力に、各セクションの画像プロンプトを作成し、**ユーザー承認を得てから**画像を用意する。図解画像は NotebookLM で生成し、イメージ画像は外部の画像生成AIでユーザーに生成してもらう。

入力（`draft/image-plan.md` のパス。省略時は作業中プロジェクトの `draft/image-plan.md`）: $ARGUMENTS

## 目的

- 絞り込み済みの画像案を、実画像にするためのプロンプトに変換する
- **作業フォルダ・親フォルダの `plan.md`・`brand.md` を読み、発信の目的・トーンに沿わせる**
- **プロンプトをまず作成・保存し、ユーザー承認を得る**（承認前に生成しない）
- 図解画像は NotebookLM に渡して各 3 枚生成する
- イメージ画像は、外部の画像生成AI（nano banana 等）でユーザーに生成してもらうため、プロンプトを提示する
- 「画像案 → プロンプト → 実画像」工程を標準化し、note 記事の画像準備を完結させる

## 手順

ルートは `ROOT=$(git rev-parse --show-toplevel)`。

### フェーズ1：プロンプト作成（承認まで）

1. **認証確認**（初回のみ／図解生成で使う）。以下のどちらかが存在するか確認する：
   - `~/.notebooklm/storage_state.json`
   - `$ROOT/gcp/notebooklm_storage_state.json`

   どちらも無い場合、Drive MCP で取得する：
   1. `mcp__claude_ai_Google_Drive__search_files` で `notebooklm_storage_state.json` を検索
   2. `mcp__claude_ai_Google_Drive__read_file_content` で内容（JSON テキスト）を取得
   3. Write ツールで `$ROOT/gcp/notebooklm_storage_state.json` に書き込む

   Drive にも無ければ中断し、ローカルで `bash scripts/notebooklm_auth_push.sh` の実行を案内する。

2. **入力を特定する。** `$ARGUMENTS` がファイルパスならそれを、空なら作業中プロジェクトの `draft/image-plan.md` を使う。`PLAN` をそのパス、`PROJ` を `draft/` の親フォルダ（プロジェクトフォルダ）とする。

3. **plan.md・brand.md を読み込む。** 作業フォルダ（`PROJ`）と、その親フォルダをさかのぼって見つかる `plan.md`・`brand.md` を Read で読み込み、発信の目的・ターゲット・トーン・NG表現を把握してからプロンプトを作成する（存在するものだけ読めばよい）。これらの方針に沿った画像プロンプトにする。

4. **NOTEBOOK_ID を取得する。** `cat "$PROJ/notebook-id.md"` の 1 行を `NOTEBOOK_ID` とする。空・不正なら中断してユーザーに知らせる。

5. **`image-plan.md` を解析する。** `## ` 行で H2 セクションに分割し、各セクションの絞り込まれた 1 案から **画像種類**（図解 / イメージ / 写真）と **画像説明** を抽出する。`# 画像プランニング` 見出しは無視する。

6. **写真画像はスキップ。** 画像種類が「写真」のセクションは生成せず、「スキップ: <セクション>（写真）」と記録する。

7. **保存先を用意する。** `mkdir -p "$PROJ/draft/images"`。

8. **図解／イメージのセクションごとにプロンプトを作成し、保存する。** 画像説明の本文に、画像種類に応じた明示指示を加える：
   - **図解画像（NotebookLM 用 instructions）**: 末尾に「これは図解（インフォグラフィック）として作成してください。」を付ける。`draft/images/<safe>_図解.md` に Write で保存する。
   - **イメージ画像（外部の画像生成AI 用プロンプト）**: 情景を描いたイメージ画像として、画像内に説明文・キャプション・ラベル・タイトルなどの文字を一切入れない指示を含める。被写体・構図・配色・トーンと、文字を入れない明示、Negative prompt（`text, letters, captions, labels, watermark, logo` 等）を添える。`draft/images/<safe>_イメージ.md` に Write で保存する。

9. **ファイル名を安全化する。** `<safe>` は H2 セクションタイトルから `「」『』（）()`・空白・`/`・記号を `_` に置換／除去したもの。`<画像種類>` は `図解` / `イメージ`。

10. **プロンプトを提示し、承認を待つ。** 作成した図解・イメージのプロンプト（保存先パスつき）を一覧でユーザーに提示し、**承認を待つ**。承認前に画像生成（NotebookLM 呼び出し）や次フェーズへ進まない。ユーザーが修正を求めたら該当プロンプトを直して保存し直し、再提示する。

### フェーズ2：生成（承認後）

11. **図解画像を生成する（NotebookLM・各3枚・失敗時リトライ付き）。** 承認された図解プロンプトを使い、連番 01〜03 を 1 枚ずつ生成する。各連番は、`--output` の PNG が生成されなければ**最大 2 回まで再実行**（合計 3 回試行、各リトライ前に `sleep 5`）する。3 回とも生成できなければ「失敗: <ファイル名>」と記録して次の連番へ進む（全体は止めない）。
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

12. **イメージ画像は外部生成を案内する。** スキルは画像を生成しない。承認済みプロンプト（`draft/images/<safe>_イメージ.md`）を提示し、ユーザーに **外部の画像生成AI（nano banana / Gemini 2.5 Flash Image 等）で生成し、`draft/images/<safe>_イメージ_<連番>.png` として保存する**よう案内する。

13. **報告する。** 全セクション完了後、図解の生成結果・イメージの外部生成待ち・スキップを一覧で出力する。

## 出力形式

承認後の最終報告は次の形式：

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

- **プロンプトの承認前に画像を生成しない**（NotebookLM 呼び出し・次フェーズへの進行を含む）
- イメージ画像をスキル側で生成しない（外部の画像生成AIでユーザーに生成してもらう）
- 写真画像（Web取得）案を生成しない。スキップのみ
- スキルが独自に複数の切り口プロンプトを作らない。画像説明をそのまま使い、種類ごとの明示指示のみ付加する
- イメージ画像には説明文・キャプション・ラベル・タイトルの文字を入れさせない（図解はラベル文字あり可）
- notebook を新規作成・削除しない。`notebook-id.md` の既存 ID を使う
- キャラクター参照・スーパーニャンコ URL を付けない
- Drive アップロード・Gmail 送信をしない。ローカル保存のみ
- 図解は各セクション 3 枚を守る。過不足を出さない
