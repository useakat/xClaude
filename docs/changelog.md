---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-05-09

- **mond-letter-reply スキル新設・ローカル化** — mond.how レター質問を Claude Opus で自動回答し Gmail 下書きを作成。gws CLI でラベル付与・アーカイブ、ローカル cron（6時間ごと）で定期実行。[→報告書](../reports/20260509_mond_letter_reply.md)

## 2026-05-07

- **style-xonepoint.md 二人称を「僕ら」に変更** — 2人称「あなた」をなるべく使わず「僕ら」で読者を包む表現に統一。関連する例文・締め言葉サンプルも更新。
- **reporter-daily 特記事項生成の精度向上（報告書読み込み追加）** — STEP 4 を2段階に分割し、changelog リンク先の報告書ファイルも読み込んで特記事項生成に活用するよう改善。[→報告書](../reports/20260507_reporter_daily_report_reading.md)
- **reporter-daily 文体ルールの style ファイル外部化** — SKILL.md STEP 5 の直書き文体ルールを `style/style-reporter.md` に切り出し、changelog 関連の特記事項を「具体性・明示性・能動性」原則で書くルールを追加。[→報告書](../reports/20260507_reporter_daily_style_externalization.md)
- **CLAUDE.md commit前ユーザー確認の必須化** — Git ルールに「内容をユーザーに提示して確認を得てから commit & push する」を明記。

## 2026-05-06

- **daily-xonepoint へのトンマナ調整ステップ追加** — STEP 3 にトンマナ調整（3-2）を追加。ファクトチェック後に `style-xonepoint.md` を参照し文体・口調のみ調整して【最終原稿】を確定。[→報告書](../reports/20260506_daily_xonepoint_tone_check.md)
- **check-fact GPT スコア採点・修正文案生成の追加** — GPT にスコア（0〜100）採点と修正文案生成を担わせ、ループ終了条件を「スコア 95 以上」に変更。[→報告書](../reports/20260506_check_fact_gpt_scoring.md)
- **daily-xonepoint メール下書きにチェックサマリーを追加** — STEP 3 でサマリーを記憶し、メール本文を「ファイル内容 → チェックサマリー → 投稿文」の順に変更。件名の時刻も JST 取得に修正。[→報告書](../reports/20260506_daily_xonepoint_check_summary.md)
- **check-fact の openai モジュール依存を curl に変更** — `openai` パッケージ依存を排除し `curl` で直接 API を叩く形に書き直し。remote 環境でも動作するよう修正。[→報告書](../reports/20260506_check_fact_curl_migration.md)
- **git_guard.py のガードロジック反転** — `CLAUDE_CODE_REMOTE != true` から `CLAUDE_CODE_LOCAL == true` の場合のみ通す設計に変更。デフォルトブロックで想定外セッションのスルーを防止。[→報告書](../reports/20260506_git_guard_logic_inversion.md)
- **check-fact への GPT ファクトチェック統合** — GPT-5.4-mini によるファクトチェックを統合し、環境変数・空引数の不具合を修正。[→報告書](../reports/20260506_check_fact_gpt_integration.md)
- **CLAUDE.md への振る舞いルール追加** — Plan mode 中は計画提示で止まるルール・ユーザーの判断を待ってから実行するルールを追加。[→報告書](../reports/20260506_claude_md_behavior_rules.md)
- **settings.local.json への書き込みを全セッションで禁止** — `settings.json` の `permissions.deny` に Write/Edit ルールを追加し、ローカルエージェントによる意図しない上書きを防止。[→報告書](../reports/20260506_settings_local_deny.md)

## 2026-05-05

- **Wiki 日報カレンダー表示と表示修正** — 日報一覧を月カレンダー形式（`DailyCalendar.astro`）に変更。改行・title frontmatter・CI ビルド・サイドバー順序の不具合を一連で修正。
- **daily-xonepoint の子スキル隔離（context:fork 対応）** — `writer-xonepoint`・`check-fact` に `context: fork` を追加して子スキルの完了マーカーが親に漏れる構造バグを修正。STEP 2 を `writer-xonepoint` 委譲に変更して保守性を向上。[→報告書](../reports/20260505_daily_xonepoint_context_fork.md)
- **reporter-monthly のアウトプット品質向上** — 月報生成に「量・粒度のルール」「戦略転換の判定」を追加し、データ部のマネタイズ欄を `0円` ベースで埋まるように修正。書き直しの手間を削減。[→報告書](../reports/20260505_reporter_monthly_quality_improvement.md)
- **reporter-daily の特記事項生成ルール強化** — 投稿の特記事項を「[投稿種類]投稿（[テーマ]）：[数値]。[一言]」のフォーマットに定型化。数値への自分の感想を禁止し、用語を「投稿」に統一、`RT→引用`・`BM→ブクマ` に変更。[→報告書](../reports/20260505_reporter_daily_quality_improvement.md)
- **commit_and_sync.sh の permissions パターン修正** — `Bash($(git ...))` 形式のパターン内の `)` がパーサーを早期終了させる問題を `Bash(*commit_and_sync.sh *)` に変更して回避。[→報告書](../reports/20260505_commit_and_sync_permissions_fix.md)

## 2026-05-04

- **mcp-gsheets 起動設定の修正** — `--stdio` 追加・settings.json 経由の試行と .mcp.json への差し戻し・auth env を `GOOGLE_SERVICE_ACCOUNT_KEY` のみに統一する一連の修正。[→報告書](../reports/20260504_mcp_gsheets_startup_fix.md)
- **reporter-daily スキル改善** — デフォルトを前日に変更・gws CLI から mcp-gsheets に移行・日次記録シートの読み込みを最新10行に限定。
- **cron X 投稿からの下書き除外** — `post_from_email.sh` の Gmail 検索クエリに `-is:draft` を追加し、下書きメールが投稿対象になる不具合を修正。
- **CLAUDE.md ファイル削除ルール変更** — 「ファイルを削除しない」から「削除する場合はよーんに確認する」に緩和。
- **reporter スキル UX 改善（完了後表示・特記事項ルール整備）** — daily/weekly/monthly 全スキルの完了後に生成ファイルを画面表示。reporter-daily の特記事項からフォロワー増減・`[開発]` 表記を廃止し、変更ログの要約を運用視点に変更。[→報告書](../reports/20260504_reporter_ux_improvements.md)
- **remote session での docs/reports/ push 許可** — `git_guard.py` を新設し、ステージ済みファイルが `docs/reports/` 配下のみなら remote でも commit・push を通す。フックもスクリプト外部化・動的パス解決に変更。[→報告書](../reports/20260504_remote_reports_push.md)

## 2026-05-03

- **mcp-gsheets の cloud session 対応** — `.mcp.json` を新設し command 型で定義、supergateway 不使用の構成に統一。認証は `GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数で渡す。[→報告書](../reports/20260503_mcp_gsheets_cloud_session.md)
- **settings.local.json の git 管理除外** — `settings.local.json` を untrack し `.gitignore` の誤記（`settings.json` を除外していた）を修正。
- **remote session での git 書き込み操作ブロック** — `PreToolUse` フックで `CLAUDE_CODE_REMOTE=true` 時に git push / commit / ブランチ作成をブロック。[→報告書](../reports/20260503_remote_git_block.md)

- **reporter スキル追加** — 日報・週報・月報を自動作成する `reporter-daily/weekly/monthly` の3スキルを新設。gws CLI で Sheets データを取得し AI 生成で記録。[→報告書](../reports/20260503_reporter_skills/)
- **/record スキル追加・CLAUDE.md 記録ルール簡潔化** — changelog と git log を照合して未記録変更を提案・記録する `/record` スキルを新設し、CLAUDE.md の記録手順をスキルに委譲。[→報告書](../reports/20260503_record_skill/)
- **コミット前確認フックの blocking 化** — `systemMessage` 通知方式から `decision:block` 強制停止＋ `[pre-commit-ok]` bypass トークン方式に変更し、確認漏れを構造的に防止。[→報告書](../reports/20260503_precommit_hook_blocking/)
- **コミット前フック検知対象の拡張** — `commit_and_sync.sh` 経由のコミットでもフックが発動するよう `settings.json` の hook 条件を修正。
- **変更ログ形式の整備** — 変更ログのエントリを日付セクション内の箇条書き形式に統一し、CLAUDE.md のルールも更新。
- **記録不要条件の明文化** — `permissions.allow` への追記のみのコミットは記録不要という例外ルールを CLAUDE.md に追加。
- **/update-permissions スキル追加・コミット前フック廃止** — blocking フックと bypass トークンを廃止し、`/update-permissions` スキルで任意のタイミングに手動で permissions.allow を更新する運用に変更。[→報告書](../reports/20260503_update_permissions_skill/)
- **/record スキル候補表示の改善** — 変更ログ候補に「関連する過去の変更」フィールドを追加し、選択メッセージを肯定形に変更。[→報告書](../reports/20260503_record_skill_improvement/)
- **daily-xonepoint メール下書き作成の MCP 化** — gws CLI がエージェント環境で使えないため STEP 5 を `mcp__claude_ai_Gmail__create_draft` に切り替え。[→報告書](../reports/20260503_daily_xonepoint_mcp_gmail/)
- **database CSV → Google Sheets 移行** — 8スキルの CSV 読み書きを mcp-gsheets ツールに書き換え、廃止スクリプトを `unused-scripts/` へ移動、SS1 に outputs シートを新設。[→報告書](../reports/20260503_database_csv_to_sheets_migration.md)
- **mcp-gsheets ローカル認証設定** — `.mcp.json` に `GOOGLE_APPLICATION_CREDENTIALS` を追加し、ローカルセッションでもサービスアカウントファイルで認証可能に。
- **Wiki データベース・アーキテクチャページ更新** — `docs/database.md` を全シートの列構成・操作リファレンス形式に書き直し、`docs/architecture.md` のフロー図と認証セクションを Sheets 移行後の構成に更新。

## 2026-05-02

- **Wiki システム構築** — Starlight + GitHub Pages で Wiki 新設。`docs/` がソース、`starlight/` がビルド設定。[→報告書](../reports/20260502_wiki_setup/)
- **X ワンポイント投稿スタイルガイド作成** — 実投稿10件を分析し13の観点で定義した `style/style-xonepoint.md` を作成。[→報告書](../reports/20260502_style_xonepoint/)
- **writer-xonepoint・daily-xonepoint スタイルガイド参照化** — 両スキルから `style/style-xonepoint.md` を参照するよう変更。[→報告書](../reports/20260502_skill_style_reference/)
- **投稿締め言葉ルールの追加** — X ワンポイント投稿の末尾を「読者の日常生活につながる1文」で締めるルールを強制。[→報告書](../reports/20260502_closing_rule/)
- **Google サービス連携・スクリプト化ルールの追加** — gws CLI 統一とスクリプト化優先の原則を CLAUDE.md に明文化。[→報告書](../reports/20260502_implementation_rules/)
- **報告書・変更ログ運用フローの整備** — 変更ログと報告書の1対1対応構造を設計。テンプレート作成・CLAUDE.md にルール追加。[→報告書](../reports/20260502_reporting_workflow/)
- **daily-xonepoint 自動化改善** — STEP 3 を `/check-fact` に変更、STEP 5 のメール作成を gws CLI スクリプトに変更。[→報告書](../reports/20260502_daily_xonepoint_improvement/)
- **git commit 前の確認フック追加** — `PreToolUse` フックで `git commit` 実行前に settings.json 確認を自動挿入。[→報告書](../reports/20260502_precommit_hook/)
