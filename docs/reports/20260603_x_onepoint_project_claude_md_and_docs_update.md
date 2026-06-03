---
title: x-onepoint プロジェクト CLAUDE.md 追加・ドキュメント整備
date: 2026-06-03
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260603_20260603_x_onepoint_project_claude_md_and_docs_update/)

## 背景・動機

2026-06-01 に `projects/x-onepoint/` へ brand.md・spec.md・plan.md を新設したが、このフォルダで作業を始めたときに spec.md を確実に読み込ませるための CLAUDE.md が存在しなかった。また、初版のドキュメント内容をレビューして brand.md の表現ルール・plan.md の目標設定・spec.md の制作フローを実際の運用に合わせて更新する必要があった。

## 実施内容

- `projects/x-onepoint/CLAUDE.md` を新設：「作業開始前に必ず `spec.md` を Read する」起動ルールを定義
- `projects/x-onepoint/brand.md` を更新：Project Impression・Visual Rules・Writing Rules（4段構成・文体・冒頭日常接続ルール）・Do Not を整備
- `projects/x-onepoint/plan.md` を更新：W003/PE01/PR003 計画の具体化
- `projects/x-onepoint/spec.md` を更新：制作フロー・命名規則・検証項目を実運用に合わせて整備

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/x-onepoint/CLAUDE.md` | 新規作成。起動時に spec.md を Read するルールを定義 |
| `projects/x-onepoint/brand.md` | 表現ルール・4段構成・文体・Do Not を整備 |
| `projects/x-onepoint/plan.md` | W003/PE01/PR003 計画を具体化 |
| `projects/x-onepoint/spec.md` | 制作フロー・命名規則・検証項目を更新 |

## 設計判断

CLAUDE.md の起動ルールは「spec.md を Read すること」の1行ルールに絞った。brand.md・plan.md も参照対象だが、spec.md 内の Input セクションに両ファイルの参照が明記されているため、spec.md 起点で連鎖的に読み込まれる設計にした。

## 確認結果

`projects/x-onepoint/` で作業を開始する際に CLAUDE.md が読み込まれ、spec.md を Read してから制作フローに入ることを確認。
