# visual_infographic

文章を渡すと、N パターンの図解プロンプトを自動生成し、NotebookLM Infographics で図解画像を N 枚作成して Google Drive の outputs/images フォルダに保存する。
画像 N 枚 + 対応するプロンプト markdown N つ（計 2N ファイル）をアップロードする。

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

### Step 1. テキスト取得・count 確認

- `$ARGUMENTS` から count を読み取る（先頭が整数ならその値、なければデフォルト 3）
- テキストを `/tmp/infographic_source.txt` に書き出す
  - 直接渡しの場合: そのまま書き出す
  - ファイルパス指定の場合: `Read` ツールで内容を確認してから書き出す

### Step 2. メインタイトル・サブタイトルを決める

**メインタイトルの決定ルール**:
- テキストが「実は、」で始まる場合 → 冒頭の1文（句点「。」は除く）をそのままメインタイトルにする
- それ以外 → テキストのテーマを表す短いキャッチーなタイトル（15字以内）を生成する

**サブタイトルの決定ルール**:
- 内容の概要を説明する一文
- 「〜を解説します」という形は禁止。内容を端的に述べる形にする

### Step 3. count 個のプロンプトを生成

テキストの内容・構造に最適な図解レイアウトを判断し、count 個の異なるパターンを考える。
パターンタイプは固定せず、内容に応じて選ぶ。参考例：
- ステップ・フロー型（プロセスや変化を時系列で表現）
- 比較・対比型（Before/After、2つの概念の対比）
- 中心放射型（コアコンセプトを中央に、関連要素を周囲に）
- タイムライン型（歴史的経緯や時代の流れ）
- ピラミッド型（重要度の階層構造）
- チェックリスト型（箇条書きで要点を列挙）
など

各パターンで以下のテンプレートを完成させる：

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
* キャラクター指定：キャラクターとして、スーパーニャンコ（額に赤いハート、卒業帽をかぶり、赤いマントをつけた青いネコのキャラクター）を含めてください。白人間（輪郭だけを描いた白一色の人間の絵）の使用は禁止します。
* 装飾：

# 図解の構成・レイアウト
[パターンごとの具体的な構成・レイアウト指示を記述]
```

### Step 4. プロンプト markdown を count 個のファイルに保存

ファイル名: `outputs/infographic_YYYY-MM-DD_1.md` ～ `outputs/infographic_YYYY-MM-DD_N.md`

各ファイルの構成：
```markdown
パターン: [パターン名]

[そのパターンのプロンプト全文]
```

### Step 5. count 枚のインフォグラフィックを生成（1 notebook）

**1枚目**: `make-infographic --keep` で notebook を作成しながら生成。notebook_id を出力からパースする。

```bash
ROOT=$(git rev-parse --show-toplevel)
DATE=$(date +%Y-%m-%d)

OUTPUT=$(python3 "$ROOT/scripts/notebooklm_manager.py" make-infographic \
  --file /tmp/infographic_source.txt \
  --title "図解_${DATE}" \
  --infographic-title "[メインタイトル]" \
  --instructions "[パターン1のプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$ROOT/outputs/infographic_${DATE}_1.png" \
  --keep 2>&1)
echo "$OUTPUT"
NOTEBOOK_ID=$(echo "$OUTPUT" | grep "ノートブック作成" | sed 's/.*: //')
```

**2枚目以降（i = 2 ～ count）**: 同じ notebook_id を使って生成。各パターンのプロンプトを渡す。

```bash
# i 枚目（i = 2 ～ count を繰り返す）
python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
  --instructions "[パターンiのプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$ROOT/outputs/infographic_${DATE}_i.png"
```

**`--instructions` が長い場合**: 一時ファイルに書き出して `"$(cat /tmp/prompt_N.txt)"` で渡す。

### Step 6. Google Drive にアップロード

フォルダ ID: `1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb`（outputs/images）

**ローカル環境**（gws が使える場合）:
```bash
cd "$ROOT/outputs"
for N in $(seq 1 COUNT); do
  gws drive +upload "infographic_${DATE}_${N}.png" --parent 1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb
  gws drive +upload "infographic_${DATE}_${N}.md"  --parent 1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb
done
```

**リモート環境**（gws がない場合）:
Drive MCP ツールを使ってアップロードする：
- `mcp__claude_ai_Google_Drive__create_file` で各ファイルをアップロード（parent: `1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb`）

各ファイルのアップロード結果（Drive URL）を表示する。

### Step 7. ローカルファイルを削除

アップロード成功を確認してから全ファイルを削除する。

```bash
for N in $(seq 1 COUNT); do
  rm "$ROOT/outputs/infographic_${DATE}_${N}.png"
  rm "$ROOT/outputs/infographic_${DATE}_${N}.md"
done
```

エラーが出た場合は削除せずユーザーに報告する。

## 完了後の報告

- 生成した画像の Drive URL（count 枚分）
- プロンプト markdown の Drive URL（count 個分）
- 作成された NotebookLM notebook のタイトルと ID

## 注意事項

- notebook は1つ作成される（`--keep` で保持）
- 画像生成は1枚あたり数分かかる場合がある
- gws がない環境（リモート）では Drive MCP ツールを使用する
