# Claude Code から NotebookLM を操作する：ヘッドレス環境での認証設定とインフォグラフィック自動生成

## はじめに

NotebookLM は Google が提供するAIノートブックツールで、PDFや記事などのソースを読み込ませて質問したり、音声概要（ポッドキャスト）を生成したりできる。

これをブラウザではなく、Claude Code（AIコーディングアシスタントのCLI）から自動操作できたら面白い。記事の下書きを渡したらインフォグラフィックを自動生成してくれる、とか。

そこで今回は、[notebooklm-py](https://github.com/teng-lin/notebooklm-py) というライブラリを使って、Claude Code から NotebookLM を操作できる環境を整えた。特に「ブラウザが使えないサーバー環境での認証」が少し工夫が必要だったので、その手順をまとめておく。

---

## notebooklm-py でできること

notebooklm-py は NotebookLM の Web UI を Python から操作するための非公式ライブラリ。以下のことができる：

- ノートブックの作成・削除・一覧取得
- ソースの追加（URL・テキスト・ファイル）
- Q&A（チャット）
- コンテンツ生成：
  - **音声概要**（MP3/MP4）
  - **動画概要**（MP4）
  - **スライドデッキ**（PDF/PPTX）
  - **インフォグラフィック**（PNG）← 今回のメイン
  - **クイズ・フラッシュカード**
  - **レポート・マインドマップ**

---

## インストール

### ローカル環境（Mac/Windows）

```bash
pip install notebooklm
playwright install chromium
```

Debian/Ubuntu 系で `externally-managed-environment` エラーが出る場合は `pipx` を使う：

```bash
sudo apt install pipx
pipx ensurepath
source ~/.bashrc

pipx install notebooklm
~/.local/pipx/venvs/notebooklm/bin/playwright install chromium
```

### サーバー環境（headless）

サーバー側にも同じ手順でインストールする：

```bash
sudo apt install pipx
pipx ensurepath
pipx install notebooklm
```

ただし、サーバーにはブラウザがないため `notebooklm login` は実行できない。認証は次のセクションで説明する別の方法を使う。

---

## ブラウザなし環境での認証

notebooklm-py の認証は Playwright（ブラウザ自動化）を使った Google OAuth ログインが基本。ブラウザが使えるローカル環境では：

```bash
notebooklm login
```

でブラウザが開き、Google アカウントでログインすると `~/.notebooklm/storage_state.json` に認証情報（セッションクッキー）が保存される。

**サーバーでは、このファイルを scp で転送すれば OK。**

```bash
# ローカルでログイン後
scp ~/.notebooklm/storage_state.json root@<サーバーIP>:~/.notebooklm/storage_state.json
```

ライブラリはデフォルトで `~/.notebooklm/storage_state.json` を読みに行くので、転送後はそのまま動く。

### 認証情報の優先順位

notebooklm-py の認証は以下の順で解決される：

1. 明示的なパス引数
2. `NOTEBOOKLM_AUTH_JSON` 環境変数（JSON文字列をそのまま渡せる）
3. `~/.notebooklm/storage_state.json`

CI/CD 環境などファイルシステムが使えない場合は、`NOTEBOOKLM_AUTH_JSON` に `storage_state.json` の中身を設定すれば OK。

```bash
export NOTEBOOKLM_AUTH_JSON=$(cat ~/.notebooklm/storage_state.json)
```

**注意：Google セッションは数週間〜数ヶ月で切れる。** 切れたら再度ローカルでログインして転送し直す。

---

## Claude Code からの操作：notebooklm_manager.py

Claude Code から使いやすいよう、CLI ラッパースクリプト `notebooklm_manager.py` を作った。

### 主なコマンド

```bash
# ノートブック一覧
python3 scripts/notebooklm_manager.py list

# ノートブック作成（URLをソースとして追加）
python3 scripts/notebooklm_manager.py create "タイトル" --urls https://example.com

# 質問
python3 scripts/notebooklm_manager.py ask <notebook_id> "この論文の要点は？"

# 音声概要を生成してダウンロード
python3 scripts/notebooklm_manager.py audio <notebook_id> --output overview.mp3

# インフォグラフィックを生成
python3 scripts/notebooklm_manager.py infographic <notebook_id> --output output.png
```

### テキストからインフォグラフィックを一括生成

`make-infographic` コマンドを使うと、テキストや Markdown ファイルを渡すだけで：

1. 一時ノートブックの作成
2. テキストのソース追加
3. インフォグラフィック生成＆ダウンロード
4. ノートブックの削除（後片付け）

を全部やってくれる。

```bash
# テキストを直接渡す
python3 scripts/notebooklm_manager.py make-infographic \
  --text "（記事本文）" \
  --title "金星の大気" \
  --infographic-title "金星：灼熱の双子" \
  --output output.png

# ファイルを指定
python3 scripts/notebooklm_manager.py make-infographic \
  --file article.md \
  --infographic-title "金星：灼熱の双子" \
  --output output.png
```

### デフォルトのインフォグラフィック設定

| オプション | デフォルト | 意味 |
|-----------|-----------|------|
| `--orientation` | `landscape` | 横向き |
| `--detail` | `standard` | 標準詳細度 |
| `--style` | `sketch-note` | スケッチノート風 |

スタイルは他に `professional`、`bento-grid`、`editorial`、`scientific` なども選べる。

---

## 動作確認

認証が通っているかは以下で確認できる：

```bash
python3 scripts/notebooklm_manager.py list
```

ノートブック一覧が返ってきたら OK。

---

## まとめ

- notebooklm-py を使えば Python から NotebookLM を操作できる
- サーバー環境での認証は「ローカルでログイン → scp 転送」が最もシンプル
- `make-infographic` コマンドで記事テキストからインフォグラフィックを自動生成できる
- Claude Code のスキルとして組み込めば、記事執筆 → インフォグラフィック生成の流れを自動化できる

記事を書いたら `/make-infographic` を呼ぶ、という使い方が実用的。
