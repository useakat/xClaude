---
title: Wiki で空行なしの単一改行も改行表示する（remark-breaks 導入）
date: 2026-11-03
tags: [wiki, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261103_wiki_remark_breaks/)

## 背景・動機

Wiki の原稿（`docs/**/*.md`）は、Markdown の標準仕様どおり単一の改行がスペース扱いになり、空行を挟まないと表示上で改行されなかった。
そのため日報・週報では「入れ子は全角スペース、箇条書き間は空行」という回避ルールを置いて書いており、原稿を書くたびに空行を足す手間が発生していた。
Wiki は Starlight（Astro）で、Markdown の変換は remark で行われる。単一改行を `<br>` に変換する `remark-breaks` を remarkPlugins に足せば、原稿側の書き方を変えずに解決できる。

## 実施内容

- `starlight/` に `remark-breaks`（^4.0.0）を `npm install` で追加
- `astro.config.mjs` で `remark-breaks` を import し、`markdown.remarkPlugins` に登録
- 週報 2026-W33（全角スペース入れ子）・`index.md`・history 1 本の 3 ページに絞ってローカルビルドし、単一改行が `<br>` になることを確認
- master に push（デプロイは GitHub Actions が `starlight/**` の変更で自動実行）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `starlight/astro.config.mjs` | `import remarkBreaks from 'remark-breaks'` を追加し、`markdown: { remarkPlugins: [remarkBreaks] }` を登録 |
| `starlight/package.json` | 依存に `remark-breaks` を追加 |
| `starlight/package-lock.json` | 上記に合わせて更新（CI の `npm ci` が通るように） |

## 設計判断

- **プラグインで全ページに適用した**：原稿ごとに末尾スペース 2 個や `<br>` を書く案は、書き手の手間が減らないため採らなかった。
- **既存ページへの影響を事前に確認した**：空行や全角スペースで回避していたページは、今までどおり表示される。一方、幅に合わせて途中で折り返して書いている文章は、折り返した位置で改行される。該当は約 185 ファイルで、`docs/history/` の会話貼り付けが中心。会話ログは元の改行どおりに出るので、むしろ読みやすくなる想定。
- **スキル記述は変えなかった**：`reporter-daily` の「箇条書き間は空行にする」ルールは不要になる可能性があるが、今回は触っていない。

## 確認結果

- 全 800 ページのビルドは、このマシンのメモリ不足（空き約 500MB）で強制終了され、ローカルでは試せなかった。
- 3 ページに絞ったビルドは成功し、週報 2026-W33 で `<br>` が 54 箇所出力されること、全角スペース入れ子の行が改行されて出ることを確認した。
- 全ページの最終確認は、push 後の GitHub Actions（Deploy Wiki to GitHub Pages）の結果で行う。

## 今後の課題

- `reporter-daily` など、空行回避を前提にしたスキルの記述を見直す。
- 折り返し済みの段落が多い `docs/history/` で、表示が不自然なページがないかをデプロイ後に確認する。
