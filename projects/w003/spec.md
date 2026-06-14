# Production Spec — X ワンポイント解説（W003）

## Media (生成する媒体)
- X 投稿テキスト
- インフォグラフィック画像 5パターン（ユーザー承認後に生成）

## Input (読み込むファイル)
- `../../plan.md`
- `../../brand.md`（共通ブランド定義）
- `plan.md`（本プロジェクトの目的・ターゲット）
- `brand.md`（本プロジェクトの表現ルール）
- Google Sheets `onePointNeta`（spreadSheet ID: `1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM`）— ネタ在庫

## Output (保存先)
- **投稿テキスト**: Gmail (useakat@gmail.com) 下書き + `projects/w003/outputs/YYYYMMDD_[topic]/draft.md`
- **画像**: `projects/w003/outputs/YYYYMMDD_[topic]/[style].png`

## Format
- **テキスト**: 常体（だ／のだ調）、4 段構成（brand.md 参照）、改行・空白行で段落を分ける、200〜260 字推奨（最大 300 字 / 下限 140 字）
- **画像**: PNG、日本語テキスト埋め込み、1280×720

## Naming

### 投稿フォルダ

`projects/w003/outputs/YYYYMMDD_[topic]/`（例: `20260602_陸のタイド/`）

### テキスト原稿

`draft.md`（フォルダ内固定名）

### 画像

`[style].png`（例: `bento-grid.png`, `sketch-note.png`, `scientific.png`）

### Gmail 下書き

件名: `【ワンポイント解説】{トピック要約 10〜15 字} YYYYMMDD HH:MM:SS`

## Rules

### 制作フロー（`/daily-xonepoint` が自動実行）
1. **ネタ在庫確認** — 未使用 10 件未満なら補充（宇宙・物理 7 件 + その他 3 件）
2. **ネタ選定** — `日 mod 3` で分野グループ（0・1 → 宇宙・物理 / 2 → その他）を決定。最優先基準: 読者が今日体験した日常の物・感覚を入り口にできること
3. **原稿作成** — `/writer-xonepoint`
4. **ファクトチェック** — `/check-fact`
5. **ブランド適合チェック** — `/check-brand projects/w003/brand.md {本文}`（採点ループ＋トンマナ調整。brand.md の採点基準で全項目 8 点以上、最大 5 回ループ）
6. **Gmail 下書き作成** — `mcp__claude_ai_Gmail__create_draft` を直接呼び出す
7. **（承認後）画像生成** — `/visual_infographic` 5 パターン生成 → `projects/w003/outputs/YYYYMMDD_[topic]/[style].png` に保存（Drive にもアップロード）

### その他
- ネタ使用後、即座に Sheets の I 列を「使用済み」に更新する
- 画像生成前に必ず投稿テキストをユーザーに確認してもらい、承認を取る

## Verification
- テキスト字数が 140〜300 字の範囲に収まっている
- ブランド適合スコアリング（`/check-brand`）の全項目が 8 点以上（不合格時は警告を明記）
- ファクトが出典確認済み（`/check-fact` 通過）
- brand.mdと矛盾しない
- plan.mdの目的に沿う
- 出力ファイル名が揃っている
- Gmail 下書きに `[投稿文]` セクションが含まれている
