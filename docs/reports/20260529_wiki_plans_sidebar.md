---
title: Wiki：docs/plans を Wiki サイドバーに追加
date: 2026-05-29
tags: [wiki]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260529_wiki_plans_sidebar_session/)

## 背景・動機

`docs/plans/` に計画ファイル（`202606_monetization.md`）が作成されていたが、Wiki サイドバーに「計画」セクションが未登録で、かつファイルに `sidebar: hidden: true` が付いていたため Wiki から参照できなかった。計画ドキュメントも Wiki で閲覧できるよう整備した。

## 実施内容

- `starlight/astro.config.mjs` のサイドバーに「計画」セクションを追加（`autogenerate: { directory: 'plans' }` 方式）
- `docs/plans/202606_monetization.md` の `sidebar: hidden: true` を削除

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `starlight/astro.config.mjs` | sidebar に「計画」セクション（autogenerate: plans/）を追加 |
| `docs/plans/202606_monetization.md` | frontmatter の `sidebar: hidden: true` を削除 |

## 設計判断

`autogenerate` 方式を採用したため、今後 `docs/plans/` に新規ファイルを追加するだけでサイドバーに自動反映される。個別にサイドバー設定を追記する必要はない。

## 確認結果

コミット `4705dc8` を push 後、GitHub Actions（Deploy Wiki to GitHub Pages）が起動。Wiki サイドバーに「計画」セクションが追加され、6月マネタイズ計画ページが閲覧可能になる。
