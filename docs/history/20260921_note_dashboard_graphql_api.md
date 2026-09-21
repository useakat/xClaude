---
title: note 新ダッシュボードの GraphQL API からインプレッション・記事別売上・流入元を取得 — セッション履歴
date: 2026-09-21
sidebar:
  hidden: true
---

# セッション履歴

> 2026-09-21 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260921_note_dashboard_graphql_api/)

---

## よーん *(12:05 JST)*

note のダッシュボードが変更されていて、記事ごとの、インプレッション・ページビュー・スキ・コメント・売上が表示されるように成っている。また、流入元（google, X, note.com など、アクセス元のドメイン）の日毎の合計も表示されている。note API でもこれらの情報が取得できるのかしらべて

### Claude *(12:05 JST)*

*[ツール: `Bash`, `Bash`, `Read`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

調べました。**結論：全部取れます。** ただし従来の REST API（`/api/v1/stats/pv`）ではなく、note が新しく作った **GraphQL API** を使う必要があります。

## 新ダッシュボードの正体

`https://note.com/dashboard` は Next.js + Apollo の別アプリで、データ取得先は **`https://graphql.note.com/graphql`** です。JS チャンクを解析してクエリを抽出し、実際に叩いて実データが返ることを確認しました。

## 認証（2段構え）

```
1. POST https://note.com/api/v3/graphql/auth
   Cookie: _note_session_v5=<既存の NOTE_SESSION>
   → Set-Cookie: note_gql_auth_token=<JWT>（有効期限 30分）

2. POST https://graphql.note.com/graphql
   Authorization: Bearer <JWT>
```
Cookie だけを graphql ドメインに送っても `NotLoggedInViewer` になります。**Authorization ヘッダが必須**でした。

## 取れるデータ（実測値つき）

### ① 記事ごとの5指標 — `dashboardNoteListConnection`
```graphql
dashboardNoteListConnection(unit, date, endDate, order, first, after) {
  pageInfo { hasNextPage endCursor }
  edges { node {
    note { title status publishedAt link { absoluteUrl } }
    metrics { pageViewCount impressionCount likeCount commentCount salesAmount }
  }}}
```
全33記事をページネーションで取得済み。例：ボイジャー記事 = PV 1071 / IMP 762 / スキ 20 / 売上 2940円。**売上が記事単位で取れる**のが従来 API との最大の差です。

- `order`: `PUBLISHED_DATE_DESC` / `IMPRESSION_COUNT_DESC` / `PAGE_VIEW_COUNT_DESC` / `LIKE_COUNT_DESC` / `COMMENT_COUNT_DESC` / `SALES_DESC`
- `unit`: `DAY` / `WEEK` / `MONTH` / `YEAR` / `ALL` / `LAST_7_DAYS` / `LAST_28_DAYS` / `LAST_365_DAYS` / `CUSTOM`（`CUSTOM` + date/endDate で任意期間・1日単位も可）

### ② 流入元の日別内訳 — `dashboardNoteReferrersChart`
```graphql
dashboardNoteReferrersChart(unit, date, endDate) {
  legend { name count color }                      # 期間合計
  timeSeriesBarChart { labels data { label data } } # 日別
}
```
直近7日の実データ：Google 138 / no referrer 29 / note.com 18 / search.yahoo.co.jp 8 / X 4 …、日別も `["9/14","9/15",…]` × ドメインごとの配列で返ります。**ダッシュボードの積み上げ棒グラフそのもの**です。

### ③ その他
- `dashboardSummary(unit, date, endDate)` — 期間合計の5指標
- `dashboardMetricChart(unit, date, endDate, metric)` — 指標1つの日別推移（`metric`: `IMPRESSION`/`PAGE_VIEW`/`LIKE`/`COMMENT`/`SALES`）、`granularity` と `startDate`/`endDate` つき
- `dashboardMembershipPlanListConnection` / `dashboardMagazineListConnection` — メンバーシップ・マガジン別
- `dashboardStatLastUpdatedTimes` — 集計の最終更新時刻（現在 02:51 JST 更新）
- イントロスペクションが**開いている**ので、スキーマ全体を後から確認できます

## 制約

- 流入元は**アカウント全体のみ**。記事ごとの流入元内訳を返すフィールドはスキーマに存在しません。
- `impressionCount` は機能提供前の期間だと `null`（コード内コメントで明記、UI では「-」表示）。
- JWT は 30分で失効するので、長いバッチでは再取得が要ります。
- 非公開 API なので予告なく変わる可能性があります。

## 既存実装との関係

`scripts/fetch_note_stats.py` は旧 REST（`/api/v1/stats/pv`）で PV・スキ・コメントのみ。GraphQL に載せ替えれば**インプレッションと記事別売上が追加**で取れ、`fetch_body_length` の記事ごとの追加リクエストも不要になります（タイトル・URL・公開日が同じレスポンスに入るため）。`record-note-posts` の「note投稿一覧」シートも列追加で対応できます。

スクリプト化しますか？（`fetch_note_stats.py` の GraphQL 版への書き換え＋流入元取得の新規スクリプト、という構成を想定しています）

---

## よーん *(23:41 JST)*

スクリプト化して

### Claude *(23:42 JST)*

*[ツール: `Bash`, `Read`, `Bash`]*

スクリプト化します。まず既存の `fetch_note_stats.py` との数値差を確認したので、その扱いも含めて設計しました。

**重要な発見**：REST の `read_count` と GraphQL の `pageViewCount` は**一致しません**（33記事中31件で REST の方が大きい。例：ボイジャー 1096 vs 1072、最近の短記事はきれいに +20 差）。新ダッシュボード側は自己閲覧などを除外している可能性が高いです。シートの既存「ビュー」列との連続性が切れるので、**両方を出力**して後から選べるようにします。

共通の認証ヘルパーを作ります。

*[ツール: `Write`, `Write`, `Write`]*

動作確認します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Read`, `Edit`]*

スクリプト化しました。3ファイルです。

## `scripts/note_gql.py`（新規・共通基盤）

GraphQL クライアント。認証の2段構えと JWT の 30分失効を隠蔽します。

- `NoteGraphQL.query()` — トークンを自動取得し、25分経過で再取得。`Unauthenticated` エラー時は取り直して1回だけ自動リトライ（フロントの errorLink と同じ挙動）
- `NoteGraphQL.paginate()` — Relay Connection を最後まで自動で辿る
- `period_vars("28d")` — `all` / `7d` / `28d` / `365d` / `YYYY-MM-DD` / `YYYY-MM-DD:YYYY-MM-DD` を `unit`/`date`/`endDate` に変換
- CLI としても使えます（スキーマ調査用）:
  ```bash
  python3 scripts/note_gql.py --viewer                      # ログイン確認
  python3 scripts/note_gql.py --introspect DashboardMetricKind
  python3 scripts/note_gql.py -q 'query{...}' --vars '{...}'
  ```

## `scripts/fetch_note_stats.py`（改修）

既存の REST 取得はそのままに、GraphQL のメトリクスを URL キーで突き合わせて合流させました。**出力キーは追加のみ**なので `record-note-posts` スキルは無修正で動きます。

| キー | 出典 | 内容 |
|---|---|---|
| `view` / `like` / `likeRate` | REST | 従来どおりの累計（シートの H・I・J 列） |
| `impression` / `pv` / `comment` / `sales` | GraphQL | `--period` で指定した期間の値 |

```bash
python3 scripts/fetch_note_stats.py --all                       # 累計
python3 scripts/fetch_note_stats.py --all --period 28d          # 直近28日
python3 scripts/fetch_note_stats.py --all --period 2026-09-01:2026-09-30
python3 scripts/fetch_note_stats.py --all --no-charcount        # 記事ごとの本文取得を省略（高速）
python3 scripts/fetch_note_stats.py --no-gql                    # 従来どおりの挙動に戻す
```
GraphQL 側が落ちても stderr に WARN を出して REST 分だけ返すようにしてあります。

## `scripts/fetch_note_referrers.py`（新規）

```bash
python3 scripts/fetch_note_referrers.py --period 7d --csv
# date,label,referrer,count
# 2026-09-14,9/14,Google,21
# 2026-09-14,9/14,no referrer,6
python3 scripts/fetch_note_referrers.py --period all --csv --total
# X 4398 / Google 2376 / note.com 1723 / no referrer 1597 …
```
JSON 出力なら期間合計（`total`）と日別内訳（`daily`）の両方を返します。`--period 365d` のように集計粒度が月になる期間ではラベルが日付に対応しないため、**日数とラベル数が一致するときだけ実日付を割り当て**、それ以外は `date: null` にしてラベルだけ残す作りにしました（`2025/9` のような月ラベルを誤って日付にしないため）。

## 検証結果

全期間・全28記事で取得できました。売上は5記事で計 **7,290円**（ボイジャー 2,940 / 空が赤かったら後編 1,960 / 冥王星 1,200 / 天王星 1,090 / ハッブル 100）。メトリクス欠落はゼロです。

`.claude/settings.json` の `permissions.allow` に新スクリプト2本を追記しました（routine 用）。

## 気づいた点2つ

1. **REST と GraphQL の PV は一致しません**（ボイジャー 1096 vs 1072 など、33件中31件で REST が大きい）。シートの「ビュー」列は従来どおり `view`（REST）のままにしてあります。ダッシュボード表示と揃えたい場合は `pv` に切り替える判断が要ります。
2. **つぶやき4件が REST から漏れています**。`creators/contents?kind=note` が返すのは28件ですが、GraphQL は公開32件＋下書き1件を返します。差分は2025-08-31 のつぶやき（「自分のために書けばいい」など）で、記事ではないため実害はありません。

記事別の流入元内訳はスキーマに存在せず、流入元はアカウント全体のみです。

次にやるとしたら「note投稿一覧」シートへの列追加（インプレッション・コメント・売上）と流入元シートの新設ですが、列構成の変更はシートを触るので、進めてよければ言ってください。この変更を記録しますか？`/record` で記録できます。

---

## よーん *(08:58 JST)*

進めて

### Claude *(08:58 JST)*

シート側を進めます。まず現状を確認します。

*[ツール: `ToolSearch`, `Bash`, `mcp__mcp-gsheets__sheets_get_metadata`, `mcp__mcp-gsheets__sheets_get_values`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

流入元データは 2025-08-31 から日次で全部取れます（ドメインは11種類）。シート同期スクリプトを作ります。

*[ツール: `Write`, `Bash`, `Bash`, `mcp__mcp-gsheets__sheets_get_values`, `mcp__mcp-gsheets__sheets_get_values`, `Bash`]*

記事シートの列を追加します。

*[ツール: `mcp__mcp-gsheets__sheets_update_values`, `Bash`]*

スキルを更新します。

*[ツール: `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Bash`, `Bash`]*

シート整備まで完了しました。

## シート側の変更

**`note投稿一覧`（既存）に3列追加**
K「インプレッション」／L「コメント」／M「売上」。全28行をバックフィル済みで、売上は5記事・計 **7,290円** が入りました（ボイジャー 2,940 / 空が赤かったら後編 1,960 / 冥王星 1,200 / 天王星 1,090 / ハッブル 100）。URL 突き合わせで28行すべて一致、未一致ゼロです。

H列「ビュー」は従来どおり REST の累計値のままにしました。ダッシュボードの PV は記録していません（二重計上になるため）。スクリプトは `pv` も返すので、比較したくなったら参照できます。

**`note流入元`（新設）**
1行=1日の横持ちで、`日付 / 合計 / X / Google / note.com / 直接・不明 / Yahoo / Bing / その他`。**2025-08-31〜2026-09-21 の387日分**を全期間バックフィルしました。全期間の累計は X 4,398 / Google 2,379 / note.com 1,728 / 直接・不明 1,601 です。

日次の推移がそのままグラフにできる形にしてあります。ドメイン単位の生データが要るときは `fetch_note_referrers.py --csv` で全11ドメインぶん取れます。

## `scripts/sync_note_referrers.py`（新規）

```bash
python3 scripts/sync_note_referrers.py             # 直近7日を upsert
python3 scripts/sync_note_referrers.py --full      # 全期間を再構築
python3 scripts/sync_note_referrers.py --dry-run   # 書かずに確認
```
日付をキーに upsert するので**何度実行しても行が増えません**（再実行で updated=7 / appended=0 を確認済み）。note 側の集計は後から確定することがあるため、既定を「直近7日」にして取りこぼしを防いでいます。Sheets 認証は routine 用のサービスアカウント経路（`sheets_values.py`）に合わせました。

## `record-note-posts` スキルの更新

- STEP 4/5 の書き込み範囲を `H:J` → `H:M` に拡張
- **STEP 7「流入元シートを同期」を追加**（`--period 7d`）。ここが失敗しても STEP 1〜6 の結果は保持し、全体を失敗扱いにしない方針を明記
- 列構成表に「REST のビューとダッシュボードの PV は一致しない」注記を追加

毎朝3時の cron（`run_record_note_posts.sh`）がこのスキルを呼ぶので、明日から流入元も自動で溜まります。`.claude/settings.json` に新スクリプト3本の実行権限を追記しました（routine は対話できないため事前登録が必要）。

## 変更ファイル

```
M  .claude/settings.json
M  .claude/skills/record-note-posts/SKILL.md
M  scripts/fetch_note_stats.py
?? scripts/note_gql.py
?? scripts/fetch_note_referrers.py
?? scripts/sync_note_referrers.py
```

この内容で commit & push してよいですか？あわせて `/record` で報告書と変更ログも残せます。

---

## よーん *(09:14 JST)*

REST のビューとダッシュボードの PV は一致しない　のはなんでだっけ？

### Claude *(09:15 JST)*

推定で書いていたので、実データで確かめます。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

同じ期間で比べ直してみます。

*[ツール: `Bash`]*

裏取りしたら、前回書いた「自己閲覧の差」は根拠がありませんでした。実測はこうです。

## 同じ期間で比べるとほぼ一致する

| 期間 | REST | ダッシュボード | 差 |
|---|---|---|---|
| 直近7日（9/15-9/21） | 205 | 204 | 0.5% |
| 直近1ヶ月（8/22-9/21） | 1,070 | 1,065 | 0.5% |
| **累計（全期間）** | **11,702** | **10,775** | **7.9%（927）** |

ずれているのは**累計だけ**で、最近の期間はほぼ一致します。

## スキとコメントは完全一致

同じ全期間で スキ 403 vs 403、コメント 14 vs 14 と**ぴったり一致**しました。GraphQL 側も内部的に整合しています（ALL サマリー 10,775 = 月別チャートの合計 10,775）。

つまり「新ダッシュボードが古いデータを持っていない」という話ではありません。**PV という指標だけが別物**です。

## 原因はおそらく note 側の PV ログ基盤の切り替え

ダッシュボードのフロントエンドに、note 自身が書いたこのコメントが残っていました：

> `アクセス数(PV: page_views/pv 合成)。表示数(impression)は無い期間は null`

`page_views` と `pv` という**2つのテーブルを合成**して PV を出しています。ログ基盤を途中で切り替えて、新旧を繋いでいるのだと思われます。レガシーな累計カウンタ（REST の `read_count`）を完全には再現できておらず、古いデータほど差が出る、という説明が一番素直です。

記事ごとの差が総 PV に比例しないのもこれで説明がつきます。「0.999…＝1 の気持ち悪さ」148 vs 148 や「ターミナルから X に投稿」150 vs 150 は**完全一致**なのに、SOHO は 307 vs 244（63差）、つぶやき4本は揃って20差でした。一律のフィルタがかかっているなら、こういうばらつき方はしません。

ここから先（どの時点で切り替わったか、何が漏れているか）は外部からは分かりません。

## 運用上の意味

- **H列（累計ビュー）は REST のまま**で問題なし。記事間の相対比較は成立しています
- ただし**混ぜて比較しない**こと。「累計は REST、期間別はダッシュボード」と引き算すると、存在しない差が出ます
- これから積む日次データは両者ほぼ一致するので、今後の分析には影響しません

スキル内の注記が推測のままだったので、実測に差し替えておきます。

*[ツール: `Edit`]*

スキルの注記を実測ベースに差し替えました。

commit & push してよいか、先ほどの確認がまだ保留です。変更ファイルは以下のままです（今の編集で `SKILL.md` の注記が増えただけ）。

```
M  .claude/settings.json
M  .claude/skills/record-note-posts/SKILL.md
M  scripts/fetch_note_stats.py
?? scripts/note_gql.py
?? scripts/fetch_note_referrers.py
?? scripts/sync_note_referrers.py
```

---

## よーん *(09:22 JST)*

今後はPVで記録していくの？

### Claude *(09:23 JST)*

*[ツール: `Bash`, `Bash`]*

いまの実装では**していません**。H列は REST の `read_count` のままで、GraphQL から取っているのは K〜M列（インプレッション・コメント・売上）だけです。`pv` は取得はしていますがシートには書いていません。

ただ、**切り替えたほうがいいと思っています**。理由は3つです。

1. **REST は旧ダッシュボードの API** です。UI が置き換わった以上、いつ止まってもおかしくありません。止まった時点で H列だけ更新できなくなります
2. **よーんが画面で見る数字と揃う**。いまはレポートの数字とダッシュボードの表示が微妙に食い違います
3. **K〜M列は既に GraphQL なので、H列だけ別ソース**という状態が残ります

そして**継続性の問題は起きません**。GraphQL は 2025-08 の最初の記事から全履歴を持っているので、H列を28行まるごと入れ替えれば、過去も含めて一貫したデータになります。途中で段差ができる心配はありません（J列のスキ率も同時に再計算します）。

影響範囲は確認しました。`sync_x_note_analytics.py` と `monetization_metrics.py` が H列を列番号で読んでいるだけなので**コード修正は不要**です。ただし「Xnote導線記録」のビューと、マネタイズレポートの購入CVR の分母が、累計ベースで数%動きます（記事によって 0〜20%）。

デメリットは、過去のレポートに載せた数字と今後の数字が一致しなくなることです。

*[ツール: `AskUserQuestion`]*

切り替えます。まずスクリプトの出力を GraphQL 基準に変更します。

*[ツール: `Edit`, `Edit`, `Edit`, `Edit`, `Bash`]*

シートの H〜J列を再構築します。

*[ツール: `Bash`, `mcp__mcp-gsheets__sheets_get_values`, `Read`, `Edit`, `Edit`, `Bash`]*

PV に切り替えました。

## やったこと

**シート**：H〜J列（ビュー・スキ・スキ率）を全28行まるごと再構築しました。合計 **11,553 → 10,746**。これで H〜M列がすべて新ダッシュボード由来の単一ソースになり、過去も含めて一貫しています。

**`fetch_note_stats.py`**：`view` / `like` / `likeRate` の出所を GraphQL に変更しました。REST 値は `viewRest` / `likeRest` として残してあります（検証用。シートには入れません）。

フォールバックの挙動を明示的にしました。GraphQL が取れなかった場合だけ REST に退避しますが、そのとき stderr に警告を出します。

```
WARN: 28件でダッシュボードの数値が取れず、view/like を REST の累計に
フォールバックしました（出所が混ざります）: nf0ae94889f5a, ...
```

シートを空で上書きするよりマシなので退避はしますが、黙ってやると「混ぜるな」の原則を破ってしまうので、気づける形にしています。スキル側にも「WARN が出たらシートに書かず原因を先に潰す」と明記しました。

**スキル**：列構成表の出典を GraphQL に統一し、移行日と旧数値との断絶を注記に残しました（`2026-09-21 に H〜J列を移行、合計 11,553 → 10,746。過去のレポートの数値とは一致しない`）。

## 確認済み

- 通常実行で WARN なし
- `--no-gql` のフォールバック経路が正しく警告を出す
- シートの28行が再取得値と完全一致（不一致0件）
- `sync_x_note_analytics.py` / `monetization_metrics.py` は列番号で読むだけなのでコード修正不要

## 注意点

今後のレポートで、過去分と数字が変わります。特に「Xnote導線記録」のビューと購入CVR の分母が累計ベースで下がるので、月報・マネタイズレポートで前月比を見るときに一度だけ段差が出ます。

commit & push してよいですか？変更ファイルは前回と同じ6件です。

---

## よーん *(11:29 JST)*

commit & push

### Claude *(11:29 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

**master に push しました**（`578205d..6c2a737`）。

コミットしたのは今回の6ファイルだけです。作業ツリーに残っていた `logs/` や `projects/` などの変更には触れていません。

```
M  .claude/settings.json
M  .claude/skills/record-note-posts/SKILL.md
M  scripts/fetch_note_stats.py
A  scripts/note_gql.py
A  scripts/fetch_note_referrers.py
A  scripts/sync_note_referrers.py
```

明日の朝3時の cron から、流入元の日次記録が自動で積まれていきます。

この変更を記録しますか？`/record` で報告書と変更ログを残せます。GraphQL の認証手順やエンドポイントの調べ方は、note 側の仕様変更で再調査が必要になったときに効くので、残しておく価値はあると思います。
