---
title: プロジェクトフォルダ名を what_id に統一
date: 2026-06-14
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260614_projects_rename_to_what_id/)

## 背景・動機

`projects/` 配下のプロジェクトフォルダ名（`note-story` / `x-story` / `x-onepoint`）が、データベース（what シート）の `what_id` と一致しておらず、プロジェクト識別子とローカルフォルダの紐付けが直感的でなかった。フォルダ名を `what_id` に統一することで、シート上のプロジェクトとローカル成果物の対応を明確にする。

| 旧フォルダ名 | 新フォルダ名 | what_id |
|---|---|---|
| `projects/note-story` | `projects/w002` | W002 |
| `projects/x-story` | `projects/w001` | W001 |
| `projects/x-onepoint` | `projects/w003` | W003 |

## 実施内容

- 3 フォルダをリネーム（`note-story`/`x-onepoint` は git の rename 履歴を保持、未追跡だった `x-story` は plain mv）
- 各プロジェクトの設定・spec・スキル定義内の **active な参照パス** を新フォルダ名に置換
- スコープ判断（ユーザー確認済み）
  - docs/ 配下の過去記録・`archive/` のセッション記録は**履歴として据え置き**
  - research 系スキルの出力ファイル名接頭辞 `note-story_NNNN_` は**変更しない**（命名規約でありフォルダ名ではない）
  - スキル名（`writer_note-story` / `draft_xstory` 等）は**変更しない**（誤検出）
- 最終 grep で active ファイルの旧名参照が 0 件であることを確認

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w003/.claude/settings.json` | UserPromptSubmit フックの spec.md パス＋フラグ名を `/tmp/w003_spec_loaded` に更新 |
| `projects/w003/.claude/settings.local.json` | allow ルールのパスを w003 に更新 |
| `projects/w003/spec.md` | 出力パス・`/check-brand` 引数を w003 に更新（5箇所） |
| `projects/w002/.../{xstory,xstory-test}/.claude/settings.local.json` | Read() グロブを w002 に更新 |
| `projects/w002/.../thumbnail/brand.md`・`thmbnail_template/brand.md` | 相対パス説明文を w002 に更新（計4ファイル） |
| `.claude/skills/daily-xonepoint/SKILL.md` | `/check-brand` 引数パスを w003 に更新 |
| `.claude/skills/check-brand/SKILL.md` | 使用例パスを w003 に更新 |
| `projects/template/spec.md`・`spec_example.md` | 例示パスを w003 に更新 |
| `projects/w001/spec.md`・`spec_example.md` | 例示パスを w003 に更新 |

## 設計判断

- 履歴記録（docs/・archive/）は当時の事実の記録であり書き換えると履歴の整合が崩れるため据え置いた。機能的影響もない。
- research の出力命名規約はフォルダ名のリネームとは別概念のため変更しなかった。

## 確認結果

- `grep -rn -E "projects/(note-story|x-onepoint|x-story)|x_onepoint" projects .claude/skills`（archive/docs 除外）で残存 0 件
- `projects/` の最終構成が `w001 / w002 / w003 / template` であることを確認
- master に push 済み（commit `5aae189`）

## 今後の課題

- daily-xonepoint クラウドルーティンの作業ディレクトリが旧 `projects/x-onepoint` 指定の場合、`/schedule` 側で `projects/w003` への更新が必要（リポジトリ外のため別途対応）。
- Claude Code のセッション履歴ディレクトリ（`~/.claude/projects/-home-useakat-xClaude-projects-x-onepoint/`）は cwd 由来。新規セッションは新パスに作られ、旧履歴は旧ディレクトリに残る（移行不要・実害なし）。
