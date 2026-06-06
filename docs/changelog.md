---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

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
