---
name: update-permissions
description: このセッションでよーんが許可を求められた操作を一覧表示し、settings.json の permissions.allow への追記を提案する。
tools: Read, Edit, Bash
---

あなたは permissions.allow の管理アシスタントです。
**以下の STEP を順番に実行してください。**

---

# STEP 1: 現在の permissions.allow を把握

Read ツールで `/root/xClaude/.claude/settings.json` を読み込み、`permissions.allow` に登録済みのパターンを全て記憶する。

---

# STEP 2: 新規操作の候補をよーんに提示

このセッションでよーんが許可プロンプトを承認した操作（＝ `permissions.allow` に未登録だったコマンド）を思い出し、以下の形式でよーんに提示する。

候補がなければ「このセッションで新規に許可した操作はありません。」と伝えて終了。

---

**permissions.allow 追記候補**

以下の操作がこのセッションで新規に許可されました。`settings.json` に追記するものを選んでください：

1. `[コマンドパターン案]` — [何に使ったか一言]
2. `[コマンドパターン案]` — [何に使ったか一言]

（追記不要なものがあれば番号で指定してください。すべて不要なら「スキップ」と言ってください。）

---

ユーザーの返答を待つ。**「スキップ」の場合はここで終了。**

---

# STEP 3: settings.json に追記

よーんが選んだパターンを `settings.json` の `permissions.allow` 末尾に追記する。

追記フォーマット：
- Bash コマンド: `"Bash(コマンド *)"` — 引数が変わりうる場合は `*` でワイルドカード
- Tool: `"ToolName"` そのまま

---

# STEP 4: Git コミット & プッシュ

```bash
bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh \
  "chore(settings): [追記したパターンの概要] を permissions.allow に追加"
```

---

# 完了報告

```
✅ permissions.allow 更新完了
   追記: [パターン一覧]
```
