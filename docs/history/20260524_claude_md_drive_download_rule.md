---
title: CLAUDE.md：Drive ファイルダウンロードのスクリプト使い分けルール追加 — セッション履歴
date: 2026-05-24
sidebar:
  hidden: true
---

# セッション履歴

> 2026-05-24 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260524_claude_md_drive_download_rule/)

---

## よーん *(16:33 JST)*

ファイルのダウンロードは drive_get.py 使って

# visual_infographic

文章を渡すと、N パターンの図解プロンプトを自動生成し、NotebookLM Infographics で図解画像を N 枚作成して Google Drive の outputs/images フォルダに保存する。
画像 N 枚 + 対応するプロンプト markdown N つ（計 2N ファイル）をアップロードする。

## 引数

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `count` | `3` | 生成する枚数。例：`/visual_infographic 5` で5枚生成 |

## 入力

- **テキスト直接渡し**: ユーザーがチャットにテキストを貼り付けた場合
- **ファイルパス指定**: `--file /path/to/file.md` など

`
実は、寿命がたった「45万分の1秒」の粒子が、今日も空から僕らを貫いている。


それは、ミューオンという素粒子。

宇宙から飛んできた高エネルギー粒子（宇宙線）が大気にぶつかると、上空10〜15kmあたりで生まれる。


でも寿命は短く、光速で飛んでも約660mしか進めない。普通なら地表には届かない。


では、なぜ届くのか？


鍵は「時間の遅れ」。


地上の僕らから見ると、光速に近い爆速で飛ぶミューオンの時計はゆっくり進む。

だから寿命が尽きるまでの時間が引き延ばされ、その間に地表に到達できる。


今日も空から、時間の不思議を秘めたミューオンが、僕らの頭上に降り注いでいる。` の先頭が整数の場合はそれを count として読み取る。それ以外はすべてテキストとして扱う。

## 実行手順

### Step 0. 認証確認（初回のみ）

以下のどちらかが存在するか確認する：
- `~/.notebooklm/storage_state.json`
- `/root/xClaude/gcp/notebooklm_storage_state.json`

**どちらも存在しない場合**、Drive MCP ツールで自動取得する：

1. `mcp__claude_ai_Google_Drive__search_files` で `notebooklm_storage_state.json` を検索
2. ヒットしたファイルの ID を取得
3. `mcp__claude_ai_Google_Drive__read_file_content` でファイル内容（JSON テキスト）を取得
4. Write ツールで `/root/xClaude/gcp/notebooklm_storage_state.json` に書き込む

Drive に該当ファイルがない場合はスキル実行を中断し、ユーザーに以下をローカルで実行するよう案内する：
```
bash scripts/notebooklm_auth_push.sh
```

### Step 1. テキスト取得・count 確認

- `
実は、寿命がたった「45万分の1秒」の粒子が、今日も空から僕らを貫いている。


それは、ミューオンという素粒子。

宇宙から飛んできた高エネルギー粒子（宇宙線）が大気にぶつかると、上空10〜15kmあたりで生まれる。


でも寿命は短く、光速で飛んでも約660mしか進めない。普通なら地表には届かない。


では、なぜ届くのか？


鍵は「時間の遅れ」。


地上の僕らから見ると、光速に近い爆速で飛ぶミューオンの時計はゆっくり進む。

だから寿命が尽きるまでの時間が引き延ばされ、その間に地表に到達できる。


今日も空から、時間の不思議を秘めたミューオンが、僕らの頭上に降り注いでいる。` から count を読み取る（先頭が整数ならその値、なければデフォルト 3）
- テキストを `/tmp/infographic_source.txt` に書き出す
  - 直接渡しの場合: そのまま書き出す
  - ファイルパス指定の場合: `Read` ツールで内容を確認してから書き出す

### Step 2. メインタイトル・サブタイトルを決める

**メインタイトルの決定ルール**:
- テキストが「実は、」で始まる場合 → 冒頭の1文（句点「。」は除く）をそのままメインタイトルにする
- それ以外 → テキストのテーマを表す短いキャッチーなタイトル（15字以内）を生成する

**サブタイトルの決定ルール**:
- 内容の概要を説明する一文
- 「〜を解説します」という形は禁止。内容を端的に述べる形にする

### Step 3. count 個のプロンプトを生成

テキストの内容・構造に最適な図解レイアウトを判断し、count 個の異なるパターンを考える。
パターンタイプは固定せず、内容に応じて選ぶ。参考例：
- ステップ・フロー型（プロセスや変化を時系列で表現）
- 比較・対比型（Before/After、2つの概念の対比）
- 中心放射型（コアコンセプトを中央に、関連要素を周囲に）
- タイムライン型（歴史的経緯や時代の流れ）
- ピラミッド型（重要度の階層構造）
- チェックリスト型（箇条書きで要点を列挙）
など

各パターンで以下のテンプレートを完成させる：

```
# テーマ・全体像
* メインタイトル：[メインタイトル]
* サブタイトル（概要）：[サブタイトル]

# ビジュアル・レイアウトの指示
* 背景：白または非常に薄いオフホワイトなどの無地を基調とし、手書きの線や色が際立つシンプルな背景にしてください。
* カラー：黒のペン画の輪郭線に、淡い水彩やマーカーのような優しい色合い（オレンジ、黄色、水色など）でアクセントをつけてください。
* テキスト描写の厳守：画像内のテキストはAI側で勝手に要約や言い換えを行わず、指定した文字を一言一句違わず正確に書き込んでください。
* タイトル：上部に大きく配置し、背面にマーカーで引いたような帯を入れて強調してください。
* サブタイトル：タイトル下部に、タイトルより小さい文字で書いて配置してください。
* テキスト: 結論や印象的なフレーズには「吹き出し」を使って強調してください。
* キャラクター指定：キャラクターとして、スーパーニャンコ（額に赤いハート、卒業帽をかぶり、赤いマントをつけた青いネコのキャラクター）を含めてください。白人間（輪郭だけを描いた白一色の人間の絵）の使用は禁止します。
* 装飾：

# 図解の構成・レイアウト
[パターンごとの具体的な構成・レイアウト指示を記述]
```

### Step 4. プロンプト markdown を count 個のファイルに保存

ファイル名: `outputs/infographic_YYYY-MM-DD_1.md` ～ `outputs/infographic_YYYY-MM-DD_N.md`

各ファイルの構成：
```markdown
パターン: [パターン名]

[そのパターンのプロンプト全文]
```

### Step 5. count 枚のインフォグラフィックを生成（1 notebook）

**1枚目**: `make-infographic --keep` で notebook を作成しながら生成。notebook_id を出力からパースする。

```bash
ROOT=$(git rev-parse --show-toplevel)
DATE=$(date +%Y-%m-%d)

OUTPUT=$(python3 "$ROOT/scripts/notebooklm_manager.py" make-infographic \
  --file /tmp/infographic_source.txt \
  --title "図解_${DATE}" \
  --infographic-title "[メインタイトル]" \
  --instructions "[パターン1のプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$ROOT/outputs/infographic_${DATE}_1.png" \
  --keep 2>&1)
echo "$OUTPUT"
NOTEBOOK_ID=$(echo "$OUTPUT" | grep "ノートブック作成" | sed 's/.*: //')
```

**2枚目以降（i = 2 ～ count）**: 同じ notebook_id を使って生成。各パターンのプロンプトを渡す。

```bash
# i 枚目（i = 2 ～ count を繰り返す）
python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
  --instructions "[パターンiのプロンプト全文]" \
  --language ja --orientation landscape --detail standard --style sketch-note \
  --output "$ROOT/outputs/infographic_${DATE}_i.png"
```

**`--instructions` が長い場合**: 一時ファイルに書き出して `"$(cat /tmp/prompt_N.txt)"` で渡す。

### Step 6. Google Drive にアップロード

フォルダ ID: `1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb`（outputs/images）

**ローカル環境**（gws が使える場合）:
```bash
cd "$ROOT/outputs"
for N in $(seq 1 COUNT); do
  gws drive +upload "infographic_${DATE}_${N}.png" --parent 1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb
  gws drive +upload "infographic_${DATE}_${N}.md"  --parent 1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb
done
```

**リモート環境**（gws がない場合）:
Drive MCP ツールを使ってアップロードする：
- `mcp__claude_ai_Google_Drive__create_file` で各ファイルをアップロード（parent: `1iAz0cWYNeLXSUk88Gc1o3986xGSseAKb`）

各ファイルのアップロード結果（Drive URL）を表示する。

### Step 7. ローカルファイルを削除

アップロード成功を確認してから全ファイルを削除する。

```bash
for N in $(seq 1 COUNT); do
  rm "$ROOT/outputs/infographic_${DATE}_${N}.png"
  rm "$ROOT/outputs/infographic_${DATE}_${N}.md"
done
```

エラーが出た場合は削除せずユーザーに報告する。

## 完了後の報告

- 生成した画像の Drive URL（count 枚分）
- プロンプト markdown の Drive URL（count 個分）
- 作成された NotebookLM notebook のタイトルと ID

## 注意事項

- notebook は1つ作成される（`--keep` で保持）
- 画像生成は1枚あたり数分かかる場合がある
- gws がない環境（リモート）では Drive MCP ツールを使用する

### Claude *(15:37 JST)*

`/visual_infographic` スキルを実行します。まず認証ファイルの確認とソーステキストの書き出しを並行して行います。

*[ツール: `Bash`, `Write`]*

認証ファイルを確認しました。次に3パターンのプロンプトを生成して保存します。

**メインタイトル**: 実は、寿命がたった「45万分の1秒」の粒子が、今日も空から僕らを貫いている  
**サブタイトル**: ミューオンが「時間の遅れ」で地球に届くまでの物語

*[ツール: `Write`, `Write`, `Write`]*

3パターンのプロンプトを保存しました。NotebookLM で1枚目の画像を生成します（`--keep` で notebook を保持）。

*[ツール: `Bash`, `Bash`]*

認証エラーが発生しました。NotebookLM が「location=unsupported」にリダイレクトされており、現在の実行環境（IPアドレス/リージョン）からのアクセスがブロックされているようです。

セッションの有効期限切れの可能性もあります。ローカルで以下を実行して認証をリフレッシュしてください：

```
! bash scripts/notebooklm_auth_push.sh
```

このコマンドで NotebookLM への再ログインと認証情報の Drive へのアップロードが行われます。完了後に `/visual_infographic` を再実行できます。

なお、3パターンのプロンプト markdown はすでに `outputs/` に保存済みです：
- `outputs/infographic_2026-05-24_1.md` — ステップ・フロー型
- `outputs/infographic_2026-05-24_2.md` — 比較・対比型（ミューオン視点 vs 地上視点）
- `outputs/infographic_2026-05-24_3.md` — 問い→答え展開型

---

## よーん *(15:45 JST)*

drive へのアップロードが完了したら、gmailで通知するようにできる？計画だけ立てて.

### Claude *(15:45 JST)*

現在のスキル構造とGmail通知の既存パターンを並行して調査します。

*[ツール: `Agent`, `Agent`, `ToolSearch`]*

プランファイルを作成します。

*[ツール: `Write`, `ExitPlanMode`]*

実装します。まず現在の SKILL.md を確認します。

*[ツール: `Read`]*

Step 7 の後に Step 8 を挿入します。

*[ツール: `Edit`]*

また、完了後の報告セクションに Step 8 の結果も追記します。

*[ツール: `Edit`]*

変更内容をよーんに確認してもらいます。差分を確認します。

*[ツール: `Bash`]*

意図通りの変更です。`SKILL.md` に **Step 8** を追加しました。

**変更内容まとめ:**
- Step 7（ローカル削除）の直後に Step 8 を挿入
- `send_gmail.sh` で `useakat@gmail.com` に実際に送信（draft ではなく即時送信）
- 件名: `【インフォグラフィック完成】{DATE} {タイトル冒頭20字}`
- 本文: 画像・MD の Drive URL + NotebookLM ノートブック ID
- 送信失敗時はエラー報告のみ、スキル全体は成功扱い

commit しますか？

---

## よーん *(16:29 JST)*

はい。

### Claude *(16:29 JST)*

*[ツール: `Bash`, `Bash`, `Bash`]*

リモートに新しいコミットがあるため、まず pull してからプッシュします。

*[ツール: `Bash`, `Bash`]*

push 完了しました。

`visual_infographic/SKILL.md` に Step 8（Gmail 完了通知）を追加し、`master` にプッシュ済みです。次回スキルを実行すると、Drive アップロード・ローカル削除の後に `useakat@gmail.com` へ通知メールが自動送信されます。

---

## よーん *(16:30 JST)*

インフォグラフィックは生成できた？

### Claude *(16:30 JST)*

いいえ、生成できていません。

セッション冒頭で NotebookLM の認証エラーが発生しました：

```
ValueError: CSRF token not found in HTML.
Final URL: https://notebooklm.google?location=unsupported
```

サーバーの IP/リージョンが NotebookLM に弾かれているか、セッションクッキーが期限切れになっている状態です。

ローカルで以下を実行して認証をリフレッシュすれば再実行できます：

```
! bash scripts/notebooklm_auth_push.sh
```

完了後にもう一度 `/visual_infographic` を呼んでください。なお、プロンプト markdown 3 ファイルはすでに `outputs/` に生成済みなので、NotebookLM が使えるようになれば Step 5 から再開できます。

---

## よーん *(16:32 JST)*

google drive の auth フォルダに 認証ファイルがあるので、ダウンロードして

### Claude *(16:32 JST)*

Drive の auth フォルダを検索します。

*[ツール: `ToolSearch`, `mcp__claude_ai_Google_Drive__search_files`]*

見つかりました。内容を読み込んでローカルに書き込みます。

*[ツール: `ToolSearch`]*

JSON は `read_file_content` 非対応なので、`download_file_content` を使います。

*[ツール: `ToolSearch`, `mcp__claude_ai_Google_Drive__download_file_content`]*

---

## よーん *(16:32 JST)*

[Request interrupted by user]

gws の drive scope 追加

### Claude *(16:34 JST)*

現在の gws 設定を確認します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

Drive スコープが含まれていません。`gws auth login` の使い方を確認します。

*[ツール: `Bash`]*

ブラウザが必要な再ログインが必要です。以下をローカルで実行してください：

```
! gws auth login --scopes "email,profile,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,openid"
```

既存の Gmail スコープを維持しつつ `drive` スコープを追加します。ブラウザで Google 認証画面が開くので許可してください。

---

## よーん *(16:42 JST)*

local host が見つからない画面にいった

### Claude *(16:43 JST)*

gws がローカルサーバーを立ち上げてブラウザリダイレクトしようとしていますが、うまく繋がっていない状態です。ブラウザに表示されている URL（`http://localhost:...` へのリダイレクト前の Google の画面）を確認してみてください。

別の方法として、認証 URL をコピーして手動でコードを取得するフローが使えるか確認します：

*[ツール: `Bash`]*

`--no-browser` オプションがないため、ターミナルで直接実行する必要があります。

`!` 経由だと gws のローカルサーバーとブラウザの通信がうまくいかない場合があります。**Claude Code とは別のターミナル**を開いて、直接以下を実行してみてください：

```bash
gws auth login --scopes "email,profile,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,openid"
```

ブラウザで Google 認証 → 許可 → `localhost` にリダイレクト、の流れで完了するはずです。


別の方法として、Drive MCP ツールで直接ダウンロードする方法も使えます（さっきの `download_file_content` で取得した base64 をそのままファイルに書き出す）。どちらで進めますか？

---

## よーん *(16:46 JST)*

そっちのlocalhost にトンネルでリダイレクトしてもいい？

### Claude *(16:46 JST)*

gws が使うコールバックポートを先に確認します。

*[ツール: `Bash`, `Bash`]*

リダイレクト URI が `http://localhost`（ポート指定なし）です。gws が実際に何番ポートを使うか確認します。

*[ツール: `Bash`]*

ポートは **35347** です（動的に変わります）。

ローカルマシンで以下の SSH トンネルを張ってください：

```bash
ssh -N -L 35347:localhost:35347 root@<このサーバーのIP>
```

トンネルを張ったら、ブラウザで以下の URL を開いてください（gws が出力した URL です）：

```
https://accounts.google.com/o/oauth2/auth?scope=email%20profile%20https://www.googleapis.com/auth/gmail.modify%20https://www.googleapis.com/auth/drive%20...（略）
```

Google 認証 → 許可 → `localhost:35347` へのリダイレクトがトンネル経由でこのサーバーの gws に届いて完了します。

準備できたら教えてください。

---

## よーん *(16:47 JST)*

引数の -N ってなに？

### Claude *(16:47 JST)*

SSH 接続はするけどコマンドは実行しない、という意味です。

トンネルだけ張りたい（シェルは不要）ときに使います。`-N` なしだと接続後にシェルが起動します。今回はポート転送だけできればいいので `-N` が適切です。

---

## よーん *(16:50 JST)*

認証したけどOK?

### Claude *(16:50 JST)*

*[ツール: `Bash`, `Bash`]*

`https://www.googleapis.com/auth/drive` が追加されています。ダウンロードを試みます。

*[ツール: `Bash`, `Bash`]*

スコープは追加されていますが、トークンキャッシュが古いままかもしれません。キャッシュをクリアして再試行します。

*[ツール: `Bash`]*

ダウンロード成功です。ファイルが保存されているか確認します。

*[ツール: `Bash`]*

出力先に保存されていません。`-o` フラグの動作を確認します。

*[ツール: `Bash`, `Bash`]*

`-o` フラグが効いていないようです。stdout リダイレクトで保存します。

*[ツール: `Bash`]*

保存完了です。

`/root/xClaude/gcp/notebooklm_storage_state.json`（18KB、クッキー52件）を取得しました。NotebookLM の認証も通るはずです。`/visual_infographic` を再実行してみますか？

---

## よーん *(16:54 JST)*

drive_get.py を使ってダウンロードした？

### Claude *(16:54 JST)*

いいえ、使っていません。`drive_get.py` というファイルは存在せず（あるのは `drive_get.sh`）、それも gws の Drive スコープ不足で失敗したため、`gws drive files get` を直接実行してリダイレクトで保存しました。

`drive_get.sh` の中身も同じコマンドなので結果は同じですが、スクリプトを通さずに直接実行しています。`drive_get.sh` を使うべきでしたか？

---

## よーん *(16:54 JST)*

drive_get.sh を使ってダウンロードしてみて

### Claude *(16:55 JST)*

*[ツール: `Bash`]*

成功しました。Drive スコープを追加したことで `drive_get.sh` が正常に動作するようになっています。

---

## よーん *(16:56 JST)*

drive からのファイルダウンロードは、トークン節約のため、ローカルの場合は drive_get.sh, リモートの場合は drivemcp_get_remote.sh を使うというルールを CLAUDE.md に追加しておいて

### Claude *(16:56 JST)*

*[ツール: `Read`]*

Google サービス連携のセクションに追記します。

*[ツール: `Read`, `Edit`]*

追記しました。内容は以下のとおりです：

- **ローカル**: `drive_get.sh`
- **リモート**: `drivemcp_get_remote.sh`
- Drive MCP ツールは base64 がトークンを消費するため、スクリプトで代替できる場合は使わない

commit しますか？

---

## よーん *(16:57 JST)*

はい

### Claude *(16:57 JST)*

*[ツール: `Bash`, `Bash`]*

push 完了しました。

---

## よーん *(16:57 JST)*

/record

### Claude *(16:58 JST)*

`docs/changelog.md` と git 履歴を並行して確認します。

*[ツール: `Read`, `Bash`]*

照合しました。未記録の変更候補を提案します。


**変更ログ候補（未記録）**

以下の変更が記録されていません。記録するものを選んでください（複数選択可）：

1. **NotebookLM リモート環境対応：vendor ライブラリ追加・スキル MCP 化** — `vendor/notebooklm/` に Python クライアントを追加してリモートでのインフォグラフィック生成を可能にし、認証・Drive アップロードを MCP ツール対応に変更
   - 関連コミット: `0fee2f2 feat: notebooklm をリモート環境で実行可能にする` / `3d594ff fix: リモート環境の認証・Drive アップロードを MCP ツール対応に変更`
   - 変更ファイル: `vendor/notebooklm/`（大量）, `scripts/notebooklm_manager.py`, `.claude/skills/visual_infographic/SKILL.md`, `scripts/notebooklm_auth_pull.sh`
   - 関連する過去の変更: **drivemcp_get_remote.sh 追加：リモートセッション専用 Drive ダウンロード**

2. **visual_infographic：Drive アップロード完了後の Gmail 通知追加** — Step 7（ローカル削除）の後に `send_gmail.sh` で完了通知メールを送る Step 8 を追加
   - 関連コミット: `090465f feat(visual_infographic): Drive アップロード完了後に Gmail 通知を追加（Step 8）`
   - 変更ファイル: `.claude/skills/visual_infographic/SKILL.md`
   - 関連する過去の変更: なし

3. **drive_put.sh：gws エラー時の空レスポンス JSON 例外修正** — gws コマンド失敗時に空レスポンスを JSON パースしようとして例外が発生する不具合を修正
   - 関連コミット: `1a68c6a drive_put: gws エラー時の空レスポンスで JSON 例外が出る不具合を修正`
   - 変更ファイル: `scripts/drive_put.sh`
   - 関連する過去の変更: **drive_put.sh 汎用化：任意フォルダ対応・MIME 自動判定**

4. **CLAUDE.md：Drive ファイルダウンロードのスクリプト使い分けルール追加** — ローカルは `drive_get.sh`、リモートは `drivemcp_get_remote.sh` を使うルール（Drive MCP ツールのトークンコスト回避）を追加
   - 関連コミット: `9a605e1 docs: Drive ダウンロードのスクリプト使い分けルールを CLAUDE.md に追加`
   - 変更ファイル: `CLAUDE.md`
   - 関連する過去の変更: **drivemcp_get_remote.sh 追加：リモートセッション専用 Drive ダウンロード**、**Google サービス連携・スクリプト化ルールの追加**

（記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。）

---

## よーん *(16:59 JST)*

1はスキップ、2,3は変更ログのみ、4は変更ログと報告書

### Claude *(16:59 JST)*

了解しました。まず報告書テンプレートを確認します。

*[ツール: `Read`]*

報告書の作成と変更ログの更新を行います。

*[ツール: `Write`]*

次に変更ログに3件を追記します。

*[ツール: `Edit`]*
