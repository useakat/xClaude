---
title: Wiki 報告書サイドバーに「発信運用振り返り」「マネタイズ月報」を追加
date: 2026-11-01
tags: [wiki]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261101_wiki_reports_sidebar_ops_weekly/)

## 背景・動機

週次の発信運用振り返り（`/reporter-weekly-ops`）は 2026-08-16 の運用開始以来 `docs/reports/ops-weekly/` に12本、月次マネタイズレポート（`/reporter-monetization`）は `docs/reports/monetization/` に1本保存され、毎週・毎月 master に push されているのに、Wiki（Starlight）のサイドバー「報告書」セクションには日報・週報・月報しか載っておらず、サイトから辿れない状態だった。

当初は W44 の振り返りを claude.ai の Dashboard アーティファクトとして HTML 化したが、よーんの判断で「プロジェクトサイトの報告書セクションに追加する」方式に変更。md ファイルは既に routine が毎週保存・push しているため、サイドバーに1行足すだけで以後の週も自動反映される（アーティファクトのような追加工程が不要）。ダッシュボードは削除した。

## 実施内容

- `starlight/astro.config.mjs` のサイドバー「報告書」に、既存の `timeReportItems()`（ファイル名を新しい順に列挙する共通関数）を使って2項目を追加
  - 「発信運用振り返り」→ `reports/ops-weekly`（2026-W33〜2026-W44 の12本）
  - 「マネタイズ月報」→ `reports/monetization`（2026-07 の1本）
- 位置は「月報」の直後・「計画」の前。日報・週報・月報と同じ `collapsed: true` 形式

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `starlight/astro.config.mjs` | 報告書セクションに「発信運用振り返り」「マネタイズ月報」の2行を追加 |

## 確認結果

- `timeReportItems()` と同じロジック（index.md / template.md 除外・降順ソート）を node ワンライナーで実行し、ops-weekly が `2026-W44.md`〜`2026-W33.md` の12本を正しく列挙することを確認
- master へ push 済み。GitHub Pages のビルド後、サイドバーに反映される

## 今後の課題（任意）

- `reports/ops-weekly/index.md`・`reports/monetization/index.md` はサイドバー列挙から除外されるが、ページ自体は残っているため、必要ならセクション先頭リンクとして活用できる
