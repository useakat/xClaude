---
title: settings.local.json を git 管理化し mcp-gsheets 許可5ルールを配布（リモートで settings.json の許可が効かないため）
date: 2026-07-16
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260716_settings_local_json_git_managed/)

## 背景・動機

7/16 朝の日報 routine（reporter-daily）で、`sheets_get_values` の実行許可プロンプトが再び表示された。前日 7/15 の対策（[mcp-gsheets ツール許可を完全一致形式で明示登録](./20260715_mcp_gsheets_tool_allow_exact_rules/)）で `.claude/settings.json` に完全一致5ルールを登録済みで、そのコミット `1205f79` は今回のコンテナに clone 時点から含まれていたことを確認した。つまり「実装漏れ」ではなく、**対策自体がリモートでは効いていなかった**。

セッション内で切り分けテストを実施した：

- `settings.json` にのみ登録済みで、セッション中一度もクリック承認していない読み取り専用ツール `sheets_batch_get_values` を、MCP サーバー接続完了後に呼び出す
- 1回目：許可プロンプトが表示された（よーんが Allow once で通過）
- 2回目（再確認）：再びプロンプトが表示された（Deny で確認終了）
- 一方、朝のプロンプトで「Always allow」をクリックした結果 `.claude/settings.local.json` に書き込まれた `sheets_get_values` は、以後6回以上の呼び出しがすべてプロンプトなしで通った

この結果から以下が確定した：

- **リモート（managed）環境では、リポジトリの `.claude/settings.json` にある MCP ツール許可ルールは参照されない**（接続タイミングは無関係。当初はサーバー接続中の呼び出しによるレースコンディション仮説もあったが、接続完了後のテストで棄却）
- **同じルール文字列でも `.claude/settings.local.json` に置けば効く**（クリック承認の書き込み先で、実挙動で2日連続実証）

settings.local.json はコンテナ固有ファイル（gitignore 済み）のため新品コンテナでは毎回消える。そこで「効く場所」にファイルを配布する方式として、settings.local.json 自体を git 管理する対策を採った。

## 実施内容

- `.gitignore` から `.claude/settings.local.json` の行を削除し、git 追跡対象にした
- `.claude/settings.local.json` を、スキル・エージェントで使用実績のある mcp-gsheets ツール5種の完全一致ルールだけの内容で作成：
  - `mcp__mcp-gsheets__sheets_get_values`
  - `mcp__mcp-gsheets__sheets_batch_get_values`
  - `mcp__mcp-gsheets__sheets_append_values`
  - `mcp__mcp-gsheets__sheets_update_values`
  - `mcp__mcp-gsheets__sheets_batch_update_values`
- 作業ブランチにコミット後、routine が参照する master にも反映（コミット `0774065`）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.gitignore` | `.claude/settings.local.json` の除外行を削除 |
| `.claude/settings.local.json` | mcp-gsheets 読み書き5ツールの完全一致 allow ルールのみで新規作成（git 追跡対象） |

## 設計判断

- **SessionStart フックで settings.local.json を生成する案（案B）も検討したが、ファイル直接配布を選んだ**。リモートが settings.json の許可ルールを無視する以上、同ファイルのフック定義も無視される可能性が否定できず、配布方式ならその不確実性がない。
- `settings.json` 側の完全一致5ルール（`1205f79`）は削除しなかった。ローカル環境・headless cron では機能する実績があるため。
- クリックで書かれていた既存の settings.local.json（`sheets_get_values` 1件のみ）は、それを包含する厳選5ルールで置き換えた。全40ツールの列挙は書き込み系・破壊系まで無条件許可になるため採らなかった（7/15 報告書と同じ判断）。

## 確認結果

- 切り分けテスト2回で「settings.json のルールは効かず、settings.local.json のルールは効く」ことを確認（上記）。
- 配布した settings.local.json が新品コンテナで実際にプロンプトを抑止するかは、次回の日報 routine 実行で確認する。

## 今後の課題

- **次回 routine での実挙動確認**（プロンプトなしで完走するか）。
- **よーんのローカルマシンでの初回 pull**：ローカルに未追跡の settings.local.json が既にある場合、pull がチェックアウト衝突で失敗する。ローカル版を一度退避してから pull し、必要なルールを統合する必要がある。
- **「Always allow」クリックが git 差分になる**：今後どの環境でもクリックのたびに settings.local.json が書き換わり、`commit_and_sync.sh`（全ファイルステージ）経由で routine のコミットに同乗して master に入り得る。意図しない許可が増えていないか、定期的に差分を確認する。
- 「settings.json は無視・settings.local.json は有効」というリモート側の挙動が意図的な仕様か実装の隙間かは不明。将来のハーネス更新で塞がれた場合は、routine の Sheets 読み取りをサービスアカウント認証のスクリプトへ移す構造的対策（案C）に移行する。
