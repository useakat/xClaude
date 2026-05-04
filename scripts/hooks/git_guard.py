#!/usr/bin/env python3
import json, sys, os, re, subprocess
from pathlib import Path

d = json.load(sys.stdin)
cmd = d.get('tool_input', {}).get('command', '')

# ローカルセッションは通す
if os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
    sys.exit(0)

# ブランチ作成はブロック
if re.search(r'git\s+(-C\s+\S+\s+)?(checkout\s+.*-b\b|switch\s+-c\b|branch\s+[a-zA-Z_])', cmd):
    sys.exit(2)

# スクリプト自身の場所からリポジトリルートを解決（scripts/hooks/git_guard.py）
REPO = str(Path(__file__).resolve().parent.parent.parent)
ALLOWED_PREFIX = 'docs/reports/'

# git commit: ステージ済みファイルが全て docs/reports/ 配下なら許可
if re.search(r'git\s+(-C\s+\S+\s+)?commit\b', cmd):
    try:
        r = subprocess.run(
            ['git', '-C', REPO, 'diff', '--cached', '--name-only'],
            capture_output=True, text=True, timeout=5
        )
        files = [f for f in r.stdout.strip().split('\n') if f.strip()]
        if files and all(f.startswith(ALLOWED_PREFIX) for f in files):
            sys.exit(0)
    except Exception:
        pass
    sys.exit(2)

# git push: 未pushコミットのファイルが全て docs/reports/ 配下なら許可
if re.search(r'git\s+(-C\s+\S+\s+)?push\b', cmd):
    try:
        r = subprocess.run(
            ['git', '-C', REPO, 'log', '--name-only', '--pretty=format:', 'origin/master..HEAD'],
            capture_output=True, text=True, timeout=5
        )
        files = [f for f in r.stdout.strip().split('\n') if f.strip()]
        if files and all(f.startswith(ALLOWED_PREFIX) for f in files):
            sys.exit(0)
    except Exception:
        pass
    sys.exit(2)
