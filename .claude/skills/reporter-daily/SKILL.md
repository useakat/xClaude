---
name: reporter-daily
description: X・note・threads 運用の日報を作成し、docs/reports/daily/ に保存する。スプレッドシートから前日の数値を取得し、投稿実績をもとに特記事項をAI生成する。
tools: Bash, Read, Write, Edit, Glob, Grep
---

あなたは X・note・threads 運用の日報を自律的に作成するエージェントです。
**以下の STEP を順番に、自動的に実行してください。ユーザー入力を待たない。**

**シートの読み取りはすべて `scripts/sheets_values.py`（Bash 経由・サービスアカウント認証）で行う。mcp-gsheets の MCP ツールは使わない**（リモート環境では MCP ツールの許可プロンプトを抱止できず routine が停止するため）。スクリプトは repo ルートからの相対パスで呼ぶ：

```bash
python3 scripts/sheets_values.py get <spreadsheetId> "<range>"
```

出力は `{"range", "rowCount", "values"}` の JSON。

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

```bash
python3 scripts/sheets_values.py get "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c" "日次記録!A:A"
```

返却された `rowCount` を `N` とする（ヘッダー行を含む）。
最新10行の開始行: `start = max(2, N - 9)`（1-indexed）

**2-2. ヘッダー＋最新10行を取得する**

```bash
python3 scripts/sheets_values.py get "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c" "日次記録!A1:AB1"
```

```bash
python3 scripts/sheets_values.py get "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c" "日次記録!A{start}:AB{N}"
```

取得した2つの結果を結合し（ヘッダー行 + データ行）、A列（日付）が `DATE_SHEET` に一致する行を探す。見つかったら以下の列を取得する：
- `ポスト数` → `posts`
- `引用数` → `quotes`
- `セルフリプ数` + `リプ数（他人）` の合計 → `replies`

このシートの数値は **X の実績のみ**（threads は含まない）。threads の件数は STEP 5 で別に数える。

行が見つからない場合は `posts`・`quotes`・`replies` を空として続行する。

---

# STEP 3: outputs シートから対象日の投稿記録を取得

```bash
python3 scripts/sheets_values.py get "1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc" "outputs!A:H"
```

A列（日時）が `DATE_SHEET` で始まる行を全て抽出し `outputs_today` として記憶する（B=URL・C=what_id・F=note_url・H=x_url を保持）。
`outputs` 全体（絞り込み前の全行）も `outputs_all` として保持しておく（STEP 5 のURL照合で使う。行数が多い場合は B列・C列・H列だけ保持すればよい）。

`outputs`に媒体（X/threads/note）の列は無い。媒体はURL列（B列）から判別する：`threads.com`を含む→threads、`note.com`を含む→note、それ以外（`twitter.com`/`x.com`）→X。

## what_id → 種類ラベル対応表

| what_id | ラベル |
|---|---|
| W001 | 長文ストーリー |
| W003 | ワンポイント解説 |
| W006 | 質問回答 |
| z01 | 短文 |
| W002 | note記事 |
| 上記以外・該当なし | その他 |

**W001（長文ストーリー）の note 販促用判定**: outputs のその行の `note_url`（F列）に URL が入っていれば **note 販促用の投稿**。ラベルを `長文ストーリー（note販促用、[要約]）` の形にする（要約の直前に `note販促用、` を置く）。`note_url` が空なら通常どおり `長文ストーリー（[要約]）`。
この判定は X・threads の両方に適用する（threads は STEP 5 で解決した X 投稿の outputs 行の `note_url` を見る）。

---

# STEP 4: X投稿一覧シートから対象日の投稿を取得・分類

投稿一覧シートを取得する：

```bash
python3 scripts/sheets_values.py get "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c" "X投稿一覧!A:P"
```

取得した全行を `x_posts_all` として保持する（URL・本文だけでよい。STEP 5 のフォールバック照合で使う）。
そのうち A列（日時）が `DATE_SHEET` で始まる行を全て抽出する。各行について以下を取得する：
- `ポスト種類`・`ポスト本文`（先頭80字）・`インプレッション`・`いいね`・`リポスト`・`ブックマーク`・`リプライ`

**`ポスト種類` が `リプライ` の行は内訳から除外する。** セルフリプ・note 記事へのリンク誘導リプライはオリジナルポストではなく、STEP 2 の `リプライ数` に計上済みのため、内訳には載せない。

各行のポストURLを `outputs_today` のURL列と突合し、一致すればその what_id を種類ラベル対応表でラベルに変換する。一致しなければラベルは「その他」。

インプレッションが最も大きい投稿を `x_top` として記憶する（STEP 8 で「一言」を書くかどうかの参考情報として使う）。

抽出・分類した投稿一覧を `x_posts_today` として記憶する。

---

# STEP 5: Threads投稿一覧シートから対象日の投稿を取得・分類

```bash
python3 scripts/sheets_values.py get "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c" "Threads投稿一覧!A:S"
```

A列（投稿日時）が `DATE_SHEET` で始まる行を全て抽出する。各行について以下を取得する：
- `本文`・`views`・`いいね`・`リプライ`・`リポスト`・`引用`

各行を以下の優先順位でカテゴリ判定する：

1. `outputs_today` の中で、投稿URL（B列）が一致する行を探し、その `x_url`（H列）を取得する。
2. `x_url` が入っていれば、`outputs_all` の中でURLが `x_url` と一致する行を探し、その what_id を種類ラベル対応表でラベルに変換する。
3. `x_url` が空、または一致する行が無い場合のフォールバック：`x_posts_all`（STEP 4。**対象日に限らずシート全体**）の中で本文が完全一致（または大部分一致）する投稿を探し、そのURLで `outputs_all` を検索して what_id を取得 → ラベルに変換する（Threads投稿は元のX投稿と同日に投稿されているとは限らないため、日付を絞らずシート全体から探す）。
4. 1〜3のいずれでも判定できなければラベルは「その他」。

views が最も大きい投稿を `threads_top` として記憶する（STEP 8 で「一言」を書くかどうかの参考情報として使う）。

抽出・分類した投稿一覧を `threads_posts_today` として記憶する（0件なら空のまま）。
その件数を `threads_posts` として記憶する（日次記録シートは X 専用のため、threads のオリジナルポスト数はこの件数を使う）。

---

# STEP 6: note記事公開の確認

`outputs_today` の中で what_id が `W002` の行を探す。

見つかった場合：

**6-1. note投稿一覧からタイトルを取得**

```bash
python3 scripts/sheets_values.py get "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c" "note投稿一覧!B:C"
```

note_url（outputs の F列）と一致する行のタイトル（C列）を取得する。

**6-2. note購入記録から対象日の売上を集計**

```bash
python3 scripts/sheets_values.py get "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c" "note購入記録!A:F"
```

A列（購入日）が `DATE_SHEET` と一致する行を抽出し、E列（記事タイトル）でグルーピング。件数と、F列（価格）の値（タイムセール等で複数価格が混在する場合はその内訳）を記憶する。
**当日の購入が0件でも「販売数：0」として必ず記録する**（購入記録に行が無い＝販売0件であって、記事公開の項目を省略する理由にはしない）。

**6-3. 定価の取得（購入0件で価格が分からない場合）**

購入記録から価格が取れないときは、記事の制作フォルダ `projects/w002/<記事フォルダ>/thumbnail/design-brief.md` の「媒体」行に書かれた価格（例: `有料記事サムネイル・980円`）を使う。
そこにも無い、または複数の価格が食い違う場合は `[価格未確認]` と書いて日報を保存し、**完了報告でよーんに確認を依頼する**（推測で断定しない）。

`note_publish_today` として、タイトル・当日の購入件数・価格情報をまとめて記憶する（W002の投稿が無ければ空のまま）。

---

# STEP 7: 変更ログから対象日の開発作業を取得

**7-1. 変更ログのエントリを抽出する**

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

**7-2. 報告書を読み込む**

`changelog_entries` が「（変更なし）」でなければ、エントリ内の `[→報告書](../reports/...)` リンクを全て抽出し、対応する報告書ファイルを Read ツールで読み込む。

- リンクのパスは `docs/changelog.md` からの相対パスなので、実ファイルは `docs/reports/XXXXX.md`（または `docs/reports/XXXXX/index.md`）
- 各報告書の「背景・動機」「実施内容」「確認結果」セクションを把握する
- 読み込んだ内容を `report_details` として記憶する（報告書が無い場合は空）

---

# STEP 8: 特記事項の生成

まず `style/style-reporter.md` を Read ツールで読み込み、そのルールに従って④特記事項を生成する。

## 構成

**媒体別の4セクション構成**。以下の順番で並べる：

1. **note** — 記事執筆の進捗、note 記事公開があればその項目
2. **X** — 引用・リプライ数・オリジナルポスト数と、その内訳
3. **threads** — オリジナルポスト数と、その内訳
4. **特記事項** — 変更ログまとめ・投稿以外の活動

- **note・X・threads の見出しは投稿0件の日でも必ず出す**（数値は `0` と書く）
- **特記事項だけは、書く内容が無ければ見出しごと省略する**
- 見出しは `**太字**`、項目の箇条書き記号は「・」（style-reporter.md のルールと同じ）

## 表記ルール（Wiki 描画の制約・必ず守る）

- **投稿の内訳（入れ子）のインデントは全角スペース2個（`　　`／U+3000）を使う。** 半角スペース4個は Markdown がコードブロックと解釈して描画が崩れるため使わない
- **すべての箇条書きの間に空行を１行入れる。** 空行が無いと Wiki で改行が無視され、全項目が1行に連結される

## note セクション

**項目の順序は「記事公開 → 記事執筆中」**（公開という実績を先に置き、進行中の作業を後に置く）。

- `note_publish_today` があれば、**1行目**に記事公開を書く：

```
・記事公開：[記事内容の要約]の[価格]円有料記事。販売数：[当日の購入件数]。
```

- **販売数は 0 件でも必ず `販売数：0。` と書く**（省略しない）
- タイムセール等で価格が複数混在した日は、販売数のあとに内訳を1文添える
  - 例: `・記事公開：Xストーリー投稿の深堀りの980円有料記事。販売数：4。すべてタイムセール中（490円）。`
- 例（当日の販売なし）: `・記事公開：ケプラー望遠鏡の復活劇の980円有料記事。販売数：0。`

- 続けて `・記事執筆中` を書く（進捗の詳細は、よーんが後から括弧書きで追記する運用。**スキル側で推測して書かない**。よーんが書いていない日はこの行を削除して最終版にする）

## X セクション

以下の3項目をこの順で書く（数値は STEP 2 の日次記録シートの値）：

```
・引用：[quotes]

・リプライ数：[replies]

・オリジナルポスト数：[posts]
```

`x_posts_today` が1件以上あれば、`オリジナルポスト数` の下に内訳を全件、全角スペース2個の入れ子で列挙する（**リプライは STEP 4 で除外済み**）。
`posts` の件数と `x_posts_today` の件数が食い違う場合は、**件数表示は日次記録シートの値を正とし、内訳は投稿一覧の全件（リプライ除外後）を出す**。

## threads セクション

```
・オリジナルポスト数：[threads_posts]
```

`threads_posts_today` が1件以上あれば、その下に内訳を全件、全角スペース2個の入れ子で列挙する。
threads は引用・リプライ数の行を出さない。

## 投稿の内訳の項目フォーマット（X・threads 共通）

```
　　・[ラベル]（[投稿内容を10字程度で要約]）：[数値]。[一言]
```

- X投稿の数値: `インプXXX・いいねXXX・リポストXXX・ブクマXXX・リプXXX`（style-reporter.md の順序）
- threads投稿の数値: `viewsXXX・いいねXXX・リポストXXX・引用XXX・リプXXX`
- 一言は特に記載すべき内容（反応の大きさなど）があれば書く。無理に毎回付けなくてよい
- ラベルが「その他」の投稿にも同じフォーマットを使う（例: `　　・その他（はやぶさ230が撮影した小惑星トリフネの画像）：インプ816・いいね60・リポスト10・ブクマ4・リプ0。`）
- **W001 で outputs の `note_url` に URL が入っている投稿は「note販促用」を明示する**（STEP 3 の判定を参照）
  - 例: `　　・長文ストーリー（note販促用、ケプラー望遠鏡の復活劇）：インプ744・いいね44・リポスト6・ブクマ3・リプ1。`
- **リプライ（セルフリプ・note へのリンク誘導リプライ）は内訳に載せない**（STEP 4 で除外済み。件数は `リプライ数` の行が担う）

## 特記事項セクション

- 変更ログまとめ（`changelog_entries` がある場合）
- 投稿以外の活動（1活動1項目）
- 投稿の数値は各媒体セクションに書くので、ここには入れない

## データ条件ルール（SKILL 固有）

- 特にインプレッション／viewsが高かった投稿（目安：5,000以上）は一言を詳しく書く
- note執筆・ツール設定・セミナー参加など、投稿以外の活動も推論して記載する
- `changelog_entries` が「（変更なし）」でなければ、`report_details`（報告書の詳細）も参照したうえで、X・note・threads運用の観点から「この変更によって運用がどう変わるか・どんな恩恵があるか」を1〜2行にまとめて特記事項セクションに含める（何を実装したかは書かない）
- フォロワー数の増減には触れない
- 投稿が1件も無かった日も **note・X・threads の見出しは出し、数値は `0` と書く**（内訳の入れ子は無し）。注力した活動があれば特記事項セクションに書く

## 保存前チェック（媒体セクション・必ず実施）

STEP 9 で保存する前に、以下を1項目ずつ確認する。１つでも引っかかったら直す。

1. **note の順序**: `記事公開` が `記事執筆中` より**上**にあるか
2. **販売数**: 記事公開の行に `販売数：N。` があるか（0件でも省略していないか）
3. **note販促用**: outputs の `note_url` に URL が入っている W001 の内訳に `note販促用、` が入っているか（X・threads とも）
4. **リプライ除外**: オリジナルポストの内訳に、セルフリプ・リンク誘導リプライが混じっていないか

## 自己チェック（保存前に必ず実施）

生成した特記事項を STEP 9 で保存する前に、以下を1項目ずつ声に出して確認する。１つでも引っかかったら書き直す。

1. **専門用語チェック**: `git push` / `MCP` / `プロキシ` / `403` / `hook` / `フック` / `commit` / `master` / `branch` / `API` / `ID` / `what_id` のような、システムを知らない人に伝わらない語が混じっていないか。混じっていたら一般語に言い換える
2. **「何を」ではなく「どう変わるか」チェック**: 文中に「〜を実装した」「〜を変更した」「〜に移行した」「〜を追加した」のような実装行為の動詞が主役になっていないか。主役は「これまで困っていたこと」と「これから楽になること」になっているか
3. **読者想定チェック**: この文だけを「システムを知らない友人」に読ませて、何が良くなったか伝わるか。伝わらなければ書き直す

---

# STEP 9: ファイル保存

以下のパスに日報ファイルを保存する：
`[REPO_ROOT]/docs/reports/daily/[DATE_ISO].md`

## ファイルフォーマット

```markdown
---
title: 日報 [DATE_JP]
---

## 【日報　[DATE_JP]】

**note**

・[note 記事公開があればその項目（販売数まで書く）]

・記事執筆中

**X**

・引用：[quotes]

・リプライ数：[replies]

・オリジナルポスト数：[posts]

　　・[X投稿の内訳1]

　　・[X投稿の内訳2]

**threads**

・オリジナルポスト数：[threads_posts]

　　・[threads投稿の内訳1]

　　・[threads投稿の内訳2]

**特記事項**

・[変更ログまとめ・投稿以外の活動（各項目）]
```

**重要**:
- 各項目・各箇条書きの間には必ず空行を１行入れること。空行が無いと Wiki で改行が無視され、全項目が1行に連結される
- 内訳の入れ子は**全角スペース2個**（`　　`／U+3000）でインデントする。半角スペース4個は Markdown がコードブロックと解釈するため使わない
- **note・X・threads の見出しは0件の日でも省略しない**（数値は `0` と書く）。**特記事項**だけは書く内容が無ければ見出しごと省略する

REPO_ROOT は以下で取得する：
```bash
git -C /root/xClaude rev-parse --show-toplevel
```

---

# STEP 9.5: 日報の全文表示（必須・省略禁止）

保存したファイル（`docs/reports/daily/[DATE_ISO].md`）を Read ツールで読み込み、**内容を省略せずそのままチャットに表示する**。

- このステップを飛ばして STEP 10 以降に進むことは禁止
- commit 前に表示することで、push される内容の最終確認を兼ねる

---

# STEP 10: インデックス更新

日報インデックスはカレンダーコンポーネントが自動でファイルを検出・表示するため、更新不要。このステップをスキップして STEP 11 へ進む。

---

# STEP 11: Git コミット & GitHub MCP プッシュ

**11-1. ローカルコミット**

```bash
bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh \
  "report(daily): [DATE_JP]の日報を追加" \
  docs/reports/daily/[DATE_ISO].md
```

- **対象パスを必ず渡す。** 省略すると `git add -A` にフォールバックし、他セッションの未コミット作業を巻き込む（2026-08-14 に `/record` で実際に発生）。

**11-2. GitHub MCP で master にプッシュ**

`git diff HEAD~1 --name-only` で変更ファイル一覧を取得し、各ファイルを Read ツールで読み込む。その後 `mcp__github__push_files` ツールで master に直接プッシュする：

- owner: `useakat`
- repo: `xClaude`
- branch: `master`
- files: 変更ファイルの path と content のリスト
- message: `report(daily): [DATE_JP]の日報を追加`

---

# 完了報告

日報の全文は STEP 9.5 で表示済みのはず。**もし STEP 9.5 を飛ばしていた場合は、ここで必ず全文を表示してから**、以下のサマリーを表示する。

```
✅ 日報作成完了: [DATE_JP]
   X: オリジナルポスト数 [posts] / 引用 [quotes] / リプライ [replies]
   threads: オリジナルポスト数 [threads_posts]
   保存先: docs/reports/daily/[DATE_ISO].md
```
