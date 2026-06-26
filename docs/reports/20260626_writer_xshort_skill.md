---
title: writer-xshort スキルを追加
date: 2026-06-26
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260627_20260626_writer_xshort_and_w003_roles/)

## 背景・動機

X投稿のバリエーション拡充のため、ワンポイント解説（200-260字）とは別に、より短くコンパクトな135-140字の投稿を自動生成するスキルが必要になった。4つのネタシート（onePointNeta / noteNeta / newsTopics / thoughts）を横断してランダムにネタを選ぶことで、多様な切り口の投稿を効率よく生成できる。

## 実施内容

- `.claude/skills/writer-xshort/SKILL.md` を新規作成
- `metadata.yaml` に `writer-xshort: category: コンテンツ制作` を追記
- 実行フロー: 4シート全件取得 → python3 random でランダム1件選択 → 135-140字投稿文生成（文字数チェック付き・最大2回再生成）→ Gmail 下書き作成

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/writer-xshort/SKILL.md` | スキル本体を新規作成 |
| `.claude/skills/metadata.yaml` | `writer-xshort: category: コンテンツ制作` を追記 |

## 設計判断

- **全シート全件対象**（ステータスフィルタなし）: ネタの多様性を確保するため、onePointNeta/newsTopics の「未使用」フィルタはかけない。
- **ランダム選択はランダムインデックスで実装**: 4シートを1プールに集約し `python3 random.randint` でインデックスを生成。Claude が「自分の好み」でネタを選ばないようにする。
- **ユーザー承認不要・全自動**: Gmail下書きはDraftであり送信ではないため、承認なしで完結するフローとした。
- **`[投稿文]...[/投稿文]` タグ形式**: cron 投稿フロー（`extract_tag.py`）との互換性を確保。メール本文に `ソース: {シート名}[{ネタ番号}]` を含め、どのネタから生成したかを追跡可能にした。

## 確認結果

`/writer-xshort` として呼び出せることをスキルリストで確認。
