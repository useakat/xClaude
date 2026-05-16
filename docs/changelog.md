---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-05-16

- **reporter-daily 特記事項の記載順を定義** — ワンポイント→質問→ストーリー→note→変更ログ→その他の順を SKILL.md に明記。週報・月報参照時に種別ごとに追いやすくなった。[→報告書](../reports/20260516_reporter_daily_note_order.md)
- **style-reporter.md メトリクス表記をリポスト・リプに修正** — 数値表記の「引用」を「リポスト」に変更し「リプ」を追加。シートの列との対応（リツイート列→リポスト・ブックマーク列→ブクマ・リプライ列→リプ）を明記。v1.1→v1.2。
- **analyze-impression スキル新設** — X投稿のIMP分析と関連スキル改善提案を行う9STEPのスキルを新設。HOW_ID単位でフィルタしてパターン抽出・スキル/style修正案生成・承認後の自動編集まで実行する。[→報告書](../reports/20260516_analyze_impression_skill.md)
- **writer-xonepoint/daily-xonepoint：日常入り口・具体的数字フックのルール化** — 実データ分析（5/1〜5/14のW003）で「日常の物を冒頭の入り口にした投稿」が高IMP、「宇宙固有現象が入り口の投稿」が低IMPと判明。フック制約・日常接続位置・ネタ補充条件を強化。[→報告書](../reports/20260515_xonepoint_impression_analysis.md)
- **record_output.py に cron 用サービスアカウントファイル fallback 追加** — cron は `.bashrc` を読まないため `GOOGLE_SERVICE_ACCOUNT_KEY` が未設定になり Sheets 記録が失敗していた。環境変数がない場合に `gcp/` の JSON ファイルを直接読む fallback を追加。[→報告書](../reports/20260516_record_output_cron_fallback.md)

## 2026-05-15

- **record_output.py を Google Sheets 書き込みに移行** — X投稿記録先をローカル CSV から Google Sheets の outputs シートに切り替え。gspread + サービスアカウント認証で実装し、既存18行も転記済み。[→報告書](../reports/20260515_record_output_sheets_migration.md)
- **brand.md の想定読者・締めルール削除・フォント定義追加** — 想定読者セクションと締めのルールを削除し、フォント指定（Noto Sans JP Black）を追加。
- **writer-xstory スキル改善：フック・構成・完結性ルール追加** — フック2文構成・ブロック空行区切り・ストーリー完結・教訓は末尾集約の4ルールを追記。SOHOの長文X投稿の初稿→最終原稿の差分を学習として反映。[→報告書](../reports/20260515_writer_xstory_hook_rules.md)

## 2026-05-14

- **reporter-daily STEP 5 に保存前の自己チェック追加** — 特記事項を保存する前に「専門用語チェック」「何を→どう変わるかチェック」「読者想定チェック」の3項目を必ず通過させる手順を SKILL.md に追加し、style ルールの取りこぼしを構造的に防止。[→報告書](../reports/20260514_reporter_daily_self_check.md)
- **mcp__github__push_files の PreToolUse リマインドフック追加** — `git_guard.py` のブロック回避として `push_files` を使っていないかをツール実行直前に確認するリマインドを `.claude/settings.json` に追加。
- **git_guard.py 削除・リモートセッションの git 操作制限を全廃** — `git_guard.py` を削除し PreToolUse フックを全削除。リモートセッションでは feature ブランチで作業・merge 段階で精査する方針に切り替え。[→報告書](../reports/20260514_git_guard_removal.md)
- **【X長文】メール→X投稿の自動化追加** — `【X長文】` 件名のメールを毎日17時にXへ自動投稿する cron ジョブを追加。既存の `post_from_email.sh` をそのまま流用し、HOW_ID=W001 で記録。[→報告書](../reports/20260514_xlong_post_automation.md)
- **発信 plan.md の新設・CLAUDE.md への参照ルール追加** — 発信の目的・ターゲット・価値提供・成功条件を `plan.md` に定義し、コンテンツ制作前の参照を CLAUDE.md に義務化。[→報告書](../reports/20260514_plan_md_and_claude_md.md)

## 2026-05-13

- **commit_and_sync.sh を GitHub MCP プッシュ方式に移行** — master へのローカルプロキシ経由 push が 403 で失敗するため、スクリプトをローカルコミットのみに変更し、push は `mcp__github__push_files` で直接行う方式に移行。reporter・record・update-permissions の5スキルの Git ステップを更新。[→報告書](../reports/20260513_commit_and_sync_github_mcp.md)
- **CLAUDE.md git フックブロック回避禁止ルール追加** — `git_guard.py` などのフックによるブロックを勝手に回避しないよう禁止事項に明記。回避が必要な場合は必ずよーんに許可を求めてから行う。

## 2026-05-11

- **cron メール投稿スクリプト：複数メール溜まり時に1件のみ投稿するよう修正** — 投稿成功後に `break` を追加し、未処理メールが複数あっても最古の1件のみ投稿して終了。質問回答・ワンポイント解説の両 cron に適用。[→報告書](../reports/20260511_post_from_email_single_post.md)

## 2026-05-09

- **Wiki スキル一覧の自動更新システム実装** — スキル追加時に Wiki が自動更新されるシステムを構築。metadata.yaml でスキル ↔ カテゴリを管理、post-commit フックで自動生成。[→報告書](../reports/20260509_wiki_skills_auto_update.md)
- **check-fact スキル改良：完全性チェック機能追加** — テーマの背景知識から説明の不足要素を自動検出し追加文案を生成するステップを追加。ファクトチェック前に説明の完全性を確保。[→報告書](../reports/20260509_check_fact_completeness_check.md)
- **daily-xonepoint スキル改良：ファイル保存時の git commit & push 削除** — STEP 4 の自動 git コミット処理を削除。下書き作成段階での git 記録は不要と判断。[→報告書](../reports/20260509_daily_xonepoint_remove_git_commit.md)
- **mond-letter-reply スキル新設・ローカル化** — mond.how レター質問を Claude Opus で自動回答し Gmail 下書きを作成。gws CLI でラベル付与・アーカイブ、ローカル cron（6時間ごと）で定期実行。[→報告書](../reports/20260509_mond_letter_reply.md)
- **brand.md 新設・スタイルガイド差分化** — 全スタイルファイルの共通定義（人格・想定読者・言葉遣い・NG）を `brand.md` に集約し、各 style ファイルをフォーマット固有の差分のみに簡略化。[→報告書](../reports/20260509_brand_md_and_style_diff.md)
- **Wiki スキル詳細ページの自動生成と index.md のリンク化** — 全26スキルの詳細ページを自動生成し、index.md のスキル名をクリック可能なリンクに変更。ユーザーが各スキルの SKILL.md 内容を閲覧できるよう整備。[→報告書](../reports/20260509_wiki_skill_detail_pages.md)
- **analyze-target スキル改良：Google Sheets 自動追記機能追加** — 複数候補を「スコア付き」で提示し、ユーザーの選択後に Sheets へ自動追記する機能を追加。手動貼り付けの廃止で運用負荷を軽減。[→報告書](../reports/20260509_analyze_target_sheets_auto_append.md)

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
- **X ワンポイント投稿スタイルガイド作成** — 実投稱0件を分析し13の観点で定義した `style/style-xonepoint.md` を作成。[→報告書](../reports/20260502_style_xonepoint/)
- **writer-xonepoint・daily-xonepoint スタイルガイド参照化** — 両スキルから `style/style-xonepoint.md` を参照するよう変更。[→報告書](../reports/20260502_skill_style_reference/)
- **投稿締め言葉ルールの追加** — X ワンポイント投稿の末尾を「読者の日常生活につながる1文」で締めるルールを強制。[→報告書](../reports/20260502_closing_rule/)
- **Google サービス連携・スクリプト化ルールの追加** — gws CLI 統一とスクリプト化優先の原則を CLAUDE.md に明文化。[→報告書](../reports/20260502_implementation_rules/)
- **報告書・変更ログ運用フローの整備** — 変更ログと報告書の1対1対応構造を設計。テンプレート作成・CLAUDE.md にルール追加。[→報告書](../reports/20260502_reporting_workflow/)
- **daily-xonepoint 自動化改善** — STEP 3 を `/check-fact` に変更、STEP 5 のメール作成を gws CLI スクリプトに変更。[→報告書](../reports/20260502_daily_xonepoint_improvement/)
- **git commit 前の確認フック追加** — `PreToolUse` フックで `git commit` 実行前に settings.json 確認を自動挿入。[→報告書](../reports/20260502_precommit_hook/)
