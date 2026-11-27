"""Extra shots for the 10-minute film + chapter/title cards."""
import numpy as np, cv2, math
from fx import *
from scenes import GOLD, WARM, bg_dust, EndCard


# Endless staircase climbing into the light
class Stairs:
    def frame(self, t, d):
        img = vgrad(H, W, [(0, (0.6, 0.42, 0.18)), (0.25, (0.2, 0.13, 0.05)), (1, (0.0, 0.0, 0.0))])
        img += radial(H, W, W / 2, 120, 700, 1.5)[..., None] * np.asarray(WARM) * 1.5
        st = np.zeros((H, W), np.float32); lines = np.zeros((H, W), np.float32)
        off = (t * 0.6) % 1
        for k in range(-1, 26):
            z = min(1.0, max(0.0, (k + off) / 25.0)); z2 = min(1.0, z + 0.04)
            y = H - (H - 260) * (1 - (1 - z) ** 1.6)
            y2 = H - (H - 260) * (1 - (1 - z2) ** 1.6)
            wdt = 700 * (1 - z) + 80
            cv2.rectangle(st, (int(W / 2 - wdt / 2), int(y2)), (int(W / 2 + wdt / 2), int(y)), 1.0, -1)
            cv2.line(lines, (int(W / 2 - wdt / 2), int(y2)), (int(W / 2 + wdt / 2), int(y2)), float(0.4 + 0.6 * z), max(1, int(4 * (1 - z))), cv2.LINE_AA)
        img = comp(img, st, (0.012, 0.009, 0.006))
        img += (blur(lines, 1) + 0.6 * blur(lines, 8))[..., None] * np.asarray(GOLD) * 1.4
        s = 64; st_ = math.sin(t * 3)
        fig = figure_mask(H, W, W / 2, 1420 - 3.75 * s, s, dict(front=True, la1=12 * st_, la2=10 * st_, ra1=-12 * st_, ra2=-10 * st_,
                                                             ll1=10 * st_, ll2=5 * st_, rl1=-10 * st_, rl2=-5 * st_))
        img = comp(img, fig, (0.003, 0.002, 0.002))
        img += rim(fig, 0, 1, 3, 2)[..., None] * np.asarray(WARM) * 1.5
        img += bg_dust(t, 101, 90)[..., None] * np.asarray(WARM) * 0.6
        img = bloom(img, 0.6, 30, 0.8)
        return cam(img, 1.05 + 0.05 * t / d, W / 2, H * 0.5)


# Meditating figure with golden aura rings
class Meditate:
    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + radial(H, W, W / 2, H * 0.45, 900, 2)[..., None] * np.asarray((0.15, 0.1, 0.04))
        cx, cy = W / 2, H * 0.47
        rings = np.zeros((H, W), np.float32)
        for k in range(6):
            r = ((k / 6 + t * 0.12) % 1) * 900
            cv2.circle(rings, (int(cx), int(cy)), int(r), float(1 - r / 900) * 0.8, 3, cv2.LINE_AA)
        img += (blur(rings, 2) + blur(rings, 12))[..., None] * np.asarray(GOLD)
        img += radial(H, W, cx, cy, 420, 2)[..., None] * np.asarray(GOLD) * 0.7
        m = np.zeros((H, W), np.uint8); s = 60
        hip = (int(cx), int(cy + 180))
        cv2.ellipse(m, hip, (int(3.4 * s), int(0.7 * s)), 0, 0, 360, 255, -1, cv2.LINE_AA)  # crossed legs
        tor = np.array([[cx - 0.85 * s, cy + 180 - 2.7 * s], [cx + 0.85 * s, cy + 180 - 2.7 * s], [cx + 0.6 * s, cy + 180], [cx - 0.6 * s, cy + 180]], np.int32)
        cv2.fillPoly(m, [tor], 255, cv2.LINE_AA)
        cv2.ellipse(m, (int(cx), int(cy + 180 - 3.45 * s)), (int(0.45 * s), int(0.55 * s)), 0, 0, 360, 255, -1, cv2.LINE_AA)
        cv2.line(m, (int(cx), int(cy + 180 - 2.9 * s)), (int(cx), int(cy + 180 - 2.6 * s)), 255, int(0.4 * s))
        for sd in (-1, 1):
            cv2.line(m, (int(cx + sd * 0.75 * s), int(cy + 180 - 2.5 * s)), (int(cx + sd * 1.6 * s), int(cy + 180 - 0.9 * s)), 255, int(0.4 * s), cv2.LINE_AA)
            cv2.line(m, (int(cx + sd * 1.6 * s), int(cy + 180 - 0.9 * s)), (int(cx + sd * 1.9 * s), int(cy + 180 - 0.1 * s)), 255, int(0.34 * s), cv2.LINE_AA)
        fig = m.astype(np.float32) / 255
        img = comp(img, fig, (0.003, 0.002, 0.002))
        img += rim(fig, 0, 1, 4, 2)[..., None] * np.asarray(WARM) * 1.6
        img += particles(H, W, 120, 33, t, vel=(0, -25), size=(1, 3), bright=(0.2, 1))[..., None] * np.asarray(GOLD) * 0.8
        img = bloom(img, 0.6, 30, 0.8)
        return cam(img, 1.0 + 0.06 * t / d, W / 2, H * 0.5)


# Forge: flames + rising embers + anvil silhouette
class Embers:
    def __init__(self):
        self.n = [fbm(H // 2, W // 4, 70 + k, 5, 4) for k in range(2)]

    def frame(self, t, d):
        h4, w4 = H // 4, W // 4
        yy = np.linspace(0, 1, h4)[:, None]
        o1 = int(h4 - (t * 60) % h4); o2 = int(h4 - (t * 100) % h4)
        n = self.n[0][o1:o1 + h4] * 0.6 + self.n[1][o2:o2 + h4] * 0.4
        flame = np.clip((n - (1 - yy) * 1.15 + 0.25) * 2.2, 0, 1) ** 1.5
        flame = cv2.resize(flame.astype(np.float32), (W, H))
        img = flame[..., None] * np.asarray((1.6, 0.85, 0.25)) * 1.2
        em = np.zeros((H, W), np.float32); r = rng(19); k = 260
        x0 = r.uniform(0, W, k); sp = r.uniform(150, 500, k); ph = r.uniform(0, 1, k)
        for i in range(k):
            age = (ph[i] + t * sp[i] / 2000) % 1
            x = x0[i] + 60 * math.sin(age * 9 + i); y = H - age * H * 1.1
            cv2.circle(em, (int(x), int(y)), 3, float(1.3 * (1 - age)), -1, cv2.LINE_AA)
        img += (em[..., None] + blur(em, 6)[..., None] * 1.5) * np.asarray((1, 0.7, 0.3))
        anv = np.zeros((H, W), np.float32)
        cv2.fillPoly(anv, [np.array([[150, 1350], [930, 1350], [930, 1420], [760, 1460], [700, 1560], [800, 1640], [280, 1640], [380, 1560], [320, 1460], [150, 1400]], np.int32)], 1.0, cv2.LINE_AA)
        cv2.fillPoly(anv, [np.array([[930, 1350], [1080, 1380], [930, 1400]], np.int32)], 1.0, cv2.LINE_AA)
        cv2.rectangle(anv, (0, 1640), (W, H), 1.0, -1)
        img = comp(img, anv, (0.005, 0.004, 0.003))
        img += rim(anv, 0, 1, 3, 2)[..., None] * np.asarray(WARM) * 2
        img = bloom(img, 0.6, 30, 0.9)
        return cam(img, 1.05 + 0.05 * t / d, W / 2, H * 0.52)


# Night ocean with golden moon path, figure on a rock
class Ocean:
    def frame(self, t, d):
        hz_ = int(H * 0.45)
        img = vgrad(H, W, [(0, (0, 0, 0)), (0.44, (0.12, 0.08, 0.04)), (0.45, (0.02, 0.015, 0.01)), (1, (0.01, 0.01, 0.01))])
        img += radial(H, W, W / 2, hz_ - 330, 90, 1.0)[..., None] * 3 * np.asarray(WARM) + radial(H, W, W / 2, hz_ - 330, 600, 2)[..., None] * 0.5 * np.asarray(GOLD)
        wv = np.zeros((H, W), np.float32); r = rng(5)
        for k in range(700):
            z = r.uniform(0, 1) ** 2; y = hz_ + (H - hz_) * z
            spread = 30 + 600 * z
            x = W / 2 + r.normal(0, 1) * spread * 0.5 + 40 * math.sin(t * 1.5 + k)
            ln = 6 + 90 * z
            br = (0.6 + 0.4 * math.sin(t * 3 + k * 1.3)) * (1 - 0.5 * z)
            cv2.line(wv, (int(x - ln), int(y)), (int(x + ln), int(y)), float(br), max(1, int(1 + 3 * z)), cv2.LINE_AA)
        img += blur(wv, 1.5)[..., None] * np.asarray(WARM) * 1.2
        rock = np.zeros((H, W), np.float32)
        cv2.fillPoly(rock, [np.array([[0, 1500], [250, 1420], [420, 1450], [560, 1560], [700, 1700], [W, 1760], [W, H], [0, H]], np.int32)], 1.0, cv2.LINE_AA)
        s = 40
        fig = figure_mask(H, W, 330, 1430 - 3.75 * s, s, dict(front=True, coat=2.8, flap=math.sin(t * 2) * 0.3))
        sil = np.clip(rock + fig, 0, 1)
        img = comp(img, sil, (0.004, 0.003, 0.002))
        img += rim(sil, 0, 1, 3, 2)[..., None] * np.asarray(WARM) * 0.8
        img = bloom(img, 0.6, 30, 0.9)
        return cam(img, 1.06 - 0.05 * t / d, W / 2, H * 0.5)


# Desert dunes, lone walker, heat sun
class Desert:
    def __init__(self):
        self.d = []
        for k, (y0, amp, c) in enumerate([(1050, 120, 0.45), (1250, 160, 0.25), (1500, 200, 0.08)]):
            xs = np.linspace(0, 1, W)
            ys = y0 - amp * (0.5 + 0.5 * np.sin(xs * (1.1 + 0.6 * k) * math.pi * 2 + k * 1.7)) + 25 * ridge(W, 200 + k, 0.4, 3)
            self.d.append((fill_below(H, W, ys.astype(np.float32)), c, ys))

    def frame(self, t, d):
        img = vgrad(H, W, [(0, (0.05, 0.03, 0.01)), (0.45, (0.9, 0.6, 0.25)), (0.6, (1.0, 0.85, 0.55)), (1, (0.5, 0.3, 0.1))])
        img += radial(H, W, W * 0.62, 900, 170, 1.1)[..., None] * 3 * np.asarray(WARM)
        for k, (m, c, ys) in enumerate(self.d):
            img = comp(img, m, np.asarray((0.85, 0.55, 0.22)) * c)
            img += rim(m, 0, 1, 3, 2)[..., None] * np.asarray(WARM) * (0.8 - 0.25 * k)
        ys = self.d[1][2]; x = int(W * 0.35 + t * 18); s = 26
        fig = figure_mask(H, W, x, ys[min(x, W - 1)] - 3.75 * s + 4, s, run_pose(t * 2.2, 6) | dict(la1=10 * math.sin(t * 2.2), la2=10, ra1=-10 * math.sin(t * 2.2), ra2=-5,
                                                                                              ll1=15 * math.sin(t * 2.2), ll2=10 * math.sin(t * 2.2), rl1=-15 * math.sin(t * 2.2), rl2=-10 * math.sin(t * 2.2)))
        img = comp(img, fig, (0.01, 0.008, 0.005))
        img += streaks(H, W, 80, 3, t, angle=178, speed=500, length=80, alpha=0.2)[..., None] * np.asarray(WARM)
        img = bloom(img, 0.75, 40, 0.9)
        return cam(img, 1.08 - 0.06 * t / d, W / 2 + 20 * t, H * 0.5)


# Rain on glass, city bokeh, silhouette inside
class RainWindow:
    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + 0.01
        bok = particles(H, W, 70, 12, t * 0.3, vel=(0, 0), size=(14, 40), bright=(0.15, 0.6))
        img += blur(bok, 14)[..., None] * np.asarray(GOLD) * 1.6
        drops = np.zeros((H, W), np.float32); r = rng(8); n = 180
        x0 = r.uniform(0, W, n); y0 = r.uniform(0, H, n); sp = r.uniform(40, 260, n); sz = r.uniform(3, 9, n)
        for i in range(n):
            y = (y0[i] + sp[i] * t) % H
            cv2.ellipse(drops, (int(x0[i]), int(y)), (int(sz[i]), int(sz[i] * 1.3)), 0, 0, 360, 0.7, -1, cv2.LINE_AA)
            cv2.line(drops, (int(x0[i]), int(y - sp[i] * 0.5)), (int(x0[i]), int(y)), 0.25, max(1, int(sz[i] / 3)), cv2.LINE_AA)
        img += (drops - blur(drops, 3) * 0.6).clip(0)[..., None] * np.asarray(WARM) * 0.9
        s = 80
        fig = figure_mask(H, W, W * 0.3, 1950 - 3.75 * s, s, dict(front=True, la1=8, la2=4, ra1=-8, ra2=-4))
        img = comp(img, fig * 0.97, (0.004, 0.003, 0.002))
        img += rim(fig, 1, 0, 3, 2)[..., None] * np.asarray(GOLD) * 0.8
        img += streaks(H, W, 120, 22, t, angle=95, speed=1400, length=60, alpha=0.18)[..., None] * 0.7
        img = bloom(img, 0.5, 25, 0.8)
        return cam(img, 1.0 + 0.06 * t / d, W / 2, H * 0.5)


# Push-ups in a spotlight (side view)
class Pushups:
    def frame(self, t, d):
        img = vgrad(H, W, [(0, (0, 0, 0)), (1, (0.04, 0.03, 0.02))]) + radial(H, W, W / 2, 1320, 650, 1.6)[..., None] * np.asarray((0.75, 0.5, 0.2))
        rep = 0.5 - 0.5 * math.cos(t * 2 * math.pi / 1.1)
        s = 52; floor = 1420
        hand = (W * 0.72, floor); foot = (W * 0.16, floor)
        sh_h = 2.6 * s * (0.45 + 0.55 * rep)
        sh = (hand[0] - 0.2 * s, floor - sh_h)
        m = np.zeros((H, W), np.uint8)
        el = ((sh[0] + hand[0]) / 2 + (1 - rep) * 0.9 * s * 0 - 0.6 * s * (1 - rep), (sh[1] + hand[1]) / 2 - (1 - rep) * 0.3 * s)
        P = lambda p: (int(p[0]), int(p[1]))
        cv2.line(m, P(foot), P(sh), 255, int(0.75 * s), cv2.LINE_AA)
        cv2.line(m, P(sh), P(el), 255, int(0.42 * s), cv2.LINE_AA); cv2.line(m, P(el), P(hand), 255, int(0.34 * s), cv2.LINE_AA)
        hd = (sh[0] + 0.85 * s, sh[1] - 0.25 * s)
        cv2.ellipse(m, P(hd), (int(0.5 * s), int(0.42 * s)), 0, 0, 360, 255, -1, cv2.LINE_AA)
        fig = m.astype(np.float32) / 255
        flo = fill_below(H, W, np.full(W, floor + 12, np.float32))
        sil = np.clip(fig + flo, 0, 1)
        img = comp(img, sil, (0.004, 0.003, 0.002))
        img += rim(sil, 0, 1, 4, 2)[..., None] * np.asarray(WARM) * 2
        img += bg_dust(t, 44, 100)[..., None] * np.asarray(WARM) * 0.6
        img = bloom(img, 0.55, 30, 0.8)
        return cam(img, 1.05 + 0.06 * t / d, W / 2, H * 0.55)


# Rotating gold diamond with sparkles
class Diamond:
    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + radial(H, W, W / 2, H * 0.45, 800, 2)[..., None] * np.asarray((0.2, 0.13, 0.05))
        cx, cy, R = W / 2, H * 0.43, 330; rot = t * 0.6; n = 8
        crown_y, girdle_y, tip_y = cy - 190, cy - 60, cy + 380
        top = [(cx + R * 0.55 * math.cos(rot + k * 2 * math.pi / n), crown_y + 25 * math.sin(rot + k * 2 * math.pi / n)) for k in range(n)]
        gir = [(cx + R * math.cos(rot + (k + 0.5) * 2 * math.pi / n), girdle_y + 40 * math.sin(rot + (k + 0.5) * 2 * math.pi / n)) for k in range(n)]
        for k in range(n):
            a = rot + (k + 0.5) * 2 * math.pi / n
            facing = math.sin(a)
            if facing < -0.05: continue
            b = 0.25 + 0.75 * max(0, math.cos(a - 1.2)) ** 3
            for poly, f in (([top[k], top[(k + 1) % n], gir[k]], 1.0), ([gir[k], gir[(k - 1) % n], (cx, tip_y)], 0.7), ([top[k], gir[k], gir[(k - 1) % n]], 0.85)):
                col = np.asarray((1.0, 0.78, 0.4)) * b * f * 1.4
                cv2.fillPoly(img, [np.array(poly, np.int32)], tuple(float(c) for c in col), cv2.LINE_AA)
                cv2.polylines(img, [np.array(poly, np.int32)], True, (1.4, 1.2, 0.9), 2, cv2.LINE_AA)
        cv2.fillPoly(img, [np.array(top, np.int32)], (0.9, 0.7, 0.35), cv2.LINE_AA)
        sp = np.zeros((H, W), np.float32); r = rng(3)
        for k in range(12):
            ph = (t * 1.3 + k * 0.37) % 1; x, y = cx + r.uniform(-300, 300), cy + r.uniform(-200, 300)
            a = math.sin(ph * math.pi) ** 4 * 1.5; l = 60 * a
            cv2.line(sp, (int(x - l), int(y)), (int(x + l), int(y)), float(a), 2, cv2.LINE_AA); cv2.line(sp, (int(x), int(y - l)), (int(x), int(y + l)), float(a), 2, cv2.LINE_AA)
        img += (sp + blur(sp, 6))[..., None] * np.asarray(WARM) * 1.5
        img += bg_dust(t, 66, 100)[..., None] * np.asarray(GOLD) * 0.6
        img = bloom(img, 0.6, 30, 1.0)
        return cam(img, 1.08 - 0.06 * t / d, W / 2, H * 0.47)


# Gold clock face, ticking
class Clock:
    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + radial(H, W, W / 2, H * 0.44, 800, 2)[..., None] * np.asarray((0.15, 0.1, 0.04))
        cx, cy, R = W // 2, int(H * 0.42), 400
        c = np.zeros((H, W), np.float32)
        cv2.circle(c, (cx, cy), R, 1.0, 8, cv2.LINE_AA); cv2.circle(c, (cx, cy), R - 30, 0.4, 2, cv2.LINE_AA)
        for k in range(60):
            a = k * math.pi / 30; l = 45 if k % 5 == 0 else 18; w_ = 7 if k % 5 == 0 else 2
            cv2.line(c, (int(cx + math.sin(a) * (R - 50)), int(cy - math.cos(a) * (R - 50))), (int(cx + math.sin(a) * (R - 50 - l)), int(cy - math.cos(a) * (R - 50 - l))), 1.0, w_, cv2.LINE_AA)
        sec = math.floor(t * 2) / 2 + 0.5 * ease_out((t * 2) % 1 * 4)
        for ang, ln, wd in ((sec * 6 + 120, R - 70, 3), (305 + t * 0.6, R - 130, 10), (40 + t * 0.05, R - 210, 16)):
            a = math.radians(ang)
            cv2.line(c, (cx, cy), (int(cx + math.sin(a) * ln), int(cy - math.cos(a) * ln)), 1.0, wd, cv2.LINE_AA)
        cv2.circle(c, (cx, cy), 18, 1.0, -1, cv2.LINE_AA)
        img += (c[..., None] * 1.2 + blur(c, 10)[..., None] * 0.8) * np.asarray((1.0, 0.75, 0.35))
        img += bg_dust(t, 88, 80)[..., None] * np.asarray(GOLD) * 0.5
        img = bloom(img, 0.6, 25, 0.8)
        return cam(img, 1.12 - 0.08 * t / d, W / 2, H * 0.45, rot=3 - 6 * t / d)


# 5:00 AM alarm glowing in a dark bedroom
class Alarm:
    def __init__(self):
        from PIL import Image, ImageDraw, ImageFont
        f = ImageFont.truetype('fonts/Montserrat.ttf', 300); f.set_variation_by_name('Thin')
        im = Image.new('L', (W, 420), 0); ImageDraw.Draw(im).text((W / 2, 210), '5:00', font=f, fill=255, anchor='mm')
        self.txt = np.asarray(im).astype(np.float32) / 255
        f2 = ImageFont.truetype('fonts/Montserrat.ttf', 70); f2.set_variation_by_name('Medium')
        im = Image.new('L', (W, 120), 0); ImageDraw.Draw(im).text((W / 2, 60), 'A M', font=f2, fill=255, anchor='mm')
        self.am = np.asarray(im).astype(np.float32) / 255

    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + 0.008
        blink = 1.0 if (t % 1.0) < 0.6 else 0.55
        lay = np.zeros((H, W), np.float32)
        lay[560:980] = self.txt * blink; lay[960:1080] = self.am * 0.8
        img += (lay[..., None] * 1.6 + blur(lay, 18)[..., None] * 1.2) * np.asarray((1.0, 0.7, 0.3))
        img += radial(H, W, W / 2, 1300, 700, 2)[..., None] * np.asarray(GOLD) * 0.25 * blink
        bed = fill_below(H, W, (1500 + 40 * np.sin(np.linspace(0, 3, W))).astype(np.float32))
        img = comp(img, bed, (0.02, 0.015, 0.01))
        img += rim(bed, 0, 1, 3, 2)[..., None] * np.asarray(GOLD) * 0.6 * blink
        img = bloom(img, 0.5, 25, 0.8)
        return cam(img, 1.0 + 0.1 * ease(t / d), W / 2, H * 0.45)


# Late-night work at a desk with city behind
class Desk:
    def __init__(self):
        from scenes import City
        self.city = City(seed=55)

    def frame(self, t, d):
        c = self.city.compose(t, -8 * t)
        img = cam(c, 1.0, self.city.LW / 2, self.city.LH * 0.7) * 0.55
        desk = np.zeros((H, W), np.float32)
        cv2.rectangle(desk, (0, 1380), (W, H), 1.0, -1)
        scr = np.array([[560, 1060], [900, 1030], [900, 1260], [560, 1290]], np.int32)
        img = comp(img, desk, (0.01, 0.008, 0.006))
        glow = np.zeros((H, W), np.float32); cv2.fillPoly(glow, [scr], 1.0, cv2.LINE_AA)
        img += glow[..., None] * np.asarray((1.0, 0.85, 0.6)) * 1.3 + blur(glow, 80)[..., None] * np.asarray(GOLD) * 1.5
        cv2.fillPoly(img, [np.array([[530, 1290], [930, 1260], [990, 1380], [500, 1380]], np.int32)], (0.02, 0.015, 0.01), cv2.LINE_AA)
        s = 70
        typing = 4 * math.sin(t * 14)
        fig = figure_mask(H, W, 330, 1380, s, dict(torso=12, head=8, la1=-80 + 0, la2=-100 + typing, ra1=-75, ra2=-95 - typing, ll1=-90, ll2=0, rl1=-90, rl2=0))
        img = comp(img, fig, (0.004, 0.003, 0.002))
        img += rim(fig, 1, 0, 4, 2)[..., None] * np.asarray(WARM) * 1.6
        img = bloom(img, 0.55, 25, 0.8)
        return cam(img, 1.0 + 0.05 * t / d, W / 2, H * 0.52)


# Chapter title card / opening title
class Card:
    def __init__(self, kind, a, b):
        from PIL import Image, ImageDraw, ImageFont
        self.kind = kind
        cz = ImageFont.truetype('fonts/Cinzel.ttf', 120 if kind == '#' else 170); cz.set_variation_by_name('Bold')
        mt = ImageFont.truetype('fonts/Montserrat.ttf', 38); mt.set_variation_by_name('SemiBold')

        def txt(s, f, sp):
            ws = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != ' ' else f.size // 3 for c in s]
            tw = sum(ws) + sp * (len(s) - 1); im = Image.new('L', (int(tw + 40), int(f.size * 1.5)), 0); dr = ImageDraw.Draw(im); x = 20
            for c, w_ in zip(s, ws): dr.text((x, 10), c, font=f, fill=255); x += w_ + sp
            return np.asarray(im).astype(np.float32) / 255
        if kind == '#':
            self.top = txt('CHAPTER ' + a, mt, 16)
            words = b.split(' ')
            self.main = [txt(w, cz, 10) for w in ([b] if len(b) <= 10 else words)]
        else:
            self.top = None
            self.main = [txt('BEYOND', cz, 14), txt('MIND', cz, 40)]
            self.sub = txt(b, mt, 10)

    def paste(self, img, m, cx, cy, col, a):
        h, w = m.shape; x0, y0 = int(cx - w / 2), int(cy - h / 2)
        reg = img[y0:y0 + h, x0:x0 + w]; reg[:] = reg * (1 - m[..., None] * a) + m[..., None] * a * col

    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + radial(H, W, W / 2, H * 0.45, 900, 2)[..., None] * np.asarray((0.1, 0.065, 0.025))
        img += particles(H, W, 140, 7, t, vel=(0, -35), spread=(8, 10), size=(1, 3), bright=(0.2, 0.9))[..., None] * np.asarray(GOLD) * 0.8
        yc = H * 0.42
        if self.top is not None:
            a = ease_out(t / 0.5); self.paste(img, self.top, W / 2, yc - 150, np.asarray((1, 0.93, 0.8)), a)
        n = len(self.main); lh = 170 if self.kind == '#' else 190
        for i, m in enumerate(self.main):
            a = ease_out((t - 0.2 - 0.12 * i) / 0.6)
            if a <= 0: continue
            h, w = m.shape
            grad = np.linspace(1.15, 0.55, h)[:, None, None] * np.asarray((1.0, 0.76, 0.36))
            xs = np.arange(w)[None, :]
            shine = np.exp(-((xs - (-300 + (w + 600) * ((t - 0.8) / 1.3))) / 60.0) ** 2)[..., None] * 1.5
            col = grad + shine * np.asarray(WARM)
            y = yc + i * lh - (n - 1) * lh / 2 + 25 * (1 - a) + 40
            x0, y0 = int(W / 2 - w / 2), int(y - h / 2)
            reg = img[y0:y0 + h, x0:x0 + w]; reg[:] = reg * (1 - m[..., None] * a) + m[..., None] * a * col
        k = ease_out((t - 0.6) / 0.8)
        ly = int(yc + n * lh / 2 + 70)
        cv2.line(img, (int(W / 2 - 300 * k), ly), (int(W / 2 + 300 * k), ly), (0.8, 0.6, 0.28), 2, cv2.LINE_AA)
        if self.kind == '@':
            self.paste(img, self.sub, W / 2, ly + 70, np.asarray((1, 0.93, 0.8)), ease_out((t - 1.0) / 0.6))
        img = bloom(img, 0.6, 25, 0.6)
        fade = min(1.0, (d - t) / 0.6, t / 0.25 + 0.2)
        return cam(img, 1.0 + 0.04 * t / d, W / 2, H / 2) * max(0, fade)
