---
title: save_session_history.py をサブディレクトリ起動セッション対応に修正
date: 2026-06-14
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260614_save_session_history_subdir_fix/)

## 背景・動機

`/record` のセッション履歴保存（STEP 4.5）で `save_session_history.py` を実行したところ、履歴が空（メッセージ0件）になった。

原因は JSONL の探索ディレクトリを **git ルート基準で固定**していたこと。Claude Code のセッション JSONL は「セッションを開いた作業ディレクトリ」を基にした `~/.claude/projects/<dir>/` に保存される。git ルート（`/home/useakat/xClaude`）ではなくサブディレクトリ（`projects/note-story/.../xstory`）でセッションを開くと、JSONL は `-home-useakat-xClaude-projects-...-xstory` 配下に置かれるため、`-home-useakat-xClaude` だけを見ていた旧実装では取りこぼしていた。

## 実施内容

- `JSONL_DIR`（単一ディレクトリ固定）を廃止し、`PROJECTS_DIR` と `REPO_DIR_PREFIX`（git ルートのパスを接頭辞化した文字列）を導入。
- `_candidate_jsonls()` を新設。`~/.claude/projects/` 配下で **git ルートのパスを接頭辞に持つ全ディレクトリ**から `*.jsonl` を集め、更新時刻の新しい順で返す。
- `find_latest_jsonl()` / `list_jsonls()` を `_candidate_jsonls()` 利用に変更。
- これにより、git ルートでもサブディレクトリでも、`--jsonl` を明示せずに現在のセッション履歴を拾えるようになった。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/save_session_history.py` | JSONL 探索を git ルート基準の単一ディレクトリ固定から、git ルートのパスを接頭辞に持つ全 projects ディレクトリの最新 JSONL を探す方式へ変更 |

## 確認結果

- サブディレクトリ（`.../xstory`）から `python3 scripts/save_session_history.py --list` を実行し、現在のセッション JSONL（`bc6586ff…`、最新更新）が先頭に表示されることを確認。
- 同セッションの履歴を `--jsonl` 明示なしで取得できることを確認。

## 今後の課題

- 複数セッションを同時に開いている場合は「最新更新の JSONL」を現在のセッションとみなす方式のため、厳密な現在セッション特定が必要なら環境変数等でのセッションID受け渡しを検討する。
