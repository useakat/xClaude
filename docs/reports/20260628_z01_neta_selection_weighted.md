---
title: z01 ネタ選定を onePointNeta 除外・noteNeta:newsTopics:thoughts 2:2:1 加重に変更
date: 2026-06-28
tags: [workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260628_z01_neta_selection_weighted/)

## 背景・動機

z01（X 短文投稿）の制作フローは、SS1 の 4 シート（onePointNeta / noteNeta / newsTopics / thoughts）から**等確率**でソースシートを選んでいた。運用方針として、軽い解説型の onePointNeta を z01 では使わず、物語型（noteNeta）・ニュース（newsTopics）・思想（thoughts）に絞り、かつ配分を狙った比率（2:2:1）にしたいというニーズが出た。

cron（`scripts/run_xshort_draft.sh`）は `projects/z01/spec.md` を直接 Read して STEP1〜7 を実行するため、spec.md の STEP 1 を直すだけで実運用に反映される。

## 実施内容

- STEP 1 のソースシート選択を、3 シート（noteNeta / newsTopics / thoughts）の**重み付きランダム**に変更（`random.choices(..., weights=[2,2,1])`）。onePointNeta を選定対象から除外。
- 選択理由の説明文を「物語型・ニュース・思想を 2:2:1 で出す方針」に更新。
- STEP 2 の取得範囲テーブルから onePointNeta 行を削除し、誤解を防止。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/z01/spec.md` | STEP 1 を `random.choices(['noteNeta','newsTopics','thoughts'], weights=[2,2,1])[0]` に変更、説明文更新。STEP 2 テーブルから onePointNeta 行を削除 |

## 設計判断

- 廃止予定の `writer-xshort` スキル（全行プール→行数加重という別構造）は cron 未使用のため今回据え置き。
- 新コマンドは global `settings.json` の `Bash(python3 -c *)` で既に許可済みのため、permissions 追加は不要。
- `brand.md` の onePointNeta 採点軸（1a 等）は w003 など他フローでも使う共通定義のため残置。

## 確認結果

- 単発実行で noteNeta / newsTopics / thoughts のみが出力され、onePointNeta が出ないことを確認。
- 5000 回試行の分布が `noteNeta:1938 / newsTopics:2029 / thoughts:1033` と概ね 2:2:1 になることを確認。
