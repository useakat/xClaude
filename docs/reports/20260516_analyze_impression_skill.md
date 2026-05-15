---
title: analyze-impression スキル新設
date: 2026-05-16
tags: [skill, workflow]
---

← [変更ログへ](../changelog.md)

## 背景・動機

5/15 に手動で「ワンポイント解説投稿のインプレッション分析 → writer-xonepoint / daily-xonepoint のルール改善」を実施し、有効性を確認した。この workflow は HOW_ID 単位で他の投稿タイプ（W001/W002/W006）にも適用可能で、定期的に回すことで継続的に投稿品質を改善できる。手動運用の再現性を上げるため、スキル化した。

既存の `analyze-x-posts` は汎用的なアドホック分析スキルで、HOW_ID フィルタやスキル修正提案・自動編集の機能を持たないため、別スキルとして新規追加した。

## 実施内容

- `.claude/skills/analyze-impression/SKILL.md` を新規作成（9 STEP 構成：分析対象決定 → URL 取得 → メトリクス取得 → 比較対象取得 → パターン分析 → 改善提案 → ユーザー承認 → 修正適用 → 任意レポート保存）
- HOW_ID → スキル対応マップを定義（W001/W002/W003/W006 → writer-xstory / writer-note / writer-xonepoint / daily-xonepoint / style-xonepoint）
- `.claude/skills/metadata.yaml` に `analyze-impression: category: リサーチ・分析` を追加
- PostToolUse hook により `docs/skills/analyze-impression.md` と `docs/skills/index.md` が自動再生成された

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/analyze-impression/SKILL.md` | 新規作成。9 STEP 構成のスキル定義 |
| `.claude/skills/metadata.yaml` | analyze-impression をリサーチ・分析カテゴリに追加 |
| `docs/skills/analyze-impression.md` | 自動生成 |
| `docs/skills/index.md` | 自動再生成（リサーチ・分析カテゴリにリンク追加） |

## 設計判断

`analyze-x-posts` を拡張する案も検討したが、両者の役割が明確に異なる（汎用アドホック分析 vs HOW_ID連動のworkflow）ため、別スキルとして新規追加した。`analyze-x-posts` のデータ取得・正規化ロジックは新スキルでも踏襲。

## 確認結果

`/analyze-impression` でスキルとして呼び出せることを確認。Wiki にも詳細ページが反映済み。
