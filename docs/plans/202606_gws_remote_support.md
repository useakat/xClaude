---
title: gws CLI リモート対応実装計画
date: 2026-06-06
status: pending
---

## 背景

`gws` CLI（Gmail・Drive・Sheets 操作）はローカルでのみ動作しており、リモートセッション（claude.ai/code の cloud VM）では以下の理由で使えない：

1. **バイナリなし** — リモート VM に `gws`（`@googleworkspace/cli`）がインストールされていない
2. **OAuth 認証情報なし** — ローカルの `~/.config/gws/` はリモートには存在しない
3. **リモートは毎回クリーン** — 永続化の仕組みがないと起動のたびに消える

現状の回避策：
- Gmail → `mcp__Gmail__*` MCP ツール
- Drive（ダウンロード） → `drivemcp_get_remote.sh`（Drive MCP ツール）
- Drive（アップロード） → 手段なし
- Sheets → `mcp__mcp-gsheets__*` MCP ツール（今回修正済み）

---

## 目標

SessionStart フックで gws を自動セットアップし、リモートでも `scripts/*.sh` の gws ベーススクリプトをそのまま動かせるようにする。

---

## アーキテクチャ

```
SessionStart フック（セッション開始時に自動実行）
  ├── 1. gws バイナリをインストール（npm）
  └── 2. OAuth 認証情報を env vars から復元（~/.config/gws/）
```

認証情報の永続化場所：**クラウド環境変数 UI**（platform env vars）

ローカル → env vars への登録は初回のみ手動。以降はフックが自動復元する。

---

## 実装ステップ

### STEP 1：ローカルで認証情報を調査・エクスポートする（手動・一回限り）

ローカルで実行：

```bash
ls -la ~/.config/gws/
```

期待されるファイル構成：

| ファイル | 内容 |
|---------|------|
| `client_secret.json` | OAuth クライアント ID・シークレット |
| `accounts.json` | 登録アカウント一覧 |
| `credentials.<b64-email>.enc` | 暗号化された OAuth トークン（アカウント毎） |

各ファイルを base64 エンコードして env vars に登録する：

```bash
# エンコード（ローカルで実行）
base64 -w0 ~/.config/gws/client_secret.json
base64 -w0 ~/.config/gws/accounts.json
base64 -w0 ~/.config/gws/credentials.*.enc  # ファイル名も記録
```

**登録する env vars（claude.ai/code の Environments > Variables）：**

| 変数名 | 内容 |
|--------|------|
| `GWS_CLIENT_SECRET_B64` | client_secret.json の base64 |
| `GWS_ACCOUNTS_JSON_B64` | accounts.json の base64 |
| `GWS_CREDENTIALS_ENC_B64` | credentials.*.enc の base64 |
| `GWS_CREDENTIALS_FILENAME` | credentials ファイルのファイル名（例：`credentials.eW9...dA==.enc`） |

### STEP 2：SessionStart フックを追加する（`.claude/settings.json`）

```json
{
  "type": "command",
  "command": "bash /home/user/xClaude/scripts/setup_gws_remote.sh",
  "async": true
}
```

### STEP 3：`scripts/setup_gws_remote.sh` を新規作成する

```bash
#!/bin/bash
# gws CLI のリモートセットアップスクリプト
# SessionStart フックから呼ばれる（ローカルでは何もしない）

# すでに gws が使える場合はスキップ
which gws >/dev/null 2>&1 && exit 0

echo "[gws-setup] gws not found. Setting up for remote session..." >&2

# 1. gws バイナリをインストール
npm install -g @googleworkspace/cli@0.11.1 --silent
if ! which gws >/dev/null 2>&1; then
  echo "[gws-setup] ERROR: npm install failed" >&2
  exit 1
fi

# 2. 認証情報 env vars が設定されているか確認
if [ -z "$GWS_CLIENT_SECRET_B64" ] || [ -z "$GWS_ACCOUNTS_JSON_B64" ] || [ -z "$GWS_CREDENTIALS_ENC_B64" ]; then
  echo "[gws-setup] WARNING: GWS_* env vars not set. Skipping credential restore." >&2
  exit 0
fi

# 3. ~/.config/gws/ に認証情報を復元
mkdir -p ~/.config/gws
echo "$GWS_CLIENT_SECRET_B64" | base64 -d > ~/.config/gws/client_secret.json
echo "$GWS_ACCOUNTS_JSON_B64" | base64 -d > ~/.config/gws/accounts.json
echo "$GWS_CREDENTIALS_ENC_B64" | base64 -d > ~/.config/gws/${GWS_CREDENTIALS_FILENAME}

echo "[gws-setup] Done." >&2
```

### STEP 4：動作確認

リモートセッションで以下を確認：

```bash
gws auth status          # 認証済みと表示されるか
bash scripts/check_auth.sh   # gws ✅ OK と表示されるか
```

---

## リスクと対策

### リスク 1：`credentials.enc` がシステム固有の鍵で暗号化されている場合

gws は OS のキーリング（macOS Keychain / Linux Secret Service）で credentials を暗号化することがある。その場合、別のマシンでは復号できない。

**対策：** STEP 1 の実施前に、以下でローカルからリモートへの転送テストを行う：

```bash
# ローカルで
echo "$GWS_CLIENT_SECRET_B64" | base64 -d | diff ~/.config/gws/client_secret.json -
# → 差分なしなら base64 エンコードは正しい

# リモートで（手動テスト）
mkdir -p ~/.config/gws
echo "$GWS_CLIENT_SECRET_B64" | base64 -d > ~/.config/gws/client_secret.json
echo "$GWS_CREDENTIALS_ENC_B64" | base64 -d > ~/.config/gws/$GWS_CREDENTIALS_FILENAME
gws auth status
```

復号に失敗した場合は「リスク 1b」へ。

### リスク 1b：暗号化が転送不可だった場合の代替案

gws の内部実装を確認して、`credentials.enc` の代わりに生の refresh_token を使う方法を検討する。具体的には：

- `credentials.json`（非暗号化・旧形式）を作成して gws に読ませる
- または `GOOGLE_WORKSPACE_CLI_CLIENT_ID` / `GOOGLE_WORKSPACE_CLI_CLIENT_SECRET` + 独自トークンキャッシュを構築する

この代替案は難易度が高いため、まず STEP 1〜4 を試してから判断する。

### リスク 2：OAuth トークン失効

Google の OAuth refresh token は通常無期限だが、長期間使わないと失効する。失効した場合：

```bash
# ローカルで再認証
gws auth login --scopes "email,profile,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/userinfo.email,openid"
# 再エンコードして env vars を更新
```

### リスク 3：npm インストール時間（初回起動が遅くなる）

`npm install -g` はネットワーク経由で数十秒かかる場合がある。

**対策：** フックを `async: true` で実行し、起動ブロックを防ぐ。スキルの STEP 冒頭に「gws が必要なスキルは数十秒後に実行」の旨を記載する（ただし現状の SessionStart フックもすでに async なので許容範囲）。

---

## 対象スクリプト（対応後に動くようになるもの）

| スクリプト | 用途 |
|-----------|------|
| `send_gmail.sh` | Gmail 送信 |
| `create_gmail_draft.sh` | Gmail 下書き作成 |
| `get_gmail_body.sh` | Gmail スレッド本文取得 |
| `download_gmail_attachment.sh` | Gmail 添付ダウンロード |
| `drive_put.sh` | Drive アップロード |
| `drive_get.sh` | Drive ダウンロード |
| `sync_to_drive.sh` | Drive 同期 |

---

## 実装順序

1. **STEP 1**（よーんがローカルで実施）— `~/.config/gws/` のファイルを確認・base64 エンコードし、環境変数 UI に登録
2. **STEP 3**（Claude が実施）— `setup_gws_remote.sh` スクリプトを作成
3. **STEP 2**（Claude が実施）— `settings.json` の SessionStart フックに追加
4. **STEP 4**（よーんがリモートで確認）— 動作確認

STEP 1 はよーんのローカル操作が必要なため、実装の起点はよーん側になる。

---

## 今後の拡張

gws が動けば `CLAUDE.md` の「Gmail・Drive の連携は gws CLI を使って実装する」方針をリモートでも完全に守れるようになる。
現在 MCP で代替しているスキルの一部（`daily-xonepoint` STEP 5 など）を gws ベーススクリプトに戻すことも検討できる（ただしトークン節約の観点では MCP のままの方が良い場合もある）。
