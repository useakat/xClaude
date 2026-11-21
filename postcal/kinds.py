"""postcal の定数: 投稿種類 → what_id、投稿枠、メディア制限、公開 URL。

Web アプリ（postcal/app.py）と cron ランナー（scripts/post_scheduled.py）の両方が参照する。
"""
import os

# 投稿種類 → (表示名, outputs に記録する what_id)。2026-11-15 よーん決定:
# 自己研鑽・フォロワー感謝は what シートに行を作らず W004（自己開示）として記録する
KINDS = {
    "short":  ("短文",         "z01"),
    "onepoint": ("ワンポイント解説", "W003"),
    "long":   ("長文",         "W001"),
    "study":  ("自己研鑽",     "W004"),
    "self":   ("自己開示",     "W004"),
    "thanks": ("フォロワー感謝", "W004"),
    "promo":  ("販促",         "W007"),
    # リライト（writer-xrewrite）。what_id は元投稿の what_id に r を付けたもの
    "rewrite_short":    ("リライト（短文）",         "z01r"),
    "rewrite_onepoint": ("リライト（ワンポイント）", "W003r"),
    "rewrite_long":     ("リライト（長文）",         "W001r"),
}

# cron の 4 枠（run_xonepoint_post.sh 06 / run_question_post.sh 12 / run_xlong_post.sh 17 / run_xshort_post.sh 20）
SLOTS = [6, 12, 17, 20]

MB = 1024 * 1024
# 拡張子 → 上限バイト。webp は tweepy の MIME 判定（mimetypes）が None を返して落ちるので受け付けない
IMAGE_EXT = {"png": 5 * MB, "jpg": 5 * MB, "jpeg": 5 * MB, "gif": 15 * MB}
VIDEO_EXT = {"mp4": 512 * MB, "mov": 512 * MB}
MAX_IMAGES = 4          # X の 1 ツイートあたりの画像上限
VIDEO_MAX_SECONDS = 140  # X の動画長上限（UI の注意書きのみ。ffprobe が無いので検査しない）

# メディアの公開 URL（Threads API がここから取得する）。Caddy で /m/* だけ Basic 認証を外す
PUBLIC_BASE_URL = os.environ.get("POSTCAL_PUBLIC_URL", "https://post.usephys.net").rstrip("/")

STATUSES = ("draft", "queued", "posting", "posted", "failed", "skipped")


def media_url(name: str) -> str:
    return f"{PUBLIC_BASE_URL}/m/{name}"


def ext_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
