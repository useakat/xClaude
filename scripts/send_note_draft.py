#!/usr/bin/env python3
"""
note.com に記事を下書き保存するスクリプト。

使い方:
    python3 send_note_draft.py "タイトル" "本文（Markdown）"
    python3 send_note_draft.py "タイトル" < article.md
    python3 send_note_draft.py "タイトル" --base-dir path/to/article --eyecatch thumbnail.png < article.md

本文中の Markdown 画像記法 ![alt](path) は、ローカルファイルなら note にアップロードして
figure タグとして埋め込む（--no-images で無効化）。--eyecatch でアイキャッチも設定できる。

note の非公開 API を使っているため、note 側の仕様変更で動かなくなることがある。
その場合は下書き本文だけ保存し、画像は note.com 上で手動設定に切り替えること。
"""
import os
import sys
import uuid
import re
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

NOTE_SESSION = os.getenv("NOTE_SESSION")  # .env に _note_session_v5 の値を設定

MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _headers(json_body: bool = True) -> dict:
    h = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"_note_session_v5={NOTE_SESSION}",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def _mime_of(path: Path) -> str:
    mime = MIME_BY_SUFFIX.get(path.suffix.lower())
    if not mime:
        raise ValueError(f"対応していない画像形式です: {path.name}")
    return mime


def _image_size(path: Path) -> tuple:
    """画像の (幅, 高さ) を返す。Pillow が無い・読めない場合は (None, None)。"""
    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size
    except Exception:
        return (None, None)


def upload_body_image(path: Path) -> dict:
    """本文用の画像を S3 へアップロードし、埋め込み用の情報を返す。

    ① note に presigned POST を要求 → ② 返ったフィールドごと S3 に multipart POST。
    x-amz-security-token を含む全フィールドをそのまま送らないと 403 になる。
    リクエストのキーは `filename`（2026-08 の仕様変更。旧 `file_name` は invalid_param で 400）。
    埋め込み URL はレスポンスの `url` をそのまま使う（`post.key` は `img/` を含むため連結すると重複する）。
    """
    mime = _mime_of(path)

    r = requests.post(
        "https://note.com/api/v3/images/upload/presigned_post",
        headers=_headers(),
        json={"content_type": mime, "filename": path.name},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()["data"]
    action = data["action"]
    fields = data["post"]

    with path.open("rb") as fp:
        r2 = requests.post(
            action,
            data=fields,
            files={"file": (path.name, fp, mime)},
            timeout=120,
        )
    r2.raise_for_status()

    width, height = _image_size(path)
    return {
        "src": data["url"],
        "width": width,
        "height": height,
    }


def upload_eyecatch(note_id, path: Path) -> str:
    """アイキャッチ（サムネイル）画像をアップロードして URL を返す。

    本文画像と違い note のサーバへ直接 multipart で送る。note_id を同梱すると
    その下書きに紐づくため draft_save 側での指定は不要。MIME 型を明示しないと 500 になる。
    """
    mime = _mime_of(path)
    width, height = _image_size(path)

    with path.open("rb") as fp:
        r = requests.post(
            "https://note.com/api/v1/image_upload/note_eyecatch",
            headers=_headers(json_body=False),
            data={
                "note_id": str(note_id),
                "width": str(width or 1920),
                "height": str(height or 1005),
            },
            files={"file": (path.name, fp, mime)},
            timeout=120,
        )
    if r.status_code not in (200, 201):
        r.raise_for_status()
    return r.json()["data"]["url"]


def md_to_note_html(md_text: str, image_resolver=None) -> str:
    """Markdown を note の内部 HTML 形式に変換する。

    image_resolver は ![alt](path) の path を受け取り、埋め込み情報 dict または
    None（＝変換せずそのまま残す）を返す関数。
    """
    lines = md_text.strip().split("\n")
    parts = [
        f'<table-of-contents name="{uuid.uuid4()}" id="{uuid.uuid4()}"><br></table-of-contents>'
    ]
    in_code_block = False
    code_lines = []

    img_pattern = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")

    for line in lines:
        uid = str(uuid.uuid4())

        # コードブロック処理
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_html = "<br>".join(code_lines)
                parts.append(f'<pre name="{uid}" id="{uid}"><code>{code_html}</code></pre>')
            continue

        if in_code_block:
            code_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        if line.strip() == "":
            continue

        # HTML コメント行（`<!-- ハッシュタグ -->` など）は本文に出さない
        if line.strip().startswith("<!--"):
            continue

        # 画像行（単独行の ![alt](path) のみ figure に変換する）
        m = img_pattern.match(line.strip())
        if m:
            info = image_resolver(m.group(2)) if image_resolver else None
            if info:
                alt = m.group(1).replace('"', "&quot;")
                size = ""
                if info.get("width") and info.get("height"):
                    size = f' width="{info["width"]}" height="{info["height"]}"'
                # figcaption は省略できない。無いとエディタが下書きを開けず 404 になる
                # （2026-08-13 検証。note 自身の出力にも data-align と空の figcaption が入る）
                parts.append(
                    f'<figure name="{uid}" id="{uid}" data-align="center">'
                    f'<img src="{info["src"]}" alt="{alt}"{size}>'
                    f"<figcaption></figcaption></figure>"
                )
            else:
                # 解決できなかった画像は、壊れたリンクにせず元の記法を残す
                escaped = line.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                parts.append(f'<p name="{uid}" id="{uid}">{escaped}</p>')
            continue

        # インライン変換
        def convert_inline(text):
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            # URL に括弧を含むリンク（Wikipedia の …/Opportunity_(rover) など）を
            # 最初の ")" で打ち切らないよう、括弧1段のネストを許す
            text = re.sub(
                r"\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))+)\)",
                r'<a href="\2">\1</a>',
                text,
            )
            return text

        if line.startswith("## "):
            parts.append(f'<h2 name="{uid}" id="{uid}">{convert_inline(line[3:])}</h2>')
        elif line.startswith("### "):
            parts.append(f'<h3 name="{uid}" id="{uid}">{convert_inline(line[4:])}</h3>')
        else:
            parts.append(f'<p name="{uid}" id="{uid}">{convert_inline(line)}</p>')

    return "\n".join(parts)


def create_draft(
    title: str,
    body_md: str,
    base_dir: Path = None,
    eyecatch: Path = None,
    upload_images: bool = True,
    note_id: int = None,
) -> dict:
    """下書きを保存する。

    note_id を渡すとその下書きを上書き更新し、省略すると新規作成する。
    画像アップロードだけ失敗したときに下書きを増やさず再実行できるようにするための引数。
    """
    base_dir = Path(base_dir) if base_dir else Path.cwd()
    uploaded = []
    failed = []
    cache = {}

    def resolve(src: str):
        # すでにホストされている画像はアップロード不要でそのまま埋め込む
        if src.startswith(("http://", "https://")):
            return {"src": src, "width": None, "height": None}
        if not upload_images or src.startswith("data:"):
            return None
        if src in cache:
            return cache[src]
        path = (base_dir / src).resolve()
        if not path.is_file():
            failed.append(f"{src}（ファイルが見つかりません）")
            cache[src] = None
            return None
        try:
            info = upload_body_image(path)
            uploaded.append(src)
        except Exception as e:
            failed.append(f"{src}（{type(e).__name__}: {e}）")
            info = None
        cache[src] = info
        return info

    # ① 下書きを新規作成（ID を取得）。note_id 指定時は既存の下書きを使う
    reused = note_id is not None
    if note_id is None:
        r1 = requests.post(
            "https://note.com/api/v1/text_notes",
            headers=_headers(),
            json={"draft": True, "name": title},
            timeout=30,
        )
        r1.raise_for_status()
        note_id = r1.json()["data"]["id"]

    body_html = md_to_note_html(body_md, image_resolver=resolve)

    # ② 本文とタイトルを保存
    r2 = requests.post(
        f"https://note.com/api/v1/text_notes/draft_save?id={note_id}",
        headers=_headers(),
        json={"name": title, "body": body_html},
        timeout=60,
    )
    r2.raise_for_status()

    # ③ アイキャッチ（任意）
    eyecatch_url = None
    if eyecatch:
        eyecatch_path = Path(eyecatch)
        if not eyecatch_path.is_absolute():
            eyecatch_path = (base_dir / eyecatch_path).resolve()
        try:
            eyecatch_url = upload_eyecatch(note_id, eyecatch_path)
        except Exception as e:
            failed.append(f"eyecatch {eyecatch}（{type(e).__name__}: {e}）")

    return {
        "note_id": note_id,
        "mode": "update" if reused else "create",
        "edit_url": f"https://note.com/notes/{note_id}/edit",
        "eyecatch_url": eyecatch_url,
        "uploaded_images": uploaded,
        "failed_images": failed,
    }


def main():
    ap = argparse.ArgumentParser(description="note.com に記事を下書き保存する")
    ap.add_argument("title", help="記事タイトル")
    ap.add_argument("body", nargs="?", help="本文 Markdown（省略時は標準入力）")
    ap.add_argument(
        "--base-dir",
        help="本文中の画像相対パスの基準ディレクトリ（既定: カレントディレクトリ）",
    )
    ap.add_argument("--eyecatch", help="アイキャッチ画像のパス（1280x672 推奨）")
    ap.add_argument(
        "--note-id",
        type=int,
        help="既存の下書き ID。指定するとその下書きを上書き更新する"
        "（画像だけ失敗したときの再実行用。省略時は新規作成）",
    )
    ap.add_argument(
        "--no-images",
        action="store_true",
        help="本文中の画像をアップロードせず Markdown のまま残す",
    )
    args = ap.parse_args()

    if not NOTE_SESSION:
        print("ERROR: NOTE_SESSION が .env に設定されていません", file=sys.stderr)
        sys.exit(1)

    body = args.body if args.body is not None else sys.stdin.read().strip()
    if not body:
        print("ERROR: 本文が空です", file=sys.stderr)
        sys.exit(1)

    result = create_draft(
        args.title,
        body,
        base_dir=args.base_dir,
        eyecatch=args.eyecatch,
        upload_images=not args.no_images,
        note_id=args.note_id,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["failed_images"]:
        # 画像が1点でも欠けた下書きは未完成。気づかず次の工程へ進まないよう明示する
        print(
            f"\nERROR: 画像 {len(result['failed_images'])} 点のアップロードに失敗しました。"
            "この下書きは未完成です。原因を直したうえで、"
            f"同じ下書きに --note-id {result['note_id']} を付けて再実行してください"
            "（新しい下書きを作らないため）。",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
