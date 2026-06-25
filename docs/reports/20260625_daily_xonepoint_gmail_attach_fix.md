---
title: daily-xonepoint のメール下書きを画像添付対応に修正
date: 2026-06-25
tags: [skill, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260625_daily_xonepoint_gmail_attach_and_deprecation/)

## 背景・動機

W003 のワンポイント解説では Gmail 下書きに完成インフォグラフィックを添付する。しかし `daily-xonepoint` SKILL の STEP 8 は `mcp__claude_ai_Gmail__create_draft` ツールを指定していた。このツールは添付に非対応（ツール説明に "Creating drafts with attachments is not supported yet"）で、実際に作成した下書きに画像が付かなかった。

spec.md は本来「画像添付があるため `bash scripts/create_gmail_draft.sh --attach …` を使う」と指定しており、SKILL.md だけが古い添付非対応の指定のまま残っていた（spec.md と SKILL.md の不整合）。

## 実施内容

- SKILL STEP 8 の作成手段を `mcp__claude_ai_Gmail__create_draft` → **`bash scripts/create_gmail_draft.sh --attach <png>`**（gws CLI 経由・複数添付可）に変更。本文は一時ファイルに Write し `--body-file` で渡す形に。
- 添付対象を完成画像（採用した型の `output/infographic_[連番].png`）に明記。
- 成功判定を「`✓ 下書き作成完了` の出力」＋必要なら `mcp__claude_ai_Gmail__list_drafts`（`query: "subject:… has:attachment"`）での確認に変更（gws の戻り JSON 構造で id が空表示になる場合があるため）。
- ベテルギウス投稿の下書きを `create_gmail_draft.sh --attach output/infographic_01.png` で作り直し、`has:attachment` 検索で添付付き下書きの作成を確認（id `r2458164055745492186`）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 8 のメール下書き作成を添付対応の `create_gmail_draft.sh --attach` に変更 |

## 確認結果

- `mcp__claude_ai_Gmail__list_drafts`（`query: "subject:ベテルギウス has:attachment"`）で添付付き下書きがヒットすることを確認。
- 注: 本修正直後に `daily-xonepoint` スキル自体を非推奨化したため、今後は同フローを `projects/w003/spec.md`（既に添付対応を明記）に沿って実行する。
