#!/bin/bash
# 【threads投稿】メールを Threads に投稿する cron ラッパー。
# 専用 cron は無い。X 投稿 cron（06/12/17/20）が X に投稿が無かったときのフォールバックとして呼ぶ。
# （2026-11-12 に足した 09:00 専用枠は 2026-11-22 に削除。4 枠のどこかで拾われるため）
export PATH="/usr/local/bin:$PATH"
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"

DIR="$(dirname "$0")"
exec /bin/bash "$DIR/post_threads_from_email.sh"
