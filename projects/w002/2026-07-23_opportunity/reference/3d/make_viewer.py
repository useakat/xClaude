#!/usr/bin/env python3
"""オポチュニティ (MER-B) の .glb から、単一HTMLで完結する対話式3Dビューアを生成する。

`projects/w002/2026-07-04_kepler-k2-revival/draft/images/3d/kepler_viewer.html` の
ビューア（WebGL・スライダーで任意角度・PNG保存）を流用し、メッシュデータだけ差し替える。

メッシュの埋め込み形式（ビューア側のデコードに合わせる）:
  pos : Int16  正規化（[-1,1] にスケールしたモデル座標 × 32767）
  nrm : Int8   正規化（法線 × 127）
  col : Uint8  頂点カラー（マテリアルの baseColorFactor をガンマ補正して割り当て）

使い方:
  python3 make_viewer.py           # opportunity_viewer.html を生成
"""
import base64
import json
import os
import re

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.environ.get("GLB") or os.path.join(HERE, "mer_static_highpoly.glb")
TEMPLATE = os.path.join(
    HERE, "..", "..", "..", "2026-07-04_kepler-k2-revival", "draft", "images", "3d",
    "kepler_viewer.html")
OUT_HTML = os.environ.get("OUT_HTML") or os.path.join(HERE, "opportunity_viewer.html")
OUT_JSON = os.path.join(HERE, "opportunity_mesh.json")

# ビューアの文言差し替え（ケプラー固有 → オポチュニティ）
REPLACEMENTS = [
    ("<title>ケプラー 姿勢ビューア</title>", "<title>オポチュニティ 姿勢ビューア</title>"),
    ("<h1>ケプラー 姿勢ビューア</h1>", "<h1>オポチュニティ 姿勢ビューア</h1>"),
    ('<div class="axis-name">ロール<span>鏡筒の軸まわり</span></div>',
     '<div class="axis-name">ロール<span>進行方向の軸まわり</span></div>'),
    ('<div class="axis-name">ヨー<span>開口部を手前へ</span></div>',
     '<div class="axis-name">ヨー<span>機体を水平に回す</span></div>'),
    ('<button data-p="45,30,0">尾根＋開口部<small>45 / 30 / 0</small></button>',
     '<button data-p="20,35,0">斜め前から<small>20 / 35 / 0</small></button>'),
    ('<button data-p="45,30,30">立ち姿<small>45 / 30 / 30</small></button>',
     '<button data-p="-25,30,0">地表からの煽り<small>-25 / 30 / 0</small></button>'),
    ('<button data-p="0,90,0">開口部を正面<small>0 / 90 / 0</small></button>',
     '<button data-p="0,90,0">側面<small>0 / 90 / 0</small></button>'),
    ('<button data-p="90,0,0">パネル全面<small>90 / 0 / 0</small></button>',
     '<button data-p="90,0,0">上面（パネル全面）<small>90 / 0 / 0</small></button>'),
]


def srgb(c):
    """glTF の baseColorFactor（リニア）を sRGB 8bit に変換する。"""
    c = np.clip(np.asarray(c, dtype=float), 0.0, 1.0)
    out = np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)
    return np.round(np.clip(out, 0, 1) * 255).astype(np.uint8)


def bake_colors(m):
    """メッシュの頂点カラーを返す。テクスチャがあれば UV でサンプルして焼き込む。"""
    n = len(m.vertices)
    vis = m.visual
    # 1) 既に頂点カラーを持つ場合
    try:
        if getattr(vis, "kind", None) == "vertex" and vis.vertex_colors is not None:
            return np.asarray(vis.vertex_colors)[:, :3].astype(np.uint8)
    except Exception:
        pass
    # 2) テクスチャ + UV
    try:
        mat = vis.material
        img = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)
        uv = np.asarray(vis.uv, dtype=float) if vis.uv is not None else None
        if img is not None and uv is not None and len(uv) == n:
            tex = np.asarray(img.convert("RGB"))
            h, w = tex.shape[:2]
            px = np.clip((uv[:, 0] % 1.0) * (w - 1), 0, w - 1).astype(int)
            py = np.clip((1.0 - (uv[:, 1] % 1.0)) * (h - 1), 0, h - 1).astype(int)
            return tex[py, px].astype(np.uint8)
    except Exception:
        pass
    # 3) 単色マテリアル
    try:
        f = vis.material.baseColorFactor
        if f is not None:
            f = np.asarray(f, dtype=float)[:3]
            if f.max() > 1.5:
                f = f / 255.0
            return np.tile(srgb(f), (n, 1))
    except Exception:
        pass
    return np.tile(np.array([160, 160, 160], dtype=np.uint8), (n, 1))


def main():
    tm = trimesh.load(GLB)
    meshes = tm.dump(concatenate=False) if isinstance(tm, trimesh.Scene) else [tm]

    all_b = np.vstack([m.bounds for m in meshes])
    lo, hi = all_b.min(axis=0), all_b.max(axis=0)
    center = (lo + hi) / 2.0
    scale = float(np.abs(np.vstack([m.vertices for m in meshes]) - center).max())

    pos_l, nrm_l, col_l = [], [], []
    for m in meshes:
        v = (np.asarray(m.vertices, dtype=np.float64) - center) / scale   # [-1,1]
        f = np.asarray(m.faces)
        n = np.asarray(m.face_normals, dtype=np.float64)
        vc = bake_colors(m)                          # (V,3) 頂点カラー
        tri = v[f]                                   # (F,3,3)
        pos_l.append(tri.reshape(-1, 3))
        nrm_l.append(np.repeat(n, 3, axis=0))
        col_l.append(vc[f].reshape(-1, 3))

    pos = np.concatenate(pos_l)
    nrm = np.concatenate(nrm_l)
    col = np.concatenate(col_l)
    n_vert = len(pos)

    pos_i = np.clip(np.round(pos * 32767), -32768, 32767).astype("<i2")
    nrm_i = np.clip(np.round(nrm * 127), -128, 127).astype("<i1")
    col_i = col.astype(np.uint8)

    mesh = {
        "n": int(n_vert),
        "pos": base64.b64encode(pos_i.tobytes()).decode("ascii"),
        "nrm": base64.b64encode(nrm_i.tobytes()).decode("ascii"),
        "col": base64.b64encode(col_i.tobytes()).decode("ascii"),
    }
    with open(OUT_JSON, "w") as fp:
        json.dump(mesh, fp)
    print(f"mesh: {n_vert} vertices ({n_vert // 3} triangles) -> {os.path.basename(OUT_JSON)}")

    html = open(TEMPLATE).read()
    blob = '<script id="mesh" type="application/json">' + json.dumps(mesh) + "</script>"
    html = re.sub(r'<script id="mesh" type="application/json">.*?</script>', blob,
                  html, flags=re.S)
    for a, b in REPLACEMENTS:
        if a not in html:
            print(f"  warn: 差し替え対象が見つかりません: {a[:40]}")
        html = html.replace(a, b)
    with open(OUT_HTML, "w") as fp:
        fp.write(html)
    print(f"viewer: {os.path.basename(OUT_HTML)} ({os.path.getsize(OUT_HTML)//1024} KB)")


if __name__ == "__main__":
    main()
