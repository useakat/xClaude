---
title: スキル一覧
description: Claude Code で使用できるスキルの一覧
---

スキルは `.claude/skills/` に定義されており、チャットで `/スキル名` と入力して呼び出す。

## コンテンツ制作

| スキル | 用途 |
|---|---|
| [daily-xonepoint](/xClaude/skills/daily-xonepoint/) | Xのワンポイント解説投稿を1本作成し、品質チェック・保存・Git push・メール下書き作成まで自律実行する。インフォグラフィック作成はユーザー承認後に実行する。 |
| [draft_xstory](/xClaude/skills/draft_xstory/) | X長文ストーリー投稿（what_id W001）のネタ選定から下書き作成、ファクトチェック、トンマナチェック、Gmail下書き作成まで自律実行する |
| [note-quick](/xClaude/skills/note-quick/) | note-quick スキル |
| [writer-xnews](/xClaude/skills/writer-xnews/) | writer-xnews スキル |
| [writer-xonepoint](/xClaude/skills/writer-xonepoint/) | X用ワンポイント解説投稿を1本作成する。受け取ったネタ情報をもとに投稿原稿を生成する。 |
| [writer-xqa](/xClaude/skills/writer-xqa/) | X 上の質問への回答投稿を 1 本作成する。長文化を避け、3 段以内・400 字以内に圧縮し、超える内容は note 誘導で切り上げる。 |
| [writer-xstory](/xClaude/skills/writer-xstory/) | writer-xstory スキル |
| [writer_note-story](/xClaude/skills/writer_note-story/) | writer_note-story スキル |

## レポート生成

| スキル | 用途 |
|---|---|
| [reporter-daily](/xClaude/skills/reporter-daily/) | X・note 運用の日報を作成し、docs/reports/daily/ に保存する。スプレッドシートから前日の数値を取得し、投稿実績をもとに特記事項をAI生成する。 |
| [reporter-monthly](/xClaude/skills/reporter-monthly/) | X・note 運用の月報を作成し、docs/reports/monthly/ に保存する。スプレッドシートから月次集計値・note売上を取得し、日報・週報をもとに総評と翌月改善計画をAI生成する。Xクリエイター収益は 0円 をデフォルトで保存（実値判明後に手動更新）。 |
| [reporter-weekly](/xClaude/skills/reporter-weekly/) | X・note 運用の週報を作成し、docs/reports/weekly/ に保存する。スプレッドシートから週次集計値を取得し、日報をもとに「やったこと」「来週タスク」をAI生成する。 |

## リサーチ・分析

| スキル | 用途 |
|---|---|
| [analyze-target](/xClaude/skills/analyze-target/) | analyze-target スキル |
| [analyze-x-posts](/xClaude/skills/analyze-x-posts/) | analyze-x-posts スキル |
| [classify-followers](/xClaude/skills/classify-followers/) | フォロワー全件をペルソナ分類し、前回分類との差分（新規・アンフォロー・消滅）を更新する。初回は全件LLM分類、2回目以降は差分のみを分類して既存JSONに追記・削除する。 |
| [deep-research](/xClaude/skills/deep-research/) | deep-research スキル |
| [ops_analyze-posts](/xClaude/skills/ops_analyze-posts/) | X投稿のパフォーマンスを集計・分析する。stats モードで平均IMP等の集計サマリー、フルモードでパターン分析＋スキル改善提案を生成・適用する。 |
| [ops_post-reactions](/xClaude/skills/ops_post-reactions/) | ops_post-reactions スキル |
| [research](/xClaude/skills/research/) | research スキル |
| [research-note-projectx](/xClaude/skills/research-note-projectx/) | research-note-projectx スキル |
| [research-plan](/xClaude/skills/research-plan/) | research-plan スキル |
| [research-trivia](/xClaude/skills/research-trivia/) | research-trivia スキル |
| [research_pain-xpost](/xClaude/skills/research_pain-xpost/) | 特定のXポストのリプライ・引用RTを取得し、読者のニーズや疑問を分析して note 記事のテーマを提案する。承認後に noteNeta シートへ追記する。 |
| [research_setup-sources](/xClaude/skills/research_setup-sources/) | テーマを受け取り NotebookLM ノートブックを作成して Deep Research でソースを収集・追加し、notebook_id を返す。 |
| [research_trivia-source](/xClaude/skills/research_trivia-source/) | research_trivia-source スキル |
| [research_xhook](/xClaude/skills/research_xhook/) | research_xhook スキル |

## 品質チェック

| スキル | 用途 |
|---|---|
| [check](/xClaude/skills/check/) | check スキル |
| [check-fact](/xClaude/skills/check-fact/) | ファクトチェック付き品質レビュー。テキストまたは Drive ファイル ID を入力として受け付ける。 |
| [check-fact-lim](/xClaude/skills/check-fact-lim/) | ファクトチェック付き品質レビュー（NotebookLM の特定ノートブックのソースのみを根拠にする）。第1引数に notebook_id、第2引数以降にテキストまたは Drive ファイル ID を受け取る。 |
| [check-p01](/xClaude/skills/check-p01/) | X ワンポイント解説の本文を、作業フォルダの brand.md に基づく P01化チェックリスト6項目で10段階採点し、全項目8点以上になるまで該当箇所を書き直す。本文テキストを受け取り、最終原稿とスコアサマリーを返す。 |
| [check-tonmana](/xClaude/skills/check-tonmana/) | X ワンポイント解説の本文を projects/x-onepoint/brand.md に照らしてトンマナ調整する。本文テキストを受け取り、事実は変えず文体・口調・構成のみ整えた調整後本文を返す。 |

## メール・通知

| スキル | 用途 |
|---|---|
| [mond-letter-reply](/xClaude/skills/mond-letter-reply/) | letter-notify@mond.how からの未処理レターを読み取り、Claude Opus で回答を生成して Gmail 下書きを作成する |

## 画像・同期

| スキル | 用途 |
|---|---|
| [hashtag-note](/xClaude/skills/hashtag-note/) | hashtag-note スキル |
| [make-infographic](/xClaude/skills/make-infographic/) | make-infographic スキル |
| [notebooklm](/xClaude/skills/notebooklm/) | notebooklm スキル |
| [sync-to-drive](/xClaude/skills/sync-to-drive/) | sync-to-drive スキル |
| [sync-to-sheets](/xClaude/skills/sync-to-sheets/) | sync-to-sheets スキル |
| [visual_infographic](/xClaude/skills/visual_infographic/) | visual_infographic スキル |
| [visual_section-planner](/xClaude/skills/visual_section-planner/) | 記事の本文を入力に、H2セクションごとに画像案を3つ考え、各画像（図解／イメージ／写真Web取得）の説明を、セクション分けしたmarkdown形式で出力し、draft/image-plan.md に保存する。生成プロンプトは書かず画像の説明のみ。 |

## 運用・記録

| スキル | 用途 |
|---|---|
| [record](/xClaude/skills/record/) | 変更・実装の記録を残す。docs/changelog.md と直近の git ログを照合し、未記録の変更候補をよーんに提案する。承認後に報告書と変更ログエントリを作成して git push する。 |
| [record-note-posts](/xClaude/skills/record-note-posts/) | note.com の投稿情報（ビュー・スキ・スキ率・サムネ・ハッシュタグ）を取得して Google Sheets の「note投稿一覧」シートに記録・更新する。 |
| [save-session](/xClaude/skills/save-session/) | save-session スキル |
| [sync-x-note-analytics](/xClaude/skills/sync-x-note-analytics/) | outputs/X投稿一覧/note投稿一覧/note購入記録 を集約して「Xnote導線記録」シートを再生成する。W001 ごとの IMP・リンクCTR・購入CVR・売上を 1 行 1 投稿の集計シートにまとめる。 |

## 設定・保守

| スキル | 用途 |
|---|---|
| [update-permissions](/xClaude/skills/update-permissions/) | このセッションでよーんが許可を求められた操作を一覧表示し、settings.json の permissions.allow への追記を提案する。 |

