---
title: X / Threads 本体投稿の 24h インプ推移を 15 分刻みで記録する cron を新設 — セッション履歴
date: 2026-11-08
sidebar:
  hidden: true
---

# セッション履歴

> 2026-11-08 のセッション作業ログ。

← [報告書へ戻る](../../reports/20261108_imp_timeline_15min_24h/)

---

## よーん *(19:01 JST)*

Xとthreads の投稿の、インプの推移を、投稿から 24時間後まで、15分ごとに記録するようにしたい。実装計画を立てて。

### Claude *(19:01 JST)*

*[ツール: `Bash`, `Bash`, `Read`, `Read`, `Bash`]*

実装計画をまとめます。既存の `x_imp_alert.py` / `threads_views_alert.py`（30分おきの通知 cron）と同じ取得ロジックが流用できるので、新規は実質スクリプト1本＋cron 1行です。

## 実装計画：投稿後24時間のインプ推移を15分刻みで記録

### 1. 新規スクリプト `scripts/imp_timeline.py`（X・Threads 共通）
- cron `*/15 * * * *` で実行（`run_imp_timeline.sh` でラップ、flock で多重起動防止）
- 毎回「いま−24時間−10分」以降の自分の投稿を取り、各投稿の累計値を1行ずつ追記
  - **X**: `GET /2/users/548606471/tweets?start_time=…&exclude=retweets` → `public_metrics`（x_imp_alert.py の `fetch_recent_posts` と同じ）
  - **Threads**: `/{user_id}/threads?since=…` → 各投稿の `/{id}/insights`（threads_views_alert.py と同じ）
- 投稿から24時間を超えたものは記録しない（最大 97 点/投稿）
- 記録列：`記録時刻(JST), 媒体, 投稿ID, 投稿時刻, 経過分, インプ(views), いいね, RP, リプ, 引用, ブクマ(shares), URL`
- API 失敗時はその回を飛ばしてログに残すだけ（系列に欠けができるが、経過分で分かる）。state ファイルは不要

### 2. 保存先
- `logs/imp_timeline/x_YYYY-MM.csv` / `threads_YYYY-MM.csv`（月別 CSV、追記のみ）
- 想定量：X 4本＋Threads 4本/日 × 97点 ≒ 約 800 行/日 → 月 2.4 万行。Sheets に全部入れるには多いので **CSV を正とし、Sheets やダッシュボードへは必要になったとき集計して出す**（`w001_imp_daily.csv` と同じ扱い）

### 3. X API の費用（ここが唯一の判断点）
X は従量課金（返却投稿 1 件ごと）。15分刻みだと 1 投稿あたり 96 回読みます。

| 条件 | 月額（Owned Read $0.001/件） |
|---|---|
| 原稿投稿のみ 4本/日、24h ずっと15分 | **約 $11.5** |
| ＋セルフリプも追跡（+4本/日） | 約 $23 |
| 最初の 6h は15分・以降は 1h（4本/日） | 約 $5 |
| 参考：現行 x_imp_alert（30分×2h） | 約 $1.8 |

- Owned Read 単価 $0.001 が Bearer Token で適用されているかは未確認（10/1 の報告書の課題のまま）。**$0.005 だと上の金額は5倍**になるので、着手前に Developer Console の請求で単価を確認してほしいです
- セルフリプは `exclude=retweets,replies` で API 側から除外すれば課金されません（既定は除外）
- Threads API は無料で費用なし

### 4. 既存通知との統合（任意・第2段階）
`x_imp_alert.py` の API 呼び出しを廃止し、この CSV の最新行を読んで閾値判定する形に変えれば、現行 $1.8 分が浮き、X の読み取りが一本化されます。

### 5. 作業手順
1. 単価を Developer Console で確認（よーん）
2. `imp_timeline.py` + `run_imp_timeline.sh` 作成、`--dry-run` で X・Threads とも取得確認
3. crontab に `*/15 * * * *` を追加、`.gitignore` に `logs/imp_timeline/` を追加するか判断（CSV を git 管理するかどうか）
4. 数日動かして欠けや経過分のずれを確認 → `/record`

*[ツール: `AskUserQuestion`]*

決まった内容で計画を確定します。

## 確定版

**取得間隔**：投稿から 3 時間までは 15 分刻み（13 点）、以降 24 時間までは 1 時間刻み（21 点）＝ 1 投稿 34 点

**費用の抑え方**：cron は `*/15` のままで、X API の `start_time` を tick ごとに切り替えます
- `:15 / :30 / :45` の tick → `start_time = now − 3h − 10min`（3h 以内の投稿だけ返る＝課金もそれだけ）
- `:00` の tick → `start_time = now − 24h − 10min`（24h 以内の全投稿）
- `exclude=retweets,replies` で本体投稿のみ
- 見積もり：4 本/日 × 34 読み × 30 日 ≒ **月 $4.1**（Owned Read 単価の場合。$0.005 なら $20）

**Threads**：無料なので同じ間隔で揃えます（曲線を X と比較しやすくするため）。15 分刻みを 24h 続けたければ設定 1 行で変えられるようにしておきます。

**保存**：`logs/imp_timeline/x_YYYY-MM.csv` と `threads_YYYY-MM.csv`（月別、追記のみ）
列：`記録時刻JST, 投稿ID, 投稿時刻JST, 経過分, インプ, いいね, RP, リプ, 引用, ブクマ, URL`

**ファイル**
- 新規 `scripts/imp_timeline.py`（X・Threads 共通。`--dry-run` / `--platform x|threads` あり）
- 新規 `scripts/run_imp_timeline.sh`（flock ＋ログ `logs/imp_timeline.log`）
- crontab に `*/15 * * * *` を 1 行追加
- `.gitignore` に `logs/imp_timeline/` を追加（CSV は git 管理しない。`w001_imp_daily.csv` と違い月 1 万行になるため）

**手順**
1. スクリプト 2 本を作成 → `--dry-run` で X・Threads とも取得を確認（X は投稿 1 件分の課金が出ます）
2. crontab 追加
3. 数日後に CSV の点数（3h で 13 点・以降 1h）と欠けを確認 → `/record`

この内容でスクリプトの作成に進んでよいですか？

---

## よーん *(19:27 JST)*

OK

### Claude *(19:27 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Read`]*

git pull 時にログ CSV の競合が出たので、両方の行を残して解消してから本題に進みます。

*[ツール: `Bash`]*

Now the scripts.

*[ツール: `Write`, `Write`, `Bash`, `Edit`, `Bash`, `Bash`]*

実装が終わり、cron も動き始めました。

**作成・変更**
- `scripts/imp_timeline.py`（新規）：X・Threads 共通。3h まで 15 分、以降 1h（`:00` の tick だけ 24h 窓で取得）、`exclude=retweets,replies` で本体のみ
- `scripts/run_imp_timeline.sh`（新規）：flock ＋ `logs/imp_timeline.log`
- `.gitignore`：`logs/imp_timeline/` を追加
- crontab：`*/15 * * * * run_imp_timeline.sh` を追加（元の crontab は `/tmp/crontab.bak.*` に退避）

**動作確認（dry-run）**
- 24h 窓：X 1 件（06:01 投稿・経過 807 分・2,383 インプ）、Threads 1 件（4,173 views）を取得
- 3h 窓（19:28 の tick 相当）：X・Threads とも 0 件 → 窓外は API 側で除外され課金なし
- 最初の実記録は 19:30 の tick から `logs/imp_timeline/x_2026-11.csv` / `threads_2026-11.csv` に入ります

**補足**
- git pull 時に `logs/hook_records.csv` で競合が出たため、upstream 側と手元側の行を両方残して解消しました（11/8 の z01 2 行＋11/3 の W001 1 行）
- 直近 24h の X 本体投稿が 1 件しか無かったので（06:00 のみ）、見積もりの「4 本/日」より実費は下がる見込みです

上記 3 ファイルだけを commit & push してよいですか？（作業ツリーの他の変更には触れません。）また、この変更を `/record` で記録しますか？

---

## よーん *(19:51 JST)*

commit push して　 /record

### Claude *(19:51 JST)*

*[ツール: `Bash`]*

master に push しました（`cf03576`）。続いて `/record` を実行します。

*[ツール: `Skill`, `Bash`, `Bash`]*

先に報告すべきことがあります。

**コミットに意図しないファイルが混入しました**
`git pull` 時の autostash がステージ済みの状態で戻っていたため、`cf03576` には予定の 3 ファイルに加えて、作業ツリーに残っていた未コミットの変更 39 ファイルが一緒に入り、master に push されています。内容は以下です（私が編集したものではなく、以前から手元にあった変更です）。
- `.claude/skills/writer-xstory/SKILL.md`・`projects/w001/spec.md`（15 案を全件チャット表示する指示の追加）、`check-fact-lim` / `research_setup-sources` / `research_trivia-source` の SKILL.md
- `docs/skills/*.md` 13 件（Wiki の自動生成分）
- `logs/*.log`・`logs/hook_records.csv`（約 1.6 万行の追記）
- `projects/w002/2026-08-20_akatsuki/draft/*`・`projects/w002/.../note-record.md`・`redirect/redirects.json`

対応の選択肢です。
1. **このままにする** — いずれも、よーんの手元の変更なので master に載っていて問題なければ何もしない
2. **39 ファイルを元に戻すコミットを積む** — `f26f33f` 時点の内容に戻す revert コミットを push し、変更は未コミットとして作業ツリーに残す（履歴の書き換えはしない）

どちらにしますか？

---

**変更ログ候補（未記録）**

1. **X / Threads 本体投稿の 24h インプ推移を 15 分刻みで記録する cron を新設** — 投稿から 3h は 15 分、以降 1h 刻み（`:00` の tick だけ 24h 窓で取得して X の従量課金を月 約 $4 に抑制）。本体投稿のみ、月別 CSV に追記
   - 関連コミット: `cf03576`
   - 変更ファイル: `scripts/imp_timeline.py`・`scripts/run_imp_timeline.sh`・`.gitignore`・crontab
   - 関連する過去の変更: 「X インプ監視を従量課金対応（start_time 絞り込み・30分間隔化）」「X インプ通知の条件変更（2 時間以内に 1,500 インプ）と Threads views 通知の新設」「仮説検証インフラを追加（H4 日次IMPスナップショット…）」

記録するなら「1」、不要なら「スキップ」と返してください。混入ファイルの対応（1 か 2）と合わせてお答えください。

---

## よーん *(20:03 JST)*

1

### Claude *(20:04 JST)*

「1」を、混入ファイルは「このままにする」、記録は候補 1、の両方と解釈して進めます（違えば止めてください）。

*[ツール: `Bash`]*
