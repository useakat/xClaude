---
title: z01 Gmail 下書きを「1投稿1回」に固定（修正しても作り直さない）
date: 2026-06-28
tags: [workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260628_z01_gmail_draft_once/)

## 背景・動機

z01 の制作フローは STEP 6 で Gmail 下書きを自動作成する。下書き作成後にユーザーが本文修正（締め追加・固有名詞の補足など）を指示すると、`create_gmail_draft.sh` が更新非対応のため毎回「新規作成＋旧下書き削除」を繰り返す churn が発生していた（本セッションで実際に2回発生）。

ユーザー方針: **一度下書きを書いたら、その投稿に関しては以後本文を修正しても下書きを作り直さない**。修正版はチャットで提示するに留める。これにより churn と下書きの取り違えを防ぐ。

（当初検討した「作成前に承認ゲートを設ける」案はユーザー不採用。下書き作成タイミングは従来どおり STEP 6 で1回のまま。）

## 実施内容

- spec.md STEP 6 冒頭に「下書き作成は1投稿につき1回だけ。作成後に本文修正があっても作り直さない」を明記。
- spec.md「### その他」に同ルールと理由（`create_gmail_draft.sh` は更新不可・churn防止）、下書き前に本文を確定させる旨を追記。
- spec.md Verification に「下書き作成後に本文修正が入っても新規下書きが作成されていない（1投稿1下書き）」を追加。
- 記憶 `feedback_z01_flow_no_stop.md` に「1投稿1下書きルール」を追記し、`MEMORY.md` のインデックス行も更新。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/z01/spec.md` | STEP 6・その他・Verification に「1投稿1下書き・修正で作り直さない」ルールを明記 |
| `.claude/projects/.../memory/feedback_z01_flow_no_stop.md` | 同ルールを追記（git 管理外） |
| `.claude/projects/.../memory/MEMORY.md` | インデックス行を新ルール込みに更新（git 管理外） |

## 設計判断

- 下書き作成後の修正は Gmail 下書きに反映されない（cron が投稿するのは最初の版）。そのため STEP 4（check-fact）・STEP 5（check-brand）を通した確定稿で STEP 6 に進む現行フローが前提として重要。
- in-place 更新（`gws gmail users drafts update`）で1件を上書きし続ける別案もあるが、ユーザー指示は「作り直さない」のためデフォルトは上書きもしない（最初の1回で確定）。
- cron（`run_xshort_draft.sh`）は1回作成のみ・修正が発生しないため無変更。

## 確認結果

- spec.md の STEP 6・その他・Verification に新ルールが反映されていることを確認。
- 運用上は「下書き作成後の本文修正はチャット提示のみ・新規下書きを作らない」で、`gws gmail users drafts list` の件数が増えないことを今後の運用で確認する。
