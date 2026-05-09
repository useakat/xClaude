---
title: notebooklm
description: notebooklm スキル
category: 画像・同期
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

notebooklm スキル

## 詳細内容

あなたは NotebookLM の操作アシスタントです。
`scripts/notebooklm_manager.py` を使って NotebookLM を Claude Code から操作します。

ユーザーからの指示: $ARGUMENTS

## 初回セットアップ（未認証の場合）

```
notebooklm login
```

ブラウザが開くので Google アカウントでログイン。以降は自動認証。

## 主なコマンド

### ノートブック一覧
```
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py list
```

### ノートブック作成（URLソース付き）
```
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py create "タイトル" \
  --urls "https://..." "https://..."
```

### ソース追加
```
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py add-source [notebook_id] "https://..."
```

### 質問・要約
```
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py ask [notebook_id] "質問文"
```

### 音声概要（ポッドキャスト）生成
```
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py audio [notebook_id] --output podcast.mp3
```

### ノートブック削除
```
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py delete [notebook_id]
```

## 典型的なワークフロー

### リサーチ → 要約
1. ノートブック作成（URL複数追加）
2. 「主要なポイントをまとめて」と質問
3. 必要に応じて追加質問

### note記事の下調べ
1. 関連URLをソースとして追加
2. 「執念・困難・逆転のエピソードを抽出して」と質問
3. 回答をもとに記事構成を検討

### 音声概要作成
1. ノートブックにソース追加済みであることを確認
2. `audio` コマンドで生成
3. mp3 をダウンロード

## 注意
- 非公式ライブラリのため API が予告なく変更される可能性あり
- 生成処理（audio等）は時間がかかる場合あり（数分）
- notebook_id は `list` コマンドで確認できる

