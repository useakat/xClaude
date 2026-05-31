# Production Spec — X ワンポイント解説（W003）

## Media
- X 投稿テキスト（1 本 / 日）
- インフォグラフィック画像 5 パターン（ユーザー承認後に生成）

## Input
- `../../brand.md`（共通ブランド定義）
- `brand.md`（本プロジェクトの表現ルール）
- `plan.md`（本プロジェクトの目的・ターゲット）
- Google Sheets `onePointNeta`（SS1: `1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM`）— ネタ在庫

## Output
- **テキスト**: Gmail 下書き（`[投稿文]` セクション付き）→ cron が X 投稿
- **画像**: `outputs/YYYYMMDD_xonepoint_[suffix].png` → Google Drive 自動同期

## Format
- **テキスト**: 常体（だ／のだ調）、4 段構成（brand.md 参照）、改行・空白行で段落を分ける
- **画像**: PNG、日本語テキスト埋め込み、`notebooklm_manager.py make-infographic` で生成

## Size
- **テキスト**: 200〜260 字推奨（最大 300 字 / 下限 140 字）
- **画像 landscape**: 1280 × 720
- **画像 portrait**: 縦長（notebooklm_manager.py の portrait オプションに委ねる）

## Naming

### 画像
| # | style | orientation | suffix |
|---|-------|-------------|--------|
| 1 | sketch-note | landscape | `sketch` |
| 2 | visual-cards | landscape | `cards` |
| 3 | timeline | landscape | `timeline` |
| 4 | sketch-note | portrait | `portrait` |
| 5 | visual-cards | portrait | `cards_p` |

ファイル名: `outputs/YYYYMMDD_xonepoint_[suffix].png`（例: `outputs/20260531_xonepoint_sketch.png`）

### Gmail 下書き
件名: `【ワンポイント解説】{トピック要約 10〜15 字} YYYYMMDD HH:MM:SS`

## Rules

### 制作フロー（`/daily-xonepoint` が自動実行）
1. **ネタ在庫確認** — 未使用 10 件未満なら補充（宇宙・物理 7 件 + その他 3 件）
2. **ネタ選定** — `日 mod 3` で分野グループ（0・1 → 宇宙・物理 / 2 → その他）を決定。最優先基準: 読者が今日体験した日常の物・感覚を入り口にできること
3. **原稿作成** — `/writer-xonepoint`
4. **ファクトチェック** — `/check-fact`
5. **トンマナ調整・P01化スコアリング** — 全 6 項目 8 点以上で合格（最大 5 回ループ）
6. **Gmail 下書き作成** — `mcp__claude_ai_Gmail__create_draft` を直接呼び出す
7. **（承認後）画像生成** — 5 パターン生成 → Drive 同期

### その他
- ネタ使用後、即座に Sheets の I 列を「使用済み」に更新する
- 画像生成前に必ずユーザー承認を取る
- Drive 同期は `uv run scripts/sync_to_drive.py` で実行

## Verification
- テキスト字数が 140〜300 字の範囲に収まっているか
- P01化スコアリング全 6 項目が 8 点以上か（不合格時は警告を明記）
- ファクトが出典確認済みか（`/check-fact` 通過）
- brand.md の Do Not と矛盾していないか
- Gmail 下書きに `[投稿文]` セクションが含まれているか
- 画像生成時: ファイル名 5 本が揃い、Drive 同期が完了しているか
