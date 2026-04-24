# make-infographic

テキストまたはファイルを渡すと、NotebookLM を使ってインフォグラフィック（PNG）を生成する。

## 入力の受け取り方

ユーザーが渡す内容に応じて処理を分岐する：

- **テキストを直接渡した場合** → `--text` に渡す（長い場合は一時ファイルに書き出して `--file` でも可）
- **ファイルパスを指定した場合** → `--file` に渡す

## 実行手順

1. 出力ファイル名を決める
   - 指定がなければ `ポスト用/infographic_YYYY-MM-DD.png` にする
   - タイトルはテーマや内容から短く決める

2. コマンドを実行する：

```bash
# テキスト直接渡しの場合
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py make-infographic \
  --text "（テキスト内容）" \
  --title "（ノートブックタイトル）" \
  --infographic-title "（インフォグラフィックのタイトル）" \
  --output $(git rev-parse --show-toplevel)/ポスト用/infographic_YYYY-MM-DD.png

# ファイル指定の場合
python3 $(git rev-parse --show-toplevel)/scripts/notebooklm_manager.py make-infographic \
  --file /path/to/file.txt \
  --title "（ノートブックタイトル）" \
  --infographic-title "（インフォグラフィックのタイトル）" \
  --output $(git rev-parse --show-toplevel)/ポスト用/infographic_YYYY-MM-DD.png
```

- `--infographic-title` はインフォグラフィック画像内のタイトル。指定がなければ省略。
- `--title` はNotebookLMのノートブック名（内部管理用）。

## デフォルトオプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--orientation` | `landscape` | 横向き |
| `--detail` | `standard` | 標準詳細度 |
| `--style` | `sketch-note` | スケッチノート風 |

スタイル変更が必要な場合はユーザーに確認してから変更する。

## 完了後の報告

保存先パスを1行だけ報告する。
