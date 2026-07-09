# NotebookLM 再認証 手順（runbook）

`notebooklm_manager.py` が `Authentication expired or invalid ... WebLiteSignIn`（signin リダイレクト）で失敗したときの復旧手順。

## 前提（この構成の要点）

- この環境の IP は NotebookLM にブロックされているため、**Windows server (133.18.136.38) 経由の SSH SOCKS トンネル**で manager の通信を出している。
- cookie は **出口 IP と一致する Windows server 側で採取**しないと headless で signin に飛ぶ（別 IP で作った cookie は不可）。
- トンネルの SSH ユーザは **`nbtunnel`（鍵認証）**。ファイル採取・scp は **`Administrator`** を使う（cookie が Administrator プロファイル配下のため）。
- 詳しい経緯・根本原因は [報告書](docs/reports/20260709_notebooklm_tunnel_recovery_hardening.md) 参照。

---

## Step 1. Windows server で cookie を再採取（RDP で入る）

1. 踏み台 VPS（`94.26.88.123`）から Windows server (133.18.136.38) に **RDP** で入る。
2. 管理者 PowerShell で採取スニペットを実行：
   ```powershell
   python $env:USERPROFILE\nblogin.py
   ```
   - Chromium が開く → **NotebookLM のホーム（ノート一覧）**まで進む（未ログインならログイン。※対象 notebook が見える正しい Google アカウントで）。
   - ホームが見えたら PowerShell に戻って **ENTER**。
   - `SAVED: C:\Users\Administrator\.notebooklm\storage_state.json` が出れば成功。
   - `nblogin.py` が無い場合は本書末尾【付録】の内容で再作成する。
   - ※ `notebooklm login`（CLI）はリダイレクト競合でクラッシュする既知バグのため使わない。必ず nblogin.py を使う。

## Step 2. この環境へ取り込む（scp）

3. トンネルを確認/起動（落ちていれば張り直し）：
   ```bash
   bash scripts/notebooklm_tunnel.sh          # or --restart
   ```
4. 出口 IP が Windows server か確認：
   ```bash
   curl -s --socks5-hostname 127.0.0.1:1080 https://api.ipify.org   # → 133.18.136.38
   ```
5. cookie を scp で取り込む（**Administrator** で。値はチャットに出さない）：
   ```bash
   cd "$(git rev-parse --show-toplevel)"
   scp -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
     Administrator@133.18.136.38:"C:/Users/Administrator/.notebooklm/storage_state.json" \
     gcp/notebooklm_storage_state.json
   ```
6. **古い既定ファイルが新 cookie を隠さないよう確認**（重要）：
   ```bash
   ls -la ~/.notebooklm/storage_state.json 2>/dev/null && \
     mv ~/.notebooklm/storage_state.json ~/.notebooklm/storage_state.json.bak
   ```
   （`~/.notebooklm/storage_state.json` が存在すると `_storage_path()` が gcp を使わなくなる）

## Step 3. 検証

7. ```bash
   NOTEBOOKLM_SOCKS_PROXY=socks5://127.0.0.1:1080 python3 scripts/notebooklm_manager.py list
   ```
   notebook 一覧が出れば復旧完了。

---

## トラブルシュート

- **トンネルが `Connection reset` / 落ちる**：`bash scripts/notebooklm_tunnel.sh --restart`。SSH は `nbtunnel` 鍵認証なので Claude 側で自動復旧可。
- **SSH 認証で reset（`0xC0000234`）**：Administrator がロックアウト。SMB 総当たり等が原因。ロックアウトは無効化済み（`net accounts /lockoutthreshold:0`）だが再発時は Windows で解除：
  ```powershell
  $u=[ADSI]"WinNT://./Administrator,user"; $u.IsAccountLocked=$false; $u.SetInfo()
  ```
- **signin が続く**：①`gcp/notebooklm_storage_state.json` が新版か、②`~/.notebooklm/storage_state.json` が残って隠していないか、③出口 IP=133.18.136.38 か、を順に確認。
- **サービス本体のログ**（Windows）：`Get-Content C:\ProgramData\ssh\logs\sshd.log -Tail 30`（`LogLevel DEBUG3` 有効化済み）。

## ファイアウォール（現状の制限）

- SSH(22)=この環境の IP のみ / SMB(445,139)=遮断 / RDP(3389)=踏み台 VPS(94.26.88.123) のみ。
- この環境の IP が変わった場合は Windows で SSH 許可 IP を更新：
  ```powershell
  Set-NetFirewallRule -Name OpenSSH-Server-In-TCP -RemoteAddress <新しいIP>
  ```

---

## 【付録】nblogin.py（Windows: `%USERPROFILE%\nblogin.py`）

```python
from playwright.sync_api import sync_playwright
import os
prof = os.path.expanduser(r"~\.notebooklm\browser_profile")
out  = os.path.expanduser(r"~\.notebooklm\storage_state.json")
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(prof, headless=False)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try:
        page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
    except Exception as e:
        print("goto note:", e)
    input(">>> NotebookLM のホームが表示されたら ENTER: ")
    ctx.storage_state(path=out)
    ctx.close()
print("SAVED:", out)
```

前提パッケージ（初回のみ・Windows）：
```powershell
pip install notebooklm-py==0.3.4 playwright
python -m playwright install chromium
```
