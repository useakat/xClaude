---
name: visual_section-imager
description: draft/image-plan.md（H2ごとに1案へ絞り込み済み）を入力に、各画像の説明を notebook-id.md の NotebookLM notebook に渡して、図解画像はinfographic指示・イメージ画像は情景画像指示（文字なし）で各3枚生成し、draft/images に <H2タイトル>_<画像種類>_<連番>.png と使用プロンプト .md を保存する。生成失敗時は自動リトライ。写真画像案はスキップ。
---

# visual_section-imager

`draft/image-plan.md`（各 H2 セクションを 1 案に絞り込み済み）を入力に、各セクションの画像説明を NotebookLM に渡し、図解・イメージ画像を notebook 内で生成して `draft/images/` に保存する。

入力（`draft/image-plan.md` のパス。省略時は作業中プロジェクトの `draft/image-plan.md`）: $ARGUMENTS

## 目的

- 絞り込み済みの画像案を、実際の画像に変換する
- 各画像説明につき 3 枚を NotebookLM に生成させ、`draft/images/` に保存する
- 「画像案 → 実画像」工程を標準化し、note 記事の画像準備を完結させる

## 手順

ルートは `ROOT=$(git rev-parse --show-toplevel)`。

1. **認証確認**（初回のみ）。以下のどちらかが存在するか確認する：
   - `~/.notebooklm/storage_state.json`
   - `$ROOT/gcp/notebooklm_storage_state.json`

   どちらも無い場合、Drive MCP で取得する：
   1. `mcp__claude_ai_Google_Drive__search_files` で `notebooklm_storage_state.json` を検索
   2. `mcp__claude_ai_Google_Drive__read_file_content` で内容（JSON テキスト）を取得
   3. Write ツールで `$ROOT/gcp/notebooklm_storage_state.json` に書き込む

   Drive にも無ければ中断し、ローカルで `bash scripts/notebooklm_auth_push.sh` の実行を案内する。

2. **入力を特定する。** `$ARGUMENTS` がファイルパスならそれを、空なら作業中プロジェクトの `draft/image-plan.md` を使う。`PLAN` をそのパス、`PROJ` を `draft/` の親フォルダ（プロジェクトフォルダ）とする。

3. **NOTEBOOK_ID を取得する。** `cat "$PROJ/notebook-id.md"` の 1 行を `NOTEBOOK_ID` とする。空・不正なら中断してユーザーに知らせる。

4. **`image-plan.md` を解析する。** `## ` 行で H2 セクションに分割し、各セクションの絞り込まれた 1 案から **画像種類**（図解画像 / イメージ画像 / 写真画像）と **画像説明** を抽出する。`# 画像プランニング` 見出しは無視する。

5. **写真画像はスキップ。** 画像種類が「写真画像」のセクションは生成せず、「スキップ: <セクション>（写真画像）」と記録する。

6. **保存先を用意する。** `mkdir -p "$PROJ/draft/images"`。

7. **図解／イメージのセクションごとに instructions を組み立てる。** 画像説明の本文に、画像種類に応じた明示指示を加える：
   - **図解画像**: 末尾に「これは図解（インフォグラフィック）として作成してください。」を付ける
   - **イメージ画像**: 末尾に「図解ではなく、情景を描いたイメージ画像として作成してください。画像内には説明文・キャプション・ラベル・タイトルなどの文字を一切入れないでください。」を付ける

   この instructions を `draft/images/<safe>_<画像種類>_<連番>.md` に Write で保存する（連番 01〜03、3 枚とも同一内容）。

8. **ファイル名を安全化する。** `<safe>` は H2 セクションタイトルから `「」『』（）()`・空白・`/`・記号を `_` に置換／除去したもの。`<画像種類>` は `図解画像` / `イメージ画像`。

9. **画像を 3 枚生成する（失敗時リトライ付き）。** 同じ instructions で連番 01〜03 を 1 枚ずつ生成する。各連番は、`--output` の PNG が生成されなければ**最大 2 回まで再実行**（合計 3 回試行、各リトライ前に `sleep 5`）する。3 回とも生成できなければ「失敗: <ファイル名>」と記録して次の連番へ進む（全体は止めない）。
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
   # 各連番で gen_one "<...>_<連番>.png" "<...>_<連番>.md" を呼ぶ
   ```
   - notebook は新規作成しない（`make-infographic` ではなく `infographic`）。`NOTEBOOK_ID` を再利用する
   - キャラクター参照 URL（`--extra-source-url`）は付けない

10. **報告する。** 全セクション完了後、生成・スキップ結果を一覧で出力する。

## 出力形式

```
[画像生成結果]

## <H2タイトル1>（図解画像）
- draft/images/<safe>_図解画像_01.png
- draft/images/<safe>_図解画像_02.png
- draft/images/<safe>_図解画像_03.png

## <H2タイトル2>（イメージ画像）
- draft/images/<safe>_イメージ画像_01.png
- draft/images/<safe>_イメージ画像_02.png
- draft/images/<safe>_イメージ画像_03.png

## スキップ
- <H2タイトルX>（写真画像）

[/画像生成結果]
```

## 禁止事項

- 写真画像（Web取得）案を生成しない。スキップのみ
- スキルが独自に複数の切り口プロンプトを作らない。画像説明をそのまま渡す（種類ごとの明示指示のみ付加する）
- イメージ画像には説明文・キャプション・ラベル・タイトルの文字を入れさせない（図解画像はラベル文字あり可）
- notebook を新規作成・削除しない。`notebook-id.md` の既存 ID を使う
- キャラクター参照・スーパーニャンコ URL を付けない
- Drive アップロード・Gmail 送信をしない。ローカル保存のみ
- 各セクション 3 枚を守る。過不足を出さない
