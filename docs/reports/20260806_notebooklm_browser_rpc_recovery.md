---
title: NotebookLM の Gemini 移行後の認証断をブラウザ内 RPC 方式で復旧（cookie 持ち出し廃止）
date: 2026-08-06
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260806_notebooklm_browser_rpc_recovery/)

## 背景・動機

W003 の画像生成中に `notebooklm_manager.py` が `Authentication expired or invalid ... WebLiteSignIn` で落ちた。
[2026-07-09 の復旧手順](../20260709_notebooklm_tunnel_recovery_hardening/) に従い、Windows server (133.18.136.38) で cookie を採り直して scp で取り込んだが、**何度やっても signin に飛ばされた**。

切り分けの結果、これは従来の「古い cookie が隠している」類の問題ではなく、**Google 側の仕様変更で従来方式そのものが成立しなくなった**ことが判明した。

**判明した二つの壁**

1. **ドメイン移行**：NotebookLM が Gemini の `notebook.google.com` に統合された。旧 `notebooklm.google.com` は新ドメインへリダイレクトされる。
2. **cookie が持ち出せない**（本質的な壁）：実物 Chrome（`channel="chrome"`）で新規ログインして採取した `storage_state.json` に、Google のセッション検証に必要な **`__Secure-1PSIDTS` / `__Secure-3PSIDTS`（ローテーション・トークン）が含まれない**。デバイスに紐づくセッション管理の挙動と整合する。

さらに従来の chromium 版 `nblogin.py` は、Google の自動化検知（`navigator.webdriver`）でログイン画面から先に進めず、**そもそも再ログインできない**状態だった。整理すると：

| 採取方法 | 新規ログイン | 1PSIDTS の書き出し | 結果 |
|---|---|---|---|
| 旧 chromium | ✗ 自動化ブロック | ○ | 古いトークンのまま signin |
| 実物 Chrome | ○ | ✗ | 新しくても signin |

つまり **「cookie をファイルに書き出して別プロセスの httpx で再生する」という前提が塞がれた**。再認証の繰り返しでは直らないため、方式そのものを変える必要があった。

## 実施内容

**可否判定（プローブ）**

ログイン済みブラウザ内なら通るはずと仮説を立て、判定用スクリプトで検証した。結果：

- 新ドメイン `notebook.google.com` では **signin に飛ばず**、`SNlM0e`(CSRF) / `FdrFJe`(session id) もページから取得できる
- ページ内 `fetch` からの `batchexecute(LIST_NOTEBOOKS)` が **HTTP 200・626KB** を返し、実際のノート名・ID が入っていた
- 旧ドメインからの fetch は別オリジンとなり CORS で失敗する（→ 新ドメインを使う必要がある）
- **ヘッドレス＋ssh で完走**したため、RDP なしで Claude 側から実行できる

**本実装（Deep Research を通す最小構成）**

cookie を書き出さず、**Windows のログイン済み Chrome の中から `batchexecute` を呼ぶ**方式に変更した。cookie はブラウザが自動付与するため 1PSIDTS 問題を根本回避できる。

- Windows 側に常駐サーバを置き、stdin/stdout の JSON 行プロトコルで fetch を代理実行（ブラウザ起動は1回だけ）
- この環境側は ssh 越しにそれを駆動。**RPC の符号化/復号・結果解析は `vendor/notebooklm` をそのまま再利用**し、差し替えたのは通信層のみ
- 併せて、実物 Chrome で自動化検知を回避してログインし直す `nblogin.py` を整備（`channel="chrome"` ＋ `--disable-blink-features=AutomationControlled`、ログイン後に NotebookLM を再ロードして OSID を再発行）

**途中で踏んだ問題**：Windows のコンソール既定が cp932 のため、応答 JSON に日本語やダッシュが含まれると `UnicodeEncodeError` で落ちた。サーバ側の標準入出力を UTF-8 に固定して解消。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_browser_bridge.py` | 新規。ssh 越しに Windows 常駐ブラウザを駆動する CLI。`BridgeCore` が `vendor/notebooklm` の `*API` クラスに `rpc_call` を提供し、解析ロジックを再利用。`list` / `create` / `deep-research` / `list-sources` を実装 |
| `scripts/windows/nbrpc_server.py` | 新規（Windows 配置用の控え）。ログイン済み Chrome を1回だけ開き、ページ内 `fetch` で `batchexecute` を代理実行。標準入出力は UTF-8 固定 |
| `scripts/windows/nblogin.py` | 新規（同上）。実物 Chrome で自動化検知を回避して再ログインし、ログイン後に NotebookLM を再ロードして OSID を再発行してから `storage_state` を保存 |

## 設計判断

**なぜ UI 自動操作ではなくブラウザ内 RPC にしたか**
画面のボタンを順に押す方式は、Gemini 移行のような UI 変更のたびに壊れる。エンドポイント（`wXbhsf` 等の RPC ID とパラメータ構造）は `vendor/notebooklm` に既知で、プローブで健在も確認できたため、**UI に依存しない RPC 直叩き**を選んだ。

**なぜ vendor を書き換えず通信層だけ差し替えたか**
Deep Research の応答解析（タスク状態・ソース配列・レポート抽出）は分岐が多く、移植するとバグの温床になる。`*API` クラスが必要とするのは `_core.rpc_call` と `_core.auth` だけと確認できたため、最小の `BridgeCore` を用意して**既存の解析コードをそのまま使う**構成にした。

**なぜ Deep Research だけに絞ったか（全コマンド移植をしなかった）**
W003 の運用で NotebookLM に必要なのは実質 Deep Research（ソース収集）のみで、画像生成は lovart に移行済み。全コマンド対応は工数が大きい割に効果が薄いため、小さく作って確実に戻すことを優先した。

## 確認結果

- `list` … ノート **128件** を取得
- `create` … ノート新規作成に成功（ID 返却）
- `deep-research` … クジラ心拍のテーマで完走。Deep Research の日本語レポートを生成
- `list-sources` … 取り込み後 **64件**。PNAS 原論文 "Extreme bradycardia and tachycardia in the world's largest animal"、Journal of Experimental Biology、Royal Society、Stanford など一次情報を含む
- いずれも **ヘッドレス＋ssh** で完走し、RDP 操作なしで実行できることを確認

## 今後の課題

- ~~`ask` / `add-source` / `infographic` などは旧方式のまま。必要になった時点で同じブリッジ上に追加する（画像生成は lovart で足りているため急がない）~~
  → **`ask` は 2026-08-09 に追加済み**（[報告書](../20260809_notebooklm_bridge_ask_command/)）。残るは `add-source` / `infographic` など
- ブラウザのログインセッション自体が切れた場合は、`scripts/windows/nblogin.py` を Windows 側で実行して再ログインする（cookie の scp 取り込みは**不要になった**）
- `notebooklm_reauth.md` は cookie 採取＋scp を前提とした旧手順のまま。運用が固まったら本方式に合わせて更新する
