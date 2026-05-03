---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-05-03

- **reporter スキル追加** — 日報・週報・月報を自動作成する `reporter-daily/weekly/monthly` の3スキルを新設。gws CLI で Sheets データを取得し AI 生成で記録。[→報告書](../reports/20260503_reporter_skills/)
- **/record スキル追加・CLAUDE.md 記録ルール簡潔化** — changelog と git log を照合して未記録変更を提案・記録する `/record` スキルを新設し、CLAUDE.md の記録手順をスキルに委譲。[→報告書](../reports/20260503_record_skill/)
- **コミット前確認フックの blocking 化** — `systemMessage` 通知方式から `decision:block` 強制停止＋ `[pre-commit-ok]` bypass トークン方式に変更し、確認漏れを構造的に防止。[→報告書](../reports/20260503_precommit_hook_blocking/)
- **コミット前フック検知対象の拡張** — `commit_and_sync.sh` 経由のコミットでもフックが発動するよう `settings.json` の hook 条件を修正。
- **変更ログ形式の整備** — 変更ログのエントリを日付セクション内の箇条書き形式に統一し、CLAUDE.md のルールも更新。
- **記録不要条件の明文化** — `permissions.allow` への追記のみのコミットは記録不要という例外ルールを CLAUDE.md に追加。

## 2026-05-02

- **Wiki システム構築** — Starlight + GitHub Pages で Wiki 新設。`docs/` がソース、`starlight/` がビルド設定。[→報告書](../reports/20260502_wiki_setup/)
- **X ワンポイント投稿スタイルガイド作成** — 実投稿10件を分析し13の観点で定義した `style/style-xonepoint.md` を作成。[→報告書](../reports/20260502_style_xonepoint/)
- **writer-xonepoint・daily-xonepoint スタイルガイド参照化** — 両スキルから `style/style-xonepoint.md` を参照するよう変更。[→報告書](../reports/20260502_skill_style_reference/)
- **投稿締め言葉ルールの追加** — X ワンポイント投稿の末尾を「読者の日常生活につながる1文」で締めるルールを強制。[→報告書](../reports/20260502_closing_rule/)
- **Google サービス連携・スクリプト化ルールの追加** — gws CLI 統一とスクリプト化優先の原則を CLAUDE.md に明文化。[→報告書](../reports/20260502_implementation_rules/)
- **報告書・変更ログ運用フローの整備** — 変更ログと報告書の1対1対応構造を設計。テンプレート作成・CLAUDE.md にルール追加。[→報告書](../reports/20260502_reporting_workflow/)
- **daily-xonepoint 自動化改善** — STEP 3 を `/check-fact` に変更、STEP 5 のメール作成を gws CLI スクリプトに変更。[→報告書](../reports/20260502_daily_xonepoint_improvement/)
- **git commit 前の確認フック追加** — `PreToolUse` フックで `git commit` 実行前に settings.json 確認を自動挿入。[→報告書](../reports/20260502_precommit_hook/)
