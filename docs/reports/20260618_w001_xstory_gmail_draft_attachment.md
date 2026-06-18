---
title: X長文投稿用 Gmail 下書きの自動化（サムネ添付対応）
date: 2026-06-18
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260618_w001_flow_and_gmail_draft_attachment/)

## 背景・動機

W001（X長文ストーリー）は、投稿原稿と添付画像（サムネ）を Gmail 下書きにし、件名 `【Xストーリー】` を拾う cron（`scripts/post_from_email.sh` ＋ `x-post-from-email` エージェント）が X に投稿する運用。これまで spec に下書き作成ステップが無く、また下書きへのサムネ添付が自動化されていなかった（MCP `create_draft` は添付未対応）。投稿原稿＋サムネをワンステップで下書き化したい。

## 実施内容

- spec.md に「⑭ X投稿用メール下書き作成」を追加。cron が拾う体裁（件名 `【Xストーリー】YYYYMMDD HH:MM:SS …`、本文 `[note_url]`／`[投稿文]…[/投稿文]`＝本編、添付PNG）を `/draft_xstory` STEP 6 に準拠して明記。
- 下書き作成を `scripts/create_gmail_draft.sh`（gws CLI）に統一し、**`--attach <path>`（複数可）を追加**。`gws gmail +send … --draft` に渡してサムネを自動添付する。
- gws の `--attach` はカレントディレクトリ内のファイルしか受け付けないため、spec の手順を「投稿フォルダに `cd` してから相対パスで `--attach output/thumbnail.png`」と明記。
- 添付サムネの保存先を `output/images/thumbnail.png` → **`output/thumbnail.png`** に変更（spec の Output・制作フロー）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/create_gmail_draft.sh` | `--attach <path>`（複数回指定可・存在チェック付き）を追加し、`gws gmail +send --draft` に渡すよう拡張。後方互換を維持 |
| `projects/w001/spec.md` | 制作フローに「⑭ X投稿用メール下書き作成」を追加、サムネ保存先を `output/thumbnail.png` に変更、Verification に下書き作成チェックを追加 |

## 設計判断

- MCP `mcp__claude_ai_Gmail__create_draft` は説明上「添付未対応」かつ大容量 base64 のインライン化が非現実的なため、添付に対応する **gws CLI（`gws gmail +send --draft -a`）に一本化**。CLAUDE.md の「Gmail は gws CLI」方針とも合致。

## 確認結果

- 拡張した `create_gmail_draft.sh` で `【Xストーリー】` 下書きを作成し、`multipart/mixed` に `thumbnail.png`（1,279,059バイト）が添付されていることを Gmail API で確認。
- 既存の `--to/--subject/--body-file` のみの呼び出し（添付なし）も従来どおり動作。

## 今後の課題

- gws は当初サービスアカウントで構成されており Gmail ユーザー API が `failedPrecondition` で全滅していた。`gcp/` の OAuth クライアントを `~/.config/gws/client_secret.json` に配置し `gws auth login`（ユーザー OAuth・Gmail modify スコープ）で再認証して解消した。リモート/cron 実行時にも同じユーザー OAuth が必要。
