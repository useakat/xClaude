---
title: /update-permissions スキル追加・コミット前フック廃止
date: 2026-05-03
tags: [skill, workflow, infra]
---

← [変更ログへ](../changelog/)

## 関連する過去の変更

このフック廃止は以下の変遷の最終段階にあたる：

1. **git commit 前の確認フック追加**（2026-05-02）— `systemMessage` 通知方式で初期実装。[→報告書](./20260502_precommit_hook/)
2. **コミット前フック検知対象の拡張**（2026-05-03）— `commit_and_sync.sh` 経由のコミットも検知対象に追加。[→変更ログ](../changelog/)
3. **コミット前確認フックの blocking 化**（2026-05-03）— `decision:block` ＋ `[pre-commit-ok]` bypass トークン方式に変更。[→報告書](./20260503_precommit_hook_blocking/)

## 背景・動機

blocking 化（変遷3）の運用で新たな問題が判明した：

- フックが必ずブロックするため、確認済みの場合でも `# [pre-commit-ok]` トークンを手動で付ける手順が必要だった
- `[pre-commit-ok]` をよーんへの確認前に付けてコミットしてしまうケースが発生した（トークンの使い方が曖昧）
- 結果として「フックがあっても確認が漏れる」という根本問題は解決されていなかった

「自動で強制する仕組み」より「必要な時に手動で実行する仕組み」の方がシンプルで運用しやすいと判断し、フックを廃止してスキルに置き換えた。

## 実施内容

- `settings.json` の `hooks.PreToolUse` セクションを完全削除
- `/update-permissions` スキル（`.claude/skills/update-permissions/SKILL.md`）を新設
- CLAUDE.md の Git ルールからコミット前確認の記述を削除し、`/update-permissions` への言及に簡潔化

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `hooks` セクション全体を削除 |
| `.claude/skills/update-permissions/SKILL.md` | 新規作成（4ステップ：現在の allow 把握 → 新規操作提示 → 追記 → コミット）|
| `CLAUDE.md` | Git ルールのコミット前確認手順を削除し `/update-permissions` 参照に変更 |

## 設計判断

**スキル方式を選んだ理由**：フック方式は Claude が自律的に動く前提だが、実際には Claude の記憶と判断に依存するため信頼性が低かった。スキルとして切り出すことで、よーんが必要と感じた時に明示的に実行する設計にした。確認の責任をよーんに委ねることで、運用の透明性が上がる。

## 確認結果

スキルが `/update-permissions` で呼び出せることを確認。`settings.json` からフックが除去されていることを確認。
