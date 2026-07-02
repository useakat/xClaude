---
title: z01 短文原稿作成をローカル cron → Claude routine（クラウド）へ移行
date: 2026-07-02
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260702_z01_draft_cron_to_routine/)

## 背景・動機

z01 短文の原稿作成（`projects/z01/spec.md` フローで Gmail 下書きを1件作成）は、ローカル cron（`0 8 * * * scripts/run_xshort_draft.sh`）で毎朝8:00に実行していた。これを Claude の **routine（クラウド定時エージェント）**に移し、ローカルマシン非依存で回るようにする。

## クラウドで動く根拠

- **mcp-gsheets**: `.mcp.json` の command 型サーバーは repo に含まれるため cloud session でも clone・起動される（報告書 `20260503_mcp_gsheets_cloud_session` / `20260504_mcp_gsheets_startup_fix`）。認証は cloud environment の環境変数 UI に設定した `GOOGLE_SERVICE_ACCOUNT_KEY`（JSON文字列）で行う。**Default 環境に KEY 設定済み**（ユーザー確認）。`gcp/` ファイルは gitignore のため使わない。先日の起動ラッパー `scripts/mcp_gsheets_launch.sh` はクラウドでも互換（env の KEY を使用）。
- **Gmail 下書き作成**: クラウドでは gws CLI（`create_gmail_draft.sh`）が使えないため、接続済みの **Gmail コネクタ**の `create_draft` ツールで代替。
- **スキル**（`/writer-xpost` / `/check-fact` / `/check-brand`）: repo checkout に含まれる。

## 実施内容

- Claude routine を新規作成（`RemoteTrigger` action=create）:
  - ID: `trig_018f2gJJwYQ46UifKPtXjq27`
  - スケジュール: `0 23 * * *`（UTC）＝ **毎朝8:00 JST**
  - 環境: **Default**（`env_01TNPFtqE8u1RSFCsNSTn53x`）/ モデル: **opus**（`claude-opus-4-8`）
  - repo: `github.com/useakat/xClaude` / Gmail コネクタ接続
  - プロンプト: spec.md STEP 1〜5 を実行、STEP 6 は Gmail コネクタで下書き作成、投稿はしない旨を自己完結で指示
- **即時テスト実行**（action=run）→ 成功を確認（ユーザー確認済み）。
- ローカル crontab から `0 8 * * * .../run_xshort_draft.sh` を**撤去**。`scripts/run_xshort_draft.sh` は手動実行用に残置。

## 変更ファイル

| 対象 | 変更内容 |
|---|---|
| Claude routine（クラウド） | `trig_018f2gJJwYQ46UifKPtXjq27` 新規作成（毎朝8:00 JST・Default・opus・Gmail コネクタ） |
| crontab（ローカル） | `run_xshort_draft.sh` の 8:00 行を撤去 |
| `scripts/run_xshort_draft.sh` | 変更なし（手動用に残置） |

※ リポジトリのコードファイル変更は無し（routine 新設＋crontab 撤去のみ）。

## 設計判断

- **原稿作成＝クラウド routine、投稿＝ローカル cron** の役割分担にした。投稿系（6/12/17 フォールバック＋21:00）は X 投稿の即時性・既存資産（`post_from_email.sh`）の都合でローカル cron のまま。
- **Gmail 下書きはコネクタ経由**：クラウドに gws 認証が無いため。下書き本文は spec.md の Naming（`ソース:`／`[最終原稿]`／`[投稿文]`）を維持し、投稿側 cron の `extract_tag.py` が拾える形を保つ。
- **環境は Default**（KEY 設定済み）。

## 確認結果

- routine 作成 API 200・`next_run_at` = 2026-07-03 08:00 JST を確認。
- テスト実行（`cse_01SvqqkVCa8e1miUi8ZDm6uk`）で Gmail 下書き作成まで完走を確認（ユーザー確認 OK）。
- ローカル cron から 8:00 行が消え、投稿系 cron はそのまま残存を確認。

## 今後の課題

- 数日 routine の実績を見て安定を確認する。
- routine の `allowed_tools` / MCP ツール名は初回テストで問題なかったが、spec.md 改訂時に整合を要確認。
- （任意）`projects/z01/spec.md` STEP 6 に「クラウド routine 実行時は Gmail コネクタで下書き作成」の分岐を明記すると自己文書化できる（現状は routine プロンプトで代替）。
- routine リンク: https://claude.ai/code/routines/trig_018f2gJJwYQ46UifKPtXjq27
