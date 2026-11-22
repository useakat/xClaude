---
title: リライト元の選び方を、グレード S/A 優先から IMP 1 万以上の上位 20 本からのランダムに変更
date: 2026-11-22
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261122_rewrite_pool_imp_top20_random/)

## 背景・動機

`/writer-xrewrite` のリライト元は、バズスコアのグレード S/A の投稿を優先し、S/A が無いときだけ IMP 1 万以上の上位 20 本から選ぶ二段構えだった。よーんの判断で、グレードによる優先をやめ、IMP 1 万以上の上位 20 本から常にランダムに選ぶ形にした。「半年以上前（180 日）」「未リライト」などの除外条件は従来どおり。

なお途中で「上位 20 本」の上限まで外して全件にしてしまったが、よーんの指摘で上位 20 本に戻した（上限の変更は依頼に含まれていなかった）。

## 実施内容

- `scripts/rewrite_pool.py`
  - `pick` は S/A プールを使わず、IMP 1 万以上の上位 20 本から `random.choice` で 1 本選ぶ。出力 JSON の `pool` は `IMP10K`（旧 `SA` / `TOP20`）。`--tweet-id` による手動指定（`MANUAL`）は従来どおり
  - `list` の表示と docstring を新仕様に変更。候補なしのエラー JSON は `{"error": "候補なし", "imp10k": 0}`
  - `build_pools` の戻り値の形は変えていない（`record` が使うため）
- `.claude/skills/writer-xrewrite/SKILL.md`
  - description・設計の出典・`pool` の説明・枯渇時メッセージから「S/A 優先」を削除

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/rewrite_pool.py` | S/A 優先を廃止し、IMP 1 万以上の上位 20 本からランダムに選ぶ |
| `.claude/skills/writer-xrewrite/SKILL.md` | 選び方の記述を新仕様に更新、`pool` の値を `IMP10K` に |

## 確認結果

- `rewrite_pool.py list` で候補が 20 本（母集団 113 本のうち IMP 1 万以上の上位）になることを確認
- `pick` を複数回実行し、グレードなしの投稿も含めて、IMP・日付が異なる投稿が選ばれ `pool` が `IMP10K` になることを確認
- `8a53372` として master に push 済み

## 今後の課題

- 日報・週報など、`pool` の値（`SA` / `TOP20`）を読む処理があれば追従が必要。今回の確認範囲（`rewrite_pool.py`・SKILL.md）では他に参照を見つけていない
