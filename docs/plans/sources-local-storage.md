# 実装計画: ローカルソース管理（NotebookLM 代替）

作成日: 2026-06-14  
ステータス: 保留中

---

## Context

VPS 環境では NotebookLM が使用不可。現在 `research_setup-sources` スキルが NotebookLM ノートブックを作成し `notebook_id` を返す。`check-fact-lim` がその `notebook_id` を使って「ソース限定ファクトチェック」を行う。この2スキルを NotebookLM なしで動作するよう置き換える。

---

## 実装方針

**ローカル `sources/` ディレクトリ方式**

- NotebookLM の「ノートブック ID」→ ローカルの `sources/` フォルダに置き換え
- ソースは URL からテキストに変換してローカル保存
- `_index.md` にサマリーを記録し、Claude がまずそこを読んで必要なファイルを選択（トークン効率化）

---

## ディレクトリ構造（新規）

1プロジェクト1テーマのため、`<theme_id>` フォルダは不要。`sources/` 直下にファイルを置く：

```
<プロジェクトフォルダ>/
└── sources/
    ├── _index.md        # ソース一覧 + 各600文字以内サマリー（常に読む）
    ├── nasa-source.md   # ソース原文テキスト（必要時のみ読む）
    ├── arxiv-1234.md
    └── ...
```

- `project` 引数・`theme_id` ともに不要
- スキルは `sources/` フォルダを実行コンテキストのフォルダ内に自動作成
- テーマ情報は `_index.md` の冒頭に記録

---

## `_index.md` フォーマット

```markdown
# Sources: <テーマ名>
Created: YYYY-MM-DD

## ソース一覧

### 1. <タイトル>
- File: <ファイル名>.md
- URL: <元URL>
- 取得日: YYYY-MM-DD
- 信頼性: 公的機関 / 査読論文 / 科学メディア
- 概要: 600文字以内のサマリー（どんな主張・データが含まれるか）
```

---

## 作成・変更ファイル一覧

| ファイル | 作業 |
|---|---|
| `scripts/fetch_source.sh` | 新規作成（URL→テキスト変換） |
| `.claude/skills/research_setup-sources/SKILL.md` | NotebookLM → ローカルファイル方式に書き換え |
| `.claude/skills/check-fact-lim/SKILL.md` | ローカルソースモードを追加（後方互換あり） |

---

## 各コンポーネントの詳細

### scripts/fetch_source.sh（新規）

```bash
#!/bin/bash
# 使い方: ./fetch_source.sh <URL> <output.md>
# 機能: URL からテキストを取得し、メタデータヘッダー付きで保存
```

- `curl` でHTMLを取得 → `sed`/`python3` でタグ除去してテキスト化
- PDFは `pdftotext` を試行（なければスキップ）
- 出力ファイル冒頭に `<!-- URL: ... DATE: ... -->` メタデータを付与

### research_setup-sources の変更

**現在**: NotebookLM ノートブック作成 → `notebook_id` 返却

**変更後**:
1. `$ARGUMENTS` をテーマとして受け取る（例: `ブラックホールの蒸発`）
2. 実行フォルダ配下に `sources/` ディレクトリを作成（`mkdir -p`、既存なら追記モード）
3. 既存の `deep-research` スキルと同様に WebSearch + WebFetch でソース収集
4. 各ソースを `fetch_source.sh` でテキスト化して保存
5. `_index.md` を生成/更新（タイトル・URL・信頼性・600文字以内サマリー）
6. 完了報告: 収集したソース数と `sources/` のパスを表示

**検索条件（現行維持）**:
- 優先: 査読論文・大学/研究機関・科学メディア・政府機関
- 除外: 企業製品サイト・まとめサイト

### check-fact-lim の変更

**現在**: `notebook_id` を受け取り `notebooklm_manager.py ask` で問い合わせ

**変更後（分岐あり）**:

- 第1引数が `notebook_id`（25〜44文字）→ **従来通り** `notebooklm_manager.py ask` で問い合わせ
- 第1引数なし or 引数がテキスト → **ローカルソースモード**:
  1. `sources/_index.md` を Read
  2. チェック対象テキストの主張と関連しそうなソースファイルを _index のサマリーから選択
  3. 選択したファイルを Read
  4. Claude が「そのソースの範囲内で」完全性チェック・ファクトチェックを実施
- ループ構造・スコア判定・Drive モード対応は現行維持

---

## 実装順序

1. `sources/` フォルダはスキル実行時に自動作成（事前作成不要）
2. `scripts/fetch_source.sh` 作成（よーんに確認してから実行）
3. `research_setup-sources/SKILL.md` 書き換え
4. `check-fact-lim/SKILL.md` 書き換え
5. 動作検証

---

## 検証手順

1. `/research_setup-sources ブラックホールの蒸発` を実行
   - `sources/` が作成されること
   - `_index.md` に複数ソースが記録されること
2. `/check-fact-lim <テストテキスト>` を実行
   - `_index.md` を読み、ソースを参照してファクトチェックすること
   - 「ソースに記載なし」の返答ができること
3. PDF ソースの取り込みテスト（arXiv など）
