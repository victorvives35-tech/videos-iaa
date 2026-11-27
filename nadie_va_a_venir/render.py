"""Render del vídeo (1920x1080 @30fps) a partir de timeline.json.
Uso: python3 render.py BUILD_DIR [n_procesos] [--preview SEG_INI SEG_FIN]
"""
import json, sys, subprocess, math, os
from pathlib import Path
from multiprocessing import Process
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(sys.argv[1])
NPROC = int(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 4
TL = json.load(open(OUT / "timeline.json"))
W, H, FPS = 1920, 1080, 30
W2, H2 = 960, 540
F_MAIN = "/opt/fonts/Anton.ttf"
F_SERIF = "/opt/fonts/CormorantGaramond.ttf"
WHITE = (242, 238, 230)
GOLD = (230, 178, 72)

# ------------------------------------------------------------------ utilidades
def periodic_noise(h, w, beta, seed):
    r = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    spec = (r.standard_normal((h, w)) + 1j * r.standard_normal((h, w))) / f ** beta
    spec[0, 0] = 0
    n = np.real(np.fft.ifft2(spec)); n -= n.min(); n /= n.max()
    return n.astype(np.float32)

YY, XX = np.mgrid[0:H2, 0:W2].astype(np.float32)
def radial(cx, cy, rx, ry=None):
    ry = ry or rx
    d = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2)
    return np.exp(-d ** 2).astype(np.float32)

def col(c): return np.array(c, np.float32)[None, None, :] / 255.0

# ------------------------------------------------------------------ placas base
def make_plates():
    P = {}
    base = np.zeros((H2, W2, 3), np.float32)
    P["void"] = base + radial(480, 300, 520, 340)[..., None] * col((22, 24, 30))
    P["dust"] = base + radial(480, 250, 600, 380)[..., None] * col((40, 48, 60)) + col((6, 7, 10))
    P["rays"] = base + radial(480, -40, 700, 500)[..., None] * col((80, 62, 38)) + col((7, 6, 6))
    P["stars"] = (base + (1 - YY / H2)[..., None] * col((10, 14, 30)) +
                  radial(650, 220, 380, 220)[..., None] * col((28, 22, 52)) + col((3, 4, 9)))
    P["rain"] = base + radial(480, 200, 650, 420)[..., None] * col((26, 40, 44)) + col((5, 8, 9))
    hz_y = 0.82 * H2
    sky = np.clip(1 - np.abs(YY - hz_y) / (H2 * 0.55), 0, 1) ** 2.2
    P["horizon"] = (base + sky[..., None] * col((70, 40, 22)) +
                    radial(480, hz_y, 300, 60)[..., None] * col((200, 120, 50)) +
                    radial(480, hz_y, 70, 18)[..., None] * col((255, 190, 110)) + col((4, 4, 7)))
    ground = (YY > hz_y)[..., None]
    P["horizon"] = np.where(ground, P["horizon"] * 0.18, P["horizon"])
    P["ember"] = base + radial(480, 620, 700, 330)[..., None] * col((90, 30, 10)) + col((6, 4, 4))
    P["title"] = base + radial(480, 270, 500, 260)[..., None] * col((70, 52, 24)) + col((4, 4, 5))
    P["chapter"] = base + radial(480, 270, 420, 220)[..., None] * col((38, 30, 18)) + col((3, 3, 4))
    return P

PLATES = make_plates()
FOG = periodic_noise(H2, W2 * 2, 1.25, 3)
FOG2 = periodic_noise(H2, W2 * 2, 1.0, 11)

# ángulo para los rayos de luz
SRC = (480.0, -160.0)
ANG = np.arctan2(XX - SRC[0], YY - SRC[1]).astype(np.float32)
RDIST = np.sqrt((XX - SRC[0]) ** 2 + (YY - SRC[1]) ** 2)
RFALL = (np.exp(-(RDIST / 620.0) ** 2)).astype(np.float32)

rng = np.random.default_rng(42)
def parts(n, **k): return {kk: (v(n) if callable(v) else v) for kk, v in k.items()}
DUST = dict(x=rng.uniform(0, W2, 160), y=rng.uniform(0, H2, 160), vx=rng.uniform(-6, 6, 160),
            vy=rng.uniform(-8, -1, 160), r=rng.uniform(0.6, 3.2, 160), ph=rng.uniform(0, 6.3, 160))
EMB = dict(x=rng.uniform(0, W2, 140), y=rng.uniform(0, H2, 140), vx=rng.uniform(-10, 10, 140),
           vy=rng.uniform(-60, -20, 140), r=rng.uniform(0.7, 2.4, 140), ph=rng.uniform(0, 6.3, 140))
STAR = dict(x=rng.uniform(0, W2, 420), y=rng.uniform(0, H2 * 0.95, 420), r=rng.uniform(0.3, 1.4, 420) ** 2,
            ph=rng.uniform(0, 6.3, 420), sp=rng.uniform(0.5, 3, 420))
RAIN = dict(x=rng.uniform(0, W2 * 1.3, 380), y=rng.uniform(0, H2, 380), v=rng.uniform(500, 900, 380),
            l=rng.uniform(8, 22, 380), a=rng.uniform(0.15, 0.6, 380))

VIG = None
def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
    return np.clip(1.0 - 0.75 * d ** 2.4, 0.12, 1)[..., None].astype(np.float32)

# ------------------------------------------------------------------ fondos animados
def fog_layer(T, speed, tex=FOG):
    off = int(T * speed) % (W2 * 2)
    idx = (np.arange(W2) + off) % (W2 * 2)
    return tex[:, idx]

def bg_frame(kind, T):
    img = PLATES[kind].copy()
    f1 = fog_layer(T, 9.0); f2 = fog_layer(T, -5.0, FOG2)
    fog = (0.6 * f1 + 0.4 * f2) ** 2.2
    fogc = {"void": (30, 32, 38), "dust": (55, 62, 74), "rays": (70, 58, 42), "stars": (30, 26, 60),
            "rain": (40, 56, 60), "horizon": (60, 38, 26), "ember": (80, 34, 16),
            "title": (60, 48, 28), "chapter": (40, 34, 26)}[kind]
    img += fog[..., None] * col(fogc) * (0.9 if kind != "void" else 0.6)

    layer = np.zeros((H2, W2, 3), np.float32)
    if kind in ("dust", "rays", "title", "chapter", "void", "horizon"):
        n = {"void": 50, "chapter": 70, "horizon": 70}.get(kind, 160)
        x = (DUST["x"][:n] + DUST["vx"][:n] * T + 8 * np.sin(T * 0.3 + DUST["ph"][:n])) % W2
        y = (DUST["y"][:n] + DUST["vy"][:n] * T) % H2
        a = 0.35 + 0.35 * np.sin(T * 0.8 + DUST["ph"][:n])
        c = (0.85, 0.82, 0.75) if kind not in ("title", "chapter", "rays") else (1.0, 0.8, 0.45)
        for xi, yi, ri, ai in zip(x, y, DUST["r"][:n], a):
            cv2.circle(layer, (int(xi), int(yi)), max(1, int(ri)), (c[0] * ai, c[1] * ai, c[2] * ai), -1, cv2.LINE_AA)
        layer = cv2.GaussianBlur(layer, (0, 0), 1.6)
    if kind in ("ember",):
        x = (EMB["x"] + EMB["vx"] * T + 15 * np.sin(T * 1.3 + EMB["ph"])) % W2
        y = (EMB["y"] + EMB["vy"] * T) % H2
        fl = 0.5 + 0.5 * np.sin(T * 6 + EMB["ph"] * 3)
        for xi, yi, ri, fi in zip(x, y, EMB["r"], fl):
            h = 1 - yi / H2
            a = (0.4 + 0.6 * fi) * (1 - 0.7 * h)
            cv2.circle(layer, (int(xi), int(yi)), max(1, int(ri)), (1.0 * a, 0.55 * a, 0.18 * a), -1, cv2.LINE_AA)
        layer = cv2.GaussianBlur(layer, (0, 0), 1.2) * 1.6 + cv2.GaussianBlur(layer, (0, 0), 6) * 2.5
    if kind == "stars":
        tw = 0.55 + 0.45 * np.sin(T * STAR["sp"] + STAR["ph"])
        xs = (STAR["x"] + T * 2.0) % W2
        for xi, yi, ri, ai in zip(xs, STAR["y"], STAR["r"], tw):
            v = min(1.0, 0.5 * ai * (0.5 + ri))
            cv2.circle(layer, (int(xi), int(yi)), 1 if ri < 1.2 else 2, (v * 0.9, v * 0.93, v), -1, cv2.LINE_AA)
        layer = cv2.GaussianBlur(layer, (0, 0), 0.7) * 1.4
    if kind == "rain":
        x0 = (RAIN["x"] - 0.25 * RAIN["v"] * T) % (W2 * 1.3)
        y0 = (RAIN["y"] + RAIN["v"] * T) % (H2 + 40) - 20
        for xi, yi, li, ai in zip(x0, y0, RAIN["l"], RAIN["a"]):
            cv2.line(layer, (int(xi), int(yi)), (int(xi - 0.25 * li), int(yi + li)),
                     (0.55 * ai, 0.68 * ai, 0.72 * ai), 1, cv2.LINE_AA)
        layer = cv2.GaussianBlur(layer, (0, 0), 0.6)
    if kind in ("rays", "title"):
        ph = T * 0.07
        rays = (np.cos(9 * ANG + ph) * 0.5 + np.cos(23 * ANG - ph * 1.7) * 0.3 +
                np.cos(41 * ANG + ph * 2.3) * 0.2)
        rays = np.clip(rays, 0, None) ** 1.5 * RFALL * (0.75 + 0.25 * math.sin(T * 0.5))
        img += rays[..., None] * col((150, 115, 70)) * (0.75 if kind == "rays" else 0.45)
    if kind == "horizon":
        img += radial(480, 0.82 * H2, 300, 40)[..., None] * col((90, 55, 25)) * (0.5 + 0.2 * math.sin(T * 0.4))
    img += layer
    return img

def camera(img, T):
    s = 1.06 + 0.035 * math.sin(T / 19.0)
    dx = 18 * math.sin(T / 23.0); dy = 10 * math.sin(T / 29.0 + 1)
    M = np.float32([[s, 0, (1 - s) * W2 / 2 + dx], [0, s, (1 - s) * H2 / 2 + dy]])
    return cv2.warpAffine(img, M, (W2, H2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ------------------------------------------------------------------ texto
_font_cache = {}
def font(path, size):
    k = (path, size)
    if k not in _font_cache: _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]

def parse_words(line):
    """'NI TUS *PADRES*' -> [('NI',False),('TUS',False),('PADRES',True)]"""
    out, gold = [], False
    for w in line.split(" "):
        if not w: continue
        st = w.startswith("*"); en = w.endswith("*") and len(w) > 1
        if st: gold = True
        out.append((w.strip("*"), gold))
        if en: gold = False
    return out

def word_sprite(text, size, color, glow=True):
    f = font(F_MAIN, size)
    bb = f.getbbox(text)
    pad = int(size * 0.5)
    w, h = bb[2] - bb[0] + 2 * pad, int(size * 1.35) + 2 * pad
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((pad - bb[0], pad), text, font=f, fill=255)
    a = np.asarray(im, np.float32) / 255.0
    g = np.asarray(im.filter(ImageFilter.GaussianBlur(size * 0.18)), np.float32) / 255.0
    sh = np.asarray(im.filter(ImageFilter.GaussianBlur(size * 0.08)), np.float32) / 255.0
    return dict(a=a, glow=g, shadow=sh, color=np.array(color, np.float32) / 255.0, w=w, h=h, pad=pad,
                adv=f.getlength(text), gold=(color == GOLD))

def layout_text(onscreen, big=False):
    lines = [parse_words(l) for l in onscreen.split("|")]
    longest = max(sum(len(w) for w, _ in l) + len(l) for l in lines)
    nwords = sum(len(l) for l in lines)
    if nwords == 1: size = 300
    else: size = int(np.clip(2400 / (longest * 0.55 + 4), 105, 200))
    if big: size = int(size * 1.1)
    # ajusta para que la línea más ancha no supere 1640 px
    while True:
        f = font(F_MAIN, size); sp = f.getlength(" ") * 1.05
        widths = [sum(f.getlength(w) for w, _ in l) + sp * (len(l) - 1) for l in lines]
        if max(widths) <= 1640 or size < 60: break
        size -= 6
    lh = int(size * 1.08)
    total_h = lh * len(lines)
    y0 = H / 2 - total_h / 2 - size * 0.06
    words = []
    for li, l in enumerate(lines):
        x = W / 2 - widths[li] / 2
        for w, g in l:
            spr = word_sprite(w, size, GOLD if g else WHITE)
            words.append(dict(spr=spr, x=x - spr["pad"], y=y0 + li * lh - spr["pad"] - size * 0.12))
            x += spr["adv"] + sp
    return words, size

def blit_words(frame, words, T, t_in, t_span, t_out_end, fade_out=0.45, rise=14):
    n = len(words)
    for k, wd in enumerate(words):
        ts = t_in + (k / max(1, n)) * t_span
        a = np.clip((T - ts) / 0.45, 0, 1)
        a = a * a * (3 - 2 * a)
        a *= np.clip((t_out_end - T) / fade_out, 0, 1)
        if a <= 0.003: continue
        s = wd["spr"]
        oy = (1 - a) * rise
        x0, y0 = int(round(wd["x"])), int(round(wd["y"] + oy))
        x1, y1 = x0 + s["w"], y0 + s["h"]
        cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if cx1 <= cx0 or cy1 <= cy0: continue
        sl = (slice(cy0 - y0, cy1 - y0), slice(cx0 - x0, cx1 - x0))
        reg = frame[cy0:cy1, cx0:cx1]
        sh = s["shadow"][sl][..., None] * 0.75 * a
        reg *= (1 - sh)
        gcol = s["color"] * (0.9 if s["gold"] else 0.5)
        reg += s["glow"][sl][..., None] * gcol * (0.55 if s["gold"] else 0.22) * a
        al = s["a"][sl][..., None] * a
        reg[:] = reg * (1 - al) + s["color"] * al

def label_sprite(text, size, color, spacing=0.35):
    f = font(F_SERIF, size)
    chars = list(text); sp = size * spacing
    wtot = sum(f.getlength(c) for c in chars) + sp * (len(chars) - 1)
    pad = 20
    im = Image.new("L", (int(wtot) + 2 * pad, int(size * 1.5) + 2 * pad), 0)
    d = ImageDraw.Draw(im); x = pad
    for c in chars:
        d.text((x, pad), c, font=f, fill=255); x += f.getlength(c) + sp
    a = np.asarray(im, np.float32) / 255.0
    return a, np.array(color, np.float32) / 255.0

# ------------------------------------------------------------------ bloques
ITEMS = TL["items"]
for i, it in enumerate(ITEMS):
    it["seg_end"] = ITEMS[i + 1]["start"] if i + 1 < len(ITEMS) else TL["total"]
    it["bgk"] = "chapter" if it["kind"] == "chapter" else it["bg"]

_cache = {}
def block_assets(i):
    if i in _cache: return _cache[i]
    it = ITEMS[i]
    if it["kind"] == "chapter":
        lab = label_sprite(it["num"], 46, GOLD)
        # el título del capítulo un poco más pequeño y desplazado hacia abajo
        words, size = layout_text(it["title"])
        for wd in words: wd["y"] += 40
        _cache[i] = dict(label=lab, words=words, size=size)
    elif it["kind"] == "title":
        words, size = layout_text(it["onscreen"], big=True)
        _cache[i] = dict(words=words, size=size)
    else:
        words, size = layout_text(it["onscreen"]) if it["onscreen"] else ([], 0)
        _cache[i] = dict(words=words, size=size)
    if len(_cache) > 6: _cache.pop(next(iter(_cache)))
    return _cache[i]

def block_at(T):
    for i, it in enumerate(ITEMS):
        if it["start"] <= T < it["seg_end"]: return i
    return 0 if T < ITEMS[0]["start"] else len(ITEMS) - 1

GRAIN = None
def render_frame(fi):
    global VIG, GRAIN
    if VIG is None:
        VIG = vignette()
        g = np.random.default_rng(5)
        GRAIN = [cv2.GaussianBlur(g.standard_normal((H, W)).astype(np.float32), (0, 0), 0.7)[..., None]
                 for _ in range(6)]
    T = fi / FPS
    i = block_at(T); it = ITEMS[i]
    bg = bg_frame(it["bgk"], T)
    # fundido de fondo con el bloque anterior si cambia
    if i > 0 and ITEMS[i - 1]["bgk"] != it["bgk"]:
        x = (T - it["start"]) / 0.9
        if x < 1:
            x = x * x * (3 - 2 * x)
            bg = bg * x + bg_frame(ITEMS[i - 1]["bgk"], T) * (1 - x)
    bg = camera(bg, T)
    frame = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR)

    A = block_assets(i)
    if it["kind"] == "line" and A["words"]:
        span = min(it["voice_dur"] * 0.55, 0.32 * len(A["words"]) + 0.2)
        blit_words(frame, A["words"], T, it["start"] + 0.05, span, it["end"] - 0.05)
    elif it["kind"] == "title":
        blit_words(frame, A["words"], T, it["start"] + 0.3, 1.2, it["end"] - 0.1, fade_out=0.9, rise=30)
    elif it["kind"] == "chapter":
        t0, t1 = it["start"], it["end"]
        a = np.clip((T - t0 - 0.3) / 0.7, 0, 1) * np.clip((t1 - T) / 0.8, 0, 1)
        la, lc = A["label"]
        lh, lw = la.shape
        cy = int(H / 2 - A["size"] * 0.9); cx = int(W / 2 - lw / 2)
        reg = frame[cy:cy + lh, cx:cx + lw]
        reg[:] = reg * (1 - la[..., None] * a) + lc * la[..., None] * a
        # línea dorada que se expande
        g = np.clip((T - t0 - 0.5) / 1.2, 0, 1); g = g * g * (3 - 2 * g)
        half = int(260 * g)
        if half > 2:
            ly = cy + lh + 6
            cv2.line(frame, (W // 2 - half, ly), (W // 2 + half, ly),
                     tuple(float(c) * float(a) * 0.8 for c in np.array(GOLD) / 255.0), 2, cv2.LINE_AA)
        blit_words(frame, A["words"], T, t0 + 0.8, 0.6, t1 - 0.1, fade_out=0.8, rise=20)

    # fundidos a negro: inicio, final, y alrededor de capítulos
    k = 1.0
    k *= np.clip(T / 1.5, 0, 1)
    k *= np.clip((TL["total"] - T) / 2.5, 0, 1)
    for it2 in ITEMS:
        if it2["kind"] in ("chapter", "title"):
            d = T - it2["start"]
            if -0.6 < d <= 0: k *= 0.08 + 0.92 * (-d / 0.6)
            elif 0 < d < 0.5: k *= 0.08 + 0.92 * (d / 0.5)
    frame *= VIG
    # gradación: sombras frías, luces cálidas
    lum = frame.mean(axis=2, keepdims=True)
    frame += (1 - lum) * np.float32([-0.004, 0.003, 0.012]) + lum * np.float32([0.03, 0.012, -0.02])
    frame = frame * k
    frame += GRAIN[fi % 6] * 0.022
    return (np.clip(frame, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)

# ------------------------------------------------------------------ main
def worker(a, b, path):
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-tune", "film", str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(a, b):
        p.stdin.write(render_frame(fi).tobytes())
        if (fi - a) % 600 == 0: print(f"[{path.name}] {fi - a}/{b - a}", flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    total_f = int(TL["total"] * FPS)
    if "--preview" in sys.argv:
        k = sys.argv.index("--preview")
        a, b = int(float(sys.argv[k + 1]) * FPS), int(float(sys.argv[k + 2]) * FPS)
        worker(a, b, OUT / "preview.mp4"); sys.exit()
    if "--stills" in sys.argv:
        k = sys.argv.index("--stills")
        for s in sys.argv[k + 1:]:
            Image.fromarray(render_frame(int(float(s) * FPS))).save(OUT / f"still_{s}.jpg", quality=90)
        sys.exit()
    bounds = np.linspace(0, total_f, NPROC + 1).astype(int)
    procs = []
    for j in range(NPROC):
        p = Process(target=worker, args=(bounds[j], bounds[j + 1], OUT / f"part{j}.mp4")); p.start()
        procs.append(p)
    for p in procs: p.join()
    with open(OUT / "parts.txt", "w") as f:
        for j in range(NPROC): f.write(f"file 'part{j}.mp4'\n")
    print("render terminado")
