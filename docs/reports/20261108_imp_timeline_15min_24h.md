---
title: X / Threads 本体投稿の 24h インプ推移を 15 分刻みで記録する cron を新設
date: 2026-11-08
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261108_imp_timeline_15min_24h/)

## 背景・動機

X投稿一覧・Threads投稿一覧のインプ（views）は累計値だけで、投稿直後の伸び方（初動の速さ・何時間目で頭打ちになるか）が後から追えなかった。既存の `x_imp_alert.py` / `threads_views_alert.py` は 30 分おきに 2 時間窓だけを見て閾値通知するもので値を残さず、`w001_imp_snapshot.py` は日次（1 日 1 点）なので初動 24 時間の形は分からない。

よーんの要望は「X と Threads の投稿について、投稿から 24 時間後まで 15 分ごとにインプを記録する」。X API は従量課金（返却投稿 1 件ごと）のため、全区間を 15 分刻みにすると 1 投稿 96 読み・4 本/日で月 約 $11.5 になる。費用と粒度のバランスを相談し、**3 時間までは 15 分刻み・以降は 1 時間刻み**、本体投稿のみ、保存はローカル CSV、に決めた。

## 実施内容

- `scripts/imp_timeline.py` を新設（X・Threads 共通、cron `*/15`）
  - 投稿から 3h までは毎 tick（15 分）、3h〜24h は毎時 `:00` の tick だけ記録 → 1 投稿 34 点（13 ＋ 21）
  - **X の費用対策**：`:15 / :30 / :45` の tick は `start_time = now − 3h − 10min`、`:00` の tick だけ `now − 24h − 10min` で取得する。窓外の投稿は API 側で除外されるので課金されない。`exclude=retweets,replies` で本体投稿のみ（セルフリプは取らない）
  - Threads は `/{user_id}/threads?since=` → 各投稿の `/insights`（views, likes, replies, reposts, quotes, shares）。無料なので X と同じ間隔に揃えた（`FINE_HOURS_THREADS = 24` にすれば 15 分刻みを 24h 続けられる）
  - 保存先 `logs/imp_timeline/x_YYYY-MM.csv` / `threads_YYYY-MM.csv`（月別・追記のみ）。列は `記録時刻JST, 投稿ID, 投稿時刻JST, 経過分, インプ, いいね, RP, リプ, 引用, ブクマ, URL`
  - API 失敗はその回をログに残して飛ばすだけ（state ファイル無し。欠けは経過分で分かる）
  - `--dry-run` / `--platform x|threads` / `--force-full`（分に関わらず 24h 窓）
- `scripts/run_imp_timeline.sh` を新設（flock で多重起動防止、`logs/imp_timeline.log`）
- VPS crontab に `*/15 * * * * /bin/bash /root/xClaude/scripts/run_imp_timeline.sh` を追加（元の crontab は `/tmp/crontab.bak.*` に退避）
- `.gitignore` に `logs/imp_timeline/` を追加（月 1 万行規模になるため git 管理しない。`w001_imp_daily.csv` とは扱いを変えた）

### 費用の目安（X、Owned Read $0.001/件）

| 条件 | 1 投稿の読み取り | 4 本/日の月額 |
|---|---|---|
| 24h ずっと 15 分 | 96 回 | 約 $11.5 |
| **3h まで 15 分・以降 1h（採用）** | 34 回 | **約 $4.1** |
| 参考：既存 x_imp_alert（30 分 × 2h） | 6 回 | 約 $1.8 |

Owned Read 単価が Bearer Token で適用されているかは未確認のまま（10/1 の報告書の課題）。$0.005 なら 5 倍。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/imp_timeline.py` | 新設。X / Threads の本体投稿を取得し、経過時間に応じた間隔で CSV に追記 |
| `scripts/run_imp_timeline.sh` | 新設。cron ラッパー（flock・ログ） |
| `.gitignore` | `logs/imp_timeline/` を追加 |
| crontab（VPS、git 管理外） | `*/15 * * * *` を追加 |

## 設計判断

- **cron は `*/15` 1 本にし、取得窓を tick の分で切り替える**：3h 以降を別 cron にすると同じ投稿を 2 回読む tick ができる。1 本にして `:00` だけ 24h 窓にすれば、読み取り回数がそのまま記録点数になり、費用が最小になる
- **セルフリプは追跡しない**：note 導線のリンク到達の時間推移も見られるが読み取りが倍になる。`exclude=replies` で API 側から除外すれば課金もされない。必要になれば設定で外せる
- **Sheets に入れない**：15 分刻みの全行を Sheets に置くと月 1 万行超で重い。CSV を正とし、必要になったら集計して Sheets・ダッシュボードに出す
- **既存の通知 cron とは統合しなかった**：`x_imp_alert.py` をこの CSV 読みに変えれば X の読み取りを一本化できる（$1.8/月が浮く）が、今回は記録を先に動かし、統合は様子を見てから

## 確認結果

- `--dry-run --force-full`：X 1 件（06:01 投稿・経過 807 分・2,383 インプ）、Threads 1 件（4,173 views）を取得・判定
- `--dry-run`（19:28 の tick ＝ 3h 窓）：X・Threads とも 0 件 → 窓外の投稿は返らず課金なし
- cron 初回：19:30・19:45 は 3h 窓で 0 件、20:00 の tick で 24h 窓に切り替わり X・Threads 各 1 件を CSV に記録

## 今後の課題

- 数日分たまったら、3h で 13 点・以降 1h で欠けが無いことと、経過分のずれ（cron 起動遅れ）を確認する
- Developer Console の請求で Owned Read 単価を確認する
- `x_imp_alert.py` をこの CSV 読みに変える統合（任意）
- 週次振り返り（reporter-weekly-ops）やダッシュボードで「初動カーブ」を見る集計は未着手
- 今回の実装コミット `cf03576` には、`git pull` の autostash がステージ済みで戻った影響で、作業ツリーにあった別件の未コミット変更 39 ファイル（SKILL.md 数件・`docs/skills/*`・ログ・w002 下書き等）が混入したまま push された。よーんの判断でそのままにしている
