---
title: record
description: 変更・実装の記録を残す。docs/changelog.md と直近の git ログを照合し、未記録の変更候補をよーんに提案する。承認後に報告書と変更ログエントリを作成して git push する。
category: 運用・記録
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

変更・実装の記録を残す。docs/changelog.md と直近の git ログを照合し、未記録の変更候補をよーんに提案する。承認後に報告書と変更ログエントリを作成して git push する。

## 詳細内容

あなたは変更記録を自律的に作成するエージェントです。
**以下の STEP を順番に実行してください。STEP 3 でユーザーの確認を取るまでファイルは作成しない。**

---

# STEP 1: 記録済み変更の把握

Read ツールで `/root/xClaude/docs/changelog.md` を読み込み、変更ログに記載されている **太字タイトル**（`**タイトル**` 形式）を全て記憶する。

---

# STEP 2: 直近の git コミット履歴を取得

```bash
git -C /root/xClaude log --oneline -30
```

さらに、各コミットで変更されたファイルの一覧を確認する：

```bash
git -C /root/xClaude log --name-only --pretty=format:"COMMIT: %h %s" -20 \
  | grep -v "^$" | head -80
```

---

# STEP 3: 未記録変更の候補を特定してよーんに提案

STEP 1 で把握した記録済みタイトルと STEP 2 のコミット履歴を照合し、まだ変更ログに記録されていない変更を特定する。

## フィルタリングルール（候補から除外するもの）

以下は記録不要のため候補に含めない：
- `settings.json` の `permissions.allow` への追記のみのコミット
- 日報・週報・月報の追加（`report(daily/weekly/monthly):`）
- X 投稿原稿・インフォグラフィック等のコンテンツファイルのみの変更

## 候補の提案形式

以下の形式でよーんに提案する：

---

**変更ログ候補（未記録）**

以下の変更が記録されていません。記録するものを選んでください（複数選択可）：

1. **[変更タイトル案]** — [1行の概要案]
   - 関連コミット: `[ハッシュ] [メッセージ]`
   - 変更ファイル: `[主なファイル]`
   - 関連する過去の変更: [changelog に記録済みの関連変更があればタイトルを列挙。なければ「なし」]

2. **[変更タイトル案]** — [1行の概要案]
   - 関連コミット: `[ハッシュ] [メッセージ]`
   - 変更ファイル: `[主なファイル]`
   - 関連する過去の変更: [changelog に記録済みの関連変更があればタイトルを列挙。なければ「なし」]

（記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。）

---

ユーザーの返答を待つ。**「スキップ」の場合はここで終了。**

---

# STEP 4: 報告書の作成

よーんが承認した変更について、1件ずつ報告書を作成する。

## ファイル名の決定

```bash
python3 -c "
from datetime import date
today = date.today().strftime('%Y%m%d')
print(today)
"
```

ファイルパス: `docs/reports/YYYYMMDD_<タイトルをスネークケース>.md`

## 報告書テンプレート

`docs/reports/template.md` を読み込み、以下の項目を埋めて保存する：

```markdown
---
title: [変更タイトル]
date: YYYY-MM-DD
tags: [該当するタグ: skill / workflow / style / bugfix / wiki / infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

[なぜこの変更が必要だったか。コミットメッセージと変更内容から推論して記述]

## 実施内容

- [箇条書きで]

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `path/to/file` | 何をどう変えたか |

## 確認結果

[動作確認の方法と結果。スキル追加の場合は「スキルが `/[name]` で呼び出せることを確認」など]
```

設計判断・今後の課題は、内容があれば追加する。

---

# STEP 4.5: セッション履歴の保存と相互リンク

## 4.5-1. セッション JSONL → Markdown 変換

```bash
python3 /root/xClaude/scripts/save_session_history.py \
  --title "<報告書タイトルと同じ>" \
  --slug "<報告書ファイル名スネークケースと同じ>"
# 最終行に保存先パスが出力される
```

## 4.5-2. 関係ない部分を削除

生成されたファイルを Read し、今回の報告書に**直接関係しない**やり取り（別トピックの作業・事前確認・無関係な修正など）を削除する。  
会話の文言・順序は変えない。削除のみ行う。

## 4.5-3. 相互リンクの追記

**履歴ファイルの冒頭**（`# セッション履歴` の下の `>` 説明行の直後）に追記：

```markdown
← [報告書へ戻る](../../reports/YYYYMMDD_<スラグ>/)
```

**報告書のヘッダーリンク行**を更新：

```markdown
← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/YYYYMMDD_<スラグ>_session/)
```

---

# STEP 4.7: 実装コミット照合チェック（docs のみコミット防止）

報告書の「変更ファイル」表に挙げた各ファイル（今回作成した報告書・変更ログ・セッション履歴の docs 自身は除く）について、実装が実際にコミット済みかを照合する：

```bash
# 未コミット変更が残っていないこと（出力が空であること）
git -C /root/xClaude status --porcelain -- <file>

# そのファイルを変更したコミットが直近に存在すること
git -C /root/xClaude log --oneline -3 -- <file>
```

- いずれかのファイルに未コミット変更が残っている、または該当する変更のコミットが見つからない場合は、**STEP 5 以降に進まない**。よーんに「報告書には `<file>` の変更が記載されていますが、コミットに含まれていません」と報告し、指示を待つ。
- 背景：過去に2回（7/4 事前ウォーム実装・7/7 信頼確認自動承認）、報告書・変更ログだけがコミットされ実装ファイルが未コミットのまま残り、対策が反映されず同じ障害が再発した。このチェックはその再発防止のため必ず実施する。

---

# STEP 5: 変更ログへのエントリ追加

**編集の前に、必ずリモートの最新状態を取り込む**（複数セッションが同じ日に changelog を編集するため）：

```bash
git -C /root/xClaude fetch origin master -q && git -C /root/xClaude rebase origin/master
```

そのうえで `docs/changelog.md` を読み込み、適切な日付セクションに追記する。

## エントリ形式

```markdown
- **[変更タイトル]** — [概要1行]。[→報告書](../reports/YYYYMMDD_[ファイル名]/)
```

## リンク形式ルール

**Wiki（Starlight）では `.md` 拡張子付きリンクが 404 になる。** 報告書・履歴・変更ログへのリンクはすべて末尾を `/` で終わらせる（`.md` は付けない）。

例:
- ✅ `[変更ログへ](../changelog/)`
- ✅ `[報告書](../reports/20260521_foo/)`
- ❌ `[変更ログへ](../changelog.md)`

## 追記ルール

- 今日の日付セクション（`## YYYY-MM-DD`）が存在すれば、その末尾に追記
- 存在しなければ、ファイル先頭の `---` の直後に新しい日付セクションを挿入して追記
- エントリは2行以内に収める

---

# STEP 6: Git コミット & GitHub MCP プッシュ

**6-1. ローカルコミット**

```bash
bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh \
  "docs: [変更タイトル]の報告書・変更ログを追加"
```

複数件まとめてコミットする場合は、タイトルを列挙する。

**6-2. GitHub MCP で master にプッシュ**

`git diff HEAD~1 --name-only` で変更ファイル一覧を取得し、各ファイルを Read ツールで読み込む。その後 `mcp__github__push_files` ツールで master に直接プッシュする：

- owner: `useakat`
- repo: `xClaude`
- branch: `master`
- files: 変更ファイルの path と content のリスト
- message: コミットメッセージと同じ内容

---

# STEP 6.5: プッシュ後の反映確認（エントリ消失の検知）

push しただけでは終わらない。**master 上に自分のエントリと報告書が実際に載っているか**を必ず確認する：

```bash
git -C /root/xClaude fetch origin master -q

# 1. 変更ログに自分のエントリが載っているか（今回のタイトルが出力に含まれること）
git -C /root/xClaude show origin/master:docs/changelog.md | python3 -c "
import sys
s = sys.stdin.read()
sec = s.split('## YYYY-MM-DD')[1].split('\n## ')[0]
for l in sec.split('\n'):
    if l.startswith('- **'): print('•', l[4:l.index('**', 4)])
"

# 2. リンク先の報告書・セッション履歴が master に存在するか（パスが出力されること）
git -C /root/xClaude ls-tree origin/master --name-only \
  docs/reports/YYYYMMDD_<スラグ>.md docs/history/YYYYMMDD_<スラグ>.md
```

- **自分のエントリが出力に無い場合は消失している。** 別セッションが同じ日付セクションを編集し、そのマージで自分の1行が落ちるケースがある。以下で復元する：

```bash
git -C /root/xClaude rebase origin/master   # 最新の changelog を取り込む
# 消えたエントリを再度追記して commit → push
```

- 報告書ファイルが出力に無い場合は、報告書だけが未 push（またはマージで失われた）状態。同様に復元してから完了報告する。
- 背景：2026-07-25、別セッションのマージにより変更ログの1行だけが静かに消え、報告書ファイルは残っているのにどこからもリンクされない状態になった。push の成功は「master に載っていること」を意味しないため、このステップを必ず実施する。

---

# 完了報告

```
✅ 記録完了
   報告書: docs/reports/YYYYMMDD_[ファイル名].md
   変更ログ: docs/changelog.md に追記済み（master 上で反映を確認済み）
```
