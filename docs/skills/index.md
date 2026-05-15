---
title: スキル一覧
description: Claude Code で使用できるスキルの一覧
---

スキルは `.claude/skills/` に定義されており、チャットで `/スキル名` と入力して呼び出す。

## コンテンツ制作

| スキル | 用途 |
|---|---|
| [daily-xonepoint](/xClaude/skills/daily-xonepoint/) | Xのワンポイント解説投稿を1本作成し、品質チェック・保存・Git push・メール下書き作成まで自律実行する。インフォグラフィック作成はユーザー承認後に実行する。 |
| [note-quick](/xClaude/skills/note-quick/) | note-quick スキル |
| [writer-note](/xClaude/skills/writer-note/) | writer-note スキル |
| [writer-xnews](/xClaude/skills/writer-xnews/) | writer-xnews スキル |
| [writer-xonepoint](/xClaude/skills/writer-xonepoint/) | X用ワンポイント解説投稿を1本作成する。ネタ選定・本文生成・ネタ使用済み更新を行う。 |
| [writer-xstory](/xClaude/skills/writer-xstory/) | writer-xstory スキル |

## レポート生成

| スキル | 用途 |
|---|---|
| [reporter-daily](/xClaude/skills/reporter-daily/) | X・note 運用の日報を作成し、docs/reports/daily/ に保存する。スプレッドシートから前日の数値を取得し、投稿実績をもとに特記事項をAI生成する。 |
| [reporter-monthly](/xClaude/skills/reporter-monthly/) | X・note 運用の月報を作成し、docs/reports/monthly/ に保存する。スプレッドシートから月次集計値・note売上を取得し、日報・週報をもとに総評と翌月改善計画をAI生成する。Xクリエイター収益は 0円 をデフォルトで保存（実値判明後に手動更新）。 |
| [reporter-weekly](/xClaude/skills/reporter-weekly/) | X・note 運用の週報を作成し、docs/reports/weekly/ に保存する。スプレッドシートから週次集計値を取得し、日報をもとに「やったこと」「来週タスク」をAI生成する。 |

## リサーチ・分析

| スキル | 用途 |
|---|---|
| [analyze-impression](/xClaude/skills/analyze-impression/) | X投稿のインプレッションデータを分析し、関連スキル（writer-xonepoint等）への修正提案を生成・適用する。HOW_ID単位でフィルタし、高IMP/低IMPのパターンを抽出してスキル・style ファイルを改善する。 |
| [analyze-target](/xClaude/skills/analyze-target/) | analyze-target スキル |
| [analyze-x-posts](/xClaude/skills/analyze-x-posts/) | analyze-x-posts スキル |
| [deep-research](/xClaude/skills/deep-research/) | deep-research スキル |
| [research](/xClaude/skills/research/) | research スキル |
| [research-note-projectx](/xClaude/skills/research-note-projectx/) | research-note-projectx スキル |
| [research-plan](/xClaude/skills/research-plan/) | research-plan スキル |
| [research-trivia](/xClaude/skills/research-trivia/) | research-trivia スキル |

## 品質チェック

| スキル | 用途 |
|---|---|
| [check](/xClaude/skills/check/) | check スキル |
| [check-fact](/xClaude/skills/check-fact/) | ファクトチェック付き品質レビュー。テキストまたは Drive ファイル ID を入力として受け付ける。 |

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

## 運用・記録

| スキル | 用途 |
|---|---|
| [record](/xClaude/skills/record/) | 変更・実装の記録を残す。docs/changelog.md と直近の git ログを照合し、未記録の変更候補をよーんに提案する。承認後に報告書と変更ログエントリを作成して git push する。 |

## 設定・保守

| スキル | 用途 |
|---|---|
| [update-permissions](/xClaude/skills/update-permissions/) | このセッションでよーんが許可を求められた操作を一覧表示し、settings.json の permissions.allow への追記を提案する。 |

