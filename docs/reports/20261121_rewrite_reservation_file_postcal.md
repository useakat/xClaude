---
title: リライトを予約ファイル方式にして postcal で確認・予約する形に変更し、Gmail【リライト】経路を廃止
date: 2026-11-21
tags: [workflow, skill, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261121_rewrite_reservation_file_postcal/)

## 背景・動機

同日、z01・販促（W007）の取り込みを「予約ファイル → postcal の下書き → 画面で『投稿予約』」の方式に変えた（[→報告書](../20261121_postcal_draft_review_flow/)）。一方、リライト（`/writer-xrewrite`）は件名【リライト】の Gmail 下書きのままで、この確認ゲートの対象外だった。リライトの下書きは Gmail に作られ、20 時枠の cron が件名で拾って投稿する仕組みだったため、よーんの要望（確認してから投稿予約したい）で、リライトも同じ方式に揃える。あわせて、リライトの Gmail 経路を「予備」として残す必要はないとの判断で廃止した。

## 実施内容

- **`/writer-xrewrite` の STEP 7 を差し替え**：Gmail 下書きの代わりに、`outputs/scheduled-posts/rewrite/<日時>_<topic>.md` の予約ファイルを作る。メモ・チェック証跡・不採用案は `## 記録` に入れ、`## 投稿文` には確定稿だけを置く。STEP 8 で予約ファイルと記録 CSV を同じ commit・push に含め、STEP 9 の完了報告・確定ゲート（レベル 2 見出しの混入禁止）も新方式に合わせた。
- **postcal にリライトの種類を追加**：`rewrite_short`（z01r）・`rewrite_onepoint`（W003r）・`rewrite_long`（W001r）。画面の編集・投稿予約の検証をそのまま通る。
- **インポーター**：`kind: rewrite_*` は**毎日 20:00 の最寄りの空き枠**を仮日時として下書き登録する。`source: "rewrite[ツイートID]"` を `neta_id` に引き継ぐ（投稿時に outputs の neta_id 列に入り、`rewrite_pool.py` の「リライト済み」判定が壊れない）。
- **Gmail【リライト】経路の廃止**：`run_xshort_post.sh`（20 時枠）と `post_by_label.sh` から件名【リライト】の検索を削除。リライトは postcal 経由のみ。
- `docs/workflows/x-auto-post.md` にリライトの経路を追記し、件名の種類数の記述を実態（6 種）に直した。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/writer-xrewrite/SKILL.md` | STEP 7（予約ファイルの作成）、STEP 8（予約ファイルも commit・push）、STEP 9、確定ゲート、description を新方式に更新 |
| `postcal/kinds.py` | `rewrite_short` / `rewrite_onepoint` / `rewrite_long`（z01r / W003r / W001r）を追加 |
| `scripts/postcal_import.py` | `REWRITE_SLOTS`（毎日 20 時）、`rewrite_*` の枠割当、`neta_id` に `rewrite[ID]` を許可 |
| `scripts/run_xshort_post.sh` | 件名【リライト】の検索ブロックを削除 |
| `scripts/post_by_label.sh` | 検索対象の一覧から【リライト】を削除 |
| `docs/workflows/x-auto-post.md` | リライトの予約ファイル経路と Gmail 経路の廃止を追記 |

## 設計判断

- **枠は毎日 20 時**：従来の Gmail 運用でリライトが 20 時枠だったのを踏襲した。別の日・時刻にしたいときは、画面で日時を直してから「投稿予約」を押す。
- **`neta_id` に `rewrite[ID]` を引き継ぐ**：`rewrite_pool.py` は outputs の neta_id（`rewrite[ID]`）で「リライト済み」を判定している。postcal 経由で `postcal[予約id]` になると判定が壊れるため、インポーターの許可形式を拡張した。`record_output.py` は what_id・neta_id を任意の文字列で受け付け、SS1 の更新は what_id が `z01` のときだけなので、`z01r` では誤って更新されない。
- **cron は無改修で足りる**：枠の cron は postcal の予約（`status='queued'`）を先に拾うため、下書きの間は投稿されない。Gmail 経路は、よーんの判断で予備として残さず削除した。
- **`post_from_email.sh` の `what_id:` 行の上書き処理は残した**：【リライト】専用だったが、他の Gmail 経路でも使える任意機能のため触っていない。

## 確認結果

- 一時 DB で、下書き方式のテスト 23 項目にリライト用 8 項目を加えた全 31 項目が合格（リライトの下書き登録・仮枠が毎日 20 時で別の日に重ならない・`neta_id` と what_id（W001r）の引き継ぎ・投稿文に `## 記録` 以降が混ざらない・画面からの投稿予約・画面編集後も `neta_id` を保つ）。`py_compile`・`bash -n` OK。
- VPS：`git log` の先頭が `4488702` まで取り込み済み、インポーターのタイマー稼働（`logs/postcal_import.log` で確認）。
- **未確認**：リライトの routine 実行で実際に予約ファイルが作られ、画面に下書きとして出る一連の動作。

## 今後の課題

- **リライトの routine に保存済みのプロンプトに「Gmail 下書きを作る」等の指示が残っていると、スキルと食い違う**（z01 の routine でも同じ食い違いが起きた）。routine 側のプロンプトの確認・修正が必要。
- 画面にはリライト専用の色分けがない（種類名の文字で見分ける）。スマホ幅では「リライト（ワンポイント）」のチップが途中で切れる。
- postcal の静的ファイル（CSS 等）は、更新後にブラウザのキャッシュが残ると反映されない（強制再読み込みで解消）。`style.css?v=<更新時刻>` で自動的に取り直す対策は未実施。
