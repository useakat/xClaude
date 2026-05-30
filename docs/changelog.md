---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-05-30

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

## 2026-05-22

- **persona シートへのペルソナ 19 件登録** — `persona/` フォルダの 01〜19 を Google Sheets の persona シート（SS2）に一括追加。P01〜P19 の persona_id を付与し、各ペルソナの primary pain_id を悩みセクションから推論してマッピング。[→報告書](../reports/20260522_persona_sheet_registration/)

## 2026-05-21

- **ops_post-reactions スキル改善：非フォロワー分類の精度向上** — リプライ本文・bio・公開指標をペルソナ分類入力に追加し、fetch_target_posts の date を ISO 形式で保存するよう修正。[→報告書](../reports/20260521_ops_post_reactions_improvement/)
- **style-xonepoint.md に「想定読者」セクション追加** — 反応感度分析（P01：反応感度 5.34・非フォロワー流入最多）に基づき P01（文系会社員）をメインターゲットとして明記。daily-xonepoint・writer-xonepoint の両スキルに反映。[→報告書](../reports/20260521_style_xonepoint_target_reader/)
- **draft_xstory スキル新設** — X長文ストーリー投稿（what_id W001）のネタ選定・原稿作成・ファクトチェック・トンマナチェック・Gmail下書き作成を自律実行するスキルを新設。[→報告書](../reports/20260521_draft_xstory_skill/)
- **フォロワー全件ペルソナ LLM 分類・ペルソナ19新設・classify-followers スキル追加** — 4183フォロワーをsubagent 28並列でLLM分類（2-Pass方式）。天体観測・星空実践派（P19）を新設し、差分更新対応の classify-followers スキルを追加。[→報告書](../reports/20260521_follower_persona_llm_classification/)
- **GetRepliesAndQuotes GAS スクリプト新設** — リプライ・引用RTを毎日収集し「リプ・引用一覧」シートに追記する GAS スクリプトを新設。アカウントID（@username）・アカウント名列も追加。[→報告書](../reports/20260521_get_replies_and_quotes_gas/)
- **record スキル改善：報告書作成時のセッション履歴自動保存** — `/record` の STEP 4.5 として `save_session_history.py` 変換・不要部分削除・相互リンク付与を追加。報告書と履歴ファイルのセットが自動で完結するように。[→報告書](../reports/20260521_record_skill_session_history/)
- **ops_post-reactions スキル新設** — 任意条件（キーワード・HOW_ID・期間）で X 投稿を抽出し、反応者を 19 ペルソナに分類して反応感度・密度・転換率を出力するスキルを新設。SA JWT + Sheets 直接呼び出しの事前スクリプト3本も追加。[→報告書](../reports/20260521_ops_post_reactions_skill/)

## 2026-05-20

- **Xペルソナ分析（リプ・新規フォロワーbio・引用RT3軸クロス分析）** — 17人体制のペルソナ群を実データで再構築。リプ47人・フォロワー3000人bio・引用RT2295人を分析し、248件の高反応アカリストを Sheets「高反応アカ」に書き込み。[→報告書](../reports/20260520_x_persona_analysis/)
- **「実は」ワンポイント解説投稿のXペルソナ分析** — 28本のワンポイント投稿への反応531人を分析。学生層(1.41x過剰)に届く知見を得てペルソナ18（物理に目覚めかけている学生）を新設。研究者層(1.76x)はplan.md方針に基づき追加見送り。[→報告書](../reports/20260520_jitsuwa_x_persona_analysis/)
- **save_session_history.py のパスを動的解決に修正** — ハードコードされた `/home/user/xClaude` 前提を撤廃し、`__file__` と `Path.home()` から REPO_ROOT・JSONL_DIR を動的に組み立てるよう変更。

## 2026-05-19

- **X投稿データ分析（4/20-5/17）と関連スキル群の改善** — 39投稿の事業導線分析を踏まえ、writer-xonepoint（文字数200-260字推奨・明示CTA禁止・締め強化）、writer-xstory（具体3点セット・note 誘導定型）、brand.md（反応誘導NG）、analyze-impression（導線メトリクス併行取得・異常パターン抽出）を改善し、writer-xqa（質問回答スキル）を新設。[→報告書](../reports/20260519_xpost_analysis_and_skill_improvements/)

## 2026-05-18

- **UpdateXAnalytics GAS 実装** — X アナリティクス CSV（Xanalytics/tmp）を読み込み X投稿一覧の詳細表示・リンククリック・フォロー増（AA:AC列）を更新する GAS 関数を新設し clasp でデプロイ。週次トリガー設定ヘルパーも実装。[→報告書](../reports/20260518_update_x_analytics_gas/)
- **ネタ選定に分野カテゴリ比率制御を追加** — onePointNeta シート K列「分野」を追加し、daily-xonepoint・writer-xonepoint で宇宙・物理 2/3・その他 1/3 の比率選定（日 mod 3 方式）を実装。[→報告書](../reports/20260518_xonepoint_category_ratio/)
- **save-session スキル新設** — セッション作業ログ（JSONL）を Markdown に変換して `docs/history/` に保存する `/save-session` スキルと `save_session_history.py` を新設。[→報告書](../reports/20260518_save_session_skill/)

## 2026-05-17

- **Drive MCP download_file_content のコスト検証** — download_file_content が base64（〜28,000トークン）をコンテキストに乗せること、Write ツール併用でトークン2倍・25分の迷走が起きることを実験で確認。スクリプト方式が唯一の実用解と結論。[→報告書](../reports/20260517_drive_mcp_download_cost/)
- **update-x-analytics 高速化リファクタリング** — Drive CSV 取得・Sheets B列取得・マッチングを全スクリプト化。LLM コンテキストを通じるデータ処理をゼロにし、ツール呼び出し 59回→4回・投稿数増加でも劣化しない構成に。[→報告書](../reports/20260517_update_x_analytics_refactoring/)
- **update-x-analytics サブエージェント新設** — X アナリティクス CSV（Drive の analytics_tmp）を読み込み、X投稿一覧シートの詳細表示・リンククリック・フォロー増を status ID で照合して一括更新するサブエージェントを新設。[→報告書](../reports/20260517_update_x_analytics_agent/)

## 2026-05-16

- **record-note-posts スキル新設** — note.com 記事統計（ビュー・スキ・文字数）を取得して Google Sheets「note投稿一覧」に記録・更新するスキルを新設。`v3/notes/{key}` から本文 HTML を取得し文字数カウントも実装。[→報告書](../reports/20260516_record_note_posts_skill/)
- **シート名「自分の投稿一覧」→「X投稿一覧」に変更** — Google Sheets のシート名改名に合わせ、`analyze-impression`・`analyze-x-posts`・`reporter-daily` の各 SKILL.md と `style-xonepoint.md`・Wiki スキル詳細ページを一括更新。
- **reporter-daily 特記事項の記載順を定義** — ワンポイント→質問→ストーリー→note→変更ログ→その他の順を SKILL.md に明記。週報・月報参照時に種別ごとに追いやすくなった。[→報告書](../reports/20260516_reporter_daily_note_order/)
- **style-reporter.md メトリクス表記をリポスト・リプに修正** — 数値表記の「引用」を「リポスト」に変更し「リプ」を追加。シートの列との対応（リツイート列→リポスト・ブックマーク列→ブクマ・リプライ列→リプ）を明記。v1.1→v1.2。
- **analyze-impression スキル新設** — X投稿のIMP分析と関連スキル改善提案を行う9STEPのスキルを新設。HOW_ID単位でフィルタしてパターン抽出・スキル/style修正案生成・承認後の自動編集まで実行する。[→報告書](../reports/20260516_analyze_impression_skill/)
- **writer-xonepoint/daily-xonepoint：日常入り口・具体的数字フックのルール化** — 実データ分析（5/1〜5/14のW003）で「日常の物を冒頭の入り口にした投稿」が高IMP、「宇宙固有現象が入り口の投稿」が低IMPと判明。フック制約・日常接続位置・ネタ補充条件を強化。[→報告書](../reports/20260515_xonepoint_impression_analysis/)
- **record_output.py に cron 用サービスアカウントファイル fallback 追加** — cron は `.bashrc` を読まないため `GOOGLE_SERVICE_ACCOUNT_KEY` が未設定になり Sheets 記録が失敗していた。環境変数がない場合に `gcp/` の JSON ファイルを直接読む fallback を追加。[→報告書](../reports/20260516_record_output_cron_fallback/)
- **CLAUDE.md：新規スキル作成時の metadata.yaml 追記ルール追加** — Wiki 自動更新を確実に動かすため、スキル新設時に `metadata.yaml` への追記を必須とするルールを実装ルールセクションに追加。[→報告書](../reports/20260516_claude_md_metadata_rule/)
- **thoughts シート新設・思想リスト 13 件を登録** — 発信時に引用・接続する思想を SS1 の `thoughts` シートで構造化管理。CLAUDE.md 内の思想群を分析・整理し、X発信に使える 13 件を選別して T001〜T013 として登録。[→報告書](../reports/20260516_thoughts_sheet/)
- **get_gmail_body.sh：メール本文 CRLF 正規化** — Gmail 本文の `\r\n`（Windows改行）を `\n` に変換。未変換のまま X 投稿していたため空白行の位置がメール原稿とずれていた問題を修正。
- **brand.md 説明文の簡略化** — よーんの説明文から「天体の魅力や宇宙探査の」を削除し「面白さを伝える発信者」に簡潔化。
- **Wiki：変更報告書をサイドバーに表示** — `astro.config.mjs` の「報告書」セクションを `reports/` 全体の `autogenerate` に変更。`template.md` を `sidebar: hidden` で非表示化。

## 2026-05-15

- **record_output.py を Google Sheets 書き込みに移行** — X投稿記録先をローカル CSV から Google Sheets の outputs シートに切り替え。gspread + サービスアカウント認証で実装し、既存18行も転記済み。[→報告書](../reports/20260515_record_output_sheets_migration/)
- **brand.md の想定読者・締めルール削除・フォント定義追加** — 想定読者セクションと締めのルールを削除し、フォント指定（Noto Sans JP Black）を追加。
- **writer-xstory スキル改善：フック・構成・完結性ルール追加** — フック2文構成・ブロック空行区切り・ストーリー完結・教訓は末尾集約の4ルールを追記。SOHOの長文X投稿の初稿→最終原稿の差分を学習として反映。[→報告書](../reports/20260515_writer_xstory_hook_rules/)

## 2026-05-14

- **reporter-daily STEP 5 に保存前の自己チェック追加** — 特記事項を保存する前に「専門用語チェック」「何を→どう変わるかチェック」「読者想定チェック」の3項目を必ず通過させる手順を SKILL.md に追加し、style ルールの取りこぼしを構造的に防止。[→報告書](../reports/20260514_reporter_daily_self_check/)
- **mcp__github__push_files の PreToolUse リマインドフック追加** — `git_guard.py` のブロック回避として `push_files` を使っていないかをツール実行直前に確認するリマインドを `.claude/settings.json` に追加。
- **git_guard.py 削除・リモートセッションの git 操作制限を全廃** — `git_guard.py` を削除し PreToolUse フックを全削除。リモートセッションでは feature ブランチで作業・merge 段階で精査する方針に切り替え。[→報告書](../reports/20260514_git_guard_removal/)
- **【X長文】メール→X投稿の自動化追加** — `【X長文】` 件名のメールを毎日17時にXへ自動投稿する cron ジョブを追加。既存の `post_from_email.sh` をそのまま流用し、HOW_ID=W001 で記録。[→報告書](../reports/20260514_xlong_post_automation/)
- **発信 plan.md の新設・CLAUDE.md への参照ルール追加** — 発信の目的・ターゲット・価値提供・成功条件を `plan.md` に定義し、コンテンツ制作前の参照を CLAUDE.md に義務化。[→報告書](../reports/20260514_plan_md_and_claude_md/)

## 2026-05-13

- **commit_and_sync.sh を GitHub MCP プッシュ方式に移行** — master へのローカルプロキシ経由 push が 403 で失敗するため、スクリプトをローカルコミットのみに変更し、push は `mcp__github__push_files` で直接行う方式に移行。reporter・record・update-permissions の5スキルの Git ステップを更新。[→報告書](../reports/20260513_commit_and_sync_github_mcp/)
- **CLAUDE.md git フックブロック回避禁止ルール追加** — `git_guard.py` などのフックによるブロックを勝手に回避しないよう禁止事項に明記。回避が必要な場合は必ずよーんに許可を求めてから行う。

## 2026-05-11

- **cron メール投稿スクリプト：複数メール溜まり時に1件のみ投稿するよう修正** — 投稿成功後に `break` を追加し、未処理メールが複数あっても最古の1件のみ投稿して終了。質問回答・ワンポイント解説の両 cron に適用。[→報告書](../reports/20260511_post_from_email_single_post/)

## 2026-05-09

- **Wiki スキル一覧の自動更新システム実装** — スキル追加時に Wiki が自動更新されるシステムを構築。metadata.yaml でスキル ↔ カテゴリを管理、post-commit フックで自動生成。[→報告書](../reports/20260509_wiki_skills_auto_update/)
- **check-fact スキル改良：完全性チェック機能追加** — テーマの背景知識から説明の不足要素を自動検出し追加文案を生成するステップを追加。ファクトチェック前に説明の完全性を確保。[→報告書](../reports/20260509_check_fact_completeness_check/)
- **daily-xonepoint スキル改良：ファイル保存時の git commit & push 削除** — STEP 4 の自動 git コミット処理を削除。下書き作成段階での git 記録は不要と判断。[→報告書](../reports/20260509_daily_xonepoint_remove_git_commit/)
- **mond-letter-reply スキル新設・ローカル化** — mond.how レター質問を Claude Opus で自動回答し Gmail 下書きを作成。gws CLI でラベル付与・アーカイブ、ローカル cron（6時間ごと）で定期実行。[→報告書](../reports/20260509_mond_letter_reply/)
- **brand.md 新設・スタイルガイド差分化** — 全スタイルファイルの共通定義（人格・想定読者・言葉遣い・NG）を `brand.md` に集約し、各 style ファイルをフォーマット固有の差分のみに簡略化。[→報告書](../reports/20260509_brand_md_and_style_diff/)
- **Wiki スキル詳細ページの自動生成と index.md のリンク化** — 全26スキルの詳細ページを自動生成し、index.md のスキル名をクリック可能なリンクに変更。ユーザーが各スキルの SKILL.md 内容を閲覧できるよう整備。[→報告書](../reports/20260509_wiki_skill_detail_pages/)
- **analyze-target スキル改良：Google Sheets 自動追記機能追加** — 複数候補を「スコア付き」で提示し、ユーザーの選択後に Sheets へ自動追記する機能を追加。手動貼り付けの廃止で運用負荷を軽減。[→報告書](../reports/20260509_analyze_target_sheets_auto_append/)

## 2026-05-07

- **style-xonepoint.md 二人称を「僕ら」に変更** — 2人称「あなた」をなるべく使わず「僕ら」で読者を包む表現に統一。関連する例文・締め言葉サンプルも更新。
- **reporter-daily 特記事項生成の精度向上（報告書読み込み追加）** — STEP 4 を2段階に分割し、changelog リンク先の報告書ファイルも読み込んで特記事項生成に活用するよう改善。[→報告書](../reports/20260507_reporter_daily_report_reading/)
- **reporter-daily 文体ルールの style ファイル外部化** — SKILL.md STEP 5 の直書き文体ルールを `style/style-reporter.md` に切り出し、changelog 関連の特記事項を「具体性・明示性・能動性」原則で書くルールを追加。[→報告書](../reports/20260507_reporter_daily_style_externalization/)
- **CLAUDE.md commit前ユーザー確認の必須化** — Git ルールに「内容をユーザーに提示して確認を得てから commit & push する」を明記。

## 2026-05-06

- **daily-xonepoint へのトンマナ調整ステップ追加** — STEP 3 にトンマナ調整（3-2）を追加。ファクトチェック後に `style-xonepoint.md` を参照し文体・口調のみ調整して【最終原稿】を確定。[→報告書](../reports/20260506_daily_xonepoint_tone_check/)
- **check-fact GPT スコア採点・修正文案生成の追加** — GPT にスコア（0〜100）採点と修正文案生成を担わせ、ループ終了条件を「スコア 95 以上」に変更。[→報告書](../reports/20260506_check_fact_gpt_scoring/)
- **daily-xonepoint メール下書きにチェックサマリーを追加** — STEP 3 でサマリーを記憶し、メール本文を「ファイル内容 → チェックサマリー → 投稿文」の順に変更。件名の時刻も JST 取得に修正。[→報告書](../reports/20260506_daily_xonepoint_check_summary/)
- **check-fact の openai モジュール依存を curl に変更** — `openai` パッケージ依存を排除し `curl` で直接 API を叩く形に書き直し。remote 環境でも動作するよう修正。[→報告書](../reports/20260506_check_fact_curl_migration/)
- **git_guard.py のガードロジック反転** — `CLAUDE_CODE_REMOTE != true` から `CLAUDE_CODE_LOCAL == true` の場合のみ通す設計に変更。デフォルトブロックで想定外セッションのスルーを防止。[→報告書](../reports/20260506_git_guard_logic_inversion/)
- **check-fact への GPT ファクトチェック統合** — GPT-5.4-mini によるファクトチェックを統合し、環境変数・空引数の不具合を修正。[→報告書](../reports/20260506_check_fact_gpt_integration/)
- **CLAUDE.md への振る舞いルール追加** — Plan mode 中は計画提示で止まるルール・ユーザーの判断を待ってから実行するルールを追加。[→報告書](../reports/20260506_claude_md_behavior_rules/)
- **settings.local.json への書き込みを全セッションで禁止** — `settings.json` の `permissions.deny` に Write/Edit ルールを追加し、ローカルエージェントによる意図しない上書きを防止。[→報告書](../reports/20260506_settings_local_deny/)

## 2026-05-05

- **Wiki 日報カレンダー表示と表示修正** — 日報一覧を月カレンダー形式（`DailyCalendar.astro`）に変更。改行・title frontmatter・CI ビルド・サイドバー順序の不具合を一連で修正。
- **daily-xonepoint の子スキル隔離（context:fork 対応）** — `writer-xonepoint`・`check-fact` に `context: fork` を追加して子スキルの完了マーカーが親に漏れる構造バグを修正。STEP 2 を `writer-xonepoint` 委譲に変更して保守性を向上。[→報告書](../reports/20260505_daily_xonepoint_context_fork/)
- **reporter-monthly のアウトプット品質向上** — 月報生成に「量・粒度のルール」「戦略転換の判定」を追加し、データ部のマネタイズ欄を `0円` ベースで埋まるように修正。書き直しの手間を削減。[→報告書](../reports/20260505_reporter_monthly_quality_improvement/)
- **reporter-daily の特記事項生成ルール強化** — 投稿の特記事項を「[投稿種類]投稿（[テーマ]）：[数値]。[一言]」のフォーマットに定型化。数値への自分の感想を禁止し、用語を「投稿」に統一、`RT→引用`・`BM→ブクマ` に変更。[→報告書](../reports/20260505_reporter_daily_quality_improvement/)
- **commit_and_sync.sh の permissions パターン修正** — `Bash($(git ...))` 形式のパターン内の `)` がパーサーを早期終了させる問題を `Bash(*commit_and_sync.sh *)` に変更して回避。[→報告書](../reports/20260505_commit_and_sync_permissions_fix/)

## 2026-05-04

- **mcp-gsheets 起動設定の修正** — `--stdio` 追加・settings.json 経由の試行と .mcp.json への差し戻し・auth env を `GOOGLE_SERVICE_ACCOUNT_KEY` のみに統一する一連の修正。[→報告書](../reports/20260504_mcp_gsheets_startup_fix/)
- **reporter-daily スキル改善** — デフォルトを前日に変更・gws CLI から mcp-gsheets に移行・日次記録シートの読み込みを最新10行に限定。
- **cron X 投稿からの下書き除外** — `post_from_email.sh` の Gmail 検索クエリに `-is:draft` を追加し、下書きメールが投稿対象になる不具合を修正。
- **CLAUDE.md ファイル削除ルール変更** — 「ファイルを削除しない」から「削除する場合はよーんに確認する」に緩和。
- **reporter スキル UX 改嘅（完了後表示・特記事項ルール整備）** — daily/weekly/monthly 全スキルの完了後に生成ファイルを画面表示。reporter-daily の特記事項からフォロワー増減・`[開発]` 表記を廃止し、変更ログの要約を運用視点に変更。[→報告書](../reports/20260504_reporter_ux_improvements/)
- **remote session での docs/reports/ push 許可** — `git_guard.py` を新設し、ステージ済みファイルが `docs/reports/` 配下のみなら remote でも commit・push を通す。フックもスクリプト外部化・動的パス解決に変更。[→報告書](../reports/20260504_remote_reports_push/)

## 2026-05-03

- **mcp-gsheets の cloud session 対応** — `.mcp.json` を新設し command 型で定義、supergateway 不使用の構成に統一。認証は `GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数で渡す。[→報告書](../reports/20260503_mcp_gsheets_cloud_session/)
- **settings.local.json の git 管理除外** — `settings.local.json` を untrack し `.gitignore` の誤記（`settings.json` を除外していた）を修正。
- **remote session での git 書き込み操作ブロック** — `PreToolUse` フックで `CLAUDE_CODE_REMOTE=true` 時に git push / commit / ブランチ作成をブロック。[→報告書](../reports/20260503_remote_git_block/)

- **reporter スキル追加** — 日報・週報・月報を自動作成する `reporter-daily/weekly/monthly` の3スキルを新設。gws CLI で Sheets データを取得し AI 生成で記録。[→報告書](../reports/20260503_reporter_skills/)
- **/record スキル追加・CLAUDE.md 記録ルール簡潔化** — changelog と git log を照合して未記録変更を提案・記録する `/record` スキルを新設し、CLAUDE.md の記録手順をスキルに委譲。[→報告書](../reports/20260503_record_skill/)
- **コミット前確認フックの blocking 化** — `systemMessage` 通知方式から `decision:block` 強制停止＋ `[pre-commit-ok]` bypass トークン方式に変更し、確認漏れを構造的に防止。[→報告書](../reports/20260503_precommit_hook_blocking/)
- **コミット前フック検知対象の拡張** — `commit_and_sync.sh` 経由のコミットでもフックが発動するよう `settings.json` の hook 条件を修正。
- **変更ログ形式の整備** — 変更ログのエントリを日付セクション内の箇条書き形式に統一し、CLAUDE.md のルールも更新。
- **記録不要条件の明文化** — `permissions.allow` への追記のみのコミットは記録不要という例外ルールを CLAUDE.md に追加。
- **/update-permissions スキル追加・コミット前フック廃止** — blocking フックと bypass トークンを廃止し、`/update-permissions` スキルで任意のタイミングに手動で permissions.allow を更新する運用に変更。[→報告書](../reports/20260503_update_permissions_skill/)
- **/record スキル候補表示の改嘅** — 変更ログ候補に「関連する過去の変更」フィールドを追加し、選択メッセージを肯定形に変更。[→報告書](../reports/20260503_record_skill_improvement/)
- **daily-xonepoint メール下書き作成の MCP 化** — gws CLI がエージェント環境で使えないため STEP 5 を `mcp__claude_ai_Gmail__create_draft` に切り替え。[→報告書](../reports/20260503_daily_xonepoint_mcp_gmail/)
- **database CSV → Google Sheets 移行** — 8スキルの CSV 読み書きを mcp-gsheets ツールに書き換え、廃止スクリプトを `unused-scripts/` へ移動、SS1 に outputs シートを新設。[→報告書](../reports/20260503_database_csv_to_sheets_migration/)
- **mcp-gsheets ローカル認証設定** — `.mcp.json` に `GOOGLE_APPLICATION_CREDENTIALS` を追加し、ローカルセッションでもサービスアカウントファイルで認証可能に。
- **Wiki データベース・アーキテクチャページ更新** — `docs/database.md` を全シートの列構成・操作リファレンス形式に書き直し、`docs/architecture.md` のフロー図と認証セクションを Sheets 移行後の構成に更新。

## 2026-05-02

- **Wiki システム構築** — Starlight + GitHub Pages で Wiki 新設。`docs/` がソース、`starlight/` がビルド設定。[→報告書](../reports/20260502_wiki_setup/)
- **X ワンポイント投稿スタイルガイド作成** — 実投稱．0件を分析、13の観点で定義した `style/style-xonepoint.md` を作成。[→報告書](../reports/20260502_style_xonepoint/)
- **writer-xonepoint・daily-xonepoint スタイルガイド参照化** — 両スキルから `style/style-xonepoint.md` を参照するよう変更。[→報告書](../reports/20260502_skill_style_reference/)
- **投稿締め言葉ルールの追加** — X ワンポイント投稿の末尾を「読者の日常生活につながる1文」で締めるルールを強制。[→報告書](../reports/20260502_closing_rule/)
- **Google サービス連携・スクリプト化ルールの追加** — gws CLI 統一とスクリプト化優先の原則を CLAUDE.md に明文化。[→報告書](../reports/20260502_implementation_rules/)
- **報告書・変更ログ運用フローの整備** — 変更ログと報告書の1対1対応構造を設計。テンプレート作成・CLAUDE.md にルール追加。[→報告書](../reports/20260502_reporting_workflow/)
- **daily-xonepoint 自動化改嘅** — STEP 3 を `/check-fact` に変更、STEP 5 のメール作成を gws CLI スクリプトに変更。[→報告書](../reports/20260502_daily_xonepoint_improvement/)
- **git commit 前の確認フック追加** — `PreToolUse` フックで `git commit` 実行前に settings.json 確認を自動挿入。[→報告書](../reports/20260502_precommit_hook/)
