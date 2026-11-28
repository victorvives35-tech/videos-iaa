# -*- coding: utf-8 -*-
"""Escenas procedurales animadas: recreaciones visuales ORIGINALES inspiradas en un
estado tropical ficticio. No usan material de Rockstar ni representan personajes reales."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from fx import *


class Scene:
    variants = ["sunset"]

    def __init__(self, rng, variant, dur):
        self.rng, self.v, self.dur = rng, variant, dur
        self.events = []
        self.setup()

    def setup(self):
        pass

    def frame(self, t, pan):
        raise NotImplementedError


# =====================================================================  SKYLINE
class Skyline(Scene):
    variants = ["sunset", "night", "dusk"]

    def setup(self):
        r = self.rng
        self.hy = int(H * r.uniform(0.58, 0.66))
        self.sky = vgrad(W + 800, self.hy, SKIES[self.v])
        night = self.v == "night"
        wins = [(255, 220, 150), (255, 240, 200), (120, 220, 255), (255, 150, 220)]
        far_c = (40, 25, 70) if night else (90, 40, 90)
        mid_c = (18, 12, 36) if night else (50, 22, 60)
        self.far = city_layer(W + 900, self.hy + 2, self.hy, r, 40, 170, far_c, wins, 0.25 if night else 0.08, 0.05)
        self.mid = city_layer(W + 1200, self.hy + 2, self.hy, r, 90, int(self.hy * 0.8), mid_c, wins,
                              0.45 if night else 0.18, 0.35 if self.v != "day" else 0.1, 0.45)
        if night or self.v == "dusk":
            self.mid = glowify(self.mid, 3, 1.2)
        self.sun = (r.uniform(0.3, 0.7) * W, self.hy - r.uniform(40, 150), r.uniform(70, 120))
        self.palms = [(r.uniform(-100, W + 500), r.uniform(220, 420), r.uniform(-0.3, 0.3)) for _ in range(5)]
        self.cars = [(r.uniform(0, W), r.uniform(80, 220) * r.choice([-1, 1]), r.choice([0, 1])) for _ in range(14)]
        self.heli = r.random() < 0.6
        self.stars = [(r.uniform(0, W), r.uniform(0, self.hy * 0.6), r.uniform(0.5, 1)) for _ in range(90)] if night else []

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky.crop((int(pan * 0.1) % 800, 0, int(pan * 0.1) % 800 + W, self.hy)), (0, 0))
        L = Lights()
        for sx, sy, b in self.stars:
            L.add(sx, sy, 2.5, (255, 255, 255), b * (0.6 + 0.4 * math.sin(t * 3 + sx)))
        sx, sy, sr = self.sun
        if self.v == "night":
            ImageDraw.Draw(img).ellipse([sx - 30, sy - 60, sx + 30, sy], fill=(245, 240, 220, 255))
            L.add(sx, sy - 30, 160, (60, 50, 90), 0.6)
        else:
            draw_sun(img, sx - pan * 0.12, sy, sr, t=t)
            L.add(sx - pan * 0.12, sy, sr * 3.2, (255, 120, 80), 0.35)
        paste(img, layer_crop(self.far, pan * 0.35), 0, 0)
        paste(img, layer_crop(self.mid, pan * 0.6), 0, 0)
        if self.heli:
            hx = (W * 1.1 - (t * 90 + pan * 0.4)) % (W + 200) - 100
            hy = self.hy * 0.3 + math.sin(t) * 6
            ImageDraw.Draw(img).polygon([(hx, hy), (hx + 22, hy - 5), (hx + 40, hy), (hx + 22, hy + 4)], fill=(10, 8, 20, 255))
            if int(t * 3) % 2 == 0:
                L.add(hx + 20, hy + 6, 10, (255, 40, 40), 1.0)
        img = img.convert("RGB")
        img = flip_reflect(img, self.hy, 0.55, t, 5, (40, 20, 60))
        d = ImageDraw.Draw(img)
        for cx0, sp, col in self.cars:
            x = (cx0 + sp * t - pan * 0.8) % (W + 100) - 50
            c = (255, 60, 50) if col else (255, 240, 200)
            L.add(x, self.hy + 3, 7, c, 0.9)
        sx2 = sx - pan * 0.12
        for k in range(26):
            yy = self.hy + 8 + k * k * 0.45
            if yy > H: break
            wv = 14 + k * 4 + 8 * math.sin(t * 2 + k)
            col = (255, 190, 120) if self.v != "night" else (220, 220, 255)
            d.line([(sx2 - wv + math.sin(k + t * 3) * 10, yy), (sx2 + wv + math.sin(k + t * 3) * 10, yy)], fill=col, width=2)
        base = H + 10
        for px, ph, lean in self.palms:
            x = (px - pan * 1.25) % (W + 600) - 200
            draw_palm(d, x, base, ph, lean, math.sin(t * 1.3 + px) * 1.0, (8, 5, 14))
        return L.apply(img)


# =====================================================================  HIGHWAY
class Highway(Scene):
    variants = ["sunset", "night", "dusk", "day"]

    def setup(self):
        r = self.rng
        self.vy = int(H * 0.46)
        self.sky = vgrad(W, self.vy, SKIES[self.v])
        night = self.v in ("night", "dusk")
        self.night = night
        wins = [(255, 220, 150), (120, 220, 255), (255, 120, 210)]
        self.city = city_layer(W + 600, self.vy + 1, self.vy, r, 20, 120, (30, 18, 50) if night else (80, 70, 110), wins,
                               0.4 if night else 0.05, 0.2)
        self.speed = r.uniform(28, 45)
        self.cars = [(r.choice([0.8, 2.4]), r.uniform(6, 40), r.uniform(-2, 2), CLOTHES[r.integers(len(CLOTHES))]) for _ in range(5)]
        self.onc = [(r.choice([-2.4, -4.0]), r.uniform(0, 60)) for _ in range(6)]
        self.palm_side = r.random() < 0.75

    def proj(self, X, Z, vx):
        k = 420.0
        return vx + X * k / Z, self.vy + 1.6 * k / Z

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky, (0, 0))
        vx = W / 2 + math.sin(t * 0.4) * 60 + pan * 0.15
        L = Lights()
        if not self.night:
            draw_sun(img, vx + 180, self.vy - 70, 75, t=t)
        paste(img, layer_crop(self.city, pan * 0.2 + t * 4), 0, 0)
        d = ImageDraw.Draw(img)
        ground = (20, 16, 30) if self.night else (70, 90, 60)
        d.rectangle([0, self.vy, W, H], fill=ground + (255,))
        x0, y0 = self.proj(-7, 1.0, vx); x1, _ = self.proj(7, 1.0, vx)
        d.polygon([(vx - 3, self.vy), (vx + 3, self.vy), (x1 + 900, H * 1.6), (x0 - 900, H * 1.6)], fill=(36, 34, 44, 255))
        off = (t * self.speed) % 6
        for X in (-2.6, 0, 2.6):
            for i in range(30):
                z0 = 1.0 + i * 6 - off
                if z0 < 0.6: continue
                a = self.proj(X, z0, vx); b = self.proj(X, z0 + 2.6, vx)
                w = max(1, int(14 / z0))
                d.line([a, b], fill=(240, 230, 200, 255), width=w)
        for X in (-5.8, 5.8):
            a = self.proj(X, 0.5, vx); b = (vx, self.vy)
            d.line([a, b], fill=(250, 200, 80, 255), width=3)
        # postes / palmeras laterales
        spacing = 10
        off2 = (t * self.speed) % spacing
        items = []
        for i in range(14):
            z = 0.9 + i * spacing - off2
            if z < 0.7: continue
            for s in (-1, 1):
                items.append((z, s))
        for z, s in sorted(items, reverse=True):
            px, py = self.proj(s * 9.5, z, vx)
            hh = 3000 / z
            if self.palm_side:
                draw_palm(d, px, py, min(hh, 900), -s * 0.15, math.sin(t + z) * 0.7, (12, 8, 18, 255), leaflets=hh > 120)
            else:
                d.line([(px, py), (px, py - hh * 0.8)], fill=(30, 30, 40, 255), width=max(1, int(60 / z)))
                L.add(px - s * hh * 0.1, py - hh * 0.8, max(3, 400 / z), (255, 200, 120), 0.9)
        # coches delante
        for lane, z0, dz, col in self.cars:
            z = 6 + (z0 + dz * t) % 40
            cx, cy = self.proj(lane, z, vx)
            cw = 2200 / z; ch = cw * 0.5
            d.rectangle([cx - cw / 2, cy - ch, cx + cw / 2, cy], fill=mix(col, (10, 10, 10), 0.55) + (255,))
            d.rectangle([cx - cw / 2.4, cy - ch * 1.45, cx + cw / 2.4, cy - ch], fill=(15, 15, 20, 255))
            for s in (-1, 1):
                L.add(cx + s * cw * 0.38, cy - ch * 0.55, max(3, cw * 0.18), (255, 40, 40), 1.0)
        for lane, z0 in self.onc:
            z = 60 - (z0 + t * self.speed * 2.2) % 60 + 1
            cx, cy = self.proj(lane, z, vx)
            for s in (-1, 1):
                L.add(cx + s * 900 / z, cy - 300 / z, max(3, 1600 / z), (255, 245, 220), 1.0)
        img = img.convert("RGB")
        if self.night:
            L.add(vx, self.vy, 260, (120, 40, 140), 0.35)
        return L.apply(img)


# =====================================================================  BEACH
class Beach(Scene):
    variants = ["day", "day", "sunset"]

    def setup(self):
        r = self.rng
        self.hy = int(H * 0.40)
        self.shore = int(H * 0.60)
        self.sky = vgrad(W, self.hy, SKIES[self.v])
        sea_top = (30, 150, 200) if self.v == "day" else (120, 80, 140)
        sea_bot = (60, 220, 215) if self.v == "day" else (240, 150, 120)
        self.sea = vgrad(W, self.shore - self.hy + 30, [(0, sea_top), (1, sea_bot)])
        sand1 = (245, 225, 180) if self.v == "day" else (230, 170, 130)
        self.sand = vgrad(W, H - self.shore, [(0, sand1), (1, mix(sand1, (180, 140, 100), 0.4))])
        self.hotels = city_layer(W + 1000, self.hy + 1, self.hy, r, 40, 200, (240, 230, 220), [(120, 180, 210)],
                                 0.3, 0.0, 0.6, (50, 110), pastel=True)
        self.spark = [(r.uniform(0, W), r.uniform(self.hy, self.shore), r.uniform(0, 6)) for _ in range(160)]
        self.people = []
        for _ in range(int(r.integers(80, 140))):
            y = r.uniform(self.shore + 15, H + 60)
            p = random_person(r)
            p.update(x=r.uniform(-200, W + 900), y=y, h=(y - self.shore) * 0.55 + 18,
                     walk=1.0 if r.random() < 0.35 else 0.0, sp=r.uniform(-40, 40), ph=r.uniform(0, 6),
                     arms=1.0 if r.random() < 0.08 else 0.0)
            self.people.append(p)
        self.people.sort(key=lambda p: p["y"])
        self.umb = [(r.uniform(-200, W + 900), r.uniform(self.shore + 20, H), CLOTHES[r.integers(len(CLOTHES))]) for _ in range(14)]
        self.umb.sort(key=lambda u: u[1])
        self.palms = [(r.uniform(0, W + 600), r.uniform(300, 520)) for _ in range(3)]

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky, (0, 0))
        L = Lights()
        if self.v == "sunset":
            draw_sun(img, W * 0.62 - pan * 0.1, self.hy - 50, 70, stripes=False)
        else:
            L.add(W * 0.8, 60, 220, (255, 255, 230), 0.5)
        paste(img, layer_crop(self.hotels, pan * 0.4), 0, 0)
        img.paste(self.sea, (0, self.hy))
        d = ImageDraw.Draw(img)
        for sx, sy, ph in self.spark:
            b = max(0, math.sin(t * 4 + ph * 3))
            if b > 0.6:
                L.add((sx - pan * 0.5) % W, sy, 3 + (sy - self.hy) * 0.03, (255, 255, 255), b)
        img.paste(self.sand, (0, self.shore))
        for k in range(4):
            ph = t * 0.6 + k * 1.57
            yy = self.shore + 6 * math.sin(ph) - k * 9
            pts = [(x, yy + 3 * math.sin(x * 0.02 + t * 1.5 + k)) for x in range(-20, W + 40, 40)]
            d.line(pts, fill=(255, 255, 255, 220 - k * 40), width=5 - k)
        d.polygon([(0, self.shore + 8 * math.sin(t * 0.6)), (W, self.shore + 8 * math.sin(t * 0.6)), (W, self.shore + 14), (0, self.shore + 14)],
                  fill=(210, 230, 220, 160))
        span = W + 1100
        items = [("u", u[1], u) for u in self.umb] + [("p", p["y"], p) for p in self.people]
        items.sort(key=lambda i: i[1])
        for kind, y, o in items:
            if kind == "u":
                x = (o[0] - pan * (0.6 + (y - self.shore) / H)) % span - 200
                s = (y - self.shore) * 0.5 + 20
                d.line([(x, y), (x, y - s * 1.3)], fill=(240, 240, 240), width=max(1, int(s * 0.05)))
                d.pieslice([x - s, y - s * 1.6, x + s, y - s * 0.9], 180, 360, fill=o[2])
                d.ellipse([x - s * 0.9, y - 3, x + s * 0.9, y + s * 0.12], fill=(200, 175, 135))
            else:
                p = o
                x = (p["x"] + p["sp"] * t * p["walk"] - pan * (0.6 + (y - self.shore) / H)) % span - 200
                bob = 0 if p["walk"] else math.sin(t * 2 + p["ph"]) * 1.5
                draw_person(d, x, y + bob, p["h"], p["shirt"], p["pants"], p["skin"], t * 7 + p["ph"], p["walk"],
                            p["long_hair"], p["hair"], p["arms"] * (0.7 + 0.3 * math.sin(t * 6)), facing=1 if p["sp"] > 0 else -1)
        for px, ph in self.palms:
            x = (px - pan * 1.4) % (W + 700) - 250
            draw_palm(d, x, H + 20, ph, 0.25, math.sin(t * 1.1 + px) * 1.2, (40, 60, 30) if self.v == "day" else (20, 10, 20))
        return L.apply(img.convert("RGB"))


# =====================================================================  AERIAL
class Aerial(Scene):
    variants = ["day", "night", "sunset"]
    M = 2400

    def setup(self):
        r = self.rng
        M = self.M
        night = self.v == "night"
        self.night = night
        base = (60, 62, 70) if not night else (14, 14, 22)
        img = Image.new("RGB", (M, M), base)
        d = ImageDraw.Draw(img)
        blk, road = int(r.integers(150, 220)), int(r.integers(34, 46))
        self.blk, self.road = blk, road
        coast = int(M * r.uniform(0.62, 0.75))
        self.coast = coast
        sea = (30, 140, 190) if not night else (8, 18, 40)
        d.rectangle([coast, 0, M, M], fill=sea)
        d.rectangle([coast - 60, 0, coast + 10, M], fill=(235, 215, 170) if not night else (40, 36, 40))
        roof = [(200, 200, 205), (230, 225, 215), (160, 165, 175), (210, 190, 170), (180, 200, 210)] if not night else \
            [(30, 30, 40), (24, 24, 34), (36, 32, 44)]
        winl = [(255, 210, 140), (255, 240, 200), (130, 220, 255)]
        for by in range(0, M, blk + road):
            for bx in range(0, coast - 80, blk + road):
                if r.random() < 0.12:
                    d.rectangle([bx, by, bx + blk, by + blk], fill=(70, 130, 70) if not night else (10, 22, 14))
                    for _ in range(14):
                        tx, ty = bx + r.uniform(10, blk - 10), by + r.uniform(10, blk - 10)
                        rr = r.uniform(6, 14)
                        d.ellipse([tx - rr, ty - rr, tx + rr, ty + rr], fill=(40, 100, 45) if not night else (8, 18, 10))
                    continue
                n = int(r.integers(1, 5))
                for k in range(n):
                    w_ = r.uniform(blk * 0.3, blk * 0.95); h_ = r.uniform(blk * 0.3, blk * 0.95)
                    x_ = bx + r.uniform(0, blk - w_); y_ = by + r.uniform(0, blk - h_)
                    hgt = r.uniform(4, 28)
                    d.rectangle([x_ + hgt, y_ + hgt, x_ + w_ + hgt, y_ + h_ + hgt], fill=mix(base, (0, 0, 0), 0.5))
                    c = roof[r.integers(len(roof))]
                    d.rectangle([x_, y_, x_ + w_, y_ + h_], fill=c)
                    d.rectangle([x_ + 4, y_ + 4, x_ + w_ - 4, y_ + h_ - 4], outline=mix(c, (0, 0, 0), 0.15), width=2)
                    if r.random() < 0.15 and not night:
                        d.rounded_rectangle([x_ + w_ * 0.2, y_ + h_ * 0.2, x_ + w_ * 0.55, y_ + h_ * 0.45], 6, fill=(60, 200, 230))
                    if night:
                        for _ in range(int(w_ * h_ / 300)):
                            wx, wy = x_ + r.uniform(2, w_ - 2), y_ + r.uniform(2, h_ - 2)
                            if r.random() < 0.5:
                                d.rectangle([wx, wy, wx + 2, wy + 2], fill=winl[r.integers(3)])
        # carreteras
        rc = (40, 40, 46) if not night else (22, 22, 30)
        for p in range(blk, M, blk + road):
            d.rectangle([0, p, coast - 60, p + road], fill=rc)
            if p < coast - 60:
                d.rectangle([p, 0, p + road, M], fill=rc)
            for q in range(0, M, 30):
                d.line([(q, p + road // 2), (q + 14, p + road // 2)], fill=(230, 220, 160), width=2)
                if p < coast - 60:
                    d.line([(p + road // 2, q), (p + road // 2, q + 14)], fill=(230, 220, 160), width=2)
        # olas en la costa
        for k in range(40):
            yy = r.uniform(0, M)
            d.line([(coast + 20 + r.uniform(0, 40), yy), (coast + 70 + r.uniform(0, 80), yy + 6)], fill=(220, 240, 250) if not night else (40, 60, 90), width=2)
        if self.v == "sunset":
            arr = np.asarray(img, np.float32) * np.array([1.1, 0.85, 0.8]) + np.array([30, 0, 10])
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        self.map = img
        self.cars = []
        lanes = list(range(blk, coast - 120, blk + road))
        for _ in range(110):
            p = lanes[r.integers(len(lanes))]
            hor = r.random() < 0.5
            side = r.choice([-1, 1])
            self.cars.append((hor, p + road / 2 + side * road / 4, r.uniform(0, M), side * r.uniform(60, 140),
                              CLOTHES[r.integers(len(CLOTHES))]))
        self.c0 = np.array([r.uniform(700, coast - 200), r.uniform(700, M - 700)])
        self.rot0 = r.uniform(0, 360); self.drot = r.uniform(-8, 8)
        self.z0 = r.uniform(0.85, 1.2); self.z1 = self.z0 * r.uniform(1.0, 1.35)
        self.clouds = [(r.uniform(0, W), r.uniform(0, H), r.uniform(120, 260)) for _ in range(5)]
        self.follow = None

    def frame(self, t, pan):
        u = t / self.dur
        z = lerp(self.z0, self.z1, ease(u))
        ang = math.radians(self.rot0 + self.drot * t)
        c = self.c0 + np.array([pan * 0.8, t * 20])
        if self.follow is not None:
            c = np.array(self.follow(t))
        ca, sa = math.cos(ang), math.sin(ang)
        # pantalla -> mapa: m = c + R*(s - center)/z
        a, b = ca / z, -sa / z
        dd, e = sa / z, ca / z
        cx, cy = W / 2, H / 2
        coeffs = (a, b, c[0] - a * cx - b * cy, dd, e, c[1] - dd * cx - e * cy)
        img = self.map.transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)
        d = ImageDraw.Draw(img)
        L = Lights()

        def to_scr(mx, my):
            vx, vy = mx - c[0], my - c[1]
            sx = (ca * vx + sa * vy) * z + cx
            sy = (-sa * vx + ca * vy) * z + cy
            return sx, sy
        M = self.M
        for hor, lane, p0, sp, col in self.cars:
            p = (p0 + sp * t) % M
            mx, my = (p, lane) if hor else (lane, p)
            sx, sy = to_scr(mx, my)
            if -20 < sx < W + 20 and -20 < sy < H + 20:
                s = 7 * z
                d.ellipse([sx - s, sy - s, sx + s, sy + s], fill=col if not self.night else (40, 40, 50))
                if self.night:
                    L.add(sx, sy, 10 * z, (255, 230, 180) if sp > 0 else (255, 50, 40), 0.9)
        img = img.convert("RGB")
        if not self.night:
            arr = np.asarray(img, np.float32)
            for (x0, y0, rr) in self.clouds:
                x = (x0 + t * 25) % (W + 400) - 200
                L.add(x, y0, rr, (255, 255, 255), 0.25, 1.5)
        return L.apply(img)


# =====================================================================  OCEAN
class Ocean(Scene):
    variants = ["day", "sunset", "dusk"]

    def setup(self):
        r = self.rng
        self.hy = int(H * r.uniform(0.38, 0.48))
        self.sky = vgrad(W, self.hy, SKIES[self.v])
        top = (20, 90, 150) if self.v == "day" else (70, 40, 100)
        bot = (20, 160, 190) if self.v == "day" else (200, 100, 110)
        self.base = vgrad_arr(W, H - self.hy, [(0, top), (1, bot)])
        self.isl = city_layer(W + 800, self.hy + 1, self.hy, r, 6, 60, (40, 60, 60) if self.v == "day" else (40, 20, 50),
                              [(255, 220, 150)], 0.1 if self.v != "day" else 0, 0.0, 0.2)
        yy = np.arange(H - self.hy)[:, None].astype(np.float32)
        self.depth = (yy + 8) / (H - self.hy)
        self.xx = np.arange(W)[None, :].astype(np.float32)
        self.boat_col = CLOTHES[r.integers(len(CLOTHES))]
        self.dir = r.choice([-1, 1])
        self.gulls = [(r.uniform(0, W), r.uniform(40, self.hy - 20), r.uniform(0, 6)) for _ in range(6)]

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky, (0, 0))
        if self.v != "day":
            draw_sun(img, W * 0.3, self.hy - 60, 80, t=t)
        paste(img, layer_crop(self.isl, pan * 0.3 + t * 10 * self.dir), 0, 0)
        dp = self.depth
        f = 0.05 / dp
        w1 = np.sin(self.xx * 0.012 / dp + t * 1.8 + dp * 40) * np.sin(self.xx * 0.004 / dp - t * 1.1 + dp * 25)
        hl = np.clip(w1, 0, 1) ** 3 * 70 * (0.3 + dp)
        sea = self.base + hl[..., None] * np.array([1, 1, 1.0])
        img = img.convert("RGB")
        arr = np.asarray(img).copy()
        arr[self.hy:] = np.clip(sea, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        d = ImageDraw.Draw(img)
        L = Lights()
        bx = W * 0.5 + math.sin(t * 0.5) * 60 * self.dir
        by = H * 0.72 + math.sin(t * 2.2) * 5
        Lb = 300
        s = self.dir
        # estela
        for k in range(16):
            ww = 10 + k * 26
            yy = by + 8 + k * 2.2
            xx = bx - s * (Lb * 0.5 + k * 34)
            d.ellipse([xx - ww * 0.7, yy - 6 - k, xx + ww * 0.7, yy + 6 + k], fill=(235, 245, 250))
        hull = [(bx - s * Lb / 2, by - 20), (bx + s * Lb / 2, by - 26), (bx + s * Lb * 0.35, by + 12), (bx - s * Lb / 2, by + 10)]
        d.polygon(hull, fill=(245, 245, 245))
        d.polygon([(bx - s * Lb / 2, by - 2), (bx + s * Lb * 0.45, by - 10), (bx + s * Lb * 0.38, by + 2), (bx - s * Lb / 2, by + 6)],
                  fill=self.boat_col)
        d.polygon([(bx - s * Lb * 0.15, by - 22), (bx + s * Lb * 0.05, by - 46), (bx + s * Lb * 0.12, by - 24)], fill=(30, 40, 60))
        for k in range(20):
            a = (t * 9 + k * 0.7) % 1.0
            px = bx + s * Lb * 0.3 - s * a * 140 + math.sin(k * 7) * 30
            py = by - 10 - math.sin(a * 3.14) * 40
            L.add(px, py, 6, (255, 255, 255), 1 - a)
        for gx, gy, ph in self.gulls:
            x = (gx + t * 60) % (W + 100) - 50
            fl = math.sin(t * 8 + ph) * 8
            d.line([(x - 14, gy - fl), (x, gy), (x + 14, gy - fl)], fill=(30, 30, 40), width=3)
        return L.apply(img)


# =====================================================================  SWAMP
class Swamp(Scene):
    variants = ["dusk", "dawn", "night", "sunset"]

    def setup(self):
        r = self.rng
        self.hy = int(H * r.uniform(0.5, 0.58))
        self.sky = vgrad(W, self.hy, SKIES[self.v])
        tree_c = (16, 22, 18) if self.v != "dawn" else (50, 60, 60)
        self.trees = Image.new("RGBA", (W + 900, self.hy + 1))
        d = ImageDraw.Draw(self.trees)
        x = 0
        while x < W + 900:
            h = r.uniform(60, 230)
            w = r.uniform(30, 90)
            d.rectangle([x - 4, self.hy - h, x + 4, self.hy], fill=tree_c + (255,))
            for k in range(6):
                yy = self.hy - h + k * h * 0.12
                ww = w * (0.4 + k * 0.12)
                d.ellipse([x - ww, yy - 14, x + ww, yy + 14], fill=tree_c + (255,))
                for m in range(int(ww / 8)):
                    mx = x - ww + m * 16 + r.uniform(-4, 4)
                    d.line([(mx, yy), (mx, yy + r.uniform(10, 50))], fill=tree_c + (255,), width=2)
            x += r.uniform(25, 90)
        d.rectangle([0, self.hy - 30, W + 900, self.hy], fill=tree_c + (255,))
        self.fog = vgrad(W, 120, [(0, (255, 255, 255)), (1, (255, 255, 255))], "RGBA")
        fa = np.zeros((120, W), np.uint8) + (np.sin(np.linspace(0, np.pi, 120)) * 70).astype(np.uint8)[:, None]
        self.fog.putalpha(Image.fromarray(fa))
        self.reeds = [(r.uniform(0, W + 400), r.uniform(60, 220), r.uniform(-0.3, 0.3), r.uniform(0, 6)) for _ in range(160)]
        self.birds = [(r.uniform(-200, W), r.uniform(40, self.hy - 60), r.uniform(0, 6), r.choice([0, 1])) for _ in range(5)]
        self.gator_y = H * r.uniform(0.7, 0.8)
        self.gdir = r.choice([-1, 1])
        self.flies = [(r.uniform(0, W), r.uniform(self.hy - 100, H), r.uniform(0, 6)) for _ in range(50)] if self.v == "night" else []
        self.pads = [(r.uniform(0, W + 400), r.uniform(self.hy + 20, H)) for _ in range(30)]

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky, (0, 0))
        L = Lights()
        if self.v == "night":
            ImageDraw.Draw(img).ellipse([W * 0.7 - 28, 70, W * 0.7 + 28, 126], fill=(240, 240, 220, 255))
        else:
            draw_sun(img, W * 0.35, self.hy - 40, 60, stripes=False)
            L.add(W * 0.35, self.hy - 40, 260, (255, 140, 60), 0.3)
        paste(img, layer_crop(self.trees, pan * 0.4), 0, 1)
        paste(img, self.fog, int(math.sin(t * 0.2) * 30), self.hy - 90)
        img = flip_reflect(img.convert("RGB"), self.hy, 0.6, t * 0.5, 2.5, (20, 40, 30))
        d = ImageDraw.Draw(img)
        for px, py in self.pads:
            x = (px - pan * (0.5 + py / H)) % (W + 400) - 100
            s = (py - self.hy) * 0.1 + 3
            d.ellipse([x - s * 2, py - s * 0.6, x + s * 2, py + s * 0.6], fill=(40, 90, 40))
        gx = W * 0.5 + self.gdir * (t * 30 - self.dur * 15) - pan * 0.6
        gy = self.gator_y
        g = self.gdir
        for k in range(5):
            rr = 30 + k * 38 + (t * 25) % 38
            d.arc([gx - g * rr * 1.3 - rr * 1.5, gy - rr * 0.18, gx - g * rr * 1.3 + rr * 1.5, gy + rr * 0.25], 0, 180,
                  fill=(150, 160, 140), width=2)
        d.polygon([(gx - g * 120, gy + 2), (gx - g * 40, gy - 9), (gx + g * 40, gy - 8), (gx + g * 90, gy - 3), (gx + g * 95, gy + 4), (gx - g * 120, gy + 6)],
                  fill=(30, 40, 25))
        for k in range(7):
            sx = gx - g * (110 - k * 14)
            d.polygon([(sx, gy - 2), (sx + 5, gy - 9), (sx + 10, gy - 2)], fill=(25, 35, 20))
        for s in (0, 1):
            ex = gx + g * (38 + s * 10)
            d.ellipse([ex - 6, gy - 16, ex + 6, gy - 6], fill=(40, 50, 30))
            L.add(ex, gy - 11, 4, (255, 200, 60), 0.8 if self.v == "night" else 0.4)
        for bx, by, ph, kind in self.birds:
            x = (bx + t * 70) % (W + 300) - 150
            fl = math.sin(t * 6 + ph) * 12
            col = (250, 250, 250) if kind == 0 else (250, 120, 160)
            d.line([(x - 24, by - fl), (x, by), (x + 24, by - fl)], fill=col, width=4)
            d.line([(x, by), (x + 18, by + 4)], fill=col, width=3)
        for rx, rh, lean, ph in self.reeds:
            x = (rx - pan * 1.3) % (W + 400) - 100
            sw = math.sin(t * 1.5 + ph) * 10
            d.line([(x, H + 5), (x + lean * rh + sw, H - rh)], fill=(30, 50, 25) if self.v != "night" else (10, 18, 10), width=3)
        for fx_, fy, ph in self.flies:
            L.add(fx_ + math.sin(t + ph) * 20, fy + math.cos(t * 0.7 + ph) * 15, 6, (220, 255, 120), max(0, math.sin(t * 2 + ph)))
        return L.apply(img)


# =====================================================================  RAIN STREET
SIGNS = ["MOTEL", "24H", "TACOS", "BAR", "DINER", "CLUB", "LIQUOR", "PALM INN", "COCKTAILS", "OPEN", "NOODLES",
         "PAWN", "PIZZA", "TATTOO", "HOTEL", "CAFÉ", "SUSHI", "ARCADE"]
NEON = [(255, 60, 170), (60, 230, 255), (255, 150, 40), (170, 90, 255), (80, 255, 140), (255, 70, 70)]


def facade_layer(rng, w, base, night=True, day_cols=None):
    img = Image.new("RGBA", (w, base + 1))
    d = ImageDraw.Draw(img)
    x = 0
    signs = []
    while x < w:
        bw = int(rng.integers(160, 320))
        bh = int(rng.integers(int(base * 0.55), base))
        col = jitter((40, 32, 56), rng, 12) if night else (day_cols or PASTELS)[rng.integers(len(day_cols or PASTELS))]
        d.rectangle([x, base - bh, x + bw, base], fill=col + (255,))
        d.rectangle([x, base - bh, x + bw, base - bh + 8], fill=mix(col, (255, 255, 255), 0.2) + (255,))
        sh_top = base - 120
        glass = (255, 210, 150) if night else (150, 190, 210)
        d.rectangle([x + 14, sh_top, x + bw - 14, base - 6], fill=mix(glass, (0, 0, 0), 0.45 if night else 0.1) + (255,))
        for ry in range(sh_top + 18, base - 10, 22):
            d.line([(x + 18, ry), (x + bw - 18, ry)], fill=(80, 60, 50, 255), width=2)
            for px in range(x + 20, x + bw - 22, 9):
                if rng.random() < 0.8:
                    d.rectangle([px, ry - 12, px + 6, ry - 1], fill=CLOTHES[rng.integers(len(CLOTHES))] + (255,))
        if not night:
            ac = CLOTHES[rng.integers(len(CLOTHES))]
            for k in range(0, bw - 10, 24):
                d.polygon([(x + 6 + k, sh_top - 34), (x + 30 + k, sh_top - 34), (x + 34 + k, sh_top - 4), (x + 2 + k, sh_top - 4)],
                          fill=(ac if (k // 24) % 2 == 0 else (250, 250, 250)) + (255,))
        for yy in range(base - bh + 24, sh_top - 50, 40):
            for xx in range(x + 18, x + bw - 30, 36):
                lit = rng.random() < (0.5 if night else 0.0)
                d.rectangle([xx, yy, xx + 20, yy + 24], fill=((255, 210, 140) if lit else mix(col, (0, 0, 0), 0.4)) + (255,))
        txt = SIGNS[rng.integers(len(SIGNS))]
        signs.append((x + bw // 2, sh_top - 60 if night else sh_top - 56, txt, NEON[rng.integers(len(NEON))], rng.uniform(0, 6)))
        x += bw
    return img, signs


def sign_sprite(txt, col, size=46, night=True):
    f = font("Anton-Regular.ttf", size)
    bb = f.getbbox(txt)
    w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    if night:
        d.text((20 - bb[0], 20 - bb[1]), txt, font=f, fill=col + (255,))
        g = glowify(im, 8, 2.5)
        d2 = ImageDraw.Draw(g)
        d2.text((20 - bb[0], 20 - bb[1]), txt, font=f, fill=mix(col, (255, 255, 255), 0.6) + (255,))
        return g
    d.rounded_rectangle([8, 8, w - 8, h - 8], 8, fill=(250, 250, 245, 255), outline=col + (255,), width=4)
    d.text((20 - bb[0], 20 - bb[1]), txt, font=f, fill=col + (255,))
    return im


class RainStreet(Scene):
    variants = ["night"]

    def setup(self):
        r = self.rng
        self.base = int(H * 0.60)
        self.sky = vgrad(W, self.base, SKIES["night"])
        self.fac, signs = facade_layer(r, W + 1400, self.base, True)
        self.signs = [(x, y, sign_sprite(t, c, int(r.integers(34, 54))), ph) for x, y, t, c, ph in signs]
        rain = np.zeros((H * 2, W), np.uint8)
        for _ in range(2600):
            x, y = r.integers(0, W), r.integers(0, H * 2 - 40)
            ln = r.integers(12, 34)
            rain[y:y + ln, x] = r.integers(60, 160)
        self.rain = Image.fromarray(rain).filter(ImageFilter.GaussianBlur(0.6))
        self.people = []
        for _ in range(9):
            p = random_person(r)
            p.update(x=r.uniform(0, W + 1400), sp=r.choice([-1, 1]) * r.uniform(40, 70), ph=r.uniform(0, 6),
                     umb=NEON[r.integers(len(NEON))] if r.random() < 0.7 else None, h=r.uniform(120, 150))
            self.people.append(p)
        self.cars = [(r.uniform(0, W * 2), r.choice([-1, 1]) * r.uniform(300, 520), CLOTHES[r.integers(len(CLOTHES))], int(r.integers(0, 2))) for _ in range(2)]

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky, (0, 0))
        off = pan * 0.9 + t * 15
        paste(img, layer_crop(self.fac, off), 0, 0)
        lw = self.fac.size[0]
        for x, y, spr, ph in self.signs:
            sx = (x - off) % lw
            if sx > W + 200: sx -= lw
            on = not (math.sin(t * 9 + ph * 5) > 0.93)
            if on and -300 < sx < W + 300:
                paste(img, spr, sx - spr.size[0] / 2, y - spr.size[1] / 2)
        d = ImageDraw.Draw(img)
        d.rectangle([0, self.base, W, self.base + 26], fill=(50, 46, 60, 255))
        for p in self.people:
            x = (p["x"] + p["sp"] * t - off) % lw
            if x > W + 200: x -= lw
            draw_person(d, x, self.base + 20, p["h"], mix(p["shirt"], (0, 0, 0), 0.5), (30, 30, 40), mix(p["skin"], (0, 0, 0), 0.4),
                        t * 6 + p["ph"], 1.0, p["long_hair"], p["hair"], umbrella=p["umb"], facing=1 if p["sp"] > 0 else -1)
        img = img.convert("RGB")
        img = flip_reflect(img, self.base + 26, 0.62, t, 3.0, (20, 10, 40))
        arr = np.asarray(img, np.float32).copy()
        lo = arr[self.base + 26:]
        lo = (lo + np.roll(lo, 6, 0) + np.roll(lo, 14, 0)) / 3
        arr[self.base + 26:] = lo
        img = Image.fromarray(arr.astype(np.uint8))
        d = ImageDraw.Draw(img)
        L = Lights()
        for cx0, sp, col, st in self.cars:
            x = (cx0 + sp * t) % (W * 2.4) - W * 0.7
            yb = H - 40
            Lc = 520
            draw_car_side(d, x, yb, Lc, mix(col, (0, 0, 0), 0.5), wheel_ang=t * sp / 40, style=st)
            front = x + Lc if sp > 0 else x
            back = x if sp > 0 else x + Lc
            L.add(front, yb - 70, 90, (255, 245, 210), 1.0)
            L.add(front + (1 if sp > 0 else -1) * 200, yb - 40, 230, (200, 200, 180), 0.35)
            L.add(back, yb - 75, 40, (255, 30, 30), 1.0)
        img = L.apply(img)
        ry = int(t * 900) % H
        rain = self.rain.crop((0, H - ry, W, 2 * H - ry))
        img = Image.composite(Image.new("RGB", (W, H), (200, 210, 255)), img, rain)
        return img


# =====================================================================  POLICE
class Police(Highway):
    variants = ["night", "night", "dusk"]

    def setup(self):
        super().setup()
        self.night = True
        self.speed = self.rng.uniform(50, 70)
        self.heli_ph = self.rng.uniform(0, 6)

    def frame(self, t, pan):
        img = super().frame(t, pan)
        d = ImageDraw.Draw(img)
        L = Lights()
        cx = W / 2 + math.sin(t * 0.9) * 80
        cy = H - 40
        cw = 520
        d.polygon([(cx - cw / 2, cy), (cx - cw / 2 + 20, cy - 110), (cx - cw * 0.3, cy - 150), (cx + cw * 0.3, cy - 150),
                   (cx + cw / 2 - 20, cy - 110), (cx + cw / 2, cy), (cx + cw / 2, cy + 60), (cx - cw / 2, cy + 60)], fill=(12, 12, 18))
        d.polygon([(cx - cw * 0.26, cy - 150), (cx - cw * 0.2, cy - 215), (cx + cw * 0.2, cy - 215), (cx + cw * 0.26, cy - 150)], fill=(20, 22, 30))
        d.rectangle([cx - cw * 0.5, cy - 70, cx + cw * 0.5, cy - 40], fill=(230, 230, 235))
        d.rectangle([cx - cw * 0.18, cy - 228, cx + cw * 0.18, cy - 214], fill=(30, 30, 40))
        ph = int(t * 8) % 2
        red, blue = (255, 30, 40), (40, 80, 255)
        L.add(cx - cw * 0.1, cy - 222, 70, red, 1.0 if ph else 0.15)
        L.add(cx + cw * 0.1, cy - 222, 70, blue, 0.15 if ph else 1.0)
        L.add(cx - cw * 0.1, cy - 222, 500, red, 0.25 if ph else 0.0, 1.5)
        L.add(cx + cw * 0.1, cy - 222, 500, blue, 0.0 if ph else 0.3, 1.5)
        for s in (-1, 1):
            L.add(cx + s * cw * 0.42, cy - 90, 30, (255, 40, 40), 0.9)
        # foco del helicóptero
        hx = W / 2 + math.sin(t * 0.7 + self.heli_ph) * 300
        hy = self.vy + 60
        L.add(hx, hy, 160, (255, 255, 240), 0.55, 1.2)
        img = L.apply(img)
        cone = Image.new("L", (W, H), 0)
        ImageDraw.Draw(cone).polygon([(hx - 40 + W * 0.1, -10), (hx + 40 + W * 0.1, -10), (hx + 150, hy), (hx - 150, hy)], fill=40)
        cone = cone.filter(ImageFilter.GaussianBlur(12))
        img = Image.composite(Image.new("RGB", (W, H), (255, 255, 240)), img, cone)
        return img


class PoliceHeli(Aerial):
    variants = ["night"]

    def setup(self):
        super().setup()
        lanes = list(range(self.blk, self.coast - 120, self.blk + self.road))
        self.lane = lanes[len(lanes) // 2] + self.road / 4
        self.p0 = self.rng.uniform(200, 600)
        self.z0, self.z1 = 1.4, 1.7
        self.follow = lambda t: (self.p0 + 170 * t + 40, self.lane)

    def frame(self, t, pan):
        img = super().frame(t, pan)
        L = Lights()
        L.add(W / 2, H / 2, 210, (255, 255, 230), 0.55, 1.3)
        ph = int(t * 8) % 2
        for k in range(3):
            dx = -120 - k * 90
            sx = W / 2 + dx * math.cos(math.radians(self.rot0 + self.drot * t)) * 1.5
            sy = H / 2 - dx * math.sin(math.radians(self.rot0 + self.drot * t)) * 1.5
            L.add(sx, sy, 34, (255, 30, 40) if (ph + k) % 2 else (40, 80, 255), 1.0)
        L.add(W / 2, H / 2, 14, (255, 240, 200), 1.0)
        return L.apply(img)


# =====================================================================  DUO (siluetas originales)
class Duo(Scene):
    variants = ["walk", "walk", "car", "back"]

    def setup(self):
        r = self.rng
        self.sv = r.choice(["sunset", "dusk"])
        self.hy = int(H * 0.62)
        self.sky = vgrad(W, self.hy, SKIES[self.sv])
        self.city = city_layer(W + 900, self.hy + 1, self.hy, r, 60, 300, (30, 14, 46), [(255, 210, 150), (255, 120, 200)],
                               0.35, 0.3, 0.4)
        self.city = glowify(self.city, 3, 1.2)
        self.palms = [(r.uniform(0, W + 700), r.uniform(380, 560)) for _ in range(4)]
        self.ph = r.uniform(0, 6)

    def silhouette(self, d, x, yf, h, t, female, walk, rim):
        col = (8, 6, 12)
        ph = t * 5.2 + (1.4 if female else 0)
        for dx, c in ((3, rim), (0, col)):
            sw = walk * math.sin(ph) * h * 0.12
            hip = yf - h * 0.48
            sh = yf - h * 0.81
            lw = int(h * 0.07)
            d.line([(x + dx, hip), (x + dx + sw, yf)], fill=c, width=lw)
            d.line([(x + dx, hip), (x + dx - sw, yf)], fill=c, width=lw)
            tw = h * (0.1 if female else 0.13)
            d.polygon([(x + dx - tw, sh), (x + dx + tw, sh), (x + dx + tw * (1.05 if female else 0.85), hip),
                       (x + dx - tw * (1.05 if female else 0.85), hip)], fill=c)
            d.line([(x + dx - tw, sh + 4), (x + dx - tw - sw * 0.5, hip + h * 0.04)], fill=c, width=int(h * 0.045))
            d.line([(x + dx + tw, sh + 4), (x + dx + tw + sw * 0.5, hip + h * 0.04)], fill=c, width=int(h * 0.045))
            hr = h * 0.075
            hy = sh - hr * 1.2
            d.ellipse([x + dx - hr, hy - hr, x + dx + hr, hy + hr], fill=c)
            if female:
                fl = math.sin(t * 3) * hr * 0.4
                d.polygon([(x + dx - hr * 0.2, hy - hr), (x + dx - hr * 1.1, hy - hr * 0.2),
                           (x + dx - hr * 2.4 + fl, sh + h * 0.1), (x + dx - hr * 0.6, sh + h * 0.05)], fill=c)
            else:
                d.chord([x + dx - hr * 1.08, hy - hr * 1.15, x + dx + hr * 1.08, hy + hr * 0.5], 180, 360, fill=c)

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky, (0, 0))
        L = Lights()
        draw_sun(img, W * 0.5 - pan * 0.08, self.hy - 70, 110, t=t)
        L.add(W * 0.5 - pan * 0.08, self.hy - 70, 420, (255, 110, 70), 0.35)
        move = t * 55 if self.v == "walk" else t * 8
        paste(img, layer_crop(self.city, pan * 0.3 + move * 0.3), 0, 0)
        img = flip_reflect(img.convert("RGB"), self.hy, 0.5, t, 4, (40, 10, 50))
        d = ImageDraw.Draw(img)
        rim = (255, 150, 90)
        if self.v == "walk":
            d.rectangle([0, H - 140, W, H], fill=(16, 10, 20))
            for k in range(-1, 14):
                x = (k * 110 - move * 1.6) % (W + 220) - 110
                d.line([(x, H - 140), (x, H - 200)], fill=(16, 10, 20), width=5)
            d.line([(0, H - 200), (W, H - 200)], fill=(16, 10, 20), width=6)
            self.silhouette(d, W * 0.44, H - 120, 330, t, False, 1.0, rim)
            self.silhouette(d, W * 0.56, H - 118, 300, t, True, 1.0, rim)
        elif self.v == "car":
            d.rectangle([0, H - 110, W, H], fill=(14, 10, 18))
            draw_car_side(d, W * 0.18, H - 100, 760, (14, 10, 20), wheel_ang=0, style=0)
            L.add(W * 0.18 + 760, H - 160, 60, (255, 240, 200), 0.9)
            self.silhouette(d, W * 0.72, H - 100, 360, t * 0.0 + 0.3, False, 0.0, rim)
            self.silhouette(d, W * 0.82, H - 100, 330, t * 0.0 + 1.0, True, 0.0, rim)
            fl = math.sin(t * 2.5) * 6
            d.polygon([(W * 0.82 - 10, H - 100 - 330 * 0.88), (W * 0.82 - 50 + fl, H - 100 - 330 * 0.7),
                       (W * 0.82 - 70 + fl * 1.5, H - 100 - 330 * 0.62), (W * 0.82 - 8, H - 100 - 330 * 0.78)], fill=(8, 6, 12))
        else:
            self.silhouette(d, W * 0.40, H + 120, 620, 0.2, False, 0.0, rim)
            self.silhouette(d, W * 0.58, H + 130, 580, 1.1 + math.sin(t) * 0.05, True, 0.0, rim)
        for px, ph in self.palms:
            x = (px - pan * 1.5 - move * 2.2) % (W + 800) - 300
            draw_palm(d, x, H + 30, ph, 0.2, math.sin(t * 1.2 + px) * 1.0, (6, 4, 10))
        return L.apply(img)


# =====================================================================  SHOPS
class Shops(Scene):
    variants = ["day", "dusk", "day"]

    def setup(self):
        r = self.rng
        self.base = int(H * 0.72)
        night = self.v == "dusk"
        self.sky = vgrad(W, self.base, SKIES["dusk" if night else "day"])
        self.fac, signs = facade_layer(r, W + 1600, self.base, night)
        names = ["MINI MART", "DINER", "TACOS", "PHARMACY", "PIZZA", "COFFEE", "SURF SHOP", "LAUNDRY", "BURGERS",
                 "ICE CREAM", "GYM", "BAKERY", "FISH & CHIPS", "JUICE BAR"]
        self.signs = [(x, y, sign_sprite(names[r.integers(len(names))], c, 38, night), ph) for x, y, _, c, ph in signs]
        self.people = []
        for _ in range(int(r.integers(22, 36))):
            p = random_person(r)
            y = r.uniform(self.base + 10, H - 10)
            p.update(x=r.uniform(0, W + 1600), y=y, sp=r.choice([-1, 1]) * r.uniform(30, 75), ph=r.uniform(0, 6),
                     h=150 + (y - self.base) * 0.9, walk=1.0 if r.random() < 0.8 else 0.0)
            self.people.append(p)
        self.people.sort(key=lambda p: p["y"])
        self.car = (r.uniform(0, W), r.choice([-1, 1]) * r.uniform(500, 800), CLOTHES[r.integers(len(CLOTHES))], int(r.integers(0, 2)))
        self.palms = [(r.uniform(0, W + 1600), r.uniform(380, 520)) for _ in range(4)]

    def frame(self, t, pan):
        img = Image.new("RGBA", (W, H))
        img.paste(self.sky, (0, 0))
        off = pan * 0.9 + t * 20
        paste(img, layer_crop(self.fac, off), 0, 0)
        lw = self.fac.size[0]
        for x, y, spr, ph in self.signs:
            sx = (x - off) % lw
            if sx > W + 250: sx -= lw
            if -300 < sx < W + 300:
                paste(img, spr, sx - spr.size[0] / 2, y - spr.size[1] / 2)
        d = ImageDraw.Draw(img)
        d.rectangle([0, self.base, W, H], fill=(190, 180, 170, 255) if self.v == "day" else (60, 50, 70, 255))
        for k in range(0, W + 120, 120):
            x = (k - off) % (W + 120)
            d.line([(x, self.base), (x - 60, H)], fill=(170, 160, 150, 255) if self.v == "day" else (50, 42, 60, 255), width=2)
        for px, ph in self.palms:
            x = (px - off) % lw
            if x > W + 300: x -= lw
            draw_palm(d, x, self.base + 4, ph, 0.05, math.sin(t + px) * 0.8, (60, 80, 40, 255) if self.v == "day" else (20, 14, 26, 255))
        for p in self.people:
            x = (p["x"] + p["sp"] * t * p["walk"] - off) % lw
            if x > W + 200: x -= lw
            draw_person(d, x, p["y"], p["h"], p["shirt"], p["pants"], p["skin"], t * 6.5 + p["ph"], p["walk"], p["long_hair"],
                        p["hair"], facing=1 if p["sp"] > 0 else -1)
        cx0, sp, col, st = self.car
        x = (cx0 + sp * t) % (W * 3) - W
        draw_car_side(d, x, H + 30, 700, col + (255,), wheel_ang=t * sp / 50, style=st)
        img = img.convert("RGB")
        if self.v == "dusk":
            L = Lights()
            L.add(x + (700 if sp > 0 else 0), H - 60, 80, (255, 240, 200), 0.9)
            img = L.apply(img)
        return img


# =====================================================================  CLUB
class Club(Scene):
    variants = ["dance", "dance", "bar"]

    def setup(self):
        r = self.rng
        self.bg = vgrad(W, H, [(0, (8, 4, 20)), (0.6, (30, 8, 50)), (1, (10, 4, 16))])
        self.cols = [NEON[i] for i in r.choice(len(NEON), 3, replace=False)]
        self.crowd = []
        for row in range(4):
            for k in range(int(r.integers(10, 16))):
                p = random_person(r)
                p.update(x=r.uniform(-50, W + 50), row=row, ph=r.uniform(0, 6), up=r.random() < 0.35)
                self.crowd.append(p)
        self.crowd.sort(key=lambda p: p["row"])
        self.haze = Image.fromarray((value_noise(W // 4, H // 4, r, 4, 3) * 255).astype(np.uint8)).resize((W + 300, H))
        self.sign = sign_sprite(r.choice(["COCKTAILS", "NIGHT CLUB", "DANCE", "LOUNGE", "VIP"]), self.cols[0], 80)
        self.bottles = [(r.uniform(80, W - 80), r.integers(0, 3), NEON[r.integers(len(NEON))]) for _ in range(60)]

    def frame(self, t, pan):
        img = self.bg.copy().convert("RGBA")
        d = ImageDraw.Draw(img)
        L = Lights()
        bpm = 2.1
        beat = (t * bpm) % 1.0
        pulse = math.exp(-beat * 5)
        if self.v == "dance":
            for k in range(10):
                src = (W * (0.2 + 0.6 * (k % 3) / 2), 0)
                a = math.sin(t * (0.6 + k * 0.13) + k) * 1.0 + math.pi / 2
                L2 = 1400
                col = self.cols[k % 3]
                d.line([src, (src[0] + math.cos(a) * L2, src[1] + math.sin(a) * L2)], fill=col + (255,), width=3)
                L.add(src[0], src[1] + 10, 50, col, 0.8)
            d.rectangle([W * 0.35, H * 0.38, W * 0.65, H * 0.5], fill=(20, 10, 30, 255))
            d.ellipse([W * 0.5 - 20, H * 0.3 - 20, W * 0.5 + 20, H * 0.3 + 20], fill=(10, 6, 14, 255))
            d.rectangle([W * 0.5 - 30, H * 0.32, W * 0.5 + 30, H * 0.4], fill=(10, 6, 14, 255))
        else:
            paste(img, self.sign, W / 2 - self.sign.size[0] / 2 - pan * 0.2, 60)
            for sy in (230, 300, 370):
                d.rectangle([40, sy, W - 40, sy + 6], fill=(60, 40, 70, 255))
            for bx, row, c in self.bottles:
                x = bx - pan * 0.3
                sy = 230 + row * 70
                d.rectangle([x - 7, sy - 40, x + 7, sy], fill=mix(c, (0, 0, 0), 0.4) + (255,))
                d.rectangle([x - 3, sy - 54, x + 3, sy - 40], fill=mix(c, (0, 0, 0), 0.4) + (255,))
                L.add(x, sy - 20, 14, c, 0.5)
            d.rectangle([0, H * 0.62, W, H * 0.7], fill=(30, 20, 40, 255))
            d.line([(0, H * 0.62), (W, H * 0.62)], fill=self.cols[1] + (255,), width=4)
            L.add(W / 2, H * 0.62, 700, self.cols[1], 0.15, 1.2)
        haze = layer_crop(self.haze.convert("L").convert("RGBA"), t * 20 + pan * 0.2)
        ha = np.asarray(haze.convert("L"), np.float32) * 0.22
        hz = Image.new("RGBA", (W, H), self.cols[1] + (0,))
        hz.putalpha(Image.fromarray(ha.astype(np.uint8)))
        img.alpha_composite(hz)
        rows_y = [H * 0.78, H * 0.86, H * 0.95, H * 1.06] if self.v == "dance" else [H * 0.9, H * 1.0, H * 1.1, H * 1.2]
        for p in self.crowd:
            y = rows_y[p["row"]] + abs(math.sin(t * bpm * math.pi + p["ph"])) * -10
            h = 260 + p["row"] * 90
            x = p["x"] - pan * (0.5 + p["row"] * 0.25)
            c = mix(p["shirt"], (0, 0, 0), 0.75)
            draw_person(d, x, y + h * 0.1, h, c, (8, 6, 12), mix(p["skin"], (0, 0, 0), 0.75), 0, 0.0, p["long_hair"],
                        (8, 6, 10), arms_up=(0.6 + 0.4 * pulse) if p["up"] and self.v == "dance" else 0)
        img = img.convert("RGB")
        if self.v == "dance":
            for k in range(6):
                x = (W * (k / 6) + t * 140 * (1 if k % 2 else -1)) % W
                L.add(x, H * 0.75 + math.sin(t + k) * 40, 120, self.cols[k % 3], 0.35)
            if beat < 0.08 and int(t * bpm) % 4 == 0:
                L.add(W / 2, H / 2, 900, (255, 255, 255), 0.3, 1.0)
        return L.apply(img)


# =====================================================================  MOUNTAINS
def ridge(w, rng, rough=0.55, base_amp=1.0):
    n = 1
    pts = np.array([rng.uniform(0, 1), rng.uniform(0, 1)])
    amp = base_amp
    while len(pts) < w:
        mid = (pts[:-1] + pts[1:]) / 2 + rng.uniform(-amp, amp, len(pts) - 1) * 0.5
        new = np.empty(len(pts) * 2 - 1)
        new[0::2] = pts; new[1::2] = mid
        pts = new; amp *= rough
    x = np.linspace(0, len(pts) - 1, w)
    return np.interp(x, np.arange(len(pts)), pts)


class Mountains(Scene):
    variants = ["dawn", "sunset", "day"]

    def setup(self):
        r = self.rng
        self.sky = vgrad(W, H, SKIES[self.v])
        far = (150, 120, 170) if self.v != "day" else (150, 180, 210)
        near = (20, 30, 30) if self.v != "day" else (30, 70, 45)
        self.layers = []
        for i in range(5):
            u = i / 4
            col = mix(far, near, u)
            rg = ridge(W + 800, r)
            rg = (rg - rg.min()) / (np.ptp(rg) + 1e-6)
            top = H * (0.35 + u * 0.22) + rg * H * (0.25 - u * 0.05)
            im = Image.new("RGBA", (W + 800, H))
            d = ImageDraw.Draw(im)
            poly = [(x, top[x]) for x in range(0, W + 800, 4)] + [(W + 800, H), (0, H)]
            d.polygon(poly, fill=col + (255,))
            if i >= 2:
                for x in range(0, W + 800, int(14 - i * 2)):
                    if r.random() < 0.7:
                        th = r.uniform(14, 40) * (1 + u)
                        yy = top[min(x, W + 799)] + 4
                        d.polygon([(x - th * 0.3, yy), (x, yy - th), (x + th * 0.3, yy)], fill=col + (255,))
            self.layers.append((im, 0.15 + u * 0.9))
        self.mist = Image.fromarray((value_noise(W // 4, 60, r, 4, 3) * 255).astype(np.uint8)).resize((W + 400, 240))
        self.birds = [(r.uniform(0, W), r.uniform(80, 260), r.uniform(0, 6)) for _ in range(7)]

    def frame(self, t, pan):
        img = self.sky.copy().convert("RGBA")
        L = Lights()
        if self.v != "day":
            draw_sun(img, W * 0.6 - pan * 0.05, H * 0.42 - t * 4, 70, (255, 240, 180), (255, 140, 100), False)
            L.add(W * 0.6, H * 0.42, 400, (255, 160, 100), 0.35)
        for k, (im, f) in enumerate(self.layers):
            paste(img, layer_crop(im, pan * f + t * 6 * f), 0, 0)
            if k == 1 or k == 3:
                m = layer_crop(self.mist.convert("L").convert("RGBA"), t * 15 * (k + 1) + pan * f)
                ma = np.asarray(m.convert("L"), np.float32) * 0.45
                fog = Image.new("RGBA", (W, 240), (255, 255, 255, 0))
                fog.putalpha(Image.fromarray(ma.astype(np.uint8)))
                img.alpha_composite(fog, (0, int(H * (0.45 + k * 0.08))))
        d = ImageDraw.Draw(img)
        for bx, by, ph in self.birds:
            x = (bx + t * 45) % (W + 100) - 50
            fl = math.sin(t * 7 + ph) * 6
            d.line([(x - 10, by - fl), (x, by), (x + 10, by - fl)], fill=(30, 30, 40, 255), width=2)
        return L.apply(img.convert("RGB"))


# =====================================================================  STORM
class Storm(Scene):
    variants = ["sea", "city"]

    def setup(self):
        r = self.rng
        self.hy = int(H * 0.6)
        n = value_noise(W // 3 + 200, self.hy // 3, r, 5, 3)
        c1, c2 = np.array([20, 24, 34], np.float32), np.array([90, 96, 110], np.float32)
        cl = c1 + (c2 - c1) * (n[..., None] ** 1.4)
        self.clouds = Image.fromarray(cl.astype(np.uint8)).resize((W + 600, self.hy), Image.BICUBIC)
        rain = np.zeros((H * 2, W + 400), np.uint8)
        for _ in range(5000):
            x, y = r.integers(0, W + 400), r.integers(0, H * 2 - 60)
            ln = int(r.integers(20, 50))
            for k in range(0, ln, 2):
                xx = x - k // 3
                if 0 <= xx < W + 400:
                    rain[y + k, xx] = 150
        self.rain = Image.fromarray(rain).filter(ImageFilter.GaussianBlur(0.7))
        self.city = city_layer(W + 600, self.hy + 1, self.hy, r, 60, 260, (16, 18, 26), [(255, 210, 140)], 0.25, 0.05)
        self.palms = [(r.uniform(0, W + 400), r.uniform(320, 520)) for _ in range(4)]
        times = sorted(r.uniform(0.3, max(0.4, self.dur - 0.4), int(r.integers(1, 3))))
        self.flashes = times
        self.events = [("thunder", tt) for tt in times]
        self.bolts = []
        for tt in times:
            x = r.uniform(W * 0.2, W * 0.8); y = 0
            pts = [(x, y)]
            while y < self.hy - 40:
                y += r.uniform(20, 50); x += r.uniform(-40, 40)
                pts.append((x, y))
            self.bolts.append(pts)

    def frame(self, t, pan):
        img = Image.new("RGB", (W, H), (20, 24, 30))
        cx = int(t * 40 + pan * 0.2) % 600
        img.paste(self.clouds.crop((cx, 0, cx + W, self.hy)), (0, 0))
        img = img.convert("RGBA")
        paste(img, layer_crop(self.city, pan * 0.4), 0, 0)
        d = ImageDraw.Draw(img)
        flash = 0.0
        for tt, bolt in zip(self.flashes, self.bolts):
            dt = t - tt
            if 0 <= dt < 0.35:
                flash = max(flash, math.exp(-dt * 10) * (0.7 + 0.3 * math.sin(dt * 80)))
                if dt < 0.2:
                    d.line(bolt, fill=(235, 235, 255, 255), width=4)
        if self.v == "sea":
            yy = np.arange(H - self.hy)[:, None].astype(np.float32)
            xx = np.arange(W)[None, :].astype(np.float32)
            dp = (yy + 10) / (H - self.hy)
            wv = np.sin(xx * 0.02 / dp + t * 3 + dp * 30) * np.sin(xx * 0.007 / dp - t * 2)
            base = np.array([25, 40, 50], np.float32) + np.clip(wv, 0, 1)[..., None] ** 2 * 90 * dp[..., None]
            arr = np.asarray(img.convert("RGB")).copy()
            arr[self.hy:] = np.clip(base, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr).convert("RGBA")
            d = ImageDraw.Draw(img)
        else:
            d.rectangle([0, self.hy, W, H], fill=(24, 26, 34, 255))
        for px, ph in self.palms:
            x = (px - pan * 1.3) % (W + 500) - 200
            sw = 3.0 + math.sin(t * 2.5 + px) * 1.2
            draw_palm(d, x, H + 20, ph, 0.35, sw, (8, 10, 12, 255))
        img = img.convert("RGB")
        if flash > 0:
            arr = np.asarray(img, np.float32) * (1 + flash * 1.5) + flash * 60
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        ry = int(t * 1500) % H
        rx = int(t * 300) % 400
        rain = self.rain.crop((rx, H - ry, rx + W, 2 * H - ry))
        img = Image.composite(Image.new("RGB", (W, H), (190, 200, 220)), img, rain)
        return img


# =====================================================================  MAP (ilustrativo)
REGIONS = [("MOUNT KALAGA", 0.50, 0.16), ("PORT GELLHORN", 0.18, 0.22), ("AMBROSIA", 0.52, 0.40),
           ("GRASSRIVERS", 0.50, 0.66), ("VICE CITY", 0.73, 0.70), ("LEONIDA KEYS", 0.48, 0.93)]


class MapScene(Scene):
    variants = ["map"]

    def setup(self):
        r = self.rng
        S = 1800
        self.S = S
        img = Image.new("RGB", (S, S), (6, 14, 30))
        d = ImageDraw.Draw(img)
        for k in range(0, S, 60):
            d.line([(k, 0), (k, S)], fill=(12, 26, 50), width=1)
            d.line([(0, k), (S, k)], fill=(12, 26, 50), width=1)
        # silueta de península ficticia (forma original, no el mapa oficial)
        rr = np.random.default_rng(7)
        pts = []
        outline = [(0.05, 0.12), (0.30, 0.10), (0.62, 0.06), (0.80, 0.12), (0.82, 0.35), (0.86, 0.55), (0.84, 0.74),
                   (0.74, 0.86), (0.60, 0.84), (0.50, 0.74), (0.40, 0.58), (0.34, 0.40), (0.24, 0.30), (0.05, 0.30)]
        for i in range(len(outline)):
            a, b = outline[i], outline[(i + 1) % len(outline)]
            for s in np.linspace(0, 1, 18, endpoint=False):
                x = a[0] + (b[0] - a[0]) * s + rr.uniform(-0.006, 0.006)
                y = a[1] + (b[1] - a[1]) * s + rr.uniform(-0.006, 0.006)
                pts.append((x * S, y * S))
        land = Image.new("L", (S, S), 0)
        ImageDraw.Draw(land).polygon(pts, fill=255)
        for k in range(9):
            x, y = (0.62 - k * 0.04) * S, (0.88 + k * 0.012) * S
            ImageDraw.Draw(land).ellipse([x - 14, y - 8, x + 14, y + 8], fill=255)
        tex = value_noise(S // 6, S // 6, rr, 4, 3)
        tex = np.asarray(Image.fromarray((tex * 255).astype(np.uint8)).resize((S, S)), np.float32) / 255
        lc = np.stack([20 + tex * 30, 60 + tex * 50, 70 + tex * 40], -1)
        base = np.asarray(img, np.float32)
        la = np.asarray(land, np.float32)[..., None] / 255
        out = base * (1 - la) + lc * la
        contour = (np.abs(((tex * 12) % 1) - 0.5) < 0.04)[..., None] * la * 40
        out += contour
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        edge = land.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
        glow = edge.filter(ImageFilter.GaussianBlur(6))
        img = Image.composite(Image.new("RGB", (S, S), (255, 80, 180)), img, glow)
        img = Image.composite(Image.new("RGB", (S, S), (255, 200, 240)), img, edge)
        self.map = img
        self.order = list(r.permutation(len(REGIONS)))
        self.font = font("Anton-Regular.ttf", 34)
        self.small = font("Poppins-Bold.ttf", 16)

    def frame(self, t, pan):
        S = self.S
        u = t / self.dur
        n = len(self.order)
        seg = u * (n - 1) * 0.6
        i0 = int(seg) % n; i1 = (i0 + 1) % n; f = ease(seg - int(seg))
        a, b = REGIONS[self.order[i0]], REGIONS[self.order[i1]]
        cxm = lerp(a[1], b[1], f) * S; cym = lerp(a[2], b[2], f) * S
        z = 1.1 + 0.25 * math.sin(u * math.pi)
        cxm = lerp(S / 2, cxm, 0.55); cym = lerp(S / 2, cym, 0.55)
        vw, vh = W / z * 1.35, H / z * 1.35
        box = (cxm - vw / 2, cym - vh / 2, cxm + vw / 2, cym + vh / 2)
        img = self.map.transform((W, H), Image.EXTENT, box, Image.BILINEAR, fillcolor=(6, 14, 30))
        d = ImageDraw.Draw(img)
        L = Lights()
        sx_ = W / vw
        for k, (name, rx, ry) in enumerate(REGIONS):
            x = (rx * S - box[0]) * sx_; y = (ry * S - box[1]) * sx_
            p = (t * 1.2 + k * 0.3) % 1.0
            rad = 10 + p * 40
            d.ellipse([x - rad, y - rad, x + rad, y + rad], outline=(255, 120, 200), width=2)
            L.add(x, y, 26, (255, 90, 190), 1.0)
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(255, 255, 255))
            d.text((x + 16, y - 22), name, font=self.font, fill=(255, 255, 255), stroke_width=3, stroke_fill=(10, 10, 30))
        sy = int((t * 260) % H)
        L.add(W / 2, sy, 10, (80, 200, 255), 0.0)
        d.line([(0, sy), (W, sy)], fill=(80, 200, 255), width=2)
        d.text((24, H - 40), "MAPA ILUSTRATIVO · UBICACIONES APROXIMADAS", font=self.small, fill=(180, 200, 230))
        return L.apply(img)


# =====================================================================  CAR (primer plano)
class Car(Scene):
    variants = ["night", "sunset", "close"]

    def setup(self):
        r = self.rng
        self.col = [(200, 30, 60), (30, 180, 200), (245, 245, 245), (140, 60, 220), (250, 170, 40), (20, 20, 24)][r.integers(6)]
        self.style = int(r.integers(0, 2))
        sk = "night" if self.v in ("night", "close") else "sunset"
        self.sky = vgrad(W, H, SKIES[sk])
        self.night = sk == "night"
        self.lights = [(r.uniform(0, W * 2), r.uniform(80, H * 0.6), r.uniform(10, 40), NEON[r.integers(len(NEON))] if self.night else (255, 200, 140)) for _ in range(40)]
        self.city = city_layer(W + 900, int(H * 0.62) + 1, int(H * 0.62), r, 80, 380, (20, 14, 34) if self.night else (60, 30, 70),
                               [(255, 210, 150), (120, 220, 255)], 0.4, 0.3)
        self.city = self.city.filter(ImageFilter.GaussianBlur(3))

    def frame(self, t, pan):
        img = self.sky.copy().convert("RGBA")
        speed = 900
        paste(img, layer_crop(self.city, t * speed * 0.15 + pan * 0.3), 0, 0)
        d = ImageDraw.Draw(img)
        L = Lights()
        for lx, ly, rr, c in self.lights:
            x = (lx - t * speed * 0.6) % (W * 2) - W * 0.3
            d.line([(x, ly), (x + 160, ly)], fill=c + (255,), width=int(rr * 0.3))
            L.add(x + 80, ly, rr * 2, c, 0.25)
        d.rectangle([0, H * 0.62, W, H], fill=(30, 28, 38, 255))
        for k in range(8):
            x = (k * 260 - t * speed) % (W + 260) - 130
            d.rectangle([x, H * 0.88, x + 120, H * 0.9], fill=(220, 220, 200, 255))
        Lc = 980
        x0 = W / 2 - Lc / 2 + math.sin(t * 0.8) * 15
        y0 = H * 0.86 + math.sin(t * 13) * 1.5
        d.ellipse([x0 - 20, y0 - 18, x0 + Lc + 20, y0 + 14], fill=(10, 10, 14, 200))
        poly = draw_car_side(d, x0, y0, Lc, self.col + (255,), wheel_ang=-t * 18, style=self.style)
        img = img.convert("RGB")
        # brillo de reflejo que recorre la carrocería
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        md.polygon(poly, fill=255)
        band = Image.new("L", (W, H), 0)
        bx = (t * 500) % (W + 600) - 300
        ImageDraw.Draw(band).polygon([(bx, 0), (bx + 90, 0), (bx - 110, H), (bx - 200, H)], fill=120)
        band = band.filter(ImageFilter.GaussianBlur(20))
        band = Image.fromarray(np.minimum(np.asarray(band), np.asarray(mask)))
        img = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), img, band)
        L.add(x0 + Lc * 0.99, y0 - Lc * 0.26 * 0.5, 90, (255, 245, 220), 1.0)
        L.add(x0 + 6, y0 - Lc * 0.26 * 0.5, 40, (255, 30, 30), 1.0)
        img = L.apply(img)
        if self.v == "close":
            cx = min(W * 0.72, max(W * 0.28, x0 + Lc * 0.78))
            img = img.resize((W, H), Image.BILINEAR, box=(cx - W * 0.28, H * 0.42, cx + W * 0.28, H * 0.42 + H * 0.56))
        return img


# =====================================================================  BRIDGE (cayos)
class Bridge(Scene):
    variants = ["day", "sunset"]

    def setup(self):
        r = self.rng
        self.hy = int(H * 0.30)
        self.sky = vgrad(W, self.hy, SKIES[self.v])
        top = (40, 150, 200) if self.v == "day" else (120, 70, 120)
        bot = (60, 220, 210) if self.v == "day" else (240, 150, 110)
        self.sea = vgrad_arr(W, H - self.hy, [(0, top), (1, bot)])
        n = value_noise(W // 4, (H - self.hy) // 4, r, 3, 3)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H - self.hy)), np.float32) / 255
        self.sea = self.sea * (0.9 + 0.2 * n[..., None])
        self.isl = []
        for _ in range(int(r.integers(3, 6))):
            x, y = r.uniform(0, W), r.uniform(self.hy + 30, H - 60)
            s = (y - self.hy) / (H - self.hy) * 120 + 20
            self.isl.append((x, y, s))
        self.cars = [(r.uniform(0, 1), r.choice([-1, 1]) * r.uniform(0.04, 0.08), CLOTHES[r.integers(len(CLOTHES))]) for _ in range(12)]
        self.boats = [(r.uniform(0, W), r.uniform(self.hy + 40, H - 40), r.choice([-1, 1]) * r.uniform(20, 50)) for _ in range(4)]
        self.p0 = (r.uniform(-0.2, 0.2) * W, H + 20)
        self.p1 = (W * r.uniform(0.55, 0.8), self.hy)

    def pt(self, s, pan):
        x = lerp(self.p0[0], self.p1[0], s) - pan * (1 - s) * 0.8
        y = lerp(self.p0[1], self.p1[1], s ** 0.6)
        return x, y

    def frame(self, t, pan):
        img = Image.new("RGB", (W, H))
        img.paste(self.sky, (0, 0))
        sea = self.sea.copy()
        img_arr = np.asarray(img).copy()
        sh = np.sin(np.arange(W)[None, :] * 0.05 + np.arange(H - self.hy)[:, None] * 0.3 + t * 3)
        img_arr[self.hy:] = np.clip(sea + (sh > 0.97)[..., None] * 60, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_arr)
        d = ImageDraw.Draw(img)
        for x, y, s in self.isl:
            xx = x - pan * (y / H)
            d.ellipse([xx - s * 1.7, y - s * 0.5, xx + s * 1.7, y + s * 0.5], fill=(240, 225, 180) if self.v == "day" else (220, 170, 140))
            d.ellipse([xx - s * 1.4, y - s * 0.4, xx + s * 1.4, y + s * 0.35], fill=(60, 140, 70) if self.v == "day" else (40, 40, 40))
            for k in range(3):
                draw_palm(d, xx - s + k * s, y, s * 0.9, 0.1, math.sin(t + k) * 0.8, (30, 80, 40) if self.v == "day" else (20, 15, 25), leaflets=s > 60)
        for bx, by, sp in self.boats:
            x = (bx + sp * t - pan * by / H) % (W + 100) - 50
            s = (by - self.hy) / (H - self.hy) * 30 + 6
            d.polygon([(x - s * 1.6 * (1 if sp > 0 else -1), by + 4), (x - s * 4 * (1 if sp > 0 else -1), by - 1), (x - s * 4 * (1 if sp > 0 else -1), by + 9)], fill=(240, 250, 250))
            d.ellipse([x - s, by - s * 0.3, x + s, by + s * 0.3], fill=(250, 250, 250))
        # puente
        N = 60
        for k in range(N):
            s0, s1 = k / N, (k + 1) / N
            a, b = self.pt(s0, pan), self.pt(s1, pan)
            wdt = max(2, int(lerp(70, 3, s0)))
            d.line([a, b], fill=(225, 220, 210), width=wdt)
            if k % 3 == 0:
                d.line([a, (a[0], a[1] + lerp(80, 4, s0))], fill=(190, 185, 175), width=max(1, int(wdt * 0.35)))
        for s0, sp, col in self.cars:
            s = (s0 + sp * t) % 1.0
            x, y = self.pt(s, pan)
            sz = lerp(22, 2, s)
            off = sz * 0.6 * (1 if sp > 0 else -1)
            d.rectangle([x + off - sz, y - sz * 0.8, x + off + sz, y], fill=col)
        return img


SCENES = {
    "skyline": Skyline, "highway": Highway, "beach": Beach, "aerial": Aerial, "ocean": Ocean, "swamp": Swamp,
    "rainstreet": RainStreet, "police": Police, "policeheli": PoliceHeli, "duo": Duo, "shops": Shops, "club": Club,
    "mountains": Mountains, "storm": Storm, "map": MapScene, "car": Car, "bridge": Bridge,
}
