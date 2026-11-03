---
title: 毎朝 7 時の宇宙ダイジェストメールを新設（RSS/arXiv 収集 → claude -p 要約 → Gmail）
date: 2026-11-03
tags: [workflow, skill, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261103_space_digest_daily_mail/)

## 背景・動機

探査機・宇宙探査・宇宙物理・宇宙開発・素粒子物理の新着（論文・ニュース・プレスリリース・配信）を毎朝 1 通で把握し、発信軸（探査機の執念・直感を裏切る驚き）に合うネタ候補に早く気づきたい、というよーんの依頼（7 時送信希望）。

repo には新着を集める仕組みが無かった（research 系スキルは WebSearch の都度検索、`newsTopics` は手動の `/add-neta` のみ）。一方で部品は揃っていた：ローカル cron が `claude -p --model opus "/skill"` で無人スキルを動かす型（`run_mond_letter_reply.sh`）、`send_gmail.sh`、状態ファイルで重複通知を防ぐ型（`x_imp_alert.py`）。

よーんの決定（2026-11-01）：ローカル cron ＋ `claude -p`／英語＋日本語ソース／arXiv はキーワード絞り込み → 上位 5 本を要約／★ネタ候補を付ける（シート登録はしない）。計画段階で「みお」のキーワード追加と Nature・Nature Astronomy・Nature Physics・Science の論文ソース追加を指示された。

## 実施内容

3 段階・1 本の cron（06:45 JST → 07:00 前後に着信）：

1. **収集** `scripts/space_digest_fetch.py`：`scripts/space_digest_sources.json` の 25 ソース（RSS/Atom）と arXiv API（10 カテゴリ・300 件）から直近 48 時間の新着を並列取得（curl `--max-time 40`、8 並列、約 5 秒）。既読（`logs/space_digest_state.json`、30 日保持）・除外語（deal / podcast / APOD など）・同一タイトルを落とし、強 3 点・弱 1 点のキーワードスコアで絞って候補ファイル `logs/space_digest/YYYY-MM-DD_candidates.md` を書く。ソースごと 10 件・全体 60 件。終了コード 0 候補あり／20 なし／1 全ソース失敗
2. **要約** `.claude/skills/space-digest/SKILL.md`：`claude -p --model opus` が候補を読み、ニュース 8・プレス 6・論文 5（＋その他論文 10 件のタイトル）を日本語 2〜3 行で要約し、★ネタ候補を最大 3 件（理由つき）。候補ファイルに無い事実は書かない。WebFetch は ★ の 3 件のみ。本文を `_digest.txt` に Write して終了（送信はしない）
3. **送信** `scripts/run_space_digest.sh`：flock、`timeout 900`、収集失敗／新着なし／要約失敗の各ケースで別件名のメールを送る（毎日 1 通は届くので動作確認を兼ねる）。件名は本文 2 行目の件数から組む。60 日より古い日次ファイルを削除

ソース：プレス（NASA News Releases・NASA Science・JPL・ESA ×2・ESO・Fermilab・JAXA・国立天文台・KEK）、ニュース（Space.com・Universe Today・Phys.org ×2・SpaceNews・Quanta・CERN Courier・Physics World・Science News・sorae・AstroArts）、論文（arXiv・Nature・Nature Astronomy・Nature Physics・Science）。全分野が流れるソースは `keyword_filter` で 1 点以上だけ残す。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/space_digest_fetch.py` | 新規：収集・既読除外・スコアリング・候補ファイル生成 |
| `scripts/space_digest_sources.json` | 新規：ソース一覧・キーワード（強／弱）・除外語・arXiv カテゴリ・死んだフィードのメモ |
| `scripts/run_space_digest.sh` | 新規：cron ラッパー（収集 → claude -p → send_gmail.sh）。`--dry-run` で状態更新と送信を省く |
| `.claude/skills/space-digest/SKILL.md` | 新規：選別・要約・★付け・本文 Write |
| `.claude/skills/metadata.yaml` | `space-digest: リサーチ・分析` を追加 |
| `.gitignore` | `/logs/space_digest/` を追加 |
| `docs/workflows/space-digest.md`、`docs/scripts/index.md` | 新規・3 行追加 |
| crontab | `45 6 * * * run_space_digest.sh` を追加 |

## 設計判断

- **収集は Python、判断だけ Claude**：Claude が WebSearch で探す方式にしなかった。「昨日以降の新着」を検索で網羅できず、毎回の探索トークンも多い。収集を決定的にすると既読管理・件数制御がコードで保証できる
- **送信はスキルではなくラッパー**：本文ファイルが無ければ送らず、失敗がログに残る。スキルに送信権限を持たせない
- **requests → curl**：初回の直列取得は 5 分を超えた（NASA のフィードが 1 リクエスト 25 秒）。並列化に加えて curl `--max-time` で 1 ソースの上限を固定した
- **XML の壊れ対策**：NASA Science は root の xmlns 属性間にスペースが無く、JPL は `<content:encoded<![CDATA[` という壊れた要素がある。正規表現で先頭を直し、だめなら lxml の `recover=True` で読む
- **★ はシートに自動登録しない**：よーんが読んで `/add-neta` で登録する（自動登録すると候補の質を人が見る前にシートが汚れる）

## 確認結果

- 72 時間の dry-run で 60 件の候補（プレス 13・ニュース 25・論文 22）。全 25 ソース取得成功
- `claude -p` の手動実行で本文生成（約 76 秒）。★ は Voyager 1 の節電・通信復帰、Hera の初撮影、Hubble 民間整備 RFI の 3 件で発信軸に沿っていた
- `run_space_digest.sh --dry-run` で件名 `【宇宙ダイジェスト】2026-11-01（日）ニュース 8・プレス 5・論文 0` を生成し、状態ファイルを書かないことを確認
- よーんの承認後に実送信（`✓ 送信完了`）、crontab に登録

## 今後の課題

- 初回の自動実行（11/2 06:45）で既読除外が効くか、着信時刻が 07:00 前後かを確認する
- 候補が毎日 60 件に張り付くなら `per_source_max` や除外語を調整する
- 日本語ソースで「みお」「はやぶさ」が拾えるかは実際の新着が出るまで未確認
