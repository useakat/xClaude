---
title: mcp-gsheets リモート認証修正 — セッション履歴
date: 2026-06-07
sidebar:
  hidden: true
---

# セッション履歴

> 2026-06-07 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260607_mcp_gsheets_remote_auth_fix/)

---

## よーん *(09:59 JST)*

mcp-gsheets がなんで使えないの？

### Claude *(09:59 JST)*

2点の原因を確認します。

*[ツール: `Bash`, `Bash`]*

原因は2つあります。

---

**原因① `${HOME}` が展開されない**

`settings.json` の `env` セクションはシェルスクリプトではなく JSON なので、`${HOME}` が変数展開されずに文字列 `${HOME}` のまま mcp-gsheets サーバーに渡されます。サーバーは `/` で始まらないためこれを「相対パス」と解釈し、作業ディレクトリ `/home/user/xClaude/` を前置します。結果：

```
/home/user/xClaude/${HOME}/xClaude/gcp/xxxxxx.json  ← 存在しない
```

**原因② リモート環境に認証ファイルがない**

仮にパスが正しく `/root/xClaude/gcp/` に解決されても（`HOME=/root`）、`gcp/` ディレクトリ自体がリモート環境に存在しません。セキュリティ上の理由で `.gitignore` されているため、クローン時に含まれないためです。

---

## よーん *(10:07 JST)*

原因
2026-06-04 の「認証を GOOGLE_APPLICATION_CREDENTIALS に統一」の変更が原因です。.mcp.json を書き換えて mcp-gsheets が GOOGLE_APPLICATION_CREDENTIALS（ファイルパス）を参照するようになりましたが、2026-05-04 の報告書に「ファイルが存在しないリモートで認証失敗が起きる」という知見が残っていました。その判断が引き継がれなかったため、ローカルだけ動く状態になっています。

Option A（推奨）：`.mcp.json` を `GOOGLE_SERVICE_ACCOUNT_KEY` に戻す（すでに前セッションで実施済み）

まずAをして → `.mcp.json` 修正済みを確認。

### Claude *(10:07 JST)*

`.mcp.json` はすでに `GOOGLE_SERVICE_ACCOUNT_KEY` になっていますが、`settings.json` の env にまだ `GOOGLE_APPLICATION_CREDENTIALS` が残っていて、それが mcp-gsheets に引き継がれて干渉している可能性があります。

*[ツール: `Bash`]*

原因が特定できました。

```
GOOGLE_APPLICATION_CREDENTIALS = ${HOME}/xClaude/gcp/...  ← 未展開の文字列、リモートに存在しない
GOOGLE_SERVICE_ACCOUNT_KEY     = {"type":"service_account",...}  ← 正常に設定済み ✅
```

`settings.json` の `GOOGLE_APPLICATION_CREDENTIALS` を削除する必要があります。削除してよいですか？

---

## よーん *(10:14 JST)*

了解。削除して

### Claude *(10:14 JST)*

*[ツール: `Edit`, `Bash`, `mcp__github__push_files`]*

`settings.json` から `GOOGLE_APPLICATION_CREDENTIALS` を削除し、master に push しました。

---

## よーん *(10:16 JST)*

master に push したら 「master に push しました」と伝えるようになってない？

### Claude *(10:16 JST)*

おっしゃる通りです。CLAUDE.md に「master に push した場合はその旨を明示的に伝える」とルールがあるのに、両方の master push で伝え忘れていました。以後徹底します。

---

## よーん *(10:17 JST)*

どうしたら忘れなくなる？

### Claude *(10:17 JST)*

`mcp__github__push_files` の PostToolUse フックで、実行後に「master に push しました と伝えること」とリマインドを出力するのが確実です。私の記憶に頼るより、仕組みで担保する方が信頼性が高いです。

追加してよいですか？

---

## よーん *(10:17 JST)*

はい

### Claude *(10:17 JST)*

*[ツール: `Edit`, `Bash`, `mcp__github__push_files`]*

master に push しました。

`mcp__github__push_files` 実行後に `⚠ master に push しました と必ず伝えること` が表示されるようになりました。次のセッションから有効です。
