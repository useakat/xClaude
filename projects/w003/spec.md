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
`projects/w003/YYYYMMDD_[topic]/draft`　（下書き)
`projects/w003/YYYYMMDD_[topic]/output` (完成原稿)

## Format
- **テキスト**: 常体（だ／のだ調）、4 段構成（brand.md 参照）、改行・空白行で段落を分ける、200〜260 字推奨（最大 300 字 / 下限 140 字）
- **画像**: PNG、日本語テキスト埋め込み、1280×720

## Naming

### 下書き原稿

`projects/w003/YYYYMMDD_[topic]/draft/draft.md`

### 生成図解

`projects/w003/YYYYMMDD_[topic]/draft/infographic_[連番].png`

* `[連番]` は、01 から始まり、すでに使われている番号の次の番号をつける
* 図解プロンプトの型テンプレートは `projects/w003/infographic_template/`（`step_flow` / `compare_contrast` / `radial` / `timeline` / `pyramid` / `checklist`）に置く。`/visual_infographic` はこれらを基にプロンプトを作成する

### Gmail 下書き

件名: `【ワンポイント解説】{トピック要約 10〜15 字} YYYYMMDD HH:MM:SS`

## Rules

### 制作フロー（`/daily-xonepoint` が自動実行）
1. **ネタ在庫確認** — 未使用 10 件未満なら補充（宇宙・物理 7 件 + その他 3 件）
2. **ネタ選定** — `日 mod 3` で分野グループ（0・1 → 宇宙・物理 / 2 → その他）を決定。最優先基準: 読者が今日体験した日常の物・感覚を入り口にできること。選んだネタをテーマとして `/research_trivia-source {ネタ}` を実行し、出力されたトリビアネタ候補をユーザーに提示して、使うネタを決めてもらう
3. **テーマフォルダ作成** — `projects/w003/YYYYMMDD_[topic]/`（配下に `draft/` と `output/`）を作成。以降の生成物はこのフォルダに保存する
4. **原稿作成** — `/writer-xonepoint`
5. **ファクトチェック** — `/check-fact`
6. **ブランド適合チェック** — `/check-brand projects/w003/brand.md {本文}`（採点ループ＋トンマナ調整。brand.md の採点基準で全項目 8 点以上、最大 5 回ループ）
7. **画像生成** — `/visual_infographic` 5 パターン生成 → **ローカルの `draft/` フォルダに保存**（Drive へのアップロードは行わない）。**タイトルは `output/index.md` の冒頭1文**を使用。各プロンプトは **`projects/w003/infographic_template/` の型テンプレートを基に作成**（内容に合う 5 型を選択）
8. **Gmail 下書き作成** — `mcp__claude_ai_Gmail__create_draft` を直接呼び出す

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
