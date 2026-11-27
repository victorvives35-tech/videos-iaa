"""Every shot of the film, rendered procedurally. Each scene: frame(t, d) -> HxWx3 float image."""
import numpy as np, cv2, math
from fx import *

GOLD = (1.0, 0.72, 0.3)
WARM = (1.0, 0.85, 0.6)


def bg_dust(t, seed, n=90, vel=(6, -14)):
    return particles(H, W, n, seed, t, vel=vel, spread=(5, 5), size=(1, 3.5), bright=(0.15, 0.7))


# 1 ─ Storm cliff, lightning, lone figure (HOOK)
class Storm:
    def __init__(self):
        sky = vgrad(H, W, [(0, (0.02, 0.02, 0.025)), (0.55, (0.09, 0.08, 0.07)), (1, (0.03, 0.03, 0.03))])
        self.cl = fbm(H, W, 3, 7, 3)[..., None]
        self.sky = sky * (0.4 + 1.2 * self.cl)
        xs = np.arange(W)
        self.sky = self.sky + (radial(H, W, W * 0.55, 760, 700, 1.6)[..., None] * np.asarray((0.55, 0.36, 0.14)) * (0.5 + self.cl))
        cliff = 1010 + (xs - 600).clip(0) * 0.08 + 14 * ridge(W, 5, 0.6)
        cliff = np.where(xs < 380, 1010 + (np.clip(380 - xs, 0, None) / 380) ** 1.5 * 900, cliff)
        self.cliff = fill_below(H, W, cliff.astype(np.float32))
        self.cliff_y = cliff
        r = rng(11); pts = [(r.uniform(600, 860), -20)]
        while pts[-1][1] < 900:
            x, y = pts[-1]; pts.append((x + r.normal(0, 30), y + r.uniform(30, 70)))
        self.bolt = np.zeros((H, W), np.float32)
        cv2.polylines(self.bolt, [np.array(pts, np.int32)], False, 1.0, 4, cv2.LINE_AA)
        for k in range(4):
            i = r.integers(3, len(pts) - 3); x, y = pts[i]; b = [(x, y)]
            for _ in range(5): b.append((b[-1][0] + r.normal(25, 25) * (1 if k % 2 else -1), b[-1][1] + r.uniform(25, 55)))
            cv2.polylines(self.bolt, [np.array(b, np.int32)], False, 0.6, 2, cv2.LINE_AA)

    def frame(self, t, d):
        flash = 0.0
        for ft in (0.0, 0.12, 1.25, 1.33):
            if t >= ft: flash = max(flash, math.exp(-(t - ft) * 9))
        img = self.sky * (1 + 3.5 * flash) + np.asarray((0.25, 0.22, 0.2)) * flash * self.cl * 2
        img = img + (blur(self.bolt, 2)[..., None] * 3 + blur(self.bolt, 14)[..., None] * 2) * flash
        fx_ = 520; fy = self.cliff_y[fx_] - 3.75 * 64
        flap = math.sin(t * 7) * 0.6
        fig = figure_mask(H, W, fx_, fy, 64, dict(torso=-2, coat=3.3, flap=flap, la1=8, la2=6, ra1=-6, ra2=-4, front=True,
                                               ll1=4, ll2=3, rl1=-4, rl2=-3))
        sil = np.clip(self.cliff + fig, 0, 1)
        img = comp(img, sil, (0.006, 0.005, 0.004))
        img += (rim(fig, -1, 0, 4, 2) + rim(fig, 1, 0, 4, 2))[..., None] * np.asarray(WARM) * (1.2 + 2.5 * flash)
        img += streaks(H, W, 260, 2, t, angle=103, speed=2200, length=70, alpha=0.28)[..., None] * (0.7 + flash)
        img = bloom(img, 0.55, 30, 0.7)
        z = 1.0 + 0.06 * t / d
        return cam(img, z, W / 2, H * 0.47)


# 2 ─ Hourglass of gold sand (Not luck. Not time. Not tomorrow.)
class Hourglass:
    def __init__(self):
        self.base = np.zeros((H, W, 3), np.float32) + radial(H, W, W / 2, H * 0.45, 900, 2.5)[..., None] * np.asarray((0.15, 0.1, 0.05))
        self.cx, self.cy = W / 2, H * 0.45
        self.hh = 520

    def width(self, y):  # half width of glass at relative y in [-1,1]
        a = abs(y)
        return 22 + 300 * np.sin(np.clip(a, 0, 1) * math.pi * 0.5) ** 1.6 * (1 - 0.25 * a ** 6)

    def frame(self, t, d):
        img = self.base.copy()
        cx, cy, hh = self.cx, self.cy, self.hh
        ys = np.linspace(-1, 1, 400)
        wv = self.width(ys)
        left = np.stack([cx - wv, cy + ys * hh], 1); right = np.stack([cx + wv, cy + ys * hh], 1)
        glass = np.zeros((H, W), np.float32)
        cv2.polylines(glass, [left.astype(np.int32), right.astype(np.int32)], False, 1.0, 5, cv2.LINE_AA)
        # sand levels
        k = 0.35 + 0.25 * t / d
        sand = np.zeros((H, W), np.float32)
        top_level = -1 + 0.95 * (1 - k)  # top pile surface (relative)
        for yy in np.linspace(top_level, -0.04, 120):
            ww = self.width(yy) * 0.93
            dip = (1 - (yy - top_level) / (abs(top_level) + 1e-3))
            pass
        ys2 = np.linspace(top_level, -0.03, 200); ww = self.width(ys2) * 0.94
        poly = np.concatenate([np.stack([cx - ww, cy + ys2 * hh], 1), np.stack([cx + ww, cy + ys2 * hh], 1)[::-1]])
        poly[0, 1] += 0; cv2.fillPoly(sand, [poly.astype(np.int32)], 1.0, cv2.LINE_AA)
        # funnel dip on top surface
        cv2.ellipse(sand, (int(cx), int(cy + top_level * hh)), (int(self.width(top_level) * 0.94), 40), 0, 0, 180, 0.0, -1, cv2.LINE_AA)
        bl = 1 - 0.9 * k
        ys3 = np.linspace(bl, 0.97, 200); ww3 = self.width(ys3) * 0.94
        mound = np.stack([cx - ww3, cy + ys3 * hh], 1)
        poly = np.concatenate([[[cx, cy + (bl - 0.22) * hh]], np.stack([cx + ww3, cy + ys3 * hh], 1), mound[::-1]])
        cv2.fillPoly(sand, [poly.astype(np.int32)], 1.0, cv2.LINE_AA)
        cv2.line(sand, (int(cx), int(cy)), (int(cx), int(cy + (bl - 0.2) * hh)), 0.9, 6, cv2.LINE_AA)
        # falling grains
        r = rng(4); n = 120
        ph = r.uniform(0, 1, n); spd = r.uniform(0.6, 1.0, n)
        fall = ((ph + t * spd * 1.3) % 1)
        gx = cx + r.normal(0, 4, n) * fall * 3; gy = cy + fall * (bl - 0.2) * hh
        for i in range(n): cv2.circle(sand, (int(gx[i]), int(gy[i])), 2, 1.0, -1, cv2.LINE_AA)
        shade = 0.55 + 0.45 * fbm(H, W, 8, 5, 30)
        img += (sand * shade)[..., None] * np.asarray((1.2, 0.8, 0.32))
        img += blur(glass, 1.5)[..., None] * np.asarray((0.5, 0.42, 0.32)) + blur(glass, 18)[..., None] * 0.6 * np.asarray(GOLD)
        # frame bars + posts
        bars = np.zeros((H, W), np.float32)
        for sy in (-1, 1):
            y0 = cy + sy * (hh + 40)
            cv2.rectangle(bars, (int(cx - 400), int(y0 - 28)), (int(cx + 400), int(y0 + 28)), 1.0, -1, cv2.LINE_AA)
        for sx in (-1, 1):
            cv2.rectangle(bars, (int(cx + sx * 375 - 12), int(cy - hh - 20)), (int(cx + sx * 375 + 12), int(cy + hh + 20)), 1.0, -1)
        grad = np.linspace(0.3, 1.0, W)[None, :] ** 2
        img = comp(img, bars, (0, 0, 0)) + (bars * grad)[..., None] * np.asarray((0.9, 0.62, 0.25))
        img += bg_dust(t, 21, 70)[..., None] * np.asarray(GOLD) * 0.6
        img = bloom(img, 0.5, 30, 0.9)
        return cam(img, 1.12 - 0.08 * t / d, W / 2, H * 0.47, rot=-2 + 3 * t / d)


# 3 ─ Night city, one window lit (While they sleep, you build)
class City:
    def __init__(self, seed=31, golden=False):
        self.L = []
        r = rng(seed); LW, LH = int(W * 1.35), int(H * 1.35)
        self.LW, self.LH = LW, LH
        sky = vgrad(LH, LW, [(0, (0.0, 0.0, 0.0)), (0.55, (0.04, 0.03, 0.025)), (0.75, (0.16, 0.11, 0.06) if not golden else (0.5, 0.33, 0.12)), (1, (0.05, 0.04, 0.03))])
        self.sky = sky
        for li, (n, hmin, hmax, dim) in enumerate([(26, 300, 900, 0.25), (16, 500, 1300, 0.55), (9, 700, 1700, 1.0)]):
            col = np.zeros((LH, LW), np.float32); win = np.zeros((LH, LW), np.float32)
            xs = np.sort(r.uniform(-100, LW, n))
            for x in xs:
                bw = r.uniform(110, 260) * (1 + li * 0.3); bh = r.uniform(hmin, hmax)
                x0, y0 = int(x), int(LH - bh)
                cv2.rectangle(col, (x0, y0), (int(x0 + bw), LH), 1.0, -1)
                if r.random() < 0.3:
                    cv2.rectangle(col, (int(x0 + bw * 0.45), y0 - int(r.uniform(40, 160))), (int(x0 + bw * 0.52), y0), 1.0, -1)
                p = (0.08 if not golden else 0.35) + 0.04 * li
                for wy in range(y0 + 20, LH, 26 + li * 6):
                    for wx in range(x0 + 12, int(x0 + bw) - 12, 20 + li * 6):
                        if r.random() < p:
                            cv2.rectangle(win, (wx, wy), (wx + 8 + li * 3, wy + 12 + li * 3), float(r.uniform(0.3, 1.0)), -1)
            self.L.append((col, win, dim))
        self.hero = None
        if not golden:
            col, win, dim = self.L[2]
            x0 = LW // 2 - 150; y0 = int(LH * 0.13)
            cv2.rectangle(col, (x0, y0), (x0 + 300, LH), 1.0, -1)
            cv2.rectangle(col, (x0 + 140, y0 - 220), (x0 + 160, y0), 1.0, -1)
            win[y0:, x0:x0 + 300] = 0
            self.hero = (x0 + 190, y0 + 210)
        self.golden = golden

    def compose(self, t, pan):
        img = self.sky.copy()
        for li, (col, win, dim) in enumerate(self.L):
            shift = pan * (0.3 + 0.35 * li)
            c = np.roll(col, int(shift), 1); wn = np.roll(win, int(shift), 1)
            haze = (0.06, 0.045, 0.03) if not self.golden else (0.2, 0.13, 0.05)
            base = np.asarray(haze) * (1 - li * 0.4) + 0.005
            img = comp(img, c, base)
            img += (wn * dim)[..., None] * np.asarray((1.0, 0.7, 0.32)) * (0.8 if not self.golden else 1.3)
        return img

    def frame(self, t, d):
        img = self.compose(t, -30 * t)
        if self.hero:
            hx, hy = self.hero; hx += int(-30 * t * 1.0)
            cv2.rectangle(img, (hx, hy), (hx + 26, hy + 34), (3.0, 2.2, 1.2), -1)
            gl = radial(self.LH, self.LW, hx + 13, hy + 17, 160, 2.5)
            img += gl[..., None] * np.asarray(GOLD) * 1.2
        bok = particles(self.LH, self.LW, 40, 7, t, vel=(-20, 0), size=(8, 22), bright=(0.1, 0.45))
        img += blur(bok, 9)[..., None] * np.asarray(GOLD) * 1.8
        img = bloom(img, 0.45, 20, 0.8)
        cy = self.LH * (0.62 - 0.12 * ease(t / d))
        return cam(img, 1.0, self.LW / 2, cy)


# 4 ─ Climber on the ridge at sunrise (one more step)
class Climber:
    def __init__(self):
        LW = int(W * 1.3); self.LW = LW
        sky = vgrad(H, LW, [(0, (0.0, 0.0, 0.0)), (0.35, (0.1, 0.07, 0.04)), (0.6, (0.85, 0.55, 0.2)), (0.7, (1.0, 0.8, 0.45)), (1, (0.3, 0.2, 0.1))])
        sun = radial(H, LW, LW * 0.6, H * 0.62, 260, 1.5) * 2.5 + radial(H, LW, LW * 0.6, H * 0.62, 900, 2) * 0.8
        img = sky + sun[..., None] * np.asarray(WARM)
        for i, (y0, amp, sh) in enumerate([(1180, 220, 0.5), (1300, 260, 0.3), (1420, 200, 0.15)]):
            ys = y0 + amp * ridge(LW, 40 + i, 0.55)
            m = fill_below(H, LW, ys.astype(np.float32))
            img = comp(img, m, np.asarray((0.5, 0.33, 0.14)) * sh)
        xs = np.arange(LW)
        fg = 1900 - (xs / LW) * 950 + 30 * ridge(LW, 77, 0.5)
        self.fg_y = fg
        self.img = comp(img, fill_below(H, LW, fg.astype(np.float32)), (0.01, 0.008, 0.006))

    def frame(self, t, d):
        img = self.img.copy()
        ph = t * 2.2
        x = int(self.LW * 0.48 + t * 22); yb = self.fg_y[x]
        s = 40
        st = math.sin(ph)
        pose = dict(torso=24, head=-10, pack=True, ll1=-30 + 32 * st, ll2=-35 + 30 * st, rl1=-30 - 32 * st, rl2=-38 - 20 * st,
                    la1=-35 + 30 * st, la2=-60 + 20 * st, ra1=40 - 30 * st, ra2=20)
        fig = figure_mask(H, self.LW, x, yb - 7.0 * s + 6, s, pose)
        img = comp(img, fig, (0.005, 0.004, 0.003))
        img += rim(fig, -1, 0, 3, 1.5)[..., None] * np.asarray(WARM) * 2.0
        snow = streaks(H, self.LW, 220, 9, t, angle=170, speed=700, length=25, alpha=0.5)
        img += blur(snow, 1)[..., None] * np.asarray(WARM) * 0.8
        img = bloom(img, 0.7, 40, 0.9)
        return cam(img, 1.05 + 0.05 * t / d, self.LW * 0.5 + 40 * t, H * 0.52)


# 5 ─ Boxer & heavy bag in a dark gym (Discipline)
class Boxer:
    def __init__(self):
        self.base = vgrad(H, W, [(0, (0, 0, 0)), (0.8, (0.03, 0.025, 0.02)), (1, (0.06, 0.05, 0.04))])
        cone = np.zeros((H, W), np.float32)
        cv2.fillPoly(cone, [np.array([[W / 2 - 60, 0], [W / 2 + 60, 0], [W / 2 + 560, 1700], [W / 2 - 560, 1700]], np.int32)], 1.0)
        self.cone = blur(cone, 40) * vgrad(H, W, [(0, (1, 1, 1)), (1, (0.25, 0.25, 0.25))])[..., 0]
        self.floor = radial(H, W, W / 2, 1640, 600, 1.5) * 0.35

    def frame(self, t, d):
        img = self.base + (self.cone * 0.6)[..., None] * np.asarray(WARM)
        img += self.floor[..., None] * np.asarray(WARM)
        dust = particles(H, W, 220, 5, t * 0.35, vel=(5, -8), size=(1, 3), bright=(0.2, 1.0))
        img += (dust * self.cone)[..., None] * np.asarray(WARM) * 1.2
        # punch timing (slow motion)
        hits = [0.55, 1.75]
        ext = 0; bag_sw = 0
        for hT in hits:
            if hT - 0.35 < t < hT + 0.3: ext = max(ext, 1 - abs(t - hT) / 0.35)
            if t > hT: bag_sw += 9 * math.exp(-(t - hT) * 1.2) * math.sin((t - hT) * 3.2)
        # bag
        top = (W * 0.7, 380); ang = math.radians(bag_sw)
        L = 760; bc = (top[0] + math.sin(ang) * L, top[1] + math.cos(ang) * L)
        bag = np.zeros((H, W), np.float32)
        cv2.line(bag, (int(top[0]), 0), (int(top[0]), int(top[1])), 1.0, 6, cv2.LINE_AA)
        cv2.ellipse(bag, (int(bc[0]), int(bc[1] - 270)), (175, 380), -math.degrees(ang), 0, 360, 1.0, -1, cv2.LINE_AA)
        s = 72
        pose = dict(torso=10, head=-5, ll1=28, ll2=10, rl1=-22, rl2=-8,
                    la1=-110 * (0.4 + 0.6 * ext) - 20, la2=-95 - 10 * ext, ra1=-30, ra2=-150 + 0 * ext)
        pose['la1'] = -(40 + 50 * ext); pose['la2'] = -(150 - 60 * ext)
        pose['ra1'] = 30 - 10 * ext; pose['ra2'] = -150
        pose['la1'], pose['la2'] = (40 + 50 * ext) * -1 * -1, (150 - 60 * ext)
        fig = figure_mask(H, W, int(W * 0.3), 1700 - 3.75 * s, s, pose)
        sil = np.clip(fig + bag, 0, 1)
        img = comp(img, sil, (0.004, 0.003, 0.002))
        img += rim(sil, 0, 1, 4, 2)[..., None] * np.asarray(WARM) * 1.6
        img += (rim(fig, 1, 0, 3, 1.5) + rim(fig, -1, 0, 3, 1.5))[..., None] * np.asarray(GOLD) * 1.6
        # sweat burst on impact
        for hT in hits:
            if t > hT:
                r = rng(int(hT * 100)); n = 60; dt = t - hT
                ang2 = r.uniform(-1.2, 1.2, n); sp = r.uniform(80, 420, n)
                sw = np.zeros((H, W), np.float32)
                ox, oy = W * 0.55, 900
                for i in range(n):
                    px = ox + math.cos(ang2[i]) * sp[i] * dt * 0.6; py = oy + math.sin(ang2[i]) * sp[i] * dt * 0.6 + 200 * dt * dt
                    cv2.circle(sw, (int(px), int(py)), 3, 1.0 * math.exp(-dt * 1.5), -1, cv2.LINE_AA)
                img += blur(sw, 1)[..., None] * np.asarray(WARM) * 1.5
        img = bloom(img, 0.5, 25, 0.8)
        return cam(img, 1.04 + 0.08 * ease(t / d), W * 0.48, H * 0.52)


# 6 ─ Runner on an empty road at dawn (Motivation fades. Habits stay.)
class Runner:
    def __init__(self, side=False):
        self.side = side
        sky = vgrad(H, W, [(0, (0, 0, 0)), (0.3, (0.08, 0.05, 0.03)), (0.52, (0.9, 0.6, 0.25)), (0.56, (1, 0.85, 0.55)), (0.57, (0.05, 0.04, 0.03)), (1, (0.02, 0.02, 0.02))])
        sun = radial(H, W, W / 2, H * 0.55, 200, 1.2) * 3 + radial(H, W, W / 2, H * 0.55, 800, 2.5)
        self.sky = sky + sun[..., None] * np.asarray(WARM) * 0.9
        road = np.zeros((H, W), np.float32)
        hy = int(H * 0.565)
        cv2.fillPoly(road, [np.array([[W / 2 - 20, hy], [W / 2 + 20, hy], [W + 600, H], [-600, H]], np.int32)], 1.0, cv2.LINE_AA)
        self.road = road; self.hy = hy
        ys = np.arange(H, dtype=np.float32)[:, None]
        self.roadshade = np.clip((ys - hy) / (H - hy), 0, 1) ** 0.6

    def frame(self, t, d):
        hy = self.hy
        img = self.sky.copy()
        img = comp(img, self.road, (0.02, 0.018, 0.015))
        refl = self.road * np.clip(1 - self.roadshade * 2.2, 0, 1) * 0.6
        img += refl[..., None] * np.asarray(WARM)
        # dashes moving toward camera
        dash = np.zeros((H, W), np.float32)
        for k in range(14):
            z = ((k + t * 3.0) % 14) / 14
            y0 = hy + (H - hy) * z ** 2.2; y1 = hy + (H - hy) * min(1, (z + 0.035)) ** 2.2
            w0 = 2 + 26 * z ** 2.2
            cv2.fillPoly(dash, [np.array([[W / 2 - w0, y0], [W / 2 + w0, y0], [W / 2 + w0 * 1.2, y1], [W / 2 - w0 * 1.2, y1]], np.int32)], 1.0, cv2.LINE_AA)
        img += dash[..., None] * np.asarray(WARM) * 0.5
        ph = t * 4.2
        s = 92
        pose = run_pose(ph, lean=10) if self.side else dict(run_pose(ph, 6), front=True)
        if not self.side:
            p = run_pose(ph, 6)
            pose = dict(front=True, torso=0, head=0, ll1=0, ll2=0 + 0, rl1=0, rl2=0,
                        la1=18 + 25 * math.sin(ph), la2=-40 + 30 * math.sin(ph), ra1=-18 + 25 * math.sin(ph), ra2=40 + 30 * math.sin(ph))
            lift = max(0, math.sin(ph)); lift2 = max(0, -math.sin(ph))
            pose['ll2'] = 4 + 0 * lift; pose['rl2'] = -4
        bob = 12 * abs(math.sin(ph))
        fx_, fy = W / 2, 1500 - bob
        fig = figure_mask(H, W, fx_, fy, s, pose)
        if not self.side:
            # foreshortened legs: raise alternately
            fig2 = np.zeros_like(fig)
            l1 = 1.0 - 0.3 * max(0, math.sin(ph)); l2 = 1.0 - 0.3 * max(0, -math.sin(ph))
            for side, lv in ((1, l1), (-1, l2)):
                x = int(fx_ + side * 0.33 * s)
                cv2.line(fig2, (x, int(fy)), (x + side * 6, int(fy + 3.75 * s * lv)), 1.0, int(0.55 * s), cv2.LINE_AA)
            fig = np.clip(np.where(np.arange(H)[:, None] > fy, 0, fig) + fig2, 0, 1)
        img = comp(img, fig, (0.004, 0.003, 0.002))
        img += (rim(fig, 0, 1, 4, 2) + rim(fig, 1, 0, 3, 2) + rim(fig, -1, 0, 3, 2))[..., None] * np.asarray(WARM) * 2.2
        img += streaks(H, W, 60, 13, t, angle=90, speed=900, length=120, alpha=0.18)[..., None] * np.asarray(WARM)
        img = bloom(img, 0.65, 40, 1.0)
        return cam(img, 1.08 - 0.06 * t / d, W / 2, H * 0.52 + 6 * math.sin(ph * 2))


# 7a ─ Overhead press reps (You become what you repeat)
class Lifter:
    def __init__(self):
        self.bg = vgrad(H, W, [(0, (0, 0, 0)), (1, (0.04, 0.03, 0.02))]) + radial(H, W, W / 2, H * 0.38, 800, 1.3)[..., None] * np.asarray((0.95, 0.62, 0.25)) + radial(H, W, W / 2, H * 0.38, 260, 1.5)[..., None] * 0.8

    def frame(self, t, d):
        img = self.bg.copy()
        rep = 0.5 - 0.5 * math.cos(t * 2 * math.pi / 0.75)  # 0 down, 1 up
        s = 70
        up = rep
        # front view, arms: shoulder -> elbow -> hands holding bar
        a1 = 90 + 60 * up; a2 = 180 - 0 * up
        pose = dict(front=True, torso=0, la1=a1, la2=170 + 10 * up, ra1=-a1, ra2=-(170 + 10 * up), ll1=8, ll2=6, rl1=-8, rl2=-6)
        hipy = 1500
        fig = figure_mask(H, W, W / 2, hipy, s, pose)
        sh_y = hipy - 2.65 * s
        # hand height
        el_y = sh_y - math.cos(math.radians(180 - a1)) * 1.45 * s
        hand_y = el_y - 1.3 * s * 0.98
        bar = np.zeros((H, W), np.float32)
        cv2.line(bar, (W // 2 - 470, int(hand_y)), (W // 2 + 470, int(hand_y)), 1.0, 14, cv2.LINE_AA)
        for sx in (-1, 1):
            for k, (o, rr) in enumerate([(380, 150), (420, 130)]):
                cv2.rectangle(bar, (W // 2 + sx * o - 16, int(hand_y - rr)), (W // 2 + sx * o + 16, int(hand_y + rr)), 1.0, -1, cv2.LINE_AA)
        sil = np.clip(fig + bar, 0, 1)
        img = comp(img, sil, (0.004, 0.003, 0.002))
        img += (rim(sil, 0, 1, 4, 2) + rim(sil, 1, 0, 3, 2) + rim(sil, -1, 0, 3, 2))[..., None] * np.asarray(WARM) * 2.2
        img += bg_dust(t, 31, 120, vel=(0, -30))[..., None] * np.asarray(WARM) * 0.7
        img = bloom(img, 0.55, 30, 0.8)
        return cam(img, 1.0 + 0.1 * t / d, W / 2, H * 0.5)


# 7b ─ Day after day: sun arcs time-lapse (Every single day)
class Timelapse:
    def __init__(self):
        xs = np.arange(W)
        self.hz = 1250 + 60 * ridge(W, 61, 0.5)
        self.ground = fill_below(H, W, self.hz.astype(np.float32))

    def frame(self, t, d):
        cyc = t / d * 2.2
        a = (cyc % 1)
        sx = -100 + (W + 200) * a; sy = 1250 - 700 * math.sin(a * math.pi)
        day = math.sin(a * math.pi)
        sky = vgrad(H, W, [(0, (0.02, 0.015, 0.01)), (0.65, tuple(np.array((0.9, 0.6, 0.25)) * (0.2 + 0.8 * day))), (1, (0.1, 0.07, 0.04))])
        img = sky + radial(H, W, sx, sy, 180, 1.3)[..., None] * np.asarray(WARM) * 3 + radial(H, W, sx, sy, 700, 2)[..., None] * 0.6
        # stars at night edges
        st = particles(H, W, 120, 3, 0, vel=(0, 0), size=(1, 2), bright=(0.3, 1), flicker=False) * (1 - day) * 1.5
        img += st[..., None]
        cl = streaks(H, W, 30, 6, t, angle=0, speed=1200, length=400, alpha=0.25, thick=18)
        img += blur(cl, 12)[..., None] * np.asarray(GOLD) * day
        img = comp(img, self.ground, (0.006, 0.005, 0.004))
        fig = figure_mask(H, W, W * 0.5, self.hz[W // 2] - 7 * 22 + 4, 22, dict(front=True))
        img = comp(img, fig, (0, 0, 0))
        img = bloom(img, 0.7, 30, 0.8)
        return cam(img, 1.05, W / 2, H * 0.5)


# 8 ─ The mind: neural gold network in a head profile
class Mind:
    def __init__(self):
        m = np.zeros((H, W), np.uint8)
        cx, cy = W * 0.52, H * 0.42
        cv2.ellipse(m, (int(cx), int(cy)), (330, 380), -10, 0, 360, 255, -1, cv2.LINE_AA)
        face = np.array([[cx - 230, cy - 120], [cx - 330, cy + 20], [cx - 300, cy + 60], [cx - 345, cy + 150], [cx - 300, cy + 175],
                         [cx - 310, cy + 230], [cx - 285, cy + 260], [cx - 270, cy + 330], [cx - 180, cy + 380], [cx - 140, cy + 400],
                         [cx - 130, cy + 560], [cx + 230, cy + 560], [cx + 200, cy + 300], [cx + 260, cy + 100]], np.int32)
        cv2.fillPoly(m, [face], 255, cv2.LINE_AA)
        cv2.fillPoly(m, [np.array([[cx - 420, H], [cx - 150, cy + 520], [cx + 260, cy + 520], [cx + 560, H]], np.int32)], 255, cv2.LINE_AA)
        self.head = m.astype(np.float32) / 255
        r = rng(8); pts = []
        while len(pts) < 140:
            x, y = r.uniform(cx - 330, cx + 330), r.uniform(cy - 380, cy + 330)
            if self.head[int(y), int(x)] > 0.5 and ((x - cx) / 300) ** 2 + ((y - cy + 40) / 340) ** 2 < 1: pts.append((x, y))
        self.pts = np.array(pts)
        E = []
        for i in range(len(pts)):
            dd = np.linalg.norm(self.pts - self.pts[i], axis=1); nn = np.argsort(dd)[1:4]
            for j in nn:
                if i < j: E.append((i, j))
        self.E = E; o = np.array([cx - 60, cy - 20])
        self.order = np.linalg.norm(self.pts - o, axis=1); self.order /= self.order.max()
        self.bg = radial(H, W, W * 0.6, H * 0.4, 1000, 2)[..., None] * np.asarray((0.12, 0.08, 0.04))

    def frame(self, t, d):
        img = self.bg.copy()
        img = comp(img, self.head, (0.008, 0.006, 0.004))
        img += rim(self.head, 1, 0, 5, 2.5)[..., None] * np.asarray(GOLD) * 1.5
        grow = ease_out(t / (d * 0.8))
        net = np.zeros((H, W), np.float32); nodes = np.zeros((H, W), np.float32)
        for (i, j) in self.E:
            a = max(self.order[i], self.order[j])
            if a < grow:
                cv2.line(net, tuple(self.pts[i].astype(int)), tuple(self.pts[j].astype(int)), 0.6, 2, cv2.LINE_AA)
        for k, p in enumerate(self.pts):
            if self.order[k] < grow:
                pulse = 0.5 + 0.5 * math.sin(t * 6 + k)
                cv2.circle(nodes, tuple(p.astype(int)), 5, 0.6 + 0.6 * pulse, -1, cv2.LINE_AA)
        # traveling sparks
        r = rng(2)
        for e in r.choice(len(self.E), 30):
            i, j = self.E[e]; f = (t * 1.5 + e * 0.37) % 1
            if max(self.order[i], self.order[j]) < grow:
                p = self.pts[i] * (1 - f) + self.pts[j] * f
                cv2.circle(nodes, tuple(p.astype(int)), 4, 1.5, -1, cv2.LINE_AA)
        light = net + nodes
        img += (blur(light, 1)[..., None] * 1.6 + blur(light, 10)[..., None] * 1.2) * np.asarray(GOLD)
        img += bg_dust(t, 41, 80)[..., None] * np.asarray(GOLD) * 0.5
        img = bloom(img, 0.6, 30, 0.8)
        return cam(img, 1.0 + 0.1 * ease(t / d), W * 0.5, H * 0.46)


# 9a ─ Sprint (So train it)
class Sprint:
    def frame(self, t, d):
        img = vgrad(H, W, [(0, (0, 0, 0)), (0.6, (0.2, 0.13, 0.05)), (0.7, (0.06, 0.04, 0.02)), (1, (0.01, 0.01, 0.01))])
        img += streaks(H, W, 90, 17, t, angle=180, speed=2600, length=500, alpha=0.5, thick=3)[..., None] * np.asarray(GOLD)
        s = 84; ph = t * 5.5 + 1
        fig = figure_mask(H, W, W * 0.5, 1180 - 6 * abs(math.sin(ph)), s, run_pose(ph, lean=22))
        floor = fill_below(H, W, np.full(W, 1180 + 3.6 * s, np.float32))
        sil = np.clip(fig + floor, 0, 1)
        img = comp(img, sil, (0.004, 0.003, 0.002))
        img += rim(fig, -1, 0, 4, 2)[..., None] * np.asarray(WARM) * 2.0
        img = bloom(img, 0.5, 25, 0.8)
        return cam(img, 1.1, W / 2 + 40 * t, H * 0.52)


# 9b ─ Sparks from a blade (Sharpen it)
class Sparks:
    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + radial(H, W, W * 0.45, H * 0.45, 600, 2)[..., None] * np.asarray((0.25, 0.15, 0.05))
        blade = np.zeros((H, W), np.float32)
        a = math.radians(-28)
        cx, cy = W * 0.42, H * 0.45
        p1 = (cx - math.cos(a) * 700, cy - math.sin(a) * 700); p2 = (cx + math.cos(a) * 520, cy + math.sin(a) * 520)
        nx, ny = -math.sin(a), math.cos(a)
        poly = np.array([p1, p2, (p2[0] + nx * 60, p2[1] + ny * 60), (p1[0] + nx * 90, p1[1] + ny * 90)], np.int32)
        cv2.fillPoly(blade, [poly], 1.0, cv2.LINE_AA)
        img = comp(img, blade, (0.05, 0.04, 0.03))
        edge = np.zeros((H, W), np.float32)
        cv2.line(edge, tuple(map(int, p1)), tuple(map(int, p2)), 1.0, 3, cv2.LINE_AA)
        sweep = (t / d)
        hl = radial(H, W, p1[0] + (p2[0] - p1[0]) * sweep, p1[1] + (p2[1] - p1[1]) * sweep, 300, 1.5)
        img += (edge * (0.5 + 3 * hl))[..., None] * np.asarray(WARM)
        # sparks
        sp = np.zeros((H, W), np.float32); r = rng(5); n = 260
        born = r.uniform(-0.4, d, n); ang = r.uniform(-0.2, 1.6, n) + math.pi * 0.05; spd = r.uniform(500, 1500, n)
        ox, oy = cx + 120, cy + 60
        for i in range(n):
            age = t - born[i]
            if 0 < age < 0.9:
                def pos(a_):
                    return ox + math.cos(ang[i]) * spd[i] * a_, oy + math.sin(ang[i]) * spd[i] * a_ * 0.3 + 1400 * a_ * a_ - 300 * a_
                x1, y1 = pos(age); x0, y0 = pos(max(0, age - 0.03))
                cv2.line(sp, (int(x0), int(y0)), (int(x1), int(y1)), float(1.5 * (1 - age / 0.9)), 2, cv2.LINE_AA)
        img += (sp[..., None] * 1.5 + blur(sp, 8)[..., None] * 2) * np.asarray((1, 0.75, 0.35))
        img += radial(H, W, ox, oy, 120, 1.5)[..., None] * 2 * np.asarray(WARM)
        img = bloom(img, 0.5, 25, 1.0)
        return cam(img, 1.15 - 0.08 * t / d, W / 2, H * 0.47)


# 9c ─ Gold chess king (Own it)
class King:
    def __init__(self):
        prof = np.array([[0, 0], [260, 0], [260, 40], [220, 70], [230, 110], [170, 150], [130, 200], [110, 420], [95, 560], [150, 590],
                         [150, 625], [100, 650], [150, 760], [170, 800], [60, 820], [60, 870], [25, 870], [25, 900], [80, 900], [80, 945],
                         [25, 945], [25, 1010], [0, 1010]], np.float32)
        prof[:, 1] = 1010 - prof[:, 1]
        cx, by = W / 2, 1520
        poly = np.concatenate([np.stack([cx + prof[:, 0] * 0.85, by - 1010 * 0.85 + prof[:, 1] * 0.85], 1),
                               np.stack([cx - prof[::-1, 0] * 0.85, by - 1010 * 0.85 + prof[::-1, 1] * 0.85], 1)])
        m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [poly.astype(np.int32)], 1.0, cv2.LINE_AA)
        self.m = m
        xs = (np.arange(W) - cx) / 230.0
        shade = np.clip(np.cos(np.clip(xs, -1.4, 1.4) * 1.1), 0, 1)
        self.shade = np.repeat(shade[None, :], H, 0).astype(np.float32)
        self.cx = cx

    def frame(self, t, d):
        img = vgrad(H, W, [(0, (0, 0, 0)), (1, (0.03, 0.02, 0.01))]) + radial(H, W, W / 2, H * 0.5, 800, 2)[..., None] * np.asarray((0.18, 0.11, 0.04))
        # floor reflection
        img += radial(H, W, W / 2, 1540, 500, 2)[..., None] * 0.3 * np.asarray(GOLD)
        sweep = -1.2 + 2.4 * t / d
        spec = np.exp(-((np.arange(W) - self.cx) / 230.0 - sweep * 0.6) ** 2 * 18)[None, :]
        metal = (0.18 + 0.75 * self.shade ** 2 + 2.0 * spec) * self.m
        img = comp(img, self.m, (0, 0, 0)) + metal[..., None] * np.asarray((1.0, 0.7, 0.3))
        img += rim(self.m, 0, 1, 3, 1.5)[..., None] * np.asarray(WARM)
        img += bg_dust(t, 55, 100)[..., None] * np.asarray(GOLD) * 0.6
        img = bloom(img, 0.6, 30, 0.9)
        return cam(img, 1.15 - 0.1 * ease_out(t / d), W / 2, H * 0.5)


# 10a ─ Penthouse: man in suit above a golden city
class Penthouse:
    def __init__(self):
        self.city = City(seed=77, golden=True)

    def frame(self, t, d):
        c = self.city.compose(t, -10 * t)
        c = bloom(c, 0.5, 20, 0.9)
        out = cam(c, 1.0, self.city.LW / 2, self.city.LH * 0.66)
        img = out * 0.95
        # window frame mullions + floor
        fr = np.zeros((H, W), np.float32)
        for x in (60, 400, 720, 1040):
            cv2.rectangle(fr, (x - 14, 0), (x + 14, H), 1.0, -1)
        cv2.rectangle(fr, (0, 0), (W, 90), 1.0, -1)
        cv2.rectangle(fr, (0, 1560), (W, H), 1.0, -1)
        img = comp(img, fr, (0.006, 0.005, 0.004))
        img += (rim(fr, 0, 1, 3, 2) * 0.5)[..., None] * np.asarray(GOLD)
        img += (np.flipud(out) * fill_below(H, W, np.full(W, 1560, np.float32))[..., None]) * 0.12
        s = 64
        fig = figure_mask(H, W, W * 0.56, 1560 - 3.75 * s - 2, s, dict(front=True, la1=12, la2=-4, ra1=-12, ra2=4, ll1=5, ll2=2, rl1=-5, rl2=-2))
        img = comp(img, fig, (0.003, 0.002, 0.002))
        img += rim(fig, 0, 0.6, 3, 2)[..., None] * np.asarray(WARM) * 0.9
        return cam(img, 1.0 + 0.07 * t / d, W / 2, H * 0.5)


# 10b ─ Highway light trails at night (luxury / speed)
class Trails:
    def __init__(self):
        self.bg = vgrad(H, W, [(0, (0, 0, 0)), (0.35, (0.12, 0.08, 0.04)), (0.4, (0.02, 0.015, 0.01)), (1, (0.01, 0.01, 0.01))])

    def frame(self, t, d):
        img = self.bg.copy()
        vp = (W * 0.5, H * 0.38)
        tr = np.zeros((H, W, 3), np.float32)
        for lane, (x_end, col, dirn) in enumerate([(-500, (1, 0.25, 0.1), 1), (-100, (1, 0.25, 0.1), 1), (650, (1, 0.9, 0.7), -1), (1100, (1, 0.9, 0.7), -1), (1600, (1, 0.7, 0.35), -1)]):
            curve = []
            for u in np.linspace(0, 1, 80):
                x = vp[0] + (x_end - vp[0]) * u ** 1.4 + 120 * math.sin(u * 2.2) * (1 - u)
                y = vp[1] + (H + 200 - vp[1]) * u ** 1.8
                curve.append((x, y))
            curve = np.array(curve, np.int32)
            th = 6 + lane % 2 * 3
            layer = np.zeros((H, W), np.float32)
            cv2.polylines(layer, [curve], False, 1.0, th, cv2.LINE_AA)
            # moving pulses along trail
            mod = np.zeros((H, W), np.float32)
            for k in range(5):
                u = ((k / 5 + dirn * t * 0.5) % 1)
                p = curve[int(u * 79)]
                cv2.circle(mod, tuple(p), int(30 + 90 * u), 1.0, -1)
            layer = layer * (0.45 + blur(mod, 30) * 1.5)
            tr += layer[..., None] * np.asarray(col)
        img += blur(tr, 1.5) * 1.2 + blur(tr, 20) * 1.2
        img += radial(H, W, vp[0], vp[1], 500, 2)[..., None] * np.asarray(GOLD) * 0.8
        img = bloom(img, 0.6, 30, 0.8)
        return cam(img, 1.05 + 0.1 * t / d, W / 2, H * 0.5, rot=2 - 3 * t / d)


# 11 ─ Door of light (Stop waiting to feel ready)
class Door:
    def frame(self, t, d):
        img = np.zeros((H, W, 3), np.float32) + 0.01
        open_ = ease_out(t / 0.8)
        dw = 40 + 250 * open_; dh = 640
        cx, cy = W / 2, H * 0.4
        x0, x1, y0, y1 = cx - dw / 2, cx + dw / 2, cy - dh / 2, cy + dh / 2
        door = np.zeros((H, W), np.float32)
        cv2.rectangle(door, (int(x0), int(y0)), (int(x1), int(y1)), 1.0, -1)
        floor = np.zeros((H, W), np.float32)
        cv2.fillPoly(floor, [np.array([[x0, y1], [x1, y1], [x1 + 900, H], [x0 - 900, H]], np.int32)], 1.0, cv2.LINE_AA)
        floor = blur(floor, 30) * np.clip((np.arange(H)[:, None] - y1) / 900, 0, 1) ** 0.3 * vgrad(H, W, [(0, (1, 1, 1)), (1, (0.2, 0.2, 0.2))])[..., 0]
        rays = np.zeros((H, W), np.float32)
        r = rng(3)
        for k in range(16):
            a = r.uniform(-1.2, 1.2)
            cv2.line(rays, (int(cx), int(cy)), (int(cx + math.sin(a) * 2000), int(cy + math.cos(a) * 2000 - 400)), 0.25, int(r.uniform(10, 50)))
        rays = blur(rays, 25) * (0.6 + 0.4 * math.sin(t * 2))
        img += door[..., None] * 3.0 * np.asarray((1, 0.92, 0.75)) + blur(door, 60)[..., None] * 1.4 * np.asarray(GOLD)
        img += (floor * 0.9 * open_)[..., None] * np.asarray(GOLD) + rays[..., None] * open_ * np.asarray(GOLD)
        # figure walking toward the door (getting smaller)
        z = 0.3 * t / d
        s = 60 * (1 - z); fy = H * 0.8 - (H * 0.8 - y1) * z * 1.2 - 3.75 * s
        st = math.sin(t * 4)
        fig = figure_mask(H, W, cx + 20, fy, s, dict(front=True, la1=10 + 12 * st, la2=6 + 12 * st, ra1=-10 + 12 * st, ra2=-6 + 12 * st,
                                                    ll1=6 * st, ll2=6 * st, rl1=-6 * st, rl2=-6 * st))
        img = comp(img, fig, (0.003, 0.002, 0.002))
        img += rim(fig, 0, 0, 1, 3)[..., None] * 0.0
        img += (particles(H, W, 200, 9, t, vel=(4, -10), size=(1, 3), bright=(0.2, 1)) * (blur(door, 200) * 8 + floor))[..., None] * np.asarray(WARM)
        img = bloom(img, 0.7, 40, 1.0)
        return cam(img, 1.0 + 0.12 * ease(t / d), W / 2, H * 0.47)


# 12 ─ Summit victory with sun burst (Become the one who never stops)
class Summit:
    def __init__(self):
        LW, LH = int(W * 1.3), int(H * 1.3)
        self.LW, self.LH = LW, LH
        sky = vgrad(LH, LW, [(0, (0.03, 0.02, 0.01)), (0.4, (0.5, 0.32, 0.12)), (0.62, (1.0, 0.78, 0.4)), (1, (0.4, 0.26, 0.1))])
        self.sky = sky
        self.sun = (LW * 0.5, LH * 0.47)
        cl = fbm(LH, LW, 12, 6, 4)
        self.clouds = np.clip((cl - 0.45) * 3, 0, 1) * fill_below(LH, LW, np.full(LW, LH * 0.6, np.float32))
        xs = np.arange(LW)
        peak = LH * 0.62 + np.abs(xs - LW / 2) ** 1.25 * 0.9 + 25 * ridge(LW, 3, 0.55)
        self.peak_y = peak
        self.peak = fill_below(LH, LW, peak.astype(np.float32))
        yy, xx = np.mgrid[0:LH, 0:LW].astype(np.float32)
        self.ang = np.arctan2(yy - self.sun[1], xx - self.sun[0])
        self.dist = np.sqrt((yy - self.sun[1]) ** 2 + (xx - self.sun[0]) ** 2)

    def frame(self, t, d):
        img = self.sky.copy()
        rays = (0.5 + 0.5 * np.sin(self.ang * 18 + t * 0.6)) ** 6 * np.exp(-self.dist / 900)
        img += rays[..., None] * np.asarray(WARM) * 0.9
        img += (np.exp(-self.dist / 120) * 3 + np.exp(-self.dist / 500))[..., None] * np.asarray(WARM)
        img = comp(img, self.clouds * 0.9, (0.75, 0.52, 0.22))
        img = comp(img, self.peak, (0.012, 0.009, 0.006))
        x = int(self.LW / 2); s = 34
        raise_ = ease_out(t / 0.9)
        pose = dict(front=True, la1=20 + 140 * raise_, la2=40 + 130 * raise_, ra1=-(20 + 140 * raise_), ra2=-(40 + 130 * raise_), ll1=10, ll2=8, rl1=-10, rl2=-8)
        fig = figure_mask(self.LH, self.LW, x, self.peak_y[x] - 3.75 * s + 4, s, pose)
        img = comp(img, fig, (0.003, 0.002, 0.002))
        img += rim(fig, 0, 1, 2, 1.5)[..., None] * np.asarray(WARM) * 1.5
        # flare
        img = bloom(img, 0.7, 40, 1.0)
        z = 1.25 - 0.22 * ease(t / d)
        return cam(img, z, self.LW / 2, self.LH * 0.55 - 30 * t)


# 13 ─ BEYOND MIND end card
class EndCard:
    def __init__(self):
        from PIL import Image, ImageDraw, ImageFont
        def txt(s, font, spacing=0):
            f = font
            wts = [f.getbbox(c)[2] - f.getbbox(c)[0] for c in s]
            tw = sum(wts) + spacing * (len(s) - 1); bb = f.getbbox(s)
            im = Image.new('L', (int(tw + 40), int(bb[3] + 40)), 0); dr = ImageDraw.Draw(im); x = 20
            for c, w_ in zip(s, wts):
                dr.text((x, 10), c, font=f, fill=255); x += w_ + spacing
            return np.asarray(im).astype(np.float32) / 255
        cz = ImageFont.truetype('fonts/Cinzel.ttf', 170); cz.set_variation_by_name('Bold')
        mt = ImageFont.truetype('fonts/Montserrat.ttf', 40); mt.set_variation_by_name('SemiBold')
        self.t1 = txt('BEYOND', cz, 14); self.t2 = txt('MIND', cz, 40)
        self.tag = [txt(w, mt, 10) for w in ['THINK', 'BEYOND.', 'BECOME', 'MORE.']]
        self.emblem = np.zeros((H, W), np.float32)
        self.cx, self.cy = W // 2, 640

    def paste(self, img, m, cx, cy, color, alpha=1.0):
        h, w = m.shape; x0, y0 = int(cx - w / 2), int(cy - h / 2)
        reg = img[y0:y0 + h, x0:x0 + w]
        reg[:] = reg * (1 - m[..., None] * alpha) + m[..., None] * alpha * color

    def frame(self, t, d, tag_times=(1.27, 1.83, 2.63, 2.85)):
        img = np.zeros((H, W, 3), np.float32) + radial(H, W, W / 2, H * 0.45, 900, 2)[..., None] * np.asarray((0.1, 0.065, 0.025))
        img += particles(H, W, 140, 77, t, vel=(0, -40), spread=(8, 10), size=(1, 3), bright=(0.2, 0.9))[..., None] * np.asarray(GOLD) * 0.8
        cx, cy = self.cx, self.cy
        # emblem: circle draws on, peak inside
        prog = ease_out(t / 0.9)
        em = np.zeros((H, W), np.float32)
        cv2.ellipse(em, (cx, cy), (150, 150), -90, 0, 360 * prog, 1.0, 4, cv2.LINE_AA)
        if t > 0.3:
            k = ease_out((t - 0.3) / 0.6)
            pts = np.array([[cx - 95, cy + 60], [cx - 25, cy - 30], [cx + 5, cy + 5], [cx + 40, cy - 70], [cx + 105, cy + 60]], np.float32)
            n = max(2, int(len(pts) * k + 0.999)); cv2.polylines(em, [pts[:n].astype(np.int32)], False, 1.0, 5, cv2.LINE_AA)
            cv2.circle(em, (cx + 40, cy - 115), int(10 * k), 1.0, -1, cv2.LINE_AA)
        img += em[..., None] * np.asarray((1.0, 0.8, 0.42)) * 1.3 + blur(em, 12)[..., None] * np.asarray(GOLD)
        # wordmark with gold vertical gradient + shine sweep
        a = ease_out((t - 0.15) / 0.6)
        for m, yy, delay in ((self.t1, 930, 0.15), (self.t2, 1110, 0.3)):
            a = ease_out((t - delay) / 0.6)
            if a <= 0: continue
            h, w = m.shape
            grad = np.linspace(1.15, 0.55, h)[:, None, None] * np.asarray((1.0, 0.76, 0.36))
            xs = np.arange(w)[None, :]
            shine = np.exp(-((xs - (-300 + (w + 600) * ((t - 0.9) / 1.2))) / 60.0) ** 2)[..., None] * 1.5
            col = grad + shine * np.asarray(WARM)
            yo = int(yy + 30 * (1 - a))
            x0, y0 = int(W / 2 - w / 2), int(yo - h / 2)
            reg = img[y0:y0 + h, x0:x0 + w]
            reg[:] = reg * (1 - m[..., None] * a) + m[..., None] * a * col
        # thin rules
        if t > 0.8:
            k = ease_out((t - 0.8) / 0.6)
            cv2.line(img, (int(W / 2 - 330 * k), 1235), (int(W / 2 + 330 * k), 1235), (0.8, 0.6, 0.28), 2, cv2.LINE_AA)
        # tagline words synced with voice
        widths = [m.shape[1] for m in self.tag]; gap = 18
        tot = sum(widths) + gap * 3
        # two lines: THINK BEYOND. / BECOME MORE.
        rows = [(0, 1, 1320), (2, 3, 1400)]
        for i0, i1, yy in rows:
            tw = widths[i0] + widths[i1] + gap
            x = W / 2 - tw / 2
            for i in (i0, i1):
                m = self.tag[i]; a = ease_out((t - tag_times[i]) / 0.3)
                if a > 0:
                    self.paste(img, m, x + widths[i] / 2, yy, np.asarray((1, 0.93, 0.8)) if i % 2 == 0 else np.asarray((1.0, 0.75, 0.33)), a)
                x += widths[i] + gap
        img = bloom(img, 0.6, 25, 0.6)
        fade = min(1.0, (d - t) / 0.8)
        return cam(img, 1.0 + 0.03 * t / d, W / 2, H / 2) * max(fade, 0)
