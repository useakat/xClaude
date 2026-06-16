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
- 中心放射型（コアコンセプトを中央に、関連要素を周囲に）。**バブルの配置は、読者の視線が左上→左下→右上→右下と流れるよう設計する（導入→問題→解決の鍵→結論の順）**
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
* キャラクター指定：キャラクターとして、スーパーニャンコ（額に赤いハート、卒業帽をかぶり、赤いマントをつけた青いネコのキャラクター）を、この図解全体のタッチに合わせた手書き風で描いてください。スーパーニャンコの参照画像をソースに含めているので、その姿・特徴を踏まえて描いてください。白人間（輪郭だけを描いた白一色の人間の絵）の使用は禁止します。
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

### Step 5. count 枚のインフォグラフィックを生成・1 枚ずつ即アップロード

**ポリシー**: 各画像は生成完了後すぐに Drive にアップロード→ローカル削除する（全枚数まとめてではなく1枚ずつ）。アップロードした Drive URL は配列に保存し、Step 6 の Gmail 通知で使う。

アップロード先フォルダ ID: `1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb`（outputs/images）

**共通変数**:
```bash
ROOT=$(git rev-parse --show-toplevel)
DATE=$(date +%Y-%m-%d)
NYANKO_URL="https://drive.google.com/file/d/1SHyiHZ8io64nUXculZMqLkh8_TlV_goI/view?usp=drive_link"
FOLDER_ID="1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb"

PNG_URLS=()  # Drive URL を蓄積
MD_URLS=()
```

**ヘルパー**（1枚ぶんのアップロード＋ローカル削除をまとめた処理）:

ローカル環境（gws が使える場合）:
```bash
upload_pair() {
  local i="$1"
  local png="$ROOT/outputs/infographic_${DATE}_${i}.png"
  local md="$ROOT/outputs/infographic_${DATE}_${i}.md"
  local png_id md_id

  png_id=$(gws drive +upload "$png" --parent "$FOLDER_ID" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
  md_id=$(gws drive +upload "$md"  --parent "$FOLDER_ID" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")

  [ -n "$png_id" ] && [ -n "$md_id" ] || { echo "❌ アップロード失敗: $i 枚目"; return 1; }

  PNG_URLS+=("https://drive.google.com/file/d/${png_id}/view")
  MD_URLS+=("https://drive.google.com/file/d/${md_id}/view")

  rm "$png" "$md"
  echo "✓ $i 枚目アップロード＋ローカル削除完了"
}
```

リモート環境（gws がない場合）は `mcp__claude_ai_Google_Drive__create_file` を `parent="$FOLDER_ID"` で各ファイルに呼び、返ってきた `id` から URL を組み立てて配列に追記、その後ローカルを削除する（コードは環境に応じて組み立てる）。

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

# スーパーニャンコ参照画像
if ! echo "$SRC" | grep -q "super-nyanko-ref"; then
  python3 "$ROOT/scripts/notebooklm_manager.py" add-source-file "$NOTEBOOK_ID" \
    --url "$NYANKO_URL" --title super-nyanko-ref
fi
```

**全 N 枚（i = 1 ～ count）を `infographic` で生成 → 即アップロード**:

```bash
# i = 1, 2, ..., count を繰り返す
python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
  --instructions "[パターンiのプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$ROOT/outputs/infographic_${DATE}_${i}.png"

upload_pair "$i"
```

---

#### 【新規作成ブランチ】`REUSE=false`（従来動作）

**1枚目**: `make-infographic --keep` で notebook を作成しながら生成 → 即アップロード。スーパーニャンコ参照画像も `--extra-source-url` でソースに追加。notebook_id を出力からパースする。

```bash
OUTPUT=$(python3 "$ROOT/scripts/notebooklm_manager.py" make-infographic \
  --file /tmp/infographic_source.txt \
  --title "図解_${DATE}" \
  --infographic-title "[メインタイトル]" \
  --instructions "[パターン1のプロンプト全文]" \
  --extra-source-url "$NYANKO_URL" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$ROOT/outputs/infographic_${DATE}_1.png" \
  --keep 2>&1)
echo "$OUTPUT"
NOTEBOOK_ID=$(echo "$OUTPUT" | grep "ノートブック作成" | sed 's/.*: //')

upload_pair 1
```

**2枚目以降（i = 2 ～ count）**: 同じ notebook_id を使って生成 → 即アップロード。

```bash
# i = 2, 3, ..., count を繰り返す
python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
  --instructions "[パターンiのプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$ROOT/outputs/infographic_${DATE}_${i}.png"

upload_pair "$i"
```

**`--instructions` が長い場合**: 一時ファイルに書き出して `"$(cat /tmp/prompt_N.txt)"` で渡す。

アップロード失敗時はローカル削除せずユーザーに報告し、その時点で処理を止める。

### Step 6. Gmail で完了通知を送信

Step 5 で収集した `PNG_URLS` / `MD_URLS` を使って通知メールを送る。

件名: `【インフォグラフィック完成】{DATE} {メインタイトル冒頭20字}`

本文を `/tmp/infographic_mail.txt` に書き出してから `send_gmail.sh` で送信する：

```bash
ROOT=$(git rev-parse --show-toplevel)

# メインタイトルの冒頭20字を抜き出す
TITLE_SHORT=$(echo "[メインタイトル]" | cut -c1-20)

# 本文を組み立て（Step 5 で収集した PNG_URLS / MD_URLS を列挙）
cat > /tmp/infographic_mail.txt <<EOF
インフォグラフィック ${COUNT} 枚が生成され、Drive にアップロードされました。

■ 画像ファイル (${COUNT} 枚)
[各 PNG の Drive URL を番号付きで列挙]

■ プロンプト markdown (${COUNT} 個)
[各 MD の Drive URL を番号付きで列挙]

■ NotebookLM ノートブック
  タイトル: 図解_${DATE}
  ID: ${NOTEBOOK_ID}
EOF

bash "$ROOT/scripts/send_gmail.sh" \
  --to useakat@gmail.com \
  --subject "【インフォグラフィック完成】${DATE} ${TITLE_SHORT}" \
  --body-file /tmp/infographic_mail.txt
```

送信に失敗した場合はエラーを報告するのみで、スキル全体は成功扱いとする。

## 完了後の報告

- 生成した画像の Drive URL（count 枚分）
- プロンプト markdown の Drive URL（count 個分）
- NotebookLM notebook の ID
  - 新規作成ブランチ: 作成した notebook のタイトルと ID
  - 再利用ブランチ: **再利用した** notebook ID（新規作成・削除はしていない旨を明記）と、追加したソース（原稿テキスト／スーパーニャンコ）の有無
- Gmail 送信結果（送信成功 or 失敗のメッセージ ID）

## 注意事項

- **既存 notebook の再利用**: プロジェクトフォルダ（`projects/w003/<YYYYMMDD_topic>/`）に `notebook-id.md`（ハイフン区切り・1行目に notebook ID）があれば、その notebook を使って生成する（新規作成・削除しない）。`--file` のパスから自動判定するほか、`--project-dir` で明示指定もできる。
  - 再利用時は 1枚目の前に `list-sources` でソースを確認し、`infographic_source.txt`（原稿）と `super-nyanko-ref`（ニャンコ参照画像）が無ければ自動で追加する。
  - 既存 notebook に原稿以外のソース（Deep Research の文献等）があると、図解の内容にそれらが混ざる場合がある（再利用は「その notebook の内容で図解してよい」前提）。
- notebook は新規作成ブランチでは1つ作成される（`--keep` で保持）
- 画像生成は1枚あたり数分かかる場合がある
- gws がない環境（リモート）では Drive MCP ツールを使用する
