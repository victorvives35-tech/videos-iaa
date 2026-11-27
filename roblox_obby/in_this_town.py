#!/usr/bin/env python3
"""Video TikTok vertical estilo historia Roblox "In this town..." con el momento HUSS HUSS HUSS.

Uso: python3 in_this_town.py --voice ruta/en_US-hfc_female-medium.onnx --out in_this_town.mp4
Reutiliza utilidades de make_video.py (mismo directorio).
"""
import argparse, math, os, random, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw
from make_video import (W, H, FPS, SR, font, sky, block, sticker, outlined_text, ease,
                        sfx, music, draw_captions)

N_HUSS = 6
# (texto, escena, huss)  huss: None | "solo" | "crowd"
SCRIPT = [
    ("In this town, every single kid gets a superpower on their tenth birthday!", "town", None),
    ("My best friend? Super speed!", "speed", None),
    ("My sister? She can fly!", "fly", None),
    ("And me?! I got... the HUSS!", "me", "solo"),
    ("Everyone laughed at me! Nobody knew what it did!", "laugh", None),
    ("Until one day... a giant monster attacked the town!", "monster", None),
    ("Everyone ran away! But I stood still... and I said:", "stand", None),
    ("", "huss", "solo"),
    ("The monster stopped... and started DANCING!", "dance", None),
    ("And now, everyone in this town says:", "crowd", "crowd"),
    ("Follow for part two!", "cta", None),
]

# ---------------------------------------------------------------- audio
def tts(voice, text, path, tmp, rate=1.0, ls="0.85", extra="", ns="0.667", nw="0.8"):
    raw = path + ".raw.wav"
    subprocess.run(["piper", "-m", voice, "--length-scale", ls, "--noise-scale", ns, "--noise-w", nw,
                    "--sentence-silence", "0.08", "-f", raw],
                   input=text.encode(), check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
                    f"asetrate=22050*{rate},aresample=44100{extra},acompressor=threshold=-18dB:ratio=4,volume=1.5",
                    "-ac", "1", path], check=True)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    idx = np.where(np.abs(a) > 0.02)[0]
    return a[max(0, idx[0] - 500): idx[-1] + 1500]

def repitch(a, f):
    n = int(len(a) / f)
    return np.interp(np.arange(n) * f, np.arange(len(a)), a).astype(np.float32)

HUSS_STEP = 0.30

def huss_chant(hclip, crowd):
    n = int(SR * (HUSS_STEP * N_HUSS + .6))
    out = np.zeros(n, np.float32)
    for k in range(N_HUSS):
        s = int(k * HUSS_STEP * SR)
        voices = [(1.0, 0)] if not crowd else \
            [(.82, 0), (.93, 350), (1.05, -200), (1.18, 500), (1.32, 150)]
        for f, off in voices:
            c = repitch(hclip, f) * (1.0 if not crowd else .45)
            ss = max(0, s + off); e = min(n, ss + len(c))
            out[ss:e] += c[:e - ss]
    return out

def bandnoise(n, lo, hi):
    x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n); return (y / np.abs(y).max()).astype(np.float32)

HUSS_SAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "huss.wav")

def make_huss(voice, tmp):
    if os.path.exists(HUSS_SAMPLE):  # el HUSS original del video de referencia
        with wave.open(HUSS_SAMPLE) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return a / np.abs(a).max() * .9
    """'HUSS!' del meme: grito agudo y nasal (~360 Hz), con ataque de aire 'h' y cola 'ss' silbada."""
    v = tts(voice, "Huss!", os.path.join(tmp, "huss.wav"), tmp, rate=2.8, ls="1.0",
            extra=",atempo=0.5,atempo=0.72,highpass=f=250,equalizer=f=1800:t=q:w=1.5:g=7")
    v = v[: int(SR * .30)]
    v *= np.minimum(1, np.linspace(0, 12, len(v))) * np.minimum(1, np.linspace(5, 0, len(v)))
    v /= np.abs(v).max()
    h = bandnoise(int(SR * .05), 800, 3000) * np.linspace(0, 1, int(SR * .05)) * .25
    ss_n = int(SR * .17)
    ss = bandnoise(ss_n, 4500, 9000) * np.minimum(1, np.linspace(0, 8, ss_n)) * np.linspace(1, 0, ss_n) ** 1.5 * .45
    out = np.zeros(len(h) + len(v) + ss_n // 2, np.float32)
    out[:len(h)] += h
    out[len(h):len(h) + len(v)] += v * .9
    st = len(h) + int(len(v) * .6)
    out[st:st + ss_n] += ss[: len(out) - st]
    return out / np.abs(out).max() * .9

def build(voice, tmp):
    hclip = make_huss(voice, tmp)
    segs, cur, gap = [], .25, .2
    for i, (txt, scene, huss) in enumerate(SCRIPT):
        audio = np.zeros(0, np.float32); words = []
        if txt:
            # narrador con energía: más rápido, algo más agudo, entonación más variada y con presencia
            audio = tts(voice, txt, os.path.join(tmp, f"l{i}.wav"), tmp, rate=1.09, ls="0.84", ns="0.9", nw="1.0",
                        extra=",equalizer=f=3000:t=q:w=1:g=4,equalizer=f=200:t=q:w=1:g=2")
            ws = txt.split(); wts = [len(w.strip(".,?!:")) + 2 for w in ws]
            tot, acc, d = sum(wts), 0, len(audio) / SR
            for w, wt in zip(ws, wts):
                words.append((w, cur + d * acc / tot, cur + d * (acc + wt) / tot)); acc += wt
        huss_t0 = None
        if huss:
            huss_t0 = cur + len(audio) / SR + (.6 if txt else 0)
            chant = huss_chant(hclip, huss == "crowd")
            pad = np.zeros(int((huss_t0 - cur) * SR) - len(audio), np.float32)
            audio = np.concatenate([audio, pad, chant])
            words += [("HUSS", huss_t0 + k * HUSS_STEP, huss_t0 + (k + 1) * HUSS_STEP) for k in range(N_HUSS)]
        reveal = next((a for w, a, b in words if w.strip(".,!?").upper() == "HUSS"), None)
        segs.append(dict(text=txt, scene=scene, start=cur, dur=len(audio) / SR, audio=audio,
                         words=words, huss_t0=huss_t0, huss=huss, reveal=reveal))
        cur += len(audio) / SR + gap
    return segs, cur + .5

def riser(d):
    n = int(SR * d); t = np.arange(n) / SR
    f = 200 + 1400 * (t / d) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * .25
    return ((tone + .3 * bandnoise(n, 2000, 9000)) * (t / d) ** 2).astype(np.float32)

def mix_audio(segs, total, out_wav):
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32); fx = np.zeros(n, np.float32)
    def put(buf, a, t):
        s = int(t * SR); e = min(n, s + len(a)); buf[s:e] += a[:e - s]
    for s in segs:
        put(voice, s["audio"], s["start"])
        put(fx, sfx("whoosh") * .4, max(0, s["start"] - .1))
        sc, st = s["scene"], s["start"]
        if sc == "speed": put(fx, sfx("whoosh"), st + .3)
        if sc == "fly": put(fx, sfx("boing"), st + .2)
        if sc == "monster": put(fx, sfx("boom"), st + .4); put(fx, sfx("boom"), st + 1.2)
        if s["huss"]:
            for k in range(N_HUSS):
                put(fx, sfx("boom") * .3, s["huss_t0"] + k * HUSS_STEP)
        if sc == "me" and s["reveal"]:
            put(fx, riser(1.2), max(0, s["reveal"] - 1.2)); put(fx, sfx("boom"), s["reveal"]); put(fx, sfx("ding") * .8, s["reveal"])
        if sc == "dance": put(fx, sfx("ding"), st + .8)
        if sc == "cta": put(fx, sfx("pop"), st)
    m = music(n) * .5
    envv = np.convolve(np.abs(voice), np.ones(4410) / 4410, "same")
    m *= 1 - .5 * np.clip(envv * 12, 0, 1)
    for s in segs:  # silencio antes del huss solo para dramatismo
        if s["scene"] == "stand":
            a = int((s["start"] + s["dur"] * .5) * SR); b = int((s["start"] + s["dur"] + .2) * SR)
            m[a:b] *= .1
    mix = voice + fx * .7 + m
    mix /= max(1, np.abs(mix).max() / .95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- personajes
SKIN = (255, 205, 160)
CHARS = {
    "me":     dict(head=SKIN, torso=(40, 90, 210), legs=(40, 90, 210), hair=None, logo=None, jersey="HUSS", cap=(30, 70, 190)),
    "friend": dict(head=(200, 150, 110), torso=(240, 60, 60), legs=(30, 30, 30), hair=(20, 20, 20), logo=(255, 230, 40)),
    "sister": dict(head=SKIN, torso=(255, 120, 200), legs=(140, 80, 200), hair=(230, 180, 60), logo=None, long_hair=True),
    "monster": dict(head=(120, 200, 60), torso=(70, 140, 40), legs=(50, 100, 30), hair=None, logo=None, angry=True),
}
def npc(i):
    r = random.Random(i)
    pick = lambda: (r.randint(40, 240), r.randint(40, 240), r.randint(40, 240))
    return dict(head=r.choice([SKIN, (200, 150, 110), (140, 95, 60), (245, 205, 50)]), torso=pick(), legs=pick(),
                hair=r.choice([(20, 20, 20), (90, 50, 20), (230, 180, 60), None]), logo=None)

def avatar(d, x, y, s, c, t, walk=0., arms="down", face="smile", look=0, rot_bob=0):
    sw = math.sin(t * 14) * walk
    lw = s * .9
    hip = y - s * 2
    for side, ph in ((-1, sw), (1, -sw)):
        cx = x + side * lw * .55 + ph * s * .6
        block(d, [cx - lw/2, hip, cx + lw/2, y], c["legs"])
    tw = s * 2; ty = hip - s * 2
    for side, ph in ((-1, -sw), (1, sw)):
        ax = x + side * (tw/2 + lw/2)
        if arms == "up" or (arms == "dance" and (int(t * 4) + (side > 0)) % 2):
            block(d, [ax - lw/2, ty - s*1.6, ax + lw/2, ty + s*.4], c["head"])
        elif arms == "out":
            xa, xb = ax - lw/2 + side*s*.6, ax + lw/2 + side*s*1.6
            block(d, [min(xa, xb), ty + s*.1, max(xa, xb), ty + s*.9], c["head"])
        else:
            o = ph * s * .5
            block(d, [ax - lw/2 + o, ty, ax + lw/2 + o, ty + s*2], c["head"])
    block(d, [x - tw/2, ty, x + tw/2, hip], c["torso"])
    if c.get("jersey"):
        jf = font(max(10, int(s * .62)))
        d.text((x, ty + s * .75), c["jersey"], font=jf, fill=(255, 205, 40), anchor="mm",
               stroke_width=max(1, int(s * .05)), stroke_fill=(20, 30, 90))
    if c.get("logo"):
        d.polygon([(x - s*.4, ty + s*.5), (x + s*.4, ty + s*.5), (x, ty + s*1.3)], fill=c["logo"])
    hs = s * 1.25; hy = ty - hs * 1.05
    if c.get("long_hair"):
        d.rectangle([x - hs/2 - 8, hy - 6, x + hs/2 + 8, hy + hs * 1.25], fill=c["hair"])
    block(d, [x - hs/2, hy, x + hs/2, hy + hs], c["head"])
    if c.get("cap"):
        d.rectangle([x - hs/2 - 4, hy - s*.35, x + hs/2 + 4, hy + s*.3], fill=c["cap"], outline=(20, 20, 30), width=3)
        d.rectangle([x - hs/2 + (hs*.2 if look >= 0 else -hs*.35), hy + s*.18, x + hs/2 + (hs*.35 if look >= 0 else -hs*.2), hy + s*.34], fill=c["cap"])
        d.text((x, hy - s*.03), "H", font=font(max(10, int(s * .5))), fill=(255, 205, 40), anchor="mm")
    if c.get("hair"):
        d.rectangle([x - hs/2 - 4, hy - s*.25, x + hs/2 + 4, hy + s*.25], fill=c["hair"])
    ex = s * .2 * look
    for e in (-1, 1):
        d.ellipse([x + e*s*.28 + ex - s*.09, hy + hs*.35, x + e*s*.28 + ex + s*.09, hy + hs*.35 + s*.22], fill=(15, 15, 15))
        if c.get("angry"):
            d.line([x + e*s*.45 + ex, hy + hs*.22, x + e*s*.12 + ex, hy + hs*.34], fill=(15, 15, 15), width=max(3, int(s*.12)))
    lw2 = max(3, int(s * .09))
    if face == "smile":
        d.arc([x - s*.3 + ex, hy + hs*.5, x + s*.3 + ex, hy + hs*.85], 10, 170, fill=(15, 15, 15), width=lw2)
    elif face == "laugh":
        d.chord([x - s*.32 + ex, hy + hs*.5, x + s*.32 + ex, hy + hs*.92], 0, 180, fill=(15, 15, 15))
    elif face == "shock":
        d.ellipse([x - s*.15 + ex, hy + hs*.58, x + s*.15 + ex, hy + hs*.9], fill=(15, 15, 15))
    elif face == "flat":
        d.line([x - s*.25 + ex, hy + hs*.72, x + s*.25 + ex, hy + hs*.72], fill=(15, 15, 15), width=lw2)
    elif face == "yell":
        d.ellipse([x - s*.28 + ex, hy + hs*.52, x + s*.28 + ex, hy + hs*.95], fill=(120, 0, 0), outline=(15, 15, 15), width=lw2)
    elif face == "angry":
        d.arc([x - s*.3 + ex, hy + hs*.65, x + s*.3 + ex, hy + hs*1.0], 200, 340, fill=(15, 15, 15), width=lw2)
    return hy

# ---------------------------------------------------------------- escenario
def town(img, t, cam=0., tint=None, ground_y=1450):
    if tint == "night":
        sky(img, (40, 20, 70), (230, 90, 60))
    else:
        sky(img, (90, 170, 255), (200, 235, 255))
    d = ImageDraw.Draw(img)
    for i in range(5):  # nubes
        cx = ((i * 380 + t * 25 - cam * .2) % 1700) - 300; cy = 200 + (i * 151) % 380
        for dx, dy, r in ((0, 0, 65), (55, -18, 55), (-55, 10, 50)):
            d.ellipse([cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r], fill=(255, 255, 255) if tint != "night" else (110, 80, 120))
    cols = [(230, 120, 90), (120, 170, 230), (250, 210, 110), (150, 210, 140), (210, 150, 220)]
    for i in range(-2, 9):  # casas
        x = i * 300 - (cam * .6) % 300
        hh = 300 + (i * 73) % 160
        c = cols[i % len(cols)]
        block(d, [x, ground_y - hh, x + 240, ground_y], c)
        d.polygon([(x - 20, ground_y - hh), (x + 120, ground_y - hh - 130), (x + 260, ground_y - hh)],
                  fill=(150, 60, 50), outline=(20, 20, 30))
        for wx in (40, 140):
            d.rectangle([x + wx, ground_y - hh + 60, x + wx + 60, ground_y - hh + 120],
                        fill=(255, 240, 150) if tint == "night" else (180, 220, 255), outline=(20, 20, 30), width=4)
        d.rectangle([x + 90, ground_y - 120, x + 150, ground_y], fill=(110, 70, 40), outline=(20, 20, 30), width=4)
    d.rectangle([0, ground_y, W, H], fill=(90, 90, 100))
    d.rectangle([0, ground_y, W, ground_y + 25], fill=(120, 190, 90))
    for i in range(-1, 8):
        x = i * 200 - (cam % 200)
        d.rectangle([x, ground_y + 150, x + 110, ground_y + 170], fill=(240, 230, 120))
    return d

def shake_img(img, amp):
    return Image.fromarray(np.roll(np.array(img), (random.randint(-amp, amp), random.randint(-amp, amp)), axis=(0, 1)))

# ---------------------------------------------------------------- escenas
def render_scene(seg, t, T):
    sc = seg["scene"]; dur = seg["dur"] + .2; u = t / dur
    if sc == "me" and seg["huss_t0"] and T >= seg["huss_t0"] - .05:
        sc = "huss"
    if sc == "me":
        dur = seg["huss_t0"] - seg["start"] if seg["huss_t0"] else dur; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); GY = 1450; amp = 0

    if sc == "town":
        d = town(img, T, cam=t * 60)
        for i in range(5):
            x = 120 + i * 210; walk = 1
            avatar(d, x + 20 * math.sin(t + i), GY, 34, npc(i), T + i * .3, walk * .7)
        if t > .8:
            sticker(img, "IN THIS TOWN...", W/2, 560, 110, (30, 30, 30), rot=-4)
        if t > 2.2:
            sticker(img, "10th BIRTHDAY = POWER", W/2, 760, 70, (255, 60, 120), rot=3)

    elif sc == "speed":
        d = town(img, T, cam=t * 900)
        for k in range(14):
            y = 900 + k * 40
            d.line([0, y, W/2 - 100, y], fill=(255, 255, 255), width=6)
        avatar(d, W/2, GY, 60, CHARS["friend"], T * 2, 1.6, "out", "smile", look=1)
        sticker(img, "SUPER SPEED", W/2, 560, 120, (240, 60, 60), rot=-5, scale=1 + .05*math.sin(t*12))
        amp = 6

    elif sc == "fly":
        d = town(img, T)
        y = GY - 400 * ease(u / .5) + 30 * math.sin(t * 4)
        avatar(d, W/2, y, 60, CHARS["sister"], T, 0, "up", "smile")
        for k in range(10):  # brillitos
            a = t * 3 + k * .63; r = 220
            sx, sy = W/2 + r * math.cos(a), y - 220 + r * .6 * math.sin(a)
            d.regular_polygon((sx, sy, 16), 4, rotation=t * 90, fill=(255, 240, 120))
        sticker(img, "FLYING", W/2, 560, 130, (255, 120, 200), rot=4)

    elif sc == "me":
        rv = seg["reveal"] or (seg["start"] + dur)
        pre = T < rv
        if pre:
            # suspense: el pueblo mira, se apaga la luz y un foco cae sobre él
            d = town(img, T)
            for i, x in enumerate([110, 290, 790, 970]):
                avatar(d, x, GY, 36, npc(i + 30), T, 0, "down", "shock", look=1 if x < W/2 else -1)
            k = ease((T - seg["start"]) / max(.1, rv - seg["start"]))
            z = 1 + .55 * k
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(190 * k))))
            beam = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(beam)
            bd.polygon([(W/2 - 90, 0), (W/2 + 90, 0), (W/2 + 330, GY + 60), (W/2 - 330, GY + 60)],
                       fill=(255, 250, 200, int(120 * k)))
            img.alpha_composite(beam)
            d = ImageDraw.Draw(img)
            d.ellipse([W/2 - 330, GY + 20, W/2 + 330, GY + 100], fill=(255, 250, 200))
            avatar(d, W/2, GY + 60 * (z - 1), 60 * z, CHARS["me"], T, 0, "down", "flat" if k < .8 else "shock")
            sticker(img, "AND ME???", W/2, 400, 130, (30, 30, 30), rot=-5, scale=1 + .04 * math.sin(t * 9))
            if k > .55:  # caja misteriosa temblando
                bx, by = W/2, 700 + 10 * math.sin(T * 40)
                block(d, [bx - 120, by - 110, bx + 120, by + 110], (130, 40, 220))
                d.rectangle([bx - 18, by - 110, bx + 18, by + 110], fill=(255, 210, 40))
                d.rectangle([bx - 120, by - 18, bx + 120, by + 18], fill=(255, 210, 40))
                d.text((bx, by), "?", font=font(150), fill=(255, 255, 255), anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
            amp = int(10 * max(0, k - .6) / .4)
        else:
            # ¡REVELACIÓN! fondo legendario, rayos, partículas y carta de poder
            r = T - rv
            sky(img, (40, 10, 90), (200, 40, 160))
            d = ImageDraw.Draw(img)
            for q in range(20):
                a = q * math.pi / 10 + T * .8
                d.polygon([(W/2, 1000), (W/2 + 2300*math.cos(a), 1000 + 2300*math.sin(a)),
                           (W/2 + 2300*math.cos(a + .14), 1000 + 2300*math.sin(a + .14))], fill=(255, 200, 60))
            rnd = random.Random(5)
            for q in range(40):  # chispas que salen del centro
                a = rnd.uniform(0, 6.28); sp = rnd.uniform(500, 1400)
                dist = (r * sp + rnd.uniform(0, 600)) % 1100
                px, py = W/2 + math.cos(a) * dist, 1000 + math.sin(a) * dist
                d.regular_polygon((px, py, rnd.randint(8, 20)), 4, rotation=T * 200, fill=(255, 255, 220))
            pz = min(1, r / .18)
            sz = 95 * (.4 + .6 * pz) * (1 + .12 * max(0, 1 - r / .3))
            ball_y = 1530 - abs(math.sin(T * 9)) * 160
            avatar(d, W/2, 1580, sz, CHARS["me"], T, 0, "up", "yell")
            d.ellipse([W/2 + 210, ball_y - 60, W/2 + 330, ball_y + 60], fill=(240, 120, 30), outline=(40, 20, 10), width=6)
            d.line([W/2 + 270, ball_y - 60, W/2 + 270, ball_y + 60], fill=(40, 20, 10), width=5)
            d.arc([W/2 + 180, ball_y - 60, W/2 + 270, ball_y + 60], -90, 90, fill=(40, 20, 10), width=5)
            # carta de poder
            cs = min(1, r / .22)
            cw, ch = 620 * cs, 300 * cs
            cy = 520
            if cs > .05:
                d.rounded_rectangle([W/2 - cw/2, cy - ch/2, W/2 + cw/2, cy + ch/2], radius=int(40 * cs),
                                    fill=(255, 210, 40), outline=(0, 0, 0), width=10)
                if cs > .5: d.rounded_rectangle([W/2 - cw/2 + 18, cy - ch/2 + 18, W/2 + cw/2 - 18, cy + ch/2 - 18],
                                    radius=int(30 * cs), outline=(255, 255, 255), width=5)
                if cs > .9:
                    d.text((W/2, cy - 80), "NEW POWER", font=font(52), fill=(80, 30, 0), anchor="mm")
                    d.text((W/2, cy + 10), "HUSS", font=font(150), fill=(40, 90, 210), anchor="mm",
                           stroke_width=8, stroke_fill=(255, 255, 255))
                    d.text((W/2, cy + 105), "★ LEGENDARY ★", font=font(44), fill=(200, 40, 120), anchor="mm")
            if r < .12:
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(230 * (1 - r / .12)))))
            amp = int(28 * max(0, 1 - r / .4))

    elif sc == "laugh":
        d = town(img, T)
        avatar(d, W/2, GY, 58, CHARS["me"], T, 0, "down", "flat")
        for i, x in enumerate([130, 320, 760, 950]):
            avatar(d, x, GY + 10 * abs(math.sin(t * 9 + i)), 40, npc(i + 10), T, 0, "down", "laugh", look=1 if x < W/2 else -1)
        for k, (x, y, r) in enumerate([(200, 650, -10), (820, 720, 8), (500, 900, -4)]):
            if t > .3 + k * .35:
                sticker(img, "HAHAHA", x, y, 80, (255, 220, 40), fg=(255, 255, 255), rot=r + 5 * math.sin(t*8 + k))

    elif sc == "monster":
        d = town(img, T, tint="night")
        mz = 160 * (.6 + .4 * ease(u / .4))
        step = abs(math.sin(t * 3)) * 40
        avatar(d, W/2 + 60 * math.sin(t * 1.5), GY + 20 - step, mz, CHARS["monster"], T * .4, .6, "out", "angry")
        for i, x in enumerate([100, 300, 800, 990]):
            avatar(d, (x + (t * 300 if x > W/2 else -t * 300)), GY, 30, npc(i + 20), T, 1.5, "up", "shock")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 0, 0, int(50 + 40 * math.sin(t * 10)))))
        sticker(img, "GIANT MONSTER", W/2, 420, 100, (0, 0, 0), fg=(255, 60, 60), rot=-4)
        amp = 18

    elif sc == "stand":
        d = town(img, T, tint="night")
        avatar(d, W/2 + 250, GY - 20, 150, CHARS["monster"], T * .4, 0, "out", "angry", look=-1)
        z = 1 + .5 * ease(u)
        avatar(d, W/2 - 220, GY + 80 * (z - 1), 60 * z, CHARS["me"], T, 0, "down", "flat", look=1)
        dark = Image.new("RGBA", (W, H), (0, 0, 0, int(120 * ease(u))))
        img.alpha_composite(dark)

    elif sc in ("huss", "crowd"):
        k = int((T - seg["huss_t0"]) / HUSS_STEP) if T >= seg["huss_t0"] else -1
        beat = (T - seg["huss_t0"]) % HUSS_STEP if k >= 0 else 1
        hit = max(0, 1 - beat / .15) if 0 <= k < N_HUSS else 0
        if sc == "huss":
            pal = [((255, 210, 40), (255, 90, 30), (255, 240, 120)), ((40, 160, 255), (20, 40, 160), (120, 210, 255)),
                   ((255, 60, 120), (130, 20, 90), (255, 150, 190)), ((130, 255, 90), (20, 130, 60), (210, 255, 160))]
            top, bot, ray = pal[max(0, k) % len(pal)]
            sky(img, top, bot)
            d = ImageDraw.Draw(img)
            for r in range(16):  # rayos
                a = r * math.pi / 8 + t * 1.5
                d.polygon([(W/2, 1050), (W/2 + 2200*math.cos(a), 1050 + 2200*math.sin(a)),
                           (W/2 + 2200*math.cos(a + .2), 1050 + 2200*math.sin(a + .2))], fill=ray)
            z = 1.6 + .35 * hit
            avatar(d, W/2, 1500 + 120 * (z - 1.6), 95 * z, CHARS["me"], T, 0, "out", "yell" if hit > .2 else "flat")
            by = 1560 - (1 - hit) * 220
            d.ellipse([W/2 + 260, by - 70, W/2 + 400, by + 70], fill=(240, 120, 30), outline=(40, 20, 10), width=6)
            d.line([W/2 + 330, by - 70, W/2 + 330, by + 70], fill=(40, 20, 10), width=5)
        else:
            d = town(img, T)
            for row, (y, s, xs) in enumerate([(1250, 34, range(80, W, 160)), (1480, 50, range(40, W + 100, 230))]):
                for j, x in enumerate(xs):
                    c = CHARS["me"] if (row == 1 and j == 2) else (CHARS["sister"] if (row == 1 and j == 4) else npc(row * 10 + j))
                    jump = 50 * hit
                    avatar(d, x, y - jump, s, c, T, 0, "up" if hit > .2 else "down", "yell" if hit > .2 else "smile")
            # el monstruo también
            avatar(d, 120, 1490 - 40 * hit, 70, CHARS["monster"], T, 0, "dance", "smile", look=1)
        random.seed(k * 7 + 3)
        for j in range(max(0, min(k + 1, N_HUSS))):  # HUSS acumulados en pantalla
            x = random.randint(250, W - 250); y = random.randint(260, 540)
            sc_ = 1 + (.35 * hit if j == k else 0)
            sticker(img, "HUSS", x, y, 110, random.choice([(255, 40, 90), (40, 160, 255), (130, 40, 220), (20, 20, 20)]),
                    rot=random.randint(-14, 14), scale=sc_)
        random.seed()
        amp = int(30 * hit)

    elif sc == "dance":
        d = town(img, T, tint="night")
        avatar(d, W/2 + 30 * math.sin(t * 8), GY - abs(math.sin(t * 8)) * 60, 140, CHARS["monster"], T, 0, "dance", "smile")
        avatar(d, 150, GY, 45, CHARS["me"], T, 0, "down", "shock", look=1)
        for k in range(6):  # notas musicales
            x = 200 + k * 140 + 30 * math.sin(t * 3 + k); y = 500 + ((t * 200 + k * 120) % 400)
            d.ellipse([x, y, x + 40, y + 32], fill=(255, 255, 255)); d.rectangle([x + 32, y - 80, x + 40, y + 16], fill=(255, 255, 255))
        if t > .9:
            sticker(img, "?!?!", W/2, 420, 150, (255, 220, 40), fg=(255, 255, 255), rot=-6)

    elif sc == "cta":
        sky(img, (255, 40, 90), (120, 30, 200))
        d = ImageDraw.Draw(img)
        avatar(d, W/2 - 220, 1450, 60, CHARS["me"], T, 0, "up", "smile")
        avatar(d, W/2 + 220, 1450, 60, CHARS["monster"], T, 0, "dance", "smile")
        sticker(img, "PART 2", W/2, 560, 200, (0, 0, 0), fg=(255, 230, 40), rot=-5, scale=1 + .07*math.sin(t*9))
        sticker(img, "FOLLOW +", W/2, 820, 100, (255, 255, 255), fg=(255, 40, 90), rot=4)

    if amp: img = shake_img(img, amp)
    return img

def render(segs, total, out_video):
    n = int(total * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", out_video], stdin=subprocess.PIPE)
    for i in range(n):
        T = i / FPS
        seg = segs[0]
        for s in segs:
            if T >= s["start"] - .1: seg = s
        t = max(0, T - seg["start"])
        img = render_scene(seg, t, T)
        if t < .08 and seg is not segs[0]:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(180 * (1 - t / .08)))))
        draw_captions(img, segs, T)
        p.stdin.write(img.convert("RGB").tobytes())
        if i % 200 == 0: print(f"frame {i}/{n}", flush=True)
    p.stdin.close(); p.wait()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", default="in_this_town.mp4")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        segs, total = build(a.voice, tmp)
        print(f"duración: {total:.1f}s")
        wav = os.path.join(tmp, "mix.wav"); vid = os.path.join(tmp, "v.mp4")
        mix_audio(segs, total, wav)
        render(segs, total, vid)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", a.out], check=True)
    print("OK ->", a.out)

if __name__ == "__main__":
    main()
