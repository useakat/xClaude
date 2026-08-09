---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-08-09

- **W002 に初稿精度向上ルールを追加＋check-reader に構成モード（--plan）を新設** — ケプラー記事の初稿→最終稿の差分分析（薄いH2の統合・難所の付録化・脇道の技術詳細削除が執筆後に発生）に基づく再発防止。w002 spec に構成フェーズ共通ルール（難所マップ・600字未満H2統合チェック）と執筆前ルール（事実の採用マーク・回答割り付け・図番号登場順）を追加。難所の列挙は `/check-reader --plan`（新設）で plan.md の読者ペルソナになりきった読者役に構成案を読ませて出させる。[→報告書](../reports/20260809_w002_first_draft_quality_rules/)
- **NotebookLM ブラウザ内RPCブリッジに `ask`（ノートへの質問）を追加** — 8/6 の復旧では Deep Research のみ通していたブリッジに、集めたソースに基づく質問応答を追加。`ChatAPI` は `batchexecute` ではなく別エンドポイントを `get_http_client()` から直接叩くため、httpx 互換の最小クラスで HTTP 層もブリッジ経由に差し替え、旧ドメイン宛URLを新ドメインへ書き換えて CORS を回避した。クジラのノート（ソース64件）でトリビア抽出と追加質問への回答を確認。[→報告書](../reports/20260809_notebooklm_bridge_ask_command/)
- **W002 の画像生成フローを Lovart スキルに移行（ケプラー記事で初運用）** — 図解は NotebookLM・イメージ／サムネはユーザーが外部AIで生成、と分かれていた w002 spec を `/lovart` に一本化（画像種類の注記・フロー12-(c)・フロー13-4 の3箇所）。参照画像を `upload`→`--attachments` で渡して実機形状を再現、`--thread-id` で修正を反復する手順も明記。8/4 の W001 版に続く W002 版。[→報告書](../reports/20260809_w002_lovart_image_generation/)

---

## 2026-08-08

- **Threads転載の publish 一時エラー（素材が見つからない）をリトライするよう改修** — X投稿直後の転載で、画像コンテナ作成直後の整合性遅延により publish が code24/subcode4279009「素材が見つからない」で失敗し Threads 転載が落ちていた（8/7 朝のワンポイント）。`post_threads.py` に publish の一時エラー時リトライ（8秒×最大5回）＋FINISHED後3秒バッファを追加。8/7分は手動再転載済み。[→報告書](../reports/20260808_threads_publish_retry/)
- **素朴な読者チェック `/check-reader` を新設（story-check 7項目化・phrasebook 追記）** — check-fact・check-brand を1発合格した Z01 原稿にユーザー推敲8往復が必要だった件の再発防止。制作文脈を知らない読者役サブエージェントに原稿だけを読ませ「疑問・誤解した映像・フック未回収」を検出する `/check-reader` を新設し z01 spec の STEP 3.7 に組み込み。story-check.md に「フックの回収」「語の重複」を追加して7項目化（W001/W002 の採点にも反映）、z01-phrasebook.md に「危機・運命の描写」カテゴリを追記。[→報告書](../reports/20260808_check_reader_skill_story_check7/)

---

## 2026-08-07

- **X アナリティクス月次CSVアップロードの月次リマインド routine を新設** — マネタイズ月報の note 導線（CTR/CVR）に必要な X アナリティクスCSVのアップ忘れ防止。毎月1日9:00 JST に Drive を検索し、前月分CSV（`account_analytics_content_{前月}`）が無ければ useakat@gmail.com にリマインドメール送信、あればナガらない。cloud routine（`trig_01WhHLFmPuok7f4idXnbaPdY`・Default/sonnet-5・Drive＋Gmailコネクタ）。[→報告書](../reports/20260807_x_analytics_csv_reminder_routine/)

---

## 2026-08-06

- **マネタイズ月報スキル `reporter-monetization` を新設** — X・threads の型別成績（3ヶ月推移）／note マネタイズと X・threads→note 導線（CTR/CVR/売上・note_url 付き全投稿対象）／来月マネタイズ計画案の3本柱を月次で出す新スキル。集計は `monetization_metrics.py`（outputs.what_id×各一覧を突合、SA認証・IPv4・読取専用）に集約し、スキルは JSON をもとに `docs/reports/monetization/` に生成（手動実行）。2026-07 note売上 3,430円が既存月報と一致で検算。[→報告書](../reports/20260806_reporter_monetization_skill/)
- **マネタイズ月報を実データ検証で改修（threads型解決・中央値・導線をセルフリプclick基準に）＋7月試作完成** — 試作しながら4点改修：threads型を outputs の threads行（permalink→x_url→what_id）で解決（0→26本）／型別成績に IMP合計・中央値追加＋3ヶ月推移を合計表示／note導線を親ポスト紐付けのセルフリプ行クリックで計測／7月Xアナリティクス取込＋ボイジャー本体 note_url バックフィルで導線を CTR0.54%・CVR0.48%・売上2,940円 まで実数化。[→報告書](../reports/20260806_monetization_metrics_refinement/)
- **Z01 固有名詞ルールを「記号か物語の登場人物か」で判定するよう改訂** — 判定基準を「読者が絵を描けない固有名詞は言い換える」→「**記号のような固有名詞**（カタログ名・型番・観測装置の識別子・専門単位）は言い換える」に統一。あわせて探査機・宇宙船・人物など**物語の主人公となる固有名詞は初出時の一言補足付きでそのまま使ってよい**という例外を新設し、brand.md（言い換えセクション・Do Not・採点基準 項目2）と spec.md（制作ルール・Verification）の計7箇所を揃えた。[→報告書](../reports/20260806_z01_proper_noun_protagonist_exception/)
- **NotebookLM の Gemini 移行後の認証断をブラウザ内 RPC 方式で復旧（cookie 持ち出し廃止）** — `notebook.google.com` 移行とデバイスバインドで `storage_state` に `__Secure-1PSIDTS` が書き出されなくなり、cookie 再生方式が signin に飛ぶようになった。cookie の持ち出しをやめ、Windows のログイン済み Chrome 内から `batchexecute` を呼ぶ方式へ変更（RPC の符号化/復号・解析は `vendor/notebooklm` を再利用し通信層のみ差し替え）。ヘッドレス＋ssh で完走するため RDP 不要。ノート128件取得・Deep Research でソース64件取り込みを確認。[→報告書](../reports/20260806_notebooklm_browser_rpc_recovery/)

---

## 2026-08-04

- **lovart スキルによる画像生成を W001 制作フローに導入（海王星販促投稿で初運用）** — サムネ生成を「プロンプトを渡して外部で生成」から「Claude が lovart で生成し対話で詰める」フローへ実質移行。史実準拠のため実機写真（CC0）を参考画像に添付し、肖像が残る人物は完全シルエット固定と design-brief に明文化。6回の改稿で最終版を確定し、`.gitignore` の画像除外を jpg にも拡張した。[→報告書](../reports/20260804_lovart_image_generation_w001/)

---

## 2026-08-01

- **reporter-daily の日報全文表示を STEP 9.5 に格上げ（省略防止の再修正）** — 7/29 の「完了報告2ステップ化」後も本文表示が省略されたため、指示強化ではなく実行位置を変える対策に切り替え。全文表示をファイル保存直後・commit 前の正式な STEP 9.5 として新設し、末尾の完了報告は飛ばした場合の保険文言に簡素化した。[→報告書](../reports/20260801_reporter_daily_step95_fulltext_display/)

---

## 2026-07-30

- **w001/w002 に Drive フォルダ一式アップロード工程を追加し画像を Drive-only 化（w003 方式に統一）** — w001 spec フロー15／w002 spec フロー16 に `drive_put_folder.sh` によるフォルダ丸ごとアップロード（構造再現・冪等）を新設し、`.gitignore` に `/projects/w001|w002/**/*.png` を追加して追跡中の png 39件を git 追跡解除（リポジトリ肥大防止）。過去フォルダ8件（w001×4・w002×4）を Drive `xClaude/projects/` 配下へ遡及アップロード済み。[→報告書](../reports/20260730_w001_w002_drive_folder_upload/)
- **GAS の 3M累計インプ記入先を AA列に修正し、clasp を useakat 再認証で本番デプロイ** — 「日次記録」に「週間インプ」列が挿入され 3M累計インプが Z(26)→AA(27) にシフト。`DailyMetricsRecord.js` の `IMPRESSIONS_3M` を修正し `clasp push` で反映。clasp が別アカウント（kitanagasekids）でログイン中だったため useakat へ再ログイン、認証は global を復元し `gas/.clasprc.json` へ退避、`.clasprc.json` を gitignore 化。[→報告書](../reports/20260730_gas_3m_column_fix_clasp_deploy/)
- **週報に投稿型ごとのインプレッション合計を追加（reporter-weekly）** — 週報の「やったこと」で投稿を型（ワンポイント解説・ストーリー長文等）ごとに集約し、見出し行に本数とインプ合計（threads は views 表記）を書くフォーマットに変更。日報が無い日の投稿は数値不明として合計から除外し明記する。7/20週（2026-W30）に適用済み（SKILL.md の PLACEHOLDER 誤 push は復元済み）。[→報告書](../reports/20260730_reporter_weekly_type_impressions/)

---

## 2026-07-29

- **reporter-daily の完了報告に本文表示ステップを必須化＋署名警告への反応を完全禁止** — 日報保存後にチャットへ本文を表示せず要約だけ出してしまう拜けと、コミット署名警告に毎回一言返信してしまう問題を修正。完了報告を「本文表示→サマリー」の順序厳守２ステップに変更し、署名警告ルールに確認メッセージ自体の出力禁止を明記した。[→報告書](../reports/20260729_reporter_daily_display_signature_fix/)

---

## 2026-07-25

- **research 系スキルを sheets_values.py に移行＋open_by_key に 404 リトライ追加（append 経路の本番書き込み初テスト完了）** — 7/18 の routine Sheets スクリプト移行の続編。`research-trivia` / `research-note-projectx` の `sheets_get_values` / `sheets_append_values` 呼び出しを Bash 経由の `scripts/sheets_values.py` に置換し、両スキル冒頭に「MCP ツールは使わない」方針ブロックを追加。あわせてセッション初回コールドスタート時の 404（`SpreadsheetNotFound`）を緪和する 1 秒後 1 回リトライ＋詳細ログを `open_by_key` に追加。7/18 で保留となっていた append の本番書き込みも試験行で検証し、 11 セル完全一致で書き込めることを確認。[→報告書](../reports/20260725_research_skills_sheets_migration/)
- **日次記録シート V列に Threads フォロワ数を毎朝自動記録** — GAS が毎朝書く「日次記録」シートで空だった V列「threads フォロワ数」を、ローカル python（`record_threads_followers.py` 新規）が Threads insights の `followers_count` を取得して前日行に記録（IPv4固定・SA認証・冪等・cron 5:30）。GAS トークンを持たせず自動更新トークンを使う保守性重視の選択。GAS トリガーは 5:00 に前倒し。[→報告書](../reports/20260725_threads_followers_daily_record/)
- **日報を媒体別４セクション構成に変更（reporter-daily）** — 番号付き構成（①ポスト数〜④特記事項）をやめ、`note` / `X` / `threads` / `特記事項`の媒体別に再編。各媒体の件数の下に投稿の内訳を入れ子で並べる形にし、これまで出せなかった threads の投稿件数を Threads投稿一覧シートの当日行数から算出するようにした。入れ子は全角スペース・箇条書き間は空行という Wiki 描画の制約もルール化した。[→報告書](../reports/20260725_reporter_daily_media_sections/)
- **/record にプッシュ後の反映確認ステップを追加（変更ログのエントリ消失対策）** — 別セッションが同じ日付セクションを編集したマージで、push 済みの変更ログ1行だけが master から消え、報告書がどこからもリンクされていない孤立状態になった。push の成功は master に載っていることを保証しないため、STEP 6.5 として「master を fetch し直してエントリと報告書の存在を確認、欠けていたら復元」を追加。STEP 5 冒頭にも編集前の最新化を明記。[→報告書](../reports/20260725_record_push_verification/)

---

## 2026-07-24

- **公開済み note 記事の定期販促用 X長文の介よしを追加（W001 モードB再定義＋セルフリプ cron 自動投稿＋note_url 自動記録）** — モードBを「2〜3ヶ月おきの繰り返し販促」前提に再定義（note投稿一覧からURL取得／ブリーフは「note の売り」だけ継承／アウトプットの note_url 紐付けで過去投稿と重複しないフォーカスを選ぶ／セルフリプ毎回新規）。メールに `[リプ]` タグを追加し cron が本体投稿直後にセルフリプを自動投稿、`[note_url]` タグ→outputs F列自動記録で Xnote導線記録に自動反映。モードCは note 公開直後の初回専用に。[→報告書](../reports/20260724_w001_note_promo_mode/)
- **X短文投稿の cron 実行時刻を 21 時→20 時に変更（コメント同期）** — `scripts/run_xshort_post.sh` のヘッダコメントを crontab 本体（20:00 実行）と揃えるためのメンテナンス修正。
- **gws OAuth 再認証（2026-07-24・本番公開化＋spreadsheets スコープ追加）** — Drive/Gmail に加え `spreadsheets` スコープ入りで本番公開版クライアントに再認証（`token_cache.json` クリア済み）。

---

## 2026-07-21

- **cron の Threads 投稿を複数画像（カルーセル）対応にし、record_output.py の記録ハングを再修正** — 複数画像の投稿が「画像URL連結」で全失敗していた不具合を、`post_threads.py` のカルーセル対応（2枚以上→item container→CAROUSEL→publish、上限20枚・セルフリプも対応）で解消。あわせて `record_output.py` の IPv4 固定パッチが x_url 対応リファクタ（`9be5617`）で消失し記録ハングが再発していたのを再追加（60秒超→1.3秒）。動物园4枚画像の実投稿＋記録完走を確認。[→報告書](../reports/20260721_threads_carousel_and_record_ipv4/)
- **X投稿をThreadsにも自動転載し、下書き投稿を「X投稿が無い時だけ」のフォールバックに変更** — X投稿cron（onepoint/question/xlong/xshort）が投稿成功後に同じ本文・画像・セルフリプをそのまま Threads に転載（`MIRROR_THREADS=1`・非致命）。画像は投稿直後に pbs.twimg.com を syndication API（`fetch_tweet_media.py` 新規）で取得。独立していた `run_threads_post.sh`（6/17/20時）cron を削除し、各Xラッパーで「X投稿ゼロ時のみ下書きをフォールバック投稿」に変更。[→報告書](../reports/20260721_x_to_threads_mirror_integration/)

---

## 2026-07-20

- **ファクトチェックに「ファクト抽出→項目別検証」工程を追加（check-fact-lim / check-fact）** — 本文を丸ごと検証器に渡す方式は網羅性がモデル任せで見落としが起きやすいため、本文から「1主張=1事実」を抽出し各項目を ○/×/要確認 で個別照合する STEP 1.5 を両スキルに新設（`.py` 非編集）。W001ボイジャー記事で17項目全て○/100点を確認。[→報告書](../reports/20260720_factcheck_claim_extraction/)
- **X長文下書きの件名を【Xストーリー】→【X長文】に統一（cron 検索キーワードとの不一致を是正）** — 生成側（`projects/w001/spec.md`・`draft_xstory` スキル）が `【Xストーリー】`、稼働中の cron（`run_xlong_post.sh`）が `【X長文】` で不一致となり、生成した下書きが cron に拾われない潜在バグを是正。両者を `【X長文】` に統一。
