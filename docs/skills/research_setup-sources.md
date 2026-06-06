---
title: research_setup-sources
description: テーマを受け取り NotebookLM ノートブックを作成して Deep Research でソースを収集・追加し、notebook_id を返す。
category: リサーチ・分析
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

テーマを受け取り NotebookLM ノートブックを作成して Deep Research でソースを収集・追加し、notebook_id を返す。

## 詳細内容

# research_setup-sources

## 目的

- 与えられたテーマで NotebookLM ノートブックを作成する
- Deep Research を実行して信頼性の高い情報源をソースとして追加する
- 後続スキルで使える notebook_id をチャットに表示する

## 引数

`$ARGUMENTS` — テーマ（例：「重力波」「ブラックホール蒸発」）
未指定ならユーザーに入力を求める。

---

## 手順

### Step 0. 認証確認

以下のどちらかが存在するか確認する：
- `~/.notebooklm/storage_state.json`
- `gcp/notebooklm_storage_state.json`（`git rev-parse --show-toplevel` 配下）

存在しない場合は中断し `bash scripts/notebooklm_auth_push.sh` を案内する。

### Step 1. テーマ取得

`$ARGUMENTS` をテーマとして読み取る。未指定ならユーザーに入力を求める。

### Step 2. ノートブック作成

```bash
ROOT=$(git rev-parse --show-toplevel)
DATE=$(date +%Y-%m-%d)
THEME="$ARGUMENTS"

OUTPUT=$(python3 "$ROOT/scripts/notebooklm_manager.py" create "nb_${THEME}_${DATE}" 2>&1)
echo "$OUTPUT"
NOTEBOOK_ID=$(echo "$OUTPUT" | grep "✓ 作成:" | awk '{print $3}')
echo "NOTEBOOK_ID: $NOTEBOOK_ID"
```

### Step 3. Deep Research 実行（ソース自動収集・追加）

```bash
DR_QUERY="${THEME}

【収集する情報源の条件】
優先: 査読付き論文・大学/研究機関のページ・科学メディア・政府機関・百科事典
除外: 企業の製品紹介ページ・販売サイト・メーカー公式サイト・ECサイト"

python3 "$ROOT/scripts/notebooklm_manager.py" deep-research "$NOTEBOOK_ID" "$DR_QUERY" 2>&1
```

Deep Research は数分かかる場合がある。完了したら追加されたソース一覧を表示する。

### Step 4. 完了報告

以下をチャットに表示してスキルを終了する：

```
✅ ノートブック作成・ソース収集完了

- テーマ　　　　: {THEME}
- ノートブック ID: {NOTEBOOK_ID}
- 追加ソース数　: {N} 件

このノートブック ID は check-fact-lim・research_trivia-source などで利用できます。
```

---

## 出力形式

- 標準出力にノートブック ID を必ず表示する
- ソース一覧は省略せず全件表示する

## 禁止事項

- トリビアネタ選定・解説文生成はしない（後続スキルの責務）
- notebook_id を省略・短縮して表示しない
