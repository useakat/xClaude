---
title: CLAUDE.md に新規スキル作成時の metadata.yaml 追記ルールを追加
date: 2026-05-16
tags: [workflow, wiki]
---

← [変更ログへ](../changelog.md)

## 背景・動機

`analyze-impression` スキルを新設した際、SKILL.md を作成して commit したが Wiki のスキル一覧に反映されなかった。原因は `.claude/skills/metadata.yaml` への追記を忘れていたこと。

Wiki 更新システム（`update_wiki_skills.py`）は `git commit` 後の PostToolUse hook で自動実行されるが、`metadata.yaml` をソースとして再生成する仕組みのため、`metadata.yaml` に新スキルが登録されていないと自動更新されない。

同じ抜けを繰り返さないよう、ルールを明文化した。

## 実施内容

- `CLAUDE.md` の「実装ルール」セクションに「新規スキル作成時のルール」サブセクションを追加
- 手順を明示：（1）SKILL.md 作成、（2）`metadata.yaml` に `<name>: category: <カテゴリ>` を追加、（3）commit すれば hook が Wiki を自動再生成
- 既存カテゴリの選択肢（コンテンツ制作 / レポート生成 / リサーチ・分析 / 品質チェック / メール・通知 / 画像・同期 / 運用・記録 / 設定・保守）を列挙

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `CLAUDE.md` | 実装ルールセクションに「新規スキル作成時のルール」を追加（9行） |

## 確認結果

ルール文章を CLAUDE.md に追加済み。次回のスキル新設時に従う。
