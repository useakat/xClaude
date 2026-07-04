---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-07-04

- **mcp-gsheets のコールドインストールを SessionStart hook で事前ウォームし、routine 実行時の接続失敗を解消** — フレッシュなクラウドコンテナで npm install(~10秒)が MCP 接続タイムアウトに間に合わず routine で Sheets 系ツールが未接続になっていた事象を、SessionStart hook（リモート限定・同期実行）での事前 install（コンテナキャッシュへの焼き込み）で解消。`$HOME` 決め打ちパスの潜在バグも修正。[→報告書](../reports/20260704_mcp_gsheets_sessionstart_prewarm/)

---

## 2026-07-03

- **mcp-gsheets 起動を prefer-offline + 版固定にして再接続タイムアウト(-32000)を解消** — `npx -y mcp-gsheets@latest` が spawn/reconnect のたびにレジストリ問い合わせを強制し、不通時に60秒ハングして Claude Code 初期化タイムアウト(-32000)を招いていた。`npx --prefer-offline -y mcp-gsheets@1.8.1` に変更しキャッシュ優先起動化（レジストリ遮断下でも1.3秒で起動を確認）。[→報告書](../reports/20260703_mcp_gsheets_prefer_offline_pin/)
- **mcp-gsheets 起動スクリプトのパスを cwd 非依存の絶対パス化して projects/ 配下からの -32000 を解消** — `.mcp.json` の相対パス `scripts/mcp_gsheets_launch.sh` が、セッション cwd が `projects/w001` のとき解決できず即終了→再接続タイムアウト(-32000)を招いていた。`bash -c 'exec bash "$HOME/xClaude/scripts/mcp_gsheets_launch.sh"'` に変更し、どのディレクトリから起動しても繋がるよう是正。[→報告書](../reports/20260703_mcp_gsheets_launch_abspath/)
- **mcp-gsheets 起動を prefer-offline → ローカルインストール方式に変更（フレッシュコンテナの ETARGET 回避）** — フレッシュなクラウドコンテナで `--prefer-offline` が陳腐化した npm メタデータキャッシュを掴み、transitive 依存 `qs@^6.15.2` を解決できず `ETARGET` で install ごと失敗しサーバ未起動（"still connecting"）になっていた。バージョン固定のローカル prefix install＋`node` 直接起動に変更（初回のみ online 取得、以降は npm/レジストリ非依存で起動）。[→報告書](../reports/20260703_mcp_gsheets_local_install/)
- **X長文→note 導線の分割設計フロー（plan-xnote-funnel）を追加** — ネタ選定直後に「X長文の範囲／有料note の売り／セルフリプ文面」を一体で設計する上流スキルを新設し、共有ブリーフ `funnel-brief.md` を起点にする協調モードC を W001/W002 spec に追加（note 先行→X長文投稿の導線前提。既存 modeA/B は併存）。[→報告書](../reports/20260703_plan_xnote_funnel_split_design/)
- **z01 に固有名詞の平易化・一次情報主義・読みやすさ採点を追加** — z01 brand/spec と check-fact に、カタログ名・型番・専門単位の言い換え表、数値の一次情報主義（丸め値を鵜呑みにせず論文・計算で裏取り）、読みやすさ採点（「の」3連・無読点35字超・連体修飾2段超のシグナル）を追加。[→報告書](../reports/20260703_z01_plain_naming_primary_source/)

---

## 2026-07-02

- **z01 短文原稿作成をローカル cron → Claude routine（クラウド）へ移行** — 8:00 の下書き作成を routine（`trig_018f2gJJwYQ46UifKPtXjq27`・毎朝8:00 JST・Default 環境・opus・Gmail コネクタ）へ移行。クラウドでは mcp-gsheets（`.mcp.json`＋Default 環境の `GOOGLE_SERVICE_ACCOUNT_KEY`）でシート読取、Gmail 下書きは Gmail コネクタ経由。ローカル cron の `run_xshort_draft.sh` 行を撤去（スクリプトは残置）。[→報告書](../reports/20260702_z01_draft_cron_to_routine/)
- **z01 短文投稿ネタの重複回避（短文最終使用日列＋選定フィルタ）を追加** — noteNeta/newsTopics に「短文最終使用日」列を追加し、ステータス≠ボツかつ未使用/90日以上前の行のみを候補にネタ選定するよう変更。候補0件時は下書きを作らずネタ枯渇報告のみで終了。[→報告書](../reports/20260702_z01_xshort_neta_reuse_filter/)
- **W003 ネタ補充フローに追加日・分野の記入を必須化** — onePointNeta シートへのネタ補充時、追加日（J列）・分野（K列）の記入をハードゲート運用として必須化。`research-trivia` の追記手順と spec.md フロー1に明記。[→報告書](../reports/20260702_w003_neta_restock_date_field_required/)
- **research-trivia / research_trivia-source のネタ発掘条件を brand.md 冒頭フック5軸準拠に更新** — W003分野別パフォーマンス集計で物理が宇宙を上回ったことを受け、ネタ発掘条件に「直感的比較数字」「パワーワード」「体感優先の身近さ接続」を必須条件として追加。NotebookLM への実プロンプトも同期。[→報告書](../reports/20260702_trivia_hook_5axis_criteria/)
- **セクション画像ワークフローを design-brief フェーズ＋テンプレ合成方式に刷新** — planner が `image/plan.md`・`image/brand.md` を読んで案出し、imager を「image-plan_final 入力→design-brief 承認→プロンプト承認→生成」の3フェーズ化。図解は `infographic_template.md` を全体ベースに構成を `infographic_layout_*` から選択（合わなければ自由記述）。セクション画像用 `image/brand.md`・`plan.md` を整備し W002 で検証。[→報告書](../reports/20260702_section_image_designbrief_workflow/)
- **gws OAuth 再認証（2026-07-02）** — Drive/Gmail トークン失効（invalid_grant）のため再認証。`token_cache.json` をクリア。

---

## 2026-06-29

- **X短文投稿(z01)の outputs 記録に neta_id / thought_id を追加** — `record_output.py` を argparse 化し `--neta-id`/`--thought-id` を追加（outputs の D/E 列）。`post_from_email.sh` が投稿後に本文の `ソース: {シート}[{番号}]` を抽出し、thoughts→thought_id（ID）/ それ以外→neta_id（`noteNeta[33]` のシート名付き）で記録。`ソース:` 行が無い他フローは従来どおり。[→報告書](../reports/20260629_outputs_neta_thought_id/)
- **ワンポイント解説(W003)の X投稿時に outputs へ neta_id 記録を復活** — `post_from_email.sh` のネタ抽出を「`[ネタID]` タグ → 無ければ `ソース:` 行」の2マーカー対応に拡張。W003 下書きの `[ネタID]onePointNeta[{No}][/ネタID]` から neta_id＝`onePointNeta[N]`（過去形式と一致）を記録。z01 の挙動は不変。
- **mcp-gsheets 認証をラッパーで両対応化＋mcp__* 無効ルール整理** — 親プロセス混入の `GOOGLE_APPLICATION_CREDENTIALS`（`${HOME}` 付き不正パス）を Auth Library が掴み失敗する問題を、起動ラッパー `scripts/mcp_gsheets_launch.sh`（`unset`＋KEY 補完）＋`.mcp.json` 経由化で恒久対策。CLAUDE.md に再発防止を明記し、/doctor 指摘の無効 `mcp__*` を有効な `mcp__<server>__*` へ置換。[→報告書](../reports/20260629_mcp_gsheets_launcher_both_envs/)

---

## 2026-06-28

- **z01 ネタ選定を onePointNeta 除外・noteNeta:newsTopics:thoughts 2:2:1 加重に変更** — spec.md STEP 1 のソースシート選択を等確率4シートから 3 シートの重み付きランダム（`random.choices(weights=[2,2,1])`）に変更し、onePointNeta を選定対象外に。STEP 2 取得範囲テーブルからも onePointNeta 行を削除。[→報告書](../reports/20260628_z01_neta_selection_weighted/)
- **定時投稿に X短文フォールバックを追加＋21:00 に短文投稿 cron** — `post_from_email.sh` に終了コード（0=成功/20=対象なし/1=失敗）を導入し、6/12/17 のワンポイント・質問回答・X長文ラッパーを「対象なし(20)なら z01短文を代替投稿」に変更。crontab は z01専用投稿を 7/13/19 から 21:00 へ置換。[→報告書](../reports/20260628_post_fallback_xshort/)
- **z01 Gmail 下書きに `[最終原稿]` ブロックを追加** — 本文フォーマットで `[投稿文]` の前に `[最終原稿]…[/最終原稿]` を追加し、両ブロックに同一投稿文を入れる形に変更（`[最終原稿]`＝人間可読の確定稿、`[投稿文]`＝cron `extract_tag.py` 抽出用）。STEP 6・Verification も整合。spec.md のみの変更で `extract_tag.py` は無変更で安全。
- **z01 Gmail 下書きを「1投稿1回」に固定（修正しても作り直さない）** — 下書き作成後に本文修正が入っても新規作成・旧削除（作り直し）をしない運用に変更。`create_gmail_draft.sh` が更新不可で繰り返す churn を防止。spec.md の STEP 6・その他・Verification に明記。[→報告書](../reports/20260628_z01_gmail_draft_once/)

---

## 2026-06-27

- **z01 短文投稿の cron 自動化（投稿スクリプト新設・writer-xshort 周辺調整）** — `【X短文投稿】` 下書きを X 投稿する `scripts/run_xshort_post.sh`（`post_from_email.sh … z01 x_post_short.log`）を新設し crontab に毎日 7:00/13:00/19:00 を登録。下書き作成用 `run_xshort_draft.sh` も追加（手動用）、`writer-xshort` 説明文を「投稿せず下書き作成のみ」と正確化。[→報告書](../reports/20260627_z01_xshort_post_cron/)
- **z01 プロジェクト定義と汎用 writer-xpost スキルを追加** — 140字テキストのみ・高頻度でX反応を観測する z01（X短文投稿）プロジェクトを新設し、テーマ＋文字数範囲から「フォーカス→冒頭フック→本文」を全自動生成する汎用 writer `writer-xpost` を追加。z01 spec.md は本文生成を `/writer-xpost` に委譲。[→報告書](../reports/20260627_z01_writer_xpost_skill/)
- **W003 ネタ選定を「シートから5候補提示→ユーザー選択」に変更（日 mod 3 分野グループ廃止）** — spec.md フロー step 2 から `日 mod 3` の分野自動決定を廃止し、未使用ネタから分野を問わず PE01 に刺さる5候補を提示してユーザーが選ぶ方式に。補充トリガーも未使用10件未満→20件未満に変更。[→報告書](../reports/20260627_w003_neta_selection_user_choice/)
- **z01 下書き作成フェーズの cron 自動化（spec.md 準拠・毎朝8:00）** — `run_xshort_draft.sh` を z01 spec.md 準拠フロー（writer-xpost＋fact/brand チェック）に作り替え毎朝8:00 cron 登録。`settings.json` に Skill 3種＋`mcp__mcp-gsheets` を明示許可（`mcp__*` ワイルドカードが headless で効かない発見を含む）。[→報告書](../reports/20260627_z01_draft_cron_spec_flow/)
- **冒頭フック候補を全型×3案に是正（出力仕様の記載漏れ修正）** — フック候補が3案しか出ない不具合を、`writer-xpost`「## 出力」と z01 `spec.md` Naming に「hook-patterns.md の全型×各3案を全列挙（省略禁止）」を明記して修正（型数はハードコードせず相対表現）。[→報告書](../reports/20260627_writer_xpost_hook_count_fix/)

---

## 2026-06-26

- **writer-xshort スキルを追加** — 4シート（onePointNeta/noteNeta/newsTopics/thoughts）からランダムに1件ネタを選び、135-140字のX投稿文を生成してGmail下書きを作成する全自動スキル。ユーザー確認なし・`ソース: {シート名}[{ネタ番号}]` をメール本文に含め追跡可能。[→報告書](../reports/20260626_writer_xshort_skill/)
- **W003 output/draft ディレクトリの役割分担を spec.md に明文化** — `output/` は最終版3種のみ（index.md・採用図解PNG・生成プロンプト）、中間版はすべて `draft/` に置くルールを spec.md の Naming セクションと Verification に追記。既存投稿フォルダ（betelgeuse）の中間版も整理。[→報告書](../reports/20260626_w003_output_draft_role/)

---

## 2026-06-25

- **daily-xonepoint の Gmail 下書き作成を最終確定の承認後に移動** — Gmail 下書きを画像生成前の自動実行から「最終確定ゲート（STEP 7）でユーザー承認後に1回だけ作成」へ変更。`create_draft` が更新・削除不可で修正のたびに下書きが溜まる問題を解消。ステップ順を 6 画像→7 最終確定→8 Gmail→9 チャット履歴→10 Drive に再構成し spec.md も整合。[→報告書](../reports/20260625_daily_xonepoint_gmail_after_final_approval/)
- **W003 投稿フォルダ画像を Drive 保存・git 除外に移行** — 投稿フォルダの画像（draft・output の `*.png`）を git にコミットせず Drive＋ローカル保存に統一。`.gitignore` を `/projects/w003/**/*.png` に拡張、誤コミット済み画像を untrack、spec.md / daily-xonepoint に運用を明文化。リポジトリ肥大を防止。[→報告書](../reports/20260625_w003_post_images_drive_only/)
- **新規作業の開始前に git pull で最新化するルールを追加** — 複数環境から同じ master に push する運用で古い状態での作業・重複実装を防ぐため、CLAUDE.md の Git ルールに「作業開始前にまず git pull（未コミット変更は commit/stash 先行）」を明記。[→報告書](../reports/20260625_git_pull_before_new_work/)
- **daily-xonepoint のメール下書きを画像添付対応に修正** — SKILL STEP 8 が添付非対応の `mcp__claude_ai_Gmail__create_draft` を指定していたため下書きに画像が付かない不具合を、`create_gmail_draft.sh --attach` 方式へ変更して修正（spec.md の指定と整合）。[→報告書](../reports/20260625_daily_xonepoint_gmail_attach_fix/)
- **daily-xonepoint スキル・agent を非推奨化** — 制作フローの正本を `projects/w003/spec.md` に一本化。SKILL.md・agent 定義に非推奨バナーを追加し、metadata.yaml で「廃止・非推奨」カテゴリへ移動・Wiki 再生成。二重管理による不整合を解消。[→報告書](../reports/20260625_daily_xonepoint_deprecated/)

---

## 2026-06-22

- **W003 Gmail 下書きの本文フォーマットを明文化（`[投稿文]` 閉じタグ必須化）** — `[/投稿文]` 欠落で `extract_tag.py` が本文を抽出できず cron 投稿フローで投稿されない不具合を修正。原因は spec.md step 8 の本文フォーマット未定義。spec.md に `[投稿文]…[/投稿文]` 付きフォーマット（daily-xonepoint STEP 6 準拠）を明記し、`create_gmail_draft.sh --attach` 指定・Verification を開き/閉じ両タグ必須に変更。
