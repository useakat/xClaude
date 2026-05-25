---
title: analyze-impression → ops_analyze-posts リネーム＋stats モード追加
date: 2026-05-25
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../history/20260525_ops_analyze_posts_rename_stats_mode_session/)

## 背景・動機

`analyze-impression` はフルモード（パターン分析＋スキル改善提案）のみで、「5月の平均インプはどのくらい？」という軽い集計確認にも全 STEP が走っていた。軽量な集計確認のための stats モードと、スキル名の命名規則統一（`ops_` プレフィックス）を兼ねてリネームと機能追加を実施した。

## 実施内容

- `analyze-impression/SKILL.md` を削除し、`.claude/skills/ops_analyze-posts/SKILL.md` を新規作成
- `metadata.yaml` のスキル名を `analyze-impression` → `ops_analyze-posts` に更新
- STEP 1 の引数テーブルに `stats` キーワードのパターンを追加（`stats`、`stats W003`、`stats 2026-05-01〜2026-05-25`、`先週 stats` など）
- STEP 3 の取得範囲を `A1:R50` → `A:R`、`AA1:AF50` → `AA:AF` に修正（50行上限バグの解消）
- STEP 3.5（stats モード専用）を新設：投稿数・平均IMP・中央値・最大/最小を集計し、外れ値（平均の3倍超）を検出して除外平均も出力。STEP 4 以降をスキップして終了

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/analyze-impression/SKILL.md` | 削除 |
| `.claude/skills/ops_analyze-posts/SKILL.md` | 新規作成（リネーム元 + stats モード追加） |
| `.claude/skills/metadata.yaml` | `analyze-impression` → `ops_analyze-posts` に変更 |

## 設計判断

stats / フルモードの切り替えは引数の `stats` キーワードで行う方式を採用。別スキルに分割する案もあったが、データ取得ロジック（STEP 2・3）を共有できる同一スキル内分岐の方がメンテコストが低い。

## 確認結果

`/ops_analyze-posts stats 2026-05-01~2026-05-25 W003` を実行し、集計サマリー（14件・平均IMP 10,079・中央値 4,124・最大 73,275・外れ値除外平均 5,218）が正常に出力されてスキルが終了することを確認。
