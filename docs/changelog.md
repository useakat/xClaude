---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。概要を読んで詳細が必要なら報告書へ。

---

## 2026-05-02

### Wiki システム構築
Starlight + GitHub Pages を使ったプロジェクト Wiki を新設。`docs/` が Markdown ソース、`starlight/` がビルド設定。
→ [詳細報告書](../reports/20260502_wiki_setup.md)

### X ワンポイント投稿スタイルガイド作成
実投稿10件をスプレッドシートから抽出・分析し、13の観点でスタイルを定義した `style/style-xonepoint.md` を作成。
→ [詳細報告書](../reports/20260502_style_xonepoint.md)

### writer-xonepoint・daily-xonepoint スキルのスタイルガイド参照化
両スキルに `style/style-xonepoint.md` への参照を追加。文体の詳細ルールを外部ガイドに委譲。
→ [詳細報告書](../reports/20260502_skill_style_reference.md)

### 投稿締め言葉ルールの追加
X ワンポイント投稿の最後の1文を「読者の日常生活につながる1文」で締めるルールを強制。
→ [詳細報告書](../reports/20260502_closing_rule.md)

### Google サービス連携・スクリプト化ルールの追加
gws CLI への統一とスクリプト化優先の原則を CLAUDE.md に明文化。
→ [詳細報告書](../reports/20260502_implementation_rules.md)

### 報告書・変更ログ運用フローの整備
変更ログと報告書を1対1対応させる構造を設計。テンプレート作成・旧 reports/ 削除・CLAUDE.md にルール追加。
→ [詳細報告書](../reports/20260502_reporting_workflow.md)

### daily-xonepoint 自動化改善
STEP 3 を `/check-fact` に変更、STEP 5 のメール作成を gws CLI スクリプトに変更。エージェントをスリム化しスキルに処理を集約。
→ [詳細報告書](../reports/20260502_daily_xonepoint_improvement.md)
