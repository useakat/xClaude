---
title: research_trivia-source スキル新設
date: 2026-05-30
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260530_research_trivia_source_skill_session/)

## 背景・動機

テーマを渡すと NotebookLM の Deep Research で信頼できるソースを自動収集し、そこからトリビアネタを選定するワークフローを自動化したかった。従来は手動で NotebookLM を操作していたため、ネタ発掘に時間がかかっていた。

企業製品ページ・販売サイトが混入しやすい問題は、スクリプト側のドメインパターンマッチで除外する方式を検討したが、メンテ対象リストが増え続ける・未知ブランドが漏れる問題があった。最終的に Deep Research のクエリ文字列に除外指示を埋め込み、NotebookLM 自身に判断させる方式を採用した。

## 実施内容

- `.claude/skills/research_trivia-source/SKILL.md` を新設
  - Step 0〜4（認証確認・ノートブック作成・Deep Research・トリビア選定）を自動実行
  - Step 5〜6（解説文生成・保存）はユーザーが明示的に指示した場合のみ実行する手動フェーズとして分離
  - Deep Research クエリに「優先: 査読付き論文・大学/研究機関・科学メディア」「除外: 企業製品ページ・販売サイト」の条件を埋め込み
  - 想定読者 PE01（物理に憧れがあるが数式で挫折した文系会社員）に刺さるネタ選定条件を定義
- `scripts/notebooklm_manager.py` に `deep-research` サブコマンドを追加
  - `NotebookLMClient.from_storage(path, timeout=120.0)` でタイムアウトを延長（デフォルト 30s では `import_sources` が timeout していた）
  - 10秒ごとにポーリング、最大 10 分待機
- `.claude/skills/metadata.yaml` に `research_trivia-source: category: リサーチ・分析` を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/research_trivia-source/SKILL.md` | スキル新設 |
| `scripts/notebooklm_manager.py` | `deep-research` サブコマンド追加、`timeout=120.0` 設定 |
| `.claude/skills/metadata.yaml` | `research_trivia-source` 追記 |

## 設計判断

**企業ページ除外をクエリ側で行う理由**：スクリプト側でドメインリストを管理する方式（`_is_corporate_source()`）は当初実装したが、リスト増加・未知ドメイン漏れの問題があった。NotebookLM の Deep Research はクエリ文字列を解釈して収集先を判断するため、自然言語で「除外: 企業製品ページ」と指示する方がシンプルかつメンテナンスフリー。

**Step 4 で止める理由**：トリビア選定（事実確認）と解説文生成（文章品質）は別の判断が必要なため、自動フェーズと手動フェーズを明確に分離した。

## 確認結果

テーマ「録音した声 × 骨伝導」でスキルを実行し、Deep Research でソース収集・トリビアネタ 4 件の選定まで正常に完了したことを確認。`import_sources` の timeout 問題は `timeout=120.0` で解消。

## 今後の課題

- クエリ側の企業除外指示が 100% 有効ではなく、一部企業ページが混入する場合がある（既知の限界）
- Step 5 の `ask` は新規会話として始まるため、Step 4 の会話履歴は引き継がれない（NotebookLM の仕様上の制約）
