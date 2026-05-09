---
title: Wiki スキル一覧の自動更新システム実装
date: 2026-05-09
tags: [wiki, infra, workflow]
---

← [変更ログへ](../changelog.md)

## 背景・動機

Wiki のスキル一覧（`docs/skills/index.md`）が手動更新のため、新規スキル追加時に更新漏れが発生していました。

また、スキル一覧の掲載順序やカテゴリ分けが統一的に管理されていない状態でした。

スキルの追加・削除・修正があったときに自動で Wiki を更新するシステムが必要でした。

## 実施内容

- **`.claude/skills/metadata.yaml` を新規作成** — スキル ↔ カテゴリのマッピングを一元管理。YAML 形式で全スキルのカテゴリを定義
- **`scripts/update_wiki_skills.py` を新規作成** — スキルディレクトリをスキャンして SKILL.md から情報抽出。metadata.yaml に不足スキルを自動追加。`docs/skills/index.md` をカテゴリ別に自動生成
- **`.claude/settings.json` に PostToolUse フック追加** — git commit 時に `update_wiki_skills.py` を自動実行。metadata.yaml と wiki を同時に更新

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/metadata.yaml` | 新規作成。スキル名と カテゴリのマッピング（コンテンツ制作、レポート生成、リサーチ・分析、品質チェック、メール・通知、画像・同期、運用・記録、設定・保守） |
| `scripts/update_wiki_skills.py` | 新規作成。スキルをスキャンして metadata.yaml を更新・wiki を生成するスクリプト |
| `.claude/settings.json` | PostToolUse フック追加。git commit 後に update_wiki_skills.py を実行 |
| `docs/skills/index.md` | 自動生成。全27スキルをカテゴリ別に整理した wiki |

## 設計判断

**metadata.yaml を手動から自動管理に変更した理由**：
- スキル追加時に metadata.yaml への追記を忘れるリスクを排除
- スクリプトが `scripts/` をスキャンして自動で新規スキルを検出・追加

**post-commit フックで自動実行**：
- ユーザーは SKILL.md を追加して commit するだけで完了
- 後続の wiki 更新は自動化

## 確認結果

1. **既存スキルの自動検出**: 全27スキルを正常に検出・分類
2. **自動生成 wiki の確認**: カテゴリ別に整理された wiki が正常に生成
3. **post-commit フック動作確認**: 実装後の git commit で自動実行されることを確認

## 今後の課題

- frontmatter がない SKILL.md の description を充実させる（現在は「スキル名 スキル」になる）
- 新規スキル追加時に自動で category フィールドのデフォルト値（「その他」）を設定するロジック確認
