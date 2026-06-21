---
title: notebooklm_manager.py に SOCKS プロキシ経由オプションを追加（IP ブロック回避）
date: 2026-06-21
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260621_notebooklm_socks_proxy/)

## 背景・動機

この実行環境の IP が NotebookLM 側でブロックされており、`notebooklm_manager.py` が一切使えなくなっていた（`make-infographic` 等 NotebookLM 依存スキルも連鎖的に停止）。

一方、別の Windows server（IP: 133.18.136.38）からはブラウザで NotebookLM に正常アクセスできる。そこで、この Windows server を SSH 経由の SOCKS プロキシとして使い、`notebooklm_manager.py` の通信だけをその IP から出すことでブロックを回避する。

調査の結果、`notebooklm_manager.py`（`NotebookLMClient.from_storage`）の実行時通信は **ブラウザ（Playwright）ではなく `httpx` の HTTP リクエスト**で行われている（`vendor/notebooklm/_core.py`）ことが判明。Playwright は初回ログイン（`storage_state.json` 作成）時のみ使用。したがってリモートでブラウザを動かす必要はなく、httpx の出口を SOCKS プロキシに向けるだけでよい。

## 実施内容

- Windows server (133.18.136.38) へ `ssh -fND 1080` で SOCKS5 トンネルを張り、出口 IP が 133.18.136.38 になることを確認。
- `notebooklm_manager.py` に、環境変数 `NOTEBOOKLM_SOCKS_PROXY` が設定されていれば `httpx.AsyncClient` をローカル DNS の SOCKS トランスポートに差し替えるモンキーパッチを追加（vendored ライブラリ本体は非改変）。
- 依存ライブラリ `httpx-socks` / `python-socks` をインストール。

## 切り分けの記録（重要）

- httpx の SOCKS（`socks5://`）は **デフォルトでリモート DNS**（プロキシ側で名前解決）を使う。Windows OpenSSH の SOCKS はリモート DNS が機能せず `ConnectError` / タイムアウトになる。
- curl の native `socks5://`（ローカル DNS = IP で SOCKS 接続）は 302 で即成功 → 「ローカル DNS + IP 接続」なら確実に動く。
- `proxychains4` はローカル DNS 設定でも curl すら 45s タイムアウトで不採用。
- `httpx-socks` の `AsyncProxyTransport.from_url(..., rdns=False)`（ローカル DNS）で httpx からも 302 到達を確認 → これを採用。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_manager.py` | import 直後に `NOTEBOOKLM_SOCKS_PROXY` を読み、設定時は `httpx.AsyncClient` を `AsyncProxyTransport(rdns=False)` 付きに差し替えるモンキーパッチを追加 |

## 設計判断

- **vendored `_core.py` は触らず、`notebooklm_manager.py` 側でモンキーパッチ**：vendored ライブラリ更新で消えないようにするため。env 未設定時は従来通り（プロキシなし）で動作し既存挙動に影響なし。
- **`rdns=False`（ローカル DNS）必須**：Windows OpenSSH の SOCKS がリモート DNS 非対応のため。

## 確認結果

```bash
# トンネル（パスワード認証のためユーザーが ! で実行）
ssh -fND 1080 <user>@133.18.136.38
# 実行
NOTEBOOKLM_SOCKS_PROXY=socks5://127.0.0.1:1080 python3 scripts/notebooklm_manager.py list
```

→ NotebookLM のノートブック一覧を正常取得できることを確認。

## 今後の課題

- 依存 `httpx-socks` / `python-socks` は別環境（リモート routine 等）では別途インストールが必要。
- SSH トンネルは常駐だが永続ではない（環境再起動・回線断・SSH 切断で要張り直し）。毎回のパスワード入力をなくすには Windows 側への公開鍵登録（鍵認証）への移行が有効。
- `make-infographic` 等 NotebookLM 依存スキルから本 env を渡す運用の標準化は未実施。
