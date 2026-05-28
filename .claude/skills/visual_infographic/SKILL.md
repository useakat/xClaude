# visual_infographic

文章を渡すと、NotebookLM にインフォグラフィック作成プロンプトを 3 パターン生成させ、それをもとに図解画像を 3 枚作成して Google Drive の outputs/images フォルダに保存する。
画像 3 枚 + 対応するプロンプト markdown 3 つ（計 6 ファイル）をアップロードする。

## 入力

- **テキスト直接渡し**: ユーザーがチャットにテキストを貼り付けた場合
- **ファイルパス指定**: `--file /path/to/file.md` など

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

### Step 1. テキスト取得

- テキストを `/tmp/infographic_source.txt` に書き出す
  - 直接渡しの場合: そのまま書き出す
  - ファイルパス指定の場合: `Read` ツールで内容を確認してから書き出す

**共通変数**:
```bash
ROOT=$(git rev-parse --show-toplevel)
DATE=$(date +%Y-%m-%d)
NYANKO_URL="https://drive.google.com/file/d/1SHyiHZ8io64nUXculZMqLkh8_TlV_goI/view?usp=drive_link"
FOLDER_ID="1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb"
SKILL_DIR="$ROOT/.claude/skills/visual_infographic"

source "$SKILL_DIR/infographic_config.env"

PNG_URLS=()
MD_URLS=()
```

### Step 2. notebook を作成（ソーステキスト＋スーパーニャンコ画像を追加）

```bash
SETUP_OUTPUT=$(python3 "$ROOT/scripts/notebooklm_manager.py" setup-notebook \
  --file /tmp/infographic_source.txt \
  --title "図解_${DATE}" \
  --extra-source-url "$NYANKO_URL" 2>&1)
echo "$SETUP_OUTPUT"
NOTEBOOK_ID=$(echo "$SETUP_OUTPUT" | grep "ノートブック作成" | sed 's/.*: //')
```

`NOTEBOOK_ID` が取得できなければ中断してエラーを報告する。

### Step 3. NotebookLM にプロンプトを生成させる

`ask_template.txt` の内容を質問として NotebookLM に送り、3 パターンのプロンプトを生成させる：

```bash
ASK_RESULT=$(python3 "$ROOT/scripts/notebooklm_manager.py" ask \
  "$NOTEBOOK_ID" \
  "$(cat "$SKILL_DIR/ask_template.txt")" 2>&1)
echo "$ASK_RESULT"
```

レスポンスは `---` で区切られた 3 ブロックを含む。各ブロックをパースして
`/tmp/prompt_1.txt` `/tmp/prompt_2.txt` `/tmp/prompt_3.txt` に書き出す：

```bash
python3 - <<EOF
import sys, re

text = """$ASK_RESULT"""
blocks = [b.strip() for b in re.split(r'\n---+\n', text) if b.strip()]
for i, block in enumerate(blocks[:3], start=1):
    with open(f'/tmp/prompt_{i}.txt', 'w') as f:
        f.write(block)
    print(f"✓ プロンプト {i} 保存: /tmp/prompt_{i}.txt")
EOF
```

### Step 4. プロンプト markdown を 3 個のファイルに保存

各 `/tmp/prompt_N.txt` の内容を `outputs/` フォルダにもコピーして保存する：

ファイル名: `outputs/infographic_YYYY-MM-DD_1.md` ～ `outputs/infographic_YYYY-MM-DD_3.md`

各ファイルの構成：
```markdown
パターン: [パターン名（プロンプト冒頭から判断）]

[プロンプト全文]
```

### Step 5. 3 枚のインフォグラフィックを生成・1 枚ずつ即アップロード

**ポリシー**: 各画像は生成完了後すぐに Drive にアップロード→ローカル削除する。

アップロード先フォルダ ID: `1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb`（outputs/images）

**ヘルパー**（1 枚ぶんのアップロード＋ローカル削除）:

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

リモート環境（gws がない場合）は `mcp__claude_ai_Google_Drive__create_file` を `parent="$FOLDER_ID"` で各ファイルに呼び、返ってきた `id` から URL を組み立てて配列に追記、その後ローカルを削除する。

**3 枚を順番に生成**（`infographic` コマンドで既存 notebook を使用）:

```bash
for i in 1 2 3; do
  python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
    --instructions "$(cat /tmp/prompt_${i}.txt)" \
    --language "$INFOGRAPHIC_LANGUAGE" \
    --orientation "$INFOGRAPHIC_ORIENTATION" \
    --detail "$INFOGRAPHIC_DETAIL" \
    --style "$INFOGRAPHIC_STYLE" \
    --output "$ROOT/outputs/infographic_${DATE}_${i}.png"

  upload_pair "$i"
done
```

アップロード失敗時はローカル削除せずユーザーに報告し、その時点で処理を止める。

**notebook を削除**:
```bash
python3 "$ROOT/scripts/notebooklm_manager.py" delete "$NOTEBOOK_ID"
```

### Step 6. Gmail で完了通知を送信

Step 5 で収集した `PNG_URLS` / `MD_URLS` を使って通知メールを送る。

件名: `【インフォグラフィック完成】{DATE} {メインタイトル冒頭20字}`

本文を `/tmp/infographic_mail.txt` に書き出してから `send_gmail.sh` で送信する：

```bash
ROOT=$(git rev-parse --show-toplevel)

cat > /tmp/infographic_mail.txt <<MAILEOF
インフォグラフィック 3 枚が生成され、Drive にアップロードされました。

■ 画像ファイル (3 枚)
[各 PNG の Drive URL を番号付きで列挙]

■ プロンプト markdown (3 個)
[各 MD の Drive URL を番号付きで列挙]

■ NotebookLM ノートブック
  タイトル: 図解_${DATE}
  ID: ${NOTEBOOK_ID}（削除済み）
MAILEOF

bash "$ROOT/scripts/send_gmail.sh" \
  --to useakat@gmail.com \
  --subject "【インフォグラフィック完成】${DATE} ${TITLE_SHORT}" \
  --body-file /tmp/infographic_mail.txt
```

送信に失敗した場合はエラーを報告するのみで、スキル全体は成功扱いとする。

## 完了後の報告

- 生成した画像の Drive URL（3 枚分）
- プロンプト markdown の Drive URL（3 個分）
- Gmail 送信結果（送信成功 or 失敗のメッセージ ID）

## 注意事項

- notebook は Step 2 で 1 つ作成し、Step 5 完了後に削除する
- 画像生成は 1 枚あたり数分かかる場合がある
- gws がない環境（リモート）では Drive MCP ツールを使用する
- Infographic 生成設定（言語/向き/スタイル/詳細度）は `infographic_config.env` で管理する
- NotebookLM への質問テンプレートは `ask_template.txt` で管理する
