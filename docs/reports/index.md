---
title: 報告書
description: プロジェクトの変更・実装に関する詳細報告書。変更ログと1対1対応。
---

変更の概要は [変更ログ](/xClaude/changelog/) を参照。詳細が必要な場合に各報告書を参照する。

## 2026-05-02

- [Wiki システム構築](20260502_wiki_setup) — Starlight + GitHub Pages による Wiki 新設
- [Google サービス連携・スクリプト化ルールの追加](20260502_implementation_rules) — CLAUDE.md に実装ルールを明文化
- [報告書・変更ログ運用フローの整備](20260502_reporting_workflow) — 変更ログと報告書の1対1対応構造を整備
- [Wiki構築で使用した操作の permissions.allow 追加](20260502_settings_permissions_wiki) — Write/Edit/mkdir/cp/npm/grep を settings.json に追記
- [git commit 前の確認フック追加](20260502_precommit_hook) — PreToolUse フックで settings.json 確認を自動挿入
