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
    ("In this town, every kid gets a superpower on their tenth birthday.", "town", None),
    ("My best friend got super speed.", "speed", None),
    ("My sister got to fly.", "fly", None),
    ("And me? I got... the huss.", "me", None),
    ("Everyone laughed at me. Nobody knew what it did.", "laugh", None),
    ("Until one day, a giant monster attacked the town.", "monster", None),
    ("Everyone ran away. But I stood still, and I said:", "stand", None),
    ("", "huss", "solo"),
    ("The monster stopped... and started dancing.", "dance", None),
    ("Now everyone in this town says:", "crowd", "crowd"),
    ("Follow for part two.", "cta", None),
]

# ---------------------------------------------------------------- audio
def tts(voice, text, path, tmp, rate=1.0):
    raw = path + ".raw.wav"
    subprocess.run(["piper", "-m", voice, "--length-scale", "0.88", "-f", raw],
                   input=text.encode(), check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
                    f"asetrate=22050*{rate},aresample=44100,acompressor=threshold=-18dB:ratio=4,volume=1.5",
                    "-ac", "1", path], check=True)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    idx = np.where(np.abs(a) > 0.02)[0]
    return a[max(0, idx[0] - 500): idx[-1] + 1500]

def repitch(a, f):
    n = int(len(a) / f)
    return np.interp(np.arange(n) * f, np.arange(len(a)), a).astype(np.float32)

HUSS_STEP = 0.34

def huss_chant(hclip, crowd):
    n = int(SR * (HUSS_STEP * N_HUSS + .6))
    out = np.zeros(n, np.float32)
    for k in range(N_HUSS):
        s = int(k * HUSS_STEP * SR)
        voices = [(1 + .03 * k, 0)] if not crowd else \
            [(.82, 0), (.93, 350), (1.05, -200), (1.18, 500), (1.32, 150)]
        for f, off in voices:
            c = repitch(hclip, f) * (1.0 if not crowd else .45)
            ss = max(0, s + off); e = min(n, ss + len(c))
            out[ss:e] += c[:e - ss]
    return out

def build(voice, tmp):
    hclip = tts(voice, "Huss!", os.path.join(tmp, "huss.wav"), tmp, rate=1.0)
    hclip = hclip[: int(SR * .32)] * np.minimum(1, np.linspace(6, 0, min(len(hclip), int(SR * .32))))
    segs, cur, gap = [], .25, .2
    for i, (txt, scene, huss) in enumerate(SCRIPT):
        audio = np.zeros(0, np.float32); words = []
        if txt:
            audio = tts(voice, txt, os.path.join(tmp, f"l{i}.wav"), tmp, rate=1.04)
            ws = txt.split(); wts = [len(w.strip(".,?!:")) + 2 for w in ws]
            tot, acc, d = sum(wts), 0, len(audio) / SR
            for w, wt in zip(ws, wts):
                words.append((w, cur + d * acc / tot, cur + d * (acc + wt) / tot)); acc += wt
        huss_t0 = None
        if huss:
            huss_t0 = cur + len(audio) / SR + (.15 if txt else 0)
            chant = huss_chant(hclip, huss == "crowd")
            pad = np.zeros(int((huss_t0 - cur) * SR) - len(audio), np.float32)
            audio = np.concatenate([audio, pad, chant])
            words += [("HUSS", huss_t0 + k * HUSS_STEP, huss_t0 + (k + 1) * HUSS_STEP) for k in range(N_HUSS)]
        segs.append(dict(text=txt, scene=scene, start=cur, dur=len(audio) / SR, audio=audio,
                         words=words, huss_t0=huss_t0, huss=huss))
        cur += len(audio) / SR + gap
    return segs, cur + .5

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
        if sc == "me": put(fx, sfx("pop"), st + s["dur"] * .8)
        if sc == "monster": put(fx, sfx("boom"), st + .4); put(fx, sfx("boom"), st + 1.2)
        if s["huss"]:
            for k in range(N_HUSS):
                put(fx, sfx("boom") * .5, s["huss_t0"] + k * HUSS_STEP)
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
    "me":     dict(head=SKIN, torso=(30, 30, 35), legs=(40, 60, 160), hair=(60, 35, 20), logo=(255, 60, 90)),
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
    if c.get("logo"):
        d.polygon([(x - s*.4, ty + s*.5), (x + s*.4, ty + s*.5), (x, ty + s*1.3)], fill=c["logo"])
    hs = s * 1.25; hy = ty - hs * 1.05
    if c.get("long_hair"):
        d.rectangle([x - hs/2 - 8, hy - 6, x + hs/2 + 8, hy + hs * 1.25], fill=c["hair"])
    block(d, [x - hs/2, hy, x + hs/2, hy + hs], c["head"])
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
        d = town(img, T)
        z = 1 + .6 * ease(u)
        avatar(d, W/2, GY + 200 * (z - 1), 60 * z, CHARS["me"], T, 0, "down", "flat" if u < .7 else "shock")
        if u > .7:
            sticker(img, "THE HUSS???", W/2, 520, 140, (130, 130, 130), rot=-6, scale=1 + .05*math.sin(t*10))

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
            sky(img, (255, 210, 40), (255, 90, 30))
            d = ImageDraw.Draw(img)
            for r in range(16):  # rayos
                a = r * math.pi / 8 + t
                d.polygon([(W/2, 1050), (W/2 + 2200*math.cos(a), 1050 + 2200*math.sin(a)),
                           (W/2 + 2200*math.cos(a + .2), 1050 + 2200*math.sin(a + .2))], fill=(255, 240, 120))
            z = 1.6 + .25 * hit
            avatar(d, W/2, 1500 + 120 * (z - 1.6), 95 * z, CHARS["me"], T, 0, "out", "yell" if hit > .2 else "flat")
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
            x = random.randint(250, W - 250); y = random.randint(350, 1000)
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
