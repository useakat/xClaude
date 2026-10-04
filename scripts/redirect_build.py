#!/usr/bin/env python3
"""
bio / 固定ポスト / 投稿用の転送サイト（Caddy）を redirect/redirects.json から生成する。

生成物:
  /var/www/redirect/<host>/index.html            … ホスト直下（キー無し）の HTML 転送ページ
  /var/www/redirect/<host>/<key>/index.html      … paths を持つホストのキー別転送ページ
  /etc/caddy/Caddyfile                            … ホストごとの site ブロック

転送ページ（人向け）: meta referrer=origin / meta refresh / JS で note へ。JS が /hit?k=<key> にビーコンを
  送るので、その件数＝人のクリック（スキャナは JS を実行しない）。参照元は自ホストになり、note の
  流入元にホスト別の行が立つ。
クローラ（Twitterbot / facebookexternalhit 等）: HTML ではなく 302 で転送先へ飛ばす。クローラは JS も
  meta refresh も追わないので、HTML を返すとカード（サムネ付きプレビュー）が出ない。302 なら
  クローラが note 本体の OG タグを読んでカードを作る。

使い方:
  python3 scripts/redirect_build.py            # 生成内容を表示（書き込まない）
  sudo python3 scripts/redirect_build.py --apply   # 書き込み＋ `caddy reload`
"""

import argparse
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONF = REPO_ROOT / "redirect" / "redirects.json"
TEMPLATE = REPO_ROOT / "redirect" / "template.html"
WWW_ROOT = Path("/var/www/redirect")
CADDYFILE = Path("/etc/caddy/Caddyfile")
LOG_DIR = Path("/var/log/caddy")

# カードを作りに来るクローラ。これらには 302 で転送先へ飛ばす
CRAWLER_UA = r"(?i)(Twitterbot|facebookexternalhit|Facebot|LinkedInBot|Slackbot|Discordbot|TelegramBot|WhatsApp|Applebot|Line/|Pinterestbot|Embedly|Iframely)"

# route {} で実行順を固定する（Caddy 既定の順序では try_files が respond より先に動き、
# /hit が /index.html に書き換えられてビーコンが 405/200 になる）
SITE_BLOCK = """{host} {{
\troot * {www}/{host}
\t@crawler header_regexp ua User-Agent {crawler_ua}
\tmap {{path}} {{target}} {{
{map_rows}
\t\tdefault {default_target}
\t}}
\troute {{
\t\trespond /hit 204
\t\tredir @crawler {{target}} 302
\t\ttry_files {{path}} {{path}}/ /index.html
\t\tfile_server
\t}}
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


def render(tmpl: str, target: str, key: str) -> str:
    return tmpl.replace("{{TARGET}}", target).replace("{{KEY}}", key)


def resolves_here(host: str, server_ip: str) -> bool:
    """DNS がこのサーバーを向いているか。向いていないホストを Caddyfile に入れると証明書取得の失敗を繰り返すので除外する"""
    try:
        return socket.gethostbyname(host) == server_ip
    except OSError:
        return False


def build(conf: dict, check_dns: bool = False) -> tuple[dict[str, str], str]:
    """(相対パス→HTML の辞書, Caddyfile 文字列) を返す。check_dns=True なら DNS 未設定のホストを除外する"""
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    pages: dict[str, str] = {}
    blocks = []
    server_ip = conf.get("server_ip", "")
    for host, h in conf["hosts"].items():
        if check_dns and server_ip and not resolves_here(host, server_ip):
            print(f"⚠ {host}: DNS がこのサーバー（{server_ip}）を向いていないため今回は除外（A レコード追加後に再実行）", file=sys.stderr)
            continue
        pages[f"{host}/index.html"] = render(tmpl, h["target"], "_root")
        map_rows = []
        for key, p in (h.get("paths") or {}).items():
            pages[f"{host}/{key}/index.html"] = render(tmpl, p["target"], key)
            map_rows.append(f"\t\t/{key} {p['target']}")
            map_rows.append(f"\t\t/{key}/ {p['target']}")
        blocks.append(SITE_BLOCK.format(
            host=host, www=WWW_ROOT, logdir=LOG_DIR, crawler_ua=CRAWLER_UA,
            map_rows="\n".join(map_rows) if map_rows else "\t\t# (paths なし)",
            default_target=h["target"],
        ))
    caddy = "# 生成元: redirect/redirects.json（scripts/redirect_build.py --apply）。手で編集しない\n\n" + "\n".join(blocks)
    return pages, caddy


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="ファイルを書き込み、caddy を reload する（要 root）")
    args = ap.parse_args()

    conf = json.loads(CONF.read_text(encoding="utf-8"))
    pages, caddy = build(conf, check_dns=args.apply)

    if not args.apply:
        for host, h in conf["hosts"].items():
            print(f"{host}  →  {h['target']}")
            for key, p in (h.get("paths") or {}).items():
                print(f"  /{key}  →  {p['target']}  ({p.get('memo', '')})")
        print("\n----- Caddyfile -----\n" + caddy)
        return 0

    # 生成物を書き、paths から消えたキーのディレクトリは削除する
    for rel, html in pages.items():
        f = WWW_ROOT / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
    for host, h in conf["hosts"].items():
        keep = set((h.get("paths") or {}).keys())
        for d in (WWW_ROOT / host).iterdir() if (WWW_ROOT / host).exists() else []:
            if d.is_dir() and d.name not in keep:
                shutil.rmtree(d)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.chown(LOG_DIR, user="caddy", group="caddy")
    CADDYFILE.parent.mkdir(parents=True, exist_ok=True)
    CADDYFILE.write_text(caddy, encoding="utf-8")
    subprocess.run(["caddy", "fmt", "--overwrite", str(CADDYFILE)], check=False)
    v = subprocess.run(["caddy", "validate", "--config", str(CADDYFILE), "--adapter", "caddyfile"],
                       capture_output=True, text=True)
    if v.returncode != 0:
        print("Caddyfile の検証に失敗:", v.stderr.strip()[-800:], file=sys.stderr)
        return 1
    # validate を root で実行するとログファイルが root 所有で作られ、caddy ユーザーが開けず reload が失敗する
    # （2026-10-04 に発生）。所有者を caddy に戻してから reload する
    for p in LOG_DIR.glob("*"):
        shutil.chown(p, user="caddy", group="caddy")
    r = subprocess.run(["systemctl", "reload", "caddy"], capture_output=True, text=True)
    if r.returncode != 0:
        print("caddy reload 失敗:", r.stderr.strip(), file=sys.stderr)
        return 1
    print(f"✅ {len(conf['hosts'])} ホスト・{len(pages)} ページを反映し、caddy を reload しました")
    for host, h in conf["hosts"].items():
        print(f"   https://{host}  →  {h['target']}")
        for key, p in (h.get("paths") or {}).items():
            print(f"     /{key}  →  {p['target']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
