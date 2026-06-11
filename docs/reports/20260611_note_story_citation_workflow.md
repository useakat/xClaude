---
title: note-story 出典運用の整備（参考情報チェック・2段階運用・リサーチ運用ルール）
date: 2026-06-11
tags: [workflow, style]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260611_note_story_docs_overhaul/)

## 背景・動機

W002「執念の物語」note 記事（SCEtoAUX）の制作中、出典まわりで次の課題が表面化した。

- ファクトチェック（`/check-fact`）は事実の正否は見るが、「どの参考文献がその記述を支えているか（出典の取り違え）」までは詰めきれず、空軍報告の出典が AmericaSpace 誤記のまま残っていた。
- 下書きに出典の要約を載せると検証はしやすいが、公開版（index.md）にも同じ内部メモが載って読み物として重い。
- 調べ物のたびに WebSearch から始めてしまい、notebook に既にあるソースを見落として重複追加する事故が起きた。

これらを制作フロー・ドキュメントに恒久ルールとして組み込む。

## 実施内容

- **参考情報チェック step を制作フローに追加**（spec.md step 10）：draft の各文献を NotebookLM へ問い合わせ→WebSearch/WebFetch で実 URL・実記載を検証→誤った出典の差し替え・不足の追加→index.md へ反映。
- **出典の2段階運用を整理**：下書き（draft.md）＝`[N]`マーカー＋「本文での参照内容」、公開版（index.md）＝マーカー除去＋「その文献自体の概要」。当初は index に参照内容要約を載せる形だったが、読者向けには「文献の概要」が有用と判断して入れ替えた。
- **リサーチ運用ルールを追加**（note-story の CLAUDE.md）：調べ物は「まず notebook のソース→分からなければ WebSearch/WebFetch→新たな信頼ソースは notebook に還元（追加前に既存ソースを確認し重複を防ぐ）」の順で行う。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/note-story/CLAUDE.md` | 「リサーチ運用ルール」を新設（notebook 優先→WebSearch→notebook 還元） |
| `projects/note-story/spec.md` | 制作フローに「参考情報チェック」step を追加。公開原稿の出典書式注記を更新 |
| `projects/note-story/brand.md` | 「史実・出典（2段階運用）」を新設・改訂（draft=参照内容／index=概要） |

## 設計判断

- index.md を「参照内容の要約」ではなく「文献の概要」にしたのは、読者が「この出典は何の資料か」を知ってリンクを開く判断に役立つため。内部メモ（参照内容）は検証用なので draft 側に集約した。
- 重複追加事故を機に、`client.sources.list(notebook_id)` で追加前に既存ソースを確認する運用をルール化した。

## 確認結果

- SCEtoAUX で参考情報チェックを実走し、空軍報告の出典を [6]AmericaSpace→[8]Moonport に是正、righto.com を [9] として追加。
- draft.md／index.md を新2段階運用に適用し、index 本文の `[N]` マーカー残存ゼロを確認。
