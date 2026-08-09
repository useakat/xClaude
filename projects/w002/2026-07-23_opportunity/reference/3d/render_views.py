#!/usr/bin/env python3
"""NASA オポチュニティ (MER-B) の .glb から同一縮尺・正投影・白背景の10視点PNGを生成する。

`projects/w002/2026-07-04_kepler-k2-revival/draft/images/3d/render_views.py` を流用。
入力の GLB は Draco 圧縮のため、事前に以下でデコードしておくこと:
  npx --yes @gltf-transform/cli@4 copy opportunity_mer-b.glb opportunity_decoded.glb

出力:
  views/01_正面.png ... views/10_背面側上斜め45度俯瞰.png (2048x2048)
  opportunity_10views_contact_sheet.png (一覧)
  opportunity_10views.zip (全ファイル)
"""
import os
import zipfile

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np
import trimesh
import pyrender
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.environ.get("GLB") or os.path.join(HERE, "mer_static_highpoly.glb")
OUT = os.environ.get("OUT") or os.path.join(HERE, "views")
RES = 2048          # 各視点の解像度
MARGIN = 1.12       # バウンディング球に対する余白
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# 視点定義: (連番, ラベル, 方位角[deg], 仰角[deg], [up ベクトル])
# 方位角: 正面を 0 とし、モデルから見て左回りを正 / 仰角: 水平 0、上 +90
# AZ_OFFSET: 「正面」をモデルのどの向きにするか（ロボットアームが前方）
AZ_OFFSET = 0
VIEWS = [
    ("01", "正面", 0, 0),
    ("02", "前方左斜め45度", 45, 0),
    ("03", "前方右斜め45度", -45, 0),
    ("04", "左側面", 90, 0),
    ("05", "右側面", -90, 0),
    ("06", "背面", 180, 0),
    ("07", "上面", 0, 90),
    ("08", "下面", 0, -90),
    ("09", "前方斜め上45度俯瞰", 45, 45),
    ("10", "地表からの煽り", 30, -25),
]


def look_at(eye, target, up):
    """カメラの pose 行列 (OpenGL 慣習: -Z が視線方向)"""
    eye = np.asarray(eye, dtype=float)
    target = np.asarray(target, dtype=float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.asarray(up, dtype=float)
    right = np.cross(fwd, up)
    if np.linalg.norm(right) < 1e-8:   # 真上・真下では up を取り直す
        up = np.array([0.0, 0.0, -1.0])
        right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, fwd)
    m = np.eye(4)
    m[:3, 0] = right
    m[:3, 1] = true_up
    m[:3, 2] = -fwd
    m[:3, 3] = eye
    return m


def main():
    os.makedirs(OUT, exist_ok=True)

    tm = trimesh.load(GLB)
    meshes = tm.dump(concatenate=False) if isinstance(tm, trimesh.Scene) else [tm]

    all_pts = np.vstack([m.bounds for m in meshes])
    lo, hi = all_pts.min(axis=0), all_pts.max(axis=0)
    center = (lo + hi) / 2.0
    radius = float(np.linalg.norm(hi - lo) / 2.0)
    mag = radius * MARGIN          # 正投影の半視野（全視点で固定＝同一縮尺）
    dist = radius * 4.0

    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0],
                           ambient_light=[0.35, 0.35, 0.35])
    for m in meshes:
        scene.add(pyrender.Mesh.from_trimesh(m, smooth=False))

    cam = pyrender.OrthographicCamera(xmag=mag, ymag=mag, znear=0.01,
                                      zfar=dist + radius * 4.0)
    cam_node = scene.add(cam, pose=np.eye(4))

    key = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)
    key_node = scene.add(key, pose=np.eye(4))
    for d in ([1, 1, 1], [-1, 0.5, -1], [0, -1, 0.5]):
        d = np.asarray(d, dtype=float)
        pose = look_at(center + d / np.linalg.norm(d) * dist, center, [0, 1, 0])
        scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=1.2),
                  pose=pose)

    r = pyrender.OffscreenRenderer(RES, RES)
    paths = []
    for view in VIEWS:
        num, label, az, el = view[:4]
        up_vec = view[4] if len(view) > 4 else [0, 1, 0]
        a = np.radians(az + AZ_OFFSET)
        e = np.radians(el)
        direction = np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
        eye = center + direction * dist
        pose = look_at(eye, center, up_vec)
        scene.set_pose(cam_node, pose)
        scene.set_pose(key_node, pose)
        color, _ = r.render(scene)
        path = os.path.join(OUT, f"{num}_{label}.png")
        Image.fromarray(color).save(path)
        paths.append((path, f"{num} {label}"))
        print(f"rendered: {os.path.basename(path)}")
    r.delete()

    # --- 一覧画像（横4列）---
    cell, pad, label_h, cols = 620, 18, 54, 4
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB",
                      (cell * cols + pad * (cols + 1),
                       (cell + label_h) * rows + pad * (rows + 1)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 30, index=0)
    for i, (path, label) in enumerate(paths):
        row, col = divmod(i, cols)
        x = pad + col * (cell + pad)
        y = pad + row * (cell + label_h + pad)
        sheet.paste(Image.open(path).resize((cell, cell), Image.LANCZOS), (x, y))
        draw.text((x + cell / 2, y + cell + 6), label, fill="black", font=font, anchor="ma")
    sheet_path = os.path.join(HERE, "opportunity_10views_contact_sheet.png")
    sheet.save(sheet_path)
    print(f"contact sheet: {os.path.basename(sheet_path)}")

    zip_path = os.path.join(HERE, "opportunity_10views.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path, _ in paths:
            z.write(path, os.path.join("views", os.path.basename(path)))
        z.write(sheet_path, os.path.basename(sheet_path))
    print(f"zip: {os.path.basename(zip_path)}")


if __name__ == "__main__":
    main()
