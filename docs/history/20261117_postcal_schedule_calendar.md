---
title: X 投稿の予約カレンダー Web アプリ（postcal）を新設し、cron 4 枠の最優先キューにする — セッション履歴
date: 2026-11-17
sidebar:
  hidden: true
---

# セッション履歴

> 2026-11-15〜17 のセッション作業ログ。

← [報告書へ戻る](../../reports/20261117_postcal_schedule_calendar/)

---

## よーん *(21:16 JST)*

Xの日々の投稿を予約するためのweb アプリを作ってほしい。要件は以下の通り

* 投稿文、画像・動画、セルフリプ、投稿種類（短文、長文、自己研鑽、自己開示、フォロワー感謝、販促）を、投稿したい日時で登録できる（時間は、現在 cron が実行される 6:00, 12:00, 17:00, 20:00 限定で良い）
* 投稿はXと同時に threads にも自動投稿される
* セルフリプにある note記事へのリンクは、投稿する際に転送サイトを使ったURLに適切に変換される
* カレンダー表示で、その日になんの投稿が何時に予約されているかが見れる。また、そこからも投稿を予約登録できる


現行の gmail の inbox にある投稿文をXや threads に自動投稿するスクリプトを使い回せると良い

実装計画を立てて

### Claude *(21:16 JST)*

*[ツール: `Read`]*

The existing plan is for a different, completed task. I'll start fresh and explore the current posting pipeline first.

*[ツール: `Agent`, `Agent`, `Agent`]*

3 本の探索エージェント（投稿パイプライン・note リンク転送の仕組み・サーバー基盤）を並走させています。結果が揃ったら設計に入ります。

note リンクの転送変換は `post_to_x.py` に既にあり（投稿時に `xpost.usephys.net` へ書き換え）、Threads 側だけ未対応と分かりました。残り 2 本の探索結果を待ちます。

*[ツール: `Bash`, `AskUserQuestion`, `AskUserQuestion`, `Read`, `Read`, `Bash`, `Agent`, `Write`]*

計画の初稿を書きました。検証エージェント（tweepy の動画アップロード・Threads VIDEO・Caddy 構文・不足パッケージ）の結果を待って、修正を反映してから提示します。

*[ツール: `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `ToolSearch`, `ExitPlanMode`, `Read`, `Read`, `Read`, `Bash`, `Write`, `Write`, `Write`, `Write`, `Write`, `Write`, `Write`, `Write`, `Write`, `Write`]*

Web アプリ本体を書きました。次に投稿ランナーと既存スクリプトの拡張をまとめて行います。

*[ツール: `Write`, `Write`, `Bash`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Edit`, `Write`]*

All files are written. Now I'll run the checks: syntax, dry-runs, the Caddyfile preview, and a local app smoke test.

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

実装と動作確認が終わりました。systemd のサービスは起動済みで、ローカル（127.0.0.1:8787）で応答しています。

## 作ったもの

| ファイル | 内容 |
|---|---|
| `postcal/app.py` `db.py` `kinds.py` `templates/` `static/` | Web アプリ本体（Starlette + SQLite）。月カレンダー、日セルの「＋」から登録、編集・削除、同一日・同一枠の重複拒否、画像 4 枚 / 動画 1 本のアップロード、`/m/<uuid>` でメディア公開配信 |
| `scripts/post_scheduled.py` | 枠ランナー。予約を原子的に確保 → `post_to_x.py` → セルフリプを返信チェーン → `record_output.py` → Threads 転載（note リンク入りの段は除外）→ 状態更新。失敗はメール通知。rc 0/20/1 |
| `scripts/post_to_x.py` | `--image` を複数可（最大 4）、`--video` 追加（チャンクアップロード・処理失敗の検知・5 分上限）。既存の呼び出しと出力は不変 |
| `scripts/post_threads.py` | `--video-url` / `--reply-video-url` 追加。動画コンテナは 300 秒待ち。画像と動画の混在カルーセル可 |
| `run_xonepoint/question/xlong/xshort_post.sh` | 先頭で `post_scheduled.py <枠>` を呼び、予約が無ければ従来の Gmail キューへ |
| `scripts/redirect_build.py` `redirect/redirects.json` | `proxies` を追加。`post.usephys.net` を Basic 認証付き reverse_proxy として生成（`/m/*` だけ認証なし）。`.env` の `POSTCAL_BASIC_AUTH` が無ければ apply を中断 |
| `postcal/postcal.service` `scripts/postcal_install.sh` | systemd ユニットと配備スクリプト |
| `.gitignore` `docs/workflows/x-auto-post.md` | `postcal/data/` を除外。枠の処理順を更新 |

## 確認したこと

- ローカル起動で登録 → カレンダー表示 → 同枠重複は 400 → 編集（種類変更・画像削除）→ 削除、`/m/<uuid>.png` が `image/png` で取れる
- `post_scheduled.py 20 --dry-run`：X 本文（画像付き）→ リプ 2 段の返信チェーン → 記録（`W007`・`postcal[1]`・note_url）→ Threads（note リンク入りの段 1 つを除外）の順でコマンド列が出る。予約の無い枠は rc=20
- `post_to_x.py --dry-run` で複数画像と note リンク変換、`post_threads.py --dry-run` で画像＋動画のカルーセル判定
- 生成した Caddyfile（ハッシュをダミーに置換）が `caddy validate` を通過
- `systemctl enable --now postcal` 済み。`/healthz` が 200

## よーんにお願いしたいこと（公開に必要）

1. パスワードを決めて、VPS で次を実行し、出力を `.env` に 1 行追加してください（単引用符で囲む）
   ```
   caddy hash-password --plaintext '<パスワード>'
   ```
   ```
   POSTCAL_BASIC_AUTH='yohn:$2a$14$…（上の出力）'
   ```
2. Cloudflare に A レコード `post.usephys.net → 133.18.181.39`（プロキシ OFF）を追加
3. 両方できたら `bash scripts/postcal_install.sh` を実行（私が実行してもかまいません。言ってください）。これで Caddy に反映され、`https://post.usephys.net/` が開けます

それまでは `ssh -L 8787:localhost:8787 root@133.18.181.39` で `http://localhost:8787/` から試せます。

実投稿の確認は、よーんがテスト用の予約を 1 件登録し、その枠の cron 実行後に outputs シートと カレンダーの「投稿済み」を見る手順です（CLAUDE.md により私は投稿しません）。

変更ファイル（上の表の 16 ファイル。`docs/skills/*.md` の自動再生成分は含めません）を commit & push（master）してよいですか？

---

## よーん *(22:11 JST)*

.env ってどこにあるの？

### Claude *(22:12 JST)*

*[ツール: `Bash`]*

リポジトリの直下にあります。

```
/root/xClaude/.env
```

X の API キーや LINE トークンなど 27 個の設定が入っている既存ファイルで、git 管理外（`.gitignore` 済み）です。VPS 上で次のように末尾に追記してください。

```
cd /root/xClaude
caddy hash-password --plaintext '<パスワード>'
echo "POSTCAL_BASIC_AUTH='yohn:<上の出力>'" >> .env
```

パスワードを教えていただければ、ハッシュ化と追記を私が行うこともできます。その場合はこのチャットに平文が残るので、ご自身で実行する方が安全です。

---

## よーん *(23:01 JST)*

どうやって Aレコードを追加するんだっけ？

### Claude *(23:01 JST)*

*[ツール: `Bash`, `Bash`, `Bash`]*

以前 `xpost` / `tpost` を作ったときと同じ手順です（10 月の記録 `docs/reports/20261004_usephys_redirect_tracking.md` に残っています）。今 `post.usephys.net` は未登録で、`xpost` と `tpost` は VPS を指しています。

1. https://dash.cloudflare.com にログイン
2. ドメイン一覧から `usephys.net` を選ぶ
3. 左メニュー「DNS」→「レコード」→「レコードを追加」
4. 次のとおり入力して保存

| 項目 | 値 |
|---|---|
| タイプ | A |
| 名前 | `post` |
| IPv4 アドレス | `133.18.181.39` |
| プロキシ状態 | **オフ（DNS のみ・灰色の雲）** |
| TTL | 自動 |

プロキシ（オレンジの雲）がオンだと Caddy が証明書を取れないので、必ず灰色にしてください。

追加後、1〜2 分で反映されます。VPS で次を実行して IP が返れば完了です。

```
dig +short A post.usephys.net
```

反映を確認できたら教えてください。`.env` の `POSTCAL_BASIC_AUTH` と合わせて揃えば、`bash scripts/postcal_install.sh` を実行して公開します。

---

## よーん *(23:08 JST)*

IPが還らない

### Claude *(23:08 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

Cloudflare 側の登録は正しくできています。原因は VPS 側の DNS キャッシュです。

- Cloudflare の権威サーバーと 1.1.1.1 は `post.usephys.net → 133.18.181.39` を返しています
- VPS が使っている ISP の DNS サーバー 2 台のうち 1 台が、レコード追加前に私が確認した時の「存在しない」という結果を約 20 分間キャッシュしています（ネガティブキャッシュ）
- もう 1 台はすでに正しい IP を返しています

何もしなくても約 20 分で消えます。VPS で解決できるようになるまで 1 分おきに監視するジョブを裏で回しているので、通れば知らせます。

その間に `.env` への `POSTCAL_BASIC_AUTH` の追記を進めてもらえると、監視が通った時点で `bash scripts/postcal_install.sh` をすぐ実行できます。追記が済んだら、または私に実行してほしいなら教えてください。

---

## よーん *(23:14 JST)*

POSTCAL_BASIC_AUTH の追記はした

### Claude *(23:14 JST)*

*[ツール: `Bash`, `SendFeedback`]*

追記は入っていましたが、ハッシュが壊れています。原因は私が示したコマンドの引用符です。

`.env` の値を読むと、ユーザー名 `yohn` は正しいものの、ハッシュが 30 文字で `a4.OQZ…` から始まっています。正しい bcrypt ハッシュは 60 文字で `$2a$14$` から始まります。私が案内した `echo "…"` は二重引用符だったため、シェルが `$2a` `$14` `$…` を変数として展開し、先頭部分が消えました。申し訳ありません。

直し方は 2 つあります。どちらか選んでください。

**A. ハッシュをこのチャットに貼る**
VPS で `caddy hash-password --plaintext '<パスワード>'` をもう一度実行し、出力された `$2a$14$…` の 60 文字をそのまま貼ってください。私が `.env` の該当行を Edit ツールで書き直します。ハッシュからパスワードは復元できないので、貼っても問題ありません。

**B. 自分で直す**
VPS で次を実行してください。`"$(…)"` の中身は再展開されないので、今回は `$` が残ります。

```
cd /root/xClaude
sed -i '/^POSTCAL_BASIC_AUTH=/d' .env
printf "POSTCAL_BASIC_AUTH='yohn:%s'\n" "$(caddy hash-password --plaintext '<パスワード>')" >> .env
grep -c '^POSTCAL_BASIC_AUTH=.yohn:\$2a\$' .env
```

最後の行が `1` と出れば正しく入っています。

DNS はまだ ISP 側のキャッシュが残っていて VPS からは解決できません。裏で監視を続けています。

---

## よーん *(23:16 JST)*

直した

### Claude *(23:16 JST)*

*[ツール: `Bash`, `Bash`]*

`.env` は正しく入りました（`yohn` / `$2a$14$` から始まる 60 文字）。

DNS は ISP 側のキャッシュがあと約 15 分残っています。監視ジョブが通ったら、そのまま `bash scripts/postcal_install.sh` を実行して Caddy に反映してよいですか？ 内容は systemd ユニットの再インストール（すでに稼働中なので実質変化なし）と Caddyfile の再生成・reload です。既存の `xpost` / `tpost` の転送はそのまま残ります。

---

## よーん *(23:17 JST)*

監視ジョブが通ったら、そのまま bash scripts/postcal_install.sh を実行して Caddy に反映してよい

### Claude *(23:17 JST)*

承知しました。DNS が通った時点で `postcal_install.sh` を実行し、結果を報告します。あと 15 分ほどお待ちください。

*[ツール: `Bash`]*

DNS が通りました。承認済みの `postcal_install.sh` を実行します。

*[ツール: `Bash`, `Bash`]*

公開できました。`https://post.usephys.net/` が使えます。

| 確認項目 | 結果 |
|---|---|
| `https://post.usephys.net/`（認証なし） | 401（Basic 認証を要求） |
| `/m/…`（メディア配信・認証なし） | 認証なしで通過（存在しないファイルは 404） |
| TLS 証明書 | Let's Encrypt 発行済み（2027-01-02 まで、自動更新） |
| 既存の転送 6 ホスト（`xpost` `tpost` など） | そのまま反映、変化なし |
| systemd `postcal` | 稼働中（昨日 21:48 から） |

ブラウザで開くとユーザー名 `yohn` と決めたパスワードを聞かれます。スマホでも同じです。

残っているのは次の 2 点です。

1. **commit & push** 前回お聞きした postcal 関連 16 ファイルの commit & push（master）の可否をまだいただいていません。よければ「commit して」と言ってください。他セッションの変更は含めません
2. **実投稿の確認** カレンダーからテスト用の予約を 1 件登録してください。その枠の cron 実行後に、outputs シートの X 行・Threads 行とカレンダーの「投稿済み」表示を確認して `/record` します

---

## よーん *(08:12 JST)*

commit

### Claude *(08:12 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

master に push しました（コミット `f36f7e1`、postcal 関連 22 ファイル。他セッションの未コミット変更は含めていません）。push 前に別セッションの日報コミット 1 件を取り込んで rebase しています。

これで postcal の実装・配備・コミットはすべて完了です。

残りは実投稿の確認だけです。`https://post.usephys.net/` でテスト用の予約を 1 件登録してください。その枠の cron が走った後に、outputs シートの X 行（what_id と `postcal[id]`）と Threads 行（x_url 付き）、カレンダーの「投稿済み」表示を確認し、問題なければ `/record` で記録します。投稿後に教えてください。

---

## よーん *(08:14 JST)*

ログインできない

### Claude *(08:14 JST)*

*[ツール: `Bash`, `Bash`]*

設定側は一致しています。`.env` のハッシュと Caddy に読み込まれているハッシュは同一で、ユーザー名も `yohn` です。ログを見ると iPad から 2 回、認証情報付きでアクセスがあり、どちらも 401 でした。つまり入力した ID かパスワードがハッシュと合っていません。

よくある原因は 2 つです。

- **iPad の自動大文字化** ユーザー名欄で先頭が `Yohn` になっている。大文字小文字は区別されます。ユーザー名が小文字の `yohn` になっているか確認してください
- **ハッシュ化したときの文字列と違う** `caddy hash-password` に渡したパスワードに `'` や `$` などの記号が入っていて、シェルで一部が変わった可能性があります

パスワードをチャットに出さずに確認するには、VPS で次を実行してください。`200` なら正しい組み合わせ、`401` なら不一致です。

```
curl -s -o /dev/null -w '%{http_code}\n' -u 'yohn:<パスワード>' https://post.usephys.net/healthz
```

ここで 401 が出るなら、ハッシュ側が意図と違う文字列から作られています。その場合は前回の B の手順でハッシュを作り直し、終わったら教えてください。私が `redirect_build.py --apply` で Caddy に再反映します。

---

## よーん *(20:46 JST)*

ハッシュには　$2a$　は含まない？

### Claude *(20:46 JST)*

含みます。`caddy hash-password` の出力 60 文字（`$2a$14$` から始まる全体）がハッシュで、今の `.env` にはそれが正しく入っています。

ただし、**ブラウザのパスワード欄に入れるのはハッシュではなく、元の平文パスワード**です。`caddy hash-password --plaintext '<パスワード>'` の `<パスワード>` に入れた文字列そのものを打ってください。ハッシュを貼ると 401 になります。

| 場所 | 入れるもの |
|---|---|
| `.env` の `POSTCAL_BASIC_AUTH` | `yohn:$2a$14$…`（ハッシュ） |
| ブラウザのユーザー名欄 | `yohn`（小文字） |
| ブラウザのパスワード欄 | 平文パスワード |

---

## よーん *(20:48 JST)*

ハッシュを作り直した。反映して

### Claude *(20:48 JST)*

*[ツール: `Bash`, `Bash`, `Bash`]*

新しいハッシュは反映できませんでした。`.env` に追記された行が、またシェルの展開で壊れていたためです。

起きたこと:

- `.env` に `POSTCAL_BASIC_AUTH` が 2 行ありました。47 行目は前回のハッシュ（形式は正常）、48 行目が今回追記した行で、値が `yohn:a4` の 2 文字だけになっていました。`$2a$14$…` の `$` がシェルに食われています
- その壊れた値で Caddyfile を生成したため検証に失敗しました。稼働中の Caddy は古い設定で動き続けていたので、サイトは止まっていません
- 壊れた 48 行目を削除し（削除前の `.env` は `/root/.env.bak_postcal` に保存）、前回のハッシュで Caddyfile を再生成・reload しました。Caddy は正常に戻っています

次はシェルを通さずに入れたいので、**ハッシュをこのチャットに貼ってください**。VPS で次を実行し、出力の `$2a$14$` から始まる 60 文字をそのまま貼ってもらえれば、私が Edit ツールで `.env` を書き換えて Caddy に反映します。ハッシュからパスワードは復元できないので貼って問題ありません。

```
caddy hash-password --plaintext '<パスワード>'
```

パスワードに `'`（シングルクォート）が含まれていると上のコマンド自体も崩れます。その場合は `--plaintext` を付けずに実行すると、対話式にパスワードを聞かれるので、そちらが安全です。

```
caddy hash-password
```

---

## よーん *(20:53 JST)*

$2a$14$<ハッシュ 53 文字・履歴では伏せ字>

### Claude *(20:53 JST)*

*[ツール: `Bash`]*

反映しました。`.env` の `POSTCAL_BASIC_AUTH` を貼っていただいたハッシュに書き換え、Caddyfile を再生成して検証を通し、reload 済みです。稼働中の設定にこのハッシュが入っていることも確認しました。

`https://post.usephys.net/` を開き、ユーザー名 `yohn`（小文字）と、このハッシュを作ったときの平文パスワードでログインしてください。iPad は前回の失敗した認証情報を記憶していることがあるので、入らなければ Safari のタブを閉じて開き直すか、プライベートブラウズで試してください。

ログインできたら、テスト用の予約を 1 件登録してください。その枠の cron 実行後に outputs シートとカレンダーの表示を確認し、`/record` で記録します。

---

## よーん *(21:11 JST)*

投稿の種類に、ワンポイント解説(W003)　を追加して

### Claude *(21:11 JST)*

*[ツール: `Bash`]*

The form reads the kinds table dynamically, so one edit to `kinds.py` and a service restart is enough. I'll add it after 短文 and before 長文.

*[ツール: `Edit`, `Bash`]*

追加しました。登録フォームの「種類」に `ワンポイント解説（W003）` が短文と長文の間に出ます。サービスを再起動済みで、ブラウザを再読み込みすれば選べます。

変更は `postcal/kinds.py` の 1 行です。この 1 ファイルを commit & push（master）してよいですか？

---

## よーん *(21:15 JST)*

commit push

### Claude *(21:15 JST)*

*[ツール: `Bash`]*

master に push しました（コミット `42905ef`、`postcal/kinds.py` のみ）。

次は実投稿の確認です。カレンダーからテスト用の予約を 1 件登録し、その枠の cron が走ったら教えてください。outputs シートの X 行・Threads 行とカレンダーの「投稿済み」表示を確認して `/record` で記録します。
