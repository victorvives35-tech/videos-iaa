#!/usr/bin/env python3
"""Historia 14: THE TREASURE — búsqueda del tesoro por pistas. La fuente se abre con HUSS.

Uso: python3 treasure.py --voice ruta/en_US-ryan-high.onnx [--out treasure.mp4]
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
import hunt as hn
from dont_say import granny, confetti
from circle import llama
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)
from hunt import neon_city, screen, tv_overlay, money_rain, captions_single, tint, flash, tone, crowd_roar, PINK, PURPLE, NEON, GOLD

ME = CHARS["me"]
RED = (255, 40, 40)
GND = 1450
MOM = dict(head=(255, 205, 160), torso=(230, 90, 120), legs=(80, 60, 120), hair=(110, 60, 30), logo=None, long_hair=True)
BAKER = dict(head=(255, 205, 160), torso=(250, 250, 250), legs=(60, 60, 70), hair=None, logo=None)
PAPER = (245, 235, 200)

SCRIPT = [
    ("In this town, there's a TV show called The Treasure.", "intro", None),
    ("One million dollars, hidden somewhere in town. Every clue leads to the next one.", "rules", None),
    ("The whole town started digging. Even the dogs.", "dig", None),
    ("Clue one said: where bread is born.", "clue1", None),
    ("The bakery! Inside a baguette, I found clue two.", "bakery", None),
    ("It said: ask the llama. So I asked the llama. The llama spat on me.", "llama", None),
    ("But the spit landed on clue three. Thank you, llama.", "llama_b", None),
    ("Clue three: Grandma knows. I asked Grandma. She said: play bingo with me first.", "bingo", None),
    ("Six hours of bingo later... clue four.", "bingo_b", None),
    ("It said: the fountain only opens with the magic word.", "fountain", None),
    ("I tried please. I tried abracadabra. Nothing. Then I said:", "fountain_huss", "solo", 6),
    ("The fountain opened! Inside... the last clue.", "fountain_b", None),
    ("It said: the treasure is under your bed.", "bed", None),
    ("MY bed?! I ran home!", "run", None),
    ("And there was my mom... wearing a brand new golden necklace.", "mom", None),
    ("She found it while cleaning my room. Lesson learned: always clean your room.", "end", None),
]

DAY = {"dig": "DAY 1", "clue1": "CLUE 1", "bakery": "CLUE 2", "llama": "CLUE 2", "llama_b": "CLUE 3", "bingo": "CLUE 3",
       "bingo_b": "CLUE 4", "fountain": "CLUE 4", "fountain_huss": "CLUE 4", "fountain_b": "CLUE 5", "bed": "CLUE 5"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.1, (.5, .5), (.5, .5)),
    "dig": (1.15, 1.0, (.5, .62), (.5, .62)), "clue1": (1.0, 1.15, (.5, .5), (.5, .48)),
    "bakery": (1.0, 1.35, (.5, .6), (.6, .6)), "llama": (1.0, 1.3, (.5, .62), (.35, .6)),
    "llama_b": (1.3, 1.0, (.35, .6), (.5, .6)), "bingo": (1.0, 1.2, (.5, .6), (.5, .6)),
    "bingo_b": (1.2, 1.0, (.5, .6), (.5, .6)), "fountain": (1.0, 1.2, (.5, .6), (.5, .62)),
    "fountain_huss": (1.15, 1.0, (.5, .6), (.5, .6)), "fountain_b": (1.0, 1.4, (.5, .6), (.5, .66)),
    "bed": (1.0, 1.15, (.5, .5), (.5, .48)), "run": (1.1, 1.1, (.4, .62), (.6, .62)),
    "mom": (1.0, 1.6, (.5, .6), (.42, .55)), "end": (1.2, 1.0, (.5, .58), (.5, .6)),
}

# ------------------------------------------------------------------ piezas
def note_card(d, lines, T, scale=1.0):
    w, h = 860 * scale, 760 * scale
    x0, y0 = W / 2 - w / 2, 420
    d.polygon([(x0, y0 + 10), (x0 + w, y0), (x0 + w + 10, y0 + h), (x0 - 10, y0 + h - 10)], fill=PAPER, outline=(170, 150, 110))
    d.text((W / 2, y0 + 80), "CLUE", font=font(70), fill=(180, 60, 40), anchor="mm")
    for q, (txt, sz) in enumerate(lines):
        d.text((W / 2, y0 + 230 + q * 170), txt, font=font(sz), fill=(60, 40, 20), anchor="mm")
    d.text((x0 + w - 70, y0 + h - 70), "X", font=font(90), fill=RED, anchor="mm")

def small_note(d, x, y, s=1.0, rot=0):
    d.rectangle([x - 50 * s, y - 35 * s, x + 50 * s, y + 35 * s], fill=PAPER, outline=(170, 150, 110), width=3)
    d.text((x, y), "?", font=font(int(50 * s)), fill=(180, 60, 40), anchor="mm")

def hole(d, x, y, r):
    d.ellipse([x - r, y - r * .35, x + r, y + r * .35], fill=(90, 60, 35))
    d.ellipse([x - r * 1.3, y - r * .2, x - r * .6, y + r * .25], fill=(130, 90, 50))

def shovel(d, x, y, T, k=0):
    a = math.sin(T * 8 + k) * .5
    ex, ey = x + 90 * math.sin(a), y - 160 * math.cos(a)
    d.line([x, y, ex, ey], fill=(140, 100, 60), width=10)
    d.polygon([(x - 25, y), (x + 25, y), (x + 15, y + 50), (x - 15, y + 50)], fill=(170, 170, 180))

def dog(d, x, y, s, T):
    col = (200, 150, 90)
    block(d, [x - s * 1.3, y - s * 1.5, x + s * 1.3, y - s * .6], col)
    for lx in (-1, 1): block(d, [x + lx * s - s * .15, y - s * .7, x + lx * s + s * .15, y], col)
    hx = x + s * 1.3
    block(d, [hx - s * .2, y - s * 2.3, hx + s * .8, y - s * 1.4], col)
    d.ellipse([hx + s * .5, y - s * 1.9, hx + s * .8, y - s * 1.7], fill=(30, 20, 20))
    for q in range(4):  # tierra volando
        a = T * 10 + q; dx = -s * 1.6 - (q * 25) - 30 * abs(math.sin(a)); dy = -s * (1 + .5 * abs(math.sin(a + 1)))
        d.ellipse([x + dx - 10, y + dy - 10, x + dx + 10, y + dy + 10], fill=(110, 75, 40))

def bakery(d, T):
    sky(Image.new("RGBA", (1, 1)), (0, 0, 0), (0, 0, 0))
    d.rectangle([0, 0, W, GND], fill=(255, 225, 180))
    for row in range(2):
        y = 560 + row * 220
        d.rectangle([60, y + 70, W - 60, y + 90], fill=(140, 90, 50))
        for j in range(4):
            x = 160 + j * 240
            d.rounded_rectangle([x - 100, y + 30, x + 100, y + 70], radius=20, fill=(210, 150, 70), outline=(120, 70, 20), width=3)
    d.rectangle([0, GND, W, 2000], fill=(210, 180, 140))
    block(d, [0, 1250, W, GND], (190, 120, 70))

def fountain(d, T, open_=0.):
    cx = W / 2
    d.ellipse([cx - 380, 1300, cx + 380, 1520], fill=(160, 160, 175), outline=(110, 110, 125), width=8)
    d.ellipse([cx - 340, 1320, cx + 340, 1490], fill=(90, 170, 230))
    rise = 260 * open_
    block(d, [cx - 70, 1080 - rise, cx + 70, 1400 - rise], (170, 170, 185))
    d.ellipse([cx - 160, 1040 - rise, cx + 160, 1120 - rise], fill=(170, 170, 185), outline=(110, 110, 125), width=6)
    if open_ < .2:
        for q in range(8):  # chorros
            a = q / 8 * math.pi
            for p in range(6):
                tt = (p / 6 + T * .8) % 1
                px = cx + math.cos(a) * 200 * tt; py = 1060 - 220 * tt + 300 * tt * tt
                d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(160, 210, 255))
    else:
        glow = Image.new("RGBA", (1, 1))
        d.rectangle([cx - 60, 1400 - rise, cx + 60, 1400], fill=(60, 50, 40))
        small_note(d, cx, 1400 - rise * .5, 1.0)
    return cx

def bed(d, x, y):
    block(d, [x - 300, y - 160, x + 300, y], (90, 140, 220))
    block(d, [x - 300, y - 210, x - 120, y - 150], (250, 250, 250))
    d.rectangle([x - 310, y - 300, x - 280, y + 40], fill=(120, 80, 50)); d.rectangle([x + 280, y - 220, x + 310, y + 40], fill=(120, 80, 50))
    d.rectangle([x - 280, y, x + 280, y + 40], fill=(40, 30, 25))

def messy_room(d, T, clean=False):
    d.rectangle([0, 0, W, 1500], fill=(240, 220, 190))
    d.rectangle([0, 1500, W, 2000], fill=(170, 120, 80))
    d.rectangle([700, 400, 960, 700], fill=(150, 210, 255), outline=(120, 80, 50), width=12)
    if not clean:
        rnd = random.Random(4)
        for q in range(14):
            x, y = rnd.uniform(60, W - 60), rnd.uniform(1480, 1800)
            col = rnd.choice([(230, 80, 80), (80, 140, 230), (250, 210, 60), (120, 200, 120)])
            d.rectangle([x - 40, y - 15, x + 40, y + 15], fill=col)

def necklace(d, x, y, s, T):
    d.arc([x - s, y - s * .8, x + s, y + s * .6], 20, 160, fill=GOLD, width=max(5, int(s * .12)))
    d.regular_polygon((x, y + s * .55, s * .3), 6, rotation=T * 30, fill=GOLD, outline=(150, 110, 10))
    for q in range(3):
        a = T * 4 + q * 2.1
        d.regular_polygon((x + s * 1.2 * math.cos(a), y + s * .3 + s * .6 * math.sin(a), 10), 4, rotation=45, fill=(255, 255, 255))

def chest(d, x, y, s, open_=1.):
    block(d, [x - s * 1.5, y - s, x + s * 1.5, y], (150, 90, 40))
    d.rectangle([x - s * 1.5, y - s * .55, x + s * 1.5, y - s * .45], fill=GOLD)
    d.polygon([(x - s * 1.5, y - s), (x + s * 1.5, y - s), (x + s * 1.3, y - s - s * 1.1 * open_), (x - s * 1.3, y - s - s * 1.1 * open_)], fill=(170, 110, 50))

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    sc = seg["scene"]; dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]

    if sc == "intro":
        d = neon_city(img, T)
        p = ease(min(1, t / .5))
        screen(d, box, [("THE", 90, (255, 255, 255)), ("TREASURE", int(170 * (.6 + .4 * p)), GOLD), ("FOLLOW THE CLUES", 50, NEON)])
        chest(d, W / 2, 1600, 90, .5 + .5 * abs(math.sin(T * 2)))
        ovl.append(None)

    elif sc == "rules":
        town(img, T); d = ImageDraw.Draw(img)
        # mapa del tesoro
        d.polygon([(90, 400), (990, 380), (1000, 1250), (80, 1270)], fill=PAPER, outline=(170, 150, 110))
        pts = [(220, 1100), (380, 900), (300, 700), (560, 640), (720, 860), (860, 560)]
        for a_, b_ in zip(pts, pts[1:]):
            for q in range(6):
                t_ = q / 6
                d.ellipse([a_[0] + (b_[0] - a_[0]) * t_ - 7, a_[1] + (b_[1] - a_[1]) * t_ - 7, a_[0] + (b_[0] - a_[0]) * t_ + 7, a_[1] + (b_[1] - a_[1]) * t_ + 7], fill=(180, 60, 40))
        d.text(pts[-1], "X", font=font(120), fill=RED, anchor="mm")
        stk("$1,000,000", W / 2, 260, 120, (90, 200, 90), rot=-4, scale=1 + .05 * math.sin(T * 10))
        ovl.append(None)

    elif sc == "dig":
        d = town(img, T)
        for i, x in enumerate([130, 330, 760, 960]):
            hole(d, x, GND + 120, 90)
            avatar(d, x - 40, GND + 110, 42, npc(2000 + i), T, 0, "out", "angry", look=1)
            shovel(d, x + 20, GND + 100, T, i)
        dog(d, 560, GND + 220, 55, T)
        hole(d, 470, GND + 240, 70)
        stk("EVERYONE DIGGING", W / 2, 400, 100, (130, 90, 50), rot=-4)
        if u > .5: stk("EVEN THE DOGS", W / 2, 600, 100, (200, 150, 90), rot=4)
        ovl.append(DAY[sc])

    elif sc in ("clue1", "bed"):
        sky(img, (60, 40, 30), (100, 70, 50)); d = ImageDraw.Draw(img)
        lines = [("WHERE BREAD", 110), ("IS BORN", 110)] if sc == "clue1" else [("UNDER", 120), ("YOUR BED", 120)]
        note_card(d, lines, T, .5 + .5 * ease(min(1, u * 3)))
        if sc == "bed" and u > .55:
            stk("?!?!", W / 2, 1400, 180, RED, rot=6); amp = 6
        ovl.append(DAY[sc])

    elif sc == "bakery":
        d = ImageDraw.Draw(img); bakery(d, T)
        avatar(d, 800, GND, 64, BAKER, T, 0, "out", "smile", look=-1)
        top = avatar(d, 320, GND, 66, ME, T, 0, "out", "laugh", look=1)
        bx = 520
        d.rounded_rectangle([bx - 180, 1200, bx + 180, 1260], radius=28, fill=(210, 150, 70), outline=(120, 70, 20), width=4)
        if u > .5:
            d.rectangle([bx - 20, 1215, bx + 20, 1245], fill=(80, 50, 20))
            small_note(d, bx, 1100 - 40 * math.sin(T * 4), .9)
            stk("CLUE 2!", W / 2, 400, 140, GOLD, fg=(255, 255, 255), rot=-4)
        else:
            stk("BAKERY", W / 2, 400, 140, (210, 150, 70), rot=4)
        ovl.append(DAY[sc])

    elif sc in ("llama", "llama_b"):
        d = town(img, T)
        llama(d, 760, GND + 150, 78, T, look=-1)
        top = avatar(d, 300, GND + 150, 66, ME, T, 0, "out" if sc == "llama" else "up", "shock" if u > .5 or sc == "llama_b" else "smile", look=1)
        if sc == "llama":
            if u > .55:
                sp = min(1, (u - .55) * 4)
                sx, sy = 760 - 110 - (760 - 110 - 330) * sp, GND + 150 - 78 * 4.1
                d.ellipse([sx - 26, sy - 18, sx + 26, sy + 18], fill=(220, 240, 220), outline=(180, 200, 180))
                if sp >= 1:
                    d.ellipse([300 - 45, top + 20, 300 + 45, top + 90], fill=(220, 240, 220, 200))
                stk("PTOO!", 560, 900, 130, (220, 240, 220), fg=(30, 80, 30), rot=-8)
            stk("ASK THE LLAMA", W / 2, 400, 110, (240, 80, 120), rot=-4)
        else:
            small_note(d, 300, top + 60, 1.0)
            stk("CLUE 3", W / 2, 400, 140, GOLD, fg=(255, 255, 255), rot=-4)
            if u > .5: stk("THANK YOU, LLAMA", W / 2, 600, 90, (240, 80, 120), rot=4)
        ovl.append(DAY[sc])

    elif sc in ("bingo", "bingo_b"):
        sky(img, (250, 230, 200), (230, 210, 180)); d = ImageDraw.Draw(img)
        d.rectangle([0, GND, W, 2000], fill=(160, 110, 80))
        block(d, [100, 1250, 980, 1320], (120, 80, 50))
        for side, x in ((1, 300), (-1, 780)):
            for q in range(3):  # cartones de bingo
                d.rectangle([x - 90 + q * 2, 1170, x + 90, 1250], fill=(255, 255, 255), outline=(60, 60, 60), width=2)
        granny(d, 780, GND, 62, T, "out", "laugh", look=-1)
        top = avatar(d, 300, GND, 62, ME, T, 0, "down", "flat" if sc == "bingo" else "shock", look=1)
        balls = [7, 22, 41, 13, 68, 5]
        bi = balls[int(T * 2) % len(balls)]
        d.ellipse([480, 700, 600, 820], fill=(255, 220, 60), outline=(160, 120, 20), width=6)
        d.text((540, 760), str(bi), font=font(56), fill=(30, 30, 30), anchor="mm")
        if sc == "bingo":
            stk("BINGO FIRST", W / 2, 400, 120, (170, 90, 160), rot=-4)
        else:
            stk("6 HOURS LATER", W / 2, 400, 110, (30, 30, 40), fg=(255, 255, 255), rot=-4)
            d.rectangle([300 - 70, top + 75, 300 + 70, top + 95], fill=(110, 80, 60))  # ojeras
            if u > .5: small_note(d, 540, 1100, 1.0); stk("CLUE 4", W / 2, 600, 120, GOLD, fg=(255, 255, 255), rot=4)
        ovl.append(DAY[sc])

    elif sc in ("fountain", "fountain_huss", "fountain_b"):
        d = town(img, T)
        open_ = 0.
        if sc == "fountain_huss": open_ = max(0, (k + 1) / seg["nh"]) * .15
        if sc == "fountain_b": open_ = ease(min(1, u / .5))
        fountain(d, T, open_)
        z = 1 + .12 * hit
        face = "flat"
        if sc == "fountain_huss": face = "yell" if hit > .2 else "flat"
        if sc == "fountain_b": face = "laugh"
        avatar(d, 180, GND + 250, 60 * z, ME, T, 0, "out" if hit > .1 else ("up" if sc == "fountain_b" else "down"), face, look=1)
        if sc == "fountain":
            stk("MAGIC WORD?", W / 2, 400, 120, (90, 170, 230), rot=-4)
        elif sc == "fountain_huss":
            if k < 0:
                third = min(1, int(u * 4))
                stk(["PLEASE?", "ABRACADABRA?"][third], W / 2, 400, 110, (255, 255, 255), fg=(40, 40, 40), rot=-4 + 6 * third)
                if u > .15: stk("NOTHING", W / 2, 600, 100, RED, rot=4)
            elif k < seg["nh"]:
                for j in range(k + 1):
                    stk("HUSS", 180 + (j * 191) % 720, 360 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                        rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
            amp = int(22 * hit)
        else:
            stk("IT OPENED!", W / 2, 400, 140, GOLD, fg=(255, 255, 255), rot=-4, scale=1 + .05 * math.sin(T * 10))
            if u < .2: flash(img, 1 - u / .2)
        ovl.append(DAY[sc])

    elif sc == "run":
        town(img, T, cam=t * 1300); d = ImageDraw.Draw(img)
        for q in range(12):
            y = 1200 + q * 35; d.line([0, y, 400, y], fill=(255, 255, 255), width=5)
        avatar(d, 640, GND + 200 - abs(math.sin(T * 10)) * 50, 70, ME, T * 2.5, 1.7, "up", "yell", look=1)
        stk("MY BED?!", W / 2, 400, 150, RED, rot=-5, scale=1 + .06 * math.sin(T * 12))
        amp = 5
        ovl.append(None)

    elif sc in ("mom", "end"):
        d = ImageDraw.Draw(img)
        messy_room(d, T, clean=True)
        bed(d, 560, 1600)
        chest(d, 830, 1760, 50, 1.0)
        top = avatar(d, 300, 1760, 70, MOM, T, 0, "out" if sc == "mom" else "up", "laugh", look=1)
        necklace(d, 300, top + 70 * 1.25 * 1.05 + 70 * .55, 70, T)
        avatar(d, 760, 1760, 62, ME, T, 0, "up", "shock", look=-1)
        if sc == "mom":
            if u > .45: stk("GOLDEN NECKLACE", W / 2, 400, 110, GOLD, fg=(255, 255, 255), rot=-4, scale=1 + .05 * math.sin(T * 10))
        else:
            d.rectangle([60, 1080, 330, 1160], fill=(255, 255, 255), outline=(60, 60, 60), width=3)
            d.text((195, 1120), "CLEAN ROOM", font=font(34), fill=(40, 160, 60), anchor="mm")
            stk("LESSON LEARNED", W / 2, 400, 110, (40, 90, 210), rot=-4)
            if u > .45: stk("CLEAN YOUR ROOM", W / 2, 600, 100, (40, 160, 60), fg=(255, 255, 255), rot=4)
        ovl.append(None)

    else:
        return ORIG_RENDER(seg, t, T)

    img = camera(img, sc, u)
    for day in ovl:
        tv_overlay(img, T, day)
    for a_, k_ in later:
        sticker(img, *a_, **k_)
    if amp: img = shake_img(img, amp)
    return img

def camera(img, key, u):
    if key not in CAMS: return img
    z0, z1, (x0, y0), (x1, y1) = CAMS[key]
    kk = ease(u); z = z0 + (z1 - z0) * kk
    cx, cy = (x0 + (x1 - x0) * kk) * W, (y0 + (y1 - y0) * kk) * H
    cw, ch = W / z, H / z
    l = min(max(0, cx - cw / 2), W - cw); tp = min(max(0, cy - ch / 2), H - ch)
    return img.crop((int(l), int(tp), int(l + cw), int(tp + ch))).resize((W, H), Image.BILINEAR)

# ------------------------------------------------------------------ audio
def dig_sound(dur):
    n = int(SR * dur); out = np.zeros(n, np.float32)
    for q in range(int(dur * 3)):
        s = int(q / 3 * SR); k = min(n - s, int(.15 * SR))
        out[s:s + k] += (np.random.randn(k) * np.exp(-np.arange(k) / SR * 25) * .15).astype(np.float32)
    return out

def spit():
    n = int(SR * .3); t = np.arange(n) / SR
    x = np.random.randn(n) * np.exp(-t * 15) + np.sin(2 * np.pi * 220 * t) * np.exp(-t * 20)
    return (x * .25).astype(np.float32)

def rumble(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 45 * t) + .4 * np.random.randn(n) * .3) * .25 * np.minimum(1, t / .2) * np.minimum(1, (dur - t) / .3)).astype(np.float32)

def water(dur):
    n = int(SR * dur); x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 800) | (f > 5000)] = 0
    y = np.fft.irfft(X, n); y /= np.abs(y).max()
    return (y * .06).astype(np.float32)

ORIG_MIX = hn.ORIG_MIX

def mix_audio(segs, total, out_wav):
    ORIG_MIX(segs, total, out_wav)
    with wave.open(out_wav) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = a.copy(); n = len(a); fx = np.zeros(n, np.float32)
    def put(x, t):
        s_ = int(t * SR); e = min(n, s_ + len(x))
        if e > s_: fx[s_:e] += x[:e - s_]
    by = {s["scene"]: s for s in segs}
    s = by["intro"]; put(m.sfx("boom") * .8, s["start"]); put(tone(880, .4) + tone(1320, .4), s["start"] + .4)
    s = by["rules"]; put(m.sfx("ding"), s["start"] + .3)
    s = by["dig"]; put(dig_sound(s["dur"] + .2), s["start"])
    for key in ("clue1", "bed"): put(m.sfx("whoosh") * .6, by[key]["start"])
    s = by["bakery"]; put(m.sfx("ding") * .7, s["start"] + (s["dur"] + .2) * .5)
    s = by["llama"]; put(spit(), s["start"] + (s["dur"] + .2) * .55)
    s = by["llama_b"]; put(m.sfx("ding") * .7, s["start"] + .1)
    s = by["bingo_b"]; put(m.sfx("ding") * .7, s["start"] + (s["dur"] + .2) * .5)
    s = by["fountain"]; put(water(s["dur"] + by["fountain_huss"]["dur"] + .4), s["start"])
    s = by["fountain_b"]; put(rumble(1.4), s["start"]); put(m.sfx("ding"), s["start"] + 1.0)
    s = by["bed"]; put(m.sfx("boom") * .7, s["start"] + (s["dur"] + .2) * .55)
    s = by["run"]; put(m.sfx("whoosh"), s["start"])
    s = by["mom"]; put(m.sfx("ding") * .8, s["start"] + (s["dur"] + .2) * .45)
    voice = np.zeros(n, np.float32)
    for s in segs:
        st_ = int(s["start"] * SR); e = min(n, st_ + len(s["audio"])); voice[st_:e] += np.abs(s["audio"][:e - st_])
    talk = np.convolve(np.clip(np.convolve(voice, np.ones(2205) / 2205, "same") * 25, 0, 1), np.ones(4410) / 4410, "same")
    a += fx * (1 - .55 * talk)
    a /= max(1, np.abs(a).max() / .95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

ORIG_RENDER = hn.ORIG_RENDER
hn.SHOW = "TREASURE"
hn.TICKER = "  LIVE · THE TREASURE · $1,000,000 HIDDEN IN TOWN · FOLLOW THE CLUES · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "treasure.mp4"]
    m.main()
