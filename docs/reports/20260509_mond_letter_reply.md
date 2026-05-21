---
title: mond-letter-reply スキル新設・ローカル化
date: 2026-05-09
tags: [skill, workflow, style, infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

mond.how の質問箱（レター機能）に届いた質問への回答を手動で行っていたが、量が増えてきたため自動化したかった。`letter-notify@mond.how` から届くメールを検知し、Claude Opus で回答を生成して Gmail 下書きを作成するスキルを新設した。

ラベル操作は当初 Gmail MCP で実装しようとしたが、claude.ai の Gmail MCP コネクターが `gmail.modify` スコープを持たず認証エラーとなった。既存の `post_from_email.sh` と同じ gws CLI 方式（`gws gmail users threads modify`）に切り替えることで解決した。

## 実施内容

- `.claude/skills/mond-letter-reply/SKILL.md` を新規作成
  - STEP 1: Gmail 検索（`from:letter-notify@mond.how -label:mond-処理済み in:inbox`）
  - STEP 2: スレッド全文取得・質問本文抽出・「回答する」URL の `/ja` 付き変換
  - STEP 3: 質問 / お礼の判定（お礼のみはラベル付与してスキップ）
  - STEP 4: `style/style-mond_reply.md` を読み込み → 素回答生成 → `/check-fact` → トンマナ調整
  - STEP 5: Gmail 下書き作成（`[投稿文]` + `[リプ]` タグ形式）
  - STEP 6: `gws gmail users threads modify` で `mond-処理済み` ラベル付与・INBOX アーカイブ
- `.claude/agents/mond-letter-reply.md` を新規作成（model: claude-opus-4-7）
- `style/style-mond_reply.md` を新規作成（ですます調・口語寄り・よーんの人格定義）
- `scripts/run_mond_letter_reply.sh` を新規作成（cron ラッパースクリプト）
- crontab に `0 */6 * * *` エントリを追加（6時間ごとにローカル実行）
- リモートルーティン `trig_01WpdaUoC9ziegU9rYBB8mcf` を `enabled: false` に無効化
- `.claude/settings.json` の `permissions.allow` に Gmail MCP 3ツールを追加
- Gmail に `mond-処理済み` ラベル（Label_104）を作成
- gws CLI の OAuth2 トークンを再認証（期限切れのため手動コード交換で更新）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/mond-letter-reply/SKILL.md` | スキル新規作成。STEP 6 を Gmail MCP から gws CLI に変更、STEP 2 に URL 変換追加、STEP 5 に `[リプ]` タグ追加 |
| `.claude/agents/mond-letter-reply.md` | エージェント定義新規作成（claude-opus-4-7 使用） |
| `style/style-mond_reply.md` | スタイルガイド新規作成。ですます調・口語寄り・よーん人格 |
| `scripts/run_mond_letter_reply.sh` | cron ラッパースクリプト新規作成 |
| `.claude/settings.json` | `mcp__claude_ai_Gmail__search_threads` / `get_thread` / `create_draft` を permissions.allow に追加 |

## 設計判断

**ローカル cron vs リモートルーティン（CCR）**：当初はリモートルーティンで実装したが、gmail.modify スコープ不足によるラベル操作エラーが解決できなかった。既存の `post_from_email.sh` と同じ gws CLI + ローカル cron 方式に統一することで、認証・権限の問題を回避した。

**下書きフォーマット**：`[投稿文]` タグは既存の X 投稿フローと共通。`[リプ]` タグを追加し、mond 質問箱への直リンク（`/ja/topics/{id}` 形式）を下書きに含めることで、回答投稿時のリプライ先 URL をすぐ参照できるようにした。

## 確認結果

手動実行（`/mond-letter-reply`）で2件のレターを処理：
- トップクォーク質量・ヒッグス粒子・重いニュートリノに関する3問への回答
- 月の自転（潮汐固定）に関する質問への回答

Gmail に下書き2件が作成され、スレッドに `mond-処理済み` ラベルが付与・アーカイブされたことを確認。

## 今後の課題

- `[リプ]` タグの URL を実際に使った投稿フローの整備（現状は下書き確認後に手動投稿）
- 同一スレッドに複数メッセージがある場合の処理は現状手動判断（スキルは1スレッドにつき1件想定）
