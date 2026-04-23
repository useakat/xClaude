# Google Sheets セットアップ手順

スプレッドシートURL:
https://docs.google.com/spreadsheets/d/1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM/

---

## 1回だけ必要な初期設定

### Step 1: Google Cloud でサービスアカウントを作成

1. https://console.cloud.google.com にアクセス
2. プロジェクトを作成（または既存プロジェクトを選択）
3. 左メニュー → 「APIとサービス」→「ライブラリ」
4. 「Google Sheets API」を検索して有効化
5. 「Google Drive API」も有効化
6. 左メニュー → 「APIとサービス」→「認証情報」
7. 「認証情報を作成」→「サービスアカウント」
8. 名前を入力（例: `xclaude-sheets`）→「作成して続行」→「完了」
9. 作成されたサービスアカウントをクリック
10. 「キー」タブ →「鍵を追加」→「新しい鍵を作成」→「JSON」→ダウンロード
11. ダウンロードしたJSONを `/root/xClaude/google_service_account.json` として保存

### Step 2: スプレッドシートをサービスアカウントと共有

1. ダウンロードしたJSONの中の `client_email` フィールドの値をコピー
   （例: `xclaude-sheets@your-project.iam.gserviceaccount.com`）
2. スプレッドシートを開いて「共有」
3. そのメールアドレスを追加、権限は「編集者」

### Step 3: 動作確認

```bash
python3 /root/xClaude/sheets_manager.py list one-point
```

### Step 4: 既存データの一括移行

```bash
python3 /root/xClaude/sheets_manager.py migrate
```

---

## シート構成

| シート名 | 用途 | 対応ファイル |
|---|---|---|
| `onePointNeta` | 科学トリビアネタ | onePointNeta.md |
| `noteNeta` | note記事ネタ（執念の物語） | noteNeta.md |
| `newsTopics` | 最新ニュースネタ | news-topics.csv |

---

## 環境変数（オプション）

JSONファイルをデフォルト以外の場所に置く場合:

```bash
export GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/your/service_account.json
```

`.env` に追記してもOK:
```
GOOGLE_SERVICE_ACCOUNT_JSON=/root/xClaude/google_service_account.json
```
