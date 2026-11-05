---
title: 公開前の漏えい対策：履歴から秘密情報と IP を除去し、SSH 接続先を環境変数化
date: 2026-11-05
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261105_security_history_scrub/)

## 背景・動機

リポジトリ公開前の確認で、外部から 2 点の指摘を受けた。

- `scripts/notebooklm_browser_bridge.py` に Windows サーバーの SSH 接続先（`ユーザー@IP`）が直書きされている
- スプレッドシート ID と Drive フォルダ ID がファイルに入っている

調査の過程で、指摘より深刻な問題が見つかった。

- vim のスワップファイル `.env.swp` が git で追跡されており、X API・LINE・xAI・note セッション等の実キー／トークンが入っていた
- 最初のコミットには `.env` と `.env~` も含まれていた
- 調査時点で GitHub 上のリポジトリは PUBLIC 設定だった（フォーク 0・スター 0）
- 接続先 IP（Windows サーバーと踏み台 VPS の 2 つ）は、スクリプトのほか docs・チャット履歴など追跡下の 18 ファイルに書かれていた

ファイルの追跡を外すだけでは過去のコミットに残るため、履歴から消す必要があった。

## 実施内容

- **追跡解除と再発防止**: `.env.swp` と `.onePointBuzzFeature.txt.swp` を `git rm --cached` で追跡解除し、`.gitignore` に `*.swp` / `*.swo` を追加
- **履歴の書き換え**: 書き換え用に作った mirror clone で `git filter-repo` を実行
  - `.env` / `.env~` / `.env.swp` を全履歴から削除
  - `--replace-text` で 2 つの IP を `<WINDOWS_SERVER_IP>` / `<踏み台VPS_IP>` に置換
  - コミット数 1995 → 1945
- **force push**: 209 ブランチをブランチごとの `--force-with-lease` で書き換え後の履歴に差し替え
  - Claude Code の自動モードの分類器が force push をブロックしたため、よーんが手元で実行
  - 1 回目はコピー時に混入した余分な文字で refspec が不正となり、push が 1 件も実行されないまま失敗。リモート無変更を確認して再実行
- **SSH 接続先の環境変数化**
  - `notebooklm_browser_bridge.py`: `NOTEBOOKLM_SSH_HOST` を `.env` / 環境変数から読む（python-dotenv）。未設定なら `BridgeError` で停止
  - `notebooklm_tunnel.sh`: `NOTEBOOKLM_TUNNEL_SSH_HOST` を環境変数または `.env` から読む。未設定なら異常終了。出口 IP の照合値はこの変数から導出
- **許可ルールの移動**: `.claude/settings.json` の IP 入り ssh 許可ルールを削除し、リポジトリ外の `~/.claude/settings.json` に移した
- **docs 内の IP の置換**: docs・チャット履歴の IP をプレースホルダに置換（履歴と同じ置換を作業ツリーにも反映）
- **ID 類の判断**: スプレッドシート 4 件・Drive フォルダ 4 件・Drive ファイル ID 16 件の共有設定を確認し、いずれもリンク共有ではなかったため置換せず現状維持とした（1 件は削除済みか参照不可で状態を確認できなかったが、docs 内の記述のみ）
- **ローカルの整合**: `git reset --mixed` で書き換え後の履歴に揃え（作業ツリーは保持）、旧履歴を指していたローカル専用ブランチ 2 本と古い stash を削除、reflog expire と `git gc --prune=now` で旧オブジェクトを消去
  - 2 本のブランチの中身はネタ候補 10 行の追加だけで、Sheets に既存だったことを確認してから削除

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_browser_bridge.py` | SSH 接続先の直書きを `NOTEBOOKLM_SSH_HOST` の参照に変更。python-dotenv で `.env` を読み、未設定なら `BridgeError` |
| `scripts/notebooklm_tunnel.sh` | `NOTEBOOKLM_TUNNEL_SSH_HOST` を環境変数／`.env` から取得。未設定なら異常終了。出口 IP の照合値は変数から導出 |
| `.gitignore` | `*.swp` / `*.swo` を追加 |
| `.claude/settings.json` | IP 入りの ssh 許可ルールを削除 |
| `.onePointBuzzFeature.txt.swp` | 追跡解除（ファイルはローカルに残る） |
| （git 履歴） | `.env` / `.env~` / `.env.swp` の削除と IP の置換（209 ブランチを force push） |
| `~/.claude/settings.json`（リポジトリ外） | 削除した ssh 許可ルールを移動 |
| `.env`（ローカル・gitignore 済み） | `NOTEBOOKLM_SSH_HOST` / `NOTEBOOKLM_TUNNEL_SSH_HOST` を追記 |

## 設計判断

- **mirror clone で書き換えた**: `git filter-repo` は最後に作業ツリーを hard reset するため、未コミットの作業がある本体では実行しなかった。書き換え後に本体を `git reset --mixed` で合わせ、作業ツリーを保った
- **IP は行を消さずプレースホルダに置換した**: 過去の報告書やチャット履歴が読めなくなるのを避けるため
- **環境変数を 2 つに分けた**: ブリッジ（Windows サーバー）とトンネル（踏み台）で接続先・ユーザーが異なる。Python 側は python-dotenv、シェル側は `.env` の grep で読む
- **許可ルールは環境変数で書けない**: `permissions.allow` は環境変数を展開できず、IP を含むルールは公開リポジトリに置けない。`.claude/settings.local.json` は git 追跡下なので不適で、リポジトリ外の `~/.claude/settings.json` に置いた。このルールはこの端末にだけ存在する
- **スプレッドシート ID／Drive ID は秘密ではないと判断した**: ID だけでは中身に入れず、アクセスは共有設定で決まる。リンク共有が無いことを確認して現状維持とした
- **他の環境の対応は不要と判断した**: 他に使う環境は routine だけで、実行ごとに新規 clone するため、旧履歴を再 push する恐れがない

## 確認結果

- 書き換え後のリモートの heads は 209 本で、書き換え済みの mirror と全件一致（master も一致）
- 書き換え後の全オブジェクトで IP の残存は 0 行。3 つのパスの履歴も 0 件
- 各ブランチの先端は、削除・置換したファイルを除いて書き換え前と同一
- ブリッジ: モジュールの読み込みと、未設定時のエラー経路を確認
- トンネル: `bash -n` で構文確認、環境変数と `.env` からの変数解決を確認
- ローカル: 旧初回コミットは存在せず、`git log --all -- .env .env.swp` は 0 件。到達不能オブジェクトも 0 件
- GitHub 側: **旧初回コミットは API から今も取得でき、`refs/pull/1〜14/head` の 14 本すべてに `.env.swp` が残っている**（2026-11-05 に読み取り API で確認）。force push では `refs/pull/*` を書き換えられないため

## 今後の課題

1. **キーのローテーション（保留中・最優先）**: X API・LINE・xAI・note セッション・OAuth クライアントシークレット等を再発行する。上のとおり旧データは GitHub から今も取得でき、公開されていた間に第三者が取得していた場合は取り戻せない。履歴の書き換えだけでは対策にならない
2. **GitHub Support への削除依頼（保留中）**: `refs/pull/1〜14` と旧コミットのキャッシュ・到達不能オブジェクトの削除を依頼する。削除されれば、旧初回コミットを API で引いて 404 になることで確認できる
   - 代替案はリポジトリの作り直し。旧データは即座に消えるが、14 本の PR と Actions・Pages 等の設定を失う
3. **再発防止の検討**: 秘密のコミット検知（pre-commit のシークレットスキャン等）は未導入
4. **小さな残件**: `scripts/__pycache__` の pyc が追跡下に残っている。また、置換した docs・チャット履歴のうち未追跡の 3 ファイル（他セッションの作業中）は、置換のみで未コミット
