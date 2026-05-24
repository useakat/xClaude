---
title: CLAUDE.md：Drive ファイルダウンロードのスクリプト使い分けルール追加
date: 2026-05-24
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../history/20260524_claude_md_drive_download_rule_session/)

## 背景・動機

Drive からファイルをダウンロードする際、Drive MCP ツール（`mcp__claude_ai_Google_Drive__download_file_content`）を使うと base64 エンコードされたファイル内容がそのままコンテキストに乗り、約 28,000 トークンを消費することが過去の検証（2026-05-17）で判明していた。

ローカル環境では `drive_get.sh`（gws CLI ラッパー）が使えるが、今回 gws の Drive スコープ未設定で失敗するケースが発生。対処として Drive スコープを追加し、スクリプトが正常動作することを確認した。あわせて「どの環境でどのスクリプトを使うか」がドキュメント化されていなかったため、CLAUDE.md にルールを明文化した。

## 実施内容

- `gws auth login` に `https://www.googleapis.com/auth/drive` スコープを追加し、SSH トンネル経由で OAuth 認証を完了
- CLAUDE.md の「Google サービス連携」セクションに「Drive ファイルダウンロードのルール」サブセクションを追加
  - ローカル環境: `bash scripts/drive_get.sh <file-id> <output-path>`
  - リモート環境: `bash scripts/drivemcp_get_remote.sh <file-id> <output-path>`
  - Drive MCP ツールはトークン消費が大きいため、スクリプトで代替できる場合は使わない旨を明記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `CLAUDE.md` | Google サービス連携セクションに Drive ダウンロードのスクリプト使い分けルールを追記 |

## 設計判断

Drive MCP ツールを「使わない」のではなく「スクリプトで代替できる場合は使わない」という表現にした。リモート環境かつ `drivemcp_get_remote.sh` も使えない状況（セッション変数が取得できないなど）では MCP ツールが唯一の手段になるため、完全禁止は適切でないと判断。

## 確認結果

`bash scripts/drive_get.sh 1l8X4r2oOPviH_-ae7sIi9RC98c0Js5se /root/xClaude/gcp/notebooklm_storage_state.json` が「ダウンロード: /root/xClaude/gcp/notebooklm_storage_state.json」を返し、正常にダウンロードできることを確認。
