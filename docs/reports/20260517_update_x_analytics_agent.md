---
title: update-x-analytics サブエージェント新設
date: 2026-05-17
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md#2026-05-17)

## 背景・動機

X の管理画面からエクスポートした CSV（analytics_tmp フォルダに保管）には「詳細表示」「リンククリック」「フォロー増」の列がある。これらは X 投稿一覧シートに手動で転記していたが、投稿数が増えると手間になるため自動化したかった。また、CSV 側の URL は `x.com/usephys/status/{ID}` 形式だが、シート側は `twitter.com/i/web/status/{ID}` 形式なので、直接マッチングできずに ID 抽出が必要という技術的な課題もあった。

## 実施内容

- `.claude/agents/update-x-analytics.md` を新設
- Drive MCP でCSVを検索・取得 → Python 正規表現でパース → Sheets B列と status ID で照合 → AA:AC 列を一括更新する7ステップのフローを定義
- URL形式の違い（`twitter.com` vs `x.com`）を `/status/(\d+)` で吸収する照合ロジックを組み込み
- `record-note-posts` スキルの「既存データ取得→URL照合→更新」パターンを参考に設計

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/agents/update-x-analytics.md` | サブエージェント定義を新規作成 |

## 設計判断

- **スキルではなくエージェントとして定義**：スキルはユーザーが `/` で呼ぶ軽量フロー向きだが、Drive 検索→CSV パース→Sheets 照合→一括更新は複数 MCP ツールをまたぐ自律的な処理であり、エージェントの方が適切と判断。
- **`general-purpose` エージェントに委譲**：`.claude/agents/` ファイルはセッション開始時にロードされるため、作成直後のセッションでは `subagent_type` として認識されない。次回セッション以降は `@update-x-analytics` で直接呼び出せる。
- **CSV パースを Python 正規表現で実装**：CSVの行末がカンマ区切りで数値が連続する形式のため、`csv` モジュールより正規表現の方がシンプルかつ確実と判断。

## 確認結果

初回実行でCSV 81件中21件（シート登録済み分）を正しくマッチし、AA:AC 列（詳細表示・リンククリック・フォロー増）の63セルを一括更新できたことを確認。
