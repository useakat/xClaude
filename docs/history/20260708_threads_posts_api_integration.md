---
title: Threads 投稿一覧の API 取得・記録基盤を新規構築 — セッション履歴
date: 2026-07-08
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-08 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260708_threads_posts_api_integration/)

---

## よーん *(23:05 JST)*

threads という SNS があるんだけど、それの投稿一覧シートを　https://docs.google.com/spreadsheets/d/1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c/edit?gid=1832329664#gid=1832329664　に追加したい。実装計画を立てて。その際、X みたいに、API などで投稿データを取得できるか調べて

### Claude *(23:05 JST)*

実装計画を立てるため plan mode に入ります。Threads API の調査と、既存の X 投稿一覧まわりの実装を並行で調べます。

*[ツール: `EnterPlanMode`]*

2つの Explore エージェント（Threads API 調査／既存 X 分析フローの調査）と、対象スプレッドシートの構成確認を並行で行います。

*[ツール: `Agent`, `Agent`, `mcp__mcp-gsheets__sheets_get_metadata`]*

対象スプレッドシートは「発信記録」で、**「X投稿一覧」シート（33列）**が既にあります。これを雛形に「Threads投稿一覧」を作る形になります。X投稿一覧のヘッダーを確認します（Explore エージェントは並行実行中）。

*[ツール: `mcp__mcp-gsheets__sheets_get_values`]*

対象スプレッドシート「発信記録」の X投稿一覧（33列：本文・画像・インプレ/いいね/リポスト/リプ/ブクマ・各種率・詳細表示/リンククリック/フォロー増 等）を確認しました。

現在、2つの調査を並行実行中です:
- **Threads 公式 API で投稿一覧・メトリクスを取得できるか**（認証・エンドポイント・制約）
- **既存の X 投稿一覧の記録/更新フロー**（雛形に流用できるスクリプト・スキル）

両方の結果が揃い次第、Threads 投稿一覧シートの列設計・データ取得方式・更新フローを含む実装計画をまとめます。完了通知を待っています。

Threads API 調査が完了しました。**結論：API で投稿一覧もメトリクスも取得可能**です（要点は後述）。もう1つの「既存 X 分析フロー」調査の完了を待って、実装計画をまとめます。

（Threads API 要点メモ: `GET /{user-id}/threads` で投稿一覧、`GET /{media-id}/insights` で views/likes/replies/reposts/quotes/shares。OAuth `threads_basic`＋`threads_manage_insights`、長期トークン60日、Instagram プロフェッショナルアカウント連携が必要、本番は App Review 2〜8週間・テスターは即時。公式SDKなし＝`requests` 直叩き。）

両方の調査が揃いました。要点を共有し、計画を詰めるため2点確認します。

## 調査結論

**① Threads は X 同様、API で投稿データを取得できます（無料）。**
- 投稿一覧: `GET /{user-id}/threads`（id・本文・permalink・timestamp・media_type 等）
- 投稿ごとのメトリクス: `GET /{media-id}/insights`（**views**（≒インプレッション）・likes・replies・reposts・quotes・shares）
- 認証: OAuth（`threads_basic`＋`threads_manage_insights`）、**長期トークン60日**、**Instagram プロフェッショナルアカウント連携が必須**
- **自分のデータ取得は「テスターモード」で即時利用可**（本番公開の App Review 2〜8週間は不要）。CSV 不要で API 直取得できる分、**X より自動化しやすい**（X はアナリティクス CSV 手動取り込みが必要）。

**② 記録先**は「発信記録」スプレッドシートで、既に「X投稿一覧」（33列）があります。ここに「**Threads投稿一覧**」シートを新設し、X 流の記録/分析フロー（`record_output.py`／`fetch_*` スクリプト／分析スキル `ops_analyze-posts`）を雛形に流用できます。

計画を確定する前に2点教えてください。

*[ツール: `AskUserQuestion`]*

スコープ＝取得・記録のみ、IG 連携はガイド必要、で確定。計画をまとめます。

*[ツール: `Write`]*

Threads 投稿一覧の実装計画をまとめました。承認をお願いします。

*[ツール: `ExitPlanMode`]*

承知しました。3点反映します。まず **media_id** の説明:

**media_id** は Threads API が各投稿に振る一意の ID（例: 投稿の `id` フィールド）です。**再取得のたびに「同じ投稿の行」を見分けてメトリクスだけ更新する（重複行を作らない）ための突合キー**として使う想定でした。ただ、これは技術的な列なので——**専用の media_id 列は無くし、代わりに「投稿URL(permalink)」を突合キーにします**（permalink も投稿ごとに一意なので同じ役割を果たせます）。これで技術列が消えてスッキリします。

計画の列設計を更新します（目的列を削除・X投稿URL 追加・media_id 列を廃止）。

*[ツール: `Edit`]*

Verification セクションの upsert 記述も突合キーを permalink に合わせて更新します。

*[ツール: `Edit`]*

列設計を更新しました（目的列を削除・**X投稿URL(H)** を親投稿URLの次に追加・media_id 列は廃止して permalink を突合キーに）。承認をお願いします。

*[ツール: `ExitPlanMode`]*

ご指摘のとおり表現が不整合でした。正確には：**media_id は「シートの列としては持たない」だけで、API がメトリクスを返すには各投稿の `id`（＝ media_id）が必要**です。取得スクリプトは `GET /{user-id}/threads` の応答に含まれる各投稿の `id` を**内部的に使って** `/{id}/insights` を叩きますが、その id はシートには保存しません（シートの突合キーは permalink）。Phase 2 の文言を直します。

*[ツール: `Edit`]*

文言を修正しました（media_id ＝ API 内部で使う各投稿の `id`。シート列としては持たず、突合は permalink）。承認をお願いします。

*[ツール: `ExitPlanMode`]*

計画承認ありがとうございます。実装は **Phase 0（セットアップ）から**進めます。ここはよーんのブラウザ操作が中心なので、対話でガイドします。全体像 → 最初のステップの順で進めます。

## Phase 0 の全体像（一度きり・所要30〜60分目安）
1. **Instagram をプロフェッショナル化 → Threads と連携**（← まずここ）
2. Meta 開発者アプリ作成（Threads ユースケース）
3. 自分をテスターに追加
4. OAuth でトークン取得（短期→長期60日）＋ Threads User ID 取得
5. トークンを `gcp/threads_token.json` に保存 → 私が疎通確認

---

## STEP 1：Instagram プロフェッショナル化 & Threads 連携

Threads API は「Threads にひも付いた Instagram プロフェッショナルアカウント」を通して認証します。まず現状確認をお願いします。

**確認 A：Threads アカウントはどの Instagram とひも付いていますか？**
- Threads アプリ → プロフィール → 設定 → アカウント で、連携中の Instagram を確認できます。

**確認 B：その Instagram はプロフェッショナル（ビジネス/クリエイター）ですか？**
- Instagram アプリ → 設定 →「アカウントの種類とツール」→「プロアカウントに切り替える」があれば **まだ個人アカウント**です。
- もし個人アカウントなら、**クリエイター**に切り替えるのがおすすめ（無料・非公開性ほぼ変わらず・いつでも戻せる）。

---

まずこの **確認 A・B の結果**を教えてください（例：「IG は @xxx、すでにクリエイターアカウント」/「個人アカウントのまま」など）。それに応じて、切り替え手順 or 次の STEP 2（Meta アプリ作成）に進みます。

一気に全部やってしまいたい場合は「全部の手順をまとめて出して」と言ってください。詳細な手順書を一括で出します。

---

## よーん *(22:48 JST)*

instagram は usephys1  で個人アカウント

### Claude *(22:49 JST)*

了解です。IG `@usephys1` は個人アカウントなので、まず**プロフェッショナル（クリエイター）に切り替え**ます。Threads もこの `usephys1` に紐付いている前提で進めます。

## STEP 1：Instagram をクリエイターアカウントに切り替え

**スマホの Instagram アプリで:**
1. プロフィール画面 → 右上「≡」→ **設定とプライバシー**
2. **アカウントの種類とツール** → **プロアカウントに切り替える**
3. カテゴリを選択（例:「デジタルクリエイター」「科学」など何でも可）
4. **「クリエイター」** を選択（※「ビジネス」でも API は使えますが、個人発信ならクリエイター推奨）
5. 連絡先などはスキップ可 → 完了

**⚠ 注意点（事前に把握しておいてください）:**
- プロアカウント（ビジネス/クリエイター）は原則**公開アカウント**になります。`@usephys1` が今**非公開**なら公開に変わります。発信用アカウントなら問題ないはずですが、非公開のままにしたい場合は言ってください（別の方針を検討します）。
- 切り替えは**無料**、**いつでも個人アカウントに戻せます**。

---

切り替えが済んだら「**切り替えた**」と教えてください。次に **STEP 2：Meta 開発者アプリの作成**（Threads ユースケース）に進みます。

（`@usephys1` を非公開で運用したい等の懸念があれば、先に相談してください。）

---

## よーん *(22:53 JST)*

切り替えた

### Claude *(22:54 JST)*

切り替えありがとうございます。次は **STEP 2：Meta 開発者アプリの作成**です。ブラウザ（PC 推奨）で進めてください。

## STEP 2：Meta アプリを作る（Threads ユースケース）

1. **https://developers.facebook.com/** を開き、Facebook アカウントでログイン
   - 初めてなら「**開始する / Get Started**」で**開発者登録**（電話/メール認証）を済ませる。
2. 右上 **My Apps（マイアプリ）** → **Create App（アプリを作成）**
3. ユースケース選択で **「Access the Threads API（Threads API を利用）」** を選ぶ → Next
4. アプリ名（例: `usephys1-threads`）と連絡先メールを入力 → **Create App**（パスワード確認あり）
5. 作成後のダッシュボードで、左メニューの **Use cases（ユースケース）→ Threads** を開き **Customize（カスタマイズ）**
6. **Permissions（権限）** で次の2つを **Add** する:
   - `threads_basic`
   - `threads_manage_insights`
7. 左メニュー **App settings（アプリの設定）→ Basic** を開き、**App ID** と **App secret（表示ボタンで確認）** を控える

---

できたら、次を教えてください:
- **App ID**（数字の羅列。公開情報なので貼ってOK）
- `threads_basic` と `threads_manage_insights` を **Add できたか**

※ **App secret は秘密情報**なので、ここには貼らないでください（後でトークン交換に使いますが、その時は安全な方法を案内します）。

App ID をもらったら、**STEP 3（自分をテスターに追加）→ STEP 4（トークン取得）**に進みます。ここが少し込み入るので、一つずつ一緒にやりましょう。

---

## よーん *(23:04 JST)*

AppID: 1129050173636012

threads_basic と threads_manage_insights を Add できた

### Claude *(23:05 JST)*

App ID 受け取りました（`1129050173636012`）。次は自分をテスターに追加 → トークン取得です。少し込み入るので2段階で。

## STEP 3：自分を Threads テスターに追加

1. アプリのダッシュボード左メニュー → **App roles（アプリの役割）→ Roles（ロール）**
2. **Threads testers** の欄で **Add people / Add Threads Testers** → Threads のユーザー名 **`usephys1`** を入力して招待
3. 招待を**承認**する：
   - ブラウザで **https://www.threads.net/settings/account** を開く（`usephys1` でログイン）
   - **「ウェブサイトのアクセス許可 / Apps and websites（アプリとウェブサイト）」**あたりに**招待（Invites）**が来ているので **承認/Accept**
   - （Threads アプリの 設定→アカウント からも辿れます）

## STEP 4a：リダイレクト URI 設定 → 認可コードを取得

1. ダッシュボード → **Use cases → Threads → Customize → Settings** の中の **Redirect Callback URLs（リダイレクトコールバックURL）** に次を追加して保存:
   ```
   https://localhost/
   ```
2. 下の**認可URL**をブラウザで開く（`usephys1` でログイン状態で）:
   ```
   https://threads.net/oauth/authorize?client_id=1129050173636012&redirect_uri=https%3A%2F%2Flocalhost%2F&scope=threads_basic%2Cthreads_manage_insights&response_type=code
   ```
3. 「許可する / Allow」を押すと、`https://localhost/?code=XXXXXXXX#_` にリダイレクトされます（ページは表示エラーでOK）。
4. アドレスバーの **`code=` の後ろの文字列**をコピー（末尾の **`#_` は含めない**）。

---

STEP 3 の承認まで済んで、STEP 4a で **`code`（認可コード）**が取れたら教えてください。

次の **STEP 4b** で、その `code` と App secret を使って**長期トークン（60日）に交換**します。**App secret はチャットに貼らない**方法（よーんのターミナルで `!` 実行）で行うので安心してください。準備できたら code をどうぞ。

---

## よーん *(23:11 JST)*

コールバックURL） にhttps://localhost/  を追加すると、保存できない。

### Claude *(23:12 JST)*

localhost は Meta 側で弾かれます（公開到達可能な HTTPS でないとダメ）。**`https://httpbin.org/get`** を使いましょう。これは公開されていて、リダイレクト後に受け取ったパラメータ（`code`）を画面にそのまま表示してくれるので、コード取得に最適です。

## STEP 4a（修正版）

1. **Redirect Callback URLs** に localhost の代わりに次を追加して保存:
   ```
   https://httpbin.org/get
   ```
2. この認可URLをブラウザで開く（`usephys1` でログイン状態）:
   ```
   https://threads.net/oauth/authorize?client_id=1129050173636012&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_manage_insights&response_type=code
   ```
3. 「許可する / Allow」を押すと **httpbin.org のページ**が開き、JSON の中に:
   ```json
   "args": { "code": "XXXXXXXXXXXX" }
   ```
   のように **`code` が表示**されます。その **`XXXX` の文字列**をコピー（末尾に `#_` が付いていたら**除く**）。

---

※ リダイレクトURI は **アプリ設定と認可URLで完全一致**が必要です（両方 `https://httpbin.org/get`）。

`code` が取れたら教えてください。次の STEP 4b でトークンに交換します（App secret はよーんのターミナルで `!` 実行、チャットに貼らない方式）。

---

## よーん *(23:13 JST)*

Redirect Callback URLs に https://httpbin.org/get を追加して保存ボタンを押すと、

フォームを保存できません
すべての情報が正しく入力されていることをご確認のうえ、もう一度実行してください

というエラーが出る

### Claude *(23:14 JST)*

そのエラーは「redirect URL 単体の問題」ではなく、**フォーム内のどこかに未入力の必須項目がある**ときに出やすい一般エラーです。Threads/Meta アプリでよくある原因は「**プライバシーポリシー URL 未設定**」です。順に確認してください。

## まず確認①：どこがエラーか
Redirect URL の入力欄**自体が赤く**なっていますか？ それとも**ページ上部に帯**でエラーが出ているだけ？
- 入力欄が赤 → URL の問題（後述の別 URL を試す）
- 上部に帯だけ → **別の必須項目が未入力**（下の②が原因の可能性大）

## 確認②：必須項目を埋める（有力）
1. 左メニュー **App settings（設定）→ Basic（基本）** を開く
2. 次が空なら埋める:
   - **Privacy Policy URL（プライバシーポリシーURL）** ← Threads で必須になりがち。とりあえず自分の note か X プロフィール、無ければ `https://www.threads.net/@usephys1` でも可（後で差し替え可）
   - **Category（カテゴリ）** を選択
   - （**App Domains** があれば `httpbin.org` を追加）
3. 下部の **変更を保存**
4. その後、もう一度 **Threads → Settings → Redirect Callback URLs** に `https://httpbin.org/get` を入れて保存

## それでもダメなら：別のリダイレクトURL
同じ画面に **Deauthorize callback URL / Data deletion callback URL** の欄があれば、そこも同じ `https://httpbin.org/get` で埋めてみてください（空だと弾く実装があります）。

---

どこが赤かった／どの欄が空だったかを教えてもらえれば、ピンポイントで直せます。まずは **Basic 設定のプライバシーポリシーURL** を埋めて再保存を試してください。

---

## よーん *(23:18 JST)*

保存できました

### Claude *(23:19 JST)*

保存できましたね。では**認可コードの取得**に進みます。

## 認可URLを開いて code を取得

`usephys1` でログインした状態のブラウザで、次を開いてください:

```
https://threads.net/oauth/authorize?client_id=1129050173636012&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_manage_insights&response_type=code
```

1. 認可画面が出たら **「許可する / Allow」**
2. すると **httpbin.org のページ**（JSON）が開きます。その中の:
   ```json
   "args": { "code": "AQ...長い文字列..." }
   ```
   の **`code` の値**をコピー（末尾に `#_` があれば除く）

---

補足:
- もし **「テスターとして招待を承認していない」系のエラー**や、そもそも認可画面が出ない場合は、STEP 3（テスター招待の承認）が未完了です。https://www.threads.net/settings/account の「アプリとウェブサイト / 招待」で承認してから再度開いてください。
- 認可画面は出たのにエラーになる場合は、その**エラー文言をそのまま**教えてください。

`code` が取れたら貼ってください（code 自体は一時的なもので、これだけでは悪用しづらいですが、気になる場合は「取れた」とだけ言ってもらい、次の交換コマンドをよーんのターミナルで実行する形にもできます）。

---

## よーん *(23:19 JST)*

```
{"error_message":"Authorization Failed: No app ID was sent with the request.","error_code":4476002}

上記のエラーが出る
```

### Claude *(23:20 JST)*

そのエラー（`4476002 / No app ID was sent`）は、**リクエストに client_id が届いていない**ときに出ます。多くはURLのコピペ崩れ（`?` や `&` が欠ける／検索窓に入れてしまう）が原因です。切り分けましょう。

## まず確認：エラー画面のアドレスバー
エラーが出たときの**ブラウザのアドレスバー**に `client_id=1129050173636012` の文字列は残っていますか？
- **無い/欠けている** → URL が途中で切れています（コピペ崩れ）。下の手順で貼り直し。
- **ちゃんと有る** → アプリ側設定の問題なので、別途対処します。

## 貼り直し手順
1. 下のURLを**1行まるごと**コピー（改行を挟まない）
2. ブラウザの**アドレスバーに直接ペースト**（Google 検索窓ではなく、URL 欄）してエンター

URL（1行）:
```
https://threads.net/oauth/authorize?client_id=1129050173636012&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_manage_insights&response_type=code
```

もし上でダメなら、**scope を1つだけ**にした最小URLも試してください（原因切り分け）:
```
https://threads.net/oauth/authorize?client_id=1129050173636012&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic&response_type=code
```

---

補足の確認ポイント:
- **Threads → Settings** に `client_id` に対応する **App ID が 1129050173636012** で合っているか（別アプリの画面を見ていないか）。
- アドレスバーに client_id が残っているのにエラー、という場合は**その時のURL全体**（code は無いはず）を教えてください。設定側を詰めます。

どちらのURLで結果がどうなったか教えてください。

---

## よーん *(23:24 JST)*

scope 1つだけのURL でも同じエラーが出る。

エラーが出た時のアドレスバーのURL
https://www.threads.com/oauth/authorize/error.json?error_message=Authorization+Failed%3A+No+app+ID+was+sent+with+the+request.&error_code=4476002&ext=1783434300&hash=Aed7gnHBaDckNlfDiazybuZ86M0

### Claude *(23:25 JST)*

原因判明です。アドレスバーが **`www.threads.com`** になっています。`threads.net` にアクセス→ **threads.com にリダイレクトされる際に client_id が落ちて**このエラーになっています（Threads はドメインが threads.com に移行済み）。

**最初から threads.com のドメインで開けば**リダイレクトが起きず、パラメータが保持されます。次を試してください:

```
https://www.threads.com/oauth/authorize?client_id=1129050173636012&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_manage_insights&response_type=code
```

- `usephys1` ログイン状態で、アドレスバーに直接ペースト → エンター
- 「許可する / Allow」→ httpbin.org のページに `"code": "..."` が出る

---

もしこれでも同じエラーなら、`threads.net` 版（前回のURL）と見比べて、アドレスバーで client_id が保持されているか確認してください。うまくいったら `code` を教えてください（次のトークン交換に進みます）。

---

## よーん *(23:29 JST)*

client_id は App ID のこと？Threads App ID ではなくて？

### Claude *(23:30 JST)*

鋭いです。**Threads の OAuth では `client_id` は「Threads App ID」を使います**（アプリ全体の App ID `1129050173636012` とは**別物**のことが多い）。同様に、あとで使う秘密鍵も「**Threads App Secret**」です。

## Threads App ID の場所
ダッシュボードで次のどちらかにあります:
- **Use cases → Threads → Settings** の中に「**Threads app ID**」「**Threads app secret**」
- または **App settings（設定）→ Basic** を下にスクロールした **Threads** セクション

そこに表示される **Threads app ID**（`1129...` とは違う数字のはず）を教えてください。

## それで認可URLを作り直します
Threads App ID を `THREADS_APP_ID` として:
```
https://www.threads.com/oauth/authorize?client_id=THREADS_APP_ID&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_manage_insights&response_type=code
```
（`www.threads.com` ドメインも前回判明した修正点なので、そのまま使います）

---

もし「Threads app ID が見当たらない／App ID と同じ数字しかない」場合は、その旨教えてください（アプリによっては共通のこともあります）。Threads App ID が分かれば、それで再度 Allow まで進めます。

---

## よーん *(23:30 JST)*

Threads app ID: 4371768313073061

### Claude *(23:30 JST)*

それです。Threads App ID を使って認可URLを作り直しました。これで開いてください:

```
https://www.threads.com/oauth/authorize?client_id=4371768313073061&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_manage_insights&response_type=code
```

1. `usephys1` ログイン状態でアドレスバーに直接ペースト → エンター
2. **「許可する / Allow」**
3. httpbin.org のページが開き、JSON の中に:
   ```json
   "args": { "code": "AQ...長い文字列..." }
   ```
   が表示される → その **`code` の値**をコピー（末尾に `#_` があれば除く）

---

取れたら `code` を貼ってください。次に **App secret（Threads App Secret）を使ったトークン交換**に進みます。その際 **secret はチャットに貼らず、よーんのターミナルで `!` 実行**する方式にします（安全のため）。

`code` 取得後の流れ:
- 私が「code＋secret を使って長期トークンを取得し `gcp/threads_token.json` に保存する」ワンライナー/スクリプトを用意
- よーんが `!` で実行（secret はそこで入力）
- 私はトークンには触れず、疎通確認だけ行う

まず `code` をどうぞ。

---

## よーん *(23:32 JST)*

503 Service Temporarily Unavailable

と表示された。
アドレスバーのURL : https://httpbin.org/get?code=AQI9hR-ZRf2MZKe1nTw1RkUp10bWWyPJF4UKK_81EoLN4VGeOYUrMFB_SOMaqBwyYQ3R8s-Hl7-gRSxDwpyXs4WjpLi2i5KNEnvSvAuIc0WjHj03gomdMwDjI6aWuv6Iwd7spzqKm479F52iQeFzUSg31sgoXKczyYsJDI8vBjqFjX_IPjt8PnYa-I9spS0OFu6CHvUzNVAPKdeg53ic5yKGem7yKuVaoof5W5kHuwH3EA#_

### Claude *(23:33 JST)*

認可は**成功しています**（httpbin の 503 は httpbin 側の一時障害で無関係。重要なのはアドレスバーの `code=` で、ちゃんと取れています）。

⚠ **認可コードは短時間（約1時間）で失効**するので、早めにトークン交換します。

## STEP 4b：トークン交換（よーんが `!` で実行）

下のコマンドの **`ここにThreadsAppSecretを貼る`** を、**Threads App Secret**（Threads use case → Settings の「Threads app secret」を表示して取得）に置き換えて、`!` を付けて実行してください。**code は取得済みの値を埋め込んであります。**

```
! THREADS_APP_SECRET='ここにThreadsAppSecretを貼る' THREADS_CODE='AQI9hR-ZRf2MZKe1nTw1RkUp10bWWyPJF4UKK_81EoLN4VGeOYUrMFB_SOMaqBwyYQ3R8s-Hl7-gRSxDwpyXs4WjpLi2i5KNEnvSvAuIc0WjHj03gomdMwDjI6aWuv6Iwd7spzqKm479F52iQeFzUSg31sgoXKczyYsJDI8vBjqFjX_IPjt8PnYa-I9spS0OFu6CHvUzNVAPKdeg53ic5yKGem7yKuVaoof5W5kHuwH3EA' python3 - <<'PY'
import os, json, time, urllib.parse, urllib.request
cid='4371768313073061'; secret=os.environ['THREADS_APP_SECRET']; code=os.environ['THREADS_CODE']; redirect='https://httpbin.org/get'
body=urllib.parse.urlencode({'client_id':cid,'client_secret':secret,'grant_type':'authorization_code','redirect_uri':redirect,'code':code}).encode()
try:
    d=json.load(urllib.request.urlopen(urllib.request.Request('https://graph.threads.net/oauth/access_token', data=body)))
except urllib.error.HTTPError as e:
    print('短期トークン取得エラー:', e.read().decode()); raise SystemExit(1)
short=d['access_token']; uid=d.get('user_id'); print('短期トークンOK user_id=',uid)
q=urllib.parse.urlencode({'grant_type':'th_exchange_token','client_secret':secret,'access_token':short})
try:
    d2=json.load(urllib.request.urlopen('https://graph.threads.net/access_token?'+q))
except urllib.error.HTTPError as e:
    print('長期トークン取得エラー:', e.read().decode()); raise SystemExit(1)
os.makedirs('gcp', exist_ok=True)
json.dump({'access_token':d2['access_token'],'user_id':uid,'token_type':d2.get('token_type'),'expires_in':d2.get('expires_in'),'obtained_at':int(time.time())}, open('gcp/threads_token.json','w'))
print('✓ 長期トークンを gcp/threads_token.json に保存。有効日数≈', (d2.get('expires_in') or 0)//86400)
PY
```

- 成功すると `✓ 長期トークンを gcp/threads_token.json に保存。有効日数≈ 59` のように出ます。
- `gcp/` は gitignore 済みなので Git には上がりません。
- **secret はこのコマンド内だけで使われ**、保存されるのはトークンのみです。

実行結果（成功/エラー文言）を教えてください。エラーなら文言を見て直します。うまくいったら、私が `gcp/threads_token.json` で投稿一覧の取得疎通を確認します（Phase 1・2 へ）。

---

## よーん *(23:41 JST)*

こまんどが長すぎてうまくできない。

### Claude *(23:41 JST)*

長すぎましたね。短いコマンドで済むよう、**交換用スクリプトを用意**して、認可コードもファイルに入れておきます。よーんは**secret を1つ足すだけ**で実行できます。

まず交換スクリプトと認可コードファイルを作成します。

*[ツール: `Write`]*

認可コードをファイルに保存します。

*[ツール: `Write`]*

準備できました。よーんは **secret を1つ足すだけ**です。次を `!` で実行してください（`ここに貼る` を **Threads App Secret** に置き換え）:

```
! THREADS_APP_SECRET='ここに貼る' python3 scripts/threads_token_exchange.py
```

- 認可コードは `gcp/threads_code.txt` から自動で読みます（実行後に自動削除されます）。
- 成功すると `✓ 長期トークンを gcp/threads_token.json に保存。有効日数≈59` のように出ます。

**Threads App Secret の場所**（忘れた場合）: ダッシュボード → Use cases → Threads → Settings の「**Threads app secret**」の Show ボタン。

---

結果（成功メッセージ or エラー文言）を教えてください。
- 成功 → 私が投稿一覧の取得疎通を確認して Phase 1・2 に進みます。
- `APIエラー ... code ... expired`（コード失効）が出たら → 認可URLをもう一度開いて新しい code を取り、`gcp/threads_code.txt` を更新して再実行します（すぐ案内します）。

---

## よーん *(23:57 JST)*

スクリプトを実行したが、なかなか終わらない。以下が実行を途中で止めた時のメッセージ

root@v133-18-181-39-vir:~/xClaude# THREADS_APP_SECRET='***REDACTED***' python3 
scripts/threads_token_exchange.py
^CTraceback (most recent call last):
  File "/root/xClaude/scripts/threads_token_exchange.py", line 99, in <module>
    main()
  File "/root/xClaude/scripts/threads_token_exchange.py", line 67, in main
    d = _post("https://graph.threads.net/oauth/access_token", body)
  File "/root/xClaude/scripts/threads_token_exchange.py", line 37, in _post
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data)))
  File "/usr/lib/python3.10/urllib/request.py", line 216, in urlopen
    return opener.open(url, data, timeout)
  File "/usr/lib/python3.10/urllib/request.py", line 519, in open
    response = self._open(req, data)
  File "/usr/lib/python3.10/urllib/request.py", line 536, in _open
    result = self._call_chain(self.handle_open, protocol, protocol +
  File "/usr/lib/python3.10/urllib/request.py", line 496, in _call_chain
    result = func(*args)
  File "/usr/lib/python3.10/urllib/request.py", line 1391, in https_open
    return self.do_open(http.client.HTTPSConnection, req,
  File "/usr/lib/python3.10/urllib/request.py", line 1348, in do_open
    h.request(req.get_method(), req.selector, req.data, headers,
  File "/usr/lib/python3.10/http/client.py", line 1312, in request
    self._send_request(method, url, body, headers, encode_chunked)
  File "/usr/lib/python3.10/http/client.py", line 1358, in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.10/http/client.py", line 1307, in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.10/http/client.py", line 1067, in _send_output
    self.send(msg)
  File "/usr/lib/python3.10/http/client.py", line 1005, in send
    self.connect()
  File "/usr/lib/python3.10/http/client.py", line 1477, in connect
    super().connect()
  File "/usr/lib/python3.10/http/client.py", line 971, in connect
    self.sock = self._create_connection(
  File "/usr/lib/python3.10/socket.py", line 833, in create_connection
    sock.connect(sa)
KeyboardInterrupt

[Request interrupted by user]

スクリプトを実行したが、なかなか終わらない。以下が実行を途中で止めた時のメッセージ

root@v133-18-181-39-vir:~/xClaude# THREADS_APP_SECRET='***' python3 
scripts/threads_token_exchange.py
^CTraceback (most recent call last):
  File "/root/xClaude/scripts/threads_token_exchange.py", line 99, in <module>
    main()
  File "/root/xClaude/scripts/threads_token_exchange.py", line 67, in main
    d = _post("https://graph.threads.net/oauth/access_token", body)
  File "/root/xClaude/scripts/threads_token_exchange.py", line 37, in _post
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data)))
  File "/usr/lib/python3.10/urllib/request.py", line 216, in urlopen
    return opener.open(url, data, timeout)
  File "/usr/lib/python3.10/urllib/request.py", line 519, in open
    response = self._open(req, data)
  File "/usr/lib/python3.10/urllib/request.py", line 536, in _open
    result = self._call_chain(self.handle_open, protocol, protocol +
  File "/usr/lib/python3.10/urllib/request.py", line 496, in _call_chain
    result = func(*args)
  File "/usr/lib/python3.10/urllib/request.py", line 1391, in https_open
    return self.do_open(http.client.HTTPSConnection, req,
  File "/usr/lib/python3.10/urllib/request.py", line 1348, in do_open
    h.request(req.get_method(), req.selector, req.data, headers,
  File "/usr/lib/python3.10/http/client.py", line 1312, in request
    self._send_request(method, url, body, headers, encode_chunked)
  File "/usr/lib/python3.10/http/client.py", line 1358, in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.10/http/client.py", line 1307, in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.10/http/client.py", line 1067, in _send_output
    self.send(msg)
  File "/usr/lib/python3.10/http/client.py", line 1005, in send
    self.connect()
  File "/usr/lib/python3.10/http/client.py", line 1477, in connect
    super().connect()
  File "/usr/lib/python3.10/http/client.py", line 971, in connect
    self.sock = self._create_connection(
  File "/usr/lib/python3.10/socket.py", line 833, in create_connection
    sock.connect(sa)
KeyboardInterrupt

### Claude *(23:59 JST)*

2つ問題があります。

**① App Secret がチャットに露出しました**（`***REDACTED***`）。これは後で必ず **Threads App Secret をリセット**（ダッシュボードで再生成）してください。今のトークン取得自体には使えますが、露出した secret は無効化すべきです。あとで案内します。

**② 接続が `sock.connect` でハング** ＝ **この VPS から `graph.threads.net` に到達できていない**可能性が高いです（NotebookLM が IP ブロックされていたのと同じ現象かも）。切り分けます。

まず到達性とプロキシの状態を確認します。

*[ツール: `Bash`]*

原因判明です。**IP ブロックではありません**（curl は graph.threads.net に到達＝http 500 応答あり）。DNS が **IPv6 アドレスのみ**を返し、この VPS は **IPv6 が通らないため python が IPv6 接続でハング**していました（curl は IPv4 にフォールバックして成功）。

secret は既にこのチャットに出てしまっているので、**今あるコードと secret で私が curl（IPv4 強制）で交換して即座にトークンを取得**します（その後 secret リセットを必ず実施いただきます）。トークン本体は表示せずファイル保存します。

*[ツール: `Bash`]*

トークン取得は成功しました（60日有効・`gcp/threads_token.json` に保存）。ただ `UID` が bash の予約変数と衝突して **user_id が誤って 0 で保存**されました。正しい Threads user_id を API から取得して修正しつつ、**疎通確認**（投稿一覧が取れるか）も行います。

*[ツール: `Bash`]*

🎉 **Phase 0 完了・疎通確認できました。**

## 確認結果
- トークン有効（`/me` → id=`28009154138682425`, username=**usephys1**）
- **投稿一覧が取れる**（最新3件を取得できました）:
  - 7/6 CAROUSEL「はやぶさ２の撮ったトリフネの画像来た！…」
  - 7/5 IMAGE「実は、僕らの手が届かない場所で、ボイジャーは…」
  - 7/4 TEXT「太陽系には、175年に一度の外惑星の並び…」
- 誤って 0 になっていた user_id を正しい値に修正済み。
- 長期トークン（60日）を `gcp/threads_token.json`（gitignore 済み）に保存。認可コードファイルは削除済み。

**原因メモ**: この VPS は IPv6 が通らず、`graph.threads.net` が IPv6 のみ解決されるため python がハングしていました。→ **取得スクリプトは IPv4 強制（curl -4 相当）で作ります。**

## ⚠ セキュリティ（お願い）
チャットに出てしまった **Threads App Secret はリセット**してください（ダッシュボード → Use cases → Threads → Settings →「Threads app secret」→ Reset/再生成）。
- リセットしても**今の60日トークンは有効なまま**（トークンの更新 `th_refresh_token` にも secret は不要）なので、**運用に支障はありません**。露出した secret を無効化するのが目的です。

---

## 次（Phase 1・2）
このまま進めてよければ:
1. **Phase 1**: 「発信記録」に **「Threads投稿一覧」シート新設**（承認済み列設計：投稿日時／permalink／本文／種類／文字数／画像URL／親投稿URL／**X投稿URL**／views／いいね／リプ／リポスト／引用／シェア／エンゲージ合計／各率／最終更新）
2. **Phase 2**: 取得スクリプト `scripts/fetch_threads_posts.py`（IPv4 強制・permalink 突合 upsert）を作成し、まず `--dry-run` で確認

Phase 1・2 に進めてよいですか？（シート新設＝スプレッドシートに見える変更が入るため確認します）

---

## よーん *(00:06 JST)*

進めて

### Claude *(00:07 JST)*

進めます。まず **Phase 1：「Threads投稿一覧」シート新設**。シート追加ツールを読み込みます。

*[ツール: `ToolSearch`]*

「Threads投稿一覧」シートを作成し、ヘッダー行を書き込みます。

*[ツール: `mcp__mcp-gsheets__sheets_insert_sheet`, `mcp__mcp-gsheets__sheets_update_values`]*

Phase 1 完了（「Threads投稿一覧」シート・ヘッダー作成）。次に **Phase 2：取得スクリプト** を作成します。

*[ツール: `Write`]*

まず `--dry-run` で取得だけ確認します（シート書き込みなし）。

*[ツール: `Bash`]*

17件取得・メトリクスも取れています。**本実行**（シートへ upsert）します。

*[ツール: `Bash`]*

書き込めました（17件追記）。**upsert が重複せず動くか**（再実行で新規0・更新17になるか）と、シート内容を確認します。

*[ツール: `Bash`]*

Upsert 正常（再実行で **新規0・既存17更新**＝重複しない）。シート内容を確認します。

*[ツール: `mcp__mcp-gsheets__sheets_get_values`]*

🎉 **Phase 1・2 完了・検証OK。** Threads 投稿がメトリクス付きでシートに入りました。

## 現状
- **「Threads投稿一覧」シート**作成（発信記録内）
- `scripts/fetch_threads_posts.py`（IPv4 固定・permalink 突合 upsert）作成
- **17件を取得・記録**（2026/03〜07）。本文・種類・文字数・画像URL・views・いいね・リプ・リポスト・引用・シェア・各率・最終更新 が入力済み
- **upsert 冪等性 確認**（再実行で 新規0・既存17更新＝重複なし）
- **H列「X投稿URL」は手動列**として空のまま（スクリプトは非上書き）

## 残り：Phase 3（自動化＋トークン更新）
1つ設計上のポイント：**トークン `gcp/threads_token.json` はローカル限定**（gitignore でクラウドに無い）なので、Phase 3 は**ローカル cron**で実装します（z01 のようなクラウド routine ではトークンを読めないため）。

提案:
- **日次取得**: `run_threads_fetch.sh`（`fetch_threads_posts.py` 実行）を **1日1回 cron**（メトリクスは増えるので毎日 upsert 更新）。時刻の希望は？（例: 毎朝 5:00）
- **トークン更新**: 60日失効対策に `th_refresh_token`（secret 不要）で延長する更新ジョブを **月1回 cron**。

この方針（ローカル cron・日次取得＋月次トークン更新）で進めてよいですか？ 取得の実行時刻だけ決めてください（未指定なら毎朝 5:00 にします）。

---
**⚠ 再掲（お願い）**: 露出した **Threads App Secret のリセット**を忘れずに（今のトークン・更新は secret 不要なので運用に影響しません）。

そして、この Threads 連携基盤の新規構築は完了後に `/record` で記録します。

---

## よーん *(00:17 JST)*

進めて。取得の実行時刻は、毎朝 5:00

### Claude *(00:18 JST)*

毎朝5:00 で進めます。Phase 3（日次取得 cron ＋ 月次トークン更新）を実装します。

まずトークン更新スクリプトと2つの cron ラッパーを作成します。

*[ツール: `Write`, `Write`, `Write`]*

crontab に登録し、日次取得ラッパーを1回テスト実行して確認します（トークン更新は発行24h以内だと拒否される仕様なので、動作確認は次回以降）。

*[ツール: `Bash`]*

🎉 **Threads 連携、全フェーズ完了しました。**

## 完成した仕組み
| 項目 | 内容 |
|---|---|
| 認証 | 長期トークン（60日）を `gcp/threads_token.json` に保存（Phase 0） |
| シート | 発信記録に **「Threads投稿一覧」**（19列・X投稿URL 手動列含む） |
| 取得 | `fetch_threads_posts.py`（IPv4固定・permalink 突合 upsert・17件取得済み） |
| 日次取得 | `run_threads_fetch.sh` を **毎朝5:00 cron**（テスト実行 rc=0 ✓） |
| トークン更新 | `run_threads_token_refresh.sh` を **月次 cron（1日4:00）**（`th_refresh_token`・secret 不要） |

crontab 登録済み:
```
0 5 * * * run_threads_fetch.sh          # 日次取得
0 4 1 * * run_threads_token_refresh.sh  # 月次トークン更新
```

これで毎朝、Threads の投稿一覧とメトリクス（views/いいね/リプ/リポスト/引用/シェア＋各率）が自動更新されます。X 投稿からコピペした場合は **H列「X投稿URL」に手動で元 X 投稿URLを記入**すれば、スクリプトはそれを保持します。

## ⚠ 残タスク（よーん側・1つだけ）
露出した **Threads App Secret のリセット**（ダッシュボード → Use cases → Threads → Settings →「Threads app secret」→ Reset）。今のトークン運用・更新は secret 不要なので**リセットしても影響なし**です。

---

この Threads 連携基盤の新規構築を `/record` で記録しますか？（新規ファイル: `fetch_threads_posts.py`・`threads_token_refresh.py`・`threads_token_exchange.py`・cron ラッパー2本／新設シート／cron 2本）

STEP 1・2 を実行します。

*[ツール: `Bash`]*

STEP 3: 未記録の変更候補を提案します。

---

**変更ログ候補（未記録）**

1. **Threads 投稿一覧の API 取得・記録基盤を新規構築** — Threads 公式 API（`graph.threads.net`）で自分の投稿一覧＋メトリクス（views/いいね/リプ/リポスト/引用/シェア）を取得し、発信記録の新設「Threads投稿一覧」シートへ permalink 突合で upsert する基盤を構築。OAuth 長期トークン（60日・`gcp/threads_token.json`）、IPv4 固定（VPS の IPv6 不通対策）、日次取得 cron（5:00）＋月次トークン更新 cron を整備。新規: `fetch_threads_posts.py`／`threads_token_refresh.py`／`threads_token_exchange.py`／`run_threads_fetch.sh`／`run_threads_token_refresh.sh`。
   - 関連コミット: 未コミット（作業ツリー）
   - 変更ファイル: `scripts/fetch_threads_posts.py`、`scripts/threads_token_refresh.py`、`scripts/threads_token_exchange.py`、`scripts/run_threads_fetch.sh`、`scripts/run_threads_token_refresh.sh`（＋新設シート・cron 2本）
   - 関連する過去の変更: なし（Threads 連携は新規）

補足: `logs/threads_fetch.log` はログなので通常コミット対象外（既存ログ運用に合わせます）。`gcp/threads_token.json` は gitignore 済みでコミットされません。

記録してよいですか？（番号「1」/ スキップ）

---

## よーん *(00:24 JST)*

1

### Claude *(00:24 JST)*

STEP 4: 報告書を作成します。

*[ツール: `Write`]*
