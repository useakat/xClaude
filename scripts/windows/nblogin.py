from playwright.sync_api import sync_playwright
import os
prof = os.path.expanduser(r"~\.notebooklm\browser_profile")
out  = os.path.expanduser(r"~\.notebooklm\storage_state.json")
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        prof,
        headless=False,
        channel="chrome",                                   # 実物の Chrome を使う（自動化検知を回避しやすい）
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try:
        page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
    except Exception as e:
        print("goto note:", e)
    input(">>> Google にサインインし、NotebookLM のノート一覧が見える状態にしたら ENTER: ")
    # ログイン後に notebooklm.google.com を再ロードして OSID を確実に再発行させる
    print("NotebookLM を読み込み直しています（OSID 再発行）...")
    try:
        page.goto("https://notebooklm.google.com/", wait_until="networkidle", timeout=60000)
    except Exception as e:
        print("reload note:", e)
    page.wait_for_timeout(5000)
    final_url = page.url
    print("現在のURL:", final_url)
    if "accounts.google.com" in final_url or "ServiceLogin" in final_url:
        print("!! まだサインイン画面です。ノート一覧を表示してから、もう一度このスクリプトを実行してください。")
    ctx.storage_state(path=out)
    ctx.close()
print("SAVED:", out)
