# sync-to-drive

ローカルの `outputs/` ディレクトリを Google Drive の `outputs` フォルダへ一方向同期する。

## 同期先

- フォルダ ID: `1tBSBTLNTcxrO_83z4Z-NN4i-cs47jZnn`
- 方向: ローカル → Drive（Drive 側は削除しない、同名ファイルはスキップ）

## 実行コマンド

```bash
uv run $(git rev-parse --show-toplevel)/scripts/sync_to_drive.py
```

## 初回認証セットアップ（一度だけ）

サービスアカウントは My Drive にアップロードできないため、ユーザー OAuth を使う。

### 手順

1. **GCP コンソールで OAuth クライアント ID を作成する**
   - https://console.cloud.google.com/ → プロジェクト `charming-well-464402-u4` を選択
   - 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuthクライアントID」
   - アプリケーションの種類：**デスクトップアプリ**
   - 名前：`sync-to-drive`（任意）
   - 「作成」→「JSONをダウンロード」

2. **ダウンロードした JSON を保存する**
   ```
   gcp/drive_oauth_client.json
   ```

3. **初回実行（ターミナルで対話的に実行）**
   ```
   ! uv run scripts/sync_to_drive.py
   ```
   - URL が表示されるのでブラウザで開く
   - Google アカウントで認証 → 表示されたコードを貼り付ける
   - `gcp/drive_token.json` にトークンが保存される（以降は自動）

### 認証後の通常実行

初回認証後は Claude が直接実行できる：

```bash
uv run $(git rev-parse --show-toplevel)/scripts/sync_to_drive.py
```

## 動作仕様

- `outputs/` 内のすべてのファイルを対象とする
- Drive に同名ファイルが存在する場合はスキップ（上書きしない）
- 対応 MIME タイプ: PNG / JPG / GIF / PDF / TXT（それ以外は `application/octet-stream`）

## 完了後の報告

スクリプトの出力をそのまま報告する。
