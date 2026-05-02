---
title: 報告書・変更ログ運用フローの整備
date: 2026-05-02
tags: [wiki, infra]
---

← [変更ログへ](../changelog#報告書変更ログ運用フローの整備)

## 背景・動機

システムへの変更が増えるにつれ「いつ・何を・なぜ変えたか」を追跡する仕組みが必要になった。将来の自分と Claude が過去の判断を参照できるよう、変更ログと報告書を紐付けた記録システムを整備した。

## 実施内容

- 変更ログ（`docs/changelog.md`）と報告書（`docs/reports/`）を1対1対応させる構造を設計・合意
- 報告書テンプレート `docs/reports/template.md` を作成
- `docs/changelog.md` を1変更1エントリ形式に全面改訂
- 既存の `docs/reports/` ファイルを新フォーマットで作り直し
- 旧 `reports/` フォルダを削除（内容は `docs/reports/` に移植済み）
- CLAUDE.md に「報告書・変更ログの記録ルール」セクションを追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `docs/changelog.md` | 1変更1エントリ形式に全面改訂 |
| `docs/reports/template.md` | 新規作成 |
| `docs/reports/index.md` | 新フォーマットに更新 |
| `docs/reports/20260502_wiki_setup.md` | 新規作成（旧ファイルを置き換え） |
| `docs/reports/20260502_implementation_rules.md` | 新規作成（旧ファイルを置き換え） |
| `reports/` | フォルダごと削除 |
| `CLAUDE.md` | 「報告書・変更ログの記録ルール」セクションを追加 |

## 設計判断

変更ログのエントリ粒度を「1日1エントリ」ではなく「1変更1エントリ」にした。報告書と1対1対応させることで、変更ログから報告書へのリンクをシンプルに管理できるため。

## 確認結果

Wiki（`https://useakat.github.io/xClaude/`）に反映されることを確認。CLAUDE.md のルールに従って Claude が自動生成できる形を確認。
