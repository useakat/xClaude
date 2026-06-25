---
title: daily-xonepoint スキル・agent を非推奨化（W003 制作は spec.md に一本化）
date: 2026-06-25
tags: [skill, workflow, wiki]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260625_daily_xonepoint_gmail_attach_and_deprecation/)

## 背景・動機

W003 のワンポイント解説制作は、本来 `projects/w003/CLAUDE.md` の指示どおり `spec.md` を Read して進める設計になっている。一方で同じフローが `daily-xonepoint` スキルにも丸ごと書かれており、二重管理になっていた。その結果、ステップ順やツール指定が両者でズレ、本セッションでも「Gmail 下書きの作成タイミング（画像生成前に自動実行）」「Gmail 添付（MCP create_draft は添付非対応）」といった不整合が表面化した。

二重管理をやめ、制作フローの正本を `spec.md` に一本化するため、`daily-xonepoint` スキルと同名 agent を非推奨化する（`writer_note-story` 非推奨化と同じ方式）。

## 実施内容

- `daily-xonepoint/SKILL.md` 冒頭に `# daily-xonepoint（非推奨）` ＋非推奨バナーを追加。description を `【非推奨】…基本的に使わない` に変更。旧フローは参考用に残置。
- `metadata.yaml` で `daily-xonepoint` のカテゴリを `コンテンツ制作` → `廃止・非推奨` に移動し、`update_wiki_skills.py` で Wiki を再生成（`docs/skills/index.md` の「廃止・非推奨」セクションに集約、従来カテゴリから消去）。
- `projects/w003/spec.md` の制作フロー見出しを「`/daily-xonepoint` が自動実行」→「この spec.md を正として対話で実行する。`/daily-xonepoint` スキルは非推奨で使わない」に変更。
- `.claude/agents/daily-xonepoint.md`（同名 agent 定義）の冒頭にも非推奨バナーを追加し、description を `【非推奨】…使わない` に変更。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/daily-xonepoint/SKILL.md` | 冒頭に非推奨バナー追加・description を【非推奨】に |
| `.claude/skills/metadata.yaml` | `daily-xonepoint` を `廃止・非推奨` カテゴリへ |
| `.claude/agents/daily-xonepoint.md` | 冒頭に非推奨バナー追加・description を【非推奨】に |
| `projects/w003/spec.md` | 制作フロー見出しから `/daily-xonepoint` 参照を除去 |
| `docs/skills/index.md` ほか | Wiki 再生成（廃止・非推奨セクションに集約） |

## 設計判断

- スキル・agent とも削除せず deprecate（`writer_note-story` / `sync-to-sheets` と同様）。過去フローの参照・経緯追跡のためファイルは残す。`update_wiki_skills.py` の「`category_order` 未登録カテゴリは index から消える」生成仕様を使い、一覧除外と非推奨セクション集約を1つの仕組みで両立。
- 制作の正本は `spec.md`。W003 の `CLAUDE.md` が起動時に `spec.md` を Read させるため、スキルを使わなくてもフローは担保される。

## 確認結果

- `docs/skills/index.md` の「## 廃止・非推奨」に `daily-xonepoint` が集約され、従来カテゴリから消えていることを確認。
- SKILL.md・agent 定義の冒頭に非推奨バナーが表示されることを確認。
