---
title: NotebookLM ブリッジに排他ロックと異常終了時の後始末を追加
date: 2026-08-11
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md#2026-08-11) ｜ [セッション履歴→](../../history/20260811_notebooklm_bridge_lock_cleanup/)

## 背景・動機

[OOM 解消の修正](./20260811_notebooklm_bridge_ask_oom_fix/)（同日）を検証する過程で、「空応答に見える失敗」が別の2経路からも起きていることが判明した。

1. **並行実行の衝突**：SOHO 記事の裏取り作業中、実際に別セッションが `check-fact-lim`（別 notebook 宛）を同時実行しており、稼働中だったブラウザセッションが `Target page, context or browser has been closed` で落ちていた。ブリッジは Windows 側の単一 Chrome プロファイルを前提としており、複数セッションが同時に使うと必ず衝突する。
2. **異常終了後のロック残留**：OOM（SIGKILL）や `timeout` コマンドによる強制終了時、リモートの Chrome プロセスが後始末されずに残り、次回起動が `Lock file can not be created! Error code: 32` で失敗する。8/9 の報告書には対処として `taskkill /IM chrome.exe /F` の手動実行が書かれていたが、これはプロセス名の一括 kill のため、稼働中の別セッションを巻き添えにする副作用があった（今回まさにこの経路で1件 OOM が発生していたことを `dmesg` で確認）。

## 実施内容

- **排他ロック（`SessionLock`）**：`flock` ベースのロックファイル（`/tmp/notebooklm_bridge.lock`）でブリッジ利用を直列化。先客がいれば最大20分（環境変数で変更可）待機する。`flock` はプロセス消滅時に OS が自動解放するため、OOM や SIGKILL で異常終了してもロックが残らない。
- **異常終了時の後始末**：
  - `SIGTERM`/`SIGINT`/`SIGHUP` のハンドラを追加し、`timeout(1)` コマンドや Ctrl-C による中断でもリモートプロセスを終了させる。`nbrpc_server.py` の起動時応答（`ready`）に自 PID を追加し、`taskkill /F /PID <pid> /T` で**自分が起動したプロセスだけ**を木ごと終了する（プロセス名一括 kill と異なり他セッションを巻き込まない）。
  - `SIGKILL`（OOM 等、ハンドラごと消える異常終了）で後始末できなかった場合に備え、次回起動時にプロファイルロックのエラー文言（`Lock file can not be created` 等）を検知したら自動的に `taskkill /IM chrome.exe /F` → 再試行するフォールバックを追加した。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_browser_bridge.py` | `SessionLock` クラス新設・シグナルハンドラ追加・起動失敗時の自動掃除＋再試行・`BridgeError` に詳細情報（detail）を追加 |
| `scripts/nbrpc_server.py` | 起動時の `ready` 応答に自 PID（`pid`）を追加 |

## 設計判断

- **プロセス名一括 kill をやめ PID 指定にした**：`taskkill /IM chrome.exe /F` は環境内の全 Chrome を落とすため、正常な並行作業（存在しないはずだが）や他セッションの復旧試行と衝突する。PID を明示することで自分のプロセスだけを対象にできる。
- **ロックは flock、ヘルスチェックは行わない**：ロックファイルへの書き込み内容（PID）は診断用のみで、生死判定には使わない。`flock` の OS レベル解放に任せることで、デッドロック検知ロジックを自前で書く必要がなくなった。
- **自動掃除は起動失敗時のみ発動**：常時ヘルスチェックで掃除すると、正常に稼働中の別セッションを誤検知で落とすリスクがある。「このプロセス自身が起動を試みて失敗した」ときだけ掃除することで、安全側に倒した。

## 確認結果

すべて実機（Windows 側 Chrome・ssh 経由）で検証：

- **通常動作**：`list` が133件取得、終了後の残留 Chrome プロセス 0 を確認
- **SIGTERM 中断**（fetch 実行中に送信）：ハンドラ発火 → PID 指定でリモート終了 → 残留 Chrome 0（20秒で完了）
- **SIGKILL 後の自動復旧**：OOM 相当の SIGKILL で残留 Chrome 8プロセスを作った状態から、次コマンド実行時に自動検知（`Lock file can not be created` 相当）→ 掃除 → 再試行が16秒で完了し、正常に応答を得た
- **並行実行**：2セッションを5秒差で起動したところ、2つ目が「他セッションがブリッジ使用中。空くまで待機します…」を出して待機し、1つ目の完了後に開始（衝突なし、合計68秒で両方完了）

## 今後の課題

- ロック待機の上限（20分）に達した場合の挙動は未検証（理論上は `BridgeError` で終了するのみ）
- Windows 側のディスク容量・メモリ不足など、Chrome プロセス以外が原因の起動失敗は今回のフォールバック対象外
