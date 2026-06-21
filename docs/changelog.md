---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-06-21

- **infographic_template 6型をスーパーニャンコ詳細定義に更新** — `radial / checklist / compare_contrast / pyramid / step_flow / timeline` のキャラクター指定を簡略版から詳細版（体色・耳内側・額のハート・W字口・チーク・卒業角帽＋タッセル・マント・ベルト＋バックル・ぬいぐるみ質感）へ統一。あわせて gws を Drive スコープ付きで再認証（従来6スコープ保持＋drive 追加）、`file` コマンドを導入（Drive画像ソース追加の MIME 判定用）。[→報告書](../reports/20260621_infographic_template_nyanko_detail/)
- **notebooklm_manager.py に SOCKS プロキシ経由オプションを追加（IP ブロック回避）** — 環境の IP が NotebookLM にブロックされる問題を、別 Windows server 経由の SSH SOCKS プロキシで回避。`NOTEBOOKLM_SOCKS_PROXY` 設定時に httpx をローカル DNS（`rdns=False`）の SOCKS トランスポートへ差し替え（Windows OpenSSH はリモート DNS 非対応のため必須）。鍵認証化（`administrators_authorized_keys`）＋トンネル管理ヘルパー `scripts/notebooklm_tunnel.sh`、ソース本文表示 `get-source` サブコマンドも追加。[→報告書](../reports/20260621_notebooklm_socks_proxy/)
- **visual_infographic のスーパーニャンコ参照画像をローカル references/ 画像に変更** — 参照画像を Drive URL DL から `references/スーパーニャンコアイコン.png` の `--file` 追加へ切替。新規作成ブランチを `make-infographic`（Drive DL）から `create`→`add-text`→`add-source-file --file`→`infographic` ループへ統一し、Drive 認証・`file` コマンド依存を解消。[→報告書](../reports/20260621_visual_infographic_local_nyanko_ref/)
- **W003 制作フローに投稿フォルダの Drive アップロードを追加（drive_put_folder.sh 新設）** — Gmail 下書き後にテーマフォルダ丸ごと（draft 画像含む）を Drive `xClaude/projects/w003` 配下へフォルダ構造ごと再帰アップロードする工程を標準化。新スクリプト `scripts/drive_put_folder.sh`（gws でフォルダ get-or-create＋`drive_put.sh` 委譲）を新設し spec.md に Step 9・daily-xonepoint に STEP 8 を追加。`gws drive files create` のメタデータは `--json`（ボディ）で渡す。[→報告書](../reports/20260621_w003_post_folder_drive_upload/)
- **W003 制作フローにチャット履歴保存ステップを追加** — Gmail 下書き後に「チャット履歴を保存」（`save_session_history.py` で Markdown 化しテーマフォルダに `chat_history.md` 保存）を挿入し、Drive アップロードを後段に。spec.md と daily-xonepoint の両方を更新し、制作チャットを投稿フォルダに同梱して Drive にアーカイブする。[→報告書](../reports/20260621_w003_chat_history_step/)
- **W002 字数チェックに「裏の取れる別の具体で埋める／水増し禁止」ルールを追加** — `spec.md` step7 に、字数不足は公開ソースで裏取りした新事実・数値・固有名・当事者発言で埋め、冗長な前置き・同義の言い換え等で水増ししない／agenda 目標と実数を比較・据え置きは一言報告、を明記。[→報告書](../reports/20260621_w002_wordcount_concrete_fill_rule/)
- **W002 本文インライン執筆の明記と writer_note-story 非推奨化（Wiki 廃止・非推奨カテゴリ新設）** — `spec.md` step6 に本文は brand.md 準拠インライン執筆（`writer_note-story` は出典形式・下流フローが異なるため不使用）を明記。`writer_note-story` に廃止バナー、`metadata.yaml` で `writer_note-story`・`sync-to-sheets` を「廃止・非推奨」へ、`update_wiki_skills.py` の category_order に同カテゴリ追加し Wiki 再生成。[→報告書](../reports/20260621_w002_inline_writing_writer_note_story_deprecated/)

---

## 2026-06-20

- **notebooklm_manager.py の ask 出力を answer だけに絞る** — `cmd_ask` の `print(result)` を `print(getattr(result, "answer", result))` に変更。`AskResult` 全体（全 `cited_text`）の数百KB〜MB ダンプをやめ回答本文のみ出力に。`/check-fact-lim` フォーク実行の stream idle timeout 対策。フォークで完走を確認。[→報告書](../reports/20260620_notebooklm_ask_answer_only/)

---

## 2026-06-19

- **W002 note 記事制作を2モード対応化（X長文深掘り→note）** — ネタ起点（モードA）に加え、既存 X長文ポスト（w001）を深掘りして6000〜8000字・980円有料 note にするモードBを追加。notebook を w001 から再利用し、構成5案→タイトル5案→文字配分の3段階対話で承認、本文以降は共通フロー（`/check-fact-lim` 化）。[→報告書](../reports/20260619_w002_two_mode_xdeepdive_note/)

---

## 2026-06-18

- **mcp-gsheets 認証修正・record-note-posts cron 追加** — `settings.json` から `GOOGLE_APPLICATION_CREDENTIALS` を削除しローカル/リモート両対応に。`run_record_note_posts.sh` 新設・毎朝3時の cron を追加。`run_mond_letter_reply.sh` にも `GOOGLE_SERVICE_ACCOUNT_KEY` 明示 export を追加。[→報告書](../reports/20260618_mcp_gsheets_auth_fix_and_cron/)
- **gws 認証フロー標準化・check_auth.sh 強化** — `scripts/gws_auth.sh` 新設（VPS IP 自動取得・SSH トンネルコマンドと認証 URL を整形出力）。`check_auth.sh` の gws チェックをトークン有効性確認から Gmail API 実呼び出しに強化（スコープ不足も検知可能に）。CLAUDE.md にブラウザ認証手順と gws 再認証コマンドを追記。[→報告書](../reports/20260618_gws_auth_flow_standardization/)
- **W001 X長文制作を2モード対応化＋両モードを NotebookLM ソースで担保** — 起動時にモード確認（モードA＝`noteNeta` 先行／モードB＝既存 note 記事）し題材確定まで分岐、以降は共通化。両モードとも notebook を用意（A＝`research_setup-sources` で新規作成／B＝w002 の notebook-id.md 再利用）して `/check-fact-lim` で本文の事実をソース限定検証。モード名を writer-xstory の状況A/B と統一。[→報告書](../reports/20260618_w001_two_mode_notebook_factcheck/)
- **W001 制作フロー改善（ファクトチェック順序）＋brand.md 執筆ルール追加** — 本文作成直後に `/check-fact-lim` を1回→ユーザー承認→必要なら再チェックの順へ再構成。完全性追加はトーン・字数を壊さない範囲で取捨選択する運用を明記。brand.md に「熱量（山場は淡々を避ける）」「明確さ（曖昧表現を避ける）」を追加。[→報告書](../reports/20260618_w001_factcheck_order_and_writing_rules/)
- **X長文投稿用 Gmail 下書きの自動化（サムネ添付対応）** — spec に「⑭ X投稿用メール下書き作成」を追加（`【Xストーリー】`／`[投稿文]`／添付PNG の cron 体裁）。`create_gmail_draft.sh` に `--attach`（複数可）を追加し本文＋サムネ添付を gws CLI で自動化。サムネ保存先を `output/thumbnail.png` に変更。[→報告書](../reports/20260618_w001_xstory_gmail_draft_attachment/)

---

## 2026-06-17

- **visual_infographic のタイトル＆プロンプトをテンプレート基準に変更** — メインタイトルを入力テキストの冒頭1文に固定。プロンプトを `projects/w003/infographic_template/` の型テンプレートを Read して埋める方式へ（内容に合う count 個を自動選択、不在時は従来生成にフォールバック）。spec.md step7・Naming にも明記。[→報告書](../reports/20260617_visual_infographic_template_based_prompts/)
- **Drive ツール修正（drive_get.sh 現行 gws 対応・add-source-file のローカルファイル対応）** — `drive_get.sh` の `-o` がカレント外パスを弾く不具合を cd＋basename で解消。`notebooklm_manager.py` の `add-source-file` に `--file`（ローカル画像直接追加）を追加し、Drive 認証に依存せずソース追加できるようにした。[→報告書](../reports/20260617_drive_tool_gws_fix_local_source/)

---

## 2026-06-16

- **visual_infographic に既存 notebook 再利用分岐を追加** — プロジェクトフォルダに `notebook-id.md`（ハイフン）があればその notebook で図解生成（新規作成・削除しない）。1枚目の前に原稿テキスト・スーパーニャンコ参照ソースを確認し不足分のみ追加。`notebooklm_manager.py` に `list-sources` / `add-text` / `add-source-file` を追加。[→報告書](../reports/20260616_visual_infographic_notebook_reuse/)
- **W003 図解プロンプトの6パターンテンプレート追加** — `projects/w003/infographic_template/` に step_flow / compare_contrast / radial / timeline / pyramid / checklist の6テンプレートを新設。[→報告書](../reports/20260616_visual_infographic_notebook_reuse/)

---

## 2026-06-15

- **W003 制作フローを spec.md 基準で対話化（trivia研究→ネタ選択→フォルダ作成→画像承認）** — spec.md に `research_trivia-source` 実行＋ユーザー選択・テーマフォルダ作成ステップを追加し、daily-xonepoint を対話フロー（STEP2 ネタ選択・STEP7 画像承認で停止）へ全面改修。writer-xonepoint をテーマのみ入力で成立するよう修正。cron 無人実行は廃止。[→報告書](../reports/20260615_w003_interactive_flow_alignment/)

---

## 2026-06-14

- **writer-xstory を「フォーカス→冒頭フック→本文」の3段階対話制作に再設計** — X長文制作を、フォーカス決定・冒頭フック決定（hook-patterns 5型×3=15案）・本文作成の3段階でユーザーと相談する方式へ。note記事あり（状況A）/テーマ先行（状況B）の両対応。draft_xstory を対話前提に修正し W001 spec.md を /writer-xstory 参照にスリム化。[→報告書](../reports/20260614_writer_xstory_three_stage_interactive/)
- **save_session_history.py をサブディレクトリ起動セッション対応に修正** — JSONL 探索を git ルート基準の単一ディレクトリ固定から、git ルートのパスを接頭辞に持つ全 projects ディレクトリの最新を探す方式へ変更。サブディレクトリで開いたセッションの履歴が空になる不具合を解消。[→報告書](../reports/20260614_save_session_history_subdir_fix/)
- **プロジェクトフォルダ名を what_id に統一** — `projects/` 配下を note-story→w002・x-story→w001・x-onepoint→w003 にリネームし、各設定・spec・スキル定義の active な参照パスを更新。docs/・archive の履歴記録は据え置き。[→報告書](../reports/20260614_projects_rename_to_what_id/)

---

## 2026-06-11

- **writer_note-story を本文フェーズ専用に絞り込み** — スキルを本文・6000字チェック・演出セルフチェックの3工程専用に縮小し、構成フェーズ/ファクトチェック/保存・通知を削除。文体・演出は brand.md を権威にし notebook ソース限定執筆を追加、旧版を writer_note-story_old にバックアップ、spec.md step6-8 を委譲明記。[→報告書](../reports/20260611_writer_note_story_body_phase_only/)
- **note-story 出典運用の整備（参考情報チェック・2段階運用・リサーチ運用ルール）** — 制作フローに「参考情報チェック」step を追加、出典を2段階運用（draft=本文での参照内容／index=文献の概要）に整理、「notebook 優先→WebSearch→notebook 還元」のリサーチ運用ルールを CLAUDE.md に追加。[→報告書](../reports/20260611_note_story_citation_workflow/)
- **note-story brand/spec の役割整理＋読者視点レビュー工程の新設** — ファクトチェック後のユーザー修正を分析し、依存順序・過剰断定・呼称統一の3ルールと読者視点セルフチェックを追加。タイトル規則を spec→brand、出典書式を brand→spec へ整理し `[^N]`→`[N]` も修正。[→報告書](../reports/20260611_note_story_brand_spec_roles_reader_review/)
- **note-story spec.md サムネイル生成ステップの詳細化** — プレースホルダだった step 12 を5手順化（design-brief→生成プロンプト→画像生成は手動・外部→レビュー）。Naming に thumbnail 成果物（1280×672px）を定義。[→報告書](../reports/20260611_note_story_thumbnail_spec_step/)

---

## 2026-06-07

- **mcp-gsheets リモート認証修正** — `settings.json` の `GOOGLE_APPLICATION_CREDENTIALS` を削除し、リモートセッションでも mcp-gsheets が `GOOGLE_SERVICE_ACCOUNT_KEY` で正常動作するよう修正。`mcp__github__push_files` の PostToolUse フックも追加。[→報告書](../reports/20260607_mcp_gsheets_remote_auth_fix/)
- **W002 執念の物語 note 記事プロジェクト立ち上げ＋プロジェクト雛形** — `projects/note-story/` に plan/brand/spec を新設（style-note-story の文体・演出ルールを brand.md へ取り込み）。`projects/template/` 一式と `templates/SKILL_example.md` も追加。[→報告書](../reports/20260607_note_story_project_setup/)
- **visual_section-planner スキル新設** — 記事本文を入力に、各 H2 へ画像案を3つ（図解／イメージ／写真Web取得）セクション分け markdown で出力し `draft/image-plan.md` に保存。[→報告書](../reports/20260607_visual_section_planner_skill/)
- **visual_section-imager スキル新設（NotebookLM 画像生成）** — 絞り込み済み image-plan を入力に notebook-id.md の notebook で図解=infographic指示／イメージ=情景画像（文字なし）を各3枚生成し draft/images へ保存。失敗時自動リトライ・写真案スキップ。[→報告書](../reports/20260607_visual_section_imager_skill/)

---

## 2026-06-06

- **research_setup-sources スキル新設** — `research_trivia-source` のノートブック作成＋Deep Research（Steps 0〜3）を汎用スキルとして切り出し。notebook_id を返すビルディングブロックとして他スキルから再利用可能。[→報告書](../reports/20260606_research_setup_sources_skill/)
- **リモートセッション用 Drive アップロードスクリプト追加** — gws 認証情報をクラウドに置くセキュリティリスクを避け、Drive MCP 経由でアップロードする `drivemcp_put_remote.sh` を新設。CLAUDE.md にアップロードルールを追記。[→報告書](../reports/20260606_drivemcp_put_remote/)
- **cron：認証チェック結果を毎回 Gmail に送信** — `check_auth.sh` を改修し、エラーの有無に関わらず毎日 `useakat@gmail.com` に認証チェック結果メールを送信するよう変更。
- **CLAUDE.md：master push 完了報告にブランチ名明示ルール追加** — git push 完了を報告する際にブランチ名（例：「master に push しました」）を明示するルールを振る舞いルールに追加。

---

## 2026-06-04

- **スキル作成用汎用テンプレート追加** — `templates/SKILL_temp.md` を新設。SKILL.md 作成時のひな形（目的・手順・出力形式・禁止事項）。

- **mcp-gsheets 認証を `GOOGLE_APPLICATION_CREDENTIALS` に統一** — `.mcp.json`・`.claude/settings.json`・`~/.bashrc` の認証情報参照を Google 標準の `GOOGLE_APPLICATION_CREDENTIALS` に一本化し、認証情報の二重化を解消。[→報告書](../reports/20260604_mcp_gsheets_auth_unification/)
- **xmcp 自動起動 hook 追加・パスの環境非依存化** — SessionStart hook で xmcp サーバーを自動起動し、`.claude/settings.json` のパスハードコードを `$CLAUDE_PROJECT_DIR`＋`*xClaude` ワイルドカードに統合。mcpServers.type を http に修正。[→報告書](../reports/20260604_xmcp_autostart_hook/)
- **x-onepoint：セッション開始時に spec.md を自動読み込みする hook を追加** — `projects/x-onepoint` での作業開始時に spec.md を自動 Read する SessionStart hook を追加。
- **cron：認証チェック結果を毎回 Gmail に送信** — cron の認証チェックジョブが、結果を毎回 Gmail に通知するよう変更。
- **check-fact-lim スキル新設（NotebookLM ソース限定ファクトチェック）** — `check-fact` をベースに、GPT(gpt-5.4-mini)呼び出し2箇所（STEP1完全性・STEP2ファクト）を `notebooklm_manager.py ask` に差し替え。第1引数 notebook_id で参照ソースを限定し、その notebook のソースのみを根拠に判定する。[→報告書](../reports/20260604_check_fact_lim_skill/)
- **check-tonmana スキル新設（トンマナ調整＋P01化スコアリングの切り出し）** — `daily-xonepoint` の STEP 4-2/4-3 を独立スキルに抽出し再利用可能化。daily-xonepoint 側は `/check-tonmana` 呼び出しに置換。[→報告書](../reports/20260604_check_tonmana_skill/)
- **check-tonmana 縮小・check-p01 分離（brand.md 基準化）** — check-tonmana を作業フォルダ brand.md 基準のトンマナ調整専用に縮小し、P01化スコアリングを check-p01 へ分離。brand.md に5軸語彙・各種例・削る対象優先度リストを展開し check-p01 を brand.md 単体で非劣化に動作させた。daily-xonepoint は 4-2→4-3 の2段呼び出しに変更。[→報告書](../reports/20260604_check_p01_split_brand_based/)

## 2026-06-03

- **CLAUDE.md：master push 時の通知ルール追加** — master に push した際に「master にプッシュしました」と明示的に報告するルールを禁止事項セクションに追加。
- **x-onepoint プロジェクト CLAUDE.md 追加・ドキュメント整備** — `projects/x-onepoint/CLAUDE.md` 新設（起動時に spec.md を Read するルール定義）し、brand.md・plan.md・spec.md を実運用に合わせて整備。[→報告書](../reports/20260603_x_onepoint_project_claude_md_and_docs_update/)
- **x-onepoint/outputs/ 投稿別フォルダ構造の導入** — `projects/x-onepoint/outputs/YYYYMMDD_[topic]/` 形式で投稿ごとにフォルダを作成するルールを導入。spec.md の Output・Naming・Rules を更新し、既存3画像を新フォルダへ移行。[→報告書](../reports/20260603_x_onepoint_outputs_folder_structure/)

## 2026-06-02

- **reporter-monthly スキル改修（ポスト数集計・W001/W003推移・計画ファイル読込・具体数字明記）** — STEP 2 にポスト数集計追加・STEP 4.5（W001/W003 月別推移）新設・STEP 5（翌月マネタイズ計画ファイル読込）新設・STEP 6 の次月改善に計画ファイル具体数字を明記するルールを追加。[→報告書](../reports/20260602_reporter_monthly_skill_improvement/)

## 2026-06-01

- **analyze-x-posts：Drive アップロードをローカル保存のみに変更** — レポート依頼時の動作をローカル保存＋Drive アップロードからローカル保存のみに簡略化。SKILL.md の STEP 5（Drive アップロード）を削除し、出力ルールの説明も更新。
- **ネタ選定を writer-xonepoint から daily-xonepoint に移動** — `writer-xonepoint` を原稿生成専用に限定し、Sheets 読み込み・分野グループ選定・ステータス更新の責務を `daily-xonepoint` の STEP 2 に移植。テーマ直接指定での単体呼び出しが可能になった。[→報告書](../reports/20260601_neta_selection_move_to_daily_xonepoint/)
- **x-onepoint プロジェクト設計ドキュメント新設** — `projects/x-onepoint/` に `brand.md`（口調・表現ルール）・`spec.md`（制作フロー・命名規則）を新設し、`plan.md` を W003/PE01/PR003 計画に基づき具体化。スキルから役割別に参照できる構成にした。[→報告書](../reports/20260601_x_onepoint_project_docs/)
- **Wiki サイドバー再設計（動的生成・月別グループ）** — `astro.config.mjs` のサイドバーを autogenerate ベースの動的生成に変更し、報告書を月別にグループ化して表示する構成に再設計。
- **cron 定期実行ジョブ一覧を Wiki に追加** — `docs/wiki/cron-jobs.md` を新設し、サーバー上で稼働中の cron ジョブ一覧（スクリプト名・実行時刻・目的）を Wiki に追加。
- **収益目標を月15万円に更新** — `docs/plans/` 配下の収益計画ドキュメントの月間収益目標を15万円に更新し、KPI・施策の優先順位を再整理。

## 2026-05-30

- **research_trivia-source スキル新設** — テーマを渡すと NotebookLM Deep Research でソース収集→トリビアネタ 3〜5 件を選定するスキルを新設。企業ページ除外はクエリ文字列に指示を埋め込む方式を採用。`notebooklm_manager.py` に `deep-research` サブコマンド（timeout=120s）も追加。[→報告書](../reports/20260530_research_trivia_source_skill/)
- **writer-note スキルを writer_note-story に改名** — スキル名を内容に合わせてリネーム。`CLAUDE.md`・`note-quick`・`ops_analyze-posts` の参照も更新。
- **冒頭フック表現テンプレート集の新設・X系 writer からの参照** — @russianblue2009 の814投稿分析で得た高IMP4型（逆説・知識提示・場面描写・問いかけ）を `style/hook-patterns.md` に構文テンプレート化。X系 writer 4スキル（xstory/xonepoint/xnews/xqa）から「各スキル固有のフック制約が優先・本ファイルは引き出し」として参照させた。[→報告書](../reports/20260530_hook_patterns_style/)
- **6月マネタイズ計画の更新（目標/KPI整理・全¥980・90万IMP）** — 目標とKPIを分離し、X目標を月間IMP90万・note全¥980に設定。W001/W003/W002のKPI（本数・平均IMP・CTR・CVR）を明記し、KPI達成が目標の十分条件になるよう検算で整合させた。誘導モデル（クロス週）・期待売上の推計式も追記。[→報告書](../reports/20260530_june_monetization_plan_update/)
- **research_xhook スキル新設** — 指定 X アカウントの投稿フック（冒頭1文）を LLM で帰納的に分類し、IMP平均でランキング提示するスキルを新設（regex ハードコード廃止）。[→報告書](../reports/20260530_research_xhook_skill/)

## 2026-05-29

- **Wiki：docs/plans を Wiki サイドバーに追加** — `starlight/astro.config.mjs` のサイドバーに「計画」セクション（`autogenerate: plans/`）を追加し、`202606_monetization.md` の `sidebar: hidden: true` を削除。今後 `docs/plans/` にファイルを追加するだけで自動反映される。[→報告書](../reports/20260529_wiki_plans_sidebar/)

## 2026-05-28

- **daily-xonepoint：Gmail下書き冒頭にネタID追記** — STEP 2でネタNoを記憶対象に追加し、Gmail下書き本文冒頭に `[ネタID]onePointNeta[{No}][/ネタID]` タグを挿入するよう変更。
- **visual_infographic：NotebookLM によるプロンプト生成への委譲** — Claude 自身によるプロンプト生成を廃止し、ソーステキスト＋スーパーニャンコ画像を持つ notebook に `ask` でプロンプト 3 パターンを生成させる方式に変更。`setup-notebook` サブコマンド追加・`ask_template.txt`/`infographic_config.env` の外部ファイル化も実施。[→報告書](../reports/20260528_visual_infographic_notebooklm_prompt/)
- **database CSV アーカイブ削除・残存参照の Sheets 化** — 参照用アーカイブだった `database/*.csv` 7件を削除し、`research-plan` スキルの CSV 参照を noteNeta シート参照に修正。ネタ補充ルーティンの未使用判定も Sheets ステータス列ベースに変更（CSV 乖離による誤判定の解消）。[→報告書](../reports/20260528_database_csv_removal/)
- **visual_infographic 改善: 即アップロード方式・スーパーニャンコ参照・notebooklm_manager 修正** — 1枚生成ごとに Drive へ即アップロード＋ローカル削除する方式に変更。中心放射型バブルに視線フロー（左上→左下→右上→右下）ルールを追加し、スーパーニャンコ参照画像を `--extra-source-url` で追加対応。Drive 画像ソースの `add_file` 切替と拡張子付与 400 エラーも修正。[→報告書](../reports/20260528_visual_infographic_improvements/)
- **CLAUDE.md：スキル一覧をカテゴリ別に整理・全32スキルに更新** — `.claude/skills/` セクションを metadata.yaml と同期し、8カテゴリで全32スキルを整理。
- **wiki スキル一覧を全35スキルで更新・詳細ページ自動生成** — update_wiki_skills.py を実行して wiki スキル一覧と詳細ページを更新。追加スキル9件の新規ページも自動生成。
- **update_wiki_skills.py：git root を自動検出に改善** — PostToolUse hook が全環境で動作するよう、スクリプトを git rev-parse で git root を自動検出する仕様に修正。[→報告書](../reports/20260528_update_wiki_skills_auto_git_root/)

## 2026-05-27

- **research_pain-xpost スキル新設** — 特定 X ポストのリプライ・引用RTを取得し、読者のニーズ・疑問を5観点でクラスタリングして note 記事テーマを提案、承認後に noteNeta シートへ追記するスキルを新設。引用RT・リプ取得は `ops_post-reactions` の仕組み（xmcp＋リプ・引用一覧シート）を再利用。[→報告書](../reports/20260527_research_pain_xpost_skill/)
- **CLAUDE.md：承認待ち質問後は hook フィードバックで先に進まないルール追加** — 承認を求める質問をした後は、Stop hook 等のフィードバックが入っても、それを承認の代わりとみなして commit・push などに進まないルールを禁止事項に追加。

## 2026-05-25

- **daily-xonepoint 下書きにネタ番号・分野タグ追加、outputs に neta_id 記録** — 下書きメールに `[分野]` と `[ネタ番号]`（`onePointNeta[番号]`）タグを追加し、cron 投稿時に `[ネタ番号]` を抽出して outputs シートの neta_id 列へ記録。投稿とネタの紐付けが辿れるようになった。[→報告書](../reports/20260525_xonepoint_neta_tags_and_neta_id_record/)
- **analyze-impression → ops_analyze-posts リネーム＋stats モード追加** — スキル名を `ops_` プレフィックスに統一し、`stats` モードで集計サマリー（投稿数・平均IMP・中央値・最大/最小・外れ値検出）のみ出力して終了する軽量モードを追加。STEP 3 の50行上限バグ（`A1:R50`→`A:R`）も修正。[→報告書](../reports/20260525_ops_analyze_posts_rename_stats_mode/)

## 2026-05-24

- **drive_put.sh 汎用化：任意フォルダ対応・MIME 自動判定** — 第2引数 `[folder-id]` を追加（省略時は drafts-note で後方互換）し、更新時の MIME を `file --mime-type -b` で自動判定。gws CLI 統一方針のため一時追加した `drive_upload.py` を削除。[→報告書](../reports/20260524_drive_put_generalization/)
- **drivemcp_get_remote.sh 追加：リモートセッション専用 Drive ダウンロード** — リモート環境（gws CLI 非使用）から Drive ファイルを取得する `drivemcp_get_remote.sh` と X アナリティクス CSV パーサー `fetch_x_analytics_csv.py` を新設。[→報告書](../reports/20260524_drivemcp_get_remote/)
- **visual_infographic：Drive アップロード完了後の Gmail 通知追加** — Step 7（ローカル削除）の後に `send_gmail.sh` で完了通知メールを送る Step 8 を追加。件名に日付・タイトル冒頭20字、本文に画像・MD の Drive URL と NotebookLM ノートブック ID を含む。
- **drive_put.sh：gws エラー時の空レスポンス JSON 例外修正** — gws コマンド失敗時に空レスポンスを JSON パースしようとして例外が発生する不具合を修正。
- **CLAUDE.md：Drive ファイルダウンロードのスクリプト使い分けルール追加** — ローカルは `drive_get.sh`、リモートは `drivemcp_get_remote.sh` を使い、Drive MCP ツール（base64 でトークン大量消費）はスクリプトで代替できる場合は使わないルールを明文化。[→報告書](../reports/20260524_claude_md_drive_download_rule/)

## 2026-05-23

- **daily-xonepoint P01化に字数項目追加・引き締めルール群を整備** — P01化スコアリングを5→6項目化し字数（200〜260字推奨/300字許容）を採点に統合。style-xonepoint.md に「削る対象優先度リスト」「専門単位の分数化」「詩的余韻型の締め」を新設し、writer-xonepoint に問答リズム・分数化＋体接続型の冒頭例・締めルール緩和を追加。[→報告書](../reports/20260523_xonepoint_length_item_and_tightening_rules/)
- **CLAUDE.md：スキル内 git 指示をセッション指示より優先するルール追加** — スキルに push 先ブランチや手順が明記されている場合は、セッション冒頭のシステム指示よりスキルの指示を優先するルールを Git ルールセクションに追加。[→報告書](../reports/20260523_claude_md_git_skill_priority/)
- **daily-xonepoint P01化チェックリスト追加・スコアリングループ新設** — style-xonepoint.md に冒頭フック5軸評価（直感的比較数字・パワーワードを必須）を含む P01化チェックリスト５項目を追加。daily-xonepoint STEP 3-2 に10段階採点＋5回反復ループ（全項目8点以上で合格）を実装。[→報告書](../reports/20260523_daily_xonepoint_p01_scoring_loop/)
- **daily-xonepoint メール件名・本文タグ改善** — STEP 4 の件名にトピック要約（10〜15字）を追加し、本文に `[最終原稿]`/`[投稿文]` の二タグ構造を導入。受信トレイでの内容判別と記録用・投稿用の分離が目的。
- **post_from_email.sh：検索をインボックス限定に変更** — `subject:XXX -label:投稿済み -is:draft` を `subject:XXX in:inbox -label:投稿済み` に変更。gws 認証切れによる「投稿対象なし」の調査過程で、アーカイブ済みメールへの誤投稿リスクも除去。
- **認証トークン切れ通知スクリプト新設** — `check_auth.sh` で gws・Drive・X API・LINE を毎日 11:00 JST にチェックし、異常時は LINE → Gmail の順で通知。`send_gmail_direct.py`（gws 非依存の Gmail API 送信）も追加。[→報告書](../reports/20260523_check_auth_notification/)
