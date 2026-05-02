---
title: Wiki システム構築
date: 2026-05-02
tags: [wiki, infra]
---

← [変更ログへ](../changelog.md#wiki-システム構築)

## 背景・動機

プロジェクトの仕様・スキル定義・ワークフローが CLAUDE.md とスキルファイルに分散しており、人間が読みやすい形で参照できなかった。Claude とユーザーの両方が参照できる Wiki が必要だった。

## 実施内容

- `docs/` に Wiki の Markdown ソースを配置（15ページ）
- `starlight/` に Astro + Starlight のビルド設定を配置
- `.github/workflows/deploy.yml` で GitHub Pages への自動デプロイを設定
- CLAUDE.md に Wiki URL を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `docs/` | Wiki コンテンツ（新規作成） |
| `starlight/` | Starlight ビルド設定（新規作成） |
| `.github/workflows/deploy.yml` | GitHub Pages 自動デプロイ（新規作成） |
| `CLAUDE.md` | Wiki URL を先頭に追記 |

## 設計判断

**Starlight を選んだ理由**：全文検索（Pagefind）が標準搭載。MkDocs は開発が停滞中（2025年11月にメンテナンスモード移行）。Docusaurus より軽量でドキュメント専用途に適している。

**docs/ と starlight/ を分けた理由**：Markdown ソースを Claude が直接 Read できるよう、ビルド設定と分離した。

## 確認結果

`https://useakat.github.io/xClaude/` で15ページが正常に表示されることを確認。Pagefind による全文検索も動作。

## 今後の課題

- スキル定義ページを主要スキル分追加
- 報告書・変更ログの運用フローを整備
