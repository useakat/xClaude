---
title: Wiki スキル詳細ページの自動生成と index.md のリンク化
date: 2026-05-09
tags: [wiki, infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

前回の変更（「Wiki スキル一覧の自動更新システム実装」）では、スキル一覧（`docs/skills/index.md`）をカテゴリ別に自動生成しましたが、スキル名がプレーンテキストであり、ユーザーが詳細情報を参照できませんでした。

スキルの詳細説明（SKILL.md 本文）をユーザーが閲覧可能にするために、スキル詳細ページが必要でした。しかし、26個のスキルの詳細ページを手動で作成・管理するのは運用負荷が高いため、自動化が必須でした。

## 実施内容

- **`scripts/update_wiki_skills.py` に `generate_skill_detail_page()` 関数を追加** — SKILL.md から frontmatter と本文を抽出し、詳細ページテンプレートを適用
- **各スキルの詳細ページを自動生成** — `docs/skills/{skill-name}.md` を生成。frontmatter（title/description/category）+ スキル説明セクション + SKILL.md 本文を含む
- **`generate_wiki_index()` を修正** — テーブルのスキル名をマークダウンリンク形式（`[skill-name](/xClaude/skills/skill-name/)`）に変更
- **post-commit フックで自動実行** — git commit 時に update_wiki_skills.py が自動実行され、スキル追加・修正時に詳細ページも自動生成される設計に

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/update_wiki_skills.py` | `generate_skill_detail_page()` 関数を追加。各スキルの詳細ページを自動生成する処理を実装 |
| `docs/skills/index.md` | テーブルのスキル名をマークダウンリンク化（自動生成）。カテゴリ別整理は維持 |
| `docs/skills/analyze-target.md` 他25ファイル | 26個のスキル詳細ページを新規生成。各ページは frontmatter + スキル説明 + SKILL.md 本文を含む |

## 設計判断

**なぜ SKILL.md をソースとして使用するのか**：
- スキル定義は既に SKILL.md に記述されている
- 重複管理を避けるため、ソースは SKILL.md で統一
- スクリプトで抽出・整形することで、SKILL.md 更新時に詳細ページも自動反映

**なぜ post-commit フックで自動実行するのか**：
- スキル追加時に、ユーザーが SKILL.md を commit するだけで詳細ページも自動生成される
- 手動でのスキルリスト・詳細ページ更新を不要にし、運用負荷を軽減

## 確認結果

1. **スクリプト動作確認** — `python3 /root/xClaude/scripts/update_wiki_skills.py` 実行後、26個のスキル詳細ページが `docs/skills/` に生成されることを確認
2. **リンク確認** — `docs/skills/index.md` のテーブル内スキル名がマークダウンリンク形式で表示されることを確認（例：`[check-fact](/xClaude/skills/check-fact/)`）
3. **詳細ページ確認** — 各詳細ページに正常に frontmatter（title/description/category）とスキル説明 + SKILL.md 本文が含まれることを確認

## 今後の課題

- Starlight ビルド後、サイドバーナビゲーションが詳細ページを正常に認識するか確認
- docs/ と starlight/src/content/docs/ の同期について（別の問題として存在）
