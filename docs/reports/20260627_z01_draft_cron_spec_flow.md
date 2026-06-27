---
title: z01 下書き作成フェーズの cron 自動化（spec.md 準拠・毎朝8:00）
date: 2026-06-27
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260627_z01_draft_cron_and_hook_fix/)

## 背景・動機

z01（X短文投稿）は **(A) 下書き作成 → (B) 投稿** の2段構え。(B) 投稿フェーズは `run_xshort_post.sh`（毎日 7:00/13:00/19:00、`post_from_email.sh` が INBOX の `【X短文投稿】` を拾って投稿）として既に cron 化済みだった。一方 **(A) 下書き作成は未自動化**で、旧 `run_xshort_draft.sh` は廃止予定の `/writer-xshort` を叩くだけだった。

`projects/z01/spec.md` は対話・承認の停止点が無く完全自動で完走する設計のため、これを cron で無人実行し、毎朝 `【X短文投稿】` の Gmail 下書きを1件自動生成できるようにする（投稿はせず下書き作成まで＝レビュー関門あり）。

## 実施内容

- `scripts/run_xshort_draft.sh` を **z01 spec.md 準拠フローに作り替え**。`claude -p --model opus` に「`projects/z01/spec.md` を Read し、作業フォルダを `projects/z01` として STEP 1〜7 を完全自動で実行し Gmail 下書きを1件作成」を渡す。`mkdir -p logs` を追加。ログは `logs/xshort_draft.log`。
- crontab に `0 8 * * *`（毎朝8:00）を登録。
- `.claude/settings.json` の `permissions.allow` に無人実行用の権限を追加：`Skill(writer-xpost)` / `Skill(check-fact)` / `Skill(check-brand)`、および `mcp__mcp-gsheets` / `mcp__mcp-gsheets__sheets_get_values`。

## 重要な発見

- 初回テストが STEP 2（`sheets_get_values`）で**権限不足により停止**した。原因は **`mcp__*` ワイルドカードが Claude Code の permission として機能していない**こと。過去に `/writer-xshort` で動いていたのは、スキルが frontmatter `tools:` に当該 MCP ツールを宣言していたため。
- 対策として **サーバー単位の明示許可**（`mcp__mcp-gsheets`）と**ツール明示許可**（`mcp__mcp-gsheets__sheets_get_values`）を allow に追加 → 解決。
- 教訓: headless `claude -p` で MCP ツールを使う場合、`mcp__*` に頼らず `mcp__<server>` 形式で明示登録する。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/run_xshort_draft.sh` | 旧 `/writer-xshort` 呼び出し → z01 spec.md 準拠フローを `claude -p` で実行。`mkdir -p logs` 追加 |
| `.claude/settings.json` | allow に `Skill(writer-xpost/check-fact/check-brand)`・`mcp__mcp-gsheets`・`mcp__mcp-gsheets__sheets_get_values` を追加 |
| （crontab） | `0 8 * * * .../run_xshort_draft.sh` を追加 |

## 設計判断

- **運用方針はレビュー関門あり**: (A) は Gmail「下書き」作成まで。よーんが確認して送信し INBOX に着信したものを (B) が投稿する。`post_from_email.sh` は `in:inbox` を検索するため、下書きのままでは投稿されない＝関門として機能。
- **既存 `run_xshort_draft.sh` を流用**（新規ファイルを増やさない）。旧 `/writer-xshort` 運用は spec.md が正のため廃止。

## 確認結果

- `bash scripts/run_xshort_draft.sh` を手動実行 → spec.md の全工程（ネタ選定→writer-xpost→check-fact→check-brand→Gmail 下書き）が承認待ちなしで完走（exit 0）。
- thoughts[T007] を選び 140 字の投稿文を生成、`【X短文投稿】…` 下書きを作成、`[投稿文]…[/投稿文]` で囲まれていることを確認。
- `crontab -l` に `0 8 * * *` 登録を確認。

## 今後の課題

- 8:00 の下書き作成と 7:00 の投稿は時刻独立（レビュー関門のため競合なし）。同朝に新作を出したい場合は下書きを早朝に前倒しする運用も可能。
- 依存 `httpx-socks` 等は本フローには不要だが、別環境で cron 運用する際は権限・認証の事前確認が必要。
