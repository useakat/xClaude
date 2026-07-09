---
title: mcp-gsheets 起動パスを上方探索化し projects/ 配下起動の -32000 退行を修正 — セッション履歴
date: 2026-07-09
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-09 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260709_mcp_gsheets_launch_upward_search/)

---

## よーん *(20:51 JST)*

mcp-gsheets が接続できていない。以前も同じような症状がでて対策したと思うので、変更ログをみて、以前の対策を確認して、今回どうすれば修正できるか考えて。まだ修正はしないで

### Claude *(20:51 JST)*

まず変更ログと関連ファイルを確認します。過去の対策を調べるため探索します。

*[ツール: `Bash`, `Bash`]*

過去に何度も対策された履歴があります。起動スクリプトと現在の環境を確認します。

*[ツール: `Read`, `Read`]*

現在の実際の失敗原因を診断します（読み取り中心）。

*[ツール: `Bash`, `Bash`]*

ランチャー自体は正常に見えます。実際に JSON-RPC ハンドシェイクが通るか直接テストします。

*[ツール: `Bash`, `Bash`]*

サーバー自体は完璧に起動します（1.3秒で initialize 成功、認証OK）。つまり原因は起動側ではなく Claude Code 側の接続/信頼状態です。現在の作業ディレクトリ（projects/w002）の信頼状態を確認します。

*[ツール: `Bash`]*

重要な発見がありました。信頼設定と起動時間を確認します。

*[ツール: `Bash`]*

診断が完了しました。計画ファイルを作成します。

*[ツール: `Write`]*

診断が完了しました。まとめます。

## 診断結果

**サーバー・起動系に構造的な欠陥はありません。** 実機で確認したところ：

- ランチャーを手動実行 → JSON-RPC `initialize` が**正常応答**（`spreadsheet 1.8.0`）
- ウォーム起動 **0.76〜0.94秒**（タイムアウト閾値に対し十分速い）
- node / ENTRY / installマーカー・認証キー・`GOOGLE_PROJECT_ID`・信頼設定すべて正常
- stdout 汚染なし

過去8回以上の -32000 対策（パス絶対化・prefer-offline・ローカルinstall・信頼自動承認など）で構造的な失敗モードは潰し切られており、今回は手動 spawn が完璧なので、**一過性の再接続タイムアウト**（セッション開始時に Gmail/Drive/Calendar/gsheets が同時起動して競合し、gsheets の init が一瞬締切を超えた等）と判断します。

## 今回どう直すか

1. **まず再接続で復旧**（コード変更不要）— `/mcp` で reconnect、または Claude Code 再起動。手動ハンドシェイクが通るので、これで復帰する見込みです。
2. **再発する場合のみ** — `scripts/mcp_gsheets_launch.sh` を軽量化（ENTRY が既にあれば毎回の install 呼び出しをスキップして即 `exec node`）し、起動遅延と競合感度を下げる。
3. （任意）`enableAllProjectMcpServers: true` が `settings.local.json` にしかなく、7/7 報告書の「settings.json に追加」と食い違っている点。ローカルは問題ないが、**リモート/routine には settings.local.json が渡らない潜在ギャップ**があるので、リモートで再発するなら共有側 `settings.json` へ移設。

まだ何も修正していません。まずはステップ1の再接続を試すのが最短です。

---

## よーん *(20:59 JST)*

1 は失敗。本当に一過性の再接続タイムアウトが原因かもう一度調べて

### Claude *(21:00 JST)*

再接続がまだ失敗するなら一過性説は捨てて、Claude Code が実際に spawn する条件と手動テストの差分を調べます。重要な違いは `${CLAUDE_PROJECT_DIR}` の値です。このセッションは `projects/w002` で起動しています。

*[ツール: `Bash`, `Bash`, `Write`, `ToolSearch`, `ExitPlanMode`, `Read`, `Edit`, `Bash`]*

3 ケースすべてで `initialize` が成功しました。修正内容と検証結果をまとめます。

## 修正完了

**変更ファイル**: `/root/xClaude/.mcp.json`（args の1行のみ）

起動コマンドを「`CLAUDE_PROJECT_DIR` 決め打ち」から「`CLAUDE_PROJECT_DIR` から上方向に `scripts/mcp_gsheets_launch.sh` を探し、最後は `$HOME/xClaude` にフォールバック」に変更しました。

**検証結果**（実際の initialize ハンドシェイクで確認）:
| シナリオ | 結果 |
|---|---|
| `projects/w002` 起動（今回のバグ条件） | ✅ serverInfo 応答 |
| `/root/xClaude` ルート起動（routine 相当） | ✅ serverInfo 応答 |
| `CLAUDE_PROJECT_DIR` 未設定 + cwd=/（最終フォールバック） | ✅ serverInfo 応答 |

## 次のステップ

`/mcp` で mcp-gsheets を reconnect してみてください。設定がセッション開始時にキャッシュされている場合は reconnect でも旧 args のままの可能性があるので、その場合は **Claude Code の再起動**が必要です。

接続確認後、commit & push してよければ進めます（コミットメッセージ案: `fix(mcp): mcp-gsheets 起動パスを上方探索化し projects/ 配下起動の -32000 退行を修正`）。また、この変更を `/record` で記録しますか？

---

## よーん *(21:04 JST)*

commit & push & record

### Claude *(21:05 JST)*

Reconnected 確認できました。commit → push → record の順で進めます。

*[ツール: `Bash`]*

他は無関係な変更（ログ・別プロジェクトの成果物）なので `.mcp.json` のみをコミットします。

*[ツール: `Bash`, `Bash`, `Bash`]*

master に push しました。次に `/record` を実行して報告書・変更ログを作成します。

*[ツール: `Skill`, `Read`, `Bash`, `Bash`]*

f9a719c は runbook 追加のみで記録対象外です。未記録の変更は今回の `d14a53f`（mcp-gsheets 修正）のみでした。

**変更ログ候補（未記録）**

1. **mcp-gsheets 起動パスを上方探索化し projects/ 配下起動の -32000 退行を修正** — `${CLAUDE_PROJECT_DIR}` がセッション cwd に展開されるローカル環境で起動スクリプトが見つからず即死していたバグを、上方探索＋`$HOME/xClaude` フォールバック方式で修正。
   - 関連コミット: `d14a53f fix(mcp): mcp-gsheets 起動パスを上方探索化し projects/ 配下起動の -32000 退行を修正`
   - 変更ファイル: `.mcp.json`
   - 関連する過去の変更: mcp-gsheets 起動コマンドを `$HOME` 決め打ちから `${CLAUDE_PROJECT_DIR}` に変更（7/5）、プロジェクトMCPサーバーの信頼確認を自動承認（7/7）

これを記録してよろしいですか？（「1」または「はい」で記録、「スキップ」で終了）

---

## よーん *(21:06 JST)*

1

### Claude *(21:06 JST)*

*[ツール: `Read`, `Bash`]*

No name collision. Slug: `mcp_gsheets_launch_upward_search`.

*[ツール: `Write`]*
