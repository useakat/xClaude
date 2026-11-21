---
title: 予約に原稿を作った Claude セッションへのリンクを持たせ、編集画面・一覧から開けるようにする
date: 2026-11-21
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261121_postcal_session_link/)

## 背景・動機

z01・リライトの原稿は無人のルーチン（クラウドのセッション）が作り、予約ファイル経由で postcal に**下書き**として入る（[→下書き方式の報告書](../20261121_postcal_draft_review_flow/)）。よーんは画面で本文を確認・修正してから「投稿予約」を押すが、修正したいときに**その原稿を作ったセッション**を探して開く手間があった。下書きの編集画面からそのセッションへすぐ飛べるようにする。

## 実施内容

- **予約ファイルの front-matter に `session_url` を追加**：原稿を作った Claude セッションの URL（`https://claude.ai/code/session_…`）。システムの commit 署名指示にある `Claude-Session:` の URL をそのまま使う。分からないとき（ローカル実行など）は空文字にし、推測で書かない。
- **インポーターが `session_url` を予約に保存**：`https://claude.ai/code/…` の形だけを採用し、それ以外の URL（claude.ai 以外など）は捨てる。画面に出すリンクなので、外部ドメインを入れないための検証。
- **画面に表示**：編集画面の上部に「このセッションを開く」（修正を頼むときはここから）、一覧に小さな「セッション」リンク。別タブで開く（`rel="noopener noreferrer"`）。
- **画面で編集・投稿予約しても URL を保つ**：フォームに項目は無いので、`neta_id` と同じく編集時は既存値を引き継ぐ。ファイルの変更で下書きを更新するときも、新しい URL があればそれを、無ければ既存値を使う。
- **DB に `session_url` 列を追加**：既存 DB は `connect()` 時に自動で列を後付けする（`neta_id` の追加と同じ仕組み）。移行作業は不要。
- **書き方のルールを追記**：z01 の `spec.md` と `/writer-xrewrite` のスキルに、`session_url` の書き方（`Claude-Session:` の URL を使う・分からなければ空）を追加。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `postcal/db.py` | `session_url` 列の追加（スキーマ・旧 DB への後付け・`create()` / `update()`）、docstring |
| `postcal/app.py` | 編集時に既存の `session_url` を保つ、`empty_post` に項目追加 |
| `postcal/templates/form.html` | 編集画面の上部に「このセッションを開く」 |
| `postcal/templates/calendar.html` | 一覧に「セッション」リンク |
| `scripts/postcal_import.py` | front-matter の `session_url` を読み、`claude.ai/code` の形だけ採用して保存（作成・下書き更新の両方） |
| `projects/z01/spec.md` | front-matter の例に `session_url` を追加、書き方のルールを追記 |
| `.claude/skills/writer-xrewrite/SKILL.md` | 同上（リライトの予約ファイル） |
| `docs/workflows/x-auto-post.md` | `session_url` の説明を追記 |

## 設計判断

- **予約ファイル（front-matter）で渡す**：クラウドのルーチンは `post.usephys.net` に直接つなげず、git 経由の受け渡しだけが使える。予約に付ける情報も、これまでの `source`・`uid` と同じく front-matter に載せるのが最小の変更。
- **`claude.ai/code/…` の形だけ採用**：画面に出すリンクなので、検証なしに任意の URL を載せない。形が合わなければ空にして登録は続行する（取り込み自体は止めない）。
- **ルーチンは自分のセッション URL を `Claude-Session:` の行から取る**：commit 署名のために毎回渡される情報なので、追加の仕組みなしに使える。無ければ空にして推測しない（誤ったリンクを残さないため）。
- **販促（W007）は対象外にした**：依頼は z01・リライト。仕組みは共通なので、必要なら販促の予約ファイルにも同じ項目を足せる。

## 確認結果

- 一時 DB で全 39 項目が合格（今回追加した 8 項目：claude.ai の URL の保存／他ドメインの URL を採用しない／`session_url` なしでも登録できる／編集画面のリンク（`rel="noopener noreferrer"` つき）／URL が無ければリンクを出さない／一覧のリンク／画面で編集・投稿予約しても URL を保つ／旧スキーマ DB への列の後付けと既存行の読み取り）。`py_compile` OK。
- **未確認**：VPS 配備後の実画面での表示、および実際の z01・リライトの routine が `session_url` を書くこと。

## 今後の課題

- 配備後の最初の z01・リライトの原稿で、編集画面に「このセッションを開く」が出るか確認する（出なければ `session_url` が空のまま書かれている）。
- すでに取り込み済みの予約にはリンクが付かない（これから作る原稿から）。
- 販促（W007）の予約ファイルへの同項目の追加は未実施。
- routine 側の保存済みプロンプトに古い指示（Gmail 下書きなど）が残っていないかの確認は、引き続き必要。
