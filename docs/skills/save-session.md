---
title: save-session
description: "save-session スキル"
category: 運用・記録
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

save-session スキル

## 詳細内容

# save-session スキル

カレントセッションの作業ログ（JSONL）を Markdown に変換し、`docs/history/` に保存して master に push する。

---

## STEP 1: JSONL の確認

```bash
python3 /home/user/xClaude/scripts/save_session_history.py --list
```

最近のファイル一覧を表示する。通常は最新（一番上）が現在のセッション。

---

## STEP 2: タイトルとスラグをよーんに確認

以下の形式で提案する：

```
履歴を保存します。以下の内容でよいですか？

- タイトル: [セッション内容から自動推測]
- ファイル名: YYYYMMDD_[slug].md
- 対象 JSONL: [ファイル名]（最新）
```

よーんが OK すれば STEP 3 へ。修正があれば反映してから進む。
**よーんの返答を待ってから次へ進むこと。**

---

## STEP 3: 変換・保存

```bash
python3 /home/user/xClaude/scripts/save_session_history.py \
  --title "<タイトル>" \
  --slug "<スラグ>" \
  [--jsonl <パス>]  # 最新以外を使う場合のみ
```

最終行に保存先パスが出力される。

---

## STEP 4: 関連報告書へのリンク追加（任意）

関連する報告書（`docs/reports/` 配下）がある場合、そのファイルにセッション履歴へのリンクを追記する：

```markdown
## セッション履歴

[→ 作業ログ全文](../history/YYYYMMDD_slug.md)
```

報告書がない場合はこの STEP をスキップ。

---

## STEP 5: コミット・push

```bash
bash /home/user/xClaude/scripts/commit_and_sync.sh \
  "docs: <タイトル> のセッション履歴を追加"
```

その後、GitHub MCP でファイルを master に push する：

変更ファイルを Read ツールで読み込み（報告書も更新した場合はそちらも）、`mcp__github__push_files` で master に push：

- owner: `useakat`
- repo: `xClaude`
- branch: `master`
- message: コミットメッセージと同じ

---

## 完了報告

```
✅ セッション履歴を保存しました
   ファイル: docs/history/YYYYMMDD_slug.md
   メッセージ数: N 件
```

