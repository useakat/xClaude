---
title: Wiki スキルページの description を JSON二重引用符でクォートし YAML frontmatter 破損を修正
date: 2026-08-10
tags: [wiki, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

8/10 11:58 のデプロイ以降、Wiki（Starlight/astro）のビルドが失敗していた。エラーは `bad indentation of a mapping entry`（`starlight/src/content/docs/skills/check-reader.md:2`）。

原因は、`docs/skills/check-reader.md` の frontmatter `description:` の値に **`【構成モード】: `（コロン＋スペース）** が含まれ、無クォートだったため YAML が「ネストしたマッピング項目」と誤解したこと。この description は 8/8 の `check-reader` 新設で追加され、`--plan` の説明にコロンを含んでいた。docs/skills/ は CI で starlight 側へコピーされるため、生成元の破損がそのままビルド失敗になった。

## 実施内容

- **生成器 `scripts/update_wiki_skills.py` を修正**：frontmatter を組み立てる際、`description: {description}`（無クォート）から **`description: {json.dumps(description, ensure_ascii=False)}`** に変更。JSON の二重引用符文字列は YAML でも有効な引用スカラーで、コロン・引用符・バックスラッシュを安全にエスケープできる。`import json` を追加。
- **全スキルページを再生成**（49ページ）。すべての description がクォートされ、YAML frontmatter の全件検証で NG 0 件を確認。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/update_wiki_skills.py` | `description` を `json.dumps` でクォート出力（`import json` 追加） |
| `docs/skills/*.md`（49） | 再生成（description をクォート） |

## 確認結果

- 再生成後、`docs/skills/check-reader.md` の 2 行目が `description: "…【構成モード】: 執筆前…"` とクォートされていることを確認。
- 全 `docs/skills/*.md` の frontmatter を `yaml.safe_load` で検証し NG 0 件。
- これにより astro build の frontmatter パースエラーは解消される見込み（次回デプロイで確認）。

## 今後の課題

- 生成器がクォートするようになったため、今後 description にコロン・記号・引用符が入っても frontmatter は壊れない。
- 同種の自動生成 frontmatter（報告書・履歴等）は人手で書くため今回の対象外だが、コロンを含むタイトル/説明を書くときは引用に注意。
