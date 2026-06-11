---
title: note-story spec.md サムネイル生成ステップの詳細化
date: 2026-06-11
tags: [workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260611_note_story_docs_overhaul/)

## 背景・動機

spec.md の制作フロー step 12 が `サムネイル生成: thumbnail` だけのプレースホルダで未完成だった。SCEtoAUX で実際に行ったサムネ制作（`thumbnail/` フォルダ＋design-brief＋nanobanana-prompt→画像）を、再現可能な手順として spec に明文化する。

調査の結果、サムネの画像生成はリポジトリ内に自動化（スクリプト／MCP）が無く、nano banana（Gemini 2.5 Flash Image）で外部・手動生成していたことが判明。誰が・どこで実行するかを spec に明示する必要があった。

## 実施内容

- **Naming に「### サムネイル」を新設**：作業フォルダ `thumbnail/`（plan.md／brand.md／design-brief_template.md・design-brief.md／nanobanana-prompt.md）と完成画像 `output/images/thumbnail.png`（1280×672px）を定義。
- **制作フロー step 12 を5手順化**：①インプット確認 ②デザイン指示書作成 ③生成プロンプト作成 ④**画像生成は手動・外部**（Claude はプロンプト提示まで、ユーザーが nano banana で生成し PNG を配置）⑤レビュー＆リトライ。
- **Verification に1行追加**：サムネが plan の失格条件（タイトル可読・日本語崩れなし・文字が小さすぎない・CTAなし）を満たすこと。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/note-story/spec.md` | Naming にサムネ成果物を定義、制作フロー step 12 を5手順に詳細化、Verification にサムネ失格条件を追加 |

## 設計判断

- 画像生成は「手動・外部運用として明記」を選択（ユーザー決定）。リポジトリに nano banana を叩く手段が無いため、自動化スクリプト新設は見送り、Claude の責務はプロンプト提示までと明確化した。
- サイズは note 横長に合わせ 1280×672px に統一。

## 確認結果

- spec.md step 12 で画像生成が「手動・外部」と読め、Claude が実行しない旨が明記されていることを確認。
- Naming にサムネ成果物のパスとサイズ（1280×672）が定義されていることを確認。
