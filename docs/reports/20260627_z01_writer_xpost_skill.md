---
title: z01 プロジェクト定義と汎用 writer-xpost スキルを追加
date: 2026-06-27
tags: [skill, project]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260627_z01_writer_xpost_skill/)

## 背景・動機

X 運用に「140 字テキストのみ・高頻度」の実験枠が必要になった。ネタに対する X での反応（いいね・ブクマ・引用RT）を軽量・低コストで観測し、反応の良かったネタを note 記事（W002）/ X 長文ストーリー（W001）/ ワンポイント解説（W003）へ昇格させる導線を作るのが狙い。あわせて、毎日の投稿頻度を上げてアカウントのアクティブさを保つ。

この用途のために新規プロジェクト **z01（X 短文投稿）** を定義した。さらに、これまで投稿タイプごとに個別 writer スキル（writer-xonepoint / writer-xstory / writer-xshort 等）が分かれていたのを、**作業フォルダの spec.md/plan.md/brand.md を読んで投稿を組み立てる汎用 writer** に一般化し、`writer-xpost` として切り出した。z01 はこの汎用スキルを呼び出す構成にした。

## 実施内容

- **z01 プロジェクト定義**を新設：`projects/z01/` に `plan.md`（目的・ターゲット・成功条件）/ `brand.md`（短文専用の表現ルール・継承元 `../../brand.md`）/ `spec.md`（制作フロー）を作成。ペルソナなど基本方針は W003 に準拠。
- **汎用 writer-xpost スキル**を追加（writer-xstory のテーマ先行フローがベース）：
  - 入力は「テーマ ＋ 文字数範囲」。作業フォルダの spec/plan/brand を読み込む。
  - 「フォーカス決定 → 冒頭フック決定 → 本文作成」の 3 段階を**全自動**で実行（ユーザー確認なし。各ステージで候補を作り最良を自動選択）。
  - 投稿文は「冒頭フック → 本文 → 締め」の構成。冒頭フックは `style/hook-patterns.md` 参照、本文の内容・構成は spec.md/brand.md を正とする。
  - 型番号・案数に依存しない汎用表現に整理（特定プロジェクトに縛られないため）。
- `metadata.yaml` に `writer-xpost: category: コンテンツ制作` を追記。
- **z01 spec.md の本文生成を `/writer-xpost` に委譲**：STEP 3 を inline 生成から `/writer-xpost`（テーマ＝選定ネタ・文字数 135〜140 字）呼び出しへ変更。
- 付随して `.claude/settings.json` の `permissions.additionalDirectories` に `/root/xClaude` を追加（`projects/z01` を作業ディレクトリにした際、リポジトリ直下の `.claude/skills/...` 等を編集するたびにプロンプトが出る問題を解消）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/writer-xpost/SKILL.md` | 汎用 X 投稿 writer スキルを新規作成（全自動・3 段階フロー） |
| `.claude/skills/metadata.yaml` | `writer-xpost: category: コンテンツ制作` を追記 |
| `projects/z01/plan.md` | プロジェクトの目的・ターゲット・成功条件を定義 |
| `projects/z01/brand.md` | 短文専用の表現ルールを定義（共通 brand.md を継承） |
| `projects/z01/spec.md` | 制作フロー（4 シート取得→ランダム選択→`/writer-xpost`→Gmail 下書き）を定義 |
| `.claude/settings.json` | `permissions.additionalDirectories` に `/root/xClaude` を追加 |

## 設計判断

- **個別 writer ではなく汎用 writer に一般化**: 投稿タイプごとにスキルが増えると保守が分散する。スタイル・本文ルールを作業フォルダの spec/plan/brand に外出しし、スキル本体はフローだけを持つ構成にした。プロジェクト固有の判断は各フォルダの定義ファイルに集約される。
- **全自動フロー**: writer-xstory の対話制作（フォーカス・フックをユーザーが選ぶ）を、z01 の高頻度運用に合わせて自動選択に変更。
- **z01 は writer-xpost を呼ぶ薄い spec**: spec.md は本文生成を `/writer-xpost` に委譲し、ネタ選定（4 シート横断ランダム）と Gmail 下書き作成に専念させた。

## 確認結果

`/writer-xpost` がスキルリストに登録され呼び出せることを確認。z01 の 3 定義ファイルが揃い、spec.md の STEP 3 が `/writer-xpost` を参照していることを確認。

## 今後の課題

- 既存の writer-xshort と writer-xpost は機能が重なる。z01 spec が writer-xpost に一本化されたため、writer-xshort の廃止・統合は別途検討（spec.md には「writer-xshort は廃止予定」と明記済み）。
