"""
NotebookLM RPC ブリッジサーバ（Windows 常駐側）

ログイン済み Chrome プロファイルでブラウザを1回だけ開き、
stdin から JSON 行でリクエストを受け、ページ内 fetch で
notebook.google.com の batchexecute を叩いて結果を stdout へ JSON 行で返す。

cookie をファイルに書き出さないため、__Secure-1PSIDTS が
storage_state に出ない（デバイスバインド）問題を回避できる。

プロトコル:
  起動時に  {"ready":true,"csrf":"...","sid":"...","origin":"...","pid":<自PID>}  を1行出力
  （pid は呼び出し側が異常終了時に taskkill /PID <pid> /T で後始末するために使う。
    プロセス名での一括 kill と違い、並行実行中の他セッションを巻き込まない）
  以降 stdin:  {"url":"<full batchexecute url>","body":"<form-encoded body>"}
       stdout: {"status":200,"text":"<response text>"}
  {"cmd":"quit"} で終了

使い方（この環境から）:
  ssh Administrator@<host> python %USERPROFILE%\\nbrpc_server.py

デプロイ（このリポジトリが正本。編集したら Windows 側へ反映する）:
  scp scripts/nbrpc_server.py Administrator@<host>:nbrpc_server.py
  # 反映確認（両者のハッシュが一致すること）
  sha256sum scripts/nbrpc_server.py
  ssh Administrator@<host> "powershell -NoProfile -Command \\"(Get-FileHash (\\$env:USERPROFILE + '\\nbrpc_server.py') -Algorithm SHA256).Hash.ToLower()\\""
"""
from playwright.sync_api import sync_playwright
import os, sys, json, re

# Windows のコンソール既定が cp932 のため、標準入出力を UTF-8 に固定する
# （応答 JSON に日本語やダッシュ等が含まれると UnicodeEncodeError になる）
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.stdin.reconfigure(encoding="utf-8", errors="replace")

ORIGIN = "https://notebook.google.com"
prof = os.path.expanduser(r"~\.notebooklm\browser_profile")

# チャット（GenerateFreeFormStreamed）のストリーム応答は、更新のたびに
# 「その時点までの回答全文＋引用メタ全部」のスナップショットを送り直す。
# 引用メタは 400KB 超あるため、74 回更新されると 32MB に達し、
# 呼び出し側（ローカル python）が JSON 展開とパースで 400MB 近くまで膨らんで
# OOM Killer に殺される。最終スナップショットだけあれば回答も参照も復元できるので、
# ブラウザ内（＝もともと文字列が存在する場所）で捨ててから返す。
FETCH_JS = r"""
async ([url, body]) => {
  const WRB = '"wrb.fr"';

  // ストリーム応答から末尾の wrb.fr チャンクだけを残す。
  // 想定外の形なら無加工で返す（壊れるより素通しの方が安全）。
  function trimChatStream(t) {
    try {
      let prefix = "", rest = t;
      if (rest.startsWith(")]}'")) { prefix = ")]}'"; rest = rest.slice(4); }

      // 「長さ行」＋「JSON チャンク行」の並びを分解する
      const lines = rest.split("\n");
      const chunks = [];
      let i = 0;
      while (i < lines.length) {
        const ln = lines[i].trim();
        if (!ln) { i++; continue; }
        if (/^\d+$/.test(ln)) { i++; if (i < lines.length) { chunks.push(lines[i]); i++; } }
        else { chunks.push(lines[i]); i++; }
      }

      const wrb = [];
      for (let k = 0; k < chunks.length; k++) if (chunks[k].indexOf(WRB) >= 0) wrb.push(k);
      if (wrb.length === 0) return t;   // チャット応答ではない／構造が変わった

      // 末尾2つの wrb.fr（＝完成版スナップショット）に加えて、
      // wrb.fr 以外の小さいチャンクと、エラー payload を含むチャンクは残す
      const keep = new Set(wrb.slice(-2));
      for (let k = 0; k < chunks.length; k++) {
        if (chunks[k].indexOf(WRB) < 0) keep.add(k);
        else if (chunks[k].indexOf("UserDisplayableError") >= 0) keep.add(k);
      }

      const out = [];
      for (const k of Array.from(keep).sort((a, b) => a - b)) {
        out.push(String(chunks[k].length + 1));   // 長さ行（呼び出し側は読み飛ばすだけ）
        out.push(chunks[k]);
      }
      return prefix + (prefix ? "\n\n" : "") + out.join("\n") + "\n";
    } catch (e) {
      return t;
    }
  }

  try {
    const r = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
      body: body,
      credentials: "include"
    });
    const raw = await r.text();
    const isChat = url.indexOf("GenerateFreeFormStreamed") >= 0;
    const t = isChat ? trimChatStream(raw) : raw;
    return {status: r.status, text: t, orig_len: raw.length, trimmed: t.length !== raw.length};
  } catch (e) {
    return {status: -1, text: "FETCH_ERROR: " + String(e)};
  }
}
"""

def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        prof,
        headless=True,
        channel="chrome",
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try:
        page.goto(ORIGIN + "/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
    except Exception as e:
        emit({"ready": False, "error": "goto failed: " + str(e)[:200]})
        ctx.close(); sys.exit(1)

    final = page.url
    if "accounts.google.com" in final or "ServiceLogin" in final:
        emit({"ready": False, "error": "signin redirect: " + final[:120]})
        ctx.close(); sys.exit(1)

    html = page.content()
    m_csrf = re.search(r'"SNlM0e"\s*:\s*"([^"]+)"', html)
    m_sid = re.search(r'"FdrFJe"\s*:\s*"([^"]+)"', html)
    if not (m_csrf and m_sid):
        emit({"ready": False, "error": "tokens not found in page"})
        ctx.close(); sys.exit(1)

    emit({"ready": True, "csrf": m_csrf.group(1), "sid": m_sid.group(1),
          "origin": ORIGIN, "pid": os.getpid()})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            emit({"status": -1, "text": "BAD_JSON: " + str(e)}); continue
        if req.get("cmd") == "quit":
            break
        try:
            res = page.evaluate(FETCH_JS, [req["url"], req["body"]])
            emit(res)
        except Exception as e:
            emit({"status": -1, "text": "EVAL_ERROR: " + str(e)[:300]})

    ctx.close()
