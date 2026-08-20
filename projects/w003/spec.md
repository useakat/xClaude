# Production Spec — X ワンポイント解説（W003）

> **共通ルール**：draft ファイルの扱い（`draft.md` を上書きで推敲する・初稿は `draft/first-draft.md` に自動凍結される）は `../CLAUDE.md` を参照。w001/w002/w003 で共通。

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

### フォルダの役割（draft/ と output/ の分担）

- **`draft/`** … 中間生成物を置く。本文の作業ファイル `draft.md`（推敲もこれを直接更新する）、初稿の凍結 `first-draft.md`（Stop hook が自動生成・編集禁止）、**5パターンすべての図解候補**（`infographic_[連番].png`＋プロンプト `infographic_[連番].md`）。**本文の版を `draft_vN.md` として増やさない**（`../CLAUDE.md`「draft ファイルの扱い」参照）。
- **`output/`** … **最終版のみ**を置く。次の3種だけにする：
  1. `index.md`（最終原稿の正本）
  2. `infographic_[連番].png`（採用した最終図解1枚）
  3. `infographic_[連番].md`（その最終図解の生成プロンプト）
- 中間版（`draft.md`・`first-draft.md`・不採用の図解候補）を `output/` に残さない。誤って置いた場合は `draft/` へ移す。

### 下書き原稿

`projects/w003/YYYYMMDD_[topic]/draft/draft.md`（推敲もこのファイルを直接更新する。初稿は `draft/first-draft.md` に自動で凍結される）

### 生成図解

`projects/w003/YYYYMMDD_[topic]/draft/infographic_[連番].png`

* `[連番]` は、01 から始まり、すでに使われている番号の次の番号をつける
* 図解プロンプトの型テンプレートは `projects/w003/infographic_template/`（`step_flow` / `compare_contrast` / `radial` / `timeline` / `pyramid` / `checklist`）に置く。`/visual_infographic` はこれらを基にプロンプトを作成する

### 完成版（output/）

`projects/w003/YYYYMMDD_[topic]/output/index.md`（最終原稿）／`output/infographic_[連番].png`（採用した最終図解）／`output/infographic_[連番].md`（その生成プロンプト）

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
1. **ネタ在庫確認（ハードゲート）** — `onePointNeta` の「未使用」件数を数える。**未使用が 20 件未満なら、必ず補充してからフロー2へ進む（宇宙・物理 7 件 + その他 3 件）。** 「在庫は十分あるから」「補充は重いから」等の理由で**自己判断でスキップ・後回しにしてはならない**。補充は `/research-trivia` で候補を生成し、`onePointNeta` シートに追記する。**追記時は ステータス=「未使用」に加えて、追加日（J列・実行当日 `YYYY-MM-DD`）と分野（K列・宇宙/物理/化学/生物/医学 から1つ）も必ず記入する（空欄にしない）。** 補充完了後にフロー2へ進む。
2. **ネタ選定（ユーザー確認）** — `onePointNeta` の**未使用ネタ**から、**分野を問わず** PE01 に刺さりそうなネタを **5 件**選んでユーザーに提示し、使うネタを選んでもらう（`日 mod 3` の分野グループ分けは廃止）。選定の最優先基準: 読者が今日体験した日常の物・感覚を入り口にできること（＋ brand.md 冒頭フック5軸の直感的比較数字・パワーワードが立てやすいこと）。ユーザーが選んだネタをテーマとして `/research_trivia-source {ネタ}` を実行し、出力されたトリビアネタ候補をユーザーに提示して、使うネタを決めてもらう
3. **テーマフォルダ作成** — `projects/w003/YYYYMMDD_[topic]/`（配下に `draft/` と `output/`）を作成。以降の生成物はこのフォルダに保存する
4. **原稿作成** — 投稿文の作成は `/writer-xpost` スキルに委ねる。フロー2で確定したネタをテーマとして、文字数範囲 200〜260 字を指定して呼び出す：

   ```
   /writer-xpost
   テーマ: {フロー2 で確定したネタ}
   文字数: 200〜260字
   ```

   - `/writer-xpost` は本作業フォルダ（w003）の `spec.md`・`plan.md`・`brand.md` を読み込み、「フォーカス決定→冒頭フック決定→本文作成」を全自動でこなす。
   - `/writer-xpost` の出力（フォーカス候補・冒頭フック候補・投稿内容）のうち、**投稿内容** を原稿として採用する。
   - **保存先は `projects/w003/YYYYMMDD_[topic]/draft/draft.md`**（フロー3で作成したテーマフォルダ配下）。カレントディレクトリに依存しないよう、テーマフォルダのパスを明示して渡すこと。
   - **タイトル案の出力は不要**（図解のタイトルはフロー7で `output/index.md` の冒頭1文を使う）。
   - **呼び出す前に、確定した事実を `draft/fact-table.md` にまとめておく**（brand.md「ファクト表が先、本文が後」）。原典から代表値・極値・測定条件を表にし、断定してよい事実と幅を持たせる事実を分けて記載する。テーマ引数には、この表から必要な数値と「使ってはいけない表現」を明記して渡す。
   - **`/writer-xonepoint` は廃止予定で使わない**（共通スキル `/writer-xpost` に統合）。
5. **ファクトチェック** — `/check-fact-lim <notebook_id> {本文}`（テーマフォルダの `notebook-id.md` の ID を使用。`/research_trivia-source` が作成した notebook のソースのみを根拠にする。notebook-id.md が無い場合のみ `/check-fact` にフォールバック）
5.3. **素朴な読者チェック** — `/check-reader plan.md {本文}`。読者役（PE01）が初見で読み、疑問・誤解した映像・フック未回収を列挙する。疑問に本文中で答える形で改稿し、疑問が出なくなるまで最大3ループ
5.4. **折り返しチェック（ユーザー確認前）** — `/check-reader --fold plan.md {本文}`。読者役（PE01）がタイムラインで実際に見える冒頭280weight分だけを読み、「さらに表示」を押すか通り過ぎるかを判定する。判定が「通り過ぎる」または引きの強さが7以下なら**可視ブロックの終わり方**を書き直し、**最大3ループ**回す。事実は変えず、字数（140〜300字）は維持する。3ループで基準に届かない場合は警告をユーザー提示時に添える。**本文が280weight以内で折り返しが発生しない場合はスキップし、その旨を報告する**
5.6. **知識ある読者チェック** — `/check-critic --field {分野} {本文}`。知識ある読者役が、事実への反論・単純化しすぎ・本文が触れていない前提への疑問・論理の穴を列挙する。各指摘を notebook（`/check-fact-lim` への照会）で裏取りし、事実誤りは修正、本文を強める論点は字数を壊さない範囲で反映する。指摘を裏取りなしで反映しない
6. **ブランド適合チェック** — `/check-brand projects/w003/brand.md {本文}`（採点ループ＋トンマナ調整。brand.md の採点基準で全項目 8 点以上、最大 5 回ループ）
6.5. **よーん役最終検品（ユーザー提示前）** — `/check-yohn {本文}`。よーん本人の過去の修正指摘から蒸留した検品ペルソナ（共通コア＋`persona-yohn_w003.md`。ソースが言っていない因果づけ・極値の代表値化・立場の曖昧な文・淡々とした解説口調に特に厳しい）が、フロー5〜6 を通過した本文を最終検品し、指摘が出なくなるまで改稿する（最大3ループ。疑義は notebook で裏取りしてから反映）。未収束の指摘は以降のユーザー提示に注記して進む（提示はブロックしない）。**フロー8 以降でユーザーから出た新規指摘は check-yohn の見逃しなので、制作が一段落したらペルソナに追記する**（自己改善ループ）
7. **画像生成** — `/lovart` スキル（Lovart AI）で図解を 5 パターン生成し、**ローカルの `draft/` フォルダに保存**する（Drive へのアップロードは行わない）。
   1. **プロンプト作成**: `projects/w003/infographic_template/`（`step_flow` / `compare_contrast` / `radial` / `timeline` / `pyramid` / `checklist`）から**内容に合う 5 型を選び**、各型テンプレートを土台にプロンプトを書く。**タイトルは `output/index.md` の冒頭1文**を使用。**画面内に入れる日本語文字は崩さず正確に**描かせる指示を必ず含める。仕様は PNG・1280×720。
   2. **生成**: `/lovart` で 5 枚生成する。参照したい実機・実物の形状がある場合は、参照画像を `upload` で Lovart CDN に上げ `--attachments` で渡す。修正は同一スレッドで `--thread-id` を指定して反復する。
   3. **保存**: 画像を `draft/infographic_[連番].png`、対応するプロンプトを `draft/infographic_[連番].md` として**ペアで**保存する（連番は 01 から）。
   4. **日本語が崩れる場合**: 文字数を減らすか、生成後にテキストを重ねる。
   - **`/visual_infographic` は使わない**（`scripts/notebooklm_manager.py` の cookie 認証が 2026-08-06 に廃止され、後継のブリッジに `infographic` サブコマンドが未移植のため実行不能。W001 は 8/4、W002 は 8/9 に Lovart へ移行済み）。
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
- ファクトが出典確認済み（`/check-fact-lim` 通過。notebook 無し時のみ `/check-fact`）
- `/check-reader`（素朴な読者）の疑問が解消されている
- `/check-reader --fold`（折り返し）で判定が「押す」・引きの強さ8以上になり、可視ブロックに答えのない問いが1つ以上残っている（280weight以内でスキップした場合はその旨を明記／未収束時は警告を明記）
- `/check-critic`（知識ある読者）の指摘が裏取り済みで反映・取捨が済んでいる
- `/check-yohn`（よーん役最終検品）を通過している（未収束の指摘があれば提示時に注記済み）
- brand.mdと矛盾しない
- plan.mdの目的に沿う
- 出力ファイル名が揃っている
- Gmail 下書きの本文が `[投稿文]`〜`[/投稿文]` の**開き・閉じ両タグ**で囲まれている（`python3 scripts/extract_tag.py 投稿文` で非空抽出できる）
- チャット履歴 `chat_history.md` が投稿フォルダに保存されている
- 投稿フォルダが Drive (xClaude/projects/w003) にアップロード済み
- **`output/` に最終版以外のファイルが無い**（`index.md`＋採用図解 `infographic_[連番].png`＋その `infographic_[連番].md` の3種のみ。中間版 `draft.md`・`first-draft.md`・不採用図解は `draft/` にある）
