"""postcal — X 日次投稿の予約カレンダー（Web アプリ）。

予約の保管庫に徹する。投稿は cron の 4 枠（06/12/17/20）で scripts/post_scheduled.py が
この DB を読んで scripts/post_to_x.py / post_threads.py / record_output.py を呼ぶ。
このアプリ自身は X / Threads の秘密情報を持たない。

起動（systemd postcal.service）:
  /usr/bin/python3 -m uvicorn postcal.app:app --host 127.0.0.1 --port 8787
公開: Caddy が post.usephys.net → 127.0.0.1:8787（/m/* 以外は Basic 認証）。
"""
import calendar
import os
import re
import shutil
import uuid
from datetime import date, datetime, timedelta

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import db, kinds

HERE = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(HERE, "templates"))

REPLY_SPLIT_RE = re.compile(r"^[ \t]*={3,}[ \t]*$", re.M)   # post_threads.py と同じ分割マーカー
NOTE_URL_RE = re.compile(r"https?://(?:www\.)?note\.com/[A-Za-z0-9_]+/n/n[0-9a-f]{10,16}")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WEEKDAYS = ["日", "月", "火", "水", "木", "金", "土"]


def today_jst() -> date:
    return datetime.now(db.JST).date()


def month_bounds(ym: str):
    """'YYYY-MM' → (year, month)。不正なら今月"""
    try:
        y, m = ym.split("-")
        y, m = int(y), int(m)
        if not 1 <= m <= 12:
            raise ValueError
        return y, m
    except (ValueError, AttributeError):
        t = today_jst()
        return t.year, t.month


def decorate(p: dict, today: date, hour: int) -> dict:
    """テンプレート用の派生フィールド（表示名・状態クラス）"""
    p["kind_label"] = kinds.KINDS.get(p["kind"], (p["kind"],))[0]
    p["media_urls"] = [kinds.media_url(m["name"]) for m in p["media"]]
    d = date.fromisoformat(p["post_date"])
    overdue = p["status"] == "queued" and (d < today or (d == today and p["slot"] <= hour))
    p["state"] = "overdue" if overdue else p["status"]
    return p


def ctx_common(request: Request):
    return {"request": request, "kinds": kinds.KINDS, "slots": kinds.SLOTS, "weekdays": WEEKDAYS,
            "max_images": kinds.MAX_IMAGES, "video_max_seconds": kinds.VIDEO_MAX_SECONDS}


# ---------------- カレンダー ----------------

async def calendar_view(request: Request):
    y, m = month_bounds(request.query_params.get("month", ""))
    first = date(y, m, 1)
    last = date(y, m, calendar.monthrange(y, m)[1])
    now = datetime.now(db.JST)
    today, hour = now.date(), now.hour
    con = db.connect()
    try:
        rows = db.list_range(con, first.isoformat(), last.isoformat())
    finally:
        con.close()
    by_date = {}
    for p in rows:
        decorate(p, today, hour)
        by_date.setdefault(p["post_date"], []).append(p)
    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(y, m)  # 日曜始まり
    prev_m = (first - timedelta(days=1)).strftime("%Y-%m")
    next_m = (last + timedelta(days=1)).strftime("%Y-%m")
    ctx = ctx_common(request)
    ctx.update({"year": y, "month": m, "weeks": weeks, "by_date": by_date, "rows": rows,
                "today": today, "prev_month": prev_m, "next_month": next_m,
                "msg": request.query_params.get("msg", "")})
    return templates.TemplateResponse(request, "calendar.html", ctx)


# ---------------- フォーム ----------------

def empty_post(post_date: str) -> dict:
    return {"id": None, "post_date": post_date, "slot": 20, "kind": "self", "what_id": "W004", "text": "",
            "replies": [], "media": [], "threads_enabled": 1, "note_url": "", "status": "queued",
            "x_url": "", "threads_url": "", "error": "", "session_url": ""}


async def new_form(request: Request):
    d = request.query_params.get("date", "")
    if not DATE_RE.match(d):
        d = today_jst().isoformat()
    ctx = ctx_common(request)
    ctx.update({"post": empty_post(d), "errors": [], "replies_text": ""})
    return templates.TemplateResponse(request, "form.html", ctx)


async def edit_form(request: Request):
    post_id = int(request.path_params["post_id"])
    con = db.connect()
    try:
        p = db.get(con, post_id)
    finally:
        con.close()
    if not p:
        return PlainTextResponse("not found", status_code=404)
    now = datetime.now(db.JST)
    decorate(p, now.date(), now.hour)
    ctx = ctx_common(request)
    ctx.update({"post": p, "errors": [], "replies_text": "\n=====\n".join(p["replies"])})
    return templates.TemplateResponse(request, "form.html", ctx)


def _save_upload(upload) -> dict:
    """UploadFile を postcal/data/media/<uuid>.<ext> に保存して media 要素を返す"""
    ext = kinds.ext_of(upload.filename)
    name = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(db.MEDIA_DIR, exist_ok=True)
    upload.file.seek(0)
    with open(os.path.join(db.MEDIA_DIR, name), "wb") as out:
        shutil.copyfileobj(upload.file, out)
    kind = "video" if ext in kinds.VIDEO_EXT else "image"
    return {"name": name, "kind": kind, "orig": upload.filename}


def _remove_media_file(name: str):
    if re.fullmatch(r"[0-9a-f]{32}\.[a-z0-9]{2,5}", name):
        try:
            os.remove(os.path.join(db.MEDIA_DIR, name))
        except FileNotFoundError:
            pass


async def parse_form(request: Request, existing: dict | None):
    """フォームを検証して (data, errors, uploads) を返す。uploads は保存前の UploadFile 一覧。"""
    form = await request.form()
    errors = []
    data = {}

    post_date = (form.get("post_date") or "").strip()
    if not DATE_RE.match(post_date):
        errors.append("日付の形式が不正です")
    else:
        try:
            date.fromisoformat(post_date)
        except ValueError:
            errors.append("存在しない日付です")
    data["post_date"] = post_date

    try:
        slot = int(form.get("slot") or 0)
    except ValueError:
        slot = 0
    if slot not in kinds.SLOTS:
        errors.append("投稿時刻は 6 / 12 / 17 / 20 時のどれかを選んでください")
    data["slot"] = slot

    kind = form.get("kind") or ""
    if kind not in kinds.KINDS:
        errors.append("投稿種類を選んでください")
        data["what_id"] = ""
    else:
        data["what_id"] = kinds.KINDS[kind][1]
    data["kind"] = kind

    text = (form.get("text") or "").replace("\r\n", "\n").strip()
    if not text:
        errors.append("投稿文が空です")
    data["text"] = text

    replies_raw = (form.get("replies") or "").replace("\r\n", "\n")
    data["replies"] = [s.strip() for s in REPLY_SPLIT_RE.split(replies_raw) if s.strip()]

    data["threads_enabled"] = bool(form.get("threads_enabled"))

    note_url = (form.get("note_url") or "").strip()
    if not note_url:
        m = NOTE_URL_RE.search("\n".join(data["replies"]) + "\n" + text)
        note_url = m.group(0) if m else ""
    data["note_url"] = note_url

    # neta_id（ネタの出所。フォームには項目が無いので、編集時は既存値を保つ。
    # z01 の予約には postcal_import.py が noteNeta[..] 等を入れる）
    data["neta_id"] = (existing.get("neta_id", "") if existing else "")
    # session_url（原稿を作った Claude セッション。同じくフォームに項目は無いので、編集時は既存値を保つ）
    data["session_url"] = (existing.get("session_url", "") if existing else "")

    # メディア: 既存（削除指定を除く）＋ 新規アップロード
    keep = list(existing["media"]) if existing else []
    remove = set(form.getlist("remove_media"))
    keep = [m for m in keep if m["name"] not in remove]
    data["_removed"] = [m["name"] for m in (existing["media"] if existing else []) if m["name"] in remove]

    uploads = []
    for f in form.getlist("media"):
        if not getattr(f, "filename", ""):
            continue
        ext = kinds.ext_of(f.filename)
        if ext not in kinds.IMAGE_EXT and ext not in kinds.VIDEO_EXT:
            errors.append(f"{f.filename}: 対応していない形式です（png/jpg/jpeg/gif/mp4/mov）")
            continue
        f.file.seek(0, os.SEEK_END)
        size = f.file.tell()
        f.file.seek(0)
        limit = kinds.IMAGE_EXT.get(ext) or kinds.VIDEO_EXT.get(ext)
        if size > limit:
            errors.append(f"{f.filename}: {size / kinds.MB:.1f}MB は上限 {limit // kinds.MB}MB を超えています")
            continue
        uploads.append(f)

    all_kinds = [m["kind"] for m in keep] + [("video" if kinds.ext_of(f.filename) in kinds.VIDEO_EXT else "image") for f in uploads]
    n_img, n_vid = all_kinds.count("image"), all_kinds.count("video")
    if n_vid > 1:
        errors.append("動画は 1 本までです")
    if n_vid and n_img:
        errors.append("画像と動画は同時に付けられません")
    if n_img > kinds.MAX_IMAGES:
        errors.append(f"画像は {kinds.MAX_IMAGES} 枚までです")
    data["media"] = keep
    return data, errors, uploads


def _render_form_error(request, data, errors, existing):
    p = dict(existing) if existing else empty_post(data.get("post_date") or today_jst().isoformat())
    p.update({k: v for k, v in data.items() if not k.startswith("_")})
    p["threads_enabled"] = 1 if data.get("threads_enabled") else 0
    now = datetime.now(db.JST)
    if p.get("status"):
        try:
            decorate(p, now.date(), now.hour)
        except ValueError:
            p["state"] = p["status"]
    ctx = ctx_common(request)
    ctx.update({"post": p, "errors": errors, "replies_text": "\n=====\n".join(data.get("replies", []))})
    return templates.TemplateResponse(request, "form.html", ctx, status_code=400)


async def create_post(request: Request):
    data, errors, uploads = await parse_form(request, None)
    con = db.connect()
    try:
        if not errors and db.slot_taken(con, data["post_date"], data["slot"]):
            errors.append(f"{data['post_date']} {data['slot']}時 の枠にはすでに予約があります（1 枠 1 投稿）")
        if errors:
            return _render_form_error(request, data, errors, None)
        data["media"] = data["media"] + [_save_upload(f) for f in uploads]
        post_id = db.create(con, data)
    finally:
        con.close()
    return RedirectResponse(f"/?month={data['post_date'][:7]}&msg=登録しました（#{post_id}）", status_code=303)


async def update_post(request: Request):
    post_id = int(request.path_params["post_id"])
    con = db.connect()
    try:
        existing = db.get(con, post_id)
        if not existing:
            return PlainTextResponse("not found", status_code=404)
        if existing["status"] == "posting":
            return PlainTextResponse("投稿処理中のため編集できません", status_code=409)
        data, errors, uploads = await parse_form(request, existing)
        # 「投稿予約」（draft → queued）/「下書きに戻す」（queued → draft）。ボタンの name=action で区別する
        action = ((await request.form()).get("action") or "").strip()
        approve = action == "approve" and existing["status"] == "draft"
        unapprove = action == "unapprove" and existing["status"] == "queued"
        if not errors and db.slot_taken(con, data["post_date"], data["slot"], exclude_id=post_id):
            errors.append(f"{data['post_date']} {data['slot']}時 の枠にはすでに予約があります（1 枠 1 投稿）")
        if approve and not errors:
            now = datetime.now(db.JST)
            d = date.fromisoformat(data["post_date"])
            if d < now.date() or (d == now.date() and data["slot"] <= now.hour):
                errors.append("過ぎた枠には投稿予約できません。日付・時刻を直してから「投稿予約」を押してください")
        if errors:
            return _render_form_error(request, data, errors, existing)
        data["media"] = data["media"] + [_save_upload(f) for f in uploads]
        db.update(con, post_id, data)
        # 失敗した予約を直して保存したら、再び queued に戻す（投稿済みは触らない）
        if existing["status"] == "failed":
            db.set_status(con, post_id, "queued", error="")
        if approve:
            db.set_status(con, post_id, "queued")
        elif unapprove:
            db.set_status(con, post_id, "draft")
        for name in data["_removed"]:
            _remove_media_file(name)
    finally:
        con.close()
    msg = ("投稿予約しました" if approve else "下書きに戻しました" if unapprove else "更新しました") + f"（#{post_id}）"
    return RedirectResponse(f"/?month={data['post_date'][:7]}&msg={msg}", status_code=303)


async def delete_post(request: Request):
    post_id = int(request.path_params["post_id"])
    con = db.connect()
    try:
        p = db.get(con, post_id)
        if not p:
            return PlainTextResponse("not found", status_code=404)
        if p["status"] in ("posting", "posted"):
            return PlainTextResponse("投稿済み・処理中の予約は削除できません", status_code=409)
        db.delete(con, post_id)
    finally:
        con.close()
    for m in p["media"]:
        _remove_media_file(m["name"])
    return RedirectResponse(f"/?month={p['post_date'][:7]}&msg=削除しました（#{post_id}）", status_code=303)


async def healthz(request: Request):
    return PlainTextResponse("ok")


os.makedirs(db.MEDIA_DIR, exist_ok=True)

routes = [
    Route("/", calendar_view),
    Route("/new", new_form),
    Route("/posts", create_post, methods=["POST"]),
    Route("/posts/{post_id:int}", edit_form),
    Route("/posts/{post_id:int}", update_post, methods=["POST"]),
    Route("/posts/{post_id:int}/delete", delete_post, methods=["POST"]),
    Route("/healthz", healthz),
    Mount("/m", StaticFiles(directory=db.MEDIA_DIR), name="media"),       # 公開（Threads が取得）
    Mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static"),
]

app = Starlette(routes=routes)
