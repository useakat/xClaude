---
title: 変更ログ
description: プロジェクトの変更履歴。各エントリに詳細報告書へのリンクを付ける。
---

変更1件につき1エントリ。詳細が必要なら報告書リンクへ。

---

## 2026-06-27

- **z01 短文投稿の cron 自動化（投稿スクリプト新設・writer-xshort 周辺調整）** — `【X短文投稿】` 下書きを X 投稿する `scripts/run_xshort_post.sh`（`post_from_email.sh … z01 x_post_short.log`）を新設し crontab に毎日 7:00/13:00/19:00 を登録。下書き作成用 `run_xshort_draft.sh` も追加（手動用）、`writer-xshort` 説明文を「投稿せず下書き作成のみ」と正確化。[→報告書](../reports/20260627_z01_xshort_post_cron/)
- **z01 プロジェクト定義と汎用 writer-xpost スキルを追加** — 140字テキストのみ・高頻度でX反応を観測する z01（X短文投稿）プロジェクトを新設し、テーマ＋文字数範囲から「フォーカス→冒頭フック→本文」を全自動生成する汎用 writer `writer-xpost` を追加。z01 spec.md は本文生成を `/writer-xpost` に委譲。[→報告書](../reports/20260627_z01_writer_xpost_skill/)

---

## 2026-06-26

- **writer-xshort スキルを追加** — 4シート（onePointNeta/noteNeta/newsTopics/thoughts）からランダムに1件ネタを選び、135-140字のX投稿文を生成してGmail下書きを作成する全自動スキル。ユーザー確認なし・`ソース: {シート名}[{ネタ番号}]` をメール本文に含め追跡可能。[→報告書](../reports/20260626_writer_xshort_skill/)
- **W003 output/draft ディレクトリの役割分担を spec.md に明文化** — `output/` は最終版3種のみ（index.md・採用図解PNG・生成プロンプト）、中間版はすべて `draft/` に置くルールを spec.md の Naming セクションと Verification に追記。既存投稿フォルダ（betelgeuse）の中間版も整理。[→報告書](../reports/20260626_w003_output_draft_role/)

---

## 2026-06-25

- **daily-xonepoint の Gmail 下書き作成を最終確定の承認後に移動** — Gmail 下書きを画像生成前の自動実行から「最終確定ゲート（STEP 7）でユーザー承認後に1回だけ作成」へ変更。`create_draft` が更新・削除不可で修正のたびに下書きが溜まる問題を解消。ステップ順を 6 画像→7 最終確定→8 Gmail→9 チャット履歴→10 Drive に再構成し spec.md も整合。[→報告書](../reports/20260625_daily_xonepoint_gmail_after_final_approval/)
- **W003 投稿フォルダ画像を Drive 保存・git 除外に移行** — 投稿フォルダの画像（draft・output の `*.png`）を git にコミットせず Drive＋ローカル保存に統一。`.gitignore` を `/projects/w003/**/*.png` に拡張、誤コミット済み画像を untrack、spec.md / daily-xonepoint に運用を明文化。リポジトリ肥大を防止。[→報告書](../reports/20260625_w003_post_images_drive_only/)
- **新規作業の開始前に git pull で最新化するルールを追加** — 複数環境から同じ master に push する運用で古い状態での作業・重複実装を防ぐため、CLAUDE.md の Git ルールに「作業開始前にまず git pull（未コミット変更は commit/stash 先行）」を明記。[→報告書](../reports/20260625_git_pull_before_new_work/)
- **daily-xonepoint のメール下書きを画像添付対応に修正** — SKILL STEP 8 が添付非対応の `mcp__claude_ai_Gmail__create_draft` を指定していたため下書きに画像が付かない不具合を、`create_gmail_draft.sh --attach` 方式へ変更して修正（spec.md の指定と整合）。[→報告書](../reports/20260625_daily_xonepoint_gmail_attach_fix/)
- **daily-xonepoint スキル・agent を非推奨化** — 制作フローの正本を `projects/w003/spec.md` に一本化。SKILL.md・agent 定義に非推奨バナーを追加し、metadata.yaml で「廃止・非推奨」カテゴリへ移動・Wiki 再生成。二重管理による不整合を解消。[→報告書](../reports/20260625_daily_xonepoint_deprecated/)

---

## 2026-06-22

- **W003 Gmail 下書きの本文フォーマットを明文化（`[投稿文]` 閉じタグ必須化）** — `[/投稿文]` 欠落で `extract_tag.py` が本文を抽出できず cron 投稿フローで投稿されない不具合を修正。原因は spec.md step 8 の本文フォーマット未定義。spec.md に `[投稿文]…[/投稿文]` 付きフォーマット（daily-xonepoint STEP 6 準拠）を明記し、`create_gmail_draft.sh --attach` 指定・Verification を開き/閉じ両タグ必須に変更。
