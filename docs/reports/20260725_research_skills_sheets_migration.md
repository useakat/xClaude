---
title: research 系スキルを sheets_values.py に移行＋open_by_key に 404 リトライ追加（append 経路の本番書き込み初テスト完了）
date: 2026-07-25
tags: [skill, infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260725_research_skills_sheets_migration_session/)

## 背景・動機

7/25 朝の「ネタ在庫チェック routine」（onePointNeta / noteNeta の未使用ネタ数を確認し、10 件未満のシートがあれば `/research-trivia` や `/research-note-projectx` を発火する定期タスク）を初回実行したところ、以下 2 点が確認された：

1. **routine プロンプトが mcp-gsheets の MCP ツール（`sheets_get_values`）を直呼びしていた** — 7/18 の routine Sheets スクリプト移行で `reporter-daily` は `scripts/sheets_values.py` 経由に移行済みだが、このネタ在庫チェック routine は未対応のまま残っていた。閾値割れ時に発火する `research-trivia` / `research-note-projectx` も同じ問題を抱えていた（`sheets_get_values` / `sheets_append_values` を MCP ツール直呼び）
2. **セッション初回コールドスタート時に `sheets_values.py` が 404 を返した** — 同じセッションで直後にリトライすると成功し、`values_get` ではなく `open_by_key` の Drive 側メタデータ取得だけが 404 になっていた（原因は完全特定できていないが、初回コールドで一度だけ発生する一過性の挙動）

さらに 7/18 報告書で「書き込み系（append / update）の実テスト未実施」と明記されており、routine が実際に発火して `/research-trivia` が動くと初めて `sheets_values.py append` が本番実行される状況だった。routine 落ち事故を防ぐため、事前に本番書き込みを検証しておく必要があった。

## 実施内容

- **`research-trivia` / `research-note-projectx` の Sheets 呼び出しをスクリプト経由に置換**
    - `sheets_get_values(...)` → `python3 scripts/sheets_values.py get "<id>" "<range>"`
    - `sheets_append_values(...)` → `VALUES_JSON=$(python3 -c 'json.dumps(...)') && python3 scripts/sheets_values.py append ...`（`ensure_ascii=False` 必須・複数件は 1 回でまとめて append）
    - 両スキル冒頭に「mcp-gsheets の MCP ツールは使わない」方針ブロックを追加（`reporter-daily` と同じ文言）
- **`scripts/sheets_values.py` に `open_with_retry` を追加**：`open_by_key` が 404（`SpreadsheetNotFound`）を返した場合、レスポンスの status/body を stderr にログしたうえで 1 秒待って 1 回だけリトライする。2 回目も 404 なら通常どおり例外を上げる
- **routine プロンプト書き換え案をよーんに提示**（Web UI 側で貼り替え）：MCP 直呼びから `python3 scripts/sheets_values.py get ...` に変更、両方 10 件以上ならサイレント終了（`PushNotification` は送らない）と明示
- **append 経路の本番書き込みテストを実施**：`onePointNeta` に No=999 の【TEST-DELETE】行（11 セル）を 1 件 append → read-back で日本語・記号含めて完全一致を確認 → よーんが手動削除

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/research-trivia/SKILL.md` | `sheets_get_values` / `sheets_append_values` を `sheets_values.py` 呼び出しに置換。冒頭に MCP ツール不使用の方針ブロックを追加 |
| `.claude/skills/research-note-projectx/SKILL.md` | 同上（`noteNeta` シート） |
| `scripts/sheets_values.py` | `open_with_retry` 関数を追加し `main` から呼ぶ。404 時に status/body を stderr にログして 1 秒後 1 回リトライ。`time` を import |

（routine プロンプトはリポジトリ外の Claude Code Web UI に保存されているため、書き換え文面をよーんに提示するに留めた）

## 設計判断

- **リトライは `open_by_key` にのみ適用、`values_get` / `values_append` / `values_update` はリトライしない**：観測された 404 は open_by_key（Drive API 側のメタデータ取得）のみで、書き込み後の read-back でも再現しなかったため。書き込み系にリトライを付けると二重 append のリスクが出るため、症状に応じた最小限のリトライに絞った
- **リトライ回数は 1 回のみ・待機 1 秒**：症状は「初回コールドの一過性」であり、2 回目も 404 なら真の権限問題として扱うべき。長時間の指数バックオフは routine 全体の実行時間を圧迫するため採用しない
- **append テストは本番シートに 1 行だけ書き込み → 手動削除**：テスト用シートを新設するコストが大きく、既存シートに ID=999 の明確な TEST マーカーを付ければ削除も 1 分で済むため。書き込み経路の互換性（日本語・記号・`ensure_ascii=False` の要否）を実データで検証できるメリットが上回った
- **`sheets_values.py` に delete 機能は追加しない**：今回の TEST 行削除はよーんに手動依頼で済ませ、`sheets_values.py` の責務は「本番運用で使う操作(get / append / update)」に限定。delete が routine で必要になったときに追加する

## 確認結果

- **`sheets_values.py`**：SS1 `onePointNeta!I1:I5`、SS1 `日次記録!A1:A2`、SS2 `outputs!A1:A2` の 3 経路すべて get 成功。既存の `reporter-daily` 用パスの回帰なし
- **append テスト**：`onePointNeta!A113:K113` に 11 セル書き込み成功（レスポンス `updatedCells: 11`）。read-back で `[999, "【TEST-DELETE】...", ..., "TEST"]` が完全一致で復元。日本語・`【】`・`削除してください` のような句読点混じり文字列も無事
- **リトライ挙動**：今回のセッションでは初回 404 が再現しなかったため、リトライ経路自体は空振り。次回 404 が発生した場合は stderr に `[sheets_values] 404 on open_by_key(attempt 1) id=... status=... body=...` が出力され、原因究明の材料になる

## 今後の課題

- **routine プロンプトの Web UI 側書き換え**：よーんが「未使用ネタ数を確認する」routine の本文を提示済み文面に貼り替える作業が残っている
- **404 の根本原因究明**：現時点では「初回コールドで稀に発生」以上のことはわかっていない。次回発生時のログを見て、SessionStart hook との競合／IPv4 固定パッチの副作用／gspread の open_by_key メタデータ経路特有の問題、どれに該当するか切り分ける
- **他スキルの棚卸し**：`writer-xshort` / `writer-xnews` / `writer_note-story` / `daily-xonepoint` / `draft_xstory` / `analyze-target` / `sync-to-sheets` / `sync-x-note-analytics` / `research_pain-xpost` / `plan-xnote-funnel` / `record-note-posts` / `ops_analyze-posts` / `research-plan` / `.claude/agents/update-x-analytics.md` などが未移行のまま。routine から呼ばれる可能性がある順に優先度付けして順次移行する
- **書き込み系リトライの設計判断**：今後 append/update 側でも 404 が観測された場合、二重書き込みリスクの吸収方法（idempotency key など）を検討する
