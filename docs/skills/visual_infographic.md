---
title: visual_infographic
description: "visual_infographic スキル"
category: 画像・同期
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

visual_infographic スキル

## 詳細内容

# visual_infographic

文章を渡すと、N パターンの図解プロンプトを自動生成し、NotebookLM Infographics で図解画像を N 枚作成して、プロジェクトの `draft/` フォルダに保存する。
画像 N 枚 + 対応するプロンプト markdown N つ（計 2N ファイル）を `draft/` にローカル保存する（Drive へのアップロードは行わない）。

## 引数

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `count` | `3` | 生成する枚数。例：`/visual_infographic 5` で5枚生成 |

## 入力

- **テキスト直接渡し**: ユーザーがチャットにテキストを貼り付けた場合
- **ファイルパス指定**: `--file /path/to/file.md` など

`$ARGUMENTS` の先頭が整数の場合はそれを count として読み取る。それ以外はすべてテキストとして扱う。

## 実行手順

### Step 0. 認証確認（初回のみ）

以下のどちらかが存在するか確認する：
- `~/.notebooklm/storage_state.json`
- `/root/xClaude/gcp/notebooklm_storage_state.json`

**どちらも存在しない場合**、Drive MCP ツールで自動取得する：

1. `mcp__claude_ai_Google_Drive__search_files` で `notebooklm_storage_state.json` を検索
2. ヒットしたファイルの ID を取得
3. `mcp__claude_ai_Google_Drive__read_file_content` でファイル内容（JSON テキスト）を取得
4. Write ツールで `/root/xClaude/gcp/notebooklm_storage_state.json` に書き込む

Drive に該当ファイルがない場合はスキル実行を中断し、ユーザーに以下をローカルで実行するよう案内する：
```
bash scripts/notebooklm_auth_push.sh
```

### Step 1. テキスト取得・count 確認・プロジェクトフォルダ解決

- `$ARGUMENTS` から count を読み取る（先頭が整数ならその値、なければデフォルト 3）
- テキストを `/tmp/infographic_source.txt` に書き出す
  - 直接渡しの場合: そのまま書き出す
  - ファイルパス指定の場合: `Read` ツールで内容を確認してから書き出す

**プロジェクトフォルダ（`PROJECT_DIR`）の解決**（既存 notebook 再利用の判定に使う）:

- `--project-dir <dir>` が指定されていれば、それを `PROJECT_DIR` とする。
- 指定がなく `--file <path>` がある場合は、パスの先祖から `projects/w003/<名前>/` の階層を抜き出して `PROJECT_DIR` とする。
  ```bash
  # 例: --file が projects/w003/20260615_金の起源/output/index.md なら
  #     PROJECT_DIR=.../projects/w003/20260615_金の起源
  PROJECT_DIR=$(python3 -c "import os,sys,re;
p=os.path.abspath(sys.argv[1]);
m=re.search(r'(.*/projects/w003/[^/]+)/', p);
print(m.group(1) if m else '')" "<--file のパス>")
  ```
- どちらも無い（テキスト直接渡し等）場合は `PROJECT_DIR` を空のままにする（＝ notebook 再利用はせず新規作成）。
- `PROJECT_DIR` が決まったら `NBID_FILE="$PROJECT_DIR/notebook-id.md"` を控える。

**保存先（`SAVE_DIR`）の決定**: 生成物（png・プロンプト md）は **プロジェクトの `draft/` に保存する**。
- `PROJECT_DIR` が非空なら `SAVE_DIR="$PROJECT_DIR/draft"`。
- `PROJECT_DIR` が空なら（テキスト直接渡し等）`SAVE_DIR="$ROOT/outputs"` にフォールバック。
- 実行前に `mkdir -p "$SAVE_DIR"` する。**Drive へのアップロードは行わない。**

### Step 2. メインタイトル・サブタイトルを決める

**メインタイトルの決定ルール**:
- 入力テキストの**冒頭1文**（先頭から最初の句点「。」まで。句点は除く）を、そのままメインタイトルにする。
- 例: 入力が「金って、実は超新星爆発でもほとんど作れない元素だった。…」→ メインタイトル＝「金って、実は超新星爆発でもほとんど作れない元素だった」

**サブタイトルの決定ルール**:
- 内容の概要を説明する一文
- 「〜を解説します」という形は禁止。内容を端的に述べる形にする

### Step 3. count 個のプロンプトを「型テンプレート」から作成する

プロンプトはその場で自走生成せず、**`projects/w003/infographic_template/` の型テンプレート md を基に作成する**（パスはリポジトリルート基準で固定）。

テンプレート一覧（各ファイルが1つの型）:
- `step_flow.md`（ステップ・フロー型: プロセス・変化を時系列で）
- `compare_contrast.md`（比較・対比型: Before/After・2概念の対比）
- `radial.md`（中心放射型: コアを中央に、視線が左上→左下→右上→右下）
- `timeline.md`（タイムライン型: 歴史的経緯）
- `pyramid.md`（ピラミッド型: 重要度の階層）
- `checklist.md`（チェックリスト型: 要点列挙）

**手順**:

1. テンプレートディレクトリ `<repo>/projects/w003/infographic_template/` の存在を確認する。
   - **存在しない場合のみ**フォールバック: 下記「フォールバック（テンプレート不在時）」に従い従来方式で自走生成し、その旨を警告表示する。
2. 入力テキストの内容・構造に**最も合う `count` 個の型を選ぶ**（内容に合わない型は除外する。例: 明確な階層構造が無い内容なら `pyramid` を外す）。
3. 選んだ各テンプレートを **Read** し、**本文（`# ビジュアル・レイアウトの指示`・`# 図解の構成・レイアウト` の共通指示、スーパーニャンコ指定、テキスト厳守ルール）はそのまま使う**。改変するのは以下の差し込み箇所だけ:
   - `[メインタイトル]` → Step 2 で決めた冒頭1文
   - `[サブタイトル]` → Step 2 で決めたサブタイトル
   - `[各ステップの見出し]` `[一言説明]` `[コアコンセプト]` `[結論の一文]` 等のプレースホルダ → 入力テキストの内容で具体化
   - 構成中の `[3〜5]` `[4]` などの個数指定 → 内容に合わせて確定
4. 共通のビジュアル指示・キャラクター指定・「テキストを一言一句変えない」ルールは**書き換えない**。
5. 完成したプロンプトを Step 4 の規則で保存する（先頭行の `パターン: …` 行も残す）。

**フォールバック（テンプレート不在時のみ）**: 次の参考例から count 個の型を選び、下記テンプレートを完成させる。
- ステップ・フロー型／比較・対比型／中心放射型（視線 左上→左下→右上→右下）／タイムライン型／ピラミッド型／チェックリスト型

```
# テーマ・全体像
* メインタイトル：[メインタイトル]
* サブタイトル（概要）：[サブタイトル]

# ビジュアル・レイアウトの指示
* 背景：白または非常に薄いオフホワイトなどの無地を基調とし、手書きの線や色が際立つシンプルな背景にしてください。
* カラー：黒のペン画の輪郭線に、淡い水彩やマーカーのような優しい色合い（オレンジ、黄色、水色など）でアクセントをつけてください。
* テキスト描写の厳守：画像内のテキストはAI側で勝手に要約や言い換えを行わず、指定した文字を一言一句違わず正確に書き込んでください。
* タイトル：上部に大きく配置し、背面にマーカーで引いたような帯を入れて強調してください。
* サブタイトル：タイトル下部に、タイトルより小さい文字で書いて配置してください。
* テキスト: 結論や印象的なフレーズには「吹き出し」を使って強調してください。
* キャラクター指定：キャラクターとして、スーパーニャンコ（額に赤いハート、卒業帽をかぶり、赤いマントをつけた青いネコのキャラクター）を、この図解全体のタッチに合わせた手書き風で描いてください。スーパーニャンコの参照画像をソースに含めているので、その姿・特徴を踏まえて描いてください。白人間（輪郭だけを描いた白一色の人間の絵）の使用は禁止します。
* 装飾：

# 図解の構成・レイアウト
[パターンごとの具体的な構成・レイアウト指示を記述]
```

### Step 4. プロンプト markdown を count 個のファイルに保存

ファイル名: `$SAVE_DIR/infographic_01.md` ～ `$SAVE_DIR/infographic_NN.md`（`NN` は2桁ゼロ詰めの連番）。

各ファイルの構成：
```markdown
パターン: [パターン名]

[そのパターンのプロンプト全文]
```

### Step 5. count 枚のインフォグラフィックを生成し draft/ に保存

**ポリシー**: 各画像は生成完了後すぐに `$SAVE_DIR`（＝プロジェクトの `draft/`）へ保存する。**Drive へのアップロードは行わない。ローカル削除もしない。** プロンプト md（Step 4）も同じ `$SAVE_DIR` に置き、`infographic_NN.png` と `infographic_NN.md` がペアで残る。

**共通変数**:
```bash
ROOT=$(git rev-parse --show-toplevel)
NYANKO_REF="$ROOT/references/スーパーニャンコアイコン.png"  # ローカル参照画像（Drive DL 不要）
mkdir -p "$SAVE_DIR"
```

**ブランチ判定**: `PROJECT_DIR`（Step 1）に `notebook-id.md` があり中身が非空なら **再利用ブランチ**、無ければ **新規作成ブランチ**。

```bash
REUSE=false
if [ -n "$PROJECT_DIR" ] && [ -s "$NBID_FILE" ]; then
  NOTEBOOK_ID=$(head -1 "$NBID_FILE" | tr -d '[:space:]')
  [ -n "$NOTEBOOK_ID" ] && REUSE=true
fi
```

---

#### 【再利用ブランチ】`REUSE=true`（既存 notebook を使う・新規作成も削除もしない）

**1枚目を生成する前に、ソースを担保する**（無いものだけ追加）:

```bash
SRC=$(python3 "$ROOT/scripts/notebooklm_manager.py" list-sources "$NOTEBOOK_ID")

# 原稿テキスト
if ! echo "$SRC" | grep -q "infographic_source.txt"; then
  python3 "$ROOT/scripts/notebooklm_manager.py" add-text "$NOTEBOOK_ID" \
    --file /tmp/infographic_source.txt
fi

# スーパーニャンコ参照画像（references/ のローカル画像を --file で追加）
if ! echo "$SRC" | grep -q "super-nyanko-ref"; then
  python3 "$ROOT/scripts/notebooklm_manager.py" add-source-file "$NOTEBOOK_ID" \
    --file "$NYANKO_REF" --title super-nyanko-ref
fi
```

**全 N 枚（i = 1 ～ count）を `infographic` で生成 → `draft/` に保存**:

```bash
# i = 1, 2, ..., count を繰り返す（NN は2桁ゼロ詰めの連番）
python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
  --instructions "[パターンiのプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$SAVE_DIR/infographic_$(printf '%02d' "$i").png"
echo "✓ $i 枚目を $SAVE_DIR に保存"
```

---

#### 【新規作成ブランチ】`REUSE=false`

**1枚目を生成する前に、notebook を作成してソースを揃える**（原稿テキスト＋ローカルのスーパーニャンコ参照画像）。Drive からの DL は不要。

```bash
OUTPUT=$(python3 "$ROOT/scripts/notebooklm_manager.py" create "図解_$(date +%Y-%m-%d)" 2>&1)
echo "$OUTPUT"
NOTEBOOK_ID=$(echo "$OUTPUT" | grep "✓ 作成:" | awk '{print $3}')

# 原稿テキスト
python3 "$ROOT/scripts/notebooklm_manager.py" add-text "$NOTEBOOK_ID" \
  --file /tmp/infographic_source.txt
# スーパーニャンコ参照画像（references/ のローカル画像を --file で追加）
python3 "$ROOT/scripts/notebooklm_manager.py" add-source-file "$NOTEBOOK_ID" \
  --file "$NYANKO_REF" --title super-nyanko-ref
```

**全 N 枚（i = 1 ～ count）を `infographic` で生成 → `draft/` に保存**:

```bash
# i = 1, 2, ..., count を繰り返す（NN は2桁ゼロ詰めの連番）
python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
  --instructions "[パターンiのプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$SAVE_DIR/infographic_$(printf '%02d' "$i").png"
echo "✓ $i 枚目を $SAVE_DIR に保存"
```

**`--instructions` が長い場合**: 一時ファイルに書き出して `"$(cat /tmp/prompt_N.txt)"` で渡す。

生成に失敗した枚があればユーザーに報告し、その時点で処理を止める（成功済みの png・md は `draft/` に残す）。

### Step 6. Gmail で完了通知を送信

生成した png・md は `draft/`（`$SAVE_DIR`）にローカル保存される。通知メールには **保存先のローカルパス**を列挙する（Drive URL は使わない）。

件名: `【インフォグラフィック完成】{DATE} {メインタイトル冒頭20字}`

本文を `/tmp/infographic_mail.txt` に書き出してから `send_gmail.sh` で送信する：

```bash
ROOT=$(git rev-parse --show-toplevel)

# メインタイトルの冒頭20字を抜き出す
TITLE_SHORT=$(echo "[メインタイトル]" | cut -c1-20)

cat > /tmp/infographic_mail.txt <<EOF
インフォグラフィック ${COUNT} 枚を生成し、プロジェクトの draft/ に保存しました。

■ 保存先フォルダ
  ${SAVE_DIR}

■ ファイル (${COUNT} 枚 × png/md)
  infographic_01.png / infographic_01.md
  …
  infographic_NN.png / infographic_NN.md

■ NotebookLM ノートブック
  ID: ${NOTEBOOK_ID}
EOF

bash "$ROOT/scripts/send_gmail.sh" \
  --to useakat@gmail.com \
  --subject "【インフォグラフィック完成】$(date +%Y-%m-%d) ${TITLE_SHORT}" \
  --body-file /tmp/infographic_mail.txt
```

送信に失敗した場合はエラーを報告するのみで、スキル全体は成功扱いとする。

## 完了後の報告

- 生成した画像のローカルパス（`draft/infographic_NN.png`、count 枚分）
- プロンプト markdown のローカルパス（`draft/infographic_NN.md`、count 個分）
- NotebookLM notebook の ID
  - 新規作成ブランチ: 作成した notebook のタイトルと ID
  - 再利用ブランチ: **再利用した** notebook ID（新規作成・削除はしていない旨を明記）と、追加したソース（原稿テキスト／スーパーニャンコ）の有無
- Gmail 送信結果（送信成功 or 失敗のメッセージ ID）

## 注意事項

- **既存 notebook の再利用**: プロジェクトフォルダ（`projects/w003/<YYYYMMDD_topic>/`）に `notebook-id.md`（ハイフン区切り・1行目に notebook ID）があれば、その notebook を使って生成する（新規作成・削除しない）。`--file` のパスから自動判定するほか、`--project-dir` で明示指定もできる。
  - 再利用時は 1枚目の前に `list-sources` でソースを確認し、`infographic_source.txt`（原稿）と `super-nyanko-ref`（ニャンコ参照画像）が無ければ自動で追加する。
  - 既存 notebook に原稿以外のソース（Deep Research の文献等）があると、図解の内容にそれらが混ざる場合がある（再利用は「その notebook の内容で図解してよい」前提）。
- notebook は新規作成ブランチでは `create` で1つ作成され、そのまま保持される（自動削除しない）
- **スーパーニャンコ参照画像はローカルの `references/スーパーニャンコアイコン.png` を `--file` で追加する**（Drive からの DL は不要。`--file` 経路は拡張子から MIME を判定するため `file` コマンドにも依存しない）
- **生成物（png・md）はプロジェクトの `draft/`（`$SAVE_DIR`）に保存する。Drive へのアップロードは行わない**（`PROJECT_DIR` が空のときのみ `outputs/` にフォールバック）
- 画像生成は1枚あたり数分かかる場合がある

