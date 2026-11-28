# -*- coding: utf-8 -*-
"""Utilidades de dibujo procedural (PIL + numpy) para las recreaciones visuales."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FONT_DIR = os.path.join(os.environ.get("WORK", "."), "fonts")
_fonts = {}


def font(name, size):
    k = (name, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    return _fonts[k]


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def mix(c1, c2, u):
    return tuple(int(lerp(a, b, u)) for a, b in zip(c1, c2))


def jitter(c, rng, amt=14):
    return tuple(int(max(0, min(255, v + rng.integers(-amt, amt + 1)))) for v in c)


def vgrad_arr(w, h, stops):
    pos = [s[0] for s in stops]
    cols = np.array([s[1] for s in stops], np.float32)
    y = np.linspace(0, 1, h)
    c = np.stack([np.interp(y, pos, cols[:, i]) for i in range(3)], 1)
    return np.repeat(c[:, None, :], w, 1)


def vgrad(w, h, stops, mode="RGB"):
    a = vgrad_arr(w, h, stops).astype(np.uint8)
    im = Image.fromarray(a, "RGB")
    return im.convert("RGBA") if mode == "RGBA" else im


# ---------------------------------------------------------------- luces aditivas
_spr = {}


def _sprite(r, hard=2.0):
    k = (int(r), hard)
    if k not in _spr:
        r = max(1, int(r))
        y, x = np.mgrid[-r:r, -r:r].astype(np.float32) + 0.5
        d = np.sqrt(x * x + y * y) / r
        _spr[k] = np.clip(1 - d, 0, 1) ** hard
    return _spr[k]


class Lights:
    """Acumula luces y las suma (modo aditivo) sobre el fotograma."""

    def __init__(self):
        self.items = []

    def add(self, x, y, r, col, a=1.0, hard=2.0):
        if r >= 1 and a > 0.01:
            self.items.append((x, y, r, col, a, hard))

    def apply(self, img):
        if not self.items:
            return img
        arr = np.asarray(img.convert("RGB"), dtype=np.float32).copy()
        hh, ww = arr.shape[:2]
        for x, y, r, col, a, hard in self.items:
            s = _sprite(r, hard)
            n = s.shape[0]
            x0, y0 = int(x - n / 2), int(y - n / 2)
            sx0, sy0 = max(0, -x0), max(0, -y0)
            dx0, dy0 = max(0, x0), max(0, y0)
            dx1, dy1 = min(ww, x0 + n), min(hh, y0 + n)
            if dx1 <= dx0 or dy1 <= dy0:
                continue
            sub = s[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0)]
            arr[dy0:dy1, dx0:dx1] += sub[..., None] * (np.array(col, np.float32) * a)
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def paste(dst, src, x, y):
    """alpha_composite con recorte (admite coordenadas negativas)."""
    x, y = int(x), int(y)
    sw, sh = src.size
    l, t = max(0, -x), max(0, -y)
    r, b = min(sw, dst.size[0] - x), min(sh, dst.size[1] - y)
    if r <= l or b <= t:
        return
    dst.alpha_composite(src.crop((l, t, r, b)) if (l, t, r, b) != (0, 0, sw, sh) else src, (x + l, y + t))


def layer_crop(layer, off, y=0):
    """Recorta una capa ancha en bucle horizontal (parallax infinito)."""
    lw = layer.size[0]
    off = int(off) % lw
    if off + W <= lw:
        return layer.crop((off, 0, off + W, layer.size[1]))
    a = layer.crop((off, 0, lw, layer.size[1]))
    b = layer.crop((0, 0, W - (lw - off), layer.size[1]))
    out = Image.new("RGBA", (W, layer.size[1]))
    out.paste(a, (0, 0)); out.paste(b, (lw - off, 0))
    return out


def glowify(img, radius=5, strength=1.6):
    g = img.filter(ImageFilter.GaussianBlur(radius))
    a = np.asarray(g, np.float32)
    a[..., 3] = np.clip(a[..., 3] * strength, 0, 255)
    g = Image.fromarray(a.astype(np.uint8), "RGBA")
    g.alpha_composite(img)
    return g


def value_noise(w, h, rng, octaves=5, base=4):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * (2 ** o)
        g = rng.random((max(2, int(n * h / w)) + 1, n + 1)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp
        tot += amp; amp *= 0.5
    return out / tot


# ---------------------------------------------------------------- elementos
def draw_palm(d, x, y, h, lean, sway, col, leaflets=True):
    n = 12
    w = max(2.0, h * 0.045)
    pts = [(x + lean * h * (i / n) ** 2 + sway * h * 0.015 * (i / n) ** 2, y - h * i / n) for i in range(n + 1)]
    for i in range(n):
        d.line([pts[i], pts[i + 1]], fill=col, width=int(max(1, w * (1 - 0.45 * i / n))))
    tx, ty = pts[-1]
    nf = 9
    for k in range(nf):
        ang = -math.pi / 2 + (k - (nf - 1) / 2) * (math.pi * 1.3 / (nf - 1))
        ang += sway * 0.1 * math.sin(k * 1.7 + 0.5) + sway * 0.05
        L = h * (0.40 + 0.07 * math.sin(k * 2.3))
        seg, prev = 9, (tx, ty)
        for j in range(1, seg + 1):
            s = j / seg
            fx = tx + math.cos(ang) * L * s + sway * L * 0.06 * s * s
            fy = ty + math.sin(ang) * L * s + L * 0.55 * s * s
            d.line([prev, (fx, fy)], fill=col, width=int(max(1, h * 0.03 * (1 - s) + 1)))
            if leaflets and h > 60 and j > 1:
                ll = h * 0.07 * (1 - s * 0.6)
                d.line([(fx, fy), (fx + math.cos(ang + 1.2) * ll, fy + ll * 0.9)], fill=col, width=max(1, int(h * 0.008)))
                d.line([(fx, fy), (fx + math.cos(ang - 1.2) * ll, fy + ll * 0.9)], fill=col, width=max(1, int(h * 0.008)))
            prev = (fx, fy)


def draw_person(d, x, yf, h, shirt, pants, skin, phase=0.0, walk=1.0, long_hair=False,
                hair=(30, 22, 18), arms_up=0.0, umbrella=None, facing=1):
    sw = walk * math.sin(phase) * h * 0.13
    hip = yf - h * 0.48
    sh = yf - h * 0.80
    lw = max(1, int(h * 0.075))
    d.line([(x, hip), (x + sw, yf)], fill=pants, width=lw)
    d.line([(x, hip), (x - sw, yf)], fill=pants, width=lw)
    tw = h * 0.12
    d.polygon([(x - tw, sh), (x + tw, sh), (x + tw * 0.8, hip), (x - tw * 0.8, hip)], fill=shirt)
    aw = max(1, int(h * 0.055))
    if umbrella is not None:
        d.line([(x, sh + h * 0.05), (x + facing * h * 0.12, sh - h * 0.05)], fill=shirt, width=aw)
        ux, uy = x + facing * h * 0.12, sh - h * 0.05
        d.line([(ux, uy), (ux, uy - h * 0.35)], fill=(20, 20, 20), width=max(1, int(h * 0.02)))
        r = h * 0.38
        d.pieslice([ux - r, uy - h * 0.35 - r * 0.55, ux + r, uy - h * 0.35 + r * 0.55], 180, 360, fill=umbrella)
    elif arms_up > 0:
        for s in (-1, 1):
            d.line([(x + s * tw * 0.8, sh + 2), (x + s * h * 0.2, sh - h * 0.28 * arms_up)], fill=skin, width=aw)
    else:
        d.line([(x - tw * 0.9, sh + 2), (x - tw - sw * 0.6, hip + h * 0.05)], fill=skin, width=aw)
        d.line([(x + tw * 0.9, sh + 2), (x + tw + sw * 0.6, hip + h * 0.05)], fill=skin, width=aw)
    hr = h * 0.085
    hy = sh - hr * 1.15
    if long_hair:
        d.polygon([(x - hr * 1.05, hy), (x + hr * 1.05, hy), (x + hr * 1.2 - facing * hr * 0.6, sh + h * 0.12),
                   (x - hr * 1.2 - facing * hr * 0.6, sh + h * 0.12)], fill=hair)
    d.ellipse([x - hr, hy - hr, x + hr, hy + hr], fill=skin)
    d.chord([x - hr * 1.05, hy - hr * 1.1, x + hr * 1.05, hy + hr * 0.6], 180, 360, fill=hair)


SKINS = [(241, 194, 155), (224, 172, 125), (198, 134, 90), (160, 102, 64), (110, 70, 45), (80, 52, 36)]
CLOTHES = [(230, 60, 90), (40, 170, 200), (250, 210, 60), (250, 250, 250), (40, 40, 50), (120, 200, 90),
           (250, 130, 50), (150, 80, 200), (30, 90, 180), (230, 120, 170), (200, 40, 40), (70, 200, 170)]
HAIRS = [(25, 20, 15), (60, 40, 25), (120, 80, 40), (200, 170, 100), (15, 15, 15), (90, 50, 30)]


def random_person(rng):
    return dict(shirt=CLOTHES[rng.integers(len(CLOTHES))], pants=CLOTHES[rng.integers(len(CLOTHES))],
                skin=SKINS[rng.integers(len(SKINS))], hair=HAIRS[rng.integers(len(HAIRS))],
                long_hair=bool(rng.random() < 0.45))


def city_layer(w, hh, base, rng, hmin, hmax, body, wins, win_p=0.35, neon_p=0.15, deco_p=0.3,
               bw=(40, 130), pastel=False):
    img = Image.new("RGBA", (w, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    neons = [(255, 60, 170), (60, 230, 255), (255, 140, 40), (170, 80, 255)]
    x = -20
    while x < w + 20:
        bwid = int(rng.integers(*bw))
        bh = int(rng.integers(hmin, hmax))
        top = base - bh
        col = jitter(body, rng, 10) if not pastel else PASTELS[rng.integers(len(PASTELS))]
        d.rectangle([x, top, x + bwid, base], fill=col + (255,))
        if rng.random() < deco_p:
            tiers = int(rng.integers(1, 4))
            tw, tt = bwid, top
            for _ in range(tiers):
                tw = int(tw * 0.7); th = int(rng.integers(8, 26))
                cx = x + bwid // 2
                d.rectangle([cx - tw // 2, tt - th, cx + tw // 2, tt], fill=col + (255,)); tt -= th
            if rng.random() < 0.6:
                d.line([(x + bwid // 2, tt), (x + bwid // 2, tt - rng.integers(10, 40))], fill=col + (255,), width=2)
        gw = int(rng.integers(3, 6)); gh = gw + int(rng.integers(0, 4)); gap = int(rng.integers(3, 7))
        wp = win_p * rng.uniform(0.5, 1.4)
        for yy in range(top + 7, base - 6, gh + gap):
            for xx in range(x + 5, x + bwid - 5, gw + gap):
                if rng.random() < wp:
                    d.rectangle([xx, yy, xx + gw, yy + gh], fill=wins[rng.integers(len(wins))] + (255,))
        if rng.random() < neon_p:
            nc = neons[rng.integers(len(neons))] + (255,)
            if rng.random() < 0.5:
                d.line([(x + 2, top), (x + 2, base)], fill=nc, width=3)
                d.line([(x + bwid - 2, top), (x + bwid - 2, base)], fill=nc, width=3)
            else:
                for k in range(int(rng.integers(1, 4))):
                    yy = top + 10 + k * 14
                    d.line([(x, yy), (x + bwid, yy)], fill=nc, width=3)
        x += bwid + int(rng.integers(-12, 8))
    return img


PASTELS = [(250, 200, 210), (190, 230, 225), (250, 230, 180), (210, 200, 240), (255, 220, 200), (200, 225, 250),
           (245, 245, 240)]

SKIES = {
    "sunset": [(0, (36, 18, 74)), (0.42, (196, 64, 120)), (0.72, (255, 140, 80)), (1, (255, 205, 120))],
    "night": [(0, (4, 4, 22)), (0.55, (30, 16, 62)), (1, (110, 36, 104))],
    "day": [(0, (30, 110, 205)), (0.65, (110, 185, 240)), (1, (205, 232, 250))],
    "dusk": [(0, (16, 10, 48)), (0.5, (100, 40, 140)), (0.85, (240, 110, 120)), (1, (255, 170, 120))],
    "dawn": [(0, (40, 60, 120)), (0.55, (200, 140, 170)), (1, (255, 210, 160))],
}


def draw_sun(img, cx, cy, r, top=(255, 230, 120), bot=(255, 60, 140), stripes=True, t=0.0):
    sun = vgrad(int(2 * r), int(2 * r), [(0, top), (1, bot)], "RGBA")
    m = Image.new("L", sun.size, 0)
    md = ImageDraw.Draw(m)
    md.ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    if stripes:
        for k in range(6):
            yy = int(r * 1.05 + k * r * 0.16 + (t * 8) % (r * 0.16))
            md.rectangle([0, yy, 2 * r, yy + max(1, int(r * 0.03 + k * 1.5))], fill=0)
    sun.putalpha(m)
    paste(img, sun, cx - r, cy - r)


def flip_reflect(frame, hy, darken=0.55, t=0.0, amp=6.0, tint=(0, 0, 0)):
    """Refleja la parte superior del fotograma en el agua bajo hy con ondulación."""
    arr = np.asarray(frame.convert("RGB"), np.float32)
    wh = H - hy
    src = arr[max(0, hy - wh):hy][::-1]
    if src.shape[0] < wh:
        src = np.concatenate([src, np.repeat(src[-1:], wh - src.shape[0], 0)], 0)
    ys = np.arange(wh)
    off = (np.sin(ys * 0.35 + t * 5.0) * amp * (0.3 + ys / wh) + np.sin(ys * 0.11 - t * 2.1) * amp * 0.6).astype(int)
    xs = (np.arange(W)[None, :] + off[:, None]) % W
    ref = src[ys[:, None], xs]
    fade = np.linspace(darken, darken * 0.55, wh)[:, None, None]
    ref = ref * fade + np.array(tint, np.float32) * (1 - fade) * 0.5
    out = arr.copy()
    out[hy:] = ref
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def draw_car_side(d, x, y, L, body, glass=(20, 25, 40), wheel_ang=0.0, style=0):
    """Coche deportivo genérico de perfil (diseño original). x,y = punto trasero inferior."""
    hgt = L * 0.26
    if style == 0:
        pts = [(0, 0.55), (0.02, 0.25), (0.12, 0.18), (0.30, 0.15), (0.42, -0.05), (0.62, -0.08), (0.74, 0.12),
               (0.95, 0.22), (1.0, 0.42), (0.98, 0.62), (0, 0.62)]
    else:
        pts = [(0, 0.6), (0.01, 0.2), (0.18, 0.12), (0.30, -0.12), (0.66, -0.14), (0.78, 0.10), (0.97, 0.16),
               (1.0, 0.45), (0.98, 0.64), (0, 0.64)]
    poly = [(x + px * L, y - hgt + py * hgt) for px, py in pts]
    d.polygon(poly, fill=body)
    gl = [(0.34, 0.14), (0.44, -0.0), (0.60, -0.02), (0.70, 0.13)] if style == 0 else \
        [(0.31, 0.10), (0.34, -0.06), (0.64, -0.07), (0.74, 0.10)]
    d.polygon([(x + px * L, y - hgt + py * hgt) for px, py in gl], fill=glass)
    r = L * 0.085
    for wx in (0.2, 0.8):
        cx, cy = x + wx * L, y - hgt * 0.02
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(12, 12, 14))
        d.ellipse([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62], fill=(150, 150, 160))
        for k in range(5):
            a = wheel_ang + k * 2 * math.pi / 5
            d.line([(cx, cy), (cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6)], fill=(60, 60, 70),
                   width=max(1, int(r * 0.16)))
    return poly
