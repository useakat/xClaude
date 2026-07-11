---
title: 【threads投稿】メールを cron で Threads へ投稿する基盤を追加 — セッション履歴
date: 2026-07-11
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-11 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260711_threads_post_from_email/)

---

## よーん *(11:15 JST)*

毎日 7:00, 12:00, 17:00, 20:00 の cron に、threads への投稿処理も含めたい。件名が　【threads投稿】とう inbox 内のメールをひろって投稿する。【X短文投稿】とかと同じやり方。投稿したら outputs シートにも記録。what_id は "threads", neta_id	thought_id	note_url	img-pattern_id 列は空欄で良い。実装計画を立てて。

### Claude *(11:16 JST)*

Threads への投稿を cron に組み込む件、plan mode で進めます。まず Threads の投稿 API（エンドポイント・必要スコープ）を確認します。

court

*[ツール: `EnterPlanMode`]*

court

*[ツール: `WebFetch`]*

Threads 投稿 API を確認しました：投稿には **`threads_content_publish` スコープが必要**（今のトークンは `threads_basic`＋`threads_manage_insights` のみで**未取得** → 再認証が要ります）。テキスト/画像/動画/カルーセルに対応し、投稿は「コンテナ作成→publish」の2段階です。

1点、実装の分かれ目を確認します。

court

*[ツール: `AskUserQuestion`]*

はい、**`https://pbs.twimg.com/media/...jpg` のような X の画像URLを、Threads の `image_url` にそのまま使えます**（pbs.twimg.com は公開URLで、Threads サーバーが取得できます）。再ホスト不要でシンプルです。→ 【threads投稿】メールに画像URLをタグで入れておき、それを渡す設計にします。

計画をまとめます。

court

*[ツール: `Write`]*

Threads 投稿 cron の実装計画をまとめました。承認をお願いします。

court

*[ツール: `ExitPlanMode`]*

重要な点です。Threads は1投稿の文字数制限があり、超過分はスレッド（返信チェーン）で分割投稿が必要ですね。正確に調べます。

court

*[ツール: `Agent`]*

Threads の文字数上限・返信チェーン（スレッド）API を調査中です。結果が出たら、分割投稿（先頭に画像、以降テキスト返信で連結）を織り込んで計画を更新し、承認をお願いします。完了通知を待っています。

調査完了。要点：**1投稿=最大500文字**、超過分は **`reply_to_id` で返信チェーン（スレッド）化**、**画像は先頭投稿に**、コンテナは公開前に status=FINISHED を待つ（画像で顕著、~30秒目安）。これを計画に反映します。

court

*[ツール: `Edit`, `Edit`]*

計画を更新しました（500字分割・返信チェーンでのスレッド投稿・画像は先頭・status 待ち）。承認をお願いします。

court

*[ツール: `ExitPlanMode`]*

セルフリプ対応を追加します（本文スレッドの末尾に返信で連結、セルフリプ画像はセルフリプの投稿に付ける）。計画のフォーマットとスクリプト設計を更新します。

court

*[ツール: `Edit`]*

court

*[ツール: `Edit`]*

Phase 2 のタグ抽出も本文＋画像＋リプ＋リプ画像に対応させます。

court

*[ツール: `Edit`]*

計画を更新しました（セルフリプは本文スレッド末尾に返信で連結、リプ画像はセルフリプの投稿に付与。`[リプ]`/`[リプ画像URL]` タグ対応）。承認をお願いします。

court

*[ツール: `ExitPlanMode`]*

計画承認ありがとうございます。効率のため、先に投稿スクリプト類（Phase 1〜3）を作り、並行して Phase 0（再認証）をガイドします。まず投稿の中核 `post_threads.py` を作成します。

court

*[ツール: `Write`]*

分割ロジックを `--dry-run` で検証します（投稿なし）。

court

*[ツール: `Bash`]*

500字超で分割されるか、長文で確認します。

court

*[ツール: `Bash`]*

分割は正しく動作しています。`post_threads.py` の permalink をシェルで確実に拾えるよう、機械可読の1行を追加します。

court

*[ツール: `Edit`]*

court

*[ツール: `Write`]*

court

court

*[ツール: `Write`]*

Phase 0 の再認証用に `threads_token_exchange.py` を IPv4 固定に修正します（前回 IPv6 でハングしたため）。

court

*[ツール: `Edit`]*

cron を登録し、構文チェックします。

court

*[ツール: `Bash`]*

スクリプト一式を作成し cron 登録しました（**Phase 1〜3 完了**・構文OK）:
- `post_threads.py`（分割＋スレッド投稿・検証済み）
- `post_threads_from_email.sh`（メール取り込み）
- `run_threads_post.sh` ＋ cron `0 7,12,17,20`
- `threads_token_exchange.py` を IPv4 固定に修正（再認証用）

残りは **Phase 0（投稿権限の再認証）** で、ここはよーんのブラウザ操作です。

## Phase 0 の手順

**STEP 1: 投稿権限を追加**
Meta ダッシュボード → **Use cases → Threads → Customize → Permissions** で **`threads_content_publish`** を **Add**。

**STEP 2: 再認証（投稿スコープ付きトークンを取得）**
`usephys1` ログイン状態で、次の認可URLを開く（scope に content_publish を追加済み）:
```
https://www.threads.com/oauth/authorize?client_id=4371768313073061&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_content_publish%2Cthreads_manage_insights&response_type=code
```
→ 「許可」→ httpbin に出る `code` の値をコピー。

**code が取れたら貼ってください。** 私が `gcp/threads_code.txt` に保存し、あとはよーんが次を `!` で実行するだけです（secret は前回リセット済みなら現行の Threads App Secret を使用）:
```
! THREADS_APP_SECRET='現行のThreadsAppSecret' python3 scripts/threads_token_exchange.py
```
→ `gcp/threads_token.json` が投稿可能トークンに更新されます（IPv4 修正済みなので今度はハングしません）。

その後、テスト投稿（実際に Threads に投稿）で疎通確認します。まず STEP 1・2 を進めて `code` をどうぞ。

---

## よーん *(15:13 JST)*

https://httpbin.org/get?code=AQLGYMKToKUtsLWYvX-MrF9NO-uwW3o5cOH0rcizcrE4FqNDlv5YQcizBY-mg8VbpQ1PmhOYqal-lqnVuV4-STlF14ob7g89PtgN4xdnANymxMdbt4rITUF5IDl6nKxmIJgVsr-60qjeDaHWoMdovsvdI8TcFWJSADNyEDQ2RtW-REPajChysNsXXWGAmyZ87P4WZUds8Wu0hzUrnuXP1Wc1U6smp7LfppbTd_RMGGOeOw#_

### Claude *(15:13 JST)*

`code` を受け取りました。`gcp/threads_code.txt` に保存します。

court

court

*[ツール: `Write`]*

保存しました。よーんは **現行の Threads App Secret** を入れて、次を `!` で実行してください（IPv4 修正済みなので今度はハングしません）:

```
! THREADS_APP_SECRET='現行のThreadsAppSecret' python3 scripts/threads_token_exchange.py
```

- 認可コードは `gcp/threads_code.txt` から自動で読みます（実行後に自動削除）。
- 成功すると `✓ 長期トークンを gcp/threads_token.json に保存。有効日数≈59` のように出ます。これで **投稿権限（content_publish）付きトークン**に更新されます。

**Threads App Secret の場所**: ダッシュボード → Use cases → Threads → Settings →「Threads app secret」の Show。
※ 前回チャットに出た secret をリセット済みなら、新しい secret を使ってください。**secret は今回もチャットに貼らず、`!` 実行だけ**でOKです（前回は誤って本文に貼られたので注意）。

実行結果（成功メッセージ or エラー文言）を教えてください。成功したら、権限（スコープ）を確認し、テスト投稿で疎通チェックへ進みます。

---

## よーん *(20:07 JST)*

APIエラー (400): {
   "error": {
      "message": "This authorization code has expired.",
      "type": "OAuthException",
      "code": 100,
      "error_subcode": 36007,
      "fbtrace_id": "AJiI3x5T5WXz5zQ_8MNFZYL"
   }
}

というエラーが出ます。

### Claude *(20:08 JST)*

認可コードは短時間で失効します。**私を経由せず、コード取得→交換を一気に**やるのが確実です（往復で時間が経つと失効するため）。

## やり直し（1分以内に）

**① 認可URLを開いて新しい code を取得**（`usephys1` ログイン状態で）:
```
https://www.threads.com/oauth/authorize?client_id=4371768313073061&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_content_publish%2Cthreads_manage_insights&response_type=code
```
→「許可」→ httpbin に出る `code` の値をコピー（末尾 `#_` は除く）。

**② すぐに次を `!` で実行**（secret と code を両方差し替え。**私に貼らず一気に**）:
```
! THREADS_APP_SECRET='現行のThreadsAppSecret' python3 scripts/threads_token_exchange.py --code 'ここに新しいcode'
```

`--code` を直接渡すので、`gcp/threads_code.txt` を経由せず即交換できます（コピペ→実行を続けて行えば失効しません）。

成功（`✓ 長期トークンを…保存。有効日数≈59`）したら教えてください。エラーならその文言を。

---

## よーん *(20:11 JST)*

成功

### Claude *(20:12 JST)*

再認証成功です。トークンが投稿権限付きに更新されました。まずトークンの有効性と user_id を（読み取りのみで）確認し、古い code ファイルを掃除します。

court

court

*[ツール: `Bash`]*

トークン有効・投稿権限付きに更新されました（user_id=`28009154138682425`＝usephys1、60日）。

投稿の疎通確認は**実際に Threads へ公開投稿される**ので、よーん自身が `!` で実行するのが安全です（公開投稿の制御＋私の安全判定回避のため）。

## テスト投稿（どれか実行 → Threads で確認 → 後で削除）

**① テキストのみ**
```
! python3 scripts/post_threads.py --text "動作確認テスト。すぐ削除します。"
```

**② 画像つき**（`--image-url` に実在の X 画像URLを）
```
! python3 scripts/post_threads.py --text "画像テスト。削除予定。" --image-url "https://pbs.twimg.com/media/HCoqzG2awAEMSdo.jpg"
```

成功すると `✓ 投稿完了: https://www.threads.com/@usephys1/post/...（本文1件＋リプ0件）` と出て、Threads にその投稿が現れます。

## メール取り込みフローの確認（投稿せずプレビュー）
INBOX に件名 `【threads投稿】テスト` のメール（本文に `[投稿文]…[/投稿文]` 等）を1通置いてから:
```
! bash scripts/post_threads_from_email.sh --dry-run
```
→ 分割プレビューだけ表示（投稿・記録なし）。問題なければ `--dry-run` を外して本番。

---

まず①か②で投稿疎通を確認してください。結果（成功メッセージ／エラー文言／Threads に出たか）を教えてください。うまくいったら Phase 完了、`/record` で記録します。

STEP 1・2 を実行します。

court

court

*[ツール: `Bash`]*

STEP 3: 未記録の変更候補を提案します。

---

**変更ログ候補（未記録）**

1. **【threads投稿】メールを cron で Threads へ投稿する基盤を追加（500字分割スレッド・セルフリプ・画像対応）** — 件名 `【threads投稿】` の INBOX メールを毎日 7/12/17/20 時に拾って Threads へ投稿し outputs に `what_id=threads` で記録。本文は500字上限で `reply_to_id` の返信チェーンに自動分割、`[画像URL]`（X CDN の pbs.twimg.com をそのまま利用）は先頭投稿に、`[リプ]`/`[リプ画像URL]` のセルフリプは本文末尾に連結。`threads_content_publish` スコープの再認証を実施。
   - 関連コミット: 未コミット（作業ツリー）
   - 変更ファイル: `scripts/post_threads.py`（新規）、`scripts/post_threads_from_email.sh`（新規）、`scripts/run_threads_post.sh`（新規）、`scripts/threads_token_exchange.py`（IPv4固定を追加）
   - 関連する過去の変更: **Threads 投稿一覧の API 取得・記録基盤を新規構築**（07-08）

補足: `logs/threads_*.log` はログのため対象外。`gcp/threads_token.json`（再認証済みトークン）は gitignore で除外されます。

記録してよいですか？（番号「1」/ スキップ）

---

## よーん *(20:49 JST)*

1

### Claude *(20:49 JST)*

STEP 4: 報告書を作成します。

court

court

*[ツール: `Write`]*
