# -*- coding: utf-8 -*-
"""Animaciones científicas procedurales (recreaciones artísticas propias) a 1920x1080."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FONTS = os.path.join(os.environ.get("WORK", "."), "fonts")
_f = {}


def font(sz, name="Poppins-Bold.ttf"):
    if (sz, name) not in _f:
        _f[(sz, name)] = ImageFont.truetype(os.path.join(FONTS, name), sz)
    return _f[(sz, name)]


def ease(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


def noise2(h, w, rng, oct_=5, base=4):
    out = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(oct_):
        n = base * 2 ** o
        g = rng.random((max(2, int(n * h / w)) + 1, n + 1)).astype(np.float32)
        out += np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 * amp
        tot += amp; amp *= 0.5
    return out / tot


def tileable_noise(h, w, rng, oct_=5):
    """Ruido periódico en horizontal (para texturas que giran)."""
    n = noise2(h, w * 2, rng, oct_)
    a = n[:, :w]; b = n[:, w:]
    t = np.linspace(0, 1, w)[None, :]
    return a * (1 - t) + b[:, ::-1] * 0  + a * 0 + (a * (1 - t) + n[:, w:2 * w] * t) * 0 + _wrap(n, w)


def _wrap(n, w):
    a = n[:, :w]
    t = (0.5 - 0.5 * np.cos(np.linspace(0, 2 * np.pi, w)))[None, :]
    return a * (1 - t) + np.roll(a, w // 2, 1) * t - a * 0  # aproximadamente periódico


def starfield(rng, w=W, h=H, n=2500, nebula=True, tint=(60, 40, 120)):
    img = np.zeros((h, w, 3), np.float32)
    if nebula:
        nb = noise2(h // 4, w // 4, rng, 5, 3) ** 2.2
        nb = np.asarray(Image.fromarray((np.clip(nb, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        nb2 = noise2(h // 4, w // 4, rng, 4, 2) ** 2
        nb2 = np.asarray(Image.fromarray((np.clip(nb2, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        img += nb[..., None] * np.array(tint, np.float32) * 0.9 + nb2[..., None] * np.array([20, 60, 110], np.float32) * 0.6
    xs = rng.integers(0, w, n); ys = rng.integers(0, h, n)
    b = rng.random(n) ** 6 * 255 + 30
    col = np.stack([b, b * rng.uniform(0.85, 1, n), b * rng.uniform(0.85, 1.1, n)], 1)
    np.add.at(img, (ys, xs), col)
    big = rng.random(n) > 0.985
    for x, y in zip(xs[big], ys[big]):
        for dx, dy, a in ((1, 0, .5), (-1, 0, .5), (0, 1, .5), (0, -1, .5)):
            if 0 <= x + dx < w and 0 <= y + dy < h:
                img[y + dy, x + dx] += 120 * a
    return np.clip(img, 0, 255)


def cam_crop(arr, z, cx=0.5, cy=0.5):
    """Zoom de cámara sobre un array HxWx3 (float o uint8)."""
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if z <= 1.001:
        return im
    cw, ch = W / z, H / z
    l = min(max(0, cx * W - cw / 2), W - cw); t = min(max(0, cy * H - ch / 2), H - ch)
    return im.resize((W, H), Image.BILINEAR, box=(l, t, l + cw, t + ch))


def label(img, txt, x, y, sz=40, col=(255, 255, 255), anchor="la", alpha=255):
    d = ImageDraw.Draw(img, "RGBA")
    d.text((x, y), txt, font=font(sz), fill=col + (alpha,), anchor=anchor, stroke_width=3, stroke_fill=(0, 0, 0, alpha))


class CGI:
    def __init__(self, rng, dur, v=0):
        self.rng, self.dur, self.v = rng, dur, v
        self.setup()

    def setup(self):
        pass


# ------------------------------------------------------------ agujero negro con lente gravitacional
class BlackHole(CGI):
    def setup(self):
        r = self.rng
        self.inc = math.radians(78 if self.v == 0 else 62)
        sc = 1.0 if self.v == 0 else 0.8
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        x = (x - W / 2) / (H * 0.5 * sc); y = (y - H / 2) / (H * 0.5 * sc)
        th2 = x * x + y * y + 1e-6
        thE = 0.20
        f = 1 - thE ** 2 / th2
        bx, by = x * f, y * f
        # coordenadas en el plano del disco
        X = bx; Y = by / math.cos(self.inc)
        self.rad = np.sqrt(X * X + Y * Y)
        self.phi = np.arctan2(Y, X)
        self.shadow = np.sqrt(th2) < thE * 1.25
        self.ring = np.exp(-((np.sqrt(th2) - thE * 1.27) / 0.006) ** 2)
        tex = noise2(256, 1024, r, 6, 4)
        self.tex = np.concatenate([tex, tex[:, :1]], 1)
        bg = starfield(r, n=3000, tint=(40, 30, 80))
        sx = np.clip((bx * H * 0.5 * sc + W / 2).astype(int), 0, W - 1)
        sy = np.clip((by * H * 0.5 * sc + H / 2).astype(int), 0, H - 1)
        self.bg = bg[sy, sx] * (~self.shadow)[..., None]
        self.rin, self.rout = 0.32, 1.05
        self.mask = (self.rad > self.rin) & (self.rad < self.rout) & (~self.shadow)
        self.z0 = r.uniform(1.0, 1.1); self.z1 = self.z0 * r.uniform(1.05, 1.25)

    def frame(self, t):
        rad, phi = self.rad, self.phi
        om = 0.9 / (np.maximum(rad, 0.2) ** 1.5)
        u = ((phi + om * t) / (2 * np.pi)) % 1.0
        v = np.clip((rad - self.rin) / (self.rout - self.rin), 0, 0.999)
        tv = self.tex[(v * 255).astype(int), (u * 1024).astype(int)]
        bright = (self.rin / np.maximum(rad, self.rin)) ** 2.2 * (0.45 + 0.9 * tv) * (1 + 0.55 * np.cos(phi))
        bright *= np.clip((rad - self.rin) / 0.05, 0, 1) * np.clip((self.rout - rad) / 0.35, 0, 1)
        bright = np.where(self.mask, bright, 0)
        col = np.stack([bright * 255 * 1.4, bright * 255 * 0.85, bright * 255 * 0.45], -1)
        img = self.bg + col + self.ring[..., None] * np.array([255, 210, 160]) * 1.2
        u_ = t / self.dur
        return cam_crop(img, self.z0 + (self.z1 - self.z0) * ease(u_))


# ------------------------------------------------------------ galaxia espiral de partículas
class Galaxy(CGI):
    def setup(self):
        r = self.rng
        n = 160000
        arms = r.choice([2, 2, 4])
        rad = r.exponential(0.32, n).clip(0, 1.5)
        arm = r.integers(0, arms, n)
        ang = arm * 2 * np.pi / arms + np.log(rad + 0.05) * 2.4 + r.normal(0, 0.28, n) * (0.4 + rad)
        bulge = r.random(n) < 0.22
        rad[bulge] = np.abs(r.normal(0, 0.12, bulge.sum()))
        ang[bulge] = r.uniform(0, 2 * np.pi, bulge.sum())
        self.rad, self.ang = rad, ang
        self.zz = r.normal(0, 0.02, n)
        c = np.where(bulge[:, None], [255, 210, 150], [150, 180, 255])
        hot = (~bulge) & (r.random(n) < 0.06)
        c[hot] = [255, 120, 200]
        self.col = c.astype(np.float32) * r.uniform(0.3, 1.0, n)[:, None]
        self.inc0 = math.radians(r.uniform(35, 70)); self.inc1 = self.inc0 + math.radians(r.uniform(-15, 15))
        self.rot = r.uniform(0, 6)
        self.bg = starfield(r, n=2500, tint=(30, 20, 60))
        self.scale0 = r.uniform(380, 460); self.scale1 = self.scale0 * r.uniform(1.1, 1.6)
        self.hue = r.integers(0, 3)

    def frame(self, t):
        u = ease(t / self.dur)
        a = self.ang + 0.15 * t / (0.2 + self.rad) + self.rot
        x = self.rad * np.cos(a); y = self.rad * np.sin(a)
        inc = self.inc0 + (self.inc1 - self.inc0) * u
        ys = y * math.cos(inc) + self.zz * math.sin(inc)
        s = self.scale0 + (self.scale1 - self.scale0) * u
        px = (x * s + W / 2).astype(int); py = (ys * s + H / 2).astype(int)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        acc = np.zeros((H, W, 3), np.float32)
        np.add.at(acc, (py[ok], px[ok]), self.col[ok] * 0.55)
        small = Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
        glow = np.asarray(small.filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR), np.float32)
        img = self.bg * 0.8 + acc + glow * 2.2
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# ------------------------------------------------------------ viaje entre estrellas
class Warp(CGI):
    def setup(self):
        r = self.rng
        self.n = 2500
        self.p = np.stack([r.uniform(-1, 1, self.n), r.uniform(-1, 1, self.n), r.uniform(0.05, 1, self.n)], 1)
        self.bg = starfield(r, n=800, tint=tuple(int(v) for v in r.choice([[70, 30, 110], [20, 60, 110], [110, 40, 60]])))
        self.speed = r.uniform(0.12, 0.3)

    def frame(self, t):
        img = Image.fromarray((self.bg * 0.9).astype(np.uint8))
        d = ImageDraw.Draw(img)
        z = (self.p[:, 2] - t * self.speed) % 1.0 + 0.02
        z2 = z + 0.012 + self.speed * 0.04
        f = 500
        x1 = self.p[:, 0] / z * f + W / 2; y1 = self.p[:, 1] / z * f + H / 2
        x2 = self.p[:, 0] / z2 * f + W / 2; y2 = self.p[:, 1] / z2 * f + H / 2
        b = np.clip((1 - z) * 300, 0, 255)
        for i in np.argsort(-z):
            if 0 <= x1[i] < W and 0 <= y1[i] < H:
                c = int(b[i])
                d.line([(x2[i], y2[i]), (x1[i], y1[i])], fill=(c, c, min(255, c + 30)), width=1 + int(2 * (1 - z[i])))
        return img


# ------------------------------------------------------------ planetas texturizados
def planet_texture(kind, rng, h=512, w=1024):
    t = _planet_texture(kind, rng, h, w // 2)
    return np.concatenate([t, t[:, ::-1]], 1).astype(np.float32)


def _planet_texture(kind, rng, h=512, w=512):
    n = noise2(h, w, rng, 6, 4)
    n2 = noise2(h, w, rng, 5, 8)
    lat = np.linspace(-1, 1, h)[:, None]
    if kind == "europa":
        base = np.stack([200 + 40 * n, 190 + 35 * n, 175 + 30 * n], -1)
        img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        for _ in range(140):
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            pts = [(x, y)]
            a = rng.uniform(0, np.pi)
            for k in range(rng.integers(6, 20)):
                a += rng.normal(0, 0.15); x += math.cos(a) * 18; y += math.sin(a) * 9
                pts.append((x % w, y))
            d.line(pts, fill=(150, 90, 60), width=int(rng.integers(1, 4)))
        return np.asarray(img, np.float32)
    if kind == "titan":
        return np.stack([200 + 40 * n, 140 + 30 * n, 60 + 20 * n], -1)
    if kind == "jupiter":
        bands = np.sin(lat * 22 + n2 * 3.0)
        c1 = np.array([230, 200, 170]); c2 = np.array([170, 110, 70]); c3 = np.array([245, 235, 220])
        t = (bands * 0.5 + 0.5)[..., None]
        img = c1 * t + c2 * (1 - t)
        img = img * (0.85 + 0.3 * n[..., None]) * np.ones((1, w, 1))
        yy, xx = np.mgrid[0:h, 0:w]
        spot = np.exp(-(((xx - w * 0.3) / 40) ** 2 + ((yy - h * 0.62) / 20) ** 2))
        img = img * (1 - spot[..., None]) + np.array([200, 90, 60]) * spot[..., None]
        return img
    if kind == "saturn":
        bands = np.sin(lat * 16 + n2 * 1.2)
        t = (bands * 0.5 + 0.5)[..., None]
        return (np.array([235, 215, 170]) * t + np.array([200, 170, 120]) * (1 - t)) * np.ones((1, w, 1))
    if kind == "earth":
        land = (n > 0.52)
        ocean = np.stack([20 + 30 * n, 60 + 50 * n, 140 + 60 * n], -1)
        green = np.stack([60 + 80 * n2, 110 + 60 * n2, 50 + 30 * n2], -1)
        img = np.where(land[..., None], green, ocean)
        ice = np.abs(lat) > 0.82
        img = np.where(ice[..., None] * np.ones((1, w, 1), bool), np.array([240, 245, 250]), img)
        return img
    if kind == "cmb":
        m = noise2(h, w, rng, 7, 16) - 0.5
        t = np.clip(m * 3 + 0.5, 0, 1)[..., None]
        return np.array([30, 60, 200]) * (1 - t) + np.array([255, 120, 40]) * t
    if kind == "neutron":
        return np.stack([170 + 60 * n, 200 + 40 * n, 255 + 0 * n], -1)
    return np.stack([128 + 60 * n] * 3, -1)


class Planet(CGI):
    kind = "europa"

    def setup(self):
        r = self.rng
        self.tex = planet_texture(self.kind, r)
        self.clouds = (lambda c: np.concatenate([c, c[:, ::-1]], 1))(noise2(512, 512, r, 5, 6)) if self.kind == "earth" else None
        self.R0 = H * r.uniform(0.30, 0.38); self.R1 = self.R0 * r.uniform(1.05, 1.5)
        self.cx = W * r.uniform(0.38, 0.62); self.cy = H * r.uniform(0.45, 0.55)
        self.tilt = r.uniform(-0.3, 0.3)
        self.spin = r.uniform(0.02, 0.05) * r.choice([-1, 1])
        self.light = np.array([-0.6, -0.3, 0.75]); self.light /= np.linalg.norm(self.light)
        self.bg = starfield(r, n=2500, nebula=r.random() < 0.5)
        self.atm = {"titan": (255, 170, 70), "earth": (100, 160, 255), "europa": (180, 200, 255), "jupiter": (255, 220, 180),
                    "saturn": (255, 230, 180), "cmb": (0, 0, 0), "neutron": (120, 170, 255)}[self.kind]
        self.rings = self.kind == "saturn"

    def sphere(self, img, R, cx, cy, t, tex, spin, tilt, atm, emissive=False):
        x0, x1 = max(0, int(cx - R * 1.12)), min(W, int(cx + R * 1.12) + 1)
        y0, y1 = max(0, int(cy - R * 1.12)), min(H, int(cy + R * 1.12) + 1)
        if x1 <= x0 or y1 <= y0:
            return img
        img = img.copy()
        img[y0:y1, x0:x1] = self._sphere(img[y0:y1, x0:x1], R, cx - x0, cy - y0, t, tex, spin, tilt, atm, emissive)
        return img

    def _sphere(self, img, R, cx, cy, t, tex, spin, tilt, atm, emissive=False):
        hh, ww = img.shape[:2]
        y, x = np.mgrid[0:hh, 0:ww].astype(np.float32)
        X = (x - cx) / R; Y = (y - cy) / R
        rr = X * X + Y * Y
        m = rr < 1
        Z = np.sqrt(np.clip(1 - rr, 0, 1))
        ct, st = math.cos(tilt), math.sin(tilt)
        Xr = X * ct - Y * st; Yr = X * st + Y * ct
        lat = np.arcsin(np.clip(Yr, -1, 1))
        lon = np.arctan2(Xr, Z) + t * spin
        th, tw = tex.shape[:2]
        u = ((lon / (2 * np.pi)) % 1 * (tw - 1)).astype(int)
        v = ((lat / np.pi + 0.5) * (th - 1)).astype(int)
        c = tex[v, u]
        if self.clouds is not None and tex is self.tex:
            cl = self.clouds[v, ((u + int(t * 8)) % self.clouds.shape[1])]
            c = c * (1 - np.clip(cl * 1.6 - 0.6, 0, 1)[..., None]) + 255 * np.clip(cl * 1.6 - 0.6, 0, 1)[..., None]
        if emissive:
            shade = np.ones_like(Z) * (0.6 + 0.4 * Z)
        else:
            shade = np.clip(X * self.light[0] + Y * self.light[1] + Z * self.light[2], 0, 1) ** 0.8 * 1.1 + 0.03
        out = np.where(m[..., None], c * shade[..., None], img)
        rim = np.exp(-((np.sqrt(rr) - 1) / 0.035) ** 2) * (1 + np.clip(-X * 0.6 - Y * 0.3, 0, 1))
        out = out + rim[..., None] * np.array(atm) * 0.5
        return out

    def frame(self, t):
        u = ease(t / self.dur)
        R = self.R0 + (self.R1 - self.R0) * u
        img = self.bg.copy()
        if self.rings:
            img = self.draw_rings(img, R, back=True)
        img = self.sphere(img, R, self.cx, self.cy, t, self.tex, self.spin, self.tilt, self.atm)
        if self.rings:
            img = self.draw_rings(img, R, back=False)
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

    def draw_rings(self, img, R, back):
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        X = (x - self.cx) / R; Y = (y - self.cy) / R
        inc = 0.28
        rr = np.sqrt(X ** 2 + (Y / inc) ** 2)
        ring = (rr > 1.25) & (rr < 2.3)
        sel = ring & ((Y < 0) if back else (Y >= 0))
        if not back:
            sel &= ~((X ** 2 + Y ** 2) < 1) | (Y > 0)
        band = 0.6 + 0.4 * np.sin(rr * 40) * np.sin(rr * 7)
        band *= np.where((rr > 1.9) & (rr < 1.97), 0.1, 1)
        col = np.array([220, 200, 160]) * band[..., None]
        return np.where(sel[..., None], img * 0.25 + col * 0.8, img)


class PlanetEuropa(Planet): kind = "europa"
class PlanetTitan(Planet): kind = "titan"
class PlanetEarth(Planet): kind = "earth"
class SaturnView(Planet): kind = "saturn"


class CMBSphere(Planet):
    kind = "cmb"

    def frame(self, t):
        u = ease(t / self.dur)
        R = self.R0 + (self.R1 - self.R0) * u
        img = self.sphere(np.zeros((H, W, 3), np.float32), R, self.cx, self.cy, t, self.tex, self.spin * 2, self.tilt, (80, 80, 120), emissive=True)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        label(im, "Fondo cósmico de microondas · ilustración", 60, H - 90, 34, (200, 220, 255))
        return im


class JupiterView(Planet):
    kind = "jupiter"

    def setup(self):
        super().setup()
        self.R0 = H * 0.75; self.R1 = H * 0.8; self.cx = W * 0.25; self.cy = H * 0.5
        self.etex = planet_texture("europa", self.rng)
        self.spin = 0.03

    def frame(self, t):
        img = self.bg.copy()
        img = self.sphere(img, self.R0 + (self.R1 - self.R0) * ease(t / self.dur), self.cx, self.cy, t, self.tex, self.spin, 0.05, self.atm)
        ex = W * (0.92 - 0.25 * t / self.dur)
        img = self.sphere(img, H * 0.09, ex, H * 0.42, t, self.etex, 0.1, 0.1, (180, 200, 255))
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


class Magnetar(Planet):
    kind = "neutron"

    def setup(self):
        super().setup()
        self.R0 = H * 0.12; self.R1 = H * 0.14; self.cx, self.cy = W / 2, H / 2
        self.bg = starfield(self.rng, n=2000, nebula=False)

    def frame(self, t):
        img = self.bg.copy()
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        R = self.R0
        ax = t * 0.8
        for k in range(1, 9):
            L = 1.4 + k * 0.55
            for s in (-1, 1):
                pts = []
                for th in np.linspace(0.12, np.pi - 0.12, 60):
                    rr = L * math.sin(th) ** 2 * R
                    x = rr * math.sin(th) * s; y = -rr * math.cos(th)
                    xr = x * math.cos(ax) * 1.0; yr = y
                    a = 0.4
                    pts.append((W / 2 + xr * math.cos(a) - yr * math.sin(a), H / 2 + xr * math.sin(a) + yr * math.cos(a)))
                d.line(pts, fill=(120, 170, 255, 90 + 15 * (k % 3)), width=2)
        img = np.asarray(im, np.float32)
        img = self.sphere(img, R, W / 2, H / 2, t, self.tex, 1.5, 0.4, (150, 200, 255), emissive=True)
        flare = max(0, math.sin(t * 2.2)) ** 20
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        g = np.exp(-(((x - W / 2) ** 2 + (y - H / 2) ** 2) / (R * (2.5 + 4 * flare)) ** 2))
        img += g[..., None] * np.array([120, 170, 255]) * (0.8 + 2.5 * flare)
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# ------------------------------------------------------------ gráficos explicativos
class RotationCurve(CGI):
    def setup(self):
        self.bg = starfield(self.rng, n=1500, tint=(20, 20, 50)) * 0.6
        self.gal = Galaxy(np.random.default_rng(self.rng.integers(1e9)), self.dur)

    def frame(self, t):
        g = self.gal.frame(t).resize((W // 2, H // 2))
        im = Image.fromarray(self.bg.astype(np.uint8))
        im.paste(g, (-120, H // 4))
        d = ImageDraw.Draw(im, "RGBA")
        x0, y0, x1, y1 = 880, 820, 1800, 220
        d.rectangle([x0 - 40, y1 - 90, x1 + 40, y0 + 110], fill=(5, 8, 20, 190))
        d.line([(x0, y0), (x1, y0)], fill=(200, 200, 220), width=3); d.line([(x0, y0), (x0, y1)], fill=(200, 200, 220), width=3)
        label(im, "Distancia al centro", (x0 + x1) // 2, y0 + 50, 30, anchor="ma")
        label(im, "Velocidad de giro", x0 - 10, y1 - 70, 30)
        u = ease(t / (self.dur * 0.8))
        xs = np.linspace(0.02, 1, 120)[: max(2, int(120 * u))]
        kep = [(x0 + x * (x1 - x0), y0 - (y0 - y1) * 0.85 * min(1, 2.2 * x) * (0.25 / max(x, 0.25)) ** 0.5) for x in xs]
        obs = [(x0 + x * (x1 - x0), y0 - (y0 - y1) * 0.85 * min(1, 2.2 * x) * (1 - 0.05 * x)) for x in xs]
        d.line(kep, fill=(255, 170, 60), width=6)
        d.line(obs, fill=(90, 220, 255), width=6)
        if u > 0.5:
            a = int(255 * min(1, (u - 0.5) * 3))
            label(im, "Esperado (solo materia visible)", x1 - 10, y0 - 120, 30, (255, 170, 60), "ra", a)
            label(im, "Observado", x1 - 10, y1 + 40, 30, (90, 220, 255), "ra", a)
        return im


class Pie(CGI):
    def frame(self, t):
        if not hasattr(self, "bg"):
            self.bg = starfield(self.rng, n=1500, tint=(30, 20, 60)) * 0.7
        im = Image.fromarray(self.bg.astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        u = ease(t / (self.dur * 0.6))
        parts = [(68, (120, 90, 255), "Energía oscura ≈ 68 %"), (27, (60, 200, 230), "Materia oscura ≈ 27 %"), (5, (255, 200, 80), "Materia ordinaria ≈ 5 %")]
        cx, cy, R = 620, 560, 330
        a0 = -90
        for i, (p, c, txt) in enumerate(parts):
            a1 = a0 + 360 * p / 100 * u
            d.pieslice([cx - R, cy - R, cx + R, cy + R], a0, a1, fill=c + (230,))
            a0 = a0 + 360 * p / 100 * u
        d.ellipse([cx - R * 0.55, cy - R * 0.55, cx + R * 0.55, cy + R * 0.55], fill=(5, 5, 15, 255))
        label(im, "El universo", cx, cy - 25, 44, anchor="ma")
        for i, (p, c, txt) in enumerate(parts):
            a = int(255 * min(1, max(0, (t - 1 - i * 0.6) * 2)))
            d.rectangle([1100, 360 + i * 130, 1150, 410 + i * 130], fill=c + (a,))
            label(im, txt, 1180, 360 + i * 130, 44, alpha=a)
        label(im, "Valores aproximados (Planck)", 1100, 760, 28, (180, 190, 220))
        return im


class Expansion(CGI):
    def setup(self):
        r = self.rng
        self.pts = r.uniform(-1, 1, (600, 2)); self.sz = r.uniform(2, 6, 600)
        self.col = np.array([[255, 220, 180], [170, 200, 255], [255, 170, 210]])[r.integers(0, 3, 600)]

    def frame(self, t):
        im = Image.new("RGB", (W, H), (3, 4, 12))
        d = ImageDraw.Draw(im, "RGBA")
        a = 0.35 + 0.08 * t + 0.02 * t * t
        for k in range(-12, 13):
            x = W / 2 + k * 160 * a
            d.line([(x, 0), (x, H)], fill=(60, 80, 140, 70)); y = H / 2 + k * 160 * a
            d.line([(0, y), (W, y)], fill=(60, 80, 140, 70))
        for (x, y), s, c in zip(self.pts, self.sz, self.col):
            px, py = W / 2 + x * W * a, H / 2 + y * H * a
            if -20 < px < W + 20 and -20 < py < H + 20:
                d.ellipse([px - s, py - s * 0.6, px + s, py + s * 0.6], fill=tuple(c) + (230,))
        label(im, "El espacio se expande cada vez más rápido", 60, 60, 40)
        label(im, "Animación ilustrativa", 60, H - 80, 28, (170, 180, 210))
        return im


class FRB(CGI):
    def setup(self):
        r = self.rng
        self.noise = r.random((260, 480)).astype(np.float32)

    def frame(self, t):
        im = Image.new("RGB", (W, H), (4, 6, 16))
        x0, y0, w, h = 200, 180, 1100, 720
        nz = (np.roll(self.noise, int(t * 30), 1) * 60).astype(np.float32)
        ff = np.linspace(1, 0, 260)[:, None]
        tt = np.linspace(0, 1, 480)[None, :]
        delay = 0.15 + 0.5 * (1 / (0.4 + 0.6 * ff) ** 2 - 1) / (1 / 0.16 - 1)
        prog = (t / self.dur) * 1.4
        sig = np.exp(-((tt - delay) / 0.006) ** 2) * (tt < prog) * 255
        arr = np.clip(nz + sig, 0, 255)
        rgb = np.stack([arr * 0.4, arr * 0.9, arr], -1).astype(np.uint8)
        im.paste(Image.fromarray(rgb).resize((w, h), Image.BILINEAR), (x0, y0))
        d = ImageDraw.Draw(im)
        d.rectangle([x0, y0, x0 + w, y0 + h], outline=(120, 140, 200), width=3)
        label(im, "Tiempo →", x0 + w // 2, y0 + h + 30, 32, anchor="ma")
        label(im, "Frecuencia", x0 - 30, y0 - 60, 32)
        label(im, "Ráfaga rápida de radio: dura ~1 milisegundo", 1360, 300, 38)
        label(im, "Las frecuencias bajas llegan más tarde", 1360, 380, 30, (150, 220, 255))
        label(im, "porque la señal atraviesa gas intergaláctico", 1360, 430, 30, (150, 220, 255))
        label(im, "Ilustración", 1360, 980, 26, (160, 170, 200))
        return im


class RadioDish(CGI):
    def setup(self):
        r = self.rng
        self.bg = starfield(r, n=4000, tint=(50, 40, 90))
        band = noise2(H // 4, W // 4, r, 5, 3)
        y, x = np.mgrid[0:H // 4, 0:W // 4]
        mw = np.exp(-((y - (x * 0.35 + 20)) / 30) ** 2) * band
        mw = np.asarray(Image.fromarray((np.clip(mw, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
        self.bg += mw[..., None] * np.array([200, 180, 170])
        self.n = int(r.integers(2, 5))

    def frame(self, t):
        sh = int(t * 6)
        img = np.roll(self.bg, sh, 1)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.rectangle([0, H * 0.82, W, H], fill=(5, 6, 10))
        for k in range(self.n):
            cx = W * (0.2 + 0.6 * k / max(1, self.n - 1)); cy = H * 0.62; R = 200 - k * 25
            ang = math.radians(-30 + 8 * math.sin(t * 0.3 + k))
            d.line([(cx, cy), (cx, H * 0.83)], fill=(10, 12, 18), width=24)
            d.polygon([(cx - 70, H * 0.83), (cx + 70, H * 0.83), (cx, H * 0.7)], fill=(10, 12, 18))
            pts = [(cx + R * math.cos(a) * math.cos(ang) - R * 0.25 * math.sin(a) * math.sin(ang) * 0,
                    cy + R * math.cos(a) * math.sin(ang) + R * 0.35 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 50)]
            d.polygon(pts, fill=(14, 16, 24))
            d.line([(cx, cy), (cx + math.sin(-ang) * 160, cy - math.cos(ang) * 160)], fill=(14, 16, 24), width=6)
        return im


class GW(CGI):
    def frame(self, t):
        im = Image.new("RGB", (W, H), (2, 3, 10))
        d = ImageDraw.Draw(im, "RGBA")
        T = self.dur
        merge = T * 0.75
        sep = max(0.0, 1 - t / merge) ** 0.25 * 220
        om = 1.5 + 12 * (t / merge) ** 3 if t < merge else 0
        ph = 2 + t * om
        cx, cy = W / 2, H * 0.45
        for i in range(-16, 17):
            pts = []
            for j in range(-30, 31):
                x = j * 40; y = i * 40
                rr = math.hypot(x, y) + 1
                amp = (14 if t < merge else 24 * math.exp(-(t - merge) * 1.5)) * math.sin(rr * 0.03 - t * 8 + 2 * math.atan2(y, x))
                well = -2500 / (rr + 80)
                X = cx + x * 1.0
                Y = cy + 180 + y * 0.35 + (well + amp) * 1.2
                pts.append((X, Y))
            d.line(pts, fill=(80, 140, 255, 110), width=2)
        for j in range(-30, 31, 1):
            pass
        if t < merge:
            for s in (-1, 1):
                x = cx + s * sep * math.cos(ph); y = cy + s * sep * math.sin(ph) * 0.35
                d.ellipse([x - 38, y - 38, x + 38, y + 38], fill=(0, 0, 0), outline=(255, 180, 90, 200), width=5)
        else:
            k = math.exp(-(t - merge) * 3)
            d.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], fill=(0, 0, 0), outline=(255, 200, 120, 220), width=6)
            d.ellipse([cx - 400 * k - 60, cy - 400 * k - 60, cx + 400 * k + 60, cy + 400 * k + 60], outline=(255, 255, 255, int(200 * k)), width=10)
        label(im, "Fusión de dos agujeros negros · ondas gravitacionales (ilustración)", 60, H - 90, 30, (190, 200, 230))
        return im


class HubbleChart(CGI):
    def frame(self, t):
        im = Image.new("RGB", (W, H), (4, 6, 16))
        d = ImageDraw.Draw(im, "RGBA")
        x0, x1, y = 260, 1660, 640
        lo, hi = 64, 77
        X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
        d.line([(x0, y), (x1, y)], fill=(180, 190, 220), width=4)
        for v in range(lo, hi + 1):
            d.line([(X(v), y - 10), (X(v), y + 10)], fill=(180, 190, 220), width=2)
            if v % 2 == 0:
                label(im, str(v), X(v), y + 25, 30, anchor="ma")
        label(im, "Constante de Hubble (km/s por megapársec)", W / 2, y + 90, 34, anchor="ma")
        items = [(67.4, 0.5, (90, 200, 255), "Universo primitivo (Planck): ~67", 330, 0.5),
                 (73.0, 1.0, (255, 140, 90), "Universo cercano (cefeidas + supernovas): ~73", 440, 2.0),
                 (69.5, 2.0, (200, 200, 120), "Otros métodos con el Webb: ~68–70", 530, 4.0)]
        for v, e, c, txt, yy, t0 in items:
            a = min(1, max(0, (t - t0) * 2))
            if a <= 0: continue
            A = int(255 * a)
            d.line([(X(v - e), yy), (X(v + e), yy)], fill=c + (A,), width=6)
            d.ellipse([X(v) - 16, yy - 16, X(v) + 16, yy + 16], fill=c + (A,))
            label(im, txt, X(v), yy - 70, 32, c, "ma", A)
        if t > 3.0:
            a = int(255 * min(1, (t - 3) * 1.5))
            label(im, "¿POR QUÉ NO COINCIDEN?", W / 2, 120, 64, (255, 255, 255), "ma", a)
        return im


class BigBang(CGI):
    def setup(self):
        r = self.rng
        n = 20000
        self.dir = r.normal(0, 1, (n, 3)); self.dir /= np.linalg.norm(self.dir, axis=1, keepdims=True)
        self.sp = r.uniform(0.3, 1.0, n)

    def frame(self, t):
        u = t / self.dur
        R = (u ** 0.6) * 900
        p = self.dir * (self.sp * R)[:, None]
        px = (p[:, 0] + W / 2).astype(int); py = (p[:, 1] * 0.9 + H / 2).astype(int)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        acc = np.zeros((H, W, 3), np.float32)
        temp = max(0, 1 - u * 1.3)
        col = np.array([255, 200 * (0.4 + 0.6 * temp) + 40, 255 * temp * 0.6 + 60 * (1 - temp)])
        np.add.at(acc, (py[ok], px[ok]), col * 2.5)
        small = Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
        img = acc + np.asarray(small.resize((W, H)), np.float32) * 6
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        core = np.exp(-((x - W / 2) ** 2 + (y - H / 2) ** 2) / (40 + R * 0.3) ** 2) * 255 * max(0, 1 - u * 1.5) * 2
        img += core[..., None]
        if u < 0.05:
            img += 255 * (1 - u / 0.05)
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


class Multiverse(CGI):
    def setup(self):
        r = self.rng
        self.b = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.3, 1.2), r.uniform(0, 4), r.integers(0, 3)) for _ in range(26)]

    def frame(self, t):
        im = Image.new("RGB", (W, H), (6, 4, 18))
        d = ImageDraw.Draw(im, "RGBA")
        cols = [(120, 90, 255), (60, 200, 230), (255, 120, 200)]
        for x, y, g, t0, c in self.b:
            if t < t0: continue
            R = 30 + (t - t0) * 70 * g
            d.ellipse([x - R, y - R, x + R, y + R], outline=cols[c] + (200,), width=4, fill=cols[c] + (25,))
        label(im, "Hipótesis: universos burbuja (inflación eterna) · ilustración", 60, H - 90, 30, (200, 200, 230))
        return im


class GhostGalaxy(CGI):
    def setup(self):
        r = self.rng
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        rr = np.sqrt(((x - W / 2) / 1.2) ** 2 + (y - H / 2) ** 2)
        n = noise2(H // 4, W // 4, r, 4, 3)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H)), np.float32) / 255
        self.base = starfield(r, n=1800, tint=(20, 20, 40)) * 0.8 + (np.exp(-(rr / 330) ** 1.3) * (0.7 + 0.5 * n))[..., None] * np.array([90, 95, 110])
        self.gc = [(r.uniform(-280, 280), r.uniform(-200, 200), r.uniform(0, 6)) for _ in range(10)]

    def frame(self, t):
        z = 1 + 0.12 * ease(t / self.dur)
        im = cam_crop(self.base, z)
        d = ImageDraw.Draw(im, "RGBA")
        for gx, gy, ph in self.gc:
            x = W / 2 + (gx + 10 * math.sin(t * 0.3 + ph)) * z; y = H / 2 + (gy + 6 * math.cos(t * 0.3 + ph)) * z
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 240, 210, 240))
            if t > 1.5:
                d.ellipse([x - 22, y - 22, x + 22, y + 22], outline=(120, 220, 255, 160), width=2)
        if t > 1.5:
            label(im, "Cúmulos globulares", W / 2 + 330, H / 2 - 260, 34, (120, 220, 255))
        label(im, "Galaxia ultradifusa · recreación artística", 60, H - 90, 30, (190, 200, 230))
        return im


class Collision(CGI):
    def frame(self, t):
        im = Image.new("RGB", (W, H), (3, 4, 12))
        d = ImageDraw.Draw(im, "RGBA")
        u = t / self.dur
        cx = W / 2
        off = (1 - 2 * u) * 650
        gas_off = max(abs(off), 120) * (1 if off > 0 else -1) if abs(off) > 120 else off * 0.3
        for s in (-1, 1):
            x = cx + s * off
            for k in range(8, 0, -1):
                R = 40 + k * 28
                d.ellipse([x - R, H / 2 - R, x + R, H / 2 + R], fill=(150, 90, 255, 12))
            gx = cx + s * (off if abs(off) > 140 else 140 * (abs(off) / 140) ** 0.2 * (1 if off * s > 0 else 1) * 0 + s * 0 + off * 0.15)
            for k in range(5, 0, -1):
                R = 15 + k * 18
                d.ellipse([gx - R * 1.3, H / 2 - R, gx + R * 1.3, H / 2 + R], fill=(80, 200, 255, 30))
        label(im, "Materia oscura", 80, 80, 36, (180, 130, 255)); label(im, "Gas", 80, 140, 36, (90, 210, 255))
        label(im, "Hipótesis: colisión de galaxias enanas · ilustración", 60, H - 90, 30, (190, 200, 230))
        return im


class EuropaCut(CGI):
    def frame(self, t):
        if not hasattr(self, "bg"):
            self.bg = starfield(self.rng, n=2000, nebula=False)
            self.tex = planet_texture("europa", self.rng)
        img = self.bg.copy()
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy, R = W * 0.4, H * 0.52, H * 0.42
        X = (x - cx) / R; Y = (y - cy) / R; rr = np.sqrt(X * X + Y * Y)
        Z = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
        lon = np.arctan2(X, Z) + t * 0.05; lat = np.arcsin(np.clip(Y, -1, 1))
        u_ = ((lon / (2 * np.pi)) % 1 * 1023).astype(int); v_ = ((lat / np.pi + 0.5) * 511).astype(int)
        shade = np.clip(-0.5 * X - 0.2 * Y + 0.8 * Z, 0, 1) + 0.05
        surf = self.tex[v_, u_] * shade[..., None]
        open_ = ease(t / (self.dur * 0.5))
        wedge = (X > 0) & (Y < 0) & (rr < 1)
        img = np.where((rr < 1)[..., None], surf, img)
        if open_ > 0:
            lay = np.where(rr > 0.9, 0, np.where(rr > 0.78, 1, np.where(rr > 0.35, 2, 3)))
            cols = np.array([[235, 240, 255], [40, 110, 220], [120, 90, 70], [180, 150, 110]], np.float32)
            wave = 1 + 0.08 * np.sin(rr * 120 - t * 4)
            cut = cols[lay] * np.where(lay == 1, wave, 1)[..., None]
            m = wedge & (np.arctan2(-Y, X) < open_ * np.pi / 2)
            img = np.where(m[..., None], cut, img)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        if open_ > 0.9:
            labs = [("Corteza de hielo", 0.95), ("Océano de agua salada (probable)", 0.84), ("Manto rocoso", 0.6), ("Núcleo metálico", 0.2)]
            for i, (txt, rv) in enumerate(labs):
                a = int(255 * min(1, max(0, (t - self.dur * 0.5 - i * 0.4) * 2)))
                px, py = cx + rv * R * 0.6, cy - rv * R * 0.6
                ImageDraw.Draw(im, "RGBA").line([(px, py), (W * 0.72, 260 + i * 140)], fill=(255, 255, 255, a), width=2)
                label(im, txt, W * 0.72 + 15, 240 + i * 140, 36, alpha=a)
        label(im, "Estructura interna de Europa · ilustración", 60, H - 80, 28, (190, 200, 230))
        return im


class TitanLake(CGI):
    def setup(self):
        r = self.rng
        self.sky = np.zeros((H, W, 3), np.float32)
        yy = np.linspace(0, 1, H)[:, None, None]
        self.sky = np.array([230, 150, 70]) * (1 - yy) * 0.9 + np.array([120, 70, 30]) * yy
        self.hills = [(noise2(1, W, r, 5, 4)[0] * 160 + H * (0.45 + 0.04 * k), (110 - k * 30, 60 - k * 18, 30 - k * 8)) for k in range(3)]
        self.drops = np.stack([r.uniform(0, W, 500), r.uniform(0, H, 500)], 1)

    def frame(self, t):
        img = self.sky.copy() * np.ones((1, W, 1))
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        for line, c in self.hills:
            pts = [(x, line[x]) for x in range(0, W, 8)] + [(W, H), (0, H)]
            d.polygon(pts, fill=c)
        hy = int(H * 0.62)
        d.rectangle([0, hy, W, H], fill=(25, 18, 15))
        for k in range(60):
            yy = hy + 6 + k * k * 0.12
            if yy > H: break
            x0 = (k * 97 + t * 30 * (1 + k * 0.02)) % W
            d.line([(x0 - 120 - k * 4, yy), (x0 + 120 + k * 4, yy)], fill=(200, 130, 60, 60), width=2)
        for x, y in self.drops:
            yy = (y + t * 120) % H
            d.line([(x, yy), (x - 2, yy + 14)], fill=(255, 200, 140, 70), width=2)
        haze = Image.new("RGBA", (W, H), (230, 160, 80, 50))
        im = Image.alpha_composite(im.convert("RGBA"), haze).convert("RGB")
        label(im, "Lago de metano en Titán · recreación artística", 60, H - 80, 28, (255, 230, 200))
        return im


class DeepZoom(CGI):
    def setup(self):
        r = self.rng
        self.g = [(r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-3, 0), r.uniform(0, 3.14), r.uniform(0.3, 1), r.integers(0, 4)) for _ in range(1400)]

    def frame(self, t):
        im = Image.new("RGB", (W, H), (2, 2, 6))
        d = ImageDraw.Draw(im, "RGBA")
        cols = [(255, 220, 170), (170, 200, 255), (255, 160, 120), (255, 90, 70)]
        zt = t * 0.25
        for x, y, z, a, e, c in self.g:
            zz = (z + zt) % 3 - 3
            s = 2 ** (zz + 3)
            px, py = W / 2 + x * W * 0.5 * s, H / 2 + y * H * 0.5 * s
            R = 3 * s
            if -50 < px < W + 50 and -50 < py < H + 50 and R < 200:
                al = int(min(255, 60 + 60 * s))
                d.ellipse([px - R, py - R * e, px + R, py + R * e], fill=cols[c] + (al,))
        im = im.filter(ImageFilter.GaussianBlur(0.8))
        label(im, "Campo profundo · ilustración", 60, H - 80, 28, (190, 200, 230))
        return im


class Timeline(CGI):
    def frame(self, t):
        im = Image.fromarray((starfield(np.random.default_rng(3), n=1500, tint=(20, 20, 50)) * 0.5).astype(np.uint8)) if not hasattr(self, "_bg") else self._bg.copy()
        self._bg = im.copy() if not hasattr(self, "_bg") else self._bg
        d = ImageDraw.Draw(im, "RGBA")
        x0, x1, y = 200, 1640, 560
        d.line([(x0, y), (x1, y)], fill=(200, 210, 240), width=5)
        evs = [(0.0, "Big Bang"), (0.06, "380.000 años:\nfondo de microondas"), (0.2, "~280 millones de años:\nMoM-z14"),
               (0.45, "Primeras galaxias\nmaduras"), (1.0, "Hoy:\n13.800 millones de años")]
        u = ease(t / (self.dur * 0.8))
        for i, (p, txt) in enumerate(evs):
            x = x0 + (x1 - x0) * (p ** 0.6 if p > 0 else 0)
            if (x - x0) / (x1 - x0) <= u + 0.01:
                d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(255, 200, 90))
                yy = y - 150 if i % 2 == 0 else y + 50
                d.multiline_text((x, yy), txt, font=font(32), fill=(255, 255, 255), anchor="ma", align="center", stroke_width=3, stroke_fill=(0, 0, 0))
        d.line([(x0, y), (x0 + (x1 - x0) * u, y)], fill=(255, 200, 90), width=8)
        label(im, "Línea temporal del universo (escala no lineal)", W / 2, 120, 46, anchor="ma")
        return im


class Lensing(CGI):
    def setup(self):
        r = self.rng
        self.bg = starfield(r, n=2500, tint=(30, 30, 70))
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        self.x = (x - W / 2) / (H / 2); self.y = (y - H / 2) / (H / 2)
        self.src = (r.uniform(-0.05, 0.05), r.uniform(-0.05, 0.05))
        self.cl = [(r.normal(0, 0.15), r.normal(0, 0.12), r.uniform(6, 16)) for _ in range(30)]

    def frame(self, t):
        u = ease(t / (self.dur * 0.7))
        thE = 0.03 + 0.3 * u
        th2 = self.x ** 2 + self.y ** 2 + 1e-6
        f = 1 - thE ** 2 / th2
        bx, by = self.x * f - self.src[0], self.y * f - self.src[1]
        gal = np.exp(-((bx / 0.11) ** 2 + (by / 0.07) ** 2))
        img = self.bg + gal[..., None] * np.array([120, 170, 255]) * 2.2
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        for cx, cy, s in self.cl:
            px, py = W / 2 + cx * H / 2, H / 2 + cy * H / 2
            d.ellipse([px - s, py - s * 0.8, px + s, py + s * 0.8], fill=(255, 220, 160, 200))
        label(im, "Lente gravitacional: la masa curva la luz · ilustración", 60, H - 80, 28, (190, 200, 230))
        return im


CGI_SCENES = {
    "blackhole": lambda r, d: BlackHole(r, d, 0), "blackhole2": lambda r, d: BlackHole(r, d, 1),
    "galaxy": Galaxy, "warp": Warp, "planet_europa": PlanetEuropa, "planet_titan": PlanetTitan, "planet_earth": PlanetEarth,
    "saturn_view": SaturnView, "jupiter_view": JupiterView, "magnetar": Magnetar, "rotation_curve": RotationCurve,
    "pie": Pie, "expansion": Expansion, "frb": FRB, "radio_dish": RadioDish, "gw": GW, "hubble_chart": HubbleChart,
    "cmb": CMBSphere, "bigbang": BigBang, "multiverse": Multiverse, "ghost_galaxy": GhostGalaxy, "collision": Collision,
    "europa_cut": EuropaCut, "titan_lake": TitanLake, "deep_zoom": DeepZoom, "timeline": Timeline, "lensing": Lensing,
}
