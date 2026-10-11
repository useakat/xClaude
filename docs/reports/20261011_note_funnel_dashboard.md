---
title: note 導線ダッシュボードを新設し、経路別ファネル（週次・投稿ごと）で毎朝自動更新
date: 2026-10-11
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261011_note_funnel_dashboard/)

## 背景・動機

10/4 に usephys.net 転送サイトを入れ、bio・固定ポスト・投稿からの note クリックが経路別に測れるようになった。しかし数字は Sheets（bioクリック・転送クリック明細・note流入元）に散らばっていて、「どの経路が効いているか」を見るたびに集計し直していた。

10/4 の分析では各経路を「インプ → リンク到達 → クリック → note 到達」に分解したが、当時はクリックが測れず推定だった。計測が揃った今、この分解を常設の画面にして、毎朝自動で更新されるようにしたい。

また、転送サイト経由の「note 到達」が「人のクリック」より多い現象が気になっていた。原因は 10/8 の案内ページ化より前のスキャナ混入で、ダッシュボードにもその注記が要る。

## 実施内容

### ダッシュボード（claude.ai Dashboard 型 Artifact）

- URL: https://claude.ai/artifact/Jd9f7Q3cGwpsvnRZjn5jgg
- データは添付 CSV 方式（データセット id ＝ CSV ファイル名）。ページ `files/index.html` が ArtifactData のデータセットを読む
- 表示内容
  - ヘッダータイル・日別チャート・転送クリック明細・固定ポスト履歴・note リンク付き X 投稿（当初から）
  - **導線ファネル（週次・月曜始まり）**：X bio / X 固定 / Threads bio / Threads 固定 の 4 表。インプ → 到達率 → リンク到達 → CTR → クリック →（bio のみ）到達率 → note 到達。進行中の週は「集計中」
  - **投稿ごとのファネル（累計）**：X と Threads の 2 表。本体 IMP → 到達率 → リンク到達（セルフリプの IMP / views）→ CTR → クリック。X は X アナリティクスのリンククリックを参考列に出す
  - **note 記事別**：PV・スキ・転送クリック・X 投稿に **購入数・CVR（購入数 ÷ PV 累計）** を追加
  - 「数字の定義」に各段階の出どころと注意（10/8 以前の到達はスキャナ混入、固定の週増分、Threads のインプ定義）
- 当初あった「経路別（直近7日）」「導線別」「記事の日別推移」はよーんの指示で削除

### 各経路の定義

| 経路 | インプ | リンク到達 | クリック | note 到達 |
|---|---|---|---|---|
| X bio | その週に投稿したポストの IMP 合計（X投稿一覧 K） | プロフアクセス合計（X投稿一覧 Q） | bioクリック X bio | note流入元 X bio |
| X 固定 | プロフアクセス合計 | 固定ポストの IMP 週増分（固定ポスト日次） | 固定期間内の xpost キー | 出さない |
| Threads bio | アカウント views（日次記録 AE） | 取れない（空欄） | bioクリック Threads bio | note流入元 Threads bio |
| Threads 固定 | アカウント views | 固定投稿の views 週増分 | 固定期間内の tpost キー | 出さない |
| X 本体＋セルフリプ | 本体行の IMP | セルフリプ行の IMP | xpost キーのビーコン累計（10/4 以前は X 集計） | 出さない |
| Threads 投稿＋セルフリプ | 本体行の views | セルフリプ行の views | tpost キーのビーコン累計 | 出さない |

投稿とクリックの突き合わせは **リンク本文一致 → 固定ポスト履歴** の 2 段だけ。投稿キーの日付から推定する段は、よーんの指示で入れていない。どちらでも見つからないキーは「元投稿不明」として出す。

### データ取得の追加（VPS cron。既存スクリプトに同乗）

- `record_pinned_post.py`（05:50）：固定中ポストの IMP・いいねを新シート `固定ポスト日次` に毎日スナップショット。X は `GET /2/tweets/{id}?tweet.fields=public_metrics`、Threads は `/{media}/insights`。週増分 ＝ その週の最終スナップショット − 前週の最終スナップショット
- `record_threads_followers.py`（05:30）：Threads user insights の `views` を 日次記録 AE 列「threads views」に記録。API の説明は「プロフィール閲覧数」だが実値は投稿表示の合計に近いので、アカウント views として扱う。9/29〜10/9 を backfill
- `fetch_threads_posts.py`（05:00）：`/{user_id}/replies` で自分のリプライも取り、Threads投稿一覧 の 親投稿URL（G）を埋める。権限 `threads_read_replies` が無い間は警告して飛ばす（10/10 によーんが再認可し、リプライ 126 行を取り込んだ）
- `note_article_daily.py`（05:55、00d97ea で新設）：note投稿一覧 の記事別累計を `note記事日次` に毎日スナップショット

### Threads投稿一覧 の読み手の修正

リプライ行（親投稿URL あり）を投稿数に数えないよう、reporter-daily / reporter-weekly の SKILL.md と `monetization_metrics.py` を修正。

### 書き出しと自動更新

- `scripts/note_funnel_export.py`：Sheets から 8 つの CSV（bio_clicks, click_detail, note_referrers, pinned, x_note_posts, articles, funnel_weekly, funnel_posts）を `logs/note_funnel/` に書き出す
- cloud routine「note 導線ダッシュボード更新」（`trig_01TqGyaD5wt21j8dkoECpU3L`、毎朝 06:30 JST）：書き出し → Artifact アセットにアップロード → ArtifactData でデータセットの `source` を差し替え。失敗時は Gmail でエラー通知

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/note_funnel_export.py` | 新設 → 8 CSV の書き出し。経路別・投稿ごとファネル、記事別 CVR。親投稿URL を最上位までたどる（2cd7f24） |
| `scripts/note_article_daily.py`・`run_note_article_daily.sh` | 新設。note 記事別累計の日次スナップショット（cron 05:55） |
| `scripts/record_pinned_post.py` | 固定ポストの IMP・いいねを `固定ポスト日次` に記録、IPv4 固定 |
| `scripts/record_threads_followers.py` | user insights `views` を日次記録 AE に記録。`--date` 指定時はフォロワ数を上書きしない |
| `scripts/fetch_threads_posts.py` | 自分のリプライを取得し 親投稿URL を埋める。`--no-replies` |
| `scripts/monetization_metrics.py` | Threads のリプライ行を 型別成績 から除外 |
| `.claude/skills/reporter-daily/SKILL.md`・`reporter-weekly/SKILL.md` | 親投稿URL が空の行だけを投稿として数える |
| `.claude/settings.json`・`.gitignore` | 権限追加、`logs/note_funnel/` を除外 |

## 設計判断

- **Threads のインプにアカウント views を使う**：Threads にはプロフィール閲覧数の API が無い。user insights `views` の実値は投稿表示の合計に近く、bio・固定ポストが見られる母数として使える。リンク到達（プロフ閲覧）は取れないので空欄
- **固定ポストのリンク到達は日次スナップショットの週増分**：X の投稿別 IMP は累計しか取れないため、毎日記録して差分を取る。初週は固定開始日からの差
- **投稿キーの日付推定を使わない**：Threads のキーは手で貼る日付で、同日に複数投稿があると誤って結び付く。本文一致と固定ポスト履歴だけにし、見つからないものは不明と出す方が信頼できる
- **note 到達は bio だけ**：note 側の参照元はホスト単位なので、固定・投稿ごとには分けられない
- **親投稿URL は最上位までたどる**：ツリー投稿では 本体 → 続きのリプ → リンク付きリプ と 2 段になる。1 段だけだと途中のリプ（6,973 views）を本体と誤認した（10/9 ニューホライズンズ）

## 確認結果

- 週 10/5：X bio クリック 2・Threads bio 4・X 固定 14・Threads 固定 5（bioクリック・転送クリック明細の合計と一致）
- 投稿ごと：X 10/8 ボイジャー 1,189 IMP / 14 クリック。Threads 10/9 ニューホライズンズ 本体 35,435 views → リンク到達 5,501 → クリック 114
- 記事別：ニューホライズンズ 購入 10 件・CVR 0.45%、ボイジャー 6 件・0.56%
- routine を手動実行し、8 データセットの差し替えがエラー無しで完了（61〜98 秒）

## 今後の課題

- Threads views を過去日へ backfill した際、日次記録 V 列（threads フォロワ数）を今日の値で上書きした。cron ログの日次値で 11 日分を復元し、`--date` 指定時はフォロワ数を上書きしないよう修正済み
- X 固定の「インプ」は週に投稿したポストのプロフアクセス合計で、10/4 分析の手入力の総 IMP とは定義が違う
- 残る「元投稿不明」は転送サイト導入時のテストキー（Threads、1 クリック × 2）
