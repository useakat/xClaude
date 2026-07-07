---
title: プロジェクトMCPサーバーの信頼確認を自動承認し、リモート実行でのgsheets切断を解消 — セッション履歴
date: 2026-07-07
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-07 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260707_mcp_gsheets_project_trust_auto_approve/)

---

## よーん *(08:19 JST)*

mcp-gsheets をリモートでも許可なく実行してほしい。以前そのための設定をした気がするのだが。。変更ログ確認して、修正計画を立てて

### Claude *(08:19 JST)*

変更ログとsettings.jsonを確認します。

*[ツール: `Bash`, `Read`, `Read`, `Bash`, `Bash`, `Bash`, `Bash`]*

変更ログと現在の設定を確認した結果をまとめます。

## 調査結果

**`mcp__mcp-gsheets__*` の許可は既に設定済みでした**（`.claude/settings.json` L71）。過去に何度も mcp-gsheets の接続不安定を修正した記録があります（変更ログより）：

- 7/3〜7/5にかけて計5件：起動パスの絶対パス化、npmキャッシュ対応、SessionStart hookでの事前ウォームなど
- 6/27：ヘッドレス実行（`claude -p`）では `mcp__*` ワイルドカードが効かないため `mcp__mcp-gsheets`（サーバー単位）を明示許可 → これが今の `mcp__mcp-gsheets__*` の元

**今回このセッション中に実際に起きたこと**を `logs/mcp_gsheets_launch.log` で確認したところ：

```
21:08:34  起動（コールドインストール）
22:35:04  再起動
23:19:43  再起動
```

セッション中に mcp-gsheets サーバーが2回、勝手に再起動していました。さきほどの `sheets_get_values` のエラー（`Tool permission stream closed`）は、この再起動のタイミングで通信が切れただけで、**権限（permission）の許可漏れではありません**。許可設定はすでに正しく、再試行すれば自動的に成功しています。

## 修正計画（提案）

1. **設定変更は不要** — 許可リストは既に正しい。追加のpermissions.allow修正はしない。
2. 再起動の原因（プラットフォーム側のMCP接続ライフサイクルによるものか、mcp-gsheets自体のクラッシュか）を切り分けるため、`mcp_gsheets_launch.sh` にプロセス終了理由をログするデバッグ行を足すかどうか検討 — ただし現状は再試行で自動復旧しており、実害（データ欠損・処理失敗）は出ていません。
3. 実害がない再接続の揺らぎのため、**恒久対応は見送り、既知事象として changelog に記録するだけ**にするのが妥当と考えます。

このまま「記録のみ」で進めてよいか、それとも再起動原因の追加調査（ログ強化など）まで踏み込みますか？

---

## よーん *(08:32 JST)*

いや、mcp-gsheets のget value の実行で許可を求められてるから、接続が切れたのが原因じゃないと思う。許可を求めたが一定時間過ぎても僕が反応しなかったからサーバーが接続をきったんだとおもう。もう一度その辺も含めて調べて

### Claude *(08:32 JST)*

*[ツール: `Bash`, `Bash`]*

ご指摘の通りでした。原因はサーバー接続の不安定さではなく、**プロジェクトのMCPサーバー信頼設定が空**だったことです。

## 判明した原因

`/root/.claude.json`（リポジトリ管理外・コンテナ固有のグローバル設定ファイル）内のこのプロジェクトのエントリを見ると：

```json
"mcpServers": {},
"enabledMcpjsonServers": [],
"disabledMcpjsonServers": [],
"hasTrustDialogAccepted": false
```

`.mcp.json` で定義している `mcp-gsheets`（や `xmcp`）が **どちらのリストにも入っていない＝未承認状態** です。

- `.claude/settings.json` の `permissions.allow` に書いた `mcp__mcp-gsheets__*` は「ツール単位の実行許可」
- 一方、`.mcp.json` で定義された MCP サーバー自体を起動してよいかの「サーバー単位の信頼確認」は別の仕組みで管理されており、それが `~/.claude.json` の `enabledMcpjsonServers` にあたる

このファイルは **リポジトリに含まれない・コンテナ固有の状態** です。リモート実行環境（routine/agent）は毎回まっさらなコンテナで動くため、この信頼状態が空のまま起動 → 実行中にサーバーの信頼確認ダイアログが発生 → 無人実行で誰も応答できず、一定時間後にタイムアウトしてサーバー接続が切れる、という流れだったと考えられます。ツール単位の許可（settings.json）だけでは、このサーバー単位の信頼確認をスキップできていませんでした。

## 修正案

`.claude/settings.json`（リポジトリ管理・全環境に反映される）に以下を追加する：

```json
"enableAllProjectMcpServers": true
```

これは Claude Code の公式設定キーで、`.mcp.json` に定義された全MCPサーバー（`mcp-gsheets`・`xmcp`）を信頼確認なしで自動承認するものです。コンテナ固有の `~/.claude.json` に依存せず、リポジトリ側で毎回確実に反映されます。

この内容で `.claude/settings.json` を修正してよろしいですか？

---

## よーん *(08:33 JST)*

Stop hook feedback:
[~/.claude/stop-hook-git-check.sh]: There are commit(s) on branch 'claude/zealous-fermi-ceduff' that GitHub will show as Unverified (missing signature, or committer email is not noreply@anthropic.com):
2c22a85 N noreply@anthropic.com
Please run 'git config user.email noreply@anthropic.com && git config user.name Claude', then 'git commit --amend --no-edit --reset-author' for the tip commit, or 'git rebase --exec "git commit --amend --no-edit --reset-author" origin/claude/zealous-fermi-ceduff' for earlier commits, then push.

### Claude *(08:33 JST)*

先ほど提案した `.claude/settings.json` への `enableAllProjectMcpServers: true` 追加について、進めてよいかご回答をお待ちしています。

---

## よーん *(08:36 JST)*

修正して

### Claude *(08:36 JST)*

*[ツール: `Edit`]*

`.claude/settings.json` に `enableAllProjectMcpServers: true` を追加しました。

```diff
{
  "autoMemoryEnabled": false,
+ "enableAllProjectMcpServers": true,
  "env": {
```

commitしてブランチ `claude/zealous-fermi-ceduff` にpushしてよろしいですか？

---

## よーん *(08:37 JST)*

Stop hook feedback:
[~/.claude/stop-hook-git-check.sh]: There are uncommitted changes in the repository. Please commit and push these changes to the remote branch.

### Claude *(08:37 JST)*

このStop hookのフィードバックは承認の代わりにはできません（CLAUDE.mdのルール通り）。commit・pushの可否について、よーんからの明示的な回答をお待ちしています。

---

## よーん *(12:36 JST)*

Ok

### Claude *(12:36 JST)*

*[ツール: `Bash`, `Bash`, `Bash`]*

`claude/zealous-fermi-ceduff` にpushしました（先ほどの日報コミットも含めて2件が反映されています）。

**変更内容**：`.claude/settings.json` に `enableAllProjectMcpServers: true` を追加し、`.mcp.json` 定義のMCPサーバー（mcp-gsheets・xmcp）をリポジトリ側で恒久的に信頼済みとしました。これでリモート実行時にサーバー単位の信頼確認待ちが発生しなくなるはずです。

この変更を`/record`で記録しますか？

*[ツール: `Read`]*

Recorded titles を把握しました。次に直近のgit履歴を確認します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

f9a95d2以前は既に記録済み（changelogの日付セクションに反映済み）なので、今回の調査範囲はこれで十分と判断しました。

---

**変更ログ候補（未記録）**

以下の変更が記録されていません。記録するものを選んでください（複数選択可）：

1. **プロジェクトMCPサーバーの信頼確認を自動承認し、リモート実行でのgsheets切断を解消** — `.mcp.json` 定義のMCPサーバー（mcp-gsheets等）がコンテナ固有の信頼状態に依存し、リモート/routine実行のたびに未承認状態から始まり無人実行中にタイムアウト・接続断していた問題を、`enableAllProjectMcpServers: true` で恒久解消。
   - 関連コミット: `2df5059 fix: プロジェクトMCPサーバーの信頼確認をスキップし、リモート実行でのgsheets切断を解消`
   - 変更ファイル: `.claude/settings.json`
   - 関連する過去の変更: mcp-gsheets 起動コマンドを `${CLAUDE_PROJECT_DIR}` に変更（2026-07-05）／mcp-gsheets のコールドインストールを SessionStart hook で事前ウォーム（2026-07-04）／その他 mcp-gsheets 接続安定化の一連の修正（2026-07-03複数件）

（記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。）

---

## よーん *(23:41 JST)*

1

### Claude *(23:41 JST)*

*[ツール: `Bash`, `Read`, `Write`]*

STEP 4.5: セッション履歴を保存します。

*[ツール: `Bash`]*
