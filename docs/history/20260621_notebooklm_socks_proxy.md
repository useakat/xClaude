---
title: notebooklm_manager.py に SOCKS プロキシ経由オプションを追加（IP ブロック回避） — セッション履歴
date: 2026-06-21
sidebar:
  hidden: true
---

# セッション履歴

> 2026-06-21 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260621_notebooklm_socks_proxy/)

---

## よーん *(08:43 JST)*

hello

この環境では IPアドレスでブロックされるのか、notebookLM にアクセスできません(notebooklm_manager.pyが使えない) 。別の windows server からなら、ブラウザでnotebookLM にアクセスできます。IP = 133.18.136.38。この notebookLM にアクセスするときは、この windows server を経由することはできますか？

hello

### Claude *(08:43 JST)*

結論から言うと、**可能です。** 方法は大きく2つあります。まず現状のスクリプトの作りを確認します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

調べました。結論と仕組みを説明します。

## 結論：可能です。しかも思ったより簡単です

重要な発見が1つあります。`notebooklm_manager.py`（＝`from_storage` で動く非同期クライアント）は、**ブラウザ（Playwright）を使っていません**。実際の操作はすべて `httpx` の HTTP リクエストで行われています（`vendor/notebooklm/_core.py:141`）。

- ブラウザ（Chromium）を使うのは **初回ログイン時だけ**（`storage_state.json` を作るとき）
- ネットワークでブロックされているのは、この HTTP リクエストが「この環境の IP」から出ているため

つまり **HTTP リクエストの出口を Windows server (133.18.136.38) に変えるだけ** で解決します。リモートでブラウザを動かす必要はありません。

## 推奨方法：SSH で SOCKS プロキシを張る

httpx はデフォルトで `trust_env=True`（プロキシ環境変数を尊重）なので、**コード改修ゼロ** でいけます。

```bash
# 1. この環境から Windows server 経由の SOCKS プロキシを作る
ssh -fND 1080 <windowsのユーザー名>@133.18.136.38

# 2. httpx に SOCKS サポートを入れる（未導入の場合）
pip install "httpx[socks]"

# 3. 出口を Windows IP に向けて実行
export ALL_PROXY=socks5://127.0.0.1:1080
python scripts/notebooklm_manager.py list
```

これで NotebookLM への通信が 133.18.136.38 から出るようになり、ブロックを回避できます。

## 必要な前提（よーん側で確認が必要な点）

1. **Windows server に OpenSSH サーバーが立っているか**（Windows 10/11・Server なら「オプション機能」で有効化可能）。この環境から `ssh ...@133.18.136.38` で入れればOK。
2. **`storage_state.json`（認証）が有効か**。これは別問題で、もし期限切れなら Windows 側のブラウザで一度ログインして `storage_state.json` を作り、この環境にコピーする必要があります。

## 代替案

SSH が使えない場合は、**Windows server 上で `notebooklm_manager.py` を直接動かす**方法もあります（Python + `playwright install chromium` + `vendor/notebooklm` 一式をコピー）。ただし常時 NotebookLM を使うワークフロー（`make-infographic` 等）との連携を考えると、プロキシ方式のほうが既存スクリプトをそのまま使えて筋が良いです。

---

まず **Windows server に SSH で入れるか** を試すのが最短の確認です。`ssh <user>@133.18.136.38` が通るか、試せますか？ 通れば上記手順で動かせます。

---

## よーん *(10:13 JST)*

ssh ログインはできました

### Claude *(10:14 JST)*

SSH が通ったので、プロキシを張ってテストします。まず接続情報を確認します。

*[ツール: `Bash`]*

SOCKS サポートがないので入れます。あわせて接続情報を教えてください。

`socksio` をインストールします:

*[ツール: `Bash`]*

インストールを進めつつ、トンネルを張るのに必要な情報を確認させてください。

*[ツール: `AskUserQuestion`, `Bash`]*

`socksio` 入りました。パスワード認証なので、トンネルを張る ssh コマンドは**よーん自身が実行する必要があります**（私が実行するとパスワード入力で止まるため）。

以下を、プロンプトに `!` を付けて実行してください（`<user>` は Windows のログインユーザー名に置き換え）:

```
! ssh -fND 1080 <user>@133.18.136.38
```

- `-f` でパスワード入力後に自動でバックグラウンドに回ります
- 127.0.0.1:1080 に SOCKS5 プロキシが立ち、通信が 133.18.136.38 から出るようになります

実行してパスワードを入れたら教えてください。こちらで `ALL_PROXY=socks5://127.0.0.1:1080` を付けて `notebooklm_manager.py list` の疎通を確認します。

（毎回パスワードを打つのが面倒なら、後で鍵認証を一度だけ設定すれば、以降は私がトンネル張り直しまで自動でできるようになります。まずは疎通確認を優先しましょう。）

---

## よーん *(11:19 JST)*

パスワードいれてログインした

### Claude *(11:19 JST)*

トンネルが張れたか確認して、NotebookLM への疎通をテストします。

*[ツール: `Bash`]*

トンネル成功です。プロキシ経由だと出口 IP が `133.18.136.38`（Windows server）になっています。NotebookLM の疎通を確認します。

*[ツール: `Bash`]*

疎通の途中（TLS 確立時）でこけました。プロキシ自体は生きている（ipify は通った）ので、対象ホストへの到達を切り分けます。

*[ツール: `Bash`]*

プロキシ経由で notebooklm には届いています（302）が、挙動が不安定です。原因を切り分けます。httpx の SOCKS はデフォルトで**リモート DNS**（プロキシ側で名前解決）を使い、それが Windows 側でタイムアウトしている可能性が高いです。

*[ツール: `Bash`]*

原因が特定できました。**httpx の SOCKS はリモート DNS（Windows 側で名前解決）を使い、それがこのプロキシで失敗しています**（curl もリモート DNS の `socks5h` だけ失敗、ローカル DNS の `socks5` は 302 で成功）。

対策は「ローカルで名前解決させて IP で SOCKS 接続する」ことです。`proxychains` を使うのが確実です。

*[ツール: `Bash`, `Bash`]*

proxychains4 が入りました。ローカル DNS にする設定ファイルを作ります（`proxy_dns` を無効化）。

*[ツール: `Write`, `Bash`]*

ConnectTimeout に変わりました（proxychains 経由で接続自体は試みている）。proxychains が async ソケットと相性問題を起こしている可能性があります。proxychains 自体が機能しているかを curl（同期ソケット）で切り分けます。

*[ツール: `Bash`]*

proxychains は curl でもタイムアウトするので（45s）使えません。一方、**curl の native `socks5://`（ローカル DNS）は 302 で即成功**しています。つまり「ローカル DNS + IP で SOCKS 接続」なら確実に動く、ということです。

httpx をこの挙動（ローカル DNS = `rdns=False`）にできれば解決します。`httpx-socks` で検証します（まだファイルは作らず、インラインで確認）。

*[ツール: `Bash`, `Bash`]*

**解決策が確定しました。** `httpx` をローカル DNS の SOCKS トランスポート（`rdns=False`）にすると `notebooklm.google.com` へ 302 で到達できました。

## まとめ（原因と対策）

- **原因**: Windows OpenSSH の SOCKS プロキシは「リモート DNS（プロキシ側で名前解決）」が動かない。httpx はデフォルトでリモート DNS を使うため失敗していた。
- **対策**: ローカルで名前解決させ、IP で SOCKS 接続する（curl の `socks5://` と同じ挙動）。`httpx-socks` の `rdns=False` で実現可能と検証済み。

## 提案する変更（要・承認）

`scripts/notebooklm_manager.py` の冒頭に、**環境変数 `NOTEBOOKLM_SOCKS_PROXY` が設定されていれば httpx をローカル DNS の SOCKS 経由にする**モンキーパッチを追加します（数行）。vendored ライブラリ本体は触らないので、将来の更新で壊れません。

変更後の使い方:

```bash
# 1. トンネル（よーんが ! で実行・パスワード入力）
! ssh -fND 1080 <user>@133.18.136.38

# 2. プロキシ指定で実行（普段通りのコマンドに env を足すだけ）
NOTEBOOKLM_SOCKS_PROXY=socks5://127.0.0.1:1080 python3 scripts/notebooklm_manager.py list
```

`make-infographic` 等の他スキルからも、この env を付ければそのまま使えます。

この内容で `scripts/notebooklm_manager.py` を編集してよいですか？（スクリプト編集なので確認しています）

---

## よーん *(11:37 JST)*

トンネル（よーんが ! で実行・パスワード入力）　は、1回だけやればいいの？

### Claude *(11:37 JST)*

いいえ、「コマンド実行ごと」ではなく「トンネルが生きている間ずっと」使えますが、**永続ではありません**。

`ssh -fND` はバックグラウンドの常駐プロセスです。一度張れば、その後の `notebooklm_manager.py` 実行は何回でもそのトンネルを使い回せます。ただし以下のときは切れるので、張り直しが必要です:

- この環境（マシン/コンテナ）を再起動・停止したとき
- ネットワークが切れたり、Windows 側の SSH が接続を落としたとき
- プロセスを kill したとき

つまり「セッション中はだいたい1回でOK、落ちたら張り直し」です。

確認方法（生きてれば再実行不要）:
```bash
ss -ltn | grep 1080      # 1080 が LISTEN なら生きている
```

毎回パスワードを打つのが面倒なら、対策が2つあります:

1. **鍵認証を一度だけ設定**（推奨）— Windows 側に公開鍵を1回登録すれば、以降はパスワード不要。落ちても私が自動で張り直せるようになります。
2. **自動再接続**（`autossh` 等）— 切れたら自動で復活させる。

まずは今の方式（手動トンネル＋スクリプト編集）で動かして、運用が固まったら鍵認証に移行するのがおすすめです。

スクリプト編集を進めてよいですか？

---

## よーん *(11:39 JST)*

お願いします

### Claude *(11:39 JST)*

了解しました。`scripts/notebooklm_manager.py` を編集します。

*[ツール: `Read`, `Edit`]*

編集できました。実際に `list` で動作確認します。

*[ツール: `Bash`]*

動きました。NotebookLM のノートブック一覧が Windows server (133.18.136.38) 経由で取得できています。これで `notebooklm_manager.py` がこの環境から使えます。

## 確定した使い方

```bash
# トンネルが落ちていたら張り直し（よーんが ! で・パスワード入力）
! ssh -fND 1080 <user>@133.18.136.38

# 実行（env を付けるだけ。make-infographic 等の他スキルも同様）
NOTEBOOKLM_SOCKS_PROXY=socks5://127.0.0.1:1080 python3 scripts/notebooklm_manager.py list
```

## 補足

- 依存ライブラリ `httpx-socks` / `python-socks` をこの環境に入れました（`pip install`）。別環境（リモート routine 等）で使う場合は同様にインストールが必要です。
- env を付けなければ従来通り（プロキシなし）で動くので、既存の動作には影響しません。

---

この変更を記録しますか？`/record` で記録できます。あわせて、毎回のパスワード入力をなくす**鍵認証の設定**も希望があればやります（Windows 側に公開鍵を1回登録するだけ）。

STEP 1・STEP 2 を実行します。

*[ツール: `Read`]*

STEP 2 を実行します。

*[ツール: `Bash`]*

STEP 3: 未記録の変更候補を提案します。

---

**変更ログ候補（未記録）**

今回のセッションの変更（まだコミットされていない作業ツリーの変更）が未記録です:

1. **notebooklm_manager.py に SOCKS プロキシ経由オプションを追加（IP ブロック回避）** — この環境が NotebookLM から IP ブロックされる問題を、SSH 経由の SOCKS プロキシ（別 Windows server 経由）で回避。`NOTEBOOKLM_SOCKS_PROXY` 環境変数があれば httpx をローカル DNS（`rdns=False`）の SOCKS トランスポートに切り替える。Windows OpenSSH の SOCKS はリモート DNS が動かないため `rdns=False` が必須という切り分け結果も記録。
   - 関連コミット: 未コミット（作業ツリー）
   - 変更ファイル: `scripts/notebooklm_manager.py`、`scripts/proxychains_notebooklm.conf`（不採用設定・削除候補）
   - 関連する過去の変更: なし

補足: `scripts/proxychains_notebooklm.conf` は検証過程で作って不採用になったファイルです。**記録前に削除してよいですか？**（削除はよーん確認のルールのため）

記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。

---

## よーん *(11:43 JST)*

1を記録。scripts/proxychains_notebooklm.confは削除OK

### Claude *(11:43 JST)*

不採用ファイルを削除し、記録を進めます。

*[ツール: `Bash`, `Read`]*

STEP 4: 報告書を作成します。

*[ツール: `Write`]*
