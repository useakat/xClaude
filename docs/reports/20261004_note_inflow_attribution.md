---
title: note 導線の切り分け（流入元の Threads 列・X投稿一覧の noteURL 列・直接不明の比率配分）
date: 2026-10-04
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261004_note_inflow_attribution/)

## 背景・動機

note への流入経路（X 投稿・X bio・X 固定ポスト・他人の X 投稿・Threads bio・Threads 投稿・Threads 固定ポスト）のボトルネックを調べようとしたところ、note 側の流入元データが分析に耐えない粒度だった。

- `note流入元` シートの列は X / Google / note.com / 直接・不明 / Yahoo / Bing / その他 で、**Threads（`l.threads.com`）が「その他」に合算**されていた
- 「X」列には自分の投稿・セルフリプ・他人の紹介投稿・bio 経由が混ざり、どの導線が効いているか分からない
- X アプリ内ブラウザは参照元を付けないため、X 由来の到達の多くが**「直接・不明」に落ちる**。X 側のクリック数（X アナリティクス）と note 側の到達数を突き合わせる基盤が無かった
- X投稿一覧には「どの投稿が note リンクを含むか」の記録が無く、note リンク付き投稿のクリック数を集めるには本文を目で追う必要があった

## 実施内容

- **note流入元に Threads 列を追加**（`sync_note_referrers.py`）。`l.threads.com` を「その他」から分離し、見出し行を毎回書き直す方式にして列追加を既存シートへ反映。`--full` で全期間を再構築
- **Threads ミラーから note リンクのセルフリプを除外**（`post_from_email.sh`）。Threads 投稿に note リンクを貼らなければ、Threads からの到達＝プロフィール（bio・固定）導線の性能として読めるため。dry-run・本番の両経路で `note.com` を含む `--reply-text` を落とす
- **他人の note リンク投稿の週次集計**（`x_note_mentions.py`、cron 日曜 07:00）。`url:"note.com/takaesu7431" -from:usephys -is:retweet` を検索し `logs/x_note_mentions.csv` に件数を記録。これは「リンクを含む投稿の数」であって流入数ではない点をユーザーと確認
- **X投稿一覧に noteURL 列（AI）を追加**（`gas/GetMyTweets.js`）。`entities.urls` / `note_tweet.entities.urls` の `expanded_url` から `note.com` を抽出して記録し、既存行は空なら埋める。`backfill_x_note_urls.py` で過去 43 行をバックフィル
- **月次突合 `--reconcile YYYY-MM`** を実装。列は見出し名で参照（列追加で index がずれた再発防止）。「直接・不明」を X：note.com：Threads の**見えている比で配分**し、X クリック数（X投稿一覧の noteURL 行の「リンククリック」合計）は参考値として併記。投稿別の比率表と読み方の注記を出力

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/sync_note_referrers.py` | COLUMN_MAP に Threads（`l.threads.com`）を追加。見出し行を毎回書き直す |
| `scripts/post_from_email.sh` | Threads ミラーで `note.com` を含むセルフリプを送らない（dry-run・本番） |
| `scripts/x_note_mentions.py`（新規） | 週次の他人投稿検索（CSV 追記）と `--reconcile` 月次突合（比率配分） |
| `scripts/run_x_note_mentions.sh`（新規） | cron ラッパー（日曜 07:00） |
| `gas/GetMyTweets.js` | `NOTE_URL_COL = 35`、`extractNoteUrls()`、新規行・既存行への noteURL 書き込み |
| `scripts/backfill_x_note_urls.py`（新規・一回限り） | 過去投稿の noteURL を X API から取得して AI 列に 43 行書き込み |

## 設計判断

- **「直接・不明」の推定方式**。候補は (a) 全部 X に足す、(b) ベース分（検索・note 内由来）を差し引いて残りを X、(c) X クリック数との差を X の上限とする、(d) 見えている比で配分、の4つ。ユーザー判断で (b) は「差し引く妥当性がない」、(c) は「bio・他人投稿のクリックが X クリック数に含まれないので上限として成立しない」として不採用。(d) を採用し、X クリック数は参考値にとどめた
- **X クリック数 > note の X 列** という不等式を過去 13 か月で検証。データが揃う月では成立（捕捉率 2026-02〜07 は 0.26〜0.77、08 以降は 0.7〜1.3）。7月は「X 列＋直接・不明」がクリック数の 96% で、直接・不明の主因が X アプリ内ブラウザであることを確認。3月は X アナリティクス CSV に返信が含まれず（再エクスポート2回でも 45 行 vs 2月 873 行）検証不能と判断
- **note アプリからの流入**は参照元が落ちても「note からの流入」に含めて数えるのが自然、という整理で note.com 列の扱いは変えていない
- Threads 投稿に意図的にリンクを貼る場合の経路（経路6）は、この時点では「生リンクなら Threads 列」とし、後続の転送サイト導入で `tpost` ホストに分離した

## 確認結果

- `sync_note_referrers.py --full` で 399 行を再構築し、Threads 列に値が立つことを確認
- `post_from_email.sh` の dry-run で note リンク付きセルフリプが Threads 側で落ちることを確認
- `x_note_mentions.py --reconcile` を 2025-09〜2026-09 の 13 か月で実行し、比率表・不等式の成立を確認
- GAS は clasp push 後、X投稿一覧の新規行に noteURL が入ることを確認。バックフィル 43 行

## 今後の課題

- bio・固定・投稿が転送サイト（別報告）経由になり「直接・不明」がほぼ消える見込みなので、配分の対象を見直す（X 投稿：note.com：Threads の生リンク分のみ）
- 他人の投稿（経路4）はリンク投稿の件数しか取れず、クリック・到達は測れない
