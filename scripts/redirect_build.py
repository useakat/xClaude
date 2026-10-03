#!/usr/bin/env python3
"""
bio / 固定ポスト用の転送サイト（Caddy）を redirect/redirects.json から生成する。

生成物:
  /var/www/redirect/<host>/index.html   … HTML 転送ページ（meta referrer=origin / meta refresh / JS）
  /etc/caddy/Caddyfile                   … ホストごとの site ブロック（file_server・JSON アクセスログ）

なぜ 302 ではなく HTML 転送か:
  302 だと note が受け取る参照元は元のまま（X / 直接・不明）で経路を判別できない。
  HTML ページを一度開いてから移動すると参照元が自ドメインになり、note の流入元に
  ホスト別の行（xbio.usephys.com 等）が立つ。X アプリで落ちていた参照元も付くようになる。

使い方:
  python3 scripts/redirect_build.py            # 生成内容を表示（書き込まない）
  sudo python3 scripts/redirect_build.py --apply   # 書き込み＋ `caddy reload`
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONF = REPO_ROOT / "redirect" / "redirects.json"
TEMPLATE = REPO_ROOT / "redirect" / "template.html"
WWW_ROOT = Path("/var/www/redirect")
CADDYFILE = Path("/etc/caddy/Caddyfile")
LOG_DIR = Path("/var/log/caddy")

SITE_BLOCK = """{host} {{
\troot * {www}/{host}
\tfile_server
\theader Referrer-Policy "origin"
\theader X-Robots-Tag "noindex, nofollow"
\theader Cache-Control "no-store"
\tlog {{
\t\toutput file {logdir}/{host}.log {{
\t\t\troll_size 10mb
\t\t\troll_keep 12
\t\t}}
\t\tformat json
\t}}
}}
"""


def build(conf: dict) -> tuple[dict[str, str], str]:
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    pages = {host: tmpl.replace("{{TARGET}}", h["target"]) for host, h in conf["hosts"].items()}
    caddy = "# 生成元: redirect/redirects.json（scripts/redirect_build.py --apply）。手で編集しない\n\n"
    caddy += "\n".join(SITE_BLOCK.format(host=host, www=WWW_ROOT, logdir=LOG_DIR) for host in conf["hosts"])
    return pages, caddy


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="ファイルを書き込み、caddy を reload する（要 root）")
    args = ap.parse_args()

    conf = json.loads(CONF.read_text(encoding="utf-8"))
    pages, caddy = build(conf)

    if not args.apply:
        for host, h in conf["hosts"].items():
            print(f"{host}  →  {h['target']}")
        print("\n----- Caddyfile -----\n" + caddy)
        return 0

    for host, html in pages.items():
        d = WWW_ROOT / host
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(html, encoding="utf-8")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.chown(LOG_DIR, user="caddy", group="caddy")
    CADDYFILE.parent.mkdir(parents=True, exist_ok=True)
    CADDYFILE.write_text(caddy, encoding="utf-8")
    subprocess.run(["caddy", "fmt", "--overwrite", str(CADDYFILE)], check=False)
    r = subprocess.run(["systemctl", "reload", "caddy"], capture_output=True, text=True)
    if r.returncode != 0:
        print("caddy reload 失敗:", r.stderr.strip(), file=sys.stderr)
        return 1
    print(f"✅ {len(pages)} ホストの転送ページと Caddyfile を反映し、caddy を reload しました")
    for host, h in conf["hosts"].items():
        print(f"   https://{host}  →  {h['target']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
