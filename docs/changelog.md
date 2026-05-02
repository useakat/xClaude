---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-05-02

- **Wiki システム構築** — Starlight + GitHub Pages で Wiki 新設。`docs/` がソース、`starlight/` がビルド設定。[→報告書](../reports/20260502_wiki_setup.md)
- **X ワンポイント投稿スタイルガイド作成** — 実投稿10件を分析し13の観点で定義した `style/style-xonepoint.md` を作成。[→報告書](../reports/20260502_style_xonepoint.md)
- **writer-xonepoint・daily-xonepoint スタイルガイド参照化** — 両スキルから `style/style-xonepoint.md` を参照するよう変更。[→報告書](../reports/20260502_skill_style_reference.md)
- **投稿締め言葉ルールの追加** — X ワンポイント投稿の末尾を「読者の日常生活につながる1文」で締めるルールを強制。[→報告書](../reports/20260502_closing_rule.md)
- **Google サービス連携・スクリプト化ルールの追加** — gws CLI 統一とスクリプト化優先の原則を CLAUDE.md に明文化。[→報告書](../reports/20260502_implementation_rules.md)
- **報告書・変更ログ運用フローの整備** — 変更ログと報告書の1対1対応構造を設計。テンプレート作成・CLAUDE.md にルール追加。[→報告書](../reports/20260502_reporting_workflow.md)
- **daily-xonepoint 自動化改善** — STEP 3 を `/check-fact` に変更、STEP 5 のメール作成を gws CLI スクリプトに変更。[→報告書](../reports/20260502_daily_xonepoint_improvement.md)
- **git commit 前の確認フック追加** — `PreToolUse` フックで `git commit` 実行前に settings.json 確認を自動挿入。[→報告書](../reports/20260502_precommit_hook.md)
