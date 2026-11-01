---
title: Gmail ラベルで X 自動投稿の時間帯を指定可能に（6時/12時/17時/20時投稿）
date: 2026-11-01
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

※実装は 2026-10-25 のローカルセッション（コミット `2b920f5`）。記録が漏れていたため本日付で報告書を作成。

## 背景・動機

X 自動投稿はこれまで「件名 → 投稿枠」の固定対応（例:【X短文投稿】→ 朝枠）で、下書きを作った時点で投稿時間帯が決まってしまい、投稿ごとに「この1本は17時に出したい」という指定ができなかった。曜日・時間帯の検証（H2 の折り返し設計・W001 の月金17時運用など）を進めるうえで、よーんが Gmail 下書きにラベルを付けるだけで枠を指定できる仕組みが必要だった。

## 実施内容

- **`scripts/post_by_label.sh`（新規）**: 投稿時間帯ラベル「`<時>時投稿`」（6/12/17/20 の4種）が付いたメールを、件名を問わずその枠で投稿する。件名4種（【ワンポイント解説】W003 /【質問回答】W006 /【X長文】W001 /【X短文投稿】z01）を順に探し、最初に見つかった1件だけ投稿（howID・ログは件名で決定）。終了コード 0=投稿成功 / 20=対象なし / 1=失敗
- **`scripts/post_from_email.sh`**: `--label <時刻ラベル>` オプションを追加。指定時はそのラベル付きメールだけを探し、無指定時は時刻ラベル付きを除外（二重投稿の防止）
- **`scripts/run_xonepoint_post.sh` / `run_xlong_post.sh` / `run_xshort_post.sh` / `run_question_post.sh`**: 各枠の cron が従来の件名検索の前に `post_by_label.sh <時>` を呼ぶよう変更
- **ドキュメント**: `docs/workflows/x-auto-post.md` に投稿時間帯ラベルの仕組みを追記。`projects/w001・w003・z01` の各 spec と `mond-letter-reply` SKILL にもラベルの説明を追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/post_by_label.sh` | 新規。時刻ラベル付きメールを件名横断で投稿 |
| `scripts/post_from_email.sh` | `--label` 追加・無指定時はラベル付きを除外 |
| `scripts/run_*_post.sh`（4本） | 件名検索の前に post_by_label.sh を実行 |
| `docs/workflows/x-auto-post.md` | 投稿時間帯ラベルの説明を追記 |
| `projects/{w001,w003,z01}/spec.md`・`.claude/skills/mond-letter-reply/SKILL.md` | ラベル運用の説明を追記 |

## 設計判断（任意）

- ラベル名は「17時投稿」のような日本語そのままにし、Gmail 上でよーんが直感的に付けられる形を優先
- 1枠1件・失敗時はその枠で中断（次の件名に進まない）とし、同一枠での連続投稿や失敗の連鎖を防ぐ

## 確認結果

- コミット `2b920f5`（2026-10-25）として実装済み・push 済み。cron の各枠から post_by_label.sh 経由の投稿が動作している
