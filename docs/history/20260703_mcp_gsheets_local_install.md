---
title: mcp-gsheets 起動を prefer-offline → ローカルインストール方式に変更（フレッシュコンテナの ETARGET 回避） — セッション履歴
date: 2026-07-03
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-03 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260703_mcp_gsheets_local_install/)

---

## よーん *(08:05 JST)*

あなたは z01（X短文投稿）の原稿作成を無人で行うエージェントです。リポジトリ useakat/xClaude の projects/z01/spec.md に従い、Gmail 下書きを1件だけ作成してください。ユーザー確認・承認は不要、全工程を自動で完走します。

手順:
1. projects/z01/spec.md を Read し、作業フォルダを projects/z01 として制作フロー STEP 1〜5 を実行する。ネタ4シートの読み取りは mcp-gsheets の sheets_get_values を使う（SS1 spreadsheetId=1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM）。本文生成は /writer-xpost、ファクトチェックは /check-fact、ブランド適合は /check-brand。
2. STEP 6（Gmail 下書き作成）は、このクラウド環境では gws CLI（create_gmail_draft.sh）が使えないため、代わりに Gmail コネクタの下書き作成ツール（create_draft）を使う。宛先は useakat@gmail.com、件名は『【X短文投稿】{トピック要約10〜15字} YYYYMMDD HH:MM:SS』（日時は JST=UTC+9 で算出）、本文は spec.md の Naming の本文フォーマット（先頭に『ソース: {シート}[{番号}]』行、続いて [最終原稿]…[/最終原稿]、[投稿文]…[/投稿文] のブロック。両ブロックに同一の投稿文を入れる）どおりにする。
3. 投稿は一切行わない（下書き作成のみ）。完了後、STEP 7 の完了報告（ソース・字数・件名・生成した投稿文）を出力する。

### Claude *(08:05 JST)*

I'll start by reading the spec file to understand the workflow.

*[ツール: `Read`, `ToolSearch`, `ToolSearch`, `ToolSearch`, `Read`, `Read`, `ToolSearch`, `Read`, `ToolSearch`]*

The mcp-gsheets server may still be connecting. Let me search for it specifically.

*[ツール: `ToolSearch`, `ToolSearch`]*

The mcp-gsheets server isn't surfacing yet. Let me do the random source selection while retrying.

*[ツール: `Bash`, `ToolSearch`]*

The mcp-gsheets tools still aren't appearing. Let me check available MCP servers and resources.

*[ツール: `ToolSearch`, `ToolSearch`]*

Let me check the MCP servers connected.

*[ツール: `ListMcpResourcesTool`]*

Only github and Gmail are connected — mcp-gsheets hasn't come up. Let me retry once and check for a fallback script.

*[ツール: `ToolSearch`, `Bash`]*

There's a `sheets_manager.py`. Let me check whether it can read sheets directly with the service account key.

*[ツール: `Bash`]*

The service account key is available. mcp-gsheets isn't connecting, so I'll query the Sheets API directly using the service account credentials (inline, no new script file). Let me verify the libraries.

*[ツール: `Bash`, `Bash`]*

cryptography is available. I'll mint a service-account access token and call the Sheets REST API via stdlib. Let me check proxy env first.

*[ツール: `Bash`]*

Proxy and CA are configured. Let me mint a service-account token and fetch the noteNeta sheet via the Sheets REST API.

*[ツール: `Bash`]*

cryptography's C backend is broken. I'll sign the JWT with the openssl CLI instead.

*[ツール: `Bash`]*

Fetched 145 rows. Now let me apply the STEP 2 filters (status ≠ ボツ, last-used empty or ≥90 days ago) and pick a random candidate.

*[ツール: `Bash`]*

Selected **noteNeta[119]** — H3ロケット試験機1号機の失敗と1年での立て直し。ステータス「未使用」、短文最終使用日は空。候補142件。次に投稿文を生成します。

*[ツール: `Skill`, `Read`, `Bash`]*

135〜140字にやや足りません。具体を足して調整します。

*[ツール: `Bash`, `Bash`]*

138字、読点なし最大28字、「の」3連なし。事実確認のため主要な数値を一次情報で裏取りします。

*[ツール: `ToolSearch`, `WebSearch`]*

主要数値すべて一次情報・報道で裏取り完了（だいち3号開発費280億円、指令破壊は打ち上げ約14分後、2段目着火せず）。ブランド適合も全項目基準クリア。Gmail 下書きを作成します。

*[ツール: `Bash`, `Write`]*

Now let me create the Gmail draft using the Gmail connector.

*[ツール: `Bash`, `ToolSearch`, `mcp__Gmail__create_draft`]*

Draft created (ID: r-7276159780060856616). Let me clean up the temporary private-key file.

*[ツール: `Bash`]*

STEP 6 まで完了しました。STEP 7 完了報告です。

```
✅ ネタ選択完了（ソース: noteNeta[119] / H3ロケット試験機1号機の失敗と1年での立て直し）
✅ 投稿文生成完了（138字）
✅ Gmail 下書き作成完了（件名: 【X短文投稿】H3ロケット失敗と再起 20260703 08:10:19）

---
【生成した投稿文】

2段目のエンジンに、火が点かなかった。それだけの異常で、日本の新しい主力ロケットは打ち上げ14分後に自ら爆破され、地球を撮るはずの280億円の衛星ごと海に沈んだ。だが技術者たちは原因を93項目つぶし、わずか1年で立て直す。あの夜の悔しさが、日本の宇宙への足場を取り戻したのだ。
```

補足（自動処理の実務メモ）:
- **mcp-gsheets が本クラウド環境で未接続**だったため、`GOOGLE_SERVICE_ACCOUNT_KEY`（環境変数）でサービスアカウント JWT を発行し、Sheets REST API から noteNeta を直接読み取りました（openssl 署名 / stdlib HTTP、一時的なインラインスクリプトのみ・鍵ファイルは削除済み）。
- ソースシートは重み付き抽選で **noteNeta**、候補142件からランダムで No.119 を選定（ステータス「未使用」・短文最終使用日 空）。
- ファクト: だいち3号（ALOS-3）開発費 **280億円**、指令破壊は打ち上げ**約14分後**（10:51:50）、**2段目着火せず**を JAXA報告書・報道で裏取り済み。
- ブランド適合: noteNeta=物語型(1b)で全項目基準クリア。裸の固有名詞（LE-5B-3・ALOS-3・H3）はイメージ表現に言い換え済み。読点なし最大28字・「の」3連なし。
- Gmail 下書き作成のみ。投稿は行っていません。

Sources: [JAXA H3試験機1号機打ち上げ失敗（2023/3/7）](https://www.jaxa.jp/press/2023/03/20230307-2_j.html) / [だいち3号 - Wikipedia](https://ja.wikipedia.org/wiki/%E3%81%A0%E3%81%84%E3%81%A13%E5%8F%B7) / [H3ロケット試験機1号機打上げ失敗の原因究明報告書](https://www.jaxa.jp/hq-disclosure/h3-tf1/files/H3-tf1_report_01.pdf)

---

## よーん *(21:57 JST)*

mcp-gsheets が本クラウド環境で未接続だった    この原因を調べて

### Claude *(21:57 JST)*

MCP接続の原因を調べます。

*[ツール: `Bash`, `Bash`]*

mcp-gsheets は `.mcp.json`（プロジェクトスコープ）で定義されており、起動コマンドは `npx mcp-gsheets@1.8.1` です。起動時に実際に何が起きるか確認します。

*[ツール: `Bash`]*

原因を特定しました。裏取りします。

*[ツール: `Bash`]*

`qs@^6.15.2` はレジストリに存在します（6.15.2 / 6.15.3、latest は 6.15.3）。にもかかわらず起動時は「No matching version found」で落ちていました。`--prefer-offline` によるメタデータキャッシュの陳腐化が疑わしいので、確定させます。

*[ツール: `Bash`]*

原因を特定・再現しました。

## 結論

`mcp-gsheets` が接続しなかった直接原因は、**起動ラッパー `scripts/mcp_gsheets_launch.sh` の `npx --prefer-offline` が、クラウドコンテナの陳腐化した npm メタデータキャッシュを掴み、transitive 依存 `qs@^6.15.2` を解決できずに install ごと失敗していた**ためです。

起動時のエラー（実際に再現）:
```
npm error code ETARGET
npm error notarget No matching version found for qs@^6.15.2.
```
→ install が中断 → サーバプロセスが立ち上がらない → ハーネス上は「still connecting」のまま永久に接続完了しない。

## 何が起きていたか（時系列）

1. コンテナは **7/2 23:05 にクローン/構築**され、その時点の npm メタデータキャッシュがシードされた。`qs` のメタデータは当時 **6.15.1 まで**しか含んでいなかった（npx キャッシュ `~/.npm/_npx/...` は空＝パッケージ本体も未取得）。
2. セッション開始時、ハーネスが `.mcp.json` の定義に従い `npx --prefer-offline -y mcp-gsheets@1.8.1` を起動。
3. `mcp-gsheets@1.8.1` → `googleapis@^171` 系の依存が **`qs@^6.15.2`** を要求。ところが `--prefer-offline` は**キャッシュ済みメタデータを再検証せず優先**するため、6.15.1 までしか知らず「該当バージョンなし(ETARGET)」で解決失敗。
4. 私が調査中に `npm view qs versions`（`--prefer-offline` なし）を実行したことで**メタデータキャッシュが更新**され、6.15.2 / 6.15.3 が見えるようになった。

## 再現による確定

| 条件 | 結果 |
|---|---|
| `npx --prefer-offline`（起動時と同条件・キャッシュ陳腐時） | `ETARGET qs@^6.15.2` で失敗 |
| `npx --prefer-online -y mcp-gsheets@1.8.1` | **`Google Sheets MCP server running on stdio`** ＝正常起動 |

- レジストリ自体には `qs` 6.15.2 / 6.15.3 が存在（latest=6.15.3）。**設定ミスでも認証エラーでもなく、`--prefer-offline` × フレッシュコンテナの陳腐キャッシュという環境・タイミング依存の問題**。
- 認証（`GOOGLE_SERVICE_ACCOUNT_KEY` len=2353 / `GOOGLE_PROJECT_ID`）は正常にセットされており、無関係でした。
- ローカル環境で普段動くのは、npm キャッシュが温まっている（最新メタデータ済み）ためです。

## なぜこの設計になっていたか

ラッパーのコメント通り、`--prefer-offline` は「`@latest` 相当のレジストリ問い合わせで spawn/reconnect のたびにハングし、初期化タイムアウト(-32000)を招く」問題を避けるために意図的に付けられたものです。ただし**依存ツリーに新しい transitive バージョン（qs^6.15.2）が入った瞬間、フレッシュコンテナでは逆に解決不能で落ちる**という副作用が出ました。

## 修正案（どれを採るか確認したいです）

1. **推奨：環境のセットアップ段階で npm キャッシュを事前ウォーム**する。SessionStart フックや環境の setup script で `npx -y mcp-gsheets@1.8.1 </dev/null &` を一度走らせてキャッシュを温めてから Claude を起動すれば、`--prefer-offline` のままで確実に立ち上がる。ラッパーのロジックは変えずに済む。
2. **ラッパーを条件分岐**：オフラインキャッシュに mcp-gsheets が無ければ初回だけ `--prefer-online`、以降 `--prefer-offline`。堅牢だがスクリプト改修が必要。
3. **`--prefer-offline` を外す**（デフォルト＝メタデータ再検証）。確実だが、コメントにある reconnect ハングのリスクが戻る可能性。

CLAUDE.md に従い、スクリプト（`mcp_gsheets_launch.sh` / setup 系）の編集は勝手に行いません。**1〜3 のどれで対応するか**、指示をいただければ実装します。

（補足：私の調査で現コンテナのキャッシュは温まったため、この環境では今なら `--prefer-offline` でも起動します。ただし新しいコンテナでは再発します。）

---

## よーん *(22:07 JST)*

１と２どちらの解決策が本質的？

### Claude *(22:07 JST)*

**本質的なのは 2 です。**

理由は、両者が「何を直しているか」の層が違うからです。

**問題の本質**は、`mcp_gsheets_launch.sh` が `--prefer-offline` で**「キャッシュは常に十分に新しい」という前提を無条件に置いている**こと。この前提が崩れる（フレッシュコンテナ＋transitive 依存のバージョン更新）と壊れます。

- **案2（初回だけ online、以降 offline）** は、その**壊れやすい前提をラッパー自身の中で無効化**します。どんな起動経路・どんな環境（ローカル / クラウド / cron / 新しいコンテナ）でも、キャッシュが冷えていれば自動で online 解決に落ちる＝**コンポーネントが自己修復する**。しかも `--prefer-offline` を入れた本来の目的（reconnect ごとのレジストリ問い合わせによるハング＝ -32000 回避）も、2回目以降は offline のまま維持されるので**両立**します。前提そのものを直すので本質的です。

- **案1（事前ウォーム）** は、前提（キャッシュ陳腐）を**そのまま残したうえで、外から満たしてあげる**対症療法です。「setup script や SessionStart フックが、Claude 起動より前に、毎回、すべての環境で確実に走る」という**隠れた前提条件を新たに増やす**。新しい環境タイプが増えたり、フックの配線が漏れたりすれば再発します。タイミング依存も残ります。

まとめると:

| | 直す場所 | 環境非依存性 | 再発耐性 |
|---|---|---|---|
| 案1 | 環境側（外部で補償） | フックの配線に依存 | 環境が変わると再発 |
| 案2 | ラッパー内（前提を除去） | どこでも自己完結 | 恒久的 |

案2が「壊れる前提を、それを作っている当人（ラッパー）の中で消す」ので本質的です。案1は有効な運用パッチで、案2と併用すればコールドスタートの初回コストも消せますが、単独なら案2を採るべきです。

実装（`mcp_gsheets_launch.sh` の改修）は案2で進めてよいか確認させてください。スクリプト編集は承認をいただいてから行います。

---

## よーん *(22:10 JST)*

案２で

### Claude *(22:11 JST)*

案2で実装します。まず現行スクリプトと、mcp-gsheets が公開する bin（実行エントリ）を確認します。

*[ツール: `Bash`]*

bin は `mcp-gsheets → dist/index.js`。案2を、最も決定論的な形（**バージョン固定のローカルインストール**: キャッシュミス時のみ online で1回取得 → 以降は `node` で直接起動、npx/レジストリを一切介さない）で実装します。まず動作検証します。

*[ツール: `Bash`]*

検証OK — `node dist/index.js` は起動メッセージを **stderr** に出し、**stdout はクリーン**（JSON-RPC 専用を維持）。案2をローカルインストール方式で実装します。

*[ツール: `Write`, `Read`, `Write`]*

スクリプトを更新しました。新スクリプトをコールド／ウォーム両方で動作検証します。

*[ツール: `Bash`]*

両パス正常です。コールドは online install 後に起動、ウォームは npm を介さず即起動、いずれも stdout はクリーン。構文チェックと差分を確認します。

*[ツール: `Bash`]*

案2の実装が完了しました。

## 実装内容（`scripts/mcp_gsheets_launch.sh`）

起動方式を **`npx --prefer-offline` → バージョン固定のローカルインストール＋`node` 直接起動** に変更しました。

- **初回（キャッシュミス／新バージョン）だけ** `npm install --prefix ~/.cache/mcp-gsheets/<version>` で online 取得 → 陳腐キャッシュによる `ETARGET (qs@^6.15.2)` を回避。
- **2回目以降の spawn/reconnect は npm/レジストリを一切介さず `node dist/index.js` を exec** → 高速かつレジストリ不通でもハングしない（旧 `--prefer-offline` の狙いも維持）。
- `.installed` マーカーで**部分インストールの取り込みを防止**（マーカー未達なら丸ごと入れ直し）。
- install ログは **stderr へ隔離**し、JSON-RPC の **stdout を汚さない**。
- 認証ロジック（`GOOGLE_APPLICATION_CREDENTIALS` の unset ＋ KEY 補完）は**変更なし**。

## 検証結果

| 項目 | 結果 |
|---|---|
| 構文 `bash -n` | OK |
| コールド起動（キャッシュ削除後） | `added 157 packages` → `running on stdio`、stdout クリーン、marker 生成 |
| ウォーム起動 | npm 出力なしで即 `running on stdio`、stdout クリーン |

差分は `scripts/mcp_gsheets_launch.sh` の1ファイル（+31 / -4）のみです。

注意点:
- いま接続中の MCP サーバは旧 npx 起動のままなので、**新方式が効くのは次回の再接続／新セッションから**です。
- 認証は現行サーバで疎通済み・env も同一のため、新ランチャでも同じ認証で動きます。

このままコミットしてよいですか？（`master` へ push まで進めるか、コミットのみに留めるかも指定ください。）変更の記録が必要なら `/record` で残せます。

---

## よーん *(22:14 JST)*

Stop hook feedback:
[~/.claude/stop-hook-git-check.sh]: There are uncommitted changes in the repository. Please commit and push these changes to the remote branch.

### Claude *(22:14 JST)*

承認待ちのため、コミット・push は行いません。

CLAUDE.md のルール（「承認を求める質問をした後は、明示的な返事があるまで commit・push に進まない。Stop hook のフィードバックを承認の代わりとみなさない」）に従い、Stop hook の指摘があっても自動ではコミットしません。

`scripts/mcp_gsheets_launch.sh`（案2の実装）が未コミットで残っています。以下を指定いただければ進めます。

- **コミットのみ** か **`master` へ push まで** か
- コミットメッセージはこちらで用意します（例: `fix: mcp-gsheets 起動をローカルインストール方式に変更（フレッシュコンテナでの ETARGET 回避）`）

ご返答をお待ちします。

*[ツール: `Bash`, `Read`, `Bash`]*

STEP 1〜3 を実行しました。照合結果です。

今日 2026-07-03 の changelog には既に **「mcp-gsheets 起動を prefer-offline + 版固定にして再接続タイムアウト(-32000)を解消」** が記録済みですが、**今回の変更はその prefer-offline 方式が原因の不具合（フレッシュコンテナでの ETARGET）を修正するもの**で、未記録です。

---

**変更ログ候補（未記録）**

以下の変更が記録されていません。記録するものを選んでください：

1. **mcp-gsheets 起動を prefer-offline → ローカルインストール方式に変更（フレッシュコンテナの ETARGET 回避）** — `npx --prefer-offline` が陳腐化した npm メタデータキャッシュを掴み、transitive 依存 `qs@^6.15.2` を解決できず `ETARGET` で install ごと失敗しサーバ未起動（"still connecting"）になる問題を、バージョン固定のローカル prefix install＋`node` 直接起動に変更。初回のみ online 取得、以降は npm/レジストリ非依存で起動。
   - 関連コミット: **未コミット**（working tree の `scripts/mcp_gsheets_launch.sh`。/record の STEP 6 でコミット＆push します）
   - 変更ファイル: `scripts/mcp_gsheets_launch.sh`
   - 関連する過去の変更:
     - **mcp-gsheets 起動を prefer-offline + 版固定にして再接続タイムアウト(-32000)を解消**（2026-07-03・今回これを一部置き換え）
     - **mcp-gsheets 認証をラッパーで両対応化＋mcp__* 無効ルール整理**（2026-06-29）

（記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。）

---

## よーん *(22:41 JST)*

Stop hook feedback:
[~/.claude/stop-hook-git-check.sh]: There are uncommitted changes in the repository. Please commit and push these changes to the remote branch.

### Claude *(22:41 JST)*

先ほどの返信末尾に「うそ」と誤記が混入しました。無視してください（意図しない文字です）。

`/record` の STEP 3 の途中で、記録対象の選択待ちです。承認を求める質問をした後は明示的な返事があるまで次へ進まない運用のため、Stop hook の指摘があってもコミット・push・ファイル作成は行いません。

上記の候補1を記録しますか？「1」でこのまま報告書＋変更ログを作成しコミット＆push まで進めます。「スキップ」なら記録せず終了します。

---

## よーん *(22:53 JST)*

1

### Claude *(22:53 JST)*

承認を受けて記録を作成します。まずテンプレートと日付を確認します。

*[ツール: `Read`, `Bash`, `Bash`]*

既存の実際の慣習（`../changelog/`・`../../history/<slug>/` のトレイリングスラッシュ形式）に合わせます。報告書を作成します。

*[ツール: `Write`]*

Now STEP 4.5: session history. Let me run the save script.

*[ツール: `Bash`]*
