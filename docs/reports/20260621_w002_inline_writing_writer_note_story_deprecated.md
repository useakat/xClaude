---
title: W002 本文インライン執筆の明記と writer_note-story 非推奨化（Wiki 廃止・非推奨カテゴリ新設）
date: 2026-06-21
tags: [workflow, skill, wiki]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

「W002 の note 本文は writer_note-story スキルが書いているのか」という確認から、実態が判明した。W002 の本文は担当エージェントが `brand.md`＋`spec.md` に沿って**インライン執筆**しており、`writer_note-story` は呼んでいない。spec.md にもその旨の記載がなく、本文の主体が曖昧だった。

`writer_note-story` は一段古い別系統で、W002 と矛盾する：出典マーカー `[^N]`（W002 は `[N]`）、URL 省略可（W002 は必須）、参考情報の2段階運用なし、保存先・後続スキル（`/check-fact` 等）が別。委譲するとこれらが壊れるため、インライン維持が整合的（ユーザー決定）。あわせて、今後使わない `writer_note-story` を誤って呼ばないよう非推奨化する。

## 実施内容

- `projects/w002/spec.md` step6 に「本文はスキルに委譲せず brand.md 準拠でインライン執筆する／`writer_note-story` は出典形式・下流フローが異なるため使わない」を明記。
- `writer_note-story/SKILL.md` の冒頭にタイトル `（廃止済み / 非推奨）` と廃止バナーを追加（既存の `sync-to-sheets（廃止済み）` 方式に倣う）。削除はしない。
- Wiki スキル一覧に「廃止・非推奨」カテゴリを新設：`update_wiki_skills.py` の `category_order` 末尾に `'廃止・非推奨'` を追加し、`metadata.yaml` で `writer_note-story` と `sync-to-sheets` を同カテゴリへ移動。`update_wiki_skills.py` を実行し `docs/skills/index.md` 等を再生成。両スキルは従来カテゴリ（コンテンツ制作／画像・同期）から消え、末尾の「廃止・非推奨」セクションに集約された。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w002/spec.md` | step6 にインライン執筆の明記（writer_note-story 不使用の理由つき） |
| `.claude/skills/writer_note-story/SKILL.md` | 冒頭に廃止タイトル＋非推奨バナーを追加 |
| `.claude/skills/metadata.yaml` | `writer_note-story` と `sync-to-sheets` を `廃止・非推奨` カテゴリへ |
| `scripts/update_wiki_skills.py` | `category_order` 末尾に `'廃止・非推奨'` を追加 |
| `docs/skills/index.md` ほか | Wiki 再生成（廃止・非推奨セクション反映） |

## 設計判断

- スキルは削除せず deprecate。git 履歴だけでなくファイルとして残し、過去記事（2026-05-30 SCEtoAUX 等）との対応も追えるようにした。`category_order` に未登録のカテゴリは index から消える生成仕様を利用し、「一覧から外す」と「非推奨セクション新設」を1つの仕組みで両立。

## 確認結果

- `docs/skills/index.md` に「## 廃止・非推奨」セクションが生成され、`writer_note-story`・`sync-to-sheets` が集約。両スキルが従来カテゴリから消えていることを確認。
- `writer_note-story` を開くと冒頭バナーで非推奨と分かる状態になった。
