#!/usr/bin/env python3
"""NotebookLM manager for Claude Code integration."""

import argparse
import asyncio
import re
import subprocess
import sys
import os
import tempfile

# vendored library fallback (for remote environments without pip install)
_vendor = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vendor')
if os.path.isdir(os.path.join(_vendor, 'notebooklm')) and _vendor not in sys.path:
    sys.path.insert(0, os.path.abspath(_vendor))

from notebooklm import NotebookLMClient
from notebooklm.types import InfographicOrientation, InfographicDetail, InfographicStyle

# SOCKS プロキシ経由オプション（IP ブロック回避用）
# NOTEBOOKLM_SOCKS_PROXY=socks5://127.0.0.1:1080 を設定すると、
# httpx のリクエストをローカル DNS（rdns=False）で SOCKS 経由にする。
# Windows OpenSSH の SOCKS はリモート DNS が動かないため rdns=False が必須。
_SOCKS_PROXY = os.environ.get('NOTEBOOKLM_SOCKS_PROXY')
if _SOCKS_PROXY:
    import httpx
    from httpx_socks import AsyncProxyTransport
    _orig_async_client = httpx.AsyncClient

    def _patched_async_client(*args, **kwargs):
        kwargs.setdefault(
            'transport',
            AsyncProxyTransport.from_url(_SOCKS_PROXY, rdns=False),
        )
        return _orig_async_client(*args, **kwargs)

    httpx.AsyncClient = _patched_async_client

# auth storage path: env var > gcp/ fallback > library default (~/.notebooklm/)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GCP_STORAGE = os.path.join(_ROOT, 'gcp', 'notebooklm_storage_state.json')
_DEFAULT_STORAGE = os.path.expanduser('~/.notebooklm/storage_state.json')

def _storage_path():
    custom = os.environ.get('NOTEBOOKLM_STORAGE_PATH')
    if custom:
        return custom
    if os.path.exists(_GCP_STORAGE) and not os.path.exists(_DEFAULT_STORAGE):
        return _GCP_STORAGE
    return None  # library default


async def cmd_list(args):
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        notebooks = await client.notebooks.list()
        if not notebooks:
            print("ノートブックなし")
            return
        for nb in notebooks:
            print(f"{nb.id}\t{nb.title}")


async def cmd_create(args):
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        nb = await client.notebooks.create(args.title)
        print(f"✓ 作成: {nb.id}\t{nb.title}")
        if args.urls:
            for url in args.urls:
                await client.sources.add_url(nb.id, url)
                print(f"  ソース追加: {url}")
        return nb.id


async def cmd_add_source(args):
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        for url in args.urls:
            await client.sources.add_url(args.notebook_id, url)
            print(f"✓ ソース追加: {url}")


async def cmd_ask(args):
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        result = await client.chat.ask(args.notebook_id, args.question)
        # 回答本文（インラインの [N] マーカー含む）だけを出力する。
        # AskResult 全体（references の cited_text 等）を print すると数百KB〜MB になり、
        # フォーク実行の subagent が読み込みきれず stream idle timeout の一因になるため。
        print(getattr(result, "answer", result))


async def cmd_deep_research(args):
    async with await NotebookLMClient.from_storage(_storage_path(), timeout=120.0) as client:
        result = await client.research.start(
            args.notebook_id, args.query, source="web", mode="deep"
        )
        task_id = result["task_id"]
        print(f"Deep Research 開始: task_id={task_id}")

        for _ in range(60):
            status = await client.research.poll(args.notebook_id)
            if status["status"] == "completed":
                break
            print("  調査中...", flush=True)
            await asyncio.sleep(10)
        else:
            print("タイムアウト: 10分以内に完了しませんでした", file=sys.stderr)
            sys.exit(1)

        sources = status.get("sources", [])
        imported = await client.research.import_sources(
            args.notebook_id, task_id, sources
        )
        print(f"✓ ソース {len(imported)} 件を追加しました")
        for s in imported:
            print(f"  - {s.get('title', '(タイトルなし)')}")


async def cmd_audio(args):
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        print("音声概要を生成中...")
        await client.generate.audio(args.notebook_id)
        if args.output:
            await client.download.audio(args.notebook_id, args.output)
            print(f"✓ 保存: {args.output}")
        else:
            print("✓ 生成完了（ダウンロードは --output で指定）")


async def cmd_infographic(args):
    orientation_map = {
        "landscape": InfographicOrientation.LANDSCAPE,
        "portrait": InfographicOrientation.PORTRAIT,
        "square": InfographicOrientation.SQUARE,
    }
    detail_map = {
        "concise": InfographicDetail.CONCISE,
        "standard": InfographicDetail.STANDARD,
        "detailed": InfographicDetail.DETAILED,
    }
    style_map = {
        "auto": InfographicStyle.AUTO_SELECT,
        "sketch-note": InfographicStyle.SKETCH_NOTE,
        "professional": InfographicStyle.PROFESSIONAL,
        "bento-grid": InfographicStyle.BENTO_GRID,
        "editorial": InfographicStyle.EDITORIAL,
        "instructional": InfographicStyle.INSTRUCTIONAL,
        "bricks": InfographicStyle.BRICKS,
        "clay": InfographicStyle.CLAY,
        "anime": InfographicStyle.ANIME,
        "kawaii": InfographicStyle.KAWAII,
        "scientific": InfographicStyle.SCIENTIFIC,
    }
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        print("インフォグラフィックを生成中...")
        status = await client.artifacts.generate_infographic(
            args.notebook_id,
            instructions=args.instructions or None,
            orientation=orientation_map[args.orientation],
            detail_level=detail_map[args.detail],
            language=args.language,
            style=style_map[args.style],
        )
        task_id = status.task_id if hasattr(status, "task_id") else None
        if task_id:
            print(f"  タスクID: {task_id}（完了待ち）")
            status = await client.artifacts.wait_for_completion(args.notebook_id, task_id)
        if args.output:
            await client.artifacts.download_infographic(args.notebook_id, args.output)
            print(f"✓ 保存: {args.output}")
        else:
            print("✓ 生成完了（ダウンロードは --output で指定）")


async def cmd_make_infographic(args):
    orientation_map = {
        "landscape": InfographicOrientation.LANDSCAPE,
        "portrait": InfographicOrientation.PORTRAIT,
        "square": InfographicOrientation.SQUARE,
    }
    detail_map = {
        "concise": InfographicDetail.CONCISE,
        "standard": InfographicDetail.STANDARD,
        "detailed": InfographicDetail.DETAILED,
    }
    style_map = {
        "auto": InfographicStyle.AUTO_SELECT,
        "sketch-note": InfographicStyle.SKETCH_NOTE,
        "professional": InfographicStyle.PROFESSIONAL,
        "bento-grid": InfographicStyle.BENTO_GRID,
        "editorial": InfographicStyle.EDITORIAL,
        "instructional": InfographicStyle.INSTRUCTIONAL,
        "bricks": InfographicStyle.BRICKS,
        "clay": InfographicStyle.CLAY,
        "anime": InfographicStyle.ANIME,
        "kawaii": InfographicStyle.KAWAII,
        "scientific": InfographicStyle.SCIENTIFIC,
    }

    # テキスト取得
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
        source_title = os.path.basename(args.file)
    elif args.text:
        text = args.text
        source_title = args.title
    else:
        print("エラー: --text または --file を指定してください", file=sys.stderr)
        sys.exit(1)

    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        # ノートブック作成
        nb = await client.notebooks.create(args.title)
        nb_id = nb.id
        print(f"✓ ノートブック作成: {nb_id}")

        try:
            # テキストソース追加
            await client.sources.add_text(nb_id, source_title, text)
            print(f"✓ ソース追加: {source_title}")

            # 追加ソース：Drive URL は drive_get.sh で DL→add_file、それ以外は add_url
            import mimetypes
            import shutil
            for url in args.extra_source_url:
                m = re.search(r'drive\.google\.com/file/d/([\w-]+)', url)
                if m:
                    file_id = m.group(1)
                    tmp_no_ext = tempfile.NamedTemporaryFile(prefix='nblm_src_', delete=False)
                    tmp_no_ext.close()
                    drive_get = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drive_get.sh')
                    subprocess.run(['bash', drive_get, file_id, tmp_no_ext.name], check=True)
                    # MIME 判定で拡張子を付与（NotebookLM が形式判定に拡張子を使うため）
                    mime = subprocess.check_output(['file', '--mime-type', '-b', tmp_no_ext.name]).decode().strip()
                    ext = mimetypes.guess_extension(mime) or ''
                    tmp_path = tmp_no_ext.name + ext
                    shutil.move(tmp_no_ext.name, tmp_path)
                    await client.sources.add_file(nb_id, tmp_path, wait=True)
                    os.unlink(tmp_path)
                    print(f"✓ 追加ソース（Drive, {mime}）: {url}")
                else:
                    await client.sources.add_url(nb_id, url)
                    print(f"✓ 追加ソース（URL）: {url}")

            # インフォグラフィック生成
            print("インフォグラフィックを生成中（数分かかります）...")
            instructions_parts = []
            if args.infographic_title:
                instructions_parts.append(f"タイトルは「{args.infographic_title}」にしてください。")
            if args.instructions:
                instructions_parts.append(args.instructions)
            instructions = " ".join(instructions_parts) or None
            status = await client.artifacts.generate_infographic(
                nb_id,
                language=args.language,
                instructions=instructions,
                orientation=orientation_map[args.orientation],
                detail_level=detail_map[args.detail],
                style=style_map[args.style],
            )
            task_id = status.task_id if hasattr(status, "task_id") else None
            if task_id:
                status = await client.artifacts.wait_for_completion(nb_id, task_id, timeout=300)

            # ダウンロード
            await client.artifacts.download_infographic(nb_id, args.output)
            print(f"✓ 保存: {args.output}")

        finally:
            if not args.keep:
                await client.notebooks.delete(nb_id)
                print(f"✓ ノートブック削除: {nb_id}")


async def cmd_list_sources(args):
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        sources = await client.sources.list(args.notebook_id)
        for s in sources:
            print(s.title or "")


async def cmd_add_text(args):
    if not args.file:
        print("エラー: --file を指定してください", file=sys.stderr)
        sys.exit(1)
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    title = args.title or os.path.basename(args.file)
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        await client.sources.add_text(args.notebook_id, title, text)
        print(f"✓ テキストソース追加: {title}")


async def cmd_add_source_file(args):
    """画像などを既存 notebook にファイルソースとして追加する。
    `--file` のローカルファイル、または `--url` の Drive URL を受け付ける。
    安定したソースタイトルを付けるため、`<title><ext>` というファイル名で add_file する
    （ソースタイトル＝ファイル名になり、次回 list-sources で検出できる）。"""
    import mimetypes
    import shutil
    if not args.file and not args.url:
        print("エラー: --file または --url を指定してください", file=sys.stderr)
        sys.exit(1)
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        if args.file:
            ext = os.path.splitext(args.file)[1]
            stable_dir = tempfile.mkdtemp(prefix='nblm_stable_')
            stable_path = os.path.join(stable_dir, f"{args.title}{ext}")
            shutil.copy(args.file, stable_path)
            await client.sources.add_file(args.notebook_id, stable_path, wait=True)
            os.unlink(stable_path)
            os.rmdir(stable_dir)
            print(f"✓ ファイルソース追加（local）: {args.title}{ext}")
            return
        m = re.search(r'drive\.google\.com/file/d/([\w-]+)', args.url)
        if m:
            file_id = m.group(1)
            tmp_no_ext = tempfile.NamedTemporaryFile(prefix='nblm_src_', delete=False)
            tmp_no_ext.close()
            drive_get = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drive_get.sh')
            subprocess.run(['bash', drive_get, file_id, tmp_no_ext.name], check=True)
            mime = subprocess.check_output(['file', '--mime-type', '-b', tmp_no_ext.name]).decode().strip()
            ext = mimetypes.guess_extension(mime) or ''
            stable_dir = tempfile.mkdtemp(prefix='nblm_stable_')
            stable_path = os.path.join(stable_dir, f"{args.title}{ext}")
            shutil.move(tmp_no_ext.name, stable_path)
            await client.sources.add_file(args.notebook_id, stable_path, wait=True)
            os.unlink(stable_path)
            os.rmdir(stable_dir)
            print(f"✓ ファイルソース追加（Drive, {mime}）: {args.title}{ext}")
        else:
            await client.sources.add_url(args.notebook_id, args.url)
            print(f"✓ ソース追加（URL）: {args.url}")


async def cmd_delete(args):
    async with await NotebookLMClient.from_storage(_storage_path()) as client:
        await client.notebooks.delete(args.notebook_id)
        print(f"✓ 削除: {args.notebook_id}")


def main():
    parser = argparse.ArgumentParser(description="NotebookLM 管理ツール")
    sub = parser.add_subparsers(dest="command")

    # list
    sub.add_parser("list", help="ノートブック一覧")

    # create
    p_create = sub.add_parser("create", help="ノートブック作成")
    p_create.add_argument("title", help="タイトル")
    p_create.add_argument("--urls", nargs="*", default=[], help="追加するURL（複数可）")

    # add-source
    p_add = sub.add_parser("add-source", help="ソースURL追加")
    p_add.add_argument("notebook_id", help="ノートブックID")
    p_add.add_argument("urls", nargs="+", help="追加するURL")

    # list-sources
    p_ls = sub.add_parser("list-sources", help="ノートブックのソースタイトル一覧")
    p_ls.add_argument("notebook_id", help="ノートブックID")

    # add-text
    p_at = sub.add_parser("add-text", help="既存ノートブックにテキストファイルをソース追加")
    p_at.add_argument("notebook_id", help="ノートブックID")
    p_at.add_argument("--file", default="", help="テキストファイルのパス")
    p_at.add_argument("--title", default="", help="ソースタイトル（既定: ファイル名）")

    # add-source-file
    p_asf = sub.add_parser("add-source-file", help="既存ノートブックにローカル/Drive画像をファイルソース追加")
    p_asf.add_argument("notebook_id", help="ノートブックID")
    p_asf.add_argument("--file", default="", help="ローカルファイルのパス")
    p_asf.add_argument("--url", default="", help="Drive URL（または通常URL）")
    p_asf.add_argument("--title", default="super-nyanko-ref", help="安定ソースタイトル（既定: super-nyanko-ref）")

    # ask
    p_ask = sub.add_parser("ask", help="ノートブックに質問")
    p_ask.add_argument("notebook_id", help="ノートブックID")
    p_ask.add_argument("question", help="質問文")

    # audio
    p_audio = sub.add_parser("audio", help="音声概要を生成")
    p_audio.add_argument("notebook_id", help="ノートブックID")
    p_audio.add_argument("--output", help="保存先パス（例: output.mp3）")

    # infographic
    p_info = sub.add_parser("infographic", help="インフォグラフィックを生成")
    p_info.add_argument("notebook_id", help="ノートブックID")
    p_info.add_argument("--instructions", default="", help="生成の指示（任意）")
    p_info.add_argument("--language", default="ja", help="言語コード（例: ja, en）デフォルト: ja")
    p_info.add_argument("--orientation", choices=["landscape", "portrait", "square"], default="landscape", help="向き")
    p_info.add_argument("--detail", choices=["concise", "standard", "detailed"], default="standard", help="詳細度")
    p_info.add_argument("--style", choices=["auto","sketch-note","professional","bento-grid","editorial","instructional","bricks","clay","anime","kawaii","scientific"], default="sketch-note", help="スタイル")
    p_info.add_argument("--output", help="保存先パス（例: output.png）")

    # make-infographic
    p_make = sub.add_parser("make-infographic", help="テキスト/ファイルからインフォグラフィックを生成")
    p_make.add_argument("--text", default="", help="インライン入力テキスト")
    p_make.add_argument("--file", default="", help="テキストファイルのパス")
    p_make.add_argument("--title", default="Infographic", help="ノートブックタイトル")
    p_make.add_argument("--infographic-title", default="", help="インフォグラフィックのタイトル")
    p_make.add_argument("--instructions", default="", help="生成の追加指示（任意）")
    p_make.add_argument("--language", default="ja", help="言語コード（例: ja, en）デフォルト: ja")
    p_make.add_argument("--orientation", choices=["landscape", "portrait", "square"], default="landscape")
    p_make.add_argument("--detail", choices=["concise", "standard", "detailed"], default="standard")
    p_make.add_argument("--style", choices=["auto","sketch-note","professional","bento-grid","editorial","instructional","bricks","clay","anime","kawaii","scientific"], default="sketch-note")
    p_make.add_argument("--output", required=True, help="保存先PNGパス（例: output.png）")
    p_make.add_argument("--keep", action="store_true", help="生成後もノートブックを残す")
    p_make.add_argument("--extra-source-url", action="append", default=[], help="追加で notebook に登録する URL（Drive 画像など、複数可）")

    # deep-research
    p_dr = sub.add_parser("deep-research", help="Deep Research を実行しソースを追加")
    p_dr.add_argument("notebook_id", help="ノートブックID")
    p_dr.add_argument("query", help="検索クエリ")

    # delete
    p_del = sub.add_parser("delete", help="ノートブック削除")
    p_del.add_argument("notebook_id", help="ノートブックID")

    args = parser.parse_args()

    cmd_map = {
        "list": cmd_list,
        "create": cmd_create,
        "add-source": cmd_add_source,
        "list-sources": cmd_list_sources,
        "add-text": cmd_add_text,
        "add-source-file": cmd_add_source_file,
        "ask": cmd_ask,
        "deep-research": cmd_deep_research,
        "audio": cmd_audio,
        "infographic": cmd_infographic,
        "make-infographic": cmd_make_infographic,
        "delete": cmd_delete,
    }

    if args.command not in cmd_map:
        parser.print_help()
        return

    asyncio.run(cmd_map[args.command](args))


if __name__ == "__main__":
    main()
