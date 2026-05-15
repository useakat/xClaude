---
title: reporter-daily
description: X・note 運用の日報を作成し、docs/reports/daily/ に保存する。スプレッドシートから前日の数値を取得し、投稿実績をもとに特記事項をAI生成する。
category: レポート生成
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

X・note 運用の日報を作成し、docs/reports/daily/ に保存する。スプレッドシートから前日の数値を取得し、投稿実績をもとに特記事項をAI生成する。

## 詳細内容

あなたは X・note 運用の日報を自律的に作成するエージェントです。
**以下の STEP を順番に、自動的に実行してください。ユーザー入力を待たない。**

---

# STEP 1: 対象日付の決定

引数があればその日付を使用する。なければ**前日**を使用する。

```bash
python3 -c "
from datetime import datetime, timedelta, timezone
import sys
JST = timezone(timedelta(hours=9))
args = sys.argv[1:]
if args:
    d = datetime.strptime(args[0], '%Y-%m-%d').date()
else:
    d = datetime.now(JST).date() - timedelta(days=1)
print(d.strftime('%Y-%m-%d'))
print(d.strftime('%Y/%m/%d'))
print(d.strftime('%-m月%-d日'))
" -- "$1"
```

出力された3行を以下の変数として記憶する：
- `DATE_ISO`: YYYY-MM-DD 形式（ファイル名用）
- `DATE_SHEET`: YYYY/MM/DD 形式（スプレッドシート検索用）
- `DATE_JP`: M月D日 形式（日報タイトル用）

---

# STEP 2: 日次記録シートから対象日データ取得

**2-1. 最終行番号を取得する**

```
sheets_get_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="日次記録!A:A"
)
```

返却された配列の長さを `N` とする（ヘッダー行を含む）。
最新10行の開始行: `start = max(2, N - 9)`（1-indexed）

**2-2. ヘッダー＋最新10行を取得する**

```
sheets_get_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="日次記録!A1:AB1"
)
```

```
sheets_get_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="日次記録!A{start}:AB{N}"
)
```

取得した2つの結果を結合し（ヘッダー行 + データ行）、A列（日付）が `DATE_SHEET` に一致する行を探す。見つかったら以下の列を取得する：
- `ポスト数` → `posts`
- `引用数` → `quotes`
- `セルフリプ数` + `リプ数（他人）` の合計 → `replies`

行が見つからない場合は `posts`・`quotes`・`replies` を空として続行する。

---

# STEP 3: 投稿一覧シートから対象日の投稿を取得

`sheets_get_values` MCP ツールで投稿一覧シートを取得する：

```
sheets_get_values(
  spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c",
  range="自分の投稿一覧!A:P"
)
```

返却された行から A列（日時）が `DATE_SHEET` で始まる行を全て抽出する。各行について以下を取得する：
- `ツイート種類`・`ツイート本文`（先頭80字）・`インプレッション`・`いいね`・`リツイート`・`ブックマーク`

抽出した投稿一覧を記憶する。

---

# STEP 4: 変更ログから対象日の開発作業を取得

**4-1. 変更ログのエントリを抽出する**

```bash
python3 -c "
import re, sys
date_iso = sys.argv[1]
with open('docs/changelog.md') as f:
    content = f.read()
m = re.search(r'## ' + re.escape(date_iso) + r'\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
if m:
    entries = m.group(1).strip()
    print(entries if entries else '(変更なし)')
else:
    print('(変更なし)')
" -- "DATE_ISO"
```

取得した内容を `changelog_entries` として記憶する。

**4-2. 報告書を読み込む**

`changelog_entries` が「(変更なし)」でなければ、エントリ内の `[→報告書](../reports/...)` リンクを全て抽出し、対応する報告書ファイルを Read ツールで読み込む。

- リンクのパスは `docs/changelog.md` からの相対パスなので、実ファイルは `docs/reports/XXXXX.md`（または `docs/reports/XXXXX/index.md`）
- 各報告書の「背景・動機」「実施内容」「確認結果」セクションを把握する
- 読み込んだ内容を `report_details` として記憶する（報告書がない場合は空）

---

# STEP 5: 特記事項の生成

まず `style/style-reporter.md` を Read ツールで読み込み、そのルールに従って④特記事項を生成する。

## データ条件ルール（SKILL 固有）

- 特にインプレッションが高かった投稿（目安：5,000以上）は詳しく触れる
- note執筆・ツール設定・セミナー参加など、投稿以外の活動も推論して記載する
- `changelog_entries` が「(変更なし)」でなければ、`report_details`（報告書の詳細）も参照したうえで、X・note運用の観点から「この変更によって運用がどう変わるか・どんな恩恵があるか」を1〜2行にまとめて含める（何を実装したかは書かない）
- フォロワー数の増減には触れない
- 投稿がなかった日は「0投稿。〇〇に注力した日。」と記載する

## 自己チェック（保存前に必ず実施）

生成した特記事項を STEP 6 で保存する前に、以下を1項目ずつ声に出して確認する。1つでも引っかかったら書き直す。

1. **専門用語チェック**: `git push` / `MCP` / `プロキシ` / `403` / `hook` / `フック` / `commit` / `master` / `branch` / `API` / `ID` のような、システムを知らない人に伝わらない語が混じっていないか。混じっていたら一般語に言い換える
2. **「何を」ではなく「どう変わるか」チェック**: 文中に「〜を実装した」「〜を変更した」「〜に移行した」「〜を追加した」のような実装行為の動詞が主役になっていないか。主役は「これまで困っていたこと」と「これから楽になること」になっているか
3. **読者想定チェック**: この文だけを「システムを知らない友人」に読ませて、何が良くなったか伝わるか。伝わらなければ書き直す

---

# STEP 6: ファイル保存

以下のパスに日報ファイルを保存する：
`[REPO_ROOT]/docs/reports/daily/[DATE_ISO].md`

## ファイルフォーマット

```markdown
---
title: 日報 [DATE_JP]
---

## 【日報　[DATE_JP]】

① オリジナルポスト数：[posts]

② 引用：[quotes]

③ リプライ数：[replies]

④ 特記事項：

・[AI生成した特記事項1]

・[AI生成した特記事項2]
```

**重要**: 各項目・各箇条書きの間には必ず空行を1行入れること。空行がないと Wiki で改行が無視される。

REPO_ROOT は以下で取得する：
```bash
git -C /root/xClaude rev-parse --show-toplevel
```

---

# STEP 7: インデックス更新

日報インデックスはカレンダーコンポーネントが自動でファイルを検出・表示するため、更新不要。このステップをスキップして STEP 8 へ進む。

---

# STEP 8: Git コミット & GitHub MCP プッシュ

**8-1. ローカルコミット**

```bash
bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh \
  "report(daily): [DATE_JP]の日報を追加"
```

**8-2. GitHub MCP で master にプッシュ**

`git diff HEAD~1 --name-only` で変更ファイル一覧を取得し、各ファイルを Read ツールで読み込む。その後 `mcp__github__push_files` ツールで master に直接プッシュする：

- owner: `useakat`
- repo: `xClaude`
- branch: `master`
- files: 変更ファイルの path と content のリスト
- message: `report(daily): [DATE_JP]の日報を追加`

---

# 完了報告

```
✅ 日報作成完了: [DATE_JP]
   ポスト数: [posts] / 引用: [quotes] / リプライ: [replies]
   保存先: docs/reports/daily/[DATE_ISO].md
```

保存したファイルを Read ツールで読み込み、内容をそのまま表示する。
