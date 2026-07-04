---
title: mcp-gsheets のコールドインストールを SessionStart hook で事前ウォームし、routine 実行時の接続失敗を解消 — セッション履歴
date: 2026-07-04
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-04 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260704_mcp_gsheets_sessionstart_prewarm/)

---

### Claude *(06:08 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `ToolSearch`, `ToolSearch`, `ToolSearch`, `ToolSearch`, `ListConnectors`, `Bash`, `ToolSearch`, `Bash`, `ToolSearch`, `ToolSearch`, `ToolSearch`, `PushNotification`]*

<routine_summary>
7月3日の日報作成が実行できませんでした。データ取得元の mcp-gsheets（Google Sheets 連携）がこのリモート環境で接続されておらず、投稿数・引用数・リプライ数・投稿一覧を取得できません。

確認した内容：
- .mcp.json に mcp-gsheets サーバー設定はあり、認証情報（GOOGLE_SERVICE_ACCOUNT_KEY）も環境変数に存在
- しかしこのセッションでは Gmail・Google Drive・github の MCP サーバーのみ接続されており、mcp-gsheets は接続対象に含まれていない
- ツール検索でも mcp-gsheets 関連ツールが一切見つからず

想定される原因：このリモート実行環境が、bash 経由でローカルプロセス（npm install → node 起動）を立ち上げる方式の mcp-gsheets サーバーを許可していない可能性があります。

対応が必要です。ローカル環境で実行するか、リモート環境でこの MCP サーバーを使えるようにする設定変更が必要かご確認ください。
</routine_summary>

---

## よーん *(09:58 JST)*

mcp-gsheets が実行環境によって起動できない問題は、最近の懸案事項。直近でも対策した気がするんだが。。変更ログなどを調べて、最近対策を確認してみて。まだ修正はしないで

### Claude *(09:58 JST)*

*[ツール: `Bash`, `Bash`, `Read`, `Read`, `Read`, `Bash`, `Bash`, `Bash`, `Bash`]*

直近の変更ログを確認しました。**すでに同じ問題への対策が3件、7月3日（今日）に立て続けに入っています**。

## 確認できた対策（新しい順）

1. **`20260703_mcp_gsheets_local_install`** — 現在のスクリプトの中身。フレッシュなクラウドコンテナで `npm --prefer-offline` が古いキャッシュを掴んで `ETARGET` エラーになり起動失敗する問題を解消するため、バージョン固定でローカルに一度だけ npm install → 以降は `node` 直接起動、という方式に変更済み。
2. **`20260703_mcp_gsheets_launch_abspath`** — 起動スクリプトのパスを絶対パス化（cwd 依存を解消）。
3. **`20260703_mcp_gsheets_prefer_offline_pin`** — その前段の対策（版固定＋prefer-offline）。

いずれも「今後の課題」に **「新方式が実際の MCP 再接続で効くか確認できるのは次セッション以降」** と書かれており、今日のこの routine セッションがまさにその「次セッション」に当たります。

## 今回、実際に何が起きていたか

- 起動スクリプト自体を手元で直接実行してみたところ、**正常に動作**しました（`added 157 packages in 10s` → `Google Sheets MCP server running on stdio`）。スクリプトのロジックは壊れていません。
- ところが実際の Claude セッションでは、mcp-gsheets は「接続中」リストにすら現れず、ツール検索でも一切ヒットしませんでした。

**推測される原因**：このコンテナは今回が初回起動でキャッシュが空だったため、npm install に約10秒かかっています。Claude Code 側の MCP 初期接続には（今回のように）一定のタイムアウトがある可能性があり、その間に stdio ハンドシェイクが間に合わず「未接続」のまま切り捨てられた、というのが最も筋が通る説明です。稼働中の既存プロセスには新方式が反映されないという「今後の課題」の裏返しで、**新規コンテナの初回コールドインストールがタイムアウトに間に合わない**という、まだ潰し切れていないケースに見えます。

なお診断のため手動でスクリプトを1回実行したので、このコンテナの npm キャッシュ（`~/.cache/mcp-gsheets/1.8.1`）は温まった状態になっています。コード変更は一切していません。

修正は指示通り行っていません。対策するなら「初回コールド起動時にタイムアウトが間に合うか」を再現確認した上で、必要ならインストールをセッション起動前（フック等）で先行させる方式を検討する、という方向になりそうです。

---

## よーん *(10:02 JST)*

修正計画を立てて

### Claude *(10:03 JST)*

*[ツール: `Bash`, `Bash`, `Bash`]*

変更ログ・報告書の確認と、実際に起動スクリプトを手元で動かしてみた検証結果から、以下の修正計画を立てました。**まだ何も変更していません。**

## 根本原因の仮説

- ランチャースクリプト自体（バージョン固定ローカル install → node 直接起動）は正しく動作することを確認済み（手動実行で `added 157 packages in 10s` → `Google Sheets MCP server running on stdio`）。
- 今回失敗したのは、**このコンテナが初回起動でキャッシュが空だったため**、npm install に約10秒かかり、その間に Claude Code 側の MCP 初期接続がタイムアウトして「未接続」のまま切り捨てられた、というのが最有力。
- `session-start-hook` スキルの説明によると、Claude Code on the web は **SessionStart hook 完了後の状態をコンテナごとキャッシュする**仕組みがある。つまり「フックで一度 install を走らせておけば、以降そのコンテナから起動する全セッションは最初からキャッシュ済み」という前提が使える。これは 06/29 の報告書で却下された「案1（環境側でキャッシュを事前ウォーム）」と似ているが、あのときは「毎回・全環境で確実に走る保証がない対症療法」という理由での却下だった。SessionStart hook はその保証（＝コンテナキャッシュへの焼き込み）を Claude Code 側の仕組みとして持っているため、却下理由が当てはまらない。

## 修正計画（3ステップ）

**Step 1: install ロジックの共通化**
`scripts/mcp_gsheets_launch.sh` の「バージョン固定ローカル install（`.installed` マーカー確認込み）」部分を `scripts/mcp_gsheets_install.sh` として切り出す（冪等・何度呼んでも安全）。
`mcp_gsheets_launch.sh` はそれを呼んでから `exec node` するだけにする。ロジックの二重管理を避けるため。

**Step 2: SessionStart hook で事前ウォーム**
`.claude/settings.json` の既存 `SessionStart` フック配列に、以下を追加登録：
```bash
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  bash "$CLAUDE_PROJECT_DIR/scripts/mcp_gsheets_install.sh" >&2
fi
```
- **同期実行**（async は使わない）。async だと「セッション開始と同時にバックグラウンドで走る」ため、まさに今回のレースコンディションを再現してしまう。ブロッキングで完了させてから初めて「コンテナ状態がキャッシュされる」という前提に乗る。
- `$CLAUDE_CODE_REMOTE` でリモート限定にする（ローカル環境は影響を受けないようにする＝スキルの推奨）。
- 冪等なので毎回叩いても実害なし（2回目以降は marker 確認だけで数百ms）。

**Step 3: 計測ログの追加**
`mcp_gsheets_launch.sh`（および install スクリプト）に、開始/install完了/exec直前のタイムスタンプを `logs/mcp_gsheets_launch.log` に stderr 経由で残す処理を追加。今回は「タイムアウトで切られた」という推測止まりで実測データがないため、次に何かあったときに「何秒でどこまで進んだか」を確認できるようにする。

## 検証方法

- Step 1–3 実装後、**このセッション内では検証できない**（コンテナキャッシュが焼き直されるのは次回以降のセッション/コンテナ再構築時のため）。次回の日報 routine 実行時に `sheets_get_values` 系ツールが最初から使えるかで確認する。
- 万一それでも失敗した場合は、追加したログを見て「install に何秒かかったか」「そもそも hook が走ったか」を切り分けられる。

## 未確定・リスク

- Claude Code 側の MCP 接続タイムアウトの正確な秒数は非公開のため、「10秒待てば必ず間に合う」という確証はない（あくまで状況証拠からの仮説）。
- SessionStart hook 完了後に本当にコンテナ状態が永続キャッシュされるかは、スキルの説明を根拠にした前提であり、実環境での動作は次回セッションでしか確認できない。

この計画で進めてよければ実装します。

---

## よーん *(10:20 JST)*

実装して

### Claude *(10:20 JST)*

*[ツール: `Read`, `Read`, `Bash`, `Write`, `Write`]*

Next, register the SessionStart hook in `.claude/settings.json`.

*[ツール: `Edit`, `Bash`, `Bash`]*

テストで判明しました — `$HOME/xClaude` という決め打りパスが実行環境によって repo の実体と一致しない場合があり（このサンドボックスでは `$HOME=/root` だが repo は `/home/user/xClaude`）、新しく追加した install スクリプト呼び出し行がまさにそこで失敗しました。ついでにこれも直しておきます（スクリプト自身の場所を起点に解決する方式にして `$HOME` 依存を削除）。

*[ツール: `Write`, `Write`, `Bash`]*

All working correctly now — cold install ~11.5s, warm re-run and launch both near-instant, logging works. Let me test the SessionStart hook line itself.

*[ツール: `Bash`, `Bash`, `Bash`]*

Logs are tracked in this repo, so I'll clear the test noise before committing — real entries will accumulate from actual use.

*[ツール: `Bash`, `Bash`]*

実装完了、動作確認も済みました。

## 変更内容

1. **`scripts/mcp_gsheets_install.sh`（新規）** — install ロジックを共通化。冪等（マーカーがあれば即 exit）。パス解決は `$HOME` 前提をやめ、スクリプト自身の場所から辿る方式に変更。
2. **`scripts/mcp_gsheets_launch.sh`** — install 部分を上記スクリプト呼び出しに置き換え、実行タイミングを `logs/mcp_gsheets_launch.log` に記録するよう変更。同じく `$HOME/xClaude` 決め打ちをやめた。
3. **`.claude/settings.json`** — `SessionStart` hook にリモート限定・同期実行で install スクリプトを叩く行を追加（コンテナキャッシュへの焼き込み狙い）。

## 動作確認結果

- 構文チェック・JSON バリデーション：OK
- コールドキャッシュから実行 → 11.5秒で install 完了、ログ記録も正常
- ウォーム状態での再実行 → 0.02秒（即座に「already warm」判定）
- `launch.sh` 実行 → 正常に `Google Sheets MCP server running on stdio`
- hook の実行文自体（`CLAUDE_CODE_REMOTE` ガード込み）も単体で動作確認済み

なお検証中に既存コードにも `$HOME/xClaude` 決め打ちパスの潜在バグを発見したため、計画になかった範囲ですが同時に修正しました（このサンドボックスでは `$HOME=/root` だが repo 実体は `/home/user/xClaude` にあり、決め打ちだと解決に失敗するため）。

テスト時に生成されたログ内容はコミット前に空にしてあります。

この内容で commit & push してよろしいですか？（対象ブランチ: `claude/zealous-fermi-77xftg`）

---

## よーん *(10:24 JST)*

Stop hook feedback:
[~/.claude/stop-hook-git-check.sh]: There are uncommitted changes in the repository. Please commit and push these changes to the remote branch.

### Claude *(10:24 JST)*

このメッセージは Stop hook からのフィードバックであり、よーんの承認とはみなしません。commit / push は行わず、明示的な返事をお待ちします。

---

## よーん *(10:26 JST)*

commit & push &record

### Claude *(10:26 JST)*

*[ツール: `Bash`]*

Already on the correct branch. Committing now.

*[ツール: `Bash`, `Bash`, `Bash`]*

`claude/zealous-fermi-77xftg` に push しました。次に `/record` を実行します。

*[ツール: `Skill`, `Read`, `Bash`, `Bash`]*

**変更ログ候補（未記録）**

以下の変更が記録されていません。記録するものを選んでください（複数選択可）：

1. **mcp-gsheets のコールドインストールを SessionStart hook で事前ウォームし、routine 実行時の接続失敗を解消** — フレッシュなクラウドコンテナで npm install が MCP 接続タイムアウトに間に合わず routine で Sheets 系ツールが未接続になる問題を、SessionStart hook での事前 install（コンテナキャッシュへの焼き込み）で解消。ついでに `$HOME` 決め打ちパスの潜在バグも修正。
   - 関連コミット: `669bcd1 fix: mcp-gsheets のコールドインストールを SessionStart hook で事前ウォームし、routine 実行時の接続失敗を解消`
   - 変更ファイル: `.claude/settings.json`, `scripts/mcp_gsheets_install.sh`（新規）, `scripts/mcp_gsheets_launch.sh`
   - 関連する過去の変更: mcp-gsheets 起動を prefer-offline + 版固定にして再接続タイムアウト(-32000)を解消／mcp-gsheets 起動スクリプトのパスを cwd 非依存の絶対パス化して projects/ 配下からの -32000 を解消／mcp-gsheets 起動を prefer-offline → ローカルインストール方式に変更（フレッシュコンテナの ETARGET 回避）

（記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。）

---

## よーん *(10:29 JST)*

1

### Claude *(10:29 JST)*

*[ツール: `Bash`, `Bash`]*

Good, both agree on 2026-07-04. Now creating the report.

*[ツール: `Read`, `Write`]*

Now STEP 4.5: session history conversion.

*[ツール: `Bash`]*
