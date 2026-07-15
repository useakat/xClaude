---
title: mcp-gsheets ツール許可を完全一致形式で明示登録（リモートでの許可プロンプト対策）
date: 2026-07-15
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260715_mcp_gsheets_tool_allow_exact_rules/)

## 背景・動機

7/15 朝の日報 routine（reporter-daily）実行中、`sheets_get_values` の呼び出しでツール実行許可プロンプトが表示され、よーんが手動で許可するまで処理が停止した。7/14 の対策（`enableAllProjectMcpServers: true` のコミット）でサーバー信頼確認の層は解消済みで、サーバー自体は正常に接続していた。今回止まったのはその次の層である**ツール単位の実行許可**だった。

調査の結果、以下が判明した：

- mcp-gsheets の許可は「サーバー信頼確認」（7/7 設計・7/14 コミットで解消済み）と「ツール単位の実行許可（`permissions.allow`）」の2層があり、今回の原因は後者。
- 当時の `settings.json` に登録されていたのは `mcp__mcp-gsheets__*`（ワイルドカード）と `mcp__mcp-gsheets`（サーバー名のみ）の2形式だけだった。
- ワイルドカード形式は 6/27 の報告書「[z01 下書き作成フェーズの cron 自動化](./20260627_z01_draft_cron_spec_flow/)」で「機能しない」と判明済み。
- サーバー名のみ形式は公式には全ツール許可のはずだが、リモート環境では allow に載っているにもかかわらずプロンプトが表示され、抑止できないことが実挙動で確認された。
- 6/27 報告書には「ツール名完全一致の `mcp__mcp-gsheets__sheets_get_values` も追加して解決した」と記録されているが、**git 全履歴を検索してもこのルールは一度もコミットされていない**（コミットされたのはサーバー名形式 `fac2bb8` とワイルドカード `45c77f2` のみ）。「報告書に書いたのに実装が未コミット」パターンの3件目。
- 一方、よーんがプロンプトで「Always allow」をクリックした結果 `.claude/settings.local.json` にツール名完全一致ルールが書き込まれ、以後の呼び出しはすべてプロンプトなしで通った。つまり**完全一致ルールはこの環境で確実に機能する**。ただし `settings.local.json` は gitignore 済みのコンテナ固有ファイルで、リモートの新コンテナでは毎回消えるため恒久対策にならない。

## 実施内容

- `.claude/settings.json` の `permissions.allow` に、スキル・エージェントで使用実績のある mcp-gsheets ツール5種を完全一致形式で追加：
  - `mcp__mcp-gsheets__sheets_get_values`
  - `mcp__mcp-gsheets__sheets_batch_get_values`
  - `mcp__mcp-gsheets__sheets_append_values`
  - `mcp__mcp-gsheets__sheets_update_values`
  - `mcp__mcp-gsheets__sheets_batch_update_values`
- 機能していない `mcp__mcp-gsheets__*`（ワイルドカード）を削除。
- `mcp__mcp-gsheets`（サーバー名形式）は他環境で効く可能性があるため残した。
- 作業ブランチに push 後、routine が参照する master にも反映（コミット `1205f79`）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | allow にツール名完全一致の5ルールを追加、ワイルドカード1ルールを削除 |

## 設計判断

- 使用ツールの洗い出しは `.claude/skills` / `.claude/agents` / `projects` 配下の grep で行い、実際に参照されている5種（get / batch_get / append / update / batch_update）に絞った。全40ツールの列挙は、書き込み系・破壊系ツールまで無条件許可になるため採らなかった。

## 確認結果

- 「Always allow」クリックで完全一致ルールが `settings.local.json` に入った直後から、同一セッション内の `sheets_get_values` 呼び出し（5並列）がすべてプロンプトなしで通ることを確認。同じ形式を `settings.json` に恒久登録した。
- 実挙動（次回リモート routine でプロンプトなしで完走するか）は次回の日報 routine 実行で確認する。

## 今後の課題

- 「報告書に書いたのに実装が未コミット」パターンの3件目だったため、/record に実装コミット照合チェック（STEP 4.7）が追加済み（[報告書](./20260715_record_impl_commit_check/)）。今後はこのチェックで検出される。
- 新しいスキルが上記5種以外の mcp-gsheets ツール（`sheets_insert_rows` 等）を使う場合は、完全一致ルールの追加が必要。
