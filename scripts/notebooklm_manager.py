#!/usr/bin/env python3
"""NotebookLM manager for Claude Code integration."""

import argparse
import asyncio
import sys

from notebooklm import NotebookLMClient
from notebooklm.types import InfographicOrientation, InfographicDetail, InfographicStyle


async def cmd_list(args):
    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        if not notebooks:
            print("ノートブックなし")
            return
        for nb in notebooks:
            print(f"{nb.id}\t{nb.title}")


async def cmd_create(args):
    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(args.title)
        print(f"✓ 作成: {nb.id}\t{nb.title}")
        if args.urls:
            for url in args.urls:
                await client.sources.add_url(nb.id, url)
                print(f"  ソース追加: {url}")
        return nb.id


async def cmd_add_source(args):
    async with await NotebookLMClient.from_storage() as client:
        for url in args.urls:
            await client.sources.add_url(args.notebook_id, url)
            print(f"✓ ソース追加: {url}")


async def cmd_ask(args):
    async with await NotebookLMClient.from_storage() as client:
        result = await client.chat.ask(args.notebook_id, args.question)
        print(result)


async def cmd_audio(args):
    async with await NotebookLMClient.from_storage() as client:
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
    async with await NotebookLMClient.from_storage() as client:
        print("インフォグラフィックを生成中...")
        status = await client.artifacts.generate_infographic(
            args.notebook_id,
            instructions=args.instructions or None,
            orientation=orientation_map[args.orientation],
            detail_level=detail_map[args.detail],
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


async def cmd_delete(args):
    async with await NotebookLMClient.from_storage() as client:
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
    p_info.add_argument("--orientation", choices=["landscape", "portrait", "square"], default="landscape", help="向き")
    p_info.add_argument("--detail", choices=["concise", "standard", "detailed"], default="standard", help="詳細度")
    p_info.add_argument("--output", help="保存先パス（例: output.png）")

    # delete
    p_del = sub.add_parser("delete", help="ノートブック削除")
    p_del.add_argument("notebook_id", help="ノートブックID")

    args = parser.parse_args()

    cmd_map = {
        "list": cmd_list,
        "create": cmd_create,
        "add-source": cmd_add_source,
        "ask": cmd_ask,
        "audio": cmd_audio,
        "infographic": cmd_infographic,
        "delete": cmd_delete,
    }

    if args.command not in cmd_map:
        parser.print_help()
        return

    asyncio.run(cmd_map[args.command](args))


if __name__ == "__main__":
    main()
