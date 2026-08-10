---
title: make-infographic
description: "make-infographic スキル"
category: 画像・同期
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

make-infographic スキル

## 詳細内容

# make-infographic

テキストまたはファイルを渡すと、NotebookLM を使ってインフォグラフィック（PNG）を生成する。

## 入力の受け取り方

ユーザーが渡す内容に応じて処理を分岐する：

- **テキストを直接渡した場合** → `--text` に渡す（長い場合は一時ファイルに書き出して `--file` でも可）
- **ファイルパスを指定した場合** → `--file` に渡す

## 引数

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `count` | `1` | 生成する枚数。例：`/make-infographic 3` で3枚生成 |

## 実行手順

1. 出力ファイル名を決める
   - 指定がなければ `outputs/infographic_YYYY-MM-DD.png` にする
   - 複数枚の場合は `outputs/infographic_YYYY-MM-DD_1.png`, `_2.png`, ... と連番にする
   - タイトルはテーマや内容から短く決める

2. 指定された枚数（デフォルト1）だけコマンドを繰り返し実行する：

```bash
# テキスト直接渡しの場合
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py make-infographic \
  --text "（テキスト内容）" \
  --title "（ノートブックタイトル）" \
  --infographic-title "（インフォグラフィックのタイトル）" \
  --output $(git rev-parse --show-toplevel)/outputs/infographic_YYYY-MM-DD.png

# ファイル指定の場合
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py make-infographic \
  --file /path/to/file.txt \
  --title "（ノートブックタイトル）" \
  --infographic-title "（インフォグラフィックのタイトル）" \
  --output $(git rev-parse --show-toplevel)/outputs/infographic_YYYY-MM-DD.png
```

- `--infographic-title` はインフォグラフィック画像内のタイトル。指定がなければ省略。
- `--title` はNotebookLMのノートブック名（内部管理用）。
- `--instructions` は生成への追加指示（任意）。言語指定などに使う。例：`--instructions "Generate the infographic in Japanese"`
- 複数枚生成する場合、同じコマンドを枚数分そのまま繰り返す（毎回異なるバリエーションが生成される）。

## デフォルトオプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--orientation` | `landscape` | 横向き |
| `--detail` | `standard` | 標準詳細度 |
| `--style` | `sketch-note` | スケッチノート風 |
| `--language` | `ja` | 言語コード（日本語は `ja`） |

スタイル変更が必要な場合はユーザーに確認してから変更する。

## 生成後の処理

1. `/sync-to-drive` スキルを実行して Google Drive の `outputs` フォルダへアップロードする。
2. アップロード成功を確認したら、今回生成したファイルをローカルから削除する：
```bash
rm outputs/infographic_YYYY-MM-DD_1.png outputs/infographic_YYYY-MM-DD_2.png ...
```
（エラーが出た場合は削除せずユーザーに報告する）

## 完了後の報告

- 1枚の場合：Drive へのアップロード結果とローカル削除結果を報告する。
- 複数枚の場合：生成した全ファイルのアップロード・削除結果をリストで報告する。

