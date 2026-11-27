#!/usr/bin/env python3
"""Historia 13: SKY HIGH — concurso de construir la torre más alta. Huss Boy llega al espacio.

Uso: python3 sky_high.py --voice ruta/en_US-ryan-high.onnx [--out sky_high.mp4]
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
import hunt as hn
from dont_say import confetti
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)
from hunt import neon_city, screen, tv_overlay, money_rain, captions_single, tint, flash, tone, crowd_roar, PINK, PURPLE, NEON, GOLD

ME = CHARS["me"]
RED = (255, 40, 40)
ALIEN = dict(head=(120, 230, 90), torso=(80, 60, 160), legs=(60, 40, 120), hair=None, logo=(255, 220, 40))
GROUND = 1500

SCRIPT = [
    ("In this town, there's a TV show called Sky High.", "intro", None),
    ("Build the tallest tower in one week. The winner gets five million dollars.", "rules", None),
    ("Everyone started building. Wood. Bricks. One guy used pancakes.", "build", None),
    ("Day two. The pancake tower got eaten by birds.", "birds", None),
    ("Day three. My tower was taller than the houses.", "h1", None),
    ("My mom called me for dinner. I yelled: I'm busy! I'm making history!", "h1_b", None),
    ("Day four. Taller than the clouds. A plane had to turn left.", "h2", None),
    ("The pilot waved at me. I waved back. He was very confused.", "h2_b", None),
    ("Day five. My neighbor's tower fell... onto his other neighbor's tower. Like dominoes.", "domino", None),
    ("Day six. I could see the whole country. And my house. I left the oven on.", "h3", None),
    ("Day seven. I reached space.", "space", None),
    ("There was no air. Luckily, I brought a fishbowl as a helmet.", "space_b", None),
    ("It was very quiet up there. So I said:", "space_huss", "solo", 3),
    ("And something answered:", "alien_huss", "deep", 3),
    ("Aliens! They loved the huss. They made me their king.", "aliens", None),
    ("They built me a throne. Made of moon cheese.", "aliens_b", None),
    ("Back on Earth, the TV show said: Huss Boy wins five million dollars!", "win", None),
    ("But I can't get down. The aliens took the ladder.", "stuck", None),
    ("So now I'm the richest king in space. And all my money is on Earth.", "end", None),
]

DAY = {"h1_b": "DAY 3", "h2_b": "DAY 4", "space_b": "DAY 7", "aliens_b": "DAY 7", "build": "DAY 1", "birds": "DAY 2", "h1": "DAY 3", "h2": "DAY 4", "domino": "DAY 5", "h3": "DAY 6",
       "space": "DAY 7", "space_huss": "DAY 7", "alien_huss": "DAY 7", "aliens": "DAY 7", "win": "DAY 7"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.15, (.5, .45), (.5, .4)),
    "build": (1.2, 1.0, (.5, .62), (.5, .6)), "birds": (1.0, 1.4, (.5, .55), (.25, .5)),
    "h1": (1.2, 1.0, (.5, .55), (.5, .5)), "h2": (1.0, 1.2, (.5, .45), (.6, .4)),
    "domino": (1.15, 1.0, (.5, .55), (.5, .55)), "h3": (1.0, 1.2, (.5, .45), (.5, .5)),
    "space": (1.4, 1.0, (.5, .4), (.5, .5)), "space_huss": (1.0, 1.15, (.5, .45), (.5, .42)),
    "alien_huss": (1.0, 1.3, (.5, .45), (.7, .35)), "aliens": (1.2, 1.0, (.5, .45), (.5, .45)),
    "win": (1.0, 1.05, (.5, .45), (.5, .45)), "stuck": (1.0, 1.4, (.5, .45), (.5, .55)),
    "end": (1.2, 1.0, (.5, .45), (.5, .45)),
    "h1_b": (1.0, 1.25, (.5, .5), (.5, .35)), "h2_b": (1.2, 1.0, (.55, .45), (.5, .5)),
    "space_b": (1.0, 1.6, (.5, .45), (.5, .5)), "aliens_b": (1.0, 1.2, (.5, .5), (.5, .55)),
}

# ------------------------------------------------------------------ piezas
BLOCKS = [(230, 120, 90), (120, 170, 230), (250, 210, 110), (150, 210, 140), (210, 150, 220), (240, 140, 60)]

def tower(d, x, top, bottom, w=150, seed=0, kind="blocks"):
    y = bottom; i = 0
    while y > top:
        h = 70
        if kind == "pancakes":
            d.ellipse([x - w * .6, y - 30, x + w * .6, y], fill=(220, 160, 80), outline=(160, 100, 40), width=3)
            h = 26
        else:
            col = BLOCKS[(i + seed) % len(BLOCKS)]
            block(d, [x - w / 2, max(top, y - h), x + w / 2, y], col)
        y -= h; i += 1

def sky_for(height):
    """Color del cielo según la altura (0 suelo .. 1 espacio)."""
    a = max(0., min(1., height))
    top = tuple(int(c1 * (1 - a) + c2 * a) for c1, c2 in zip((90, 170, 255), (5, 5, 25)))
    bot = tuple(int(c1 * (1 - a) + c2 * a) for c1, c2 in zip((200, 235, 255), (30, 20, 70)))
    return top, bot

def stars(d, n=80, seed=1):
    rnd = random.Random(seed)
    for q in range(n):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        r = rnd.choice([2, 2, 3, 4]); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))

def earth_curve(d, y=1500):
    d.ellipse([-900, y, W + 900, y + 2400], fill=(60, 120, 220))
    d.ellipse([-500, y + 40, 400, y + 400], fill=(80, 170, 90)); d.ellipse([500, y + 80, 1300, y + 500], fill=(80, 170, 90))
    d.ellipse([-900, y - 30, W + 900, y + 2400], outline=(140, 200, 255), width=20)

def clouds(d, y, T, n=5, seed=2):
    rnd = random.Random(seed)
    for q in range(n):
        cx = (rnd.uniform(0, W) + T * 20) % (W + 300) - 150; cy = y + rnd.uniform(-60, 60)
        for dx, dy, r in ((0, 0, 80), (70, -20, 65), (-70, 10, 60), (130, 10, 50)):
            d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], fill=(255, 255, 255))

def plane(d, x, y, s, T):
    d.ellipse([x - s * 2, y - s * .35, x + s * 2, y + s * .35], fill=(240, 240, 245), outline=(150, 150, 160), width=3)
    d.polygon([(x - s * .2, y), (x - s * .9, y + s * 1.2), (x - s * .4, y + s * 1.2), (x + s * .5, y)], fill=(200, 200, 210))
    d.polygon([(x - s * 1.8, y), (x - s * 2.3, y - s * .8), (x - s * 1.9, y - s * .8), (x - s * 1.4, y)], fill=(200, 60, 60))
    for q in range(4): d.ellipse([x + s * .2 + q * s * .35, y - s * .12, x + s * .4 + q * s * .35, y + s * .08], fill=(120, 190, 240))

def ufo(d, x, y, s, T):
    beam = Image.new("RGBA", (1, 1))
    d.ellipse([x - s * 2.2, y - s * .4, x + s * 2.2, y + s * .5], fill=(170, 170, 190), outline=(90, 90, 110), width=4)
    d.ellipse([x - s, y - s * 1.1, x + s, y + s * .1], fill=(150, 230, 255))
    for q in range(5):
        lx = x - s * 1.6 + q * s * .8
        d.ellipse([lx - 10, y + s * .1 - 10, lx + 10, y + s * .1 + 10], fill=(255, 230, 60) if (int(T * 6) + q) % 2 else (255, 80, 200))

def alien(d, x, y, s, T, face="smile", arms="down"):
    top = avatar(d, x, y, s, ALIEN, T, 0, arms, face)
    hs = s * 1.25
    for e in (-1, 1):
        d.line([x + e * hs * .3, top, x + e * hs * .45, top - s * .8], fill=(90, 200, 70), width=max(3, int(s * .1)))
        d.ellipse([x + e * hs * .45 - s * .15, top - s * .95, x + e * hs * .45 + s * .15, top - s * .65], fill=(255, 80, 200))
    return top

def crown(d, x, top, s):
    d.polygon([(x - s, top), (x - s, top - s * .7), (x - s * .5, top - s * .35), (x, top - s * .9),
               (x + s * .5, top - s * .35), (x + s, top - s * .7), (x + s, top)], fill=GOLD, outline=(0, 0, 0))

def me_on_top(d, x, y, s, T, face="laugh", arms="up"):
    return avatar(d, x, y, s, ME, T, 0, arms, face)

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    full = seg["scene"]
    sc = {"h1_b": "h1", "h2_b": "h2", "space_b": "space", "aliens_b": "aliens"}.get(full, full)
    dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]

    if sc == "intro":
        d = neon_city(img, T)
        p = ease(min(1, t / .5))
        screen(d, box, [("SKY", int(200 * (.6 + .4 * p)), NEON), ("HIGH", int(200 * (.6 + .4 * p)), (255, 255, 255)), ("BUILD TO WIN", 50, GOLD)])
        tower(d, W / 2, 1100 - 300 * ease(u), 1500, 160)
        ovl.append(None)

    elif sc == "rules":
        d = neon_city(img, T)
        third = min(2, int(u * 3))
        screen(d, box, [[("TALLEST", 120, (255, 255, 255)), ("TOWER", 160, NEON)], [("7 DAYS", 200, GOLD)],
                        [("PRIZE", 80, (255, 255, 255)), ("$5,000,000", 130, (90, 220, 90))]][third])
        if third == 2: money_rain(d, T)
        ovl.append(None)

    elif sc in ("build", "birds", "h1", "domino"):
        town(img, T, ground_y=GROUND); d = ImageDraw.Draw(img)
        if sc == "build":
            tower(d, 200, GROUND - 200 * ease(u), GROUND, 130, kind="pancakes")
            tower(d, 540, GROUND - 260 * ease(u), GROUND, 150, seed=1)
            tower(d, 880, GROUND - 230 * ease(u), GROUND, 140, seed=3)
            avatar(d, 330, GROUND + 140, 46, npc(1900), T, 0, "up", "laugh", look=-1)
            me_on_top(d, 540, GROUND - 260 * ease(u), 40, T)
            third = min(2, int(u * 3))
            stk(["WOOD", "BRICKS", "PANCAKES?!"][third], W / 2, 400, 130, [(160, 110, 60), (200, 80, 60), (220, 160, 80)][third], rot=-4 + 4 * third)
        elif sc == "birds":
            left = int(12 * (1 - ease(u)))
            tower(d, 200, GROUND - 26 * left, GROUND, 130, kind="pancakes")
            tower(d, 540, GROUND - 380, GROUND, 150, seed=1)
            me_on_top(d, 540, GROUND - 380, 40, T, "shock")
            for q in range(7):
                bx = 200 + 160 * math.cos(T * 3 + q); by = GROUND - 26 * left - 60 + 80 * math.sin(T * 4 + q)
                d.polygon([(bx - 30, by), (bx, by + 10 * math.sin(T * 20 + q)), (bx + 30, by)], fill=(40, 40, 50))
            stk("BIRDS", W / 2, 400, 140, (40, 40, 50), rot=-5)
            if u > .6: stk("PANCAKES: GONE", W / 2, 600, 95, (220, 160, 80), rot=4)
        elif sc == "h1":
            tower(d, 540, 500, GROUND, 150, seed=1)
            me_on_top(d, 540, 500, 46, T)
            for i, x in enumerate([160, 900]):
                avatar(d, x, GROUND + 140, 42, npc(1910 + i), T, 0, "up", "shock", look=1 if x < W / 2 else -1)
            if full == "h1_b":
                mom = dict(head=(255, 205, 160), torso=(230, 90, 120), legs=(80, 60, 120), hair=(110, 60, 30), logo=None, long_hair=True)
                avatar(d, 230, GROUND + 140, 50, mom, T, 0, "out", "yell", look=1)
                stk("DINNER!", 300, 900, 100, (230, 90, 120), rot=-6)
                if u > .45: stk("I'M BUSY!", 640, 330, 110, (40, 90, 210), rot=5, scale=1 + .06 * math.sin(T * 12))
            else:
                stk("TALLER THAN HOUSES", W / 2, 300, 90, (40, 90, 210), rot=-4)
        else:  # dominó de torres
            fall = ease(u)
            for q, x in enumerate([180, 420, 660]):
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                tower(ld, x, GROUND - 700, GROUND, 110, seed=q + 2)
                ang = -min(80, max(0, (fall * 3 - q) * 80))
                img.alpha_composite(lay.rotate(ang, center=(x + 55, GROUND), resample=Image.BICUBIC))
            d = ImageDraw.Draw(img)
            tower(d, 920, 300, GROUND, 140, seed=1)
            me_on_top(d, 920, 300, 40, T, "shock")
            stk("DOMINOES", W / 2, 400, 130, RED, rot=-5, scale=1 + .05 * math.sin(T * 10))
            amp = int(12 * abs(math.sin(fall * 9))) if fall < 1 else 0
        ovl.append(DAY[full])

    elif sc in ("h2", "h3"):
        hgt = .35 if sc == "h2" else .7
        top_c, bot_c = sky_for(hgt); sky(img, top_c, bot_c); d = ImageDraw.Draw(img)
        if sc == "h2":
            clouds(d, 1350, T, 6)
            px = W + 300 - (W + 900) * ease(u)
            py = 700 - 300 * max(0, (u - .4)) * 2
            if full == "h2_b": px, py = W + 200 - (W + 600) * ease(u), 760
            plane(d, px, py, 70, T)
            tower(d, 540, 900, H, 150, seed=1)
            me_on_top(d, 540, 900, 50, T, "laugh", "out")
            if full == "h2_b":
                stk("HI!", 660, 760, 110, (255, 255, 255), fg=(40, 90, 210), rot=-6)
                if u > .5: stk("CONFUSED PILOT", W / 2, 330, 95, RED, rot=4)
            else:
                stk("ABOVE THE CLOUDS", W / 2, 330, 95, (255, 255, 255), fg=(40, 90, 210), rot=-4)
                if u > .5: stk("TURN LEFT!", W / 2, 560, 100, RED, rot=6)
        else:
            d.ellipse([-600, 1300, W + 600, 3400], fill=(70, 140, 220))
            d.ellipse([-200, 1380, 500, 1700], fill=(80, 170, 90)); d.ellipse([450, 1420, 1300, 1800], fill=(80, 170, 90))
            clouds(d, 1300, T, 4, 5)
            tower(d, 540, 800, H, 150, seed=1)
            top = me_on_top(d, 540, 800, 50, T, "shock" if u > .5 else "laugh", "out")
            if u > .5:
                hx, hy = 760, 1560  # su casa con humo
                block(d, [hx - 30, hy - 30, hx + 30, hy + 20], (230, 120, 90))
                for q in range(4):
                    r = 12 + q * 8; off = (T * 60 + q * 20) % 90
                    d.ellipse([hx - r, hy - 40 - off - r, hx + r, hy - 40 - off + r], fill=(80, 80, 90))
                stk("THE OVEN!", W / 2, 330, 120, RED, rot=4, scale=1 + .06 * math.sin(T * 12))
            else:
                stk("WHOLE COUNTRY", W / 2, 330, 110, (80, 170, 90), fg=(255, 255, 255), rot=-4)
        ovl.append(DAY[full])

    elif sc in ("space", "space_huss", "alien_huss", "aliens", "win", "stuck", "end"):
        sky(img, (5, 5, 25), (30, 20, 70)); d = ImageDraw.Draw(img)
        stars(d)
        earth_curve(d, 1450)
        tower(d, 540, 1000, H, 150, seed=1)
        z = 1 + .15 * hit
        face = "laugh"
        if sc == "space_huss": face = "yell" if hit > .2 else "flat"
        if sc in ("alien_huss",): face = "shock"
        top = avatar(d, 540, 1000, 56 * z, ME, T, 0, "out" if sc == "space_huss" and hit > .1 else "up", face)
        # casco de astronauta
        hs = 56 * z * 1.25
        d.ellipse([540 - hs * .85, top - hs * .25, 540 + hs * .85, top + hs * 1.2], outline=(220, 240, 255), width=6)
        if full == "space_b":
            for q in range(3):  # burbujas dentro de la pecera
                by = top + hs - ((T * 80 + q * 30) % (hs * .9))
                d.ellipse([540 + 30 - 8 + q * 10, by - 8, 540 + 30 + 8 + q * 10, by + 8], outline=(220, 240, 255), width=3)
            stk("NO AIR", W / 2, 330, 140, RED, rot=-4)
            if u > .45: stk("FISHBOWL HELMET", W / 2, 540, 95, (150, 230, 255), fg=(30, 30, 60), rot=4)
        elif sc == "space":
            stk("SPACE", W / 2, 330, 170, PURPLE, fg=(255, 255, 255), rot=-5, scale=1 + .05 * math.sin(T * 10))
        elif sc == "space_huss":
            if 0 <= k < seg["nh"]:
                stk("HUSS!", W / 2 + (k - 1) * 250, 380, 120, (40, 90, 210), rot=-8 + 8 * k, scale=1 + .4 * hit)
                r = 80 + (T - seg["hits"][k]) * 600
                d.ellipse([540 - r, top - r, 540 + r, top + r], outline=(150, 220, 255), width=6)
            else:
                stk("SO QUIET...", W / 2, 380, 110, (30, 30, 50), fg=(255, 255, 255), rot=-3)
        elif sc == "alien_huss":
            ux, uy = 820, 420 + 20 * math.sin(T * 2)
            ufo(d, ux, uy, 80, T)
            if 0 <= k < seg["nh"]:
                stk("HUSS", ux - 100 + (k - 1) * 120, uy + 220 + k * 40, 130, (120, 230, 90), fg=(30, 20, 60), rot=-8 + 8 * k, scale=1 + .4 * hit)
            amp = int(20 * hit)
        elif sc in ("aliens", "stuck", "end"):
            ux, uy = 820, 420 + 20 * math.sin(T * 2)
            ufo(d, ux, uy, 80, T)
            for i, (x, y) in enumerate([(250, 1000), (820, 1000), (150, 760), (930, 760)]):
                alien(d, x, y - abs(math.sin(T * 6 + i)) * 30, 38, T, "laugh", "up" if sc == "aliens" else "down")
            crown(d, 540, top - 10, 50)
            if full == "aliens_b":
                block(d, [540 - 150, 1000 - 40, 540 + 150, 1000 + 60], (250, 220, 90))  # trono de queso
                for q in range(6):
                    d.ellipse([540 - 130 + q * 50, 980 + (q % 2) * 30, 540 - 105 + q * 50, 1005 + (q % 2) * 30], fill=(220, 180, 60))
                stk("MOON CHEESE THRONE", W / 2, 330, 90, (250, 220, 90), fg=(30, 20, 60), rot=-4)
            elif sc == "aliens":
                stk("ALIENS", W / 2, 330, 160, (120, 230, 90), fg=(30, 20, 60), rot=-5)
                if u > .5: stk("KING HUSS", W / 2, 540, 120, GOLD, fg=(255, 255, 255), rot=4)
            elif sc == "stuck":
                lx = 820 + 200 * ease(u); ly = 600 - 100 * ease(u)
                for q in range(6):  # escalera que se llevan
                    d.line([lx - 40, ly + q * 40, lx + 40, ly + q * 40], fill=(160, 110, 60), width=8)
                d.line([lx - 40, ly, lx - 40, ly + 200], fill=(160, 110, 60), width=10); d.line([lx + 40, ly, lx + 40, ly + 200], fill=(160, 110, 60), width=10)
                stk("NO LADDER", W / 2, 330, 140, RED, rot=-4)
            else:
                stk("RICHEST KING", W / 2, 330, 120, GOLD, fg=(255, 255, 255), rot=-4)
                if u > .5: stk("MONEY: ON EARTH", W / 2, 540, 95, (90, 200, 90), rot=4)
        elif sc == "win":
            screen(d, [110, 250, 970, 640], [("WINNER", 100, GOLD), ("HUSS BOY", 90, (255, 255, 255)), ("$5,000,000", 76, (90, 220, 90))])
            confetti(d, T, 50)
            crown(d, 540, top - 10, 50)
        ovl.append(DAY.get(full))

    else:
        return ORIG_RENDER(seg, t, T)

    img = camera(img, full if full in CAMS else sc, u)
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
def jet(dur):
    n = int(SR * dur); x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 100) | (f > 1200)] = 0
    y = np.fft.irfft(X, n); y /= np.abs(y).max(); t = np.arange(n) / SR
    return (y * .2 * np.sin(np.pi * t / dur)).astype(np.float32)

def tweets(dur):
    n = int(SR * dur); out = np.zeros(n, np.float32)
    for q in range(int(dur * 5)):
        s = int(q / 5 * SR); k = min(n - s, int(.12 * SR)); t = np.arange(k) / SR
        out[s:s + k] += (np.sin(2 * np.pi * (2500 + 1500 * t / .12) * t) * np.exp(-t * 20) * .12).astype(np.float32)
    return out

def crash(dur=1.2):
    n = int(SR * dur); out = np.zeros(n, np.float32)
    for q in range(6):
        s = int(q * .18 * SR); b = m.sfx("boom")[: n - s] * .5; out[s:s + len(b)] += b
    return out

def space_hum(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 110 * t) + .5 * np.sin(2 * np.pi * 165 * t)) * .05 * np.minimum(1, t / 1) * np.minimum(1, (dur - t) / 1)).astype(np.float32)

def ufo_sound(dur=1.5):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (600 + 300 * np.sin(2 * np.pi * 3 * t)) * t) * .1 * np.minimum(1, t / .2)).astype(np.float32)

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
    s = by["rules"]
    for q in range(3): put(tone(700, .2), s["start"] + q * (s["dur"] + .2) / 3)
    s = by["build"]
    for q in range(6): put(m.sfx("pop") * .5, s["start"] + q * .4)
    s = by["birds"]; put(tweets(s["dur"]), s["start"])
    s = by["h2"]; put(jet(s["dur"] + .2), s["start"])
    s = by["domino"]; put(crash(), s["start"] + .2)
    s = by["h3"]; put(m.sfx("ding") * .5, s["start"] + (s["dur"] + .2) * .5)
    s = by["space"]; put(space_hum(sum(by[k_]["dur"] for k_ in ("space", "space_huss", "alien_huss", "aliens")) + 1), s["start"])
    s = by["alien_huss"]; put(ufo_sound(), s["start"])
    s = by["aliens"]; put(crowd_roar(1.2) * .4, s["start"] + .2)
    s = by["win"]; put(m.sfx("ding"), s["start"]); put(crowd_roar(1.5) * .5, s["start"] + .2)
    s = by["stuck"]; put(m.sfx("whoosh"), s["start"] + .2)
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
hn.SHOW = "SKY HIGH"
hn.TICKER = "  LIVE · SKY HIGH · TALLEST TOWER WINS · $5,000,000 · 7 DAYS · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "sky_high.mp4"]
    m.main()
