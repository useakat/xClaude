---
title: mcp-gsheets 認証をラッパーで両対応化＋mcp__* 無効ルール整理 — セッション履歴
date: 2026-06-29
sidebar:
  hidden: true
---

# セッション履歴

> 2026-06-29 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260629_mcp_gsheets_launcher_both_envs/)

---

## よーん *(22:56 JST)*

そういえば、なんで mcp-gsheets が使えなかったの？

### Claude *(22:56 JST)*

mcp-gsheets が落ちた原因を調べます。エラーは認証ファイルのパスに `${HOME}` が未展開で残っていたものでした。設定箇所を確認します。

*[ツール: `Bash`, `Read`]*

`.mcp.json` を確認しました。原因の核心が見えました。検証します。

*[ツール: `Bash`]*

調べました。原因が分かりました。

## なぜ mcp-gsheets が使えなかったか

エラーはこれでした:
```
ENOENT: no such file or directory, open '/root/xClaude/${HOME}/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json'
```
パスに **`${HOME}` が未展開のまま**残り、それが cwd（`/root/xClaude`）に相対パスとして連結されて壊れたパスになっています。

### 仕組み
1. `.mcp.json` は mcp-gsheets に認証を `"GOOGLE_SERVICE_ACCOUNT_KEY": "${GOOGLE_SERVICE_ACCOUNT_KEY}"` で渡す設計。
2. ところが **mcp-gsheets サーバーは Claude Code アプリ本体が起動する**プロセスで、そのプロセス環境には `GOOGLE_SERVICE_ACCOUNT_KEY` が**入っていなかった**（この値は `~/.bashrc` の `export`（112行目）で入るが、それは bash を起動したときだけ。MCP サーバーは bash を介さず起動されるため未設定）。
3. KEY が空のため mcp-gsheets は**フォールバックの認証ファイルパス**（`GOOGLE_APPLICATION_CREDENTIALS` 由来）を使おうとしたが、そこに **リテラルの `${HOME}`** が入っていた（シェル展開されない経路で設定されていた）。
4. node が `${HOME}/xClaude/gcp/...` を相対パス扱い → cwd 連結 → `/root/xClaude/${HOME}/xClaude/gcp/...` → ファイルなし。

### なぜ gws CLI / cron / record_output.py は動いたか
これらは **bash シェル経由**で動き、`.bashrc` 112行目が `GOOGLE_SERVICE_ACCOUNT_KEY` に実体 JSON を入れてくれる（record_output.py はその env を読むか、絶対パスの `SA_FILE` にフォールバック）。だから認証が通った。

**要するに**：対話セッションでは MCP サーバーに認証情報が伝わっておらず（env 非伝播）、フォールバック先のパスに未展開の `${HOME}` が混じっていて壊れた、というのが真因です。スクリプト側は別途 env を export しているので無事でした。

---

恒久対策の候補（やるなら）:
- `.mcp.json` の env を `${HOME}` 依存にせず**絶対パス**で渡す／`GOOGLE_SERVICE_ACCOUNT_KEY` を確実に MCP プロセスへ伝播させる
- もしくは「MCP は使わず gws CLI（`gws sheets …`）に寄せる」方針に統一

修正まで進めますか？

---

## よーん *(23:01 JST)*

以前 mcp-gsheets をリモートセッションでもローカルセッションでも使えるように設定したと思ったんだけど、変更ログなどからその辺確認できない？

### Claude *(23:01 JST)*

変更ログと報告書を確認します。

*[ツール: `Bash`]*

認証まわりの報告書が複数あります。直近で「ローカル/リモート両対応」にした 2件を読みます。

*[ツール: `Bash`]*

認証修正の経緯が確認できました。整理すると：

## 変更ログ・報告書で確認できた「両対応」設定の経緯

| 日付 | 内容 | 報告書 |
|---|---|---|
| 2026-06-04 | mcp-gsheets 認証を `GOOGLE_APPLICATION_CREDENTIALS` に統一 → **これがリモートを壊した** | `20260604_mcp_gsheets_auth_unification` |
| 2026-06-07 | settings.json から `GOOGLE_APPLICATION_CREDENTIALS` を削除し、`GOOGLE_SERVICE_ACCOUNT_KEY`（.mcp.json）に寄せて**リモートでも動くよう修正** | `20260607_mcp_gsheets_remote_auth_fix` |
| 2026-06-18 | 同じ問題が再発 → 再び settings.json から削除＋cron ラッパーで `GOOGLE_SERVICE_ACCOUNT_KEY` を export | `20260618_mcp_gsheets_auth_fix_and_cron` |

**設計の意図はまさに「両対応」でした**：
- `.mcp.json` が `GOOGLE_SERVICE_ACCOUNT_KEY`（JSON文字列）を渡す（ローカル・リモート共通）
- settings.json には `GOOGLE_APPLICATION_CREDENTIALS`（`${HOME}` 入りファイルパス）を**置かない**（Google Auth Library がこれを最優先するため、置くと壊れる）

そして 2026-06-18 報告書の「今後の課題」に、**まさに今回と同じ症状が過去3回再発している**と書かれています（根本原因＝`GOOGLE_APPLICATION_CREDENTIALS`（`${HOME}` パス）が MCP プロセスに渡ること）。

今回のエラー `/root/xClaude/${HOME}/xClaude/gcp/...` も同じパターンです。settings.json は現在クリーン（env は `GOOGLE_PROJECT_ID` のみ）なので、`GOOGLE_APPLICATION_CREDENTIALS` が**別の場所から MCP プロセスに漏れている**はず。発生源を特定します。

*[ツール: `Bash`]*

結論を整理します。

## 確認できたこと

**はい、よーんは過去に「ローカル・リモート両対応」をちゃんと設定していました。** 変更ログ・報告書に残っています（上の表）。設計の要点は：
- `.mcp.json` が `GOOGLE_SERVICE_ACCOUNT_KEY`（JSON文字列）を渡す ← 両環境共通で動く方式
- settings.json には `GOOGLE_APPLICATION_CREDENTIALS`（`${HOME}` 入りパス）を**置かない**

そして実際、**現在もこの設定は保たれています**（settings.json の env は `GOOGLE_PROJECT_ID` のみ、`.mcp.json` は `GOOGLE_SERVICE_ACCOUNT_KEY` 方式）。

## ただし今回また壊れた理由

`20260618` 報告書の「今後の課題」に、**この症状が過去3回再発している**と明記され、再発防止として「**CLAUDE.md に『settings.json に `GOOGLE_APPLICATION_CREDENTIALS` を書かない』と明記する**」が提案されていました。が、**その CLAUDE.md への明記は未実施**でした（今 grep して確認）。

今回の `/root/xClaude/${HOME}/xClaude/gcp/...` エラーは同じ系統の問題ですが、発生源が以前と違います：
- `GOOGLE_APPLICATION_CREDENTIALS` は **どのリポジトリ設定にも・どのシェル初期化ファイル（.bashrc / .profile / .local/bin/env / /etc/environment / .claude.json）にも無い**（grep で 0 件）。
- それでも bash の env には入っている（しかも展開済みの正しいパス）。
- 一方 MCP サーバーは未展開の `${HOME}` 版を見ていた。

つまり **`GOOGLE_APPLICATION_CREDENTIALS` は Claude Code を起動した親プロセスの環境から注入されており（リテラル `${HOME}` 込み）、それを mcp-gsheets 子プロセスが継承して Auth Library が最優先で掴んで失敗した**、という構図です。リポジトリ側の設定は正しいまま、起動環境側の混入で再発しています。

## 恒久対策の候補
- **A**: `.mcp.json` の env で `GOOGLE_APPLICATION_CREDENTIALS` を明示的に無効化（空 or 正しい絶対パス）して、継承した不正値を上書きする（最も確実）。
- **B**: `20260618` の宿題どおり CLAUDE.md に「settings.json/env に `GOOGLE_APPLICATION_CREDENTIALS` を書かない・混入させない」を明記（再発検知の指針）。
- **C**: 起動環境（親プロセス）の `GOOGLE_APPLICATION_CREDENTIALS` 注入元を特定して断つ。

恒久対策の実装計画を立てましょうか？（A/B/C の組み合わせを詰めます）

---

## よーん *(23:15 JST)*

一旦 git pull して

### Claude *(23:15 JST)*

いま **plan mode（読み取り専用）** が有効なので、`git pull`（書き込み操作）は実行できません。

plan mode を抜けてください（**Shift+Tab** で切り替え）。抜けたらすぐ `git pull` します。

— もしくは、ご自身で `! git pull` を実行いただいてもOKです。

---

## よーん *(23:20 JST)*

切り替えた

### Claude *(23:20 JST)*

git pull します。

*[ツール: `Bash`]*

git pull 完了しました（master）。**Already up to date** — リモートに新しい差分はなく、ローカルは最新です。

なお、別件の未コミット変更がローカルに残っています（pull では触っていません）:
- 変更: `.claude/skills/research-trivia/SKILL.md`、`docs/database.md`、`projects/w003/spec.md`、`projects/w002/.../image-plan.md`
- 削除: `projects/w002/image_template/`（5ファイル）
- 未追跡: `projects/visual_prompts/`

これらは今回の作業とは別件です。必要なら扱い（コミット/破棄）を確認します。先ほどの mcp-gsheets 恒久対策はどうしますか？

---

## よーん *(23:24 JST)*

実装計画を立てて

### Claude *(23:25 JST)*

*[ツール: `ToolSearch`, `EnterPlanMode`]*

investigation は十分に済んでいるので、設計を確定して計画を書きます。最後に1点だけ、認証ファイルの存在と他に mcp 設定が無いことを確認します。

*[ツール: `Bash`]*

設計が固まりました。計画を書きます。

*[ツール: `Write`]*

恒久対策の計画をまとめました。承認をお願いします。

*[ツール: `ExitPlanMode`]*

実装します。まずラッパースクリプトを作成します。

*[ツール: `Write`]*

`.mcp.json` をラッパー経由に変更します。

*[ツール: `Edit`]*

`.mcp.json` の編集が auto モードのセーフティ判定でブロックされました（理由：MCP 起動設定の自己改変は慎重に扱う、というルール）。プラン承認済みですが、判定レイヤーは `.mcp.json` 編集を別途センシティブ扱いします。回避はしません。

ラッパー（`scripts/mcp_gsheets_launch.sh`）は作成済みです。残るは `.mcp.json` の1箇所のみ。よーん側で適用してください。

**方法A：`!` でそのまま実行**（安全に置換する python ワンライナー）:
```
! python3 - <<'PY'
import json
p="/root/xClaude/.mcp.json"
d=json.load(open(p))
g=d["mcpServers"]["mcp-gsheets"]
g["command"]="bash"
g["args"]=["scripts/mcp_gsheets_launch.sh"]
json.dump(d,open(p,"w"),ensure_ascii=False,indent=2)
print(open(p).read())
PY
```

**方法B：手で編集** — `.mcp.json` の mcp-gsheets を:
```json
"command": "bash",
"args": ["scripts/mcp_gsheets_launch.sh"],
```
に変更（`env` の2行はそのまま）。

適用したら教えてください。その後 **MCP を再読み込み（`/mcp` または Claude 再接続）**して `sheets_get_values` の疎通を確認します。

（または、私に `.mcp.json` 編集を許可いただければこちらで適用します。）

---

## よーん *(23:32 JST)*

.mcp.json 編集を許可

### Claude *(23:32 JST)*

許可ありがとうございます。`.mcp.json` を編集します。

*[ツール: `Edit`]*

CLAUDE.md に再発防止メモを追記します。実装ルールの Google サービス連携セクションに追加します。

*[ツール: `Read`, `Bash`, `Read`, `Edit`]*

構文チェックと、ラッパー単体での認証準備（GOOGLE_APPLICATION_CREDENTIALS の unset・KEY 補完）を検証します。

*[ツール: `Bash`]*

実装・検証完了しました。

## 検証結果（すべて OK）
- `bash -n scripts/mcp_gsheets_launch.sh` 構文 OK、`.mcp.json` は valid JSON
- ラッパー動作：混入していた `GOOGLE_APPLICATION_CREDENTIALS`（`${HOME}` 付き不正パス）を **unset で除去**、`GOOGLE_SERVICE_ACCOUNT_KEY` をローカル JSON から補完（length 2398）→ Auth Library が KEY を使える状態になる
- `npx` は `/usr/bin/npx` で解決可能

## 変更ファイル
| ファイル | 変更 |
|---|---|
| `scripts/mcp_gsheets_launch.sh` | 新規。`GOOGLE_APPLICATION_CREDENTIALS` を unset＋KEY 補完して mcp-gsheets を起動 |
| `.mcp.json` | mcp-gsheets を `bash scripts/mcp_gsheets_launch.sh` 経由に変更 |
| `CLAUDE.md` | 「env に `GOOGLE_APPLICATION_CREDENTIALS` を書かない／ラッパーで unset」の再発防止メモを追記 |

## 最終確認（よーんにお願い）
設定変更を反映するには **MCP の再読み込みが必要**です。`/mcp` で再接続するか Claude を再起動してから、私が `sheets_get_values`（outputs ヘッダー取得など）で疎通を確認します。

再読み込みしたら教えてください。その後この変更を `/record` で記録します（mcp-gsheets 認証修正の4回目・CLAUDE.md 明記で再発防止）。

---

## よーん *(23:41 JST)*

Help me fix the issues reported by /doctor below.

For each issue: briefly explain what the fix will do, then ask me to confirm before running any shell command that deletes files, modifies global config, or changes my installation. Safe read-only checks are fine without asking. If a suggested fix looks wrong for my setup, say so instead of running it.

- Settings (/root/xClaude/.claude/settings.json › permissions.allow): Invalid permission rule "mcp__*" was skipped: Wildcard tool name "mcp__*" is not supported in allow rules. An allow pattern must name the scope it widens — globs are permitted only in the tool position after a literal mcp__<server>__ prefix. Deny and ask rules accept wildcards anywhere

### Claude *(23:42 JST)*

/doctor の指摘は、まさに先ほど判明した「`mcp__*` ワイルドカードが効かない」件の正体です。`.claude/settings.json › permissions.allow` の `"mcp__*"` は**無効なルールとして無視されている**（許可として機能していない）ため、警告が出ています。

## 修正内容（settings.json の編集なので確認します）

`"mcp__*"` を削除します。これは2つの効果があります:
- /doctor の警告が消える
- **機能的な変化はなし**（元々スキップされて効いていなかったため）。mcp-gsheets は既に `mcp__mcp-gsheets`（サーバー単位の有効なルール）で許可済み。

ただし1点、判断が要ります。`mcp__*` は本来「全 MCP ツールを許可」する意図だったはず（今は無効）。他の MCP サーバー（Gmail / Drive / Calendar / github / xmcp）を**承認なしで使えるようにしたい**なら、有効な形式 `mcp__<server>__*` に置き換えます。

選択肢:
- **A（最小・推奨）**: `"mcp__*"` を削除するだけ。挙動は今のまま（他 MCP は使用時に都度承認）。警告だけ消す。
- **B（意図を復元）**: `"mcp__*"` を削除し、実際に使うサーバーの有効ワイルドカードを追加:
  `mcp__mcp-gsheets__*` / `mcp__claude_ai_Gmail__*` / `mcp__claude_ai_Google_Drive__*` / `mcp__claude_ai_Google_Calendar__*` / `mcp__github__*` / `mcp__xmcp__*`
  → これらを承認なしで使える（cron/routine 向けに有効。ただし許可範囲は広がる）。

どちらにしますか？（A / B）

---

## よーん *(23:46 JST)*

Bで、mcp__claude_ai_Google_Calendar__*　は追加しなくていい

### Claude *(23:47 JST)*

B で進めます（Calendar は除外）。`.claude/settings.json` を編集します。

*[ツール: `Read`, `Edit`]*

JSON の妥当性を確認します。

*[ツール: `Bash`]*

修正完了しました。

## 変更内容（`.claude/settings.json › permissions.allow`）
- 無効だった `"mcp__*"` を**削除**（/doctor 警告の原因）
- 冗長だった `mcp__mcp-gsheets` / `mcp__mcp-gsheets__sheets_get_values` を整理し、有効なワイルドカード形式に置換
- 追加した有効ルール（Calendar は除外）:
  - `mcp__mcp-gsheets__*`
  - `mcp__claude_ai_Gmail__*`
  - `mcp__claude_ai_Google_Drive__*`
  - `mcp__github__*`
  - `mcp__xmcp__*`

JSON 妥当性 OK、`mcp__*` 消去・5ルール追加を確認しました。これで /doctor の警告は解消し、各 MCP サーバーのツールが承認なしで使えます（cron/routine でも有効）。

---

未記録の作業が溜まっています（このセッションでまだ commit していない分）:
- **mcp-gsheets 起動ラッパー＋両対応化**（`scripts/mcp_gsheets_launch.sh`・`.mcp.json`・`CLAUDE.md`）
- **本 permissions.allow の修正**（`mcp__*` 無効ルール整理）

`/record` で記録できます。あわせて commit/push もしますか？（settings.json の permissions.allow 変更のみは確認不要ですが、ラッパー一式は記録対象です）

なお `.mcp.json`／settings の反映には **MCP の再読み込み（`/mcp` か再接続）** が必要です。再読み込み後に `sheets_get_values` で疎通確認できます。

STEP 1・2 を実行します。

*[ツール: `Bash`]*

STEP 3: 未記録の変更候補を提案します。

---

**変更ログ候補（未記録）**

1. **mcp-gsheets 認証をラッパーで両対応化＋`mcp__*` 無効ルール整理（CLAUDE.md 明記）** — 親プロセスから混入する `GOOGLE_APPLICATION_CREDENTIALS`（`${HOME}` 付き不正パス）を Auth Library が最優先で掴み認証失敗していた問題を、起動ラッパー `scripts/mcp_gsheets_launch.sh`（`unset`＋KEY 補完）で恒久対策。`.mcp.json` をラッパー経由に変更、CLAUDE.md に再発防止ルールを明記。あわせて /doctor 指摘の無効ルール `mcp__*` を有効な `mcp__<server>__*` 形式へ置換。
   - 関連コミット: 未コミット（作業ツリー）
   - 変更ファイル: `scripts/mcp_gsheets_launch.sh`（新規）、`.mcp.json`、`CLAUDE.md`、`.claude/settings.json`
   - 関連する過去の変更: **mcp-gsheets リモート認証修正**（06-07）、**mcp-gsheets 認証修正・record-note-posts cron 追加**（06-18）

補足: `.claude/settings.json` の変更は permissions.allow のみ（記録ルール上は確認不要ですが、今回はラッパー一式と一体の修正なのでコミットに含めます）。

記録してよいですか？（番号「1」/ スキップ）

---

## よーん *(23:50 JST)*

1

### Claude *(23:50 JST)*

STEP 4: 報告書を作成します。

*[ツール: `Write`]*
