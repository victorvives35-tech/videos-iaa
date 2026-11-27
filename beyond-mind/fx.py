"""Shared rendering helpers: noise, silhouettes, glow, grading, camera moves."""
import numpy as np, cv2, math

W, H = 1080, 1920
FPS = 30


def rng(seed):
    return np.random.default_rng(seed)


def fbm(h, w, seed, octaves=6, base=4):
    r = rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        g = r.random((max(2, int(n * h / max(h, w))) + 1, n + 1)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC); tot += amp; amp *= 0.5
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def vgrad(h, w, stops):
    """stops: list of (pos 0..1, (r,g,b))"""
    ys = np.linspace(0, 1, h)
    ps = [s[0] for s in stops]
    cols = np.stack([np.interp(ys, ps, [s[1][c] for s in stops]) for c in range(3)], -1)
    return np.repeat(cols[:, None, :], w, 1).astype(np.float32)


def radial(h, w, cx, cy, r, power=2.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return np.clip(1 - d, 0, 1) ** power


def ridge(n, seed, rough=0.55, octaves=8):
    r = rng(seed); y = np.zeros(n, np.float32); amp = 1.0
    for o in range(octaves):
        k = 2 ** (o + 1)
        pts = r.uniform(-1, 1, k + 1)
        y += amp * np.interp(np.linspace(0, k, n), np.arange(k + 1), pts)
        amp *= rough
    return y


def fill_below(h, w, ys):
    """mask = 1 below polyline ys (len w)"""
    yy = np.arange(h, dtype=np.float32)[:, None]
    return np.clip(yy - ys[None, :] + 0.5, 0, 1).astype(np.float32)


def blur(img, s):
    if s <= 0: return img
    k = int(s * 3) * 2 + 1
    return cv2.GaussianBlur(img, (k, k), s)


def bloom(img, thr=0.6, s=25, k=0.8):
    b = np.clip(img - thr, 0, None)
    small = cv2.resize(b, (b.shape[1] // 4, b.shape[0] // 4), interpolation=cv2.INTER_AREA)
    g = blur(small, s / 4) + 0.6 * blur(small, s / 1.5)
    g = cv2.resize(g, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return img + g * k


def cam(layer, zoom=1.0, cx=None, cy=None, rot=0.0, out=(W, H)):
    """crop/zoom/rotate layer around (cx,cy) in layer coords -> output size"""
    h, w = layer.shape[:2]
    if cx is None: cx = w / 2
    if cy is None: cy = h / 2
    s = zoom * max(out[0] / w, out[1] / h) if False else zoom
    M = cv2.getRotationMatrix2D((cx, cy), rot, s)
    M[0, 2] += out[0] / 2 - cx
    M[1, 2] += out[1] / 2 - cy
    return cv2.warpAffine(layer, M, out, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3


def comp(base, mask, color):
    m = mask[..., None] if mask.ndim == 2 else mask
    return base * (1 - m) + np.asarray(color, np.float32) * m


# ---------------- human silhouette ----------------

def _d(a):  # direction from angle measured from straight down, + = towards +x
    a = math.radians(a); return math.sin(a), math.cos(a)


def figure_mask(h, w, x, y, s, pose, ss=2):
    """Draw silhouette mask. (x,y)=hip, s = head-unit size (figure ~7.5 s tall).
    pose angles (deg, from down): torso (lean, 0 upright), head, la1/la2, ra1/ra2 (arms upper/fore),
    ll1/ll2, rl1/rl2 (legs thigh/shin). front=True widens torso. coat / pack / suit extras."""
    p = dict(torso=0, head=0, la1=10, la2=10, ra1=-10, ra2=-10, ll1=5, ll2=5, rl1=-5, rl2=-5,
             front=False, coat=0.0, pack=False, flap=0.0)
    p.update(pose)
    m = np.zeros((h * ss, w * ss), np.uint8)
    S = s * ss; X, Y = x * ss, y * ss

    def P(a, b): return (int(round(a)), int(round(b)))
    tdx, tdy = math.sin(math.radians(p['torso'])), -math.cos(math.radians(p['torso']))
    neck = (X + tdx * 3.0 * S, Y + tdy * 3.0 * S)
    sh = (X + tdx * 2.65 * S, Y + tdy * 2.65 * S)
    hd = _d(180 - p['torso'] - p['head'])
    head = (neck[0] - hd[0] * 0.75 * S, neck[1] - hd[1] * 0.75 * S)
    hd = (neck[0] + tdx * 0.8 * S, neck[1] + tdy * 0.8 * S)
    head = (hd[0] + math.sin(math.radians(p['head'])) * 0.1 * S, hd[1])
    # torso polygon
    nx, ny = -tdy, tdx
    shw = (0.85 if p['front'] else 0.55) * S
    hpw = (0.55 if p['front'] else 0.45) * S
    poly = np.array([[sh[0] + nx * shw, sh[1] + ny * shw], [sh[0] - nx * shw, sh[1] - ny * shw],
                     [X - nx * hpw, Y - ny * hpw], [X + nx * hpw, Y + ny * hpw]])
    cv2.fillPoly(m, [poly.astype(np.int32)], 255, cv2.LINE_AA)
    cv2.line(m, P(*sh), P(*neck), 255, int(0.42 * S), cv2.LINE_AA)
    cv2.ellipse(m, P(*head), (int(0.42 * S), int(0.5 * S)), p['torso'], 0, 360, 255, -1, cv2.LINE_AA)
    # coat (long, flapping)
    if p['coat'] > 0:
        f = p['flap']
        cpoly = np.array([[sh[0] + nx * shw * 1.05, sh[1] + ny * shw], [sh[0] - nx * shw * 1.05, sh[1] - ny * shw],
                          [X - nx * hpw * 1.4 - f * S * 0.6, Y + p['coat'] * S],
                          [X + nx * hpw * 1.5 + f * S * 0.2 - f * S * 0.9, Y + p['coat'] * S * (1 - 0.08 * f)]])
        cv2.fillPoly(m, [cpoly.astype(np.int32)], 255, cv2.LINE_AA)
    if p['pack']:
        pc = (sh[0] - nx * 0.0 - tdx * 0.9 * S - 0.55 * S * (1 if p['torso'] >= 0 else -1), sh[1] - tdy * 0.9 * S)
        cv2.ellipse(m, P(*pc), (int(0.55 * S), int(0.95 * S)), p['torso'], 0, 360, 255, -1, cv2.LINE_AA)
    # arms
    off = 0.62 * S if p['front'] else 0.0
    for side, a1, a2 in ((1, p['la1'], p['la2']), (-1, p['ra1'], p['ra2'])):
        so = (sh[0] + nx * off * side, sh[1] + ny * off * side)
        d1 = _d(a1); el = (so[0] + d1[0] * 1.45 * S, so[1] + d1[1] * 1.45 * S)
        d2 = _d(a2); hn = (el[0] + d2[0] * 1.3 * S, el[1] + d2[1] * 1.3 * S)
        cv2.line(m, P(*so), P(*el), 255, int(0.42 * S), cv2.LINE_AA)
        cv2.line(m, P(*el), P(*hn), 255, int(0.34 * S), cv2.LINE_AA)
        cv2.circle(m, P(*hn), int(0.21 * S), 255, -1, cv2.LINE_AA)
        cv2.circle(m, P(*so), int(0.24 * S), 255, -1, cv2.LINE_AA)
    # legs
    loff = 0.3 * S if p['front'] else 0.0
    for side, a1, a2 in ((1, p['ll1'], p['ll2']), (-1, p['rl1'], p['rl2'])):
        ho = (X + nx * loff * side, Y + ny * loff * side)
        d1 = _d(a1); kn = (ho[0] + d1[0] * 1.9 * S, ho[1] + d1[1] * 1.9 * S)
        d2 = _d(a2); an = (kn[0] + d2[0] * 1.85 * S, kn[1] + d2[1] * 1.85 * S)
        cv2.line(m, P(*ho), P(*kn), 255, int(0.58 * S), cv2.LINE_AA)
        cv2.line(m, P(*kn), P(*an), 255, int(0.44 * S), cv2.LINE_AA)
        cv2.circle(m, P(*kn), int(0.26 * S), 255, -1, cv2.LINE_AA)
        fdir = 1 if not p['front'] else 0.3 * side
        cv2.line(m, P(*an), P(an[0] + fdir * 0.55 * S, an[1] + 0.08 * S), 255, int(0.3 * S), cv2.LINE_AA)
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    return m.astype(np.float32) / 255.0


def rim(mask, dx, dy, width=3, s=2.0):
    sh = np.roll(np.roll(mask, int(dy * width), 0), int(dx * width), 1)
    r = np.clip(mask - sh, 0, 1)
    return blur(r, s)


def run_pose(ph, lean=14):
    s = math.sin(ph); c = math.cos(ph)
    t1 = 38 * s; t2 = -38 * s
    def shin(th, phase):
        return th - (25 + 60 * max(0.0, math.sin(phase + 1.9)))
    return dict(torso=lean, head=-6, ll1=t1, ll2=shin(t1, ph), rl1=t2, rl2=shin(t2, ph + math.pi),
                la1=-45 * s, la2=-45 * s + 95, ra1=45 * s, ra2=45 * s + 95)


# ---------------- particles ----------------

def particles(h, w, n, seed, t, vel=(0, -20), spread=(0, 0), size=(1, 3), bright=(0.3, 1.0), wrap=True, flicker=True):
    r = rng(seed)
    x0 = r.uniform(0, w, n); y0 = r.uniform(0, h, n)
    vx = vel[0] + r.normal(0, spread[0] + 1e-6, n); vy = vel[1] + r.normal(0, spread[1] + 1e-6, n)
    sz = r.uniform(*size, n); br = r.uniform(*bright, n); ph = r.uniform(0, 6.28, n)
    x = x0 + vx * t + 15 * np.sin(t * 0.7 + ph); y = y0 + vy * t
    if wrap: x %= w; y %= h
    img = np.zeros((h, w), np.float32)
    fl = (0.6 + 0.4 * np.sin(t * 3 + ph * 3)) if flicker else 1
    vals = br * fl
    for i in range(n):
        cv2.circle(img, (int(x[i] * 4), int(y[i] * 4)), max(1, int(sz[i] * 4)), float(vals[i] if np.ndim(vals) else vals), -1, cv2.LINE_AA, shift=2)
    return img


def streaks(h, w, n, seed, t, angle=100, speed=1800, length=60, alpha=0.35, thick=1):
    r = rng(seed); img = np.zeros((h, w), np.float32)
    a = math.radians(angle); dx, dy = math.cos(a), math.sin(a)
    x0 = r.uniform(-200, w + 200, n); y0 = r.uniform(0, h, n); sp = speed * r.uniform(0.7, 1.3, n)
    br = r.uniform(0.3, 1.0, n) * alpha
    for i in range(n):
        x = (x0[i] + dx * sp[i] * t) % (w + 400) - 200; y = (y0[i] + dy * sp[i] * t) % h
        cv2.line(img, (int(x), int(y)), (int(x - dx * length), int(y - dy * length)), float(br[i]), thick, cv2.LINE_AA)
    return img


# ---------------- grade ----------------
_stops = [(0.0, (0.0, 0.0, 0.0)), (0.18, (0.05, 0.035, 0.02)), (0.42, (0.33, 0.21, 0.08)),
          (0.68, (0.82, 0.58, 0.24)), (0.86, (1.0, 0.84, 0.52)), (1.0, (1.0, 0.97, 0.9))]
_xs = np.linspace(0, 1, 1024)
LUT = np.stack([np.interp(_xs, [s[0] for s in _stops], [s[1][c] for s in _stops]) for c in range(3)], -1).astype(np.float32)
_vig = None
_grain = None


def grade(img, mix=0.78):
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
        _vig = np.clip(1 - 0.75 * d ** 2.2, 0.12, 1)[..., None].astype(np.float32)
    img = np.clip(img, 0, None)
    l = img[..., 0] * 0.3 + img[..., 1] * 0.55 + img[..., 2] * 0.15
    l = l / (1 + 0.35 * l)  # soft tonemap
    l = np.clip(l * 1.2, 0, 1)
    g = LUT[(l * 1023).astype(np.int32)]
    tm = img / (1 + 0.35 * img)
    out = g * mix + np.clip(tm * 1.2, 0, 1) * (1 - mix)
    return out * _vig


def grain(img, fi, amt=0.045):
    global _grain
    if _grain is None:
        r = rng(99)
        _grain = [cv2.resize(r.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H)) for _ in range(6)]
    return img + _grain[fi % 6][..., None] * amt * (0.4 + 0.6 * (1 - img.mean(-1, keepdims=True)))
