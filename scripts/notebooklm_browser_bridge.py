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
  python3 scripts/notebooklm_browser_bridge.py list-sources <notebook_id> [--ids]
  python3 scripts/notebooklm_browser_bridge.py delete-source <notebook_id> <source_id>

ソースの品質について:
  deep-research は既定で「Deep Research が生成した報告書」をソースに含めない。
  取り込むと AI の要約がその notebook の一次資料になり、check-fact-lim が
  AI の出力を AI で検証する循環に陥る（2026-08-14 に SOHO のノートで発覚）。
  過去に混入したものは list-sources --ids で ID を調べ delete-source で除去する。

多重起動・後始末:
  Windows 側は単一の Chrome プロファイルを共有するため、同時に2つ動かすと
  プロファイルロックで衝突する。ロックファイルで直列化し、先客がいれば待つ。
  前回が異常終了して Chrome が残っていた場合は、起動失敗を検知して掃除し
  1回だけ再試行する（OOM や SIGKILL では後始末が走らないため、次回に回復させる）。
"""
import argparse
import asyncio
import fcntl
import json
import os
import signal
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
from notebooklm._chat import ChatAPI  # noqa: E402

# 旧ドメイン宛の URL は、ブラウザのページ（新ドメイン）から見ると別オリジンになり
# CORS で弾かれる。ブリッジ側で新ドメインへ書き換える。
OLD_ORIGIN = "https://notebooklm.google.com"

SSH_HOST = "Administrator@133.18.136.38"
REMOTE_SERVER = r"%USERPROFILE%\nbrpc_server.py"

# ブリッジは Windows の単一 Chrome プロファイル前提。セッション間で直列化する。
# flock はプロセス消滅時に必ず解放されるので、OOM や SIGKILL でも残らない。
LOCK_PATH = Path(os.environ.get("NBLM_BRIDGE_LOCK", "/tmp/notebooklm_bridge.lock"))
LOCK_WAIT = float(os.environ.get("NBLM_BRIDGE_LOCK_WAIT", "1200"))

# 残留 Chrome がプロファイルを掴んでいるときの Playwright のエラー文言
PROFILE_LOCK_SIGNS = ("Lock file can not be created", "SingletonLock", "ProcessSingleton")


class BridgeError(RuntimeError):
    """detail には表示しきれない全文（起動失敗時の stderr 全体）を保持する。"""

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


class SessionLock:
    """ブリッジの多重起動を防ぐ排他ロック。先客がいれば空くまで待つ。"""

    def __init__(self, path: Path = LOCK_PATH, wait: float = LOCK_WAIT):
        self.path = path
        self.wait = wait
        self.fh = None

    def acquire(self) -> None:
        self.fh = open(self.path, "w")
        deadline = time.time() + self.wait
        waited = False
        while True:
            try:
                fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.fh.write(f"{os.getpid()}\n")
                self.fh.flush()
                return
            except BlockingIOError:
                if not waited:
                    print("→ 他セッションがブリッジ使用中。空くまで待機します…", file=sys.stderr)
                    waited = True
                if time.time() >= deadline:
                    raise BridgeError(
                        f"ブリッジが他セッションに専有されたままです（{self.wait:.0f}秒待機）。"
                        "実行中の処理が終わってから再試行してください"
                    )
                time.sleep(2.0)

    def release(self) -> None:
        if not self.fh:
            return
        try:
            fcntl.flock(self.fh, fcntl.LOCK_UN)
            self.fh.close()
        except Exception:
            pass
        self.fh = None


class BrowserBridge:
    """Windows の常駐ブラウザへ RPC を中継する（stdin/stdout の JSON 行プロトコル）。"""

    def __init__(self, ssh_host: str = SSH_HOST):
        self.ssh_host = ssh_host
        self.proc: subprocess.Popen | None = None
        self.csrf = ""
        self.sid = ""
        self.origin = ""
        self.remote_pid: int | None = None

    # --- リモート操作の補助 ---

    def _ssh(self, command: str, timeout: float = 60.0) -> str:
        try:
            res = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
                 self.ssh_host, command],
                capture_output=True, text=True, timeout=timeout,
            )
            return res.stdout
        except Exception:
            return ""

    def _kill_stale_remote(self, timeout: float = 120.0) -> None:
        """残留 Chrome を終了し、プロファイルロックが解けるまで待つ。

        ロック取得後にしか呼ばないので、他セッションを巻き込むことはない。
        """
        self._ssh("taskkill /F /IM chrome.exe /T")
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(5.0)
            out = self._ssh('tasklist /FI "IMAGENAME eq chrome.exe" | find /C "chrome.exe"')
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            if lines and lines[-1] == "0":
                return
        raise BridgeError("残留 Chrome を終了できませんでした（Windows 側を確認してください）")

    def _kill_remote_session(self) -> None:
        """自分が起動したリモートプロセスだけを木ごと終了する。"""
        if self.remote_pid:
            self._ssh(f"taskkill /F /PID {self.remote_pid} /T")

    # --- 起動 ---

    def start(self, timeout: float = 180.0) -> None:
        try:
            self._spawn(timeout)
        except BridgeError as e:
            whole = str(e) + getattr(e, "detail", "")
            if not any(sign in whole for sign in PROFILE_LOCK_SIGNS):
                raise
            print("→ 前回の残留 Chrome がプロファイルを掴んでいます。掃除して再試行します…",
                  file=sys.stderr)
            self._kill_stale_remote()
            self._spawn(timeout)

    def _spawn(self, timeout: float) -> None:
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
                # 全文を detail に残す（プロファイルロックの文言は末尾側に出る）
                err = self.proc.stderr.read()
                self._discard_local()
                raise BridgeError(f"ブリッジ起動に失敗しました: {err[-400:]}", detail=err)
            line = line.strip()
            if not line.startswith("{"):
                continue  # 起動時の雑多な出力は読み飛ばす
            info = json.loads(line)
            if not info.get("ready"):
                err = str(info.get("error"))
                self._discard_local()
                raise BridgeError(f"ブリッジ初期化エラー: {err}", detail=err)
            self.csrf, self.sid, self.origin = info["csrf"], info["sid"], info["origin"]
            self.remote_pid = info.get("pid")
            return
        self._discard_local()
        raise BridgeError("ブリッジ起動がタイムアウトしました")

    def _discard_local(self) -> None:
        """起動に失敗した ssh プロセスを片付ける（再試行前に呼ぶ）。"""
        if self.proc:
            try:
                self.proc.kill()
                self.proc.wait(timeout=10)
            except Exception:
                pass
            self.proc = None

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
        """正常終了なら quit で閉じる。閉じられなければリモートを木ごと落とす。

        ここを通らずに落ちた場合（OOM / SIGKILL）は Chrome が残るが、
        次回起動時に _kill_stale_remote() が回復させる。
        """
        if not self.proc:
            return
        try:
            self.proc.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
            self.proc.stdin.flush()
            self.proc.wait(timeout=20)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
            # ssh を切っても Windows 側は生き残るため、PID 指定で確実に終了させる
            self._kill_remote_session()
        finally:
            self.proc = None


class _FakeResponse:
    """httpx.Response の最小互換（ChatAPI が直接 http_client を使うため）。"""

    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code != 200:
            raise BridgeError(f"HTTP {self.status_code}: {self.text[:200]}")


class _FakeHttpClient:
    """post() をブリッジ経由に差し替えた httpx.AsyncClient 互換の最小実装。"""

    def __init__(self, bridge: BrowserBridge):
        self.bridge = bridge

    async def post(self, url: str, content: str = "", **_):
        url = url.replace(OLD_ORIGIN, self.bridge.origin)
        res = await asyncio.to_thread(self.bridge.call, url, content)
        return _FakeResponse(res.get("status", -1), res.get("text", ""))


class BridgeCore:
    """vendor の *API クラスが必要とする最小の core。"""

    MAX_CACHE = 50

    def __init__(self, bridge: BrowserBridge):
        self.bridge = bridge
        self.auth = AuthTokens(cookies={}, csrf_token=bridge.csrf, session_id=bridge.sid)
        self._reqid_counter = 100000
        self._http_client = _FakeHttpClient(bridge)
        self._conversations: dict[str, list] = {}

    # --- ChatAPI が使う補助 ---
    def get_http_client(self):
        return self._http_client

    def get_cached_conversation(self, conversation_id: str) -> list:
        return self._conversations.get(conversation_id, [])

    def cache_conversation_turn(self, conversation_id: str, query: str, answer: str, turn_number: int) -> None:
        turns = self._conversations.setdefault(conversation_id, [])
        turns.append({"query": query, "answer": answer, "turn_number": turn_number})
        if len(self._conversations) > self.MAX_CACHE:
            self._conversations.pop(next(iter(self._conversations)))

    def clear_conversation_cache(self, conversation_id: str | None = None) -> None:
        if conversation_id:
            self._conversations.pop(conversation_id, None)
        else:
            self._conversations.clear()

    async def get_source_ids(self, notebook_id: str) -> list:
        """ノート内の全ソースIDを返す（ChatAPI が質問対象の指定に使う）。"""
        sources = await SourcesAPI(self).list(notebook_id)
        ids = []
        for s in sources:
            sid = getattr(s, "id", None) or (s.get("id") if isinstance(s, dict) else None)
            if sid:
                ids.append(sid)
        return ids

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


def _source_field(s, name: str) -> str:
    return getattr(s, name, None) or (s.get(name) if isinstance(s, dict) else "") or ""


async def cmd_list_sources(core, args):
    sources = await SourcesAPI(core).list(args.notebook_id)
    for s in sources:
        title = _source_field(s, "title")
        if args.ids:  # delete-source に渡す source_id を出す
            print(f"{_source_field(s, 'id')}\t{title}")
        else:
            print(f"- {title}")
    print(f"--- {len(sources)} 件 ---")


async def cmd_delete_source(core, args):
    """notebook からソースを1件削除する。

    Deep Research が生成した報告書が誤ってソース化された場合など、
    照合先として不適切なソースを取り除くために使う（2026-08-14 の SOHO 事例）。
    source_id は `list-sources --ids` で確認する。
    """
    api = SourcesAPI(core)
    sources = await api.list(args.notebook_id)
    target = next((s for s in sources if _source_field(s, "id") == args.source_id), None)
    if target is None:
        raise BridgeError(f"ソースが見つかりません: {args.source_id}")
    title = _source_field(target, "title")
    await api.delete(args.notebook_id, args.source_id)
    after = len(await api.list(args.notebook_id))
    print(f"✓ 削除: {title}")
    print(f"  ソース数: {len(sources)} → {after}")


async def cmd_add_source(core, args):
    """URL を指定して notebook にソースを追加する。

    CLAUDE.md のリサーチ運用ルール「新たに信頼できるソースが見つかったら notebook に
    追加する」を実行するための口。manager 側は認証が失効しているため、ブリッジに置く。
    追加前に既存ソース数を控えて、増えたことを確認できるようにする。
    """
    api = SourcesAPI(core)
    before = len(await api.list(args.notebook_id))
    src = await api.add_url(args.notebook_id, args.url, wait=True)
    title = getattr(src, "title", None) or (
        src.get("title") if isinstance(src, dict) else ""
    )
    print(f"✓ 追加: {title or args.url}")
    print(f"  ソース数: {before} → {before + 1}")


async def cmd_add_text(core, args):
    """ローカルのテキストを notebook にソースとして追加する。

    PDF・論文など URL で渡せない一次資料を入れるための口。ライブラリには add_file も
    あるが、あちらはバイナリのレジューム アップロードで、このブリッジ（JSON 1行の
    プロキシ）を通せない。テキスト層のある PDF は抽出してからここに流す。
    """
    api = SourcesAPI(core)
    content = args.content
    if content == "-":  # 長文は標準入力から受け取る
        content = sys.stdin.read()
    content = content.strip()
    if not content:
        raise SystemExit("本文が空です")

    before = len(await api.list(args.notebook_id))
    src = await api.add_text(args.notebook_id, args.title, content, wait=True)
    title = getattr(src, "title", None) or (
        src.get("title") if isinstance(src, dict) else ""
    )
    print(f"✓ 追加: {title or args.title}（{len(content)} 字）")
    print(f"  ソース数: {before} → {before + 1}")


async def cmd_ask(core, args):
    question = args.question
    if question == "-":  # 長文は標準入力から受け取る
        question = sys.stdin.read()
    result = await ChatAPI(core).ask(args.notebook_id, question)
    # 回答本文のみ出力（references を含めると巨大になるため）
    print(getattr(result, "answer", result))


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
        # Deep Research が生成した「報告書」（result_type == 5）は、既定でソース化しない。
        # これを取り込むと、AI が書いた要約がその notebook の一次資料になり、
        # 以後の check-fact-lim が AI の出力を AI で検証する循環に陥る。
        # 2026-08-14、SOHO のノートで実際に誤った物理説明が2度出力された。
        to_import = sources
        if not args.with_report:
            to_import = [s for s in sources if s.get("result_type") != 5]
            dropped = len(sources) - len(to_import)
            if dropped:
                print(f"  生成報告書 {dropped} 件は取り込まない（--with-report で取り込む）",
                      file=sys.stderr)
        if to_import:
            imported = await research.import_sources(
                args.notebook_id, latest.get("task_id", task_id), to_import)
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
    p_ls.add_argument("--ids", action="store_true",
                      help="source_id をタブ区切りで併記する（delete-source に渡す）")

    p_del = sub.add_parser("delete-source")
    p_del.add_argument("notebook_id")
    p_del.add_argument("source_id", help="list-sources --ids で確認したソースID")

    p_as = sub.add_parser("add-source")
    p_as.add_argument("notebook_id")
    p_as.add_argument("url", help="追加するソースの URL")

    p_at = sub.add_parser("add-text")
    p_at.add_argument("notebook_id")
    p_at.add_argument("title", help="ソースのタイトル")
    p_at.add_argument("content", help="本文。'-' を渡すと標準入力から読む")

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("notebook_id")
    p_ask.add_argument("question", help="質問文。'-' を渡すと標準入力から読む")

    p_dr = sub.add_parser("deep-research")
    p_dr.add_argument("notebook_id")
    p_dr.add_argument("query")
    p_dr.add_argument("--timeout", type=float, default=900.0)
    p_dr.add_argument("--interval", type=float, default=20.0)
    p_dr.add_argument("--no-import", action="store_true")
    p_dr.add_argument("--with-report", action="store_true",
                      help="Deep Research が生成した報告書もソースとして取り込む（既定では取り込まない）")

    args = ap.parse_args()
    cmds = {
        "list": cmd_list,
        "create": cmd_create,
        "list-sources": cmd_list_sources,
        "delete-source": cmd_delete_source,
        "add-source": cmd_add_source,
        "add-text": cmd_add_text,
        "ask": cmd_ask,
        "deep-research": cmd_deep_research,
    }

    bridge = BrowserBridge()
    lock = SessionLock()

    def on_signal(signum, _frame):
        # timeout(1) の SIGTERM や Ctrl-C でも Windows 側を残さない
        print(f"\n→ シグナル {signum} を受信。リモートを終了します…", file=sys.stderr)
        bridge.close()
        lock.release()
        sys.exit(128 + signum)

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, on_signal)

    try:
        lock.acquire()
        bridge.start()
        core = BridgeCore(bridge)
        asyncio.run(cmds[args.command](core, args))
    except BridgeError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        bridge.close()
        lock.release()


if __name__ == "__main__":
    main()
