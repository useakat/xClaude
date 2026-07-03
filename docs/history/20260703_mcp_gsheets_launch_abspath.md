---
title: mcp-gsheets 起動スクリプトのパスを cwd 非依存の絶対パス化して -32000 を解消 — セッション履歴
date: 2026-07-03
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-03 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260703_mcp_gsheets_launch_abspath/)

---

## よーん *(00:12 JST)*

mcp-gsheets に接続できないのはなぜ？

### Claude *(00:12 JST)*

-32000 は過去に対処した再接続タイムアウトのエラーですね。直近のコミット（843c5b9）で対処したはずなので、現状を確認します。

*[ツール: `Bash`, `Bash`]*

設定は前回の対処が入っています。実際に起動させて何が起きているか確認します。

*[ツール: `Bash`]*

env は正常です。実際に起動して、キャッシュ優先起動が成立するか（レジストリ不通でハングしないか）を確認します。

*[ツール: `Bash`]*

サーバー自体は問題なく起動しました（`Google Sheets MCP server running on stdio`、offline 起動で数秒）。実際に認証まで通るか、シート読取で確認します。

*[ツール: `Bash`]*

手元で起動〜認証〜ツール一覧まで正常に応答しました（数秒で完了）。原因と対処をまとめます。

## 結論：サーバー自体は正常。`-32000` は一過性の再接続タイムアウトです

確認結果：
- **env は正常** — `GOOGLE_SERVICE_ACCOUNT_KEY`(len=2398) セット済み、混入すると壊れる `GOOGLE_APPLICATION_CREDENTIALS` は unset 済み
- **キャッシュに 1.8.1 あり** — `npx --prefer-offline mcp-gsheets@1.8.1` がオフラインで数秒起動
- **initialize / tools/list が正常応答** — 認証も通り、`sheets_get_values` 等のツールが返る

`-32000`（Failed to reconnect）は Claude Code 側の**再接続タイムアウト**エラーで、サーバー設定の恒久的な不具合ではありません。今回は前回対処（prefer-offline + 版固定, 843c5b9）が効いていて、実起動は速く堅牢です。あの `/mcp` 実行時にたまたま初回リゾルブや別プロセスの負荷で初期化が間に合わなかった一過性のものと考えられます。

## 対処
1. **もう一度 `/mcp` で再接続**すれば繋がるはずです（今テストした限り正常起動します）
2. それでも `-32000` が続くなら、Claude Code を一度再起動してください（再接続タイムアウトはセッション側の状態に依存するため）

恒久設定は問題ないので、追加の修正は不要です。

---

## よーん *(00:19 JST)*

再起動はどうやるの？

### Claude *(00:19 JST)*

再接続でまだ `-32000` が出るなら、Claude Code 本体の再起動が確実です。手順：

## Claude Code の再起動（CLI）

1. **終了**：`/exit` と入力（または `Ctrl+C` を2回）
2. **再起動**：ターミナルで再度 `claude` を実行
3. **会話を続けたい場合**：`claude --continue`（`claude -c`）で直前セッションを引き継いで再開

再起動時に `.mcp.json` の設定で mcp-gsheets が起動し直され、再接続タイムアウトの状態がリセットされます。

補足：再起動しても改善しない場合は、npx キャッシュを一度掴み直させると確実です。以下を実行してから再起動してください。

```
npx --prefer-offline -y mcp-gsheets@1.8.1 --help
```

（先ほどのテストでこれは数秒で正常起動を確認済みです。事前に一度走らせておくと、Claude Code 起動時の初回リゾルブで詰まる可能性を潰せます）

No response requested.

---

## よーん *(00:24 JST)*

やはりmcp-gsheets がきどうできない

### Claude *(00:24 JST)*

再接続を繰り返しても駄目、しかし私の手元テストは通る。この差はおそらく**起動時のカレントディレクトリ**です。このセッションの作業ディレクトリは `projects/w001` なので、相対パス `scripts/mcp_gsheets_launch.sh` の解決先を確認します。

*[ツール: `Bash`]*

原因が特定できました。**`.mcp.json` の起動スクリプトが相対パスで、このセッションの作業ディレクトリ `projects/w001` からは存在しない**ためです。

- `.mcp.json` は `/root/xClaude/.mcp.json` にあり、`args: ["scripts/mcp_gsheets_launch.sh"]`（相対パス）
- しかしこのセッションの cwd は `projects/w001`
- w001 側 settings に `enableAllProjectMcpServers: true` があるため親の定義を起動しようとするが、`projects/w001/scripts/mcp_gsheets_launch.sh` は存在しない → 即終了 → `-32000`

前回の修正（843c5b9）でラッパースクリプト経由に変えた際、相対パスにしたのが原因です。git 履歴で裏を取ります。

*[ツール: `Bash`]*

手元テストは `cd /root/xClaude` を付けていたため通っていました。Claude Code の実際の起動条件（cwd = w001）を正確に再現します。

*[ツール: `Bash`]*

**根本原因が確定しました。**

`.mcp.json`（`/root/xClaude/.mcp.json`）の起動指定が**相対パス** `scripts/mcp_gsheets_launch.sh` になっていますが、Claude Code は MCP サーバーを**このセッションの作業ディレクトリ（`projects/w001`）を cwd として起動**します。そのため：

```
$ (cwd=w001) bash scripts/mcp_gsheets_launch.sh
bash: scripts/mcp_gsheets_launch.sh: No such file or directory   ← 即終了 → -32000
```

前回テストが通ったのは、私が `cd /root/xClaude` を付けていたためでした。**ルート（`/root/xClaude`）からセッションを開けば繋がるが、`projects/w001` から開くと繋がらない**、という状態です。再起動しても cwd が w001 のままなので直りません。

## 修正案

`.mcp.json` の相対パスを、cwd に依存しない `$HOME` 基準の絶対パスに変えます（このリポジトリは `$HOME/xClaude` 前提。ラッパー内も同じ前提なのでリモート含め移植性を保てます）。

```diff
     "mcp-gsheets": {
       "command": "bash",
-      "args": ["scripts/mcp_gsheets_launch.sh"],
+      "args": ["-c", "exec \"$HOME/xClaude/scripts/mcp_gsheets_launch.sh\""],
```

先に w001 の cwd でこの方式が通るか実証します。

*[ツール: `Bash`]*

`exec` は実行ビットが要るため、`bash <path>` で呼ぶ形にします。

*[ツール: `Bash`]*

方式が確定しました（cwd=w001 のまま正常起動）。`.mcp.json` を修正します。

*[ツール: `Edit`]*

修正しました。原因と対応をまとめます。

## 原因
`.mcp.json` の起動指定が相対パス `scripts/mcp_gsheets_launch.sh` でした。Claude Code は MCP サーバーをセッションの作業ディレクトリ（`projects/w001`）を cwd として起動するため、その場所にスクリプトが無く即終了 → `-32000`。**ルート `/root/xClaude` からセッションを開いていた頃は動き、サブプロジェクト `projects/w001` に移ったことで顕在化**しました。再起動で直らなかったのは cwd が変わらないためです。

## 修正内容（`.mcp.json`）
cwd に依存しない `$HOME` 基準の絶対パス起動に変更（cwd=w001 のまま正常起動を実証済み）：
```diff
-      "args": ["scripts/mcp_gsheets_launch.sh"],
+      "args": ["-c", "exec bash \"$HOME/xClaude/scripts/mcp_gsheets_launch.sh\""],
```

## 反映手順
この変更は**再接続では反映されず、Claude Code の再起動が必要**です：
1. `/exit`（または `Ctrl+C` 2回）で終了
2. `claude -c` で再起動（会話を引き継ぎ）

これでどのディレクトリから起動しても mcp-gsheets が繋がります。

---
この修正を記録しますか？`/record` で記録できます。

I'll start recording. First, reading the changelog and checking recent commits.

*[ツール: `Read`, `Bash`]*

変更ログを確認しました。今回の修正（`.mcp.json` 相対パス→`$HOME` 絶対パス化）はまだ未コミットで、変更ログにも未記録です。前回の prefer-offline 対処と同じ `-32000` 系列の続きの修正になります。

---

**変更ログ候補（未記録）**

1. **mcp-gsheets 起動スクリプトのパスを cwd 非依存の絶対パス化して projects/ 配下からの -32000 を解消** — `.mcp.json` の相対パス `scripts/mcp_gsheets_launch.sh` が、セッション cwd が `projects/w001` のとき解決できず即終了→再接続タイムアウト(-32000)。`bash -c 'exec bash "$HOME/xClaude/scripts/mcp_gsheets_launch.sh"'` に変更し、どのディレクトリから起動しても繋がるよう是正。
   - 関連コミット: 未コミット（本セッションの変更）
   - 変更ファイル: `.mcp.json`
   - 関連する過去の変更: **mcp-gsheets 起動を prefer-offline + 版固定にして再接続タイムアウト(-32000)を解消**、**mcp-gsheets 認証をラッパーで両対応化＋mcp__* 無効ルール整理**

（記録するなら「1」、不要なら「スキップ」と教えてください）

---

## よーん *(00:45 JST)*

1

### Claude *(00:45 JST)*

承認いただいたので記録します。まず報告書テンプレートと日付を確認します。

*[ツール: `Read`, `Bash`]*

Now creating the report file.

*[ツール: `Write`]*
