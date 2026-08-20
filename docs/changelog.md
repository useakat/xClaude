---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-08-20

- **オポチュニティ記事の初稿→最終稿の差分分析から W002 の執筆・検品ルールを7点整備** — 導入部＋H2-1〜H2-6 の全7ブロックについてユーザー修正のべ約80件・24往復を分析した。最頻出は**文法は正しいが何を言っているか像が結べない表現**（6件）で、書き手は自分の比喩の意味を知っているため**自己判定では原理的に検出できない**。判定を読者役に委ねる形で `/check-reader` の【不自然な日本語】を拡張（4プロジェクトに波及）し、W002 だけ本文の素朴な読者チェックが未配線だった穴（フロー8の2周目が書き手のセルフ通し読み）を `/check-reader` への置き換えで塞いだ。あわせて brand.md に導入で使わない表現・固有名は必要最小限・列挙の型を揃える・見せ場H2の場面化と実数の裏付けを追加し、前方参照ルールの対象に数値を加えた。[→報告書](../reports/20260820_w002_first_draft_diff_rules/)
- **よーん役最終検品スキル `/check-yohn` を新設** — W002 過去4記事のセッション履歴からユーザー発言922件を抽出し、修正指摘を判断基準10項目・実例集に蒸留した検品ペルソナを作成。既存の `/check-reader`（素朴な読者）・`/check-fact-lim`（事実）・`/check-critic`（知識ある読者）に書き切れない**よーん固有の判断の癖**を再現する最終ゲートとして、公開提示直前（フロー10.5）に配線した。ケプラー記事初稿での事後検証で的中率65%（17/26）を確認。フロー11 提示後の新規指摘はこのペルソナの見逃しとして追記していく自己改善ループも spec に明記した。[→報告書](../reports/20260820_w002_check_yohn_skill/)
- **ネタ自動振り分けスキル `/add-neta` を新設** — URL・テキストで渡されたネタの4シート（newsTopics/onePointNeta/noteNeta/thoughts）への振り分けを自動化。これまで都度手動で判断していた暗黙ルール（thoughts→noteNeta→newsTopics→onePointNeta の優先順判定、物語の芽があるニュースは newsTopics＋昇格候補付記、結末未確定は newsTopics、noteNeta は危機・逆転・人間ドラマが出典で揃う話のみ）を明文化し、重複チェック・No最大値+1採番（重複採番の実例対策）・発表日/機関の必須記載を組み込んだ。[→報告書](../reports/20260820_add_neta_skill/)
- **よーん役最終検品を W001/W003/Z01 へ展開（プロジェクト別ペルソナ補足）** — 同日新設の `/check-yohn` を全投稿系プロジェクトに展開。各プロジェクトのセッション履歴からユーザー発言473件（w001: 222・w003: 219・z01: 32）を抽出し、媒体固有の判断の癖（W001＝締めの一文・フックの回収・note の売りの温存／W003＝**ソースが言っていない因果づけの禁止**・極値と代表値／Z01＝主張の強さを証拠に合わせる・スコープの限定）を共通コア＋プロジェクト別補足の2層ペルソナに蒸留した。各 spec のユーザー提示直前（z01 は無人フローのため Gmail 下書き前・非ブロック）に配線。蒸留元事例でのバックテストは Z01 7/7・W003 5.5/7・W001 3.5/6 で、誤検知1件（メッセージ型ハッシュタグ）は「指摘しない」ルールとしてペルソナに追記（自己改善ループの初適用）。[→報告書](../reports/20260820_check_yohn_all_projects/)

## 2026-08-18

- **freeze_first_draft.sh / update_wiki_skills.py 呼び出しをサブディレクトリ起動対応に修正** — SOHO 投稿の初稿→最終稿の差分分析中、`first-draft.md` が凍結されていないことが発覚。`$CLAUDE_PROJECT_DIR` はローカル環境ではセッション起動時の cwd に展開されるため、`projects/w001` 等のサブディレクトリで起動したセッションでは hook が存在しないパスを指し無音失敗していた。2026-07-09 に mcp-gsheets の起動で発見・修正済みだった「上方探索」パターンを、freeze_first_draft.sh（3箇所）・update_wiki_skills.py（1箇所）に適用。あわせて story-check.md に相対時間（「40日後」等）の起点明示ルールを追加した。[→報告書](../reports/20260818_freeze_first_draft_subdir_fix/)

---

## 2026-08-16

- **週次の発信運用振り返り `/reporter-weekly-ops` を新設し routine 化** — 週報（数値）と月次マネタイズの間に「どの投稿が・なぜ伸びた/沈んだか」を扱う場が無かった。@galileo_fun 分析と8週実績分析（週インプの支配要因は W001 長文の有無・投稿0本日はインプ 1/4〜1/6・7月中旬にベースライン半減・切れ位置は「答えの直前」が本質）を織り込み、運用遵守チェック（W001週2本・note週1本・0本日ゼロ）→8週ローリング集計（中央値＋IQR外れ値除外平均）→要因分析→仮説検証（H1〜H4）の週次サイクルを新設。毎週日曜20時 JST の routine（claude-fable-5）がレポート作成〜メール送信まで無人実行する。初回レポート（2026-W33）作成済み。[→報告書](../reports/20260816_reporter_weekly_ops_skill/)
- **X長文冒頭の日付・地名をデフォルトで年月・大きな単位に限定** — 冒頭は情報密度が一番高くなりやすく、詳しすぎる日付・地名は読者を身構えさせ離脱を招く。8/15 のオポチュニティ記事で「2005年4月26日、火星のメリディアニ平原」が読者役チェックで離脱寸前となり「2005年4月、火星」に簡略化した実例を一般化。特別な重要性・必要性がない限り、日付は年月まで・地名は狭い固有名詞を避け大きな単位にとどめる方針を `style/hook-patterns.md` に追記した。[→報告書](../reports/20260816_hook_date_place_specificity/)
- **z01 を改善対象外（定点観測・検証用）に位置づけ** — z01 の目的は note ネタの反応観測とアカウント発信力の定点観測であり、投稿単体の改善対象ではないため、`/reporter-weekly-ops` の伸び沈み分析・トップ/ワースト選定から除外。①実績表・ベースライン監視と、フック型記録など仮説検証の場としての利用は継続する。[→報告書](../reports/20260816_z01_observation_only/)

## 2026-08-15

- **測定量を読者の意味に翻訳するルールを共通 brand.md に新設** — Z01 の DART 投稿でユーザー推敲が7往復発生し、差分の大半が一般化できるルールだった。中でも「周期が32分縮んだ」は軌道変更を測る**中間指標**で、読者役チェックでも「何の周期？」「縮むとなぜ守れるの？」が3ループ解消せず理解度4/10 で頭打ちだった。測定量・中間指標は対象読者が意味・意義を理解できるか判定し、できなければ読者が理解できる意味に置き換えるルールを、継承の根であるルート `brand.md` に追加（禁止形でなく判定形にしたため日報等は自動的に対象外）。あわせて z01-phrasebook v1.2（一般に通じる語は言い換えない・達成は控えめな断定）と z01 Verification（`/check-critic` 通過・ストーリー型／ニュース型の「いつ・誰が」明記）を補強。[→報告書](../reports/20260815_z01_metric_translation_rule/)
- **note 出力を note の仕様に合わせる（目次位置・H1・水平線・alt・figcaption）** — 8/13 に下書きを開けるようにして初めて note 上の見え方を確認でき、仕様と噛み合わない4点が判明。目次を導入の直後（最初のH2の手前）へ移動、記事タイトルのH1と水平線を本文に出力しない、**`img` の `alt` を空にする**（note のエディタは alt を画面表示するため、説明文を入れると画像に黒文字が出ていた。note 自身の出力も `alt=""`）。あわせて画像の直後の `> …` 行を **figcaption** に流し込む記法を新設し、説明文・クレジットを本文段落ではなくキャプション欄に置けるようにした。[→報告書](../reports/20260815_note_output_spec_alignment/)
- **first-draft 凍結フックに UserPromptSubmit を追加** — Stop フックはターン中断時に発火しないケースがあり、W001 のオポチュニティ販促記事で `draft.md` を9回更新しても `first-draft.md` が一度も作られない事象が発生。よーんの次発言で必ず発火する UserPromptSubmit を保険として追加し、Stop の取りこぼしを回収するようにした。[→報告書](../reports/20260815_first_draft_hook_userpromptsubmit/)
- **check-reader の判定基準を「納得できるか」から「誤解・曖昧・不自然・フック未回収の有無」へ変更** — DART投稿で理解度1〜10の自己採点方式が3ループとも4/10で頭打ちになり非収束。「もっと深く知りたい」という納得要求と「誤解・曖昧・不自然」という検証可能な指標を切り分け、後者のみを判定対象にした。[→報告書](../reports/20260815_check_reader_criteria_misunderstanding/)
- **Z01 に「驚きは1投稿に1つ」ルールを追加** — DART投稿の初稿が「進路変更」と「岩塊の反動」の2つの驚きを140字に詰め、どちらも説明不足で読者役チェックが理解度4/10のまま頭打ちになった。1投稿の驚きは最も強い1つに絞り、残りは昇格先（W001/W002/W003）候補として本文に入れないルールを z01 brand.md に追加。[→報告書](../reports/20260815_z01_single_surprise_rule/)
- **W003 の原稿作成を共通スキル `/writer-xpost` へ統合し、可視ブロック設計ステージを新設** — W003 だけが個別スキル `writer-xonepoint` に取り残されていたため z01 と同じ `/writer-xpost` へ切替。折り返しチェックが検品（本文完成後）にしかなく手戻りが発生していたため、`writer-xpost` に可視ブロックを先に書き `/check-reader --fold` で検証するステージ2.5を新設（発動条件は brand.md/spec.md の折り返し制約有無なので z01 は影響を受けない）。[→報告書](../reports/20260815_w003_writer_xpost_migration/)
- **W003 の画像生成を NotebookLM から Lovart へ移行** — `/visual_infographic` が依存する cookie 認証は8/6に廃止済み、後継ブリッジも `infographic` 未移植で実行不能と判明。W001・W002に続き `/lovart` へ移行し、実運用でラベル記法混入とハビタブルゾーン内の位置関係の誤りを検出・修正した。[→報告書](../reports/20260815_w003_lovart_image_generation/)

## 2026-08-14

- **NotebookLM の Deep Research 生成報告書によるソース汚染を解消（検証ループの循環を遮断）** — SOHO 販促原稿のファクトチェックで `/check-fact-lim` が誤った物理説明を2度出力。原因は、Deep Research が生成した報告書が `import_sources()` によって notebook 自身のソースに登録され、**AI の出力を AI が検証する循環**に陥っていたこと。ブリッジで生成報告書を既定除外（`--with-report` で従来動作）し、`list-sources --ids`・`delete-source` を新設。全24 notebook を棚卸しし汚染2件（SOHO・W003探査機の手ブレ対策）を削除、再照会で解消を確認した。`/check-critic` と一次情報の突き合わせが機能した初の実運用例。[→報告書](../reports/20260814_notebooklm_generated_report_contamination/)
- **`commit_and_sync.sh` を対象限定コミットに対応させ全7スキルを追従** — `git add -A` が他セッションの未コミット作業を巻き込む問題。同日の `/record` で43ファイル・8,833行のコミットになりかけ、過去も同じ手作業回避が6回以上繰り返されていた。スクリプトが第2引数以降で対象パスを受け取る形にし（省略時は警告つきで従来動作）、コミット前にファイル一覧を表示・空コミットを防止。呼び出し元7スキル（record / reporter-daily・weekly・monthly / update-permissions / save-session / classify-followers）すべてに対象パスを明示した。[→報告書](../reports/20260814_commit_and_sync_targeted_paths/)

---

## 2026-08-13

- **note 下書きがエディタで開けない問題を解決（`figcaption` 必須）** — 保存した下書きの編集URLが404になり、一覧には並ぶのに開けなかった。データは正常（本文31,466字・figure11個・note_draft レコードあり）で、404はブラウザ内で出ていた。テスト下書き10件で1要素ずつ切り分け、**`<figcaption>` の無い `<figure>` をエディタが読み込めない**ことを特定（`data-align`・`alt`・本文量・リンクは無関係）。あわせて切り分け中に見つけた「URLに括弧を含むリンクが途中で切れる」「HTMLコメントが本文に混入する」も修正。8/10 の実装時はローカル検証だけで、下書きをエディタで開く確認をしていなかった。[→報告書](../reports/20260813_note_draft_figcaption_fix/)

---

## 2026-08-12

- **X の折り返し位置（280weight）を設計対象にする工程を W001/W003 に新設** — 競合 @galileo_fun の高IMP投稿は可視ブロック（先頭280weight）の終わり方が設計されていた一方、こちらの既存投稿は実測5本すべてが語・説明の途中で機械的に切れていた。280weightで本文を分割する `x_fold_split.py` を新設し、可視ブロックだけを読者役に渡して「さらに表示」を押すか判定する `/check-reader --fold` を追加。W001 は執筆前の可視ブロック確定（5.5）＋提示前チェック（6.4）、W003 は段3の「問いを可視側・答えを折返し後ろ」制約＋提示前チェック（5.4）を配線し、両者の採点基準に「折り返し位置」項目を追加した。[→報告書](../reports/20260812_x_fold_position_design/)
- **note 本文画像アップロードを API 仕様変更に追従（`filename`・埋め込みURL）** — 8/10 に自動化した `send_note_draft.py` の本文画像が、初の実運用（オポチュニティ記事）で11点すべて 400（invalid_param）で失敗。パラメータを総当たりして presigned_post のキーが `file_name` → `filename` に変わったと特定し追従。あわせて埋め込み `src` をレスポンスの `url` に変更（`post.key` が `img/` を含み、従来の連結だと `/img/img/...` と重複するため）。再実行で11点すべて成功し、配信も HEAD で確認。[→報告書](../reports/20260812_note_body_image_upload_api_fix/)
- **図・サムネの最小文字サイズを画像幅の比率で規定（W002）** — 「36px 以上」はキャンバス幅を決めないと可読性の指標にならない（note のスマホ表示は幅約390pxまで縮小されるため、1280px幅の36pxは見かけ11px）。下限を**画像幅の2.19%**（1280px幅で28px）と比率で定義し、幅ごとの早見表・クレジットの例外・キャンバス1280px基本を `image/brand.md` と `thumbnail_template/brand.md` に明記。図解生成スクリプトにも `MIN = round(幅 × 0.0219)` の自動クランプを実装した。[→報告書](../reports/20260812_w002_min_font_size_rule/)
- **note 下書き保存の再実行を安全にする（`--note-id`・画像失敗時の停止）** — 上記の障害対応中に、リトライのたびに下書きが増え（画像なし版と完成版が並ぶ）、画像が欠けたままでもフローが進めてしまう問題が判明。`--note-id <既存の下書きID>` で同じ下書きを上書き更新できるようにし（戻り値に `mode: create/update` を追加）、画像が1点でも失敗したら再実行手順を stderr に出して終了コード2で止めるようにした。w002 spec フロー16 にも「`failed_images` が空でなければ次工程へ進まない」を明記し、`--no-images` は原因特定を試みた後の最終手段に格下げ。[→報告書](../reports/20260812_note_draft_retry_safety/)

---

## 2026-08-11

- **NotebookLM ブリッジのチャット応答を間引き OOM を解消** — `ask` がハング・空応答になる原因はローカル python3 が OOM Killer に殺されていたためと判明（チャットのストリーム応答が更新のたびに引用メタ全部を再送し32〜59MBに達していた）。リモート Chrome 内で最終スナップショットだけ残すトリムを実装し、転送量を24〜65分の1に削減。Windows 側にしか無かった `nbrpc_server.py` をリポジトリに取り込んだ。[→報告書](../reports/20260811_notebooklm_bridge_ask_oom_fix/)
- **NotebookLM ブリッジに排他ロックと異常終了時の後始末を追加** — 上記修正の検証中に発覚した「並行実行の衝突」「異常終了後の残留Chromeロック」を解消。flock ベースの排他ロックで直列化し、SIGTERM時はPID指定でリモートを終了、SIGKILL（OOM）後は次回起動時に自動検知・掃除・再試行する。[→報告書](../reports/20260811_notebooklm_bridge_lock_cleanup/)
- **Z01 冒頭フック採点のソース別 1a/1b 分岐を廃止し一本化** — newsTopics が無条件に日常接続型(1a)へ固定され、驚き系ネタの冒頭が「僕らの体」へ無理に接続されていた問題の是正。フック採点を全ソース共通の「つかみ＋主題＋具体（必須）」に統一し、パワーワード・直感的比較数字・日常接続は必須から加点要素へ格下げ。w003 は単一の日常接続型設計で問題が起きないため現状維持。[→報告書](../reports/20260811_z01_hook_scoring_unify/)

---

## 2026-08-10

- **note 記事の下書き保存を画像・サムネ込みで自動化（W002 フローに組み込み）** — 記事完成後の「note を開いて本文を貼り、画像を1枚ずつ挿入し、サムネを設定する」手作業を廃止。`send_note_draft.py` にアイキャッチ設定（`image_upload/note_eyecatch`・MIME明示が必須）と本文画像の S3 presigned アップロード＋figure 埋め込み（`x-amz-security-token` 必須）を追加し argparse 化（`--base-dir`/`--eyecatch`/`--no-images`）。w002 spec にフロー16 を新設し、手動作業を有料エリア設定と公開のみに縮小した。[→報告書](../reports/20260810_note_draft_images_eyecatch/)
- **note 公開後の outputs 記録を自動化（record-note-posts に STEP 6 を追加）＋W002 記事3件をバックフィル** — note投稿一覧は cron で自動更新される一方 outputs は手動記録のままで、W002 記事3本が未記録だった。`/record-note-posts` に outputs 同期を相乗りさせ、neta_id は記事フォルダの `note-record.md` からタイトル完全一致で解決（引けなければ空欄＋報告・推測しない）。実データ検証で未記録16件中15件がワークフロー外の旧記事と判明したため除外ガードを追加し、ケプラー・ボイジャー・アポロ12 の3件をバックフィルした。[→報告書](../reports/20260810_outputs_auto_record_note_posts/)
- **日報の記載ルール5点を reporter-daily に反映（note順序・販売数・note販促用・リプライ除外）** — 8/9 の日報でユーザー手直しが5回発生し、いずれも毎回同じ形で必要になる記載ルールだったため SKILL 側に固定。note は「記事公開→記事執筆中」の順、販売数は0件でも `販売数：0。` と明記、outputs の `note_url` がある W001 は `長文ストーリー（note販促用、〜）`、リプライ（セルフリプ・リンク誘導）はオリジナルポストの内訳から除外。あわせて販売0件時の定価取得手順（未確認なら断定せず確認依頼）と保存前チェックリストを新設。[→報告書](../reports/20260810_reporter_daily_format_rules/)
- **初稿（ユーザー提示版）を `draft/first-draft.md` に自動凍結する hook を新設＋draft 運用を3プロジェクトで統一** — 8/9 の執筆前ルール2件はどちらも初稿→最終稿の差分分析から生まれたが、`draft.md` を上書きする運用のため初稿が残らず分析を続けられなかった。PostToolUse(Write\|Edit) で書いた `draft.md` を記録し Stop（＝ユーザー提示の瞬間）で `first-draft.md` へ凍結する2段階 hook を新設（触ったファイルのみ対象・過去記事は走査しない）。あわせて `projects/CLAUDE.md`（3プロジェクト共通ルール）を新設し、w003 の `draft_vN.md` 版管理（0〜18版とばらつき実質不活用）を廃止して「本文は `draft.md` 一本・初稿のみ凍結」に統一。[→報告書](../reports/20260810_first_draft_freeze_hook/)
- **知識ある読者チェック（check-critic）を新設し全投稿系プロジェクトに配線＋NotebookLM 呼び出しをブリッジへ切替** — check-fact 通過後の原稿にユーザー質問だけで事実誤り3件が発覚した金星ベネラ制作の再発防止。別コンテキストの知識ある読者役が「本文が触れていない前提への疑問」まで列挙→裏取りへ流す `/check-critic` を新設し W001/W002/W003/Z01 に配線（W003 は check-fact-lim へ切替、W001/W003 に check-reader も追加）。W001 モードB は notebook 無しの旧記事で「w002 遡及作成＋notebook 新規作成を初稿前に」に変更し `/check-fact` フォールバック廃止。check-fact-lim / research 系の NotebookLM 呼び出しを認証失効した manager から browser bridge に切替（並行実行禁止を明記）。[→報告書](../reports/20260810_check_critic_skill/)
- **Wiki スキルページの description を JSON二重引用符でクォートし YAML frontmatter 破損を修正** — `check-reader` の description の `【構成モード】: `（コロン+スペース）を YAML が mapping と誤解し 8/8 以降 astro build（Wikiデプロイ）が失敗していた。`update_wiki_skills.py` の description 出力を `json.dumps`（YAML互換の引用スカラー）に変更し全49ページ再生成＋YAML全件検証（NG 0件）。[→報告書](../reports/20260810_wiki_frontmatter_quote_fix/)

---

## 2026-08-09

- **W003 brand.md に執筆前チェック3ルールを追加（初稿精度向上）** — クジラ心拍投稿の初稿→最終原稿の差分分析（フック演出過多・因果が飛ぶ主張の混入・極値の代表値化）に基づく再発防止。①原典の「代表値／極値／測定条件」を表にしてから書く（極値フックには代表値を併記）②本文内で「なぜ？」に答えられない主張は落とす（研究者の仮説は原則不採用）③フックは素朴な事実型を第一候補にし冒頭5軸は書いた後の点検に使う、の3ルールを Writing Rules 冒頭に新設。同日の W002 版と対をなす W003 版。[→報告書](../reports/20260809_w003_pre_writing_rules/)
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
