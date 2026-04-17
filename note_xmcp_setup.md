# Claude CodeにX APIを連携させた話——XMCPセットアップ完全記録

Claude Codeから直接Xに投稿できたら最高じゃないか、と思って試した。
結論、できた。しかもセッション開始と同時に自動起動する設定まで入れた。

やったことを全部書く。

---

## そもそもXMCPって何？

**XMCP**（X MCP Server）は、X（旧Twitter）のAPIをMCPサーバーとして動かすOSSツール。
X公式の開発チーム（xdevplatform）が公開している。

MCPというのは「Model Context Protocol」の略で、AIに外部ツールを接続するための規格。
これを使うと、ClaudeがXの機能を直接呼び出せるようになる。

投稿の検索、ユーザー情報の取得、ポストの作成……X APIが持っている機能をClaude Codeから自然言語で操作できる。

---

## 準備するもの

- Linux環境（Ubuntu/Debian系）
- Python 3.9以上
- **X Developer Platformのアプリ**（developer.x.com で作成）

必要なキー（「Keys and Tokens」タブで全部取得できる）：
- API Key（= Consumer Key）
- API Key Secret（= Consumer Secret）
- Bearer Token
- Access Token（OAuth 1.0a）
- Access Token Secret（OAuth 1.0a）

---

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/xdevplatform/xmcp.git
cd xmcp
```

### 2. 仮想環境を作る

```bash
# python3-venvが入っていない場合（Ubuntu 22.04）
sudo apt install python3.10-venv -y

python3 -m venv .venv
```

### 3. 依存パッケージをインストール

```bash
.venv/bin/pip install -r requirements.txt
```

### 4. .envファイルを作成

```bash
cp env.example .env
```

エディタで `.env` を開いて以下の5行を設定する：

```
X_OAUTH_CONSUMER_KEY=（API Key）
X_OAUTH_CONSUMER_SECRET=（API Key Secret）
X_BEARER_TOKEN=（Bearer Token）
X_OAUTH_ACCESS_TOKEN=（Access Token）
X_OAUTH_ACCESS_TOKEN_SECRET=（Access Token Secret）
```

> **セキュリティ注意**：キーはチャットやAIに直接渡さず、必ずエディタで直接入力する。

### 5. server.pyにパッチを当てる

デフォルトのコードは、アクセストークンが `.env` に設定してあっても無視してOAuthフローを強制実行する。サーバー環境（ブラウザなし）ではそこで詰まるので、1箇所修正が必要。

`server.py` の `build_oauth1_client()` 関数を以下のように変更：

```python
def build_oauth1_client() -> OAuth1Client:
    consumer_key = os.getenv("X_OAUTH_CONSUMER_KEY")
    consumer_secret = os.getenv("X_OAUTH_CONSUMER_SECRET")
    if not consumer_key or not consumer_secret:
        raise RuntimeError(
            "Missing X_OAUTH_CONSUMER_KEY or X_OAUTH_CONSUMER_SECRET for OAuth1 signing."
        )
    # 追加：.envにトークンがあればOAuthフローをスキップ
    env_access_token = os.getenv("X_OAUTH_ACCESS_TOKEN", "").strip()
    env_access_secret = os.getenv("X_OAUTH_ACCESS_TOKEN_SECRET", "").strip()
    if env_access_token and env_access_secret:
        access_token, access_secret = env_access_token, env_access_secret
    else:
        access_token, access_secret = run_oauth1_flow()
```

### 6. サーバーを起動

```bash
.venv/bin/python server.py
```

以下が表示されたら成功：

```
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

MCPエンドポイント：`http://127.0.0.1:8000/mcp`

---

## Claude CodeにMCPサーバーを登録する

`~/.claude/settings.json` を作成（または編集）して追加：

```json
{
  "mcpServers": {
    "xmcp": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

---

## セッション開始時に自動起動する設定

毎回手動でサーバーを起動するのは面倒なので、Claude CodeのSessionStartフックで自動起動させる。

`~/.claude/settings.json` を以下のように更新：

```json
{
  "mcpServers": {
    "xmcp": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "pkill -f 'python server.py' 2>/dev/null; cd /root/xClaude/xmcp && .venv/bin/python server.py > /tmp/xmcp.log 2>&1 &",
            "async": true
          }
        ]
      }
    ]
  }
}
```

次回セッション開始時から自動でXMCPサーバーが立ち上がる。
ログは `/tmp/xmcp.log` で確認できる。

---

## 使えるようになること

Claude Codeから自然言語でXを操作できる。一部を抜粋：

| ツール名 | できること |
|---|---|
| `getUsersByUsername` | ユーザー情報を取得 |
| `searchPostsRecent` | 最近のポストを検索 |
| `createPosts` | ポストを作成 |
| `getUsersMe` | 自分のアカウント情報を取得 |
| `getUsersTimeline` | タイムラインを取得 |

ツールは100種類以上。必要なものだけに絞りたい場合は `.env` に追加：

```
X_API_TOOL_ALLOWLIST=getUsersByUsername,createPosts,searchPostsRecent
```

---

## 詰まったところメモ

**python3-venvがない**
→ `sudo apt install python3.10-venv -y` で解決

**OAuthフローが走ってブラウザが開けない / ポート8976が使用中になる**
→ `X_OAUTH_ACCESS_TOKEN` と `X_OAUTH_ACCESS_TOKEN_SECRET` を `.env` に設定 + server.pyにパッチ
→ 前回の起動が残っている場合は `pkill -f 'python server.py'` でプロセスを落とす

---

*使用環境：Ubuntu 22.04 / Python 3.10 / Claude Code*
