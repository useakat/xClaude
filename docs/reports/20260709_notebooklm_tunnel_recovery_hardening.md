---
title: NotebookLM トンネル復旧＋恒久ハードニング（Administrator ロックアウト／古い認証ファイルの二重根本原因を解消）
date: 2026-07-09
tags: [infra, bugfix]
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260709_notebooklm_tunnel_recovery_hardening/)

## 背景・動機

この環境の IP は NotebookLM にブロックされているため、Windows server (133.18.136.38) 経由の SSH SOCKS トンネルで `notebooklm_manager.py` の通信だけを別 IP から出している（[2026-06-21 の SOCKS プロキシ導入](../20260621_notebooklm_socks_proxy/)）。

ある日この経路が壊れ、`manager` が一切使えなくなった。トンネルの SSH が **認証フェーズに入った瞬間に `Connection reset`** され、張り直しても再現。「サービス起動の sshd だけ落ちる／手動デバッグ起動(`sshd -d`)は成功」という食い違いで、当初は Windows sshd の不具合と誤認しかけた。過去は動いていた以上これは回帰であり、腰を据えて根本原因を突き止めた。

## 真因（二段構え）

**真因1：Administrator アカウントのロックアウト。**
サービス sshd は認証後に対象ユーザのログオントークンを S4U（`LsaLogonUser`）で生成する。サーバの DEBUG ログに `generate_s4u_user_token: LsaLogonUser() failed ... Status: 0xC0000234`（= `STATUS_ACCOUNT_LOCKED_OUT`）→ `fatal: ga_init, unable to resolve user administrator` が出ており、**Administrator がロックアウトされていてトークン生成に失敗**していた。デバッグ起動(`-d`)は実行中の対話トークンを使うため S4U を通らず成功していた。ロック元は公開 IP への SMB(445) 総当たり（`Failed password ... Too many authentication failures`）。ロックアウト方針はしきい値10・期間10分で、2〜4分おきに再ロックされ続けていた。

**真因2：古い認証ファイルが新 cookie を隠していた。**
トンネル復旧後も `manager` が signin(`WebLiteSignIn`) に飛ばされ続けた。切り分けの結果、`_storage_path()` は「既定ファイル `~/.notebooklm/storage_state.json` が存在するなら gcp を使わない」ロジックで、**4/23 の古い既定ファイルが残っていて、新しく採取した cookie（`gcp/notebooklm_storage_state.json`）を隠していた**。古い cookie を読むため signin になっていた。

## 実施内容

### トンネル復旧
- Windows sshd を DEBUG ログ(`LogLevel DEBUG3` + `SyslogFacility LOCAL0`)化し、サービス本体の失敗理由を `C:\ProgramData\ssh\logs\sshd.log` で直接特定。
- ロックアウトを無効化（`net accounts /lockoutthreshold:0`）し Administrator を解除。以後 S4U トークン生成が成功し、認証 reset が解消。

### 恒久ハードニング
- **トンネル専用の非管理者ユーザ `nbtunnel` を新設**（鍵認証・パスワードは自動生成で未使用）。総当たりの的になる Administrator を露出させない。プロファイル未作成でホームが `C:\WINDOWS` にフォールバックする問題は、`sshd_config` の `Match User nbtunnel` で `AuthorizedKeysFile C:\ProgramData\ssh\nbtunnel_authorized_keys` を明示して回避。
- `scripts/notebooklm_tunnel.sh` の接続先を `Administrator@…` → `nbtunnel@…` に変更。
- ファイアウォールで **SSH(22)=この環境の IP のみ / SMB(445,139)=遮断 / RDP(3389)=踏み台 VPS(94.26.88.123) のみ** に制限。

### cookie 運用の確立
- cookie は **出口 IP と一致する Windows サーバ側で採取**する（別 IP・headless だと signin に飛ぶ）。Windows に Python + notebooklm-py 0.3.4 + Playwright chromium を導入し、CLI の `login` がリダイレクト競合でクラッシュするため、永続プロファイルから `storage_state` を保存する小さな Playwright スニペットで採取。
- 採取した `storage_state.json` を SSH(scp) でこの環境の `gcp/notebooklm_storage_state.json` に転送（値はチャットに出さない）。
- 新 cookie を隠していた古い `~/.notebooklm/storage_state.json` を `.old-20260423.bak` に退避し、`gcp/` を正にした。env なしで `manager list` が対象 notebook を含め正常取得することを確認。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_tunnel.sh` | SSH 接続先を `Administrator@133.18.136.38` → `nbtunnel@133.18.136.38` に変更 |
| （Windows サーバ側） | ローカルユーザ `nbtunnel` 新設＋鍵登録、`sshd_config` に `Match User nbtunnel`、ファイアウォール（SSH/SMB/RDP 制限）、`net accounts /lockoutthreshold:0` |
| `~/.notebooklm/storage_state.json`（この環境） | 4/23 の古い版を `.old-20260423.bak` に退避（`gcp/` を認証の正とするため） |

## 確認結果

- `nbtunnel` で SSH ログイン成功（`NBTUNNEL_OK`）、トンネル経由の出口 IP = 133.18.136.38 を確認。
- Windows 採取 cookie（51個）を転送後、env なしで `python3 scripts/notebooklm_manager.py list`（`NOTEBOOKLM_SOCKS_PROXY` のみ）が **118 notebook を取得**、対象の共有 notebook `945dd10a`（ケプラー K2）も一覧に表示されることを確認。

## 今後の課題

- cookie は静的エクスポートのため、期限や Google 側の失効で再度 signin になり得る。その場合は **Windows サーバ側で再採取 → scp で `gcp/` を更新**する（`~/.notebooklm/` に古い既定ファイルを残さないこと）。
- トンネルが落ちたら `bash scripts/notebooklm_tunnel.sh --restart`（`nbtunnel` 鍵認証のため Claude 側で自動復旧可能）。
- ロックアウト無効化は総当たりを無制限に許すため、SSH/SMB/RDP のファイアウォール制限と Administrator の強固なパスワードが前提。
