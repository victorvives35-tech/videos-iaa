#!/usr/bin/env python3
"""Genera un video vertical (1080x1920) estilo TikTok de Roblox: storytime de un obby.

Uso: python3 make_video.py --voice ruta/es.onnx --out obby_tiktok.mp4
Requiere: piper-tts (CLI `piper`), ffmpeg, numpy, Pillow.
"""
import argparse, math, os, random, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 44100
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

# (texto locución, escena)
SCRIPT = [
    ("Este obby solo lo completa el cero coma uno por ciento de la gente.", "intro"),
    ("Y yo dije: fácil, hermano.", "confident"),
    ("Primer salto... y directo a la lava.", "lava"),
    ("Vale, vale. No pasa nada. Otra vez.", "respawn"),
    ("Llego al nivel cincuenta, y aparece un noob.", "noob"),
    ("Y me dice: sígueme, conozco un atajo.", "talk"),
    ("Le sigo. Saltamos al vacío...", "void"),
    ("Y aparecemos... ¡en la meta!", "finish"),
    ("Resulta que el noob... era el creador del juego.", "twist"),
    ("Sígueme para la parte dos.", "cta"),
]

# ---------------------------------------------------------------- audio
def synth_voice(voice, tmp):
    clips = []
    for i, (txt, _) in enumerate(SCRIPT):
        raw = os.path.join(tmp, f"l{i}.wav")
        out = os.path.join(tmp, f"v{i}.wav")
        subprocess.run(["piper", "-m", voice, "--length-scale", "0.82", "-f", raw],
                       input=txt.encode(), check=True, capture_output=True)
        # voz un poco más aguda y rápida, con energía
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
                        "asetrate=22050*1.07,aresample=44100,acompressor=threshold=-18dB:ratio=4,volume=1.6",
                        "-ac", "1", out], check=True)
        with wave.open(out) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        # recorta silencios
        idx = np.where(np.abs(a) > 0.02)[0]
        a = a[max(0, idx[0] - 600): idx[-1] + 2000]
        clips.append(a)
    return clips

def env(n, a=0.005, r=0.1):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)

def sfx(kind):
    if kind == "boing":
        n = int(SR * .35); t = np.arange(n) / SR
        f = 220 + 500 * t / .35
        return .5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .003, .15)
    if kind == "whoosh":
        n = int(SR * .4); x = np.random.randn(n)
        x = np.convolve(x, np.ones(30) / 30, "same")
        return .6 * x * np.sin(np.linspace(0, np.pi, n))
    if kind == "death":
        n = int(SR * .45); t = np.arange(n) / SR
        f = 600 * np.exp(-t * 5)
        return .5 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, .002, .2) * .6
    if kind == "ding":
        n = int(SR * .9); t = np.arange(n) / SR
        return .35 * (np.sin(2*np.pi*880*t) + .6*np.sin(2*np.pi*1320*t) + .3*np.sin(2*np.pi*1760*t)) * env(n, .002, .35)
    if kind == "boom":
        n = int(SR * 1.2); t = np.arange(n) / SR
        f = 90 * np.exp(-t * 2) + 30
        return .9 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .5)
    if kind == "pop":
        n = int(SR * .12); t = np.arange(n) / SR
        return .3 * np.sin(2 * np.pi * (500 + 2500 * t) * t) * env(n, .001, .03)
    raise ValueError(kind)

def music(n):
    """Loop simple tipo 'phonk light': bajo + kick + hi-hat, 128 BPM."""
    t = np.arange(n) / SR
    beat = 60 / 128
    out = np.zeros(n, np.float32)
    notes = [55, 55, 65.4, 49]  # A1 A1 C2 G1
    step = beat / 2
    for k in range(int(n / SR / step) + 1):
        s = int(k * step * SR)
        if s >= n: break
        m = min(n - s, int(step * SR))
        tt = np.arange(m) / SR
        f = notes[(k // 8) % 4]
        out[s:s+m] += .18 * np.tanh(3 * np.sin(2*np.pi*f*tt)) * np.exp(-tt * 4)
        if k % 2 == 0:  # kick
            kk = min(m, int(.25 * SR)); tk = np.arange(kk) / SR
            out[s:s+kk] += .5 * np.sin(2*np.pi*(50 + 120*np.exp(-tk*30))*tk) * np.exp(-tk*12)
        hh = min(m, int(.04 * SR))
        out[s:s+hh] += .05 * np.random.randn(hh) * np.exp(-np.arange(hh)/SR*120)
        if k % 4 == 2:  # clap
            cc = min(m, int(.15 * SR))
            out[s:s+cc] += .12 * np.random.randn(cc) * np.exp(-np.arange(cc)/SR*30)
    return out

# ---------------------------------------------------------------- timing
def build_timeline(clips):
    gap = int(SR * .18)
    segs, cur = [], int(SR * .25)
    for (txt, scene), a in zip(SCRIPT, clips):
        segs.append(dict(text=txt, scene=scene, start=cur / SR, dur=len(a) / SR, audio=a, s0=cur))
        cur += len(a) + gap
    total = cur / SR + .6
    # palabras con tiempo proporcional a su longitud
    for s in segs:
        words = s["text"].split()
        weights = [len(w.strip(".,¡!¿?")) + 2 for w in words]
        tot = sum(weights); acc = 0
        s["words"] = []
        for w, wt in zip(words, weights):
            s["words"].append((w, s["start"] + s["dur"] * acc / tot, s["start"] + s["dur"] * (acc + wt) / tot))
            acc += wt
    return segs, total

# ---------------------------------------------------------------- drawing
def font(sz): return ImageFont.truetype(FONT, sz)

PLATFORMS = [  # x, y(top), w, color   (coordenadas mundo; y crece hacia abajo)
    (-300, 1250, 600, (90, 200, 90)),
    (520, 1180, 220, (230, 70, 70)),
    (900, 1100, 200, (70, 140, 240)),
    (1250, 1150, 200, (240, 200, 50)),
]
LAVA_Y = 1480

def sky(img, top, bot):
    d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        k = y / H
        c = tuple(int(top[i] * (1 - k) + bot[i] * k) for i in range(3))
        d.rectangle([0, y, W, y + 8], fill=c)

def block(d, box, col, outline=True):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=col)
    hi = tuple(min(255, c + 45) for c in col); lo = tuple(max(0, c - 55) for c in col)
    e = max(4, int((x1 - x0) * .06))
    d.rectangle([x0, y0, x1, y0 + e], fill=hi)
    d.rectangle([x0, y1 - e, x1, y1], fill=lo)
    if outline: d.rectangle(box, outline=(20, 20, 30), width=4)

def avatar(d, x, y, s, style, t, walk=0.0, pose="idle", face_dir=1):
    """Personaje de bloques. (x,y)=pies, s=escala (altura ~ 5.5*s)."""
    if style == "hero":
        head, torso, arms, legs = (255, 205, 160), (30, 30, 35), (255, 205, 160), (40, 60, 160)
    else:  # noob
        head, torso, arms, legs = (245, 205, 50), (30, 120, 220), (245, 205, 50), (90, 180, 70)
    sw = math.sin(t * 14) * walk
    if pose == "fall": sw = math.sin(t * 30) * .9
    lw, lh = s * .9, s * 2
    hip = y - lh
    for side, ph in ((-1, sw), (1, -sw)):  # piernas
        cx = x + side * lw * .55
        off = ph * s * .6
        block(d, [cx - lw/2 + off, hip, cx + lw/2 + off, y], legs)
    tw, th = s * 2, s * 2
    ty = hip - th
    arm_up = pose in ("fall", "cheer")
    for side, ph in ((-1, -sw), (1, sw)):  # brazos
        ax = x + side * (tw/2 + lw/2)
        if arm_up:
            block(d, [ax - lw/2, ty - s * 1.6, ax + lw/2, ty + s * .4], arms)
        else:
            off = ph * s * .5
            block(d, [ax - lw/2 + off, ty, ax + lw/2 + off, ty + th], arms)
    block(d, [x - tw/2, ty, x + tw/2, hip], torso)
    if style == "hero":  # logo camiseta
        d.polygon([(x - s*.4, ty + s*.5), (x + s*.4, ty + s*.5), (x, ty + s*1.3)], fill=(255, 60, 90))
    hs = s * 1.25
    hy = ty - hs * 1.05
    block(d, [x - hs/2, hy, x + hs/2, hy + hs], head)
    if style == "hero":  # pelo
        d.rectangle([x - hs/2 - 4, hy - s*.25, x + hs/2 + 4, hy + s*.25], fill=(60, 35, 20))
    # cara sonriente simple
    ex = s * .22 * face_dir
    for e in (-1, 1):
        d.ellipse([x + e*s*.28 + ex - s*.09, hy + hs*.35, x + e*s*.28 + ex + s*.09, hy + hs*.35 + s*.22], fill=(15, 15, 15))
    mouth = [x - s*.3 + ex, hy + hs*.55, x + s*.3 + ex, hy + hs*.85]
    if pose == "fall":
        d.ellipse([x - s*.15 + ex, hy + hs*.58, x + s*.15 + ex, hy + hs*.88], fill=(15, 15, 15))
    else:
        d.arc(mouth, 10, 170, fill=(15, 15, 15), width=max(3, int(s*.09)))
    return hy  # top de la cabeza

def outlined_text(d, xy, txt, f, fill, stroke=(0, 0, 0), sw=10, anchor="mm"):
    d.text(xy, txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)

def sticker(img, txt, cx, cy, sz, bg, fg=(255, 255, 255), rot=0, scale=1.0):
    f = font(int(sz * scale))
    tmp = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((W/2, 200), txt, font=f, anchor="mm")
    pad = int(sz * .35 * scale)
    d.rounded_rectangle([bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad], radius=pad, fill=bg, outline=(0, 0, 0), width=8)
    d.text((W/2, 200), txt, font=f, fill=fg, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=False)
    img.alpha_composite(tmp, (int(cx - W/2), int(cy - 200)))

def ease(u): u = max(0, min(1, u)); return u * u * (3 - 2 * u)

def world_view(img, cam_x, cam_y, zoom, t, lava=True, extra=None):
    d = ImageDraw.Draw(img)
    def P(x, y): return ((x - cam_x) * zoom + W/2, (y - cam_y) * zoom + H/2)
    # nubes
    for i in range(6):
        cx = ((i * 420 - cam_x * .3 + t * 20) % 1800) - 300
        cy = 250 + (i * 137) % 500
        for dx, dy, r in ((0, 0, 70), (60, -20, 60), (-60, 10, 55), (110, 10, 45)):
            d.ellipse([cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r], fill=(255, 255, 255))
    for (x, y, w, c) in PLATFORMS + (extra or []):
        a, b = P(x, y); e, f_ = P(x + w, y + 90)
        block(d, [a, b, e, f_], c)
        # pilar
        pa, pb = P(x + w*.35, y + 90); pe, pf = P(x + w*.65, LAVA_Y)
        d.rectangle([pa, pb, pe, pf], fill=tuple(int(v*.55) for v in c))
    if lava:
        _, ly = P(0, LAVA_Y)
        d.rectangle([0, ly, W, H], fill=(255, 90, 0))
        for i in range(0, W + 60, 60):
            yy = ly + 12 * math.sin(i * .02 + t * 4)
            d.ellipse([i - 40, yy - 20, i + 40, yy + 20], fill=(255, 160, 20))
        for i in range(8):
            bx = (i * 173 + t * 50) % W
            by = ly + 60 + (i * 97) % 300
            r = 14 + 8 * math.sin(t * 5 + i)
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=(255, 220, 60))
    return P

def hud(img, deaths, level):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 170, 400, 260], radius=24, fill=(0, 0, 0, 160))
    d.text((70, 215), f"NIVEL {level}", font=font(52), fill=(255, 255, 255), anchor="lm")
    d.rounded_rectangle([W - 400, 170, W - 40, 260], radius=24, fill=(0, 0, 0, 160))
    d.text((W - 370, 215), f"MUERTES: {deaths}", font=font(46), fill=(255, 90, 90), anchor="lm")

# ---------------------------------------------------------------- escenas
def render_scene(seg, t, T):
    """t: tiempo local de la escena, T: tiempo global"""
    sc, dur = seg["scene"], seg["dur"] + .18
    u = t / dur
    img = Image.new("RGBA", (W, H))
    shake = (0, 0)

    if sc in ("intro", "confident", "lava", "respawn"):
        sky(img, (90, 170, 255), (190, 230, 255))
        deaths = 0 if sc in ("intro", "confident", "lava") else 1
        if sc == "lava" and u > .62: deaths = 1
        px, py, walk, pose, z = 0, 1250, 0, "idle", 1.0
        cam = (300, 1050)
        if sc == "intro":
            z = 1.0 + .25 * ease(u); cam = (150 - 100*u, 1080)
        if sc == "confident":
            z = 1.6; cam = (0, 1050)
            py = 1250 - abs(math.sin(t * 6)) * 15
        if sc == "lava":
            z = 1.1; cam = (250, 1150)
            jt = max(0, (u - .3) / .45)
            if u < .3:
                px = -150 + 400 * (u / .3); walk = 1
            else:
                px = 250 + 220 * min(jt, 1)
                py = 1250 - 330 * math.sin(min(jt, .55) * math.pi) + (max(0, jt - .55) ** 1.5) * 900
                pose = "fall" if jt > .5 else "idle"
                py = min(py, LAVA_Y + 60)
            if u > .7: shake = (random.randint(-25, 25), random.randint(-25, 25))
        if sc == "respawn":
            z = 1.3; cam = (0, 1080)
        P = world_view(img, cam[0], cam[1], z, T)
        ax, ay = P(px, py)
        visible = not (sc == "lava" and u > .75)
        if sc == "respawn":
            visible = (int(t * 10) % 2 == 0) if t < .8 else True
        if visible:
            avatar(ImageDraw.Draw(img), ax, ay, 55 * z, "hero", T, walk, pose)
        hud(img, deaths, 1)
        if sc == "intro" and t > .5:
            s = min(1, (t - .5) / .25)
            sticker(img, "0,1%", W/2, 620, 200, (255, 40, 80), rot=-6, scale=.6 + .4*s + .08*math.sin(t*8))
            sticker(img, "LO COMPLETA", W/2, 840, 70, (30, 30, 30), rot=3)
        if sc == "confident" and t > .6:
            sticker(img, "FÁCIL", W/2, 560, 150, (40, 200, 120), rot=-5, scale=1 + .05*math.sin(t*10))
        if sc == "lava" and u > .7:
            ov = Image.new("RGBA", (W, H), (255, 0, 0, int(110 * max(0, 1 - (u - .7) * 2))))
            img.alpha_composite(ov)
            sticker(img, "OOF", W/2, 700, 220, (0, 0, 0), fg=(255, 60, 60), rot=8)
        if sc == "respawn":
            sticker(img, "INTENTO #2", W/2, 600, 110, (255, 160, 0), rot=-4)

    elif sc in ("noob", "talk"):
        sky(img, (255, 150, 120), (255, 220, 170))
        extra = [(-400, 1250, 1300, (160, 90, 230))]
        save = PLATFORMS[:]; PLATFORMS.clear()
        P = world_view(img, 0, 1030, 1.25, T, extra=extra)
        PLATFORMS.extend(save)
        d = ImageDraw.Draw(img)
        # cartel nivel 50
        sx, sy = P(-250, 1250)
        d.rectangle([sx - 8, sy - 420, sx + 8, sy], fill=(90, 60, 30))
        block(d, [sx - 150, sy - 520, sx + 150, sy - 380], (250, 240, 220))
        d.text((sx, sy - 450), "NIVEL 50", font=font(56), fill=(40, 20, 10), anchor="mm")
        hx, hy = P(-80, 1250)
        avatar(d, hx, hy, 62, "hero", T, 0, "idle", face_dir=1)
        if sc == "noob":
            nx = 700 - 420 * ease(u / .6)
            nwalk = 1 if u < .6 else 0
        else:
            nx, nwalk = 280, 0
        nxp, nyp = P(nx, 1250)
        top = avatar(d, nxp, nyp, 62, "noob", T, nwalk, "idle", face_dir=-1)
        d.text((nxp, top - 50), "xX_n00b_Xx", font=font(40), fill=(255, 255, 255), anchor="mm",
               stroke_width=5, stroke_fill=(0, 0, 0))
        hud(img, 37, 50)
        if sc == "noob" and u > .6:
            sticker(img, "¿UN NOOB?", W/2, 620, 130, (245, 205, 50), fg=(255, 255, 255), rot=-5)
        if sc == "talk" and t > .5:
            # bocadillo
            bw = 760
            bx0, by0 = W/2 - bw/2, 480
            d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + 260], radius=50, fill=(255, 255, 255), outline=(0, 0, 0), width=8)
            d.polygon([(nxp - 40, by0 + 255), (nxp + 30, by0 + 255), (nxp, by0 + 360)], fill=(255, 255, 255), outline=(0, 0, 0))
            d.text((W/2, by0 + 95), "sígueme,", font=font(80), fill=(0, 0, 0), anchor="mm")
            d.text((W/2, by0 + 180), "conozco un atajo", font=font(64), fill=(0, 0, 0), anchor="mm")

    elif sc == "void":
        sky(img, (10, 10, 30), (40, 10, 70))
        d = ImageDraw.Draw(img)
        random.seed(int(T * 30))
        for _ in range(40):  # líneas de velocidad
            x = random.randint(0, W); y = random.randint(0, H); L = random.randint(150, 450)
            d.line([x, y, x, y + L], fill=(200, 200, 255), width=random.randint(3, 8))
        random.seed()
        wob = math.sin(t * 6) * 40
        avatar(d, W/2 - 180 + wob, 1150 + math.sin(t*5)*30, 70, "hero", T, 0, "fall")
        avatar(d, W/2 + 180 - wob, 1080 + math.cos(t*5)*30, 70, "noob", T, 0, "fall")
        shake = (random.randint(-8, 8), random.randint(-8, 8))
        sticker(img, "AAAAAH", W/2, 520, 140, (130, 40, 220), rot=-7, scale=1 + .06*math.sin(t*15))

    elif sc == "finish":
        sky(img, (120, 220, 255), (255, 250, 200))
        extra = [(-500, 1250, 1400, (255, 200, 40))]
        save = PLATFORMS[:]; PLATFORMS.clear()
        P = world_view(img, 0, 1030, 1.25, T, lava=False, extra=extra)
        PLATFORMS.extend(save)
        d = ImageDraw.Draw(img)
        # arco de meta
        a, b = P(-420, 1250); c, e = P(420, 1250)
        d.rectangle([a, b - 700, a + 40, b], fill=(255, 255, 255), outline=(0, 0, 0), width=5)
        d.rectangle([c - 40, b - 700, c, b], fill=(255, 255, 255), outline=(0, 0, 0), width=5)
        for i in range(12):  # bandera ajedrez
            for j in range(2):
                col = (0, 0, 0) if (i + j) % 2 else (255, 255, 255)
                cw = (c - a) / 12
                d.rectangle([a + i*cw, b - 760 + j*40, a + (i+1)*cw, b - 720 + j*40], fill=col)
        land = ease(u / .3)
        y1 = 1250 - 900 * (1 - land)
        hx, hy = P(-150, y1); nx_, ny_ = P(150, y1)
        pose = "cheer" if u > .3 else "fall"
        bounce = abs(math.sin(t * 8)) * 20 if u > .3 else 0
        avatar(d, hx, hy - bounce, 62, "hero", T, 0, pose)
        avatar(d, nx_, ny_, 62, "noob", T, 0, "idle" if u > .3 else "fall", face_dir=-1)
        if u > .3:
            random.seed(7)
            for i in range(120):  # confeti
                x0 = random.uniform(0, W); sp = random.uniform(300, 700)
                y = (random.uniform(-H, 0) + (t - .3*dur) * sp) % (H + 100) - 50
                x = x0 + 40 * math.sin(t * 3 + i)
                col = random.choice([(255, 60, 90), (60, 200, 255), (255, 220, 40), (120, 255, 120), (200, 90, 255)])
                d.rectangle([x, y, x + 18, y + 30], fill=col)
            random.seed()
            sticker(img, "¡META!", W/2, 520, 190, (40, 200, 90), rot=-4, scale=1 + .06*math.sin(t*10))

    elif sc == "twist":
        sky(img, (60, 0, 20), (10, 0, 10))
        d = ImageDraw.Draw(img)
        z = 1 + .5 * ease(u)
        # rayos de fondo
        for k in range(16):
            ang = k * math.pi / 8 + t * .5
            d.polygon([(W/2, 1000), (W/2 + 2000*math.cos(ang), 1000 + 2000*math.sin(ang)),
                       (W/2 + 2000*math.cos(ang + .18), 1000 + 2000*math.sin(ang + .18))], fill=(120, 0, 40))
        top = avatar(d, W/2, 1350 + 250*(z - 1), 90 * z, "noob", T, 0, "idle")
        if u > .45:  # corona
            cs = 90 * z
            cy = top - cs * .1
            pts = [(W/2 - cs, cy), (W/2 - cs, cy - cs*.8), (W/2 - cs*.5, cy - cs*.35), (W/2, cy - cs),
                   (W/2 + cs*.5, cy - cs*.35), (W/2 + cs, cy - cs*.8), (W/2 + cs, cy)]
            d.polygon(pts, fill=(255, 210, 30), outline=(0, 0, 0))
            for gx in (-.5, 0, .5):
                d.ellipse([W/2 + gx*cs - 12, cy - cs*.25 - 12, W/2 + gx*cs + 12, cy - cs*.25 + 12], fill=(230, 30, 60))
            sticker(img, "CREADOR DEL JUEGO", W/2, 430, 80, (255, 210, 30), fg=(255, 255, 255), rot=-3)
            if u < .6: shake = (random.randint(-30, 30), random.randint(-30, 30))
        # viñeta
        vg = Image.new("L", (W, H), 0)
        ImageDraw.Draw(vg).ellipse([-200, 200, W + 200, H - 200], fill=255)
        vg = vg.filter(ImageFilter.GaussianBlur(150))
        dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        dark.putalpha(Image.eval(vg, lambda v: 255 - v))
        img.alpha_composite(dark)

    elif sc == "cta":
        sky(img, (255, 40, 90), (120, 30, 200))
        d = ImageDraw.Draw(img)
        avatar(d, W/2 - 200, 1400, 60, "hero", T, 0, "cheer")
        avatar(d, W/2 + 200, 1400, 60, "noob", T, 0, "cheer", face_dir=-1)
        sticker(img, "PARTE 2", W/2, 560, 200, (0, 0, 0), fg=(255, 230, 40), rot=-5, scale=1 + .07*math.sin(t*9))
        sticker(img, "SÍGUEME +", W/2, 820, 100, (255, 255, 255), fg=(255, 40, 90), rot=4)

    if shake != (0, 0):
        img = Image.fromarray(np.roll(np.array(img), shake, axis=(0, 1)))
    return img

def draw_captions(img, segs, T):
    seg = None
    for s in segs:
        if s["start"] - .05 <= T <= s["start"] + s["dur"] + .15: seg = s
    if not seg: return
    words = seg["words"]
    # chunk de 3 palabras alrededor de la actual
    cur = 0
    for i, (w, a, b) in enumerate(words):
        if T >= a: cur = i
    c0 = (cur // 3) * 3
    chunk = words[c0:c0 + 3]
    d = ImageDraw.Draw(img)
    f = font(92)
    texts = [w.upper() for w, _, _ in chunk]
    gap = 34
    widths = [d.textlength(t, font=f) for t in texts]
    while sum(widths) + gap * (len(texts) - 1) > W - 120:
        f = font(f.size - 6); widths = [d.textlength(t, font=f) for t in texts]
    tot = sum(widths) + gap * (len(texts) - 1)
    x = W/2 - tot/2
    y = 1640
    for i, (txt, wd) in enumerate(zip(texts, widths)):
        a = chunk[i][1]
        if c0 + i == cur:
            k = min(1, (T - a) / .08)
            ff = font(int(f.size * (1.16 - .06 * k)))
            outlined_text(d, (x + wd/2, y), txt, ff, (255, 230, 40), sw=12)
        else:
            outlined_text(d, (x + wd/2, y), txt, f, (255, 255, 255), sw=11)
        x += wd + gap

def render(segs, total, out_video):
    n = int(total * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                          "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", out_video],
                         stdin=subprocess.PIPE)
    for i in range(n):
        T = i / FPS
        seg = segs[0]
        for s in segs:
            if T >= s["start"] - .1: seg = s
        t = T - seg["start"]
        img = render_scene(seg, max(0, t), T)
        # transición: flash blanco breve al cambiar de escena
        if 0 <= t < .08 and seg is not segs[0]:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(180 * (1 - t / .08)))))
        draw_captions(img, segs, T)
        p.stdin.write(img.convert("RGB").tobytes())
        if i % 150 == 0: print(f"frame {i}/{n}", flush=True)
    p.stdin.close(); p.wait()

def mix_audio(segs, total, out_wav):
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    fx = np.zeros(n, np.float32)
    def put(buf, a, t):
        s = int(t * SR); e = min(n, s + len(a)); buf[s:e] += a[:e - s]
    for s in segs:
        put(voice, s["audio"], s["start"])
        st, du = s["start"], s["dur"]
        put(fx, sfx("whoosh") * .5, max(0, st - .1))
        sc = s["scene"]
        if sc == "intro": put(fx, sfx("pop"), st + .5); put(fx, sfx("boom") * .6, st + .5)
        if sc == "confident": put(fx, sfx("pop"), st + .6)
        if sc == "lava": put(fx, sfx("boing"), st + (du + .18) * .3); put(fx, sfx("death"), st + (du + .18) * .7)
        if sc == "respawn": put(fx, sfx("pop"), st)
        if sc == "noob": put(fx, sfx("pop"), st + (du + .18) * .6)
        if sc == "talk": put(fx, sfx("pop"), st + .5)
        if sc == "void": put(fx, sfx("whoosh"), st); put(fx, sfx("whoosh"), st + .4)
        if sc == "finish": put(fx, sfx("ding"), st + (du + .18) * .3)
        if sc == "twist": put(fx, sfx("boom"), st + (du + .18) * .45)
        if sc == "cta": put(fx, sfx("pop"), st)
    m = music(n) * .55
    # ducking: baja la música cuando habla
    envv = np.convolve(np.abs(voice), np.ones(4410) / 4410, "same")
    m *= 1 - .55 * np.clip(envv * 12, 0, 1)
    # silencio musical en el giro dramático
    for s in segs:
        if s["scene"] == "twist":
            a = int(s["start"] * SR); b = int((s["start"] + s["dur"] * .45) * SR)
            m[a:b] *= .15
    mix = voice + fx * .7 + m
    mix /= max(1, np.abs(mix).max() / .95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", default="obby_tiktok.mp4")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        clips = synth_voice(a.voice, tmp)
        segs, total = build_timeline(clips)
        print(f"duración: {total:.1f}s")
        wav = os.path.join(tmp, "mix.wav"); vid = os.path.join(tmp, "v.mp4")
        mix_audio(segs, total, wav)
        render(segs, total, vid)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", a.out], check=True)
    print("OK ->", a.out)

if __name__ == "__main__":
    main()
