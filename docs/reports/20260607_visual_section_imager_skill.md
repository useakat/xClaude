---
title: visual_section-imager スキル新設（NotebookLM 画像生成）
date: 2026-06-07
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

`visual_section-planner` で出した画像案をユーザーが 1 案に絞り込んだ後、それを実画像に変換する工程が手作業だった。絞り込み済みの `image-plan.md` を入力に、NotebookLM で実画像を生成して `draft/images/` に保存するスキルを新設し、「画像案 → 実画像」を自動化する。

## 実施内容

- `visual_section-imager` を新設。`draft/image-plan.md`（H2 ごと 1 案に絞り込み済み）を入力に、`notebook-id.md` の既存 NotebookLM notebook 内で画像を生成
- スキルは画像説明を NotebookLM に渡すだけ。各説明につき **3 枚**生成（同一 instructions を 3 回）
  - 図解画像: 「infographic として作成」を明示指示
  - イメージ画像: 「情景イメージ画像として作成」＋**画像内に文字を入れない**指示
  - 写真画像（Web取得）: スキップ
- 保存先 `draft/images/<H2タイトル>_<画像種類>_<連番>.png` と使用プロンプト `.md`。ローカル保存のみ（Drive/メールなし）・キャラクターなし・`--style auto`
- 生成失敗時の**自動リトライ**（出力 PNG が無ければ最大 2 回再試行＝計 3 回、`sleep 5`、失敗時はスキップして継続）
- 画像種類ラベルを 図解／イメージ／写真 に統一（spec の Naming と整合）
- `scripts/notebooklm_manager.py infographic` を再利用（notebook 新規作成・削除はしない）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/visual_section-imager/SKILL.md` | 新規。NotebookLM 画像生成（リトライ・文字なし・ラベル統一を含む） |
| `.claude/skills/metadata.yaml` | `visual_section-imager: 画像・同期` を追加 |
| `projects/note-story/spec.md` | フロー11（画像生成）を本スキル呼び出しに更新、Naming のラベルを統一 |
| `docs/skills/visual_section-imager.md` `index.md` | Wiki 自動生成 |

## 設計判断

- NotebookLM の画像生成 API は infographic のみのため、図解・イメージとも `infographic` コマンドを使い、instructions の文面で描き分けた。
- 「3 枚 = 3 つの異なる切り口」案はユーザー判断で不採用。スキルは説明をそのまま渡し、NotebookLM の描画ゆらぎで 3 枚を得る方針に確定。

## 確認結果

- SCEtoAUX の絞り込み済み image-plan で実走。図解 3 枚・イメージ 6 枚（2 セクション）を生成、写真セクションはスキップ。md5 重複なし。
- 初回に 1 枚が `RPCTimeoutError` で失敗したが単純リトライで復旧したため、自動リトライ機能を追加して恒久対策とした。

## 今後の課題

- イメージ画像の既存生成分（旧仕様・文字入りの可能性）は再生成していない。必要時に文字なし版へ再生成する。
