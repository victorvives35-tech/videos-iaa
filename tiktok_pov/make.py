# -*- coding: utf-8 -*-
"""Vídeo vertical POV animado: voces (Kokoro), animación 2D procedural, subtítulos TikTok y sonido."""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from historia import LINEAS, VOCES, TITULO

WORK = os.environ["WORK"]
OUTD = os.path.join(WORK, "pov"); os.makedirs(OUTD, exist_ok=True)
FONTS = os.path.join(WORK, "fonts")
W, H, FPS, SR = 1080, 1920, 30, 24000
LEAD, GAP, TAIL = 0.6, 0.35, 2.2

# ------------------------------------------------------------------ voces
from kokoro_onnx import Kokoro
import soundfile as sf
K = Kokoro(os.path.join(WORK, "kokoro", "kokoro-v1.0.onnx"), os.path.join(WORK, "kokoro", "voices-v1.0.bin"))
segs, t, voice = [], LEAD, [np.zeros(int(LEAD * SR), np.float32)]
for i, (who, scene, txt) in enumerate(LINEAS):
    p = os.path.join(OUTD, f"l{i:02d}.wav")
    if not os.path.exists(p):
        v, sp = VOCES[who]
        a, sr = K.create(txt.replace("Marcos", "Márcos"), voice=v, speed=sp, lang="es")
        sf.write(p, a, sr)
    a, _ = sf.read(p, dtype="float32")
    nz = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, nz[0] - 200):nz[-1] + 1200]
    if who == "A":   # altavoz: filtro telefónico + eco
        a = signal.sosfilt(signal.butter(2, [400, 3200], "bandpass", fs=SR, output="sos"), a) * 1.6
        d = int(0.18 * SR); a = np.concatenate([a, np.zeros(d)]); a[d:] += a[:-d] * 0.4
    if who == "C":
        a = a * 1.0
    d = len(a) / SR
    segs.append(dict(who=who, scene=scene, text=txt, start=t, end=t + d))
    voice += [a.astype(np.float32), np.zeros(int(GAP * SR), np.float32)]
    t += d + GAP
D = t + TAIL
voice.append(np.zeros(int(TAIL * SR), np.float32))
voice = np.concatenate(voice)
win = int(SR / FPS)
env = np.array([np.sqrt(np.mean(voice[i * win:(i + 1) * win] ** 2)) for i in range(int(D * FPS) + 2)])
env = np.clip(env / (np.percentile(env[env > 0.005], 90) + 1e-9), 0, 1)
json.dump(segs, open(os.path.join(OUTD, "segs.json"), "w"), ensure_ascii=False, indent=1)
print(f"duración {D:.1f}s")


def seg_at(tt):
    for s in segs:
        if s["start"] - GAP / 2 <= tt < s["end"] + GAP / 2:
            return s
    return segs[-1] if tt >= segs[-1]["start"] else segs[0]


# ------------------------------------------------------------------ dibujo
def grad(stops, w=W, h=H):
    pos = [s[0] for s in stops]; cols = np.array([s[1] for s in stops], np.float32)
    y = np.linspace(0, 1, h)
    c = np.stack([np.interp(y, pos, cols[:, i]) for i in range(3)], 1)
    return Image.fromarray(np.repeat(c[:, None, :], w, 1).astype(np.uint8)).convert("RGBA")


def glow(img, x, y, r, col, a):
    s = Image.new("RGBA", (int(2 * r), int(2 * r)))
    yy, xx = np.mgrid[-r:r, -r:r]
    al = np.clip(1 - np.sqrt(xx ** 2 + yy ** 2) / r, 0, 1) ** 2 * 255 * a
    arr = np.zeros((s.size[1], s.size[0], 4), np.uint8)
    arr[..., :3] = col; arr[..., 3] = al[:s.size[1], :s.size[0]]
    img.alpha_composite(Image.fromarray(arr), (int(x - r), int(y - r))) if x - r >= 0 and y - r >= 0 else None


CH = {
    "N": dict(skin=(246, 200, 160), hair=(70, 45, 30), top=(40, 110, 220), hood=False, cap=False),
    "G": dict(skin=(236, 185, 150), hair=(30, 20, 30), top=(110, 60, 160), hood=True, cap=False),
    "C": dict(skin=(214, 160, 120), hair=(90, 90, 90), top=(70, 80, 90), hood=False, cap=True),
}


def character(d, who, x, y, s, mouth=0.0, blink=False, look=0.0, pale=False, shock=False, wave_=0.0, arm=None):
    c = CH[who]
    skin = c["skin"] if not pale else (225, 228, 230)
    top = c["top"]
    # cuerpo
    d.rounded_rectangle([x - 0.62 * s, y + 0.55 * s, x + 0.62 * s, y + 2.1 * s], int(0.35 * s), fill=top)
    if c["hood"]:
        d.ellipse([x - 0.78 * s, y - 0.95 * s, x + 0.78 * s, y + 0.85 * s], fill=top)
    # brazos
    if wave_:
        ang = -1.2 + math.sin(wave_) * 0.35
        hx, hy = x + 0.55 * s + math.cos(ang) * 0.9 * s, y + 0.8 * s + math.sin(ang) * 0.9 * s
        d.line([(x + 0.5 * s, y + 0.85 * s), (hx, hy)], fill=top, width=int(0.24 * s))
        d.ellipse([hx - 0.15 * s, hy - 0.15 * s, hx + 0.15 * s, hy + 0.15 * s], fill=skin)
    if arm:
        ax, ay = arm
        d.line([(x - 0.5 * s, y + 0.9 * s), (ax, ay)], fill=top, width=int(0.24 * s))
        d.ellipse([ax - 0.16 * s, ay - 0.16 * s, ax + 0.16 * s, ay + 0.16 * s], fill=skin)
    # cabeza
    d.ellipse([x - 0.6 * s, y - 0.7 * s, x + 0.6 * s, y + 0.6 * s], fill=skin)
    if c["hood"]:
        d.chord([x - 0.72 * s, y - 0.88 * s, x + 0.72 * s, y + 0.2 * s], 180, 360, fill=mix(top, (0, 0, 0), 0.15))
        d.polygon([(x - 0.6 * s, y - 0.3 * s), (x - 0.4 * s, y + 0.1 * s), (x - 0.62 * s, y + 0.5 * s)], fill=c["hair"])
        d.polygon([(x + 0.6 * s, y - 0.3 * s), (x + 0.4 * s, y + 0.1 * s), (x + 0.62 * s, y + 0.5 * s)], fill=c["hair"])
    elif c["cap"]:
        d.chord([x - 0.62 * s, y - 0.85 * s, x + 0.62 * s, y + 0.1 * s], 180, 360, fill=(30, 40, 60))
        d.rectangle([x - 0.62 * s, y - 0.4 * s, x + 0.95 * s, y - 0.3 * s], fill=(25, 32, 50))
    else:
        d.chord([x - 0.63 * s, y - 0.78 * s, x + 0.63 * s, y + 0.15 * s], 180, 360, fill=c["hair"])
        d.polygon([(x - 0.4 * s, y - 0.45 * s), (x + 0.1 * s, y - 0.25 * s), (x - 0.1 * s, y - 0.5 * s)], fill=c["hair"])
    # ojos
    er = 0.17 * s * (1.35 if shock else 1)
    for sx in (-1, 1):
        ex, ey = x + sx * 0.24 * s, y - 0.05 * s
        if blink and not shock:
            d.line([(ex - er, ey), (ex + er, ey)], fill=(30, 20, 20), width=max(2, int(0.05 * s)))
        else:
            d.ellipse([ex - er, ey - er * 1.15, ex + er, ey + er * 1.15], fill=(255, 255, 255))
            pr = er * (0.45 if shock else 0.55)
            px = ex + look * er * 0.4
            d.ellipse([px - pr, ey - pr, px + pr, ey + pr], fill=(25, 20, 30))
            d.ellipse([px - pr * 0.3 + pr * 0.3, ey - pr * 0.6, px + pr * 0.2 + pr * 0.3, ey - pr * 0.1], fill=(255, 255, 255))
        by = ey - er * 1.6
        tilt = 0.12 * s if who == "C" else (-0.06 * s if shock else 0)
        d.line([(ex - er, by + sx * tilt * 0.5), (ex + er, by - sx * tilt * 0.5)], fill=(40, 30, 30), width=max(2, int(0.055 * s)))
    if who == "C":
        d.chord([x - 0.32 * s, y + 0.12 * s, x + 0.32 * s, y + 0.42 * s], 180, 360, fill=(70, 70, 70))
    # boca
    mw = 0.2 * s; mh = 0.03 * s + mouth * 0.22 * s
    my = y + 0.33 * s
    if shock:
        d.ellipse([x - 0.12 * s, my - 0.05 * s, x + 0.12 * s, my + 0.22 * s], fill=(90, 30, 40))
    elif mouth > 0.08:
        d.ellipse([x - mw / 1.4, my - mh / 2, x + mw / 1.4, my + mh / 2], fill=(110, 35, 45))
    else:
        d.arc([x - mw, my - 0.1 * s, x + mw, my + 0.08 * s], 20, 160, fill=(80, 40, 40), width=max(2, int(0.04 * s)))
    if shock:
        d.ellipse([x + 0.48 * s, y - 0.45 * s, x + 0.62 * s, y - 0.22 * s], fill=(140, 200, 255))


def mix(a, b, u):
    return tuple(int(x + (y - x) * u) for x, y in zip(a, b))


rng = np.random.default_rng(3)
STARS = [(rng.uniform(0, W), rng.uniform(0, H * 0.4)) for _ in range(70)]
STREET = [(rng.uniform(0, 3000), rng.uniform(0.15, 0.5), rng.choice(3)) for _ in range(40)]
NEON = [(255, 70, 170), (80, 220, 255), (255, 170, 60)]


def night_window(img, box, t, speed=600):
    """Ventana del bus con la ciudad nocturna pasando."""
    x0, y0, x1, y1 = box
    win = grad([(0, (10, 10, 30)), (1, (40, 20, 60))], int(x1 - x0), int(y1 - y0))
    d = ImageDraw.Draw(win)
    ww, wh = win.size
    for bx, hy, c in STREET:
        x = (bx - t * speed) % 3000 - 200
        h = hy * wh * 1.6
        d.rectangle([x, wh - h, x + 160, wh], fill=(22, 18, 40))
        for yy in range(int(wh - h + 15), wh - 10, 34):
            for xx in range(int(x + 15), int(x + 150), 30):
                if (xx * 7 + yy * 3) % 5 < 2:
                    d.rectangle([xx, yy, xx + 12, yy + 16], fill=(255, 210, 140))
    for k in range(6):
        x = (k * 520 - t * speed * 1.8) % 3000 - 200
        d.line([(x, wh * 0.6), (x + 300, wh * 0.6)], fill=NEON[k % 3], width=6)
    img.paste(win, (int(x0), int(y0)))
    dd = ImageDraw.Draw(img)
    dd.rounded_rectangle(box, 30, outline=(60, 60, 75), width=18)


def bus_interior(img, t, flick=1.0, pale=False):
    d = ImageDraw.Draw(img)
    base = (60, 70, 80) if not pale else (55, 60, 75)
    d.rectangle([0, 0, W, H], fill=mix(base, (0, 0, 0), 1 - flick))
    night_window(img, (60, 260, W - 60, 900), t)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 200], fill=mix((40, 45, 55), (0, 0, 0), 1 - flick))
    for k in range(3):
        d.rectangle([80 + k * 340, 90, 300 + k * 340, 120], fill=mix((250, 250, 220), (30, 30, 30), 1 - flick))
    d.rectangle([0, 1400, W, H], fill=(30, 34, 44))
    return d


blink_t = sorted(rng.uniform(0, 80, 40))


def is_blink(tt, off=0.0):
    return any(0 <= tt + off - b < 0.12 for b in blink_t)


def frame(f):
    tt = f / FPS
    s = seg_at(tt)
    sc = s["scene"]
    lt = tt - s["start"]
    m = env[min(f, len(env) - 1)]
    mouth = lambda w: m if s["who"] == w and s["start"] <= tt <= s["end"] else 0.0
    img = Image.new("RGBA", (W, H))
    zoom, shake = 1.0 + 0.04 * min(1, max(0, lt) / 4), 0.0
    if sc in ("stop", "arrive"):
        img = grad([(0, (8, 8, 30)), (0.55, (50, 25, 80)), (1, (25, 20, 35))])
        d = ImageDraw.Draw(img)
        for sx, sy in STARS:
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 255, 255))
        d.rectangle([0, 1450, W, H], fill=(35, 32, 45))
        d.rectangle([0, 1440, W, 1460], fill=(80, 75, 90))
        fl = 1.0 if math.sin(tt * 23) > -0.85 else 0.25
        d.rectangle([150, 500, 175, 1450], fill=(50, 50, 60))
        d.rectangle([150, 490, 330, 515], fill=(50, 50, 60))
        cone = Image.new("RGBA", (W, H)); cd = ImageDraw.Draw(cone)
        cd.polygon([(300, 520), (60, 1460), (620, 1460)], fill=(255, 230, 160, int(60 * fl)))
        img.alpha_composite(cone.filter(ImageFilter.GaussianBlur(20)))
        glow(img, 310, 520, 90, (255, 230, 170), fl)
        d = ImageDraw.Draw(img)
        d.rectangle([560, 900, 1000, 920], fill=(70, 80, 100)); d.rectangle([580, 920, 600, 1450], fill=(70, 80, 100))
        d.rounded_rectangle([700, 760, 900, 880], 14, fill=(240, 240, 240)); d.text((735, 785), "N7", fill=(200, 30, 60), font=FONT(70))
        bx = W * 0.32
        if sc == "arrive":
            p = min(1, lt / 2.2); p = 1 - (1 - p) ** 3
            busx = W + 50 - p * 1150
            d.rounded_rectangle([busx, 780, busx + 1500, 1430], 40, fill=(230, 60, 70))
            for k in range(5):
                d.rounded_rectangle([busx + 60 + k * 270, 840, busx + 280 + k * 270, 1060], 18, fill=(255, 225, 150))
            d.rectangle([busx + 90, 1100, busx + 240, 1420], fill=(40, 40, 50))
            d.text((busx + 300, 1120), "N7 · NOCTURNO", fill=(255, 255, 255), font=FONT(56))
            for wx in (busx + 250, busx + 1200):
                d.ellipse([wx - 85, 1350, wx + 85, 1520], fill=(20, 20, 24))
            glow(img, busx + 20, 1300, 120, (255, 245, 210), 0.9)
            d = ImageDraw.Draw(img)
            bx = W * 0.22
        character(d, "N", bx, 1050, 200, mouth("N"), is_blink(tt), look=0.8 if sc == "arrive" else -0.3)
    elif sc == "driver":
        img = grad([(0, (20, 40, 40)), (1, (10, 20, 25))]).convert("RGBA")
        d = ImageDraw.Draw(img)
        night_window(img, (0, 150, W, 800), tt, 300)
        d = ImageDraw.Draw(img)
        character(d, "C", W * 0.5, 1050, 330, mouth("C"), is_blink(tt, 0.3), look=0.0)
        d.ellipse([W * 0.5 - 480, 1500, W * 0.5 + 480, 2000], outline=(30, 30, 35), width=60)
        glow(img, W * 0.5, 1000, 600, (40, 255, 160), 0.12)
        zoom = 1.0 + 0.10 * min(1, max(0, lt) / 3)
    elif sc in ("aisle",):
        img = Image.new("RGBA", (W, H), (60, 70, 80))
        d = ImageDraw.Draw(img)
        vx, vy = W / 2, 700
        d.polygon([(vx - 120, vy), (vx + 120, vy), (W, H), (0, H)], fill=(45, 50, 60))
        for k in range(6):
            z = 1 + k * 0.9
            y = vy + 1100 / z
            sw = 380 / z
            for sgn in (-1, 1):
                sx = vx + sgn * 520 / z
                d.rounded_rectangle([sx - sw / 2, y - 260 / z, sx + sw / 2, y], int(30 / z), fill=(40, 90, 140))
        for k in range(8):
            d.rectangle([vx - 300 + k * 70, 150, vx - 270 + k * 70, 170], fill=(250, 250, 220))
        p = min(1, lt / 3)
        character(d, "N", W / 2, 1150 - p * 150, 230 - p * 60, mouth("N"), is_blink(tt), look=math.sin(tt * 2))
    elif sc == "girl":
        d = bus_interior(img, tt)
        d.rounded_rectangle([140, 1150, W - 140, 1480], 40, fill=(40, 90, 140))
        character(d, "G", W * 0.62, 1000, 230, mouth("G"), is_blink(tt, 0.5), look=-0.8, wave_=tt * 6 if lt > 2 else 0)
        zoom = 1.0 + 0.08 * min(1, lt / 4)
    elif sc in ("both", "both_pale"):
        pale = sc == "both_pale"
        d = bus_interior(img, tt, pale=pale)
        d.rounded_rectangle([60, 1150, W - 60, 1480], 40, fill=(40, 90, 140))
        speaking = s["who"]
        character(d, "N", W * 0.3, 1000, 220, mouth("N"), is_blink(tt), look=0.8)
        character(d, "G", W * 0.72, 1000, 220, mouth("G"), is_blink(tt, 0.4), look=-0.8, pale=pale)
        if pale:
            zoom = 1.0 + 0.14 * min(1, lt / 5)
    elif sc == "window":
        d = bus_interior(img, tt)
        img2 = Image.new("RGBA", (W, H), (50, 55, 65))
        night_window(img2, (40, 300, W - 40, 1400), tt, 900)
        d = ImageDraw.Draw(img2)
        if lt > 2.0:
            sx = W + 200 - (lt - 2.0) * 900
            d.rectangle([sx, 700, sx + 22, 1380], fill=(160, 170, 180))
            d.rounded_rectangle([sx - 150, 560, sx + 170, 720], 20, fill=(240, 240, 240))
            d.text((sx - 120, 590), "TU PARADA", fill=(200, 30, 60), font=FONT(62))
        refl = Image.new("RGBA", (W, H)); rd = ImageDraw.Draw(refl)
        character(rd, "N", W * 0.5, 900, 260, 0, False, look=1.0, shock=lt > 3.2)
        refl.putalpha(refl.getchannel("A").point(lambda v: int(v * 0.22)))
        img2.alpha_composite(refl)
        img = img2
        zoom = 1.0 + 0.06 * min(1, lt / 5)
    elif sc == "grab":
        d = bus_interior(img, tt)
        d.rounded_rectangle([60, 1250, W - 60, 1560], 40, fill=(40, 90, 140))
        character(d, "N", W * 0.3, 860, 230, mouth("N"), is_blink(tt), look=1.0 if s["who"] == "G" else -1)
        character(d, "G", W * 0.72, 1110, 210, mouth("G"), is_blink(tt, 0.4), look=-1, pale=True,
                  arm=(W * 0.3 + 120, 1080) if lt > 1.2 or s["who"] == "G" else None)
        if s["who"] == "G":
            zoom = 1.12
    elif sc in ("flicker", "speaker"):
        fl = 1.0 if (math.sin(tt * 31) + math.sin(tt * 13)) > -0.6 else 0.12
        d = bus_interior(img, tt, flick=fl)
        if sc == "speaker" or lt > 2.5:
            d.ellipse([W / 2 - 260, 260, W / 2 + 260, 780], fill=(25, 25, 30))
            for k in range(-4, 5):
                d.line([(W / 2 - 200, 520 + k * 45), (W / 2 + 200, 520 + k * 45)], fill=(60, 60, 70), width=14)
            glow(img, W / 2, 520, 420, (255, 40, 40), 0.25 + 0.5 * m if sc == "speaker" else 0.2)
            d = ImageDraw.Draw(img)
        character(d, "N", W * 0.3, 1150, 220, mouth("N"), False, look=0.5, shock=sc == "speaker")
        character(d, "G", W * 0.72, 1150, 220, 0, False, look=-0.5, pale=True, shock=sc == "speaker")
        shake = 6 if sc == "speaker" else 0
        zoom = 1.0 + (0.2 * min(1, lt / 3) if sc == "speaker" else 0.03)
    else:  # shock / end
        img = grad([(0, (60, 10, 30)), (1, (10, 0, 10))])
        d = ImageDraw.Draw(img)
        for k in range(30):
            a = k / 30 * 2 * math.pi + tt * 0.3
            d.line([(W / 2, H * 0.45), (W / 2 + math.cos(a) * 2000, H * 0.45 + math.sin(a) * 2000)], fill=(80, 15, 40), width=30)
        character(d, "N", W / 2, H * 0.45, 420, mouth("N"), False, look=0, shock=True)
        zoom = 1.0 + 0.25 * min(1, (tt - segs[-2]["start"]) / 6)
        shake = 4 if sc == "shock" else 1
        if sc == "end":
            dark = Image.new("RGBA", (W, H), (0, 0, 0, 150)); img.alpha_composite(dark)
    # cámara
    img = img.convert("RGB")
    zoom = max(1.0, zoom)
    if zoom > 1.001 or shake:
        cw, ch = W / zoom - 2 * shake, H / zoom - 2 * shake
        cx = W / 2 + (math.sin(tt * 41) * shake if shake else 0)
        cy = H * 0.5 + (math.cos(tt * 37) * shake if shake else 0)
        l = min(max(0, cx - cw / 2), W - cw); tp = min(max(0, cy - ch / 2), H - ch)
        img = img.resize((W, H), Image.BILINEAR, box=(l, tp, l + cw, tp + ch))
    # cortes con flash
    for s2 in segs:
        if s2["scene"] != seg_at(s2["start"] - 0.5)["scene"] and 0 <= tt - (s2["start"] - GAP / 2) < 0.12:
            a = 1 - (tt - (s2["start"] - GAP / 2)) / 0.12
            img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), a * 0.5)
    return img


_F = {}


def FONT(sz):
    from PIL import ImageFont
    if sz not in _F:
        _F[sz] = ImageFont.truetype(os.path.join(FONTS, "Anton-Regular.ttf"), sz)
    return _F[sz]


# ------------------------------------------------------------------ render vídeo
nfr = int(D * FPS)
vid = os.path.join(OUTD, "video.mp4")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                      "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", vid],
                     stdin=subprocess.PIPE)
for f in range(nfr):
    p.stdin.write(frame(f).tobytes())
    if f % 300 == 0:
        print("frame", f, "/", nfr, flush=True)
p.stdin.close(); p.wait()

# ------------------------------------------------------------------ audio
ASR = 44100
N = int(D * ASR) + ASR
r2 = np.random.default_rng(5)
v = signal.resample_poly(voice, ASR, SR)
mixa = np.zeros(N); mixa[:len(v)] += v / (np.max(np.abs(v)) + 1e-9) * 0.8
tq = np.arange(N) / ASR


def lp(x, f):
    return signal.sosfilt(signal.butter(2, f, "lowpass", fs=ASR, output="sos"), x)


drone = (np.sin(2 * np.pi * 55 * tq) + 0.5 * np.sin(2 * np.pi * 82.4 * tq + np.sin(tq * 0.3))) * 0.03
drone += lp(r2.standard_normal(N), 200) * 0.05
music = drone * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * tq))
for s in segs:
    a, b = int((s["start"] - GAP / 2) * ASR), int((s["end"] + GAP / 2) * ASR)
    if s["scene"] in ("aisle", "girl", "both", "both_pale", "window", "grab", "flicker", "speaker", "driver"):
        music[a:b] += lp(r2.standard_normal(b - a), 120) * 0.12   # motor del bus
    if s["scene"] in ("both_pale", "window", "grab", "flicker", "speaker", "shock"):   # latido
        bt = 0.75 if s["scene"] in ("both_pale", "window") else 0.5
        for k in np.arange(s["start"], s["end"], bt):
            i = int(k * ASR); n = int(0.25 * ASR); x = np.arange(n) / ASR
            hb = np.sin(2 * np.pi * 50 * x) * np.exp(-x * 18) * 0.35
            music[i:i + n] += hb[:len(music[i:i + n])]
            music[i + int(0.18 * ASR):i + int(0.18 * ASR) + n] += hb[:len(music[i + int(0.18 * ASR):i + int(0.18 * ASR) + n])] * 0.7
# golpes de tensión
for s in segs:
    if s["scene"] in ("speaker", "shock", "both_pale"):
        i = int((s["start"] - 0.05) * ASR); n = int(2 * ASR); x = np.arange(n) / ASR
        hit = (np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-x * 10)) / ASR) * np.exp(-x * 2.5) + lp(r2.standard_normal(n), 800) * np.exp(-x * 6) * 0.4) * 0.5
        mixa[i:i + n] += hit[:len(mixa[i:i + n])]
# whoosh en cambios de escena
for s in segs:
    i = int((s["start"] - 0.45) * ASR); n = int(0.5 * ASR)
    wsh = signal.sosfilt(signal.butter(2, [800, 6000], "bandpass", fs=ASR, output="sos"), r2.standard_normal(n)) * np.hanning(n) * 0.06
    mixa[i:i + n] += wsh[:len(mixa[i:i + n])]
voice_env = np.convolve(np.abs(mixa), np.ones(4410) / 4410, "same")
duck = 1 - 0.5 * np.clip(voice_env / 0.05, 0, 1)
out = mixa + music * duck
out = out[:int(D * ASR)] / max(1, np.max(np.abs(out)) / 0.95)
aud = os.path.join(OUTD, "audio.wav")
with wave.open(aud, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(ASR); w.writeframes((out * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ subtítulos estilo TikTok
def ts(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


COL = {"N": "&H00FFFFFF&", "G": "&H00E0A0FF&", "C": "&H0060C0FF&", "A": "&H004040FF&"}
ass = ["[Script Info]", "PlayResX: 1080", "PlayResY: 1920", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Anton,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,8,4,5,60,60,0,1",
       "Style: Top,Anton,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,3,14,0,8,60,60,110,1",
       "Style: Who,Poppins Bold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,5,0,5,0,0,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for s in segs:
    words = s["text"].split()
    groups, cur = [], []
    for wd in words:
        cur.append(wd)
        if len(cur) >= 3 or wd[-1] in ",.?!":
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    tot = sum(len(w) + 2 for g in groups for w in g)
    t0 = s["start"]
    for g in groups:
        dd = (s["end"] - s["start"]) * sum(len(w) + 2 for w in g) / tot
        txt = " ".join(g).upper()
        ass.append(f"Dialogue: 2,{ts(t0)},{ts(t0 + dd)},Cap,,0,0,0,,{{\\pos(540,1640)\\1c{COL[s['who']]}\\fscx70\\fscy70\\t(0,90,\\fscx108\\fscy108)\\t(90,160,\\fscx100\\fscy100)}}{txt}")
        t0 += dd
    if s["who"] != "N":
        name = {"G": "LA CHICA", "C": "EL CONDUCTOR", "A": "ALTAVOZ"}[s["who"]]
        ass.append(f"Dialogue: 2,{ts(s['start'])},{ts(s['end'])},Who,,0,0,0,,{{\\pos(540,1545)\\1c{COL[s['who']]}\\fad(80,80)}}{name}")
ass.append(f"Dialogue: 1,{ts(0)},{ts(segs[-1]['start'])},Top,,0,0,0,,{TITULO.upper()}\\N{{\\1c&H0040D0FF&}}PARTE 1")
ass.append(f"Dialogue: 3,{ts(segs[-1]['start'])},{ts(D)},Cap,,0,0,0,,{{\\pos(540,820)\\fs150\\1c&H0040D0FF&\\t(0,300,\\fscx115\\fscy115)\\t(300,600,\\fscx100\\fscy100)}}¿PARTE 2?")
open(os.path.join(OUTD, "subs.ass"), "w", encoding="utf-8").writelines(l + "\n" for l in ass)

final = os.environ.get("OUT", "/home/user/videos-iaa/output/POV_ultimo_bus_parte1.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", aud, "-vf", f"ass={os.path.join(OUTD, 'subs.ass')}:fontsdir={FONTS}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5,aresample=48000",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final], check=True)
print("OK", final)
