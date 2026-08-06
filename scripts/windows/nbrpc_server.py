"""
NotebookLM RPC ブリッジサーバ（Windows 常駐側）

ログイン済み Chrome プロファイルでブラウザを1回だけ開き、
stdin から JSON 行でリクエストを受け、ページ内 fetch で
notebook.google.com の batchexecute を叩いて結果を stdout へ JSON 行で返す。

cookie をファイルに書き出さないため、__Secure-1PSIDTS が
storage_state に出ない（デバイスバインド）問題を回避できる。

プロトコル:
  起動時に  {"ready":true,"csrf":"...","sid":"...","origin":"..."}  を1行出力
  以降 stdin:  {"url":"<full batchexecute url>","body":"<form-encoded body>"}
       stdout: {"status":200,"text":"<response text>"}
  {"cmd":"quit"} で終了

使い方（この環境から）:
  ssh Administrator@<host> python %USERPROFILE%\\nbrpc_server.py
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

FETCH_JS = r"""
async ([url, body]) => {
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
      body: body,
      credentials: "include"
    });
    const t = await r.text();
    return {status: r.status, text: t};
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

    emit({"ready": True, "csrf": m_csrf.group(1), "sid": m_sid.group(1), "origin": ORIGIN})

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
