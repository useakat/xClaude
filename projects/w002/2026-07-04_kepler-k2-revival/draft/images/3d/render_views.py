#!/usr/bin/env python3
"""NASA Kepler .glb から同一縮尺・正投影・白背景の9視点PNGを生成する。

出力:
  views/01_正面.png ... views/09_上斜め45度俯瞰.png (2048x2048)
  kepler_9views_contact_sheet.png (3x3 一覧)
  kepler_9views.zip (全ファイル)
"""
import os
import zipfile

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np
import trimesh
import pyrender
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "kepler_a_decoded.glb")
# NOSHADE=1 でサンシェード(mesh 3)を除いてレンダリング（縮尺は全メッシュ基準のまま維持）
NOSHADE = os.environ.get("NOSHADE") == "1"
HIDE_MESHES = {3} if NOSHADE else set()
SUFFIX = "_noshade" if NOSHADE else ""
OUT = os.path.join(HERE, "views" + SUFFIX)
RES = 2048          # 各視点の解像度
MARGIN = 1.15       # バウンディング球に対する余白
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

# 視点定義: (連番, ラベル, 方位角[deg], 仰角[deg])
# 方位角: 正面を 0 とし、モデルから見て左回りを正
# 仰角: 水平を 0、上を +90
# AZ_OFFSET: 「正面」をモデルのどの向きにするか。
#   +90 = 望遠鏡の開口部(+X)を正面、太陽電池パネルの尾根(-X)を背面にする
AZ_OFFSET = 90
VIEWS = [
    ("01", "正面", 0, 0),
    ("02", "前方左斜め45度", 45, 0),
    ("03", "前方右斜め45度", -45, 0),
    ("04", "左側面", 90, 0),
    ("05", "右側面", -90, 0),
    ("06", "背面", 180, 0),
    ("07", "上面", 0, 90),
    ("08", "下面", 0, -90),
    ("09", "上斜め45度俯瞰", 45, 45),
    ("10", "背面側上斜め45度俯瞰", 180, 45),
    # 上面観から機体を画像の右へ5度だけ傾けた図（カメラを背面側へ5度倒す）
    # up=[0,0,-1] 指定で上面観(07)と同じ画面向き（パネル左・正面右）に揃える
    ("11", "上面から右に5度傾け", 180, 85, [0, 0, -1]),
]


def look_at(eye, target, up):
    """カメラの pose 行列 (OpenGL 慣習: -Z が視線方向)"""
    eye = np.asarray(eye, dtype=float)
    target = np.asarray(target, dtype=float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.asarray(up, dtype=float)
    right = np.cross(fwd, up)
    if np.linalg.norm(right) < 1e-8:  # 真上・真下では up を取り直す
        # 上面観: up=[0,0,-1] → 画像の右が正面(+X)、太陽電池パネル(背面側)が左に来る
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

    # --- モデル読み込み（変換適用済みメッシュ群に展開） ---
    tm = trimesh.load(GLB)
    if isinstance(tm, trimesh.Scene):
        meshes = tm.dump(concatenate=False)
    else:
        meshes = [tm]

    # 全体のバウンディング球（中心と半径）→ 全視点で共通の縮尺に使う
    all_pts = np.vstack([m.bounds for m in meshes])
    lo = all_pts.min(axis=0)
    hi = all_pts.max(axis=0)
    center = (lo + hi) / 2.0
    radius = float(np.linalg.norm(hi - lo) / 2.0)
    mag = radius * MARGIN          # 正投影の半視野（全視点で固定＝同一縮尺）
    dist = radius * 4.0            # カメラ距離（正投影なので縮尺に影響しない）

    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0],
                           ambient_light=[0.35, 0.35, 0.35])
    for i, m in enumerate(meshes):
        if i in HIDE_MESHES:
            continue
        scene.add(pyrender.Mesh.from_trimesh(m, smooth=False))

    cam = pyrender.OrthographicCamera(xmag=mag, ymag=mag, znear=0.01,
                                      zfar=dist + radius * 4.0)
    cam_node = scene.add(cam, pose=np.eye(4))

    # ライト（キーライトはカメラと一緒に動かす／固定の補助光を3方向）
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
        # 方位角0=+Z(正面)、+方位角=+X側(モデルの左)、仰角+=上(+Y)
        direction = np.array([np.sin(a) * np.cos(e),
                              np.sin(e),
                              np.cos(a) * np.cos(e)])
        eye = center + direction * dist
        pose = look_at(eye, center, up_vec)
        scene.set_pose(cam_node, pose)
        scene.set_pose(key_node, pose)
        color, _ = r.render(scene)
        img = Image.fromarray(color)
        path = os.path.join(OUT, f"{num}_{label}.png")
        img.save(path)
        paths.append((path, f"{num} {label}"))
        print(f"rendered: {os.path.basename(path)}")
    r.delete()

    # --- 3x3 一覧画像 ---
    cell = 700
    pad = 20
    label_h = 60
    rows = (len(paths) + 2) // 3
    sheet = Image.new("RGB", (cell * 3 + pad * 4, (cell + label_h) * rows + pad * (rows + 1)),
                      "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 36)
    for i, (path, label) in enumerate(paths):
        row, col = divmod(i, 3)
        x = pad + col * (cell + pad)
        y = pad + row * (cell + label_h + pad)
        thumb = Image.open(path).resize((cell, cell), Image.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw.text((x + cell / 2, y + cell + 8), label, fill="black",
                  font=font, anchor="ma")
    sheet_path = os.path.join(HERE, f"kepler_9views_contact_sheet{SUFFIX}.png")
    sheet.save(sheet_path)
    print(f"contact sheet: {os.path.basename(sheet_path)}")

    # --- ZIP ---
    zip_path = os.path.join(HERE, f"kepler_9views{SUFFIX}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path, _ in paths:
            z.write(path, os.path.join("views", os.path.basename(path)))
        z.write(sheet_path, os.path.basename(sheet_path))
    print(f"zip: {os.path.basename(zip_path)}")


if __name__ == "__main__":
    main()
