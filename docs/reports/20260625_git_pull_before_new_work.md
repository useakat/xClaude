---
title: 新規作業の開始前に git pull で最新化するルールを追加
date: 2026-06-25
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260625_w003_post_images_drive_and_git_pull_rule/)

## 背景・動機

このプロジェクトは複数の環境（ローカル／VPS／クラウドエージェント等）から同じ `master` に push して運用している。あるセッションで、ローカルが remote より数コミット遅れた状態のまま作業を始めてしまい、古い `spec.md` / `daily-xonepoint` SKILL.md を正と思い込んで作業した結果、すでに remote に実装済みだった機能（投稿フォルダの Drive アップロード）を「未実装」と誤認しかけた。さらに pull しようとしたら未コミットのローカル変更でブロックされた。

この手戻りを防ぐため、作業開始時の最新化を CLAUDE.md に明文化した。

## 実施内容

- `CLAUDE.md` の `## Git ルール` 冒頭に次のルールを追加：
  > 新しい作業を始める前に、まず `git pull` でローカルを最新化する（複数環境から同じ master に push するため、古い状態での作業・重複実装を防ぐ）。未コミットの変更があって pull がブロックされる場合は、commit するか `git stash` で退避してから pull し、必要なら戻す。
- 「常に pull」ではなく、未コミット変更時は commit / stash してから、という条件付きにした（無条件 pull はローカル変更でブロックされるため）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `CLAUDE.md` | Git ルールに「作業開始前に git pull で最新化（未コミット変更は commit/stash 先行）」を追記 |

## 設計判断

- hook（SessionStart で自動 pull）も検討したが、未コミット変更時の競合処理など分岐が増えるため、まずは CLAUDE.md 明記という軽量な手段を選んだ。必要になれば hook 化も可能。

## 確認結果

- `CLAUDE.md` の Git ルール節に追記されていることを確認。
