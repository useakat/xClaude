#!/usr/bin/env python3
"""オポチュニティの構造図（note セクション画像①）を、NASA 公式高精細3Dモデルから作る。

姿勢ビューア（opportunity_viewer.html）と同じ回転式で任意角度をレンダリングし、
各部位のアンカーを同じカメラで射影して、日本語ラベルを引き出し線で添える。
機体は白背景から切り抜いて火星の情景に合成し、足元に影を落とす。

  ビューアの式:  R = Rz(pitch)·Rx(-yaw)·Ry(-roll),  screen = VIEW · R · p
  VIEW = [[S, S, 0], [0, 0, -1], [-S, S, 0]]   (S = 1/√2)
  → カメラ基底は T = VIEW·R の各行（0:右, 1:上, 2:視点方向）

使い方:
  python3 make_structure_fig.py 7 80 80            # roll yaw pitch（ビューアの値）
  python3 make_structure_fig.py 7 80 80 --tag a    # 出力ファイル名の接尾辞
出力:
  ../../draft/images/砂の星に降りた_太陽で生きる機械_図解_<tag>.png (1280x720)
"""
import argparse
import os

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np
import trimesh
import pyrender
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import binary_dilation, label as cc_label

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "mer_static_highpoly.glb")
OUT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "draft", "images"))
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
RES = 2048
MARGIN = 1.12
CW, CH = 1280, 720
# Y-up モデル用の基準視点（方位35°・仰角18°・up=+Y）。行 = 右/上/視点方向
VIEW = np.array([[0.819152, 0.0, -0.573576],
                 [-0.177245, 0.951057, -0.253132],
                 [0.545504, 0.309017, 0.779060]])

LABELS = [
    ("panel", "太陽電池パネル", "命綱。ここに砂が積もる"),
    ("body",  "バッテリーとヒーター（内部）", "夜の寒さをしのぐ"),
    ("arm",   "ロボットアーム", "岩を調べる腕"),
    ("wheel", "車輪（6輪）", ""),
]
MAT_OF = {
    "panel": ("tex_panels_n", "tex_panels2_n"),
    "body":  ("tex_body_n",),
    "arm":   ("tex_arm",),
    "wheel": ("tex_suspension_n",),
}


def rx(d):
    a = np.radians(d); c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(d):
    a = np.radians(d); c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(d):
    a = np.radians(d); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def cutout(img):
    """白背景を外周から塗りつぶして透過にする（機体内部の白は残す）。"""
    rgb = np.asarray(img.convert("RGB"))
    a = rgb.astype(np.int16)
    near_white = (a[..., 0] > 244) & (a[..., 1] > 244) & (a[..., 2] > 244)
    lab, _ = cc_label(near_white)
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    border.discard(0)
    bg = binary_dilation(np.isin(lab, list(border)), iterations=1)
    return Image.fromarray(np.dstack([rgb, np.where(bg, 0, 255).astype(np.uint8)]), "RGBA")


def mars_background(w, h, horizon):
    """火星の情景を手続き的に描く（空・遠景の丘・地面・岩・かすみ・周辺減光）。"""
    rng = np.random.default_rng(11)
    img = np.zeros((h, w, 3), np.float32)

    # --- 空: 上ほど暗い赤褐色、地平線近くは砂色にかすむ ---
    sky_top, sky_horizon = np.array([104, 70, 52]), np.array([214, 172, 132])
    for y in range(horizon):
        t = (y / max(horizon - 1, 1)) ** 1.35
        img[y, :] = sky_top * (1 - t) + sky_horizon * t

    # --- 地面: 手前ほど暗く、粗い ---
    g_far, g_near = np.array([176, 116, 76]), np.array([88, 49, 31])
    for y in range(horizon, h):
        t = ((y - horizon) / max(h - horizon - 1, 1)) ** 0.85
        img[y, :] = g_far * (1 - t) + g_near * t

    # --- 遠景の丘（地平線上に低い起伏）---
    xs = np.arange(w)
    for amp, freq, phase, dy, col in [
        (16, 0.9, 0.4, -6, np.array([150, 98, 68])),
        (10, 2.1, 2.0, -2, np.array([164, 108, 74])),
    ]:
        ridge = (horizon + dy
                 - amp * (np.sin(xs / w * np.pi * 2 * freq + phase) * 0.6
                          + np.sin(xs / w * np.pi * 2 * freq * 2.7 + phase * 1.7) * 0.4))
        for x in range(w):
            y0 = int(max(0, ridge[x]))
            img[y0:horizon, x] = col

    # --- 砂のむら（低周波のまだら）---
    small = rng.normal(0, 1, (h // 24 + 2, w // 24 + 2)).astype(np.float32)
    blotch = np.asarray(Image.fromarray(small).resize((w, h), Image.BICUBIC))
    ground = np.zeros((h, w), np.float32)
    ground[horizon:, :] = 1.0
    img += (blotch * 11.0 * ground)[..., None]

    # --- 岩（地面に散らす。遠いほど小さく淡い）---
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    dr = ImageDraw.Draw(pil, "RGBA")
    for _ in range(160):
        t = rng.random() ** 1.6                       # 手前に多く
        y = int(horizon + 6 + t * (h - horizon - 10))
        x = int(rng.random() * w)
        r = max(1.0, (1.5 + t * 9.0) * (0.6 + rng.random()))
        shade = int(60 + rng.random() * 40)
        dr.ellipse([x - r, y - r * 0.62, x + r, y + r * 0.62],
                   fill=(shade, int(shade * 0.62), int(shade * 0.45), 190))
        dr.ellipse([x - r * 0.9, y - r * 0.72, x + r * 0.5, y - r * 0.05],
                   fill=(int(shade * 1.9), int(shade * 1.25), int(shade * 0.9), 120))

    # --- 地平線のかすみ ---
    haze = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(haze)
    band = int(h * 0.10)
    for i in range(band):
        a = int(120 * (1 - i / band))
        hd.line([(0, horizon - band + i), (w, horizon - band + i)], fill=(226, 186, 148, a))
        hd.line([(0, horizon + i), (w, horizon + i)], fill=(214, 170, 132, int(a * 0.7)))
    pil = Image.alpha_composite(pil, haze.filter(ImageFilter.GaussianBlur(6)))

    # --- 周辺減光 ---
    yy, xx = np.mgrid[0:h, 0:w]
    d2 = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    vig = np.clip(1.0 - 0.22 * d2, 0, 1)[..., None]
    arr = np.asarray(pil.convert("RGB")).astype(np.float32) * vig
    arr += rng.normal(0, 2.2, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def render(meshes, center, mag, right, up, toward, dist):
    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0],
                           ambient_light=[0.36, 0.36, 0.36])
    for m in meshes:
        scene.add(pyrender.Mesh.from_trimesh(m, smooth=False))
    pose = np.eye(4)
    pose[:3, 0], pose[:3, 1], pose[:3, 2] = right, up, toward
    pose[:3, 3] = center + toward * dist
    cam = pyrender.OrthographicCamera(xmag=mag, ymag=mag, znear=0.01, zfar=dist * 3)
    scene.add(cam, pose=pose)
    scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=3.0), pose=pose)
    for d in ([1, 1, 1], [-1, 0.5, -1], [0, -1, 0.5]):
        d = np.asarray(d, float); d = d / np.linalg.norm(d)
        p = np.eye(4)
        f = -d
        r_ = np.cross(f, [0, 1, 0])
        if np.linalg.norm(r_) < 1e-6:
            r_ = np.cross(f, [0, 0, -1])
        r_ /= np.linalg.norm(r_)
        u_ = np.cross(r_, f)
        p[:3, 0], p[:3, 1], p[:3, 2], p[:3, 3] = r_, u_, -f, center + d * dist
        scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=1.15), pose=p)
    r = pyrender.OffscreenRenderer(RES, RES)
    color, _ = r.render(scene)
    r.delete()
    return Image.fromarray(color)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roll", type=float)
    ap.add_argument("yaw", type=float)
    ap.add_argument("pitch", type=float)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--bg", choices=["mars", "white"], default="mars")
    args = ap.parse_args()
    tag = args.tag or f"r{int(args.roll)}y{int(args.yaw)}p{int(args.pitch)}"
    os.makedirs(OUT_DIR, exist_ok=True)

    tm = trimesh.load(GLB)
    meshes, geoms = [], {}
    for _, m in tm.geometry.items():
        meshes.append(m)
        mat = getattr(getattr(m.visual, "material", None), "name", None)
        geoms.setdefault(mat, []).append(np.asarray(m.vertices, dtype=float))

    all_v = np.vstack([v for vs in geoms.values() for v in vs])
    lo, hi = all_v.min(0), all_v.max(0)
    center = (lo + hi) / 2.0
    radius = float(np.linalg.norm(hi - lo) / 2.0)
    mag, dist = radius * MARGIN, radius * 4.0

    # ビューアと同じ回転規約
    #   ヨー = 機体の垂直軸まわり / ピッチ = 前後に倒す / ロール = 画面内
    #   screen = Rz(roll)·Rx(pitch) · VIEW · Ry(yaw) · p
    T = rz(args.roll) @ rx(args.pitch) @ VIEW @ ry(args.yaw)
    right, up, toward = T[0], T[1], T[2]

    def project(p):
        d = np.asarray(p, float) - center
        return np.array([np.dot(d, right) / mag * (RES / 2) + RES / 2,
                         RES / 2 - np.dot(d, up) / mag * (RES / 2)])

    body_v = np.vstack(geoms["tex_body_n"])
    body_c = body_v.mean(axis=0)
    body_c[1] = body_v[:, 1].min() + (body_v[:, 1].max() - body_v[:, 1].min()) * 0.30

    def blob_center(pts, pick):
        """頂点群を画像座標へ落として塊に分け、pick 側の塊の中心を返す。
        pick: 'left' = 画面左の塊 / 'right' = 画面右の塊"""
        pr = np.array([project(p) for p in pts])
        G = 512
        gx = np.clip((pr[:, 0] / RES * G).astype(int), 0, G - 1)
        gy = np.clip((pr[:, 1] / RES * G).astype(int), 0, G - 1)
        mask = np.zeros((G, G), bool)
        mask[gy, gx] = True
        mask = binary_dilation(mask, iterations=2)
        lab, n = cc_label(mask)
        if n == 0:
            return pr.mean(axis=0)
        ids = lab[gy, gx]
        best, best_key = None, None
        for i in range(1, n + 1):
            sel = ids == i
            if sel.sum() < 20:
                continue
            cx = pr[sel, 0].mean()
            key = -cx if pick == "left" else cx
            if best_key is None or key > best_key:
                best_key, best = key, pr[sel].mean(axis=0)
        return best if best is not None else pr.mean(axis=0)

    anchors_px = {}
    # 太陽電池パネル: 画面左の翼の中央
    anchors_px["panel"] = blob_center(
        np.vstack([v for mm in MAT_OF["panel"] for v in geoms[mm]]), "left")
    # 車輪: 足回りの下側だけを取り出し、画面右の車輪の中央
    susp = np.vstack([v for mm in MAT_OF["wheel"] for v in geoms[mm]])
    ylo, yhi = susp[:, 1].min(), susp[:, 1].max()
    wheels = susp[susp[:, 1] < ylo + (yhi - ylo) * 0.42]
    anchors_px["wheel"] = blob_center(wheels, "right")
    # ロボットアーム: 前方（+Z）へ最も突き出した先端
    arm = np.vstack([v for mm in MAT_OF["arm"] for v in geoms[mm]])
    anchors_px["arm"] = project(arm[np.argmax(arm[:, 2])])

    raw = render(meshes, center, mag, right, up, toward, dist)
    rover = cutout(raw)

    # 本体（金色の断熱材）が実際に見えている画素をアンカーにする
    body_px = np.array([project(p) for p in body_v])
    x0, y0 = np.clip(body_px.min(0) - 12, 0, RES - 1).astype(int)
    x1, y1 = np.clip(body_px.max(0) + 12, 0, RES - 1).astype(int)
    arr = np.asarray(raw.convert("RGB")).astype(np.int16)
    R_, G_, B_ = arr[..., 0], arr[..., 1], arr[..., 2]
    gold = (R_ > 105) & (R_ - B_ > 45) & (G_ > 75) & (G_ < R_)
    win = np.zeros_like(gold); win[y0:y1, x0:x1] = True
    ys, xs = np.nonzero(gold & win)
    if len(xs):
        c_px = project(body_c)
        k = np.argmin((xs - c_px[0]) ** 2 + (ys - c_px[1]) ** 2)
        anchors_px["body"] = np.array([xs[k], ys[k]], dtype=float)
    else:
        anchors_px["body"] = project(body_c)
    bbox = rover.getbbox()
    rov = rover.crop(bbox)
    sc = int(CH * 0.60) / rov.height
    if rov.width * sc > CW * 0.60:
        sc = CW * 0.60 / rov.width
    rov = rov.resize((int(rov.width * sc), int(rov.height * sc)), Image.LANCZOS)
    ox = int(CW * 0.53 - rov.width / 2)
    oy = int(CH * 0.58 - rov.height / 2)

    horizon = min(CH - 40, oy + rov.height - int(rov.height * 0.06))
    white = args.bg == "white"
    if white:
        canvas = Image.new("RGB", (CW, CH), (250, 249, 247))
        PAL = dict(title=(28, 33, 42), sub=(140, 88, 8), name=(26, 30, 38),
                   note=(92, 74, 52), line=(186, 128, 24), dot=(186, 128, 24),
                   halo=(255, 255, 255, 245), band=(238, 234, 228, 235),
                   band_text=(34, 38, 46), credit=(150, 150, 150),
                   shadow=(120, 118, 114, 90))
    else:
        canvas = mars_background(CW, CH, horizon)
        PAL = dict(title=(228, 240, 252), sub=(255, 205, 90), name=(250, 246, 240),
                   note=(255, 205, 90), line=(255, 205, 90), dot=(255, 205, 90),
                   halo=(24, 13, 8, 225), band=(30, 17, 12, 195),
                   band_text=(250, 246, 240), credit=(232, 208, 184),
                   shadow=(38, 20, 12, 150))

    # --- 足元の影 ---
    shadow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sw, sh = int(rov.width * 0.92), int(rov.height * 0.16)
    scx, scy = ox + rov.width / 2, oy + rov.height - sh * 0.35
    sd.ellipse([scx - sw / 2, scy - sh / 2, scx + sw / 2, scy + sh / 2],
               fill=PAL["shadow"])
    canvas = Image.alpha_composite(canvas.convert("RGBA"),
                                   shadow.filter(ImageFilter.GaussianBlur(18)))
    canvas.paste(rov, (ox, oy), rov)
    d = ImageDraw.Draw(canvas, "RGBA")

    # 最小文字サイズ = 画像幅の 2.19%（1280px 幅なら 28px）。image/brand.md 準拠。
    # クレジット（但し書き）だけ下限の対象外。
    MIN_FONT = round(CW * 0.0219)

    def F(size):
        return ImageFont.truetype(FONT, max(size, MIN_FONT), index=0)

    f_title = F(72)
    f_sub = F(38)
    f_name = F(35)
    f_note = F(28)
    f_cr = ImageFont.truetype(FONT, 12, index=0)

    def px_to_canvas(px, py):
        return (ox + (px - bbox[0]) * sc, oy + (py - bbox[1]) * sc)

    def to_canvas(p3):
        px, py = project(p3)
        return px_to_canvas(px, py)

    placed = [(k, t, s_, px_to_canvas(*anchors_px[k])) for k, t, s_ in LABELS]
    left = sorted([p for p in placed if p[3][0] < CW * 0.53], key=lambda p: p[3][1])
    right_ = sorted([p for p in placed if p[3][0] >= CW * 0.53], key=lambda p: p[3][1])

    def draw_side(items, side):
        if not items:
            return
        slots = np.linspace(CH * 0.40, CH * 0.80, max(len(items), 1))
        for (k, title, note, (ax, ay)), sy in zip(items, slots):
            tw = d.textlength(title, font=f_name)
            tx = 40 if side == "L" else CW - 40 - tw
            lx = tx + tw + 12 if side == "L" else tx - 12
            if k != "body":       # 内部の部品は指し示さない（引き出し線なし）
                d.line([(lx, sy + 18), (ax, ay)], fill=PAL["line"], width=3)
                d.ellipse([ax - 7, ay - 7, ax + 7, ay + 7], fill=PAL["dot"],
                          outline=(255, 255, 255) if white else (40, 22, 15), width=2)
            for dx in (-2, 2):
                for dy in (-2, 2):
                    d.text((tx + dx, sy + dy), title, font=f_name, fill=PAL["halo"])
            d.text((tx, sy), title, font=f_name, fill=PAL["name"])
            if note:
                nw = d.textlength(note, font=f_note)
                nx = tx if side == "L" else CW - 40 - nw
                for dx in (-2, 2):
                    for dy in (-2, 2):
                        d.text((nx + dx, sy + 50 + dy), note, font=f_note, fill=PAL["halo"])
                d.text((nx, sy + 50), note, font=f_note, fill=PAL["note"])

    draw_side(left, "L")
    draw_side(right_, "R")

    title = "太陽で生きる探査車、オポチュニティ"
    sub = "ゴルフカートほどの大きさ／重さ185kg"
    size = 72
    while size > max(40, MIN_FONT):        # 1行で収まる最大サイズにする（下限は守る）
        f_title = ImageFont.truetype(FONT, size, index=0)
        if d.textlength(title, font=f_title) <= CW - 80:
            break
        size -= 2
    for dx in (-3, 3):
        for dy in (-3, 3):
            d.text((40 + dx, 34 + dy), title, font=f_title, fill=PAL["halo"])
    d.text((40, 34), title, font=f_title, fill=PAL["title"])
    ty = 34 + size + 26
    for dx in (-2, 2):
        for dy in (-2, 2):
            d.text((42 + dx, ty + dy), sub, font=f_sub, fill=PAL["halo"])
    d.text((42, ty), sub, font=f_sub, fill=PAL["sub"])

    f_flow = ImageFont.truetype(FONT, 25, index=0)
    flow = "昼：パネルで発電  →  夜：バッテリーでヒーター"
    fw = d.textlength(flow, font=f_flow)
    d.rectangle([CW / 2 - fw / 2 - 20, CH - 78, CW / 2 + fw / 2 + 20, CH - 26],
                fill=PAL["band"])
    d.text((CW / 2 - fw / 2, CH - 68), flow, font=f_flow, fill=PAL["band_text"])
    d.text((40, CH - 24), "3D model: NASA/JPL-Caltech", font=f_cr, fill=PAL["credit"])

    bw = 4
    d.rectangle([bw // 2, bw // 2, CW - 1 - bw // 2, CH - 1 - bw // 2],
                outline=(96, 92, 86) if white else (150, 104, 62), width=bw)

    out = os.path.join(OUT_DIR, f"砂の星に降りた_太陽で生きる機械_図解_{tag}.png")
    canvas.convert("RGB").save(out)
    print("saved:", os.path.basename(out))


if __name__ == "__main__":
    main()
