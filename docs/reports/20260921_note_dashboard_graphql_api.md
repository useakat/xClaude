---
title: note 新ダッシュボードの GraphQL API からインプレッション・記事別売上・流入元を取得
date: 2026-09-21
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260921_note_dashboard_graphql_api/)

## 背景・動機

note のダッシュボードが刷新され、記事ごとの**インプレッション・ページビュー・スキ・コメント・売上**と、**流入元（Google / X / note.com などのドメイン）の日毎の合計**が表示されるようになった。

これらを API で取れるか調べたところ、新ダッシュボード `https://note.com/dashboard` は Next.js + Apollo の別アプリで、データ取得先が **`https://graphql.note.com/graphql`（GraphQL）** に変わっていた。従来使っていた REST `/api/v1/stats/pv` は**旧ダッシュボードの API** で、インプレッションと記事別売上は返さない。流入元に至ってはエンドポイント自体が存在しない。

つまり、新しく見えるようになった指標は**GraphQL からしか取れない**。REST を使い続ける限り、note 側がいつ旧 API を止めてもおかしくないリスクも抱え続けることになる。

## 調査の経緯（次回同じ調査をするとき用）

1. `https://note.com/dashboard` の HTML を取得し、`_next/static/chunks/` 配下の JS を全部落とす
2. チャンク内を `grep` すると `Dashboard_StatPageQuery` / `Dashboard_ReferrerSectionQuery` などの **GraphQL クエリ本文がそのまま埋まっている**（Apollo + graphql-tag のため、永続化クエリではなくクエリ文字列が残る）
3. ベース URL は `https://graphql.note.com/graphql`。イントロスペクションが**開いている**ので、enum 値やフィールド一覧は後から確認できる

認証でつまずいた点：**Cookie だけを `graphql.note.com` に送っても `NotLoggedInViewer` になる**。チャンク内の Apollo リンク実装を読むと、2段構えだった。

```
1. POST https://note.com/api/v3/graphql/auth   （Cookie: _note_session_v5）
     → Set-Cookie: note_gql_auth_token=<JWT>（有効期限30分）
2. POST https://graphql.note.com/graphql
     Authorization: Bearer <JWT>
```

`/api/v3/graphql/auth` は **POST 限定**（GET は 404 を返すので、メソッド違いで「存在しない」と誤判断しやすい）。

## 実施内容

- GraphQL クライアント `scripts/note_gql.py` を新設。2段構えの認証・JWT の30分失効・Relay Connection のページネーションを隠蔽する。CLI としてイントロスペクションも叩ける
- 流入元取得 `scripts/fetch_note_referrers.py` を新設（期間合計＋日別内訳、JSON / CSV 出力）
- 流入元シート同期 `scripts/sync_note_referrers.py` を新設。`note流入元` シート（1行=1日）へ日付キーで upsert する
- `scripts/fetch_note_stats.py` にインプレッション・コメント・売上を追加し、**ビュー・スキの出所も GraphQL に変更**
- `record-note-posts` スキルを追従（書き込み範囲 `H:J` → `H:M`、流入元同期の STEP 7 を追加）
- `note投稿一覧` シートに K〜M列（インプレッション・コメント・売上）を追加し全28行をバックフィル。`note流入元` シートを新設し 2025-08-31 以降の387日分をバックフィル

### 取得できるようになったもの

| クエリ | 内容 |
|---|---|
| `dashboardNoteListConnection` | 記事別の PV・インプレッション・スキ・コメント・売上 |
| `dashboardNoteReferrersChart` | 流入元の期間合計（`legend`）と日別内訳（`timeSeriesBarChart`） |
| `dashboardSummary` | 期間合計の5指標 |
| `dashboardMetricChart` | 指標1つの日別推移（`IMPRESSION` / `PAGE_VIEW` / `LIKE` / `COMMENT` / `SALES`） |
| `dashboardStatLastUpdatedTimes` | 集計の最終更新時刻 |

期間指定は `unit`（`ALL` / `LAST_7_DAYS` / `LAST_28_DAYS` / `LAST_365_DAYS` / `CUSTOM` ほか）＋ `date` / `endDate`。`CUSTOM` なら任意期間・単日も指定できる。

**記事ごとの流入元内訳はスキーマに存在しない**（流入元はアカウント全体のみ）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/note_gql.py` | 新規。GraphQL クライアント（認証・失効・ページネーション・期間変数の変換） |
| `scripts/fetch_note_referrers.py` | 新規。流入元の期間合計＋日別内訳を JSON / CSV で出力 |
| `scripts/sync_note_referrers.py` | 新規。`note流入元` シートへ日付キーで upsert |
| `scripts/fetch_note_stats.py` | ビュー・スキの出所を GraphQL に変更。インプレッション・コメント・売上を追加。REST 値は `viewRest` / `likeRest` として検証用に温存 |
| `.claude/skills/record-note-posts/SKILL.md` | 列構成に K〜M を追加、書き込み範囲を `H:M` に拡張、STEP 7（流入元同期）を新設、出所を混ぜない注意書きを追加 |
| `.claude/settings.json` | 新スクリプト3本の実行権限を `permissions.allow` に追加（routine 用） |

## 設計判断

### REST の `read_count` を捨てて GraphQL の `pageViewCount` に一本化した

両者は**累計が一致しない**。実測（2026-09-21）：

| 期間 | REST | ダッシュボード |
|---|---|---|
| 直近7日 | 205 | 204 |
| 直近1ヶ月 | 1,070 | 1,065 |
| 累計 | 11,702 | 10,775（-7.9%） |

**同一期間ならほぼ一致し、ずれるのは累計だけ**。スキ（403）とコメント（14）は全期間で完全一致するので、「新ダッシュボードが古いデータを持っていない」という話ではなく、PV という指標だけが別物だった。記事ごとの差は総 PV に比例せず、完全一致の記事もあれば 20% ずれる記事もある。

原因はフロントエンドに残っていた note 自身のコメントで見当がつく。

> `アクセス数(PV: page_views/pv 合成)。表示数(impression)は無い期間は null`

`page_views` と `pv` の**2テーブルを合成**しており、ログ基盤の切り替えでレガシーな累計カウンタと合わなくなったと見られる。

当初は「H列は REST のまま据え置き、K〜M列だけ GraphQL」で実装したが、以下の理由で GraphQL に一本化した。

- REST は旧ダッシュボードの API で、止まったら H列だけ更新できなくなる
- よーんが画面で見る数字とレポートの数字が食い違う
- H列だけ別ソースという状態が残る
- **GraphQL は最初の記事（2025-08）から全履歴を持っているため、H列を全行入れ替えれば段差が生じない**

最後の点が決め手。継続性を理由に旧ソースを守る必要がなかった。

### フォールバックは残すが黙ってやらない

GraphQL が取れなかったときは REST 値に退避する（cron がシートを空で上書きするより安全）。ただし出所が混ざるため、`fetch_note_stats.py` は stderr に `WARN: ... REST の累計にフォールバックしました（出所が混ざります）` を出し、スキル側に「WARN が出たらシートに書かず原因を先に潰す」と明記した。

### 流入元シートは横持ち（1行=1日）

主要6ドメイン（X / Google / note.com / 直接・不明 / Yahoo / Bing）＋その他に丸めた。`日次記録` シートと形が揃い、そのままグラフにできる。ドメイン単位の完全な内訳が要るときは `fetch_note_referrers.py --csv` を使う。

## 確認結果

- 認証: `note_gql.py --viewer` で `Viewer / takaesu7431` を確認（Authorization ヘッダなしだと `NotLoggedInViewer`）
- 記事別: 全28記事でメトリクス欠落ゼロ。売上は5記事・計 7,290円（ボイジャー 2,940 / 空が赤かったら後編 1,960 / 冥王星 1,200 / 天王星 1,090 / ハッブル 100）
- 流入元: 2025-08-31〜2026-09-21 の387日分を取得。全期間累計は X 4,398 / Google 2,379 / note.com 1,728 / 直接・不明 1,601
- 冪等性: `sync_note_referrers.py --period 7d` を再実行して `updated: 7 / appended: 0`（行が増えない）
- 長期間の粒度: `--period 365d` では集計粒度が月になるため、日数とラベル数が一致するときだけ実日付を割り当て、それ以外は `date: null` としてラベルのみ残す
- シート: `note投稿一覧` 28行が再取得値と完全一致（不一致0件）。H〜J列の入れ替えでビュー合計 11,553 → 10,746
- フォールバック経路: `--no-gql` で28件の WARN が出ることを確認
- 影響範囲: `sync_x_note_analytics.py` / `monetization_metrics.py` は H列を列番号で読むだけのためコード修正不要

## 今後の課題

- **過去レポートとの断絶**：「Xnote導線記録」のビューとマネタイズレポートの購入CVR の分母が累計ベースで変わるため、月報・マネタイズレポートの前月比に一度だけ段差が出る
- 非公開 API のため予告なく仕様が変わりうる。壊れたときは上記「調査の経緯」の手順で JS チャンクからクエリを再抽出する
- REST `/api/v2/creators/.../contents` はハッシュタグ・サムネ・文字数のためにまだ使っている（GraphQL 側にこれらのフィールドが無いため）
- `つぶやき` は REST の `kind=note` に含まれず、GraphQL には出てくる（公開32件＋下書き1件 vs REST 28件）。記事ではないためシートには入れていない
