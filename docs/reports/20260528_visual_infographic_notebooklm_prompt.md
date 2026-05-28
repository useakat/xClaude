---
title: visual_infographic：NotebookLM によるプロンプト生成への委譲
date: 2026-05-28
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../history/20260528_visual_infographic_notebooklm_prompt_session/)

## 背景・動機

従来の `visual_infographic` スキルは、Claude 自身がインフォグラフィック作成用のプロンプト（N パターン）を生成してから NotebookLM に渡していた。しかし Claude はソース素材（テキスト＋スーパーニャンコ画像）を「生成後に渡す」構造だったため、画像の特徴を反映したプロンプトが作れなかった。

NotebookLM 自身にソース素材を持たせた状態でプロンプトを生成させることで、テキスト内容とスーパーニャンコ画像の両方を文脈として活かしたプロンプトが得られると判断し、フローを変更した。

合わせて、毎回同じ Infographic 生成設定（language/orientation/style/detail）と NotebookLM への質問テンプレートを設定ファイルに外出しし、変更箇所を一元管理できるようにした。

## 実施内容

- `scripts/notebooklm_manager.py` に `setup-notebook` サブコマンドを追加（notebook 作成＋テキストソース追加＋追加 URL ソース登録のみ、インフォグラフィック生成は行わない）
- `SKILL.md` のフロー変更：
  - Step 2: `make-infographic --keep` による notebook 作成を廃止 → `setup-notebook` コマンドで先に notebook を作成
  - Step 3: Claude によるプロンプト生成を廃止 → `ask` コマンドで NotebookLM にプロンプト 3 パターンを生成させる
  - Step 5: `make-infographic` を廃止 → 既存 notebook_id を使う `infographic` コマンドに統一（1枚目も同じ）
- `ask_template.txt` を新規作成：NotebookLM への質問テンプレートを固定テキストとして管理
- `infographic_config.env` を新規作成：Infographic 生成設定（language=ja / orientation=landscape / style=sketch-note / detail=standard）を外部ファイル化

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/visual_infographic/SKILL.md` | Step 2〜5 を全面書き換え。count 引数を削除し 3 パターン固定に |
| `.claude/skills/visual_infographic/ask_template.txt` | 新規。NotebookLM への質問テンプレート |
| `.claude/skills/visual_infographic/infographic_config.env` | 新規。Infographic 生成オプション 4 項目 |
| `scripts/notebooklm_manager.py` | `setup-notebook` サブコマンドを追加（約 40 行）|

## 設計判断

- **`count` 引数を廃止して 3 固定にした理由**：`ask_template.txt` が「3パターン考えてください」と固定で問い合わせる設計のため、引数で枚数を変えても NotebookLM のレスポンスとズレが生じる。シンプルさを優先して 3 固定とした。
- **質問テンプレートをファイル外出しにした理由**：テンプレートの調整はコード変更ではなくコンテンツ変更に近いため、`SKILL.md` に埋め込むより独立ファイルの方が編集しやすい。

## 確認結果

`/visual_infographic` を実行してフローが正しく動くことをテスト実行で検証（認証トークン期限切れのため NotebookLM への接続前で中断したが、Step 0〜1 の認証ファイル取得・テキスト書き出しは正常動作を確認）。

## 今後の課題

- 認証トークンを更新後（`bash scripts/notebooklm_auth_push.sh`）に Step 2〜5 の動作を実機確認する
- NotebookLM の `ask` レスポンスが `---` 区切りで返ってこないケースへの対応（パース失敗時のフォールバック）
