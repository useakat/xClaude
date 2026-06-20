---
title: notebooklm_manager.py の ask 出力を answer だけに絞る
date: 2026-06-20
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260620_notebooklm_ask_answer_only/)

## 背景・動機

`/check-fact-lim` をフォーク実行（subagent）すると、NotebookLM への問い合わせで `API Error: Stream idle timeout - partial response received` を繰り返し、最後まで走らなかった。

原因は2つ：

1. **ストリーム idle タイムアウト**：フォークした subagent が `notebooklm_manager.py ask` を前景ブロッキングで長時間（60〜180秒+）待つ。その間トークンを出力しないため、subagent と LLM API の間のストリームが「無音」になり、API 側の idle 上限で接続が切られる。
2. **巨大出力**：`cmd_ask` が `print(result)` で `AskResult` を丸ごと出力していた。`answer` だけでなく全 `ChatReference.cited_text`・ソース抜粋まで含むため、1回の出力が **665KB〜2.3MB**（実測）に達し、subagent がこれを読み込むのも重く、別の限界にも触れやすかった。

メインループから直接 `ask` を叩くと成功していたのは、前景 Bash の同期待ち＋出力を `answer` だけ抽出するフィルタを通していたため。フォーク実行にはこの保護がない。

まず影響の大きい「出力削減」を最小変更として入れ、効果を確認する方針とした（質問分割・背景実行は今回は見送り）。

## 実施内容

- `cmd_ask` の出力を `print(result)` → `print(getattr(result, "answer", result))` に変更し、回答本文（インラインの `[N]` マーカー含む）だけを出力するようにした。
- `getattr(..., result)` のフォールバックで、`answer` 属性が無い戻り値でも従来どおり全体を印字（後方互換・防御的）。
- 捨てるのは `references=[ChatReference(... cited_text=...)]` の巨大ダンプのみ。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_manager.py` | `cmd_ask` の出力を `AskResult` 全体から `result.answer` のみへ。理由コメントを付記 |

## 設計判断

- `ask` の利用箇所（`check-fact-lim` / `research_trivia-source` / `notebooklm` の各スキル）はすべて**印字された回答テキストを読むだけ**で、`AskResult` の repr や `references` をパースしている箇所は無いことを grep で確認（`AskResult` / `answer=` / `conversation_id` のパース無し）。インライン出典マーカーは `result.answer` に含まれるため、いずれの用途も維持される。
- フラグ（`--answer-only`）追加ではなくデフォルト変更を選択。全消費者が answer のみで足りるため、デフォルトを絞る方が単純で効果が確実。

## 確認結果

- 短い質問での出力：`TCMスラスタは4本搭載されています[1-3]。` のみ。サイズ **55バイト**（従来は数百KB〜2.3MB）、`ChatReference` 出現 **0**、`[N]` マーカーは保持。
- `/check-fact-lim` をフォーク実行 → **タイムアウトせず完走**（STEP1 完全性＋STEP2 ファクト2回、最大5回ループ中2回で 100点到達）。

## 今後の課題

- 出力削減のみのため、本文全体を投げる長い ask では生成待ちブロッキングによる stream idle が依然残る可能性がある。不十分なら次の一手として「質問分割（セクション単位／主張抽出）」「背景実行＋ポーリング」を検討する。
- 防御的に `cmd_ask` のクライアントへ `timeout=` を付ける案（`deep_research` は `timeout=120` 指定済み）。
