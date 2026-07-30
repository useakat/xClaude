---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-07-30

- **w001/w002 に Drive フォルダ一式アップロード工程を追加し画像を Drive-only 化（w003 方式に統一）** — w001 spec フロー15／w002 spec フロー16 に `drive_put_folder.sh` によるフォルダ丸ごとアップロード（構造再現・冪等）を新設し、`.gitignore` に `/projects/w001|w002/**/*.png` を追加して追跡中の png 39件を git 追跡解除（リポジトリ肥大防止）。過去フォルダ8件（w001×4・w002×4）を Drive `xClaude/projects/` 配下へ遡及アップロード済み。[→報告書](../reports/20260730_w001_w002_drive_folder_upload/)

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
