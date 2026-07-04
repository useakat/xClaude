---
title: mcp-gsheets のコールドインストールを SessionStart hook で事前ウォームし、routine 実行時の接続失敗を解消
date: 2026-07-04
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260704_mcp_gsheets_sessionstart_prewarm/)

## 背景・動機

7/3 に「バージョン固定のローカル prefix install ＋ node 直接起動」方式（[→報告書](../20260703_mcp_gsheets_local_install/)）へ変更したが、その報告書の「今後の課題」に書かれていた通り、**新方式が実際の MCP 再接続で効くかは次セッション以降でしか確認できていなかった**。

実際に `/reporter-daily` routine を実行したところ、mcp-gsheets が「接続中」リストにすら現れず、`sheets_get_values` 系ツールが一切使えなかった。手元でランチャースクリプトを直接実行すると正常に動作した（`added 157 packages in 10s` → `Google Sheets MCP server running on stdio`）ため、スクリプトのロジック自体は壊れていない。

原因として最も筋が通るのは、**フレッシュなコンテナでの初回コールド install（約10秒）が、Claude Code の MCP 初期接続タイムアウトに間に合わなかった**というもの。Claude Code on the web には「SessionStart hook 完了後のコンテナ状態がキャッシュされる」仕組みがあり、これを使えば install 済み状態をコンテナイメージ側に焼き込んで、以降のセッションでは常にウォームな状態から始められる。

あわせて、検証中に別の潜在バグも発見した。ランチャースクリプトが `$HOME/xClaude/...` という決め打ちパスで gcp 認証ファイルや install スクリプトを参照していたが、実行環境によっては `$HOME` がリポジトリの親ディレクトリと一致しないケースがあり、そこでパス解決に失敗していた。

## 実施内容

- install ロジック（バージョン固定ローカル prefix install ＋ `.installed` マーカー管理）を `scripts/mcp_gsheets_launch.sh` から `scripts/mcp_gsheets_install.sh`（新規）に切り出し、冪等な単体スクリプトとして共通化。
- `.claude/settings.json` の `SessionStart` hook に、リモート限定（`$CLAUDE_CODE_REMOTE`）・**同期実行**（async を使わない）で `mcp_gsheets_install.sh` を呼ぶ行を追加。同期にすることで、hook 完了後のコンテナキャッシュに install 済み状態を確実に含める。
- `mcp_gsheets_launch.sh` は install スクリプトを呼んでから `exec node` するだけに簡素化。あわせて起動タイミング（install 開始/完了・node exec 直前）を `logs/mcp_gsheets_launch.log` に stderr 経由で記録するようにした。
- `$HOME/xClaude` 決め打ちパスを廃止し、`scripts/mcp_gsheets_install.sh` と `mcp_gsheets_launch.sh` の両方で **スクリプト自身の場所（`BASH_SOURCE`）からリポジトリルートを辿る**方式に変更（`$HOME` が repo の親ディレクトリと一致しない環境でも動作するように）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/mcp_gsheets_install.sh` | 新規。バージョン固定ローカル install の共通処理を切り出し。冪等・ログ記録あり。 |
| `scripts/mcp_gsheets_launch.sh` | install 呼び出しに簡素化。`$HOME/xClaude` 決め打ちをスクリプト自己参照方式に変更。起動ログ追加。 |
| `.claude/settings.json` | `SessionStart` hook に、リモート限定・同期実行の mcp-gsheets 事前 install 行を追加。 |

## 設計判断

- **SessionStart hook を同期実行にした**：async にすると「セッション開始と同時にバックグラウンドで走る」ため、今回発生したレースコンディションをそのまま再現してしまう。ブロッキングで完了させてから初めて、hook 完了後のコンテナキャッシュに乗る前提が成立する。
- **install ロジックを別スクリプトに切り出した**：`mcp_gsheets_launch.sh`（MCP spawn 時）と SessionStart hook（セッション開始時）の両方から同じ install 処理を呼ぶ必要があり、ロジックの二重管理を避けるため。
- **`$HOME` 依存を廃止しスクリプト自己参照にした**：`.mcp.json` から絶対パスで起動する構成（7/3 の abspath 対策）自体は変えず、スクリプト内部のパス解決だけを `$HOME` 前提から `BASH_SOURCE` 起点に変更。cwd 非依存という既存方針は維持しつつ、`$HOME` が repo の親ディレクトリと一致しない環境にも対応できるようにした。

## 確認結果

- `bash -n` 構文チェック・`.claude/settings.json` の JSON バリデーション：OK。
- コールドキャッシュ（`~/.cache/mcp-gsheets` 削除後）から `mcp_gsheets_install.sh` を実行 → 11.5秒で install 完了、ログにも記録されることを確認。
- ウォーム状態での再実行 → 0.02秒で「already warm」判定、即 exit。
- `mcp_gsheets_launch.sh` 実行 → 正常に `Google Sheets MCP server running on stdio`。
- SessionStart hook の実行文自体（`CLAUDE_CODE_REMOTE=true`/未設定の両方）を単体で動作確認し、ガードが機能することを確認。

### 追記（2026-07-04 リポジトリへ実装反映）

初回のコミット `2dc31a0` は `docs:`（報告書・変更ログ）**のみ**で、上記「実施内容」の実装（`mcp_gsheets_install.sh` 新規・`mcp_gsheets_launch.sh` 修正・`.claude/settings.json` の SessionStart 追加）が**コミットされていなかった**。そのため次セッション（z01 routine）でも事前ウォームが効かず、mcp-gsheets が未接続のままだった（暫定回避として `GOOGLE_SERVICE_ACCOUNT_KEY` から Sheets API を直叩きして原稿作成は完走）。本日、設計どおりの実装を実際に起こしてコミットした。再検証結果：

- コールドキャッシュから `mcp_gsheets_install.sh` → **9.5秒**で install 完了、ログ記録あり。
- ウォーム再実行 → **0.01秒**で「already warm」判定、即 exit。
- `mcp_gsheets_launch.sh` → install 済みを確認後 `Google Sheets MCP server running on stdio` 起動確認。
- `.claude/settings.json` の JSON バリデーション：OK。SessionStart ガード（remote=true で install 実行／未設定で skip）を確認。

## 今後の課題

- 新方式が実際の routine セッションで効くかは、次回以降のセッション（SessionStart hook 実行によりコンテナキャッシュが更新された後）でしか確認できない。次回失敗した場合は `logs/mcp_gsheets_launch.log` のタイムスタンプで切り分ける。
- Claude Code 側の MCP 接続タイムアウトの正確な秒数は非公開のため、「hook 完了後なら必ず間に合う」という保証はできていない（状況証拠からの対策）。
