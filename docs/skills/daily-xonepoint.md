---
title: daily-xonepoint
description: "【非推奨】Xのワンポイント解説投稿の制作フロー。現在は projects/w003/spec.md を正として直接実行するため、このスキルは基本的に使わない。"
category: 廃止・非推奨
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

【非推奨】Xのワンポイント解説投稿の制作フロー。現在は projects/w003/spec.md を正として直接実行するため、このスキルは基本的に使わない。

## 詳細内容

# daily-xonepoint（非推奨）

> **このスキルは非推奨です。基本的に使わないこと。** W003 のワンポイント解説制作は `projects/w003/spec.md` の制作フローを正として直接（対話で）実行する。spec.md と本スキルが二重管理になり、ステップ順・ツール指定（例: Gmail 添付）の不整合が生じやすいため、spec.md に一本化した。制作時は W003 の `CLAUDE.md` の指示どおり `spec.md` を Read して進めること。以下は参考用に残す旧フロー。

あなたはXのワンポイント科学解説投稿を制作するエージェントです。
**以下のSTEPを順番に実行してください。ただし STEP 2（ネタ選択）・STEP 6（画像生成）・STEP 7（最終確定）は必ずユーザーの確認・承認を待つ。それ以外のSTEPは完了したら直ちに次へ進む。**

> このフローは `projects/w003/spec.md` の制作フローに対応する（対話実行）。spec.md を正とし、齟齬があれば spec.md を優先する。

# STEP 1: ネタ在庫確認

以下を呼び出して未使用ネタ数を確認する：

```
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="onePointNeta!A:Z")
```

取得した行の I列（ステータス）が「未使用」の件数をカウントする。

未使用が **10件未満** の場合は、次のSTEPの前にSTEP 1aを実行する。

## STEP 1a: ネタ補充（在庫10件未満のときのみ）

以下の手順でネタを10件収集し、`database/onePointNeta.csv` に追記する。

1. 既存ネタ一覧を取得して重複を避ける：
   ```
   sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="onePointNeta!A:Z")
   ```

2. WebSearchで以下を検索し、**宇宙・物理 7件・その他 3件 計10件**収集する：
   - 宇宙・物理（7件）：「宇宙 驚き 事実」「physics surprising facts」「quantum mechanics trivia」「素粒子 面白い事実」
   - その他科学（3件）：「生物 驚き 事実」「chemistry surprising facts」「biology trivia」「医学 驚き 事実」

3. 以下の条件をすべて満たすネタのみ採用する：
   - 常識をひっくり返す意外性がある
   - 科学的に正確（出典確認できる）
   - 150〜200字でまとめられる
   - **【最優先】読者が今日すでに体験した可能性がある日常の物・感覚（雨・食事・呼吸・空・水・夜空・通勤・コーヒー等）を冒頭の入り口にできる**

**優先度低（避ける）**：「宇宙空間での出来事」「他の惑星固有の現象」など読者の日常から遠い設定が入り口のネタ。日常接続が末尾1文だけになりやすく、インプレッションが伸びにくい（実データで確認済み）。

4. 採用ネタを以下で保存する（10件分実行）。No は既存の最大 No + 1 から連番で採番する：
   - 宇宙・物理カテゴリのネタは 分野 = `宇宙` または `物理` を設定する
   - その他カテゴリのネタは内容に応じて 分野 = `生物` / `医学` / `化学` / `その他` を設定する
   ```
   sheets_append_values(
     spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM",
     range="onePointNeta!A:A",
     values=[[No, テーマ, 冒頭1行案, 身近さ接続, 仕組みのポイント, 感情的締め案, 難易度, 出典メモ, "未使用", YYYY-MM-DD, 分野]]
   )
   ```

---

# STEP 2: ネタ選定

以下を呼び出して全ネタを取得し、I列（ステータス）が「未使用」の行のみを抽出する：

```
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="onePointNeta!A:K")
```

### 分野カテゴリによる選定（2:1 比率）

K列（分野）の値を参照して未使用ネタを2グループに分類する：
- **宇宙・物理グループ**：K列が「宇宙」または「物理」
- **その他グループ**：K列が「生物」「医学」「化学」「その他」（またはK列が空欄）

今日の日付の「日」を取得し、`日 mod 3` で使用グループを決定する：

```bash
TZ=Asia/Tokyo date '+%d'
```

- `0` または `1` → 宇宙・物理グループから選ぶ
- `2` → その他グループから選ぶ

該当グループに未使用ネタがない場合は、もう一方のグループから選ぶ。

### グループ内の選定基準

決定したグループの未使用ネタから、以下の観点でXのインプレッションが取れそうな**シードネタ**を1つ選ぶ（このシードを起点に次の Deep Research を行う）：

- **【最優先】読者が今日すでに体験した可能性がある日常の物・感覚を入り口にできる**（雨・食事・呼吸・空・水・夜空・通勤・コーヒーなど）
- 直感を裏切る意外性がある
- 身近なものと宇宙・科学がつながる
- 一行で「えっ？」と思わせられる
- 難易度が易〜中（難しすぎると伝わらない）

**優先度低（避ける）**：「宇宙空間での出来事」「他の惑星固有の現象」など読者の日常から遠い設定が入り口のネタ。日常接続が末尾1文だけになりやすく、インプレッションが伸びにくい（実データで確認済み）。

### Deep Research でネタ候補を展開する

選んだシードネタをテーマとして `/research_trivia-source {シードネタのテーマ}` を実行する。
NotebookLM の Deep Research で信頼できるソースを収集し、トリビアネタ候補 3〜5 個（タイトル・選定理由・出典）が返る。

### ユーザーに候補を提示して選択を待つ（**必ず停止する**）

`/research_trivia-source` が返したネタ候補一覧をそのままユーザーに提示し、**どのネタで投稿を作るかを尋ねる**。
**ユーザーが選択するまで次のSTEPに進まない。** 候補が薄い／選び直したい場合は再実行や別シードを提案する。

### 選択確定後の処理

ユーザーが選んだネタを **【テーマ】** として記憶する（このテーマを以降のステップで使う。出典は STEP 5 のファクトチェックの根拠に使える）。
そのうえでシードネタのステータスを「使用済み」に更新する。sheets_get_values の結果から No に対応する行番号 R を特定し、以下を呼び出す：

```
sheets_update_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="onePointNeta!I{R}", values=[["使用済み"]])
```

以下を記憶して STEP 3 へ進む：
- **【ネタNo】**（シードネタの No。数値のみ）
- **【テーマ】**（ユーザーが選んだトリビアネタ）

---

# STEP 3: テーマフォルダ作成

【テーマ】から短い topic スラッグを決め、作業フォルダを作成する。

```bash
ROOT=$(git rev-parse --show-toplevel)
DATE=$(TZ=Asia/Tokyo date '+%Y%m%d')
TOPIC="{テーマから決めた短いスラッグ}"   # 例: muon_lifetime
DIR="$ROOT/projects/w003/${DATE}_${TOPIC}"
mkdir -p "$DIR/draft" "$DIR/output"
echo "$DIR"
```

作成した `${DATE}_${TOPIC}` フォルダパスを記憶し、以降の生成物（draft / output / 画像）はこのフォルダ配下に保存する。

---

# STEP 4: 投稿原稿作成

`/writer-xonepoint` スキルを **テーマのみ**を引数として呼び出す：

```
テーマ: {STEP 2 で記憶した【テーマ】}
```

返却された以下の2つを記憶する：
- **【タイトル案】**: タイトル候補10件
- **【本文】**: 投稿原稿

【本文】を STEP 3 で作成したフォルダの `draft/draft.md` に保存する（既存があれば `_vX` を付与）。

（ネタの「使用済み」更新は STEP 2 で完了している）

---

# STEP 5: 品質チェック & トンマナ調整

## 5-1: ファクトチェック

STEP 4で出力した【本文】に対して、/check-fact スキルを実行する。

- /check-fact が「チェック完了」を報告するまで、結果を確認する
- チェック完了後、check-fact の「最終修正案」を記憶する
- check-fact の出力から **【チェックサマリー】**（「チェックサマリー」の見出し以降のテーブル）を抽出して記憶する

## 5-2: ブランド適合チェック（採点＋トンマナ調整）

5-1 で確定した「最終修正案」を本文として、引数の**先頭に `projects/w003/brand.md` を付けて** `/check-brand` スキルを呼び出す。

```
引数: projects/w003/brand.md {最終修正案の本文}
```

check-brand は brand.md の「採点基準」で全項目8点以上になるまで書き直し（採点ループ）、合格本文をトンマナ調整する（事実は変更しない）。

返却された以下を記憶する：
- **【最終原稿】**: 採点合格 → トンマナ調整済みの本文
- **【スコアサマリー】**: check-brand が返したスコアサマリーテーブル（ブランド適合-各項目／ブランド適合-合計）
- **【トンマナサマリー】**: check-brand が返したトンマナ調整1行

【最終原稿】を STEP 3 で作成したフォルダの `output/draft.md` に保存する（既存があれば `_vX` を付与）。

### 5-2-1: チェックサマリーへの記録

【チェックサマリー】の末尾に、check-brand が返した【スコアサマリー】の各行（ブランド適合-各項目／ブランド適合-合計）と【トンマナサマリー】1行を追記して記憶し直す。
check-brand が **不合格（警告）** を返した場合は、メール本文の冒頭にも警告行を入れる：

```
⚠️ ブランド適合チェック不合格（最高得点版を採用しました。人手レビュー推奨）
```

**STEP 5 完了後、直ちに STEP 6（画像生成）へ進む（ここではユーザー入力を待たない）**

---

# STEP 6: 画像生成（ユーザー承認後・**必ず停止する**）

1. STEP 5 で確定した【最終原稿】（投稿テキスト）をユーザーに提示し、**画像を生成してよいか承認を求める**。
   **ユーザーが承認するまで画像生成しない。** 修正指示があれば反映してから再提示する。
2. 承認後、`/visual_infographic` でインフォグラフィック画像を **5パターン**生成する。
3. 生成画像を STEP 3 で作成したフォルダの `draft/infographic_[連番].png` に保存する。
   - `[連番]` は 01 から始め、既に使われている番号の次を付ける（spec.md の Naming 準拠）。

> **画像は git にコミットしない。** 投稿フォルダ内の画像（`draft/`・`output/` の `*.png`）は `.gitignore` の `/projects/w003/**/*.png` で除外されている。画像はローカルと STEP 10 の Drive アップロード（`xClaude/projects/w003`）で保存し、git にはテキスト（`*.md`）のみ残す。誤って `git add -A` 等で index に入った場合は `git rm --cached <png>` で外す。

---

# STEP 7: 最終確定（ユーザー承認・**必ず停止する**）

> 投稿テキストと画像がすべて出そろった段階で、**完成として確定してよいか**をユーザーに確認する。以降の保存・Drive アップロード・Gmail 下書きは、この承認後に **確定版** に対してのみ行う。

1. 最新の確定テキスト（`output/index.md` を正とする）と生成画像をユーザーに提示し、「**この内容で完成・確定してよいか**」を尋ねる。
2. **ユーザーが明示承認するまで STEP 8 以降に進まない。** 修正指示があれば反映し、テーマフォルダ（`output/index.md` ／必要なら画像）を再保存してから再提示する。
3. 承認が得られたら、その時点の `output/index.md` を **【確定版】** として以降のステップで使う。

---

# STEP 8: メール下書き作成（最終承認後・**1回だけ**）

> Gmail 下書きは、STEP 7 で完成確定の承認を得た **【確定版】** に対して **1回だけ** 作成する。`create_draft` は更新・削除ができないため、確定前に作ると修正のたびに下書きが増える。**STEP 7 の承認前は絶対に作成しない。**

STEP 4・STEP 5 で記憶した【タイトル案】【チェックサマリー】と、STEP 7 で確定した【確定版】本文を使用して、**画像を添付した** Gmail 下書きを作成する。

> **画像添付があるため `mcp__claude_ai_Gmail__create_draft` は使わない**（添付非対応）。`bash scripts/create_gmail_draft.sh --attach <png>` を使う（gws CLI 経由・複数 `--attach` 可）。

1. 以下の形式で本文を組み立て、一時ファイル（例 `/tmp/xonepoint_mail.txt`）に Write で書き出す：
   ```
   [ネタID]onePointNeta[{STEP 2 で記憶した【ネタNo】の値}][/ネタID]

   [チェックサマリー]

   （STEP 5 で記憶したチェックサマリーテーブル）

   [/チェックサマリー]

   [最終原稿]

   （STEP 7 で確定した【確定版】）

   [/最終原稿]

   [投稿文]

   （STEP 7 で確定した【確定版】）

   [/投稿文]
   ```

2. 【確定版】の内容から **10〜15字以内** の短いトピック要約を生成する：
   - 「ネタの核心キーワード＋ポイント」を名詞句で表現する
   - 例: 「ミューオン 寿命の伸び」「光速 水の中で遅くなる」「電子 2重スリット」
   - 記号・助詞は最小限に。スペース区切りで2〜3語に収める

3. 日時を JST（UTC+9）で取得する：
   ```bash
   TZ=Asia/Tokyo date '+%Y%m%d %H:%M:%S'
   ```

4. `create_gmail_draft.sh` を呼び出す（**STEP 7 承認後に1回だけ**）。添付は完成画像（採用した型の `output/infographic_[連番].png`）：
   ```bash
   bash scripts/create_gmail_draft.sh \
     --to useakat@gmail.com \
     --subject "【ワンポイント解説】{短いトピック要約} YYYYMMDD HH:MM:SS" \
     --body-file /tmp/xonepoint_mail.txt \
     --attach projects/w003/YYYYMMDD_[topic]/output/infographic_[連番].png
   ```

## 実行ルール

- **`bash scripts/create_gmail_draft.sh --attach <png>` を使用する**（MCP の `create_draft` は添付非対応のため使わない）
- **STEP 7 の承認前は絶対に作成しない。承認後に作成するのは1回だけ。**
- **成功判定は `✓ 下書き作成完了` の出力で行う**（gws の戻り JSON 構造により id が空表示になる場合があるため、必要なら `mcp__claude_ai_Gmail__list_drafts`（`query: "subject:… has:attachment"`）で添付付き下書きの存在を確認する）
- **失敗した場合は、エラー内容をそのまま報告する**

---

# STEP 9: チャット履歴を保存

このセッションのやり取りを Markdown 化し、STEP 3 のテーマフォルダ直下に `chat_history.md` として保存する（次の STEP 10 で Drive にも一緒に保存される）。

```bash
OUT=$(python3 scripts/save_session_history.py --title "{topic}" --slug "{slug}" 2>&1 | tail -1)
cp "$OUT" "projects/w003/YYYYMMDD_[topic]/chat_history.md"
```

---

# STEP 10: 投稿フォルダを Drive へアップロード

メール下書き作成・チャット履歴保存まで終わった STEP 3 のテーマフォルダを、丸ごと Drive `xClaude/projects/w003` 配下にアップロードする（draft 画像・chat_history.md 含む・フォルダ構造を再現）。

```bash
bash scripts/drive_put_folder.sh "projects/w003/YYYYMMDD_[topic]" 1DTPEzOmWd-kWQElyBByuVHjSantTl7-g
```

---

# 完了判定

すべてのSTEP（1〜10）が完了したら、以下を報告する：

- ✅ ネタ選定完了（シードネタNo.X / 採用テーマ: 〜）
- ✅ ネタを「使用済み」に更新完了
- ✅ テーマフォルダ作成完了（projects/w003/YYYYMMDD_topic/）
- ✅ 原稿作成完了（draft/draft.md・output/draft.md 保存）
- ✅ 品質チェック完了
- ✅ 画像生成完了（5パターン / draft/infographic_*.png）
- ✅ 最終確定の承認取得（STEP 7）
- ✅ メール下書き作成完了（最終承認後・draft ID: xxxxxx）
- ✅ チャット履歴保存完了（chat_history.md）
- ✅ Drive アップロード完了（xClaude/projects/w003/YYYYMMDD_topic/）

**STEP 2（ネタ選択）・STEP 6（画像承認）・STEP 7（最終確定）では必ずユーザーの応答を待つ。それ以外は自動で進める。**
