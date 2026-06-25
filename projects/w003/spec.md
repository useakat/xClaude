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

本文フォーマット（`daily-xonepoint` SKILL STEP 6 と同一。**`[投稿文]` は必ず `[/投稿文]` の閉じタグまで含める**。`scripts/extract_tag.py` が開き・閉じの間を抽出するため、閉じタグが無いと cron 投稿フローで本文が空とみなされ投稿されない）:

```
[ネタID]onePointNeta[{ネタNo}][/ネタID]

[チェックサマリー]

（チェックサマリーテーブル）

[/チェックサマリー]

[最終原稿]

（最終原稿）

[/最終原稿]

[投稿文]

（投稿テキスト）

[/投稿文]
```

作成手段: 画像を添付する場合は `mcp__claude_ai_Gmail__create_draft`（添付非対応）ではなく `bash scripts/create_gmail_draft.sh --attach <png>` を使う。

## Rules

### 制作フロー（この spec.md を正として対話で実行する。`/daily-xonepoint` スキルは非推奨で使わない）
1. **ネタ在庫確認** — 未使用 10 件未満なら補充（宇宙・物理 7 件 + その他 3 件）
2. **ネタ選定** — `日 mod 3` で分野グループ（0・1 → 宇宙・物理 / 2 → その他）を決定。最優先基準: 読者が今日体験した日常の物・感覚を入り口にできること。選んだネタをテーマとして `/research_trivia-source {ネタ}` を実行し、出力されたトリビアネタ候補をユーザーに提示して、使うネタを決めてもらう
3. **テーマフォルダ作成** — `projects/w003/YYYYMMDD_[topic]/`（配下に `draft/` と `output/`）を作成。以降の生成物はこのフォルダに保存する
4. **原稿作成** — `/writer-xonepoint`
5. **ファクトチェック** — `/check-fact`
6. **ブランド適合チェック** — `/check-brand projects/w003/brand.md {本文}`（採点ループ＋トンマナ調整。brand.md の採点基準で全項目 8 点以上、最大 5 回ループ）
7. **画像生成** — `/visual_infographic` 5 パターン生成 → **ローカルの `draft/` フォルダに保存**（Drive へのアップロードは行わない）。**タイトルは `output/index.md` の冒頭1文**を使用。各プロンプトは **`projects/w003/infographic_template/` の型テンプレートを基に作成**（内容に合う 5 型を選択）
8. **最終確定（ユーザー承認）** — 投稿テキストと画像が出そろったら、最新の確定版（`output/index.md`）と画像を提示し「**この内容で完成・確定してよいか**」を確認する。**承認まで以降に進まない。** 修正は反映・再保存して再提示する
9. **Gmail 下書き作成** — **フロー 8 の最終確定の承認後に、確定版で 1 回だけ**作成する。上記「Gmail 下書き」の本文フォーマット（**`[投稿文]`〜`[/投稿文]` の閉じタグまで必須**）。画像添付があるため `bash scripts/create_gmail_draft.sh --attach output/infographic.png` を使う
10. **チャット履歴を保存** — このセッションのやり取りを `bash scripts/save_session_history.py --title "{topic}" --slug "{slug}"` で Markdown 化し、生成物をテーマフォルダ直下に `chat_history.md` としてコピー保存する（投稿フォルダに同梱し、次の Drive アップロードで一緒に保存する）
11. **投稿フォルダを Drive へアップロード** — テーマフォルダ `projects/w003/YYYYMMDD_[topic]/` を丸ごと `bash scripts/drive_put_folder.sh projects/w003/YYYYMMDD_[topic] 1DTPEzOmWd-kWQElyBByuVHjSantTl7-g` で Drive `xClaude/projects/w003` 配下にアップロードする（draft 画像含む・フォルダ構造を再現）

### その他
- ネタ使用後、即座に Sheets の I 列を「使用済み」に更新する
- 画像生成前に必ず投稿テキストをユーザーに確認してもらい、承認を取る
- **Gmail 下書きは、投稿テキストと画像が完全に確定し、ユーザーが最終承認（フロー 8）してから 1 回だけ作成する**（承認前に作らない。`create_draft` は更新・削除不可のため、確定前に作ると修正のたびに下書きが増える）
- **投稿フォルダ内の画像（`draft/`・`output/` の `*.png`）は git にコミットしない**。`.gitignore` の `/projects/w003/**/*.png` で除外し、画像はローカルと Drive（フロー 11 のアップロード先 `xClaude/projects/w003`）に保存する。リポジトリにはテキスト（`*.md`）のみを残す（容量肥大を防ぐため）

## Verification
- テキスト字数が 140〜300 字の範囲に収まっている
- ブランド適合スコアリング（`/check-brand`）の全項目が 8 点以上（不合格時は警告を明記）
- ファクトが出典確認済み（`/check-fact` 通過）
- brand.mdと矛盾しない
- plan.mdの目的に沿う
- 出力ファイル名が揃っている
- Gmail 下書きの本文が `[投稿文]`〜`[/投稿文]` の**開き・閉じ両タグ**で囲まれている（`python3 scripts/extract_tag.py 投稿文` で非空抽出できる）
- チャット履歴 `chat_history.md` が投稿フォルダに保存されている
- 投稿フォルダが Drive (xClaude/projects/w003) にアップロード済み
