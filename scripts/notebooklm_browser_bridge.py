#!/usr/bin/env python3
"""
NotebookLM ブラウザ経由ブリッジ（この環境側）

背景:
  NotebookLM が Gemini の notebook.google.com へ移行し、実物 Chrome でログインしても
  __Secure-1PSIDTS などのローテーション cookie が storage_state に書き出されなくなった。
  そのため「cookie をファイルに書き出して httpx で再生する」従来方式は signin に飛ばされる。

方式:
  Windows server (SSH 越し) のログイン済み Chrome を常駐させ、ページ内 fetch で
  batchexecute を叩く。cookie はブラウザが自動付与するので上記問題を回避できる。
  RPC のエンコード/デコード・結果の解析は vendor/notebooklm の実装をそのまま再利用する。

使い方:
  python3 scripts/notebooklm_browser_bridge.py list
  python3 scripts/notebooklm_browser_bridge.py create "ノート名"
  python3 scripts/notebooklm_browser_bridge.py deep-research <notebook_id> "クエリ"
  python3 scripts/notebooklm_browser_bridge.py list-sources <notebook_id>
"""
import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))

from notebooklm.auth import AuthTokens  # noqa: E402
from notebooklm.rpc.encoder import encode_rpc_request, build_request_body  # noqa: E402
from notebooklm.rpc.decoder import decode_response  # noqa: E402
from notebooklm._research import ResearchAPI  # noqa: E402
from notebooklm._notebooks import NotebooksAPI  # noqa: E402
from notebooklm._sources import SourcesAPI  # noqa: E402

SSH_HOST = "Administrator@133.18.136.38"
REMOTE_SERVER = r"%USERPROFILE%\nbrpc_server.py"


class BridgeError(RuntimeError):
    pass


class BrowserBridge:
    """Windows の常駐ブラウザへ RPC を中継する（stdin/stdout の JSON 行プロトコル）。"""

    def __init__(self, ssh_host: str = SSH_HOST):
        self.ssh_host = ssh_host
        self.proc: subprocess.Popen | None = None
        self.csrf = ""
        self.sid = ""
        self.origin = ""

    def start(self, timeout: float = 180.0) -> None:
        self.proc = subprocess.Popen(
            [
                "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
                "-o", "ServerAliveInterval=30",
                self.ssh_host, "python", REMOTE_SERVER,
            ],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1,
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                err = self.proc.stderr.read()[:400]
                raise BridgeError(f"ブリッジ起動に失敗しました: {err}")
            line = line.strip()
            if not line.startswith("{"):
                continue  # 起動時の雑多な出力は読み飛ばす
            info = json.loads(line)
            if not info.get("ready"):
                raise BridgeError(f"ブリッジ初期化エラー: {info.get('error')}")
            self.csrf, self.sid, self.origin = info["csrf"], info["sid"], info["origin"]
            return
        raise BridgeError("ブリッジ起動がタイムアウトしました")

    def call(self, url: str, body: str) -> dict:
        if not self.proc:
            raise BridgeError("ブリッジが起動していません")
        self.proc.stdin.write(json.dumps({"url": url, "body": body}) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            err = self.proc.stderr.read()[:400]
            raise BridgeError(f"ブリッジが応答しません: {err}")
        return json.loads(line)

    def close(self) -> None:
        if self.proc:
            try:
                self.proc.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=20)
            except Exception:
                self.proc.kill()
            self.proc = None


class BridgeCore:
    """vendor の *API クラスが必要とする最小の core（rpc_call と auth のみ）。"""

    def __init__(self, bridge: BrowserBridge):
        self.bridge = bridge
        self.auth = AuthTokens(cookies={}, csrf_token=bridge.csrf, session_id=bridge.sid)
        self._reqid_counter = 100000

    def _build_url(self, method, source_path: str = "/") -> str:
        from urllib.parse import urlencode
        params = {
            "rpcids": method.value,
            "source-path": source_path,
            "f.sid": self.auth.session_id,
            "rt": "c",
        }
        return f"{self.bridge.origin}/_/LabsTailwindUi/data/batchexecute?{urlencode(params)}"

    async def rpc_call(self, method, params, source_path: str = "/", allow_null: bool = False, **_):
        url = self._build_url(method, source_path)
        body = build_request_body(encode_rpc_request(method, params), self.auth.csrf_token)
        res = await asyncio.to_thread(self.bridge.call, url, body)
        if res.get("status") != 200:
            raise BridgeError(f"RPC {method.name} 失敗: status={res.get('status')} {res.get('text','')[:200]}")
        return decode_response(res["text"], method.value, allow_null=allow_null)


async def cmd_list(core, _args):
    notebooks = await NotebooksAPI(core).list()
    for nb in notebooks[:50]:
        nid = getattr(nb, "id", None) or (nb.get("id") if isinstance(nb, dict) else "")
        title = getattr(nb, "title", None) or (nb.get("title") if isinstance(nb, dict) else "")
        print(f"{nid}\t{title}")
    print(f"--- {len(notebooks)} 件 ---")


async def cmd_create(core, args):
    nb = await NotebooksAPI(core).create(args.title)
    nid = getattr(nb, "id", None) or (nb.get("id") if isinstance(nb, dict) else "")
    print(f"✓ 作成: {nid}")


async def cmd_list_sources(core, args):
    sources = await SourcesAPI(core).list(args.notebook_id)
    for s in sources:
        title = getattr(s, "title", None) or (s.get("title") if isinstance(s, dict) else "")
        print(f"- {title}")
    print(f"--- {len(sources)} 件 ---")


async def cmd_deep_research(core, args):
    research = ResearchAPI(core)
    print(f"→ Deep Research 開始: {args.query[:60]}", file=sys.stderr)
    started = await research.start(args.notebook_id, args.query, source="web", mode="deep")
    if not started:
        raise BridgeError("Deep Research の開始に失敗しました")
    task_id = started["task_id"]
    print(f"  task_id: {task_id}", file=sys.stderr)

    deadline = time.time() + args.timeout
    latest = None
    while time.time() < deadline:
        await asyncio.sleep(args.interval)
        latest = await research.poll(args.notebook_id)
        status = latest.get("status")
        n_src = len(latest.get("sources") or [])
        print(f"  status={status} sources={n_src}", file=sys.stderr)
        if status == "completed":
            break
    if not latest or latest.get("status") != "completed":
        raise BridgeError(f"Deep Research がタイムアウトしました（{args.timeout}秒）")

    sources = latest.get("sources") or []
    if not args.no_import and sources:
        imported = await research.import_sources(args.notebook_id, latest.get("task_id", task_id), sources)
        print(f"✓ ソース取り込み: {len(imported)} 件", file=sys.stderr)

    print(json.dumps({
        "notebook_id": args.notebook_id,
        "task_id": latest.get("task_id"),
        "status": latest.get("status"),
        "summary": latest.get("summary", ""),
        "report": latest.get("report", ""),
        "sources": [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources],
    }, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="NotebookLM ブラウザ経由ブリッジ")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("list")

    p_create = sub.add_parser("create")
    p_create.add_argument("title")

    p_ls = sub.add_parser("list-sources")
    p_ls.add_argument("notebook_id")

    p_dr = sub.add_parser("deep-research")
    p_dr.add_argument("notebook_id")
    p_dr.add_argument("query")
    p_dr.add_argument("--timeout", type=float, default=900.0)
    p_dr.add_argument("--interval", type=float, default=20.0)
    p_dr.add_argument("--no-import", action="store_true")

    args = ap.parse_args()
    cmds = {
        "list": cmd_list,
        "create": cmd_create,
        "list-sources": cmd_list_sources,
        "deep-research": cmd_deep_research,
    }

    bridge = BrowserBridge()
    try:
        bridge.start()
        core = BridgeCore(bridge)
        asyncio.run(cmds[args.command](core, args))
    except BridgeError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        bridge.close()


if __name__ == "__main__":
    main()
