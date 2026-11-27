#!/usr/bin/env python3
"""Historia 5: THE HUNT — formato reality show (pantallas, cuenta atrás, ubicación revelada).

Uso: python3 hunt.py --voice ruta/en_US-ryan-high.onnx [--out hunt.mp4]
Reutiliza el motor de in_this_town.py (HUSS real, música de fondo, narrador).
Subtítulos de UNA palabra en el centro, gráficos de TV y paleta neón rosa/morado.
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)

MIN_DUR = 60.0
GY = 1450
ME = CHARS["me"]
PINK, PURPLE, NEON, GOLD = (255, 40, 200), (130, 40, 220), (255, 90, 230), (255, 215, 40)

SCRIPT = [
    ("In this town, there's a TV show called The Hunt.", "tv_intro", None),
    ("Every year, they pick one person... and the whole town has seven days to catch him.", "tv_rules", None),
    ("Whoever catches him wins one million dollars.", "money", None),
    ("This year... they picked me.", "target", None),
    ("Day one. I opened my door... and five hundred people started running at me.", "day1", None),
    ("I hid in a trash can. It smelled like old pizza.", "trash", None),
    ("Day two. I disguised myself as a baker. Fake mustache and everything.", "disguise", None),
    ("It worked perfectly... until a customer said hello, and I said:", "disguise_b", "solo", 1),
    ("Everyone turned around.", "disguise_c", None),
    ("Day three. My face was on every screen in town.", "screens", None),
    ("Even my grandma bought a net.", "grandma", None),
    ("Day five. They revealed my location. Live on TV.", "location", None),
    ("Drones. A helicopter. A guy on a skateboard.", "chase", None),
    ("So I jumped into the sewer.", "chase_b", None),
    ("I lived down there for two days. I made a friend. A rat named Kevin.", "sewer", None),
    ("Day seven. The last minute.", "countdown", None),
    ("I was on the roof of the TV station. Everyone was climbing up.", "roof", None),
    ("So I did the only thing I could do:", "roof_huss", "solo", 6),
    ("They all fell into the pool.", "roof_fall", None),
    ("Five. Four. Three.", "final", None),
    ("Then... something touched my shoulder.", "grab", None),
    ("It was Kevin.", "kevin", None),
    ("Kevin won one million dollars.", "kevin_rich", None),
    ("Now Kevin owns the TV station. And this year's target... is me. Again.", "end", None),
]

# ------------------------------------------------------------------ utilidades visuales
def tint(img, col, a):
    if a > 0: img.alpha_composite(Image.new("RGBA", (W, H), col + (int(a),)))

def flash(img, a): tint(img, (255, 255, 255), 255 * max(0, min(1, a)))

def neon_city(img, T, cam=0.):
    """Ciudad de noche con edificios, ventanas encendidas y pantallas."""
    sky(img, (20, 10, 50), (120, 30, 120)); d = ImageDraw.Draw(img)
    rnd = random.Random(1)
    for q in range(50):
        x, y = rnd.randint(0, W), rnd.randint(0, 700)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 255, 230))
    for i in range(-1, 8):
        x = i * 170 - (cam * .5) % 170
        h = 500 + (i * 137 % 5) * 120
        col = [(60, 40, 110), (80, 50, 140), (50, 30, 90)][i % 3]
        block(d, [x, GY - h, x + 160, GY], col)
        for wy in range(int(GY - h + 40), GY - 60, 70):
            for wx in (25, 70, 115):
                on = (i * 7 + wy // 70 + wx) % 3 != 0
                d.rectangle([x + wx, wy, x + wx + 25, wy + 35], fill=(255, 220, 120) if on else (40, 30, 70))
    d.rectangle([0, GY, W, H], fill=(40, 35, 60)); d.rectangle([0, GY, W, GY + 14], fill=PINK)
    for i in range(-1, 8):
        x = i * 200 - (cam % 200)
        d.rectangle([x, GY + 150, x + 110, GY + 168], fill=(255, 255, 255))
    return d

def screen(d, box, lines, glow=True):
    """Pantalla de TV gigante con marco neón. lines = [(texto, tamaño, color)]"""
    x0, y0, x1, y1 = box
    if glow:
        for k in range(4, 0, -1):
            d.rectangle([x0 - k * 6, y0 - k * 6, x1 + k * 6, y1 + k * 6], outline=PINK + (60,), width=6)
    d.rectangle(box, fill=(15, 10, 35), outline=NEON, width=8)
    total = sum(sz * 1.15 for _, sz, _ in lines)
    y = (y0 + y1) / 2 - total / 2
    for txt, sz, col in lines:
        d.text(((x0 + x1) / 2, y + sz * .55), txt, font=font(sz), fill=col, anchor="mm")
        y += sz * 1.15

def tv_overlay(img, T, day=None):
    """Mosca LIVE + rótulo inferior que corre."""
    d = ImageDraw.Draw(img)
    if int(T * 2) % 2 == 0:
        d.ellipse([46, 196, 74, 224], fill=(255, 30, 30))
    d.rounded_rectangle([36, 180, 240, 240], radius=14, outline=(255, 255, 255), width=4)
    d.text((150, 210), "LIVE", font=font(44), fill=(255, 255, 255), anchor="mm")
    if day:
        d.rounded_rectangle([W - 330, 180, W - 36, 240], radius=14, fill=PINK)
        d.text((W - 183, 210), day, font=font(40), fill=(255, 255, 255), anchor="mm")
    d.rectangle([0, 1700, W, 1770], fill=PURPLE)
    d.rectangle([0, 1700, 210, 1770], fill=PINK)
    d.text((105, 1735), "THE HUNT", font=font(36), fill=(255, 255, 255), anchor="mm")
    msg = "  LIVE · THE HUNT · 7 DAYS · $1,000,000 · TARGET: HUSS BOY · "
    x = 230 - (T * 160) % 1400
    while x < W:
        d.text((x, 1735), msg, font=font(34), fill=(255, 255, 255), anchor="lm")
        x += 1400

def crosshair(d, x, y, r, t):
    rr = r * (1 + .08 * math.sin(t * 10))
    d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 30, 30), width=10)
    d.ellipse([x - rr * .55, y - rr * .55, x + rr * .55, y + rr * .55], outline=(255, 30, 30), width=6)
    for a in range(4):
        dx, dy = math.cos(a * math.pi / 2), math.sin(a * math.pi / 2)
        d.line([x + dx * rr * .3, y + dy * rr * .3, x + dx * rr * 1.25, y + dy * rr * 1.25], fill=(255, 30, 30), width=8)

def disguise(d, x, top, s):
    """Gorro de chef + bigote falso."""
    hs = s * 1.25
    d.rectangle([x - hs * .5, top - s * .45, x + hs * .5, top + s * .1], fill=(255, 255, 255), outline=(40, 40, 40), width=3)
    d.ellipse([x - hs * .65, top - s * 1.45, x + hs * .65, top - s * .3], fill=(255, 255, 255), outline=(40, 40, 40), width=3)
    my = top + hs * .66
    d.polygon([(x - s * .5, my + s * .12), (x - s * .1, my - s * .06), (x, my + s * .02), (x + s * .1, my - s * .06),
               (x + s * .5, my + s * .12), (x + s * .2, my + s * .16), (x, my + s * .08), (x - s * .2, my + s * .16)], fill=(40, 25, 10))

def rat(d, x, y, s, t, face="smile", crown=False, tag=True):
    """Kevin la rata (de bloques). (x,y)=suelo."""
    gray, pink = (150, 150, 160), (255, 160, 180)
    d.line([x + s * 1.4, y - s * .5, x + s * 2.6, y - s * (.9 + .3 * math.sin(t * 6))], fill=pink, width=max(3, int(s * .15)))
    block(d, [x - s * 1.4, y - s * 1.3, x + s * 1.4, y - s * .2], gray)
    for lx in (-1, 1):
        block(d, [x + lx * s * .9 - s * .2, y - s * .3, x + lx * s * .9 + s * .2, y], gray)
    hx, hy = x - s * 1.2, y - s * 2.3
    block(d, [hx - s * .9, hy, hx + s * .9, hy + s * 1.5], gray)
    for e in (-1, 1):
        d.ellipse([hx + e * s * .65 - s * .45, hy - s * .7, hx + e * s * .65 + s * .45, hy + s * .2], fill=gray, outline=(90, 90, 100), width=2)
        d.ellipse([hx + e * s * .65 - s * .28, hy - s * .5, hx + e * s * .65 + s * .28, hy + s * .05], fill=pink)
        d.ellipse([hx + e * s * .35 - s * .12, hy + s * .45, hx + e * s * .35 + s * .12, hy + s * .7], fill=(20, 20, 20))
    d.ellipse([hx - s * .2, hy + s * .9, hx + s * .2, hy + s * 1.15], fill=pink)
    for e in (-1, 1):
        for k in (-1, 1):
            d.line([hx, hy + s * 1.0, hx + e * s * 1.1, hy + s * (1.0 + k * .2)], fill=(60, 60, 60), width=2)
    if face == "smile":
        d.arc([hx - s * .35, hy + s * .9, hx + s * .35, hy + s * 1.35], 10, 170, fill=(20, 20, 20), width=max(2, int(s * .08)))
    if tag:
        d.rectangle([x - s * .7, y - s * 1.1, x + s * .7, y - s * .6], fill=(255, 255, 255), outline=(40, 40, 40), width=2)
        d.text((x, y - s * .85), "KEVIN", font=font(max(8, int(s * .32))), fill=(40, 40, 40), anchor="mm")
    if crown:
        cy = hy - s * .4
        d.polygon([(hx - s * .7, cy), (hx - s * .7, cy - s * .7), (hx - s * .35, cy - s * .35), (hx, cy - s * .9),
                   (hx + s * .35, cy - s * .35), (hx + s * .7, cy - s * .7), (hx + s * .7, cy)], fill=GOLD, outline=(0, 0, 0))
    return hy

def helicopter(d, x, y, s, t):
    d.ellipse([x - s * 1.4, y - s * .7, x + s * 1.4, y + s * .7], fill=(230, 30, 50), outline=(60, 0, 10), width=4)
    d.ellipse([x + s * .2, y - s * .45, x + s * 1.1, y + s * .25], fill=(170, 220, 255))
    d.rectangle([x - s * 3, y - s * .15, x - s * 1.3, y + s * .15], fill=(230, 30, 50))
    rl = s * 2.6 * abs(math.cos(t * 30))
    d.line([x - rl, y - s * .9, x + rl, y - s * .9], fill=(40, 40, 40), width=6)
    d.line([x, y - s * .9, x, y - s * .7], fill=(40, 40, 40), width=6)
    d.line([x - s * 1.6, y + s * .9, x + s * 1.2, y + s * .9], fill=(40, 40, 40), width=5)
    # foco
    return (x, y + s * .7)

def drone(d, x, y, s, t):
    block(d, [x - s, y - s * .3, x + s, y + s * .3], (40, 40, 50))
    for e in (-1, 1):
        rw = s * .9 * abs(math.cos(t * 40 + e))
        d.line([x + e * s * 1.2 - rw, y - s * .5, x + e * s * 1.2 + rw, y - s * .5], fill=(200, 200, 210), width=4)
    d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 30, 30) if int(t * 6) % 2 else (90, 0, 0))

def money_rain(d, T, n=40, seed=4):
    rnd = random.Random(seed)
    for q in range(n):
        x = rnd.uniform(0, W) + 40 * math.sin(T * 2 + q); y = (rnd.uniform(0, H) + T * rnd.uniform(200, 500)) % (H + 100) - 50
        a = T * 3 + q
        w, h = 70 * abs(math.cos(a)) + 10, 38
        d.rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], fill=(90, 200, 90), outline=(30, 110, 40), width=2)

def runners(d, T, n, x0, spread, y=GY + 60, s=34, seed=0, toward=1, evil=False):
    for i in range(n):
        x = x0 + (i % 6) * spread + (i // 6) * 25 + 20 * math.sin(T * 3 + i)
        yy = y + (i // 6) * 50 - abs(math.sin(T * 9 + i)) * 30
        avatar(d, x, yy, s + (i // 6) * 4, npc(seed + i), T * 2 + i, 1.6, "up", "angry" if evil else "yell", look=toward)

def camera(img, key, u):
    if key not in CAMS: return img
    z0, z1, (x0, y0), (x1, y1) = CAMS[key]
    k = ease(u); z = z0 + (z1 - z0) * k
    cx, cy = (x0 + (x1 - x0) * k) * W, (y0 + (y1 - y0) * k) * H
    cw, ch = W / z, H / z
    l = min(max(0, cx - cw / 2), W - cw); tp = min(max(0, cy - ch / 2), H - ch)
    return img.crop((int(l), int(tp), int(l + cw), int(tp + ch))).resize((W, H), Image.BILINEAR)

CAMS = {
    "tv_intro": (1.6, 1.0, (.5, .35), (.5, .5)), "tv_rules": (1.0, 1.2, (.5, .45), (.5, .4)),
    "money": (1.0, 1.15, (.5, .5), (.5, .55)), "target": (1.0, 2.0, (.5, .6), (.5, .55)),
    "day1": (1.2, 1.0, (.6, .6), (.4, .6)), "trash": (1.0, 1.6, (.5, .6), (.45, .68)),
    "disguise": (1.0, 1.3, (.5, .55), (.4, .58)), "disguise_b": (1.25, 1.0, (.4, .58), (.5, .55)),
    "disguise_c": (1.0, 1.25, (.5, .55), (.65, .55)), "screens": (1.3, 1.0, (.5, .4), (.5, .5)),
    "grandma": (1.0, 1.3, (.5, .6), (.5, .55)), "location": (1.0, 1.25, (.5, .5), (.5, .45)),
    "chase": (1.15, 1.15, (.35, .5), (.65, .5)), "chase_b": (1.0, 1.4, (.5, .6), (.5, .7)),
    "sewer": (1.2, 1.0, (.5, .6), (.5, .55)), "countdown": (1.0, 1.2, (.5, .45), (.5, .42)),
    "roof": (1.0, 1.2, (.5, .55), (.5, .6)), "roof_huss": (1.2, 1.0, (.5, .55), (.5, .5)),
    "roof_fall": (1.0, 1.2, (.5, .6), (.5, .7)), "final": (1.0, 1.0, (.5, .5), (.5, .5)),
    "grab": (1.0, 2.2, (.5, .55), (.42, .48)), "kevin": (1.8, 1.0, (.4, .62), (.5, .55)),
    "kevin_rich": (1.0, 1.2, (.5, .55), (.5, .55)), "end": (1.0, 1.35, (.5, .5), (.5, .32)),
}

DAY = {"day1": "DAY 1 OF 7", "trash": "DAY 1 OF 7", "disguise": "DAY 2 OF 7", "disguise_b": "DAY 2 OF 7",
       "disguise_c": "DAY 2 OF 7", "screens": "DAY 3 OF 7", "grandma": "DAY 3 OF 7", "location": "DAY 5 OF 7",
       "chase": "DAY 5 OF 7", "chase_b": "DAY 5 OF 7", "sewer": "DAY 6 OF 7", "countdown": "DAY 7 OF 7",
       "roof": "DAY 7 OF 7", "roof_huss": "DAY 7 OF 7", "roof_fall": "DAY 7 OF 7", "final": "DAY 7 OF 7"}

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    sc = seg["scene"]; dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)

    if sc in ("tv_intro", "tv_rules", "money"):
        d = neon_city(img, T)
        box = [130, 330, 950, 900]
        if sc == "tv_intro":
            p = ease(min(1, t / .5))
            screen(d, box, [("THE", 90, (255, 255, 255)), ("HUNT", 230 * (.6 + .4 * p) + 10 * math.sin(T * 6), NEON),
                            ("LIVE EVERY YEAR", 50, GOLD)])
            for i in range(5):
                avatar(d, 140 + i * 200, GY + 40, 36, npc(i + 300), T, .6, "up" if i % 2 else "down", "shock", look=0)
        elif sc == "tv_rules":
            day = 7 if u < .5 else 7
            screen(d, box, [("ONE TARGET", 80, (255, 255, 255)), (f"{day} DAYS", 200, NEON), ("WHOLE TOWN HUNTS", 50, GOLD)])
            runners(d, T, 6, 80, 170, seed=310)
        else:
            screen(d, box, [("PRIZE", 80, (255, 255, 255)), ("$1,000,000", 150, (90, 220, 90))])
            money_rain(d, T)
            for i in range(5):
                avatar(d, 140 + i * 200, GY + 40 - abs(math.sin(T * 7 + i)) * 50, 36, npc(i + 320), T, 0, "up", "laugh")
        ovl.append(None)

    elif sc == "target":
        sky(img, (40, 10, 60), (150, 30, 110)); d = ImageDraw.Draw(img)
        for q in range(14):
            a = q * math.pi / 7 + T
            d.polygon([(W / 2, 1000), (W / 2 + 2200 * math.cos(a), 1000 + 2200 * math.sin(a)),
                       (W / 2 + 2200 * math.cos(a + .12), 1000 + 2200 * math.sin(a + .12))], fill=(90, 20, 90))
        top = avatar(d, W / 2, 1650, 120, ME, T, 0, "down", "shock" if u > .5 else "flat")
        r = 420 - 250 * ease(min(1, u / .6))
        crosshair(d, W / 2, top + 75, r, T)
        if u > .6:
            tint(img, (255, 0, 0), 40 + 40 * math.sin(T * 14))
            stk("TARGET: HUSS BOY", W / 2, 330, 100, (255, 30, 30), rot=-4, scale=1 + .05 * math.sin(T * 12))
            amp = 6
        ovl.append(None)

    elif sc == "day1":
        d = town(img, T, cam=t * 600)
        tint(img, (120, 30, 120), 50); d = ImageDraw.Draw(img)
        runners(d, T, 18, -60 + 60 * u, 95, seed=330)
        avatar(d, 870, GY + 40 - abs(math.sin(T * 10)) * 40, 58, ME, T * 2, 1.6, "up", "yell", look=1)
        stk("500 PEOPLE", W / 2, 420, 120, PINK, rot=-5, scale=1 + .05 * math.sin(T * 10))
        amp = 5
        ovl.append(DAY[sc])

    elif sc == "trash":
        d = town(img, T)
        for i in range(4):  # pasan corriendo sin verle
            x = (i * 300 + t * 700) % (W + 400) - 200
            avatar(d, x, GY + 60, 36, npc(340 + i), T * 2, 1.5, "up", "yell", look=1)
        bx, by = W / 2, 1520
        lid = 30 * max(0, math.sin(T * 2))
        block(d, [bx - 160, by - 300, bx + 160, by], (110, 120, 120))
        for q in range(4): d.line([bx - 120 + q * 80, by - 280, bx - 120 + q * 80, by - 20], fill=(80, 90, 90), width=6)
        d.rectangle([bx - 175, by - 330 - lid, bx + 175, by - 300 - lid], fill=(90, 100, 100))
        if lid > 8:  # ojos asomando
            d.rectangle([bx - 70, by - 300 - lid + 4, bx + 70, by - 298], fill=(20, 20, 20))
            for e in (-1, 1): d.ellipse([bx + e * 35 - 14, by - 300 - lid * .7, bx + e * 35 + 14, by - 300 - lid * .7 + 20], fill=(255, 255, 255))
        for q in range(4):  # moscas
            fx = bx + 160 * math.cos(T * 4 + q * 1.6); fy = by - 420 + 60 * math.sin(T * 6 + q)
            d.ellipse([fx - 6, fy - 6, fx + 6, fy + 6], fill=(20, 20, 20))
        for q in range(3):  # olor
            d.arc([bx - 100 + q * 70, by - 520 - q * 20 + 20 * math.sin(T * 3 + q), bx - 40 + q * 70, by - 420], 200, 340, fill=(140, 200, 90), width=8)
        if u > .5: stk("OLD PIZZA", W / 2, 420, 120, (240, 140, 30), rot=5)
        ovl.append(DAY[sc])

    elif sc in ("disguise", "disguise_b", "disguise_c"):
        sky(img, (255, 225, 180), (240, 190, 140)); d = ImageDraw.Draw(img)
        for row in range(2):
            y = 560 + row * 200
            d.rectangle([60, y + 60, W - 60, y + 80], fill=(140, 90, 50))
            for j in range(7):
                x = 120 + j * 135
                d.ellipse([x - 50, y + 10, x + 50, y + 62], fill=(200, 130, 60), outline=(90, 50, 20), width=4)
        block(d, [0, 1250, W, 1450], (190, 120, 70))  # mostrador
        d.rectangle([0, 1450, W, H], fill=(210, 180, 140))
        yell = sc == "disguise_b" and hit > .2
        top = avatar(d, 380, 1300, 66 * (1 + .15 * hit), ME, T, 0, "out" if yell else "down",
                     "yell" if yell else ("shock" if sc == "disguise_c" else "smile"), look=1)
        disguise(d, 380, top, 66 * (1 + .15 * hit))
        # clienta
        cl = avatar(d, 820, 1450, 58, npc(350), T, 0, "down" if sc != "disguise_c" else "up",
                    "smile" if sc == "disguise" else ("shock" if sc == "disguise_b" else "angry"), look=-1)
        if sc == "disguise":
            stk("NOBODY WILL KNOW", W / 2, 330, 90, (40, 40, 40), fg=(255, 255, 255), rot=-4)
        if sc == "disguise_b":
            if 0 <= k: stk("HUSS!", 380, 420, 150, (40, 90, 210), rot=-6, scale=1 + .4 * hit)
            else: stk("HELLO!", 820, 500, 100, (255, 255, 255), fg=(40, 40, 40), rot=4)
            amp = int(25 * hit)
        if sc == "disguise_c":
            # por la ventana: toda la calle se gira a mirar
            for q in range(5):
                avatar(d, 90 + q * 230, 1250, 40, npc(360 + q), T, 0, "up", "angry", look=-1 if q > 2 else 1)
            stk("OOPS", W / 2, 360, 160, (220, 30, 30), rot=6, scale=1 + .06 * math.sin(T * 12))
            amp = 4
        ovl.append(DAY[sc])

    elif sc == "screens":
        d = neon_city(img, T)
        for q, (x0, y0, x1, y1) in enumerate([(60, 300, 520, 640), (560, 300, 1020, 640), (60, 700, 520, 1040), (560, 700, 1020, 1040)]):
            d.rectangle([x0, y0, x1, y1], fill=(15, 10, 35), outline=NEON, width=6)
            cx = (x0 + x1) / 2
            top = avatar(d, cx, y1 + 120, 62, ME, T + q, 0, "down", "flat")
            d.rectangle([x0, y1 - 60, x1, y1], fill=(255, 30, 30))
            d.text((cx, y1 - 30), "WANTED · $1M", font=font(38), fill=(255, 255, 255), anchor="mm")
            d.rectangle([x0 - 6, y1, x1 + 6, y1 + 300], fill=None)
        # tapa lo que sobresale bajo las pantallas
        img2 = Image.new("RGBA", (W, H)); neon_city(img2, T)
        mask = Image.new("L", (W, H), 255)
        md = ImageDraw.Draw(mask)
        for (x0, y0, x1, y1) in [(60, 300, 520, 640), (560, 300, 1020, 640), (60, 700, 520, 1040), (560, 700, 1020, 1040)]:
            md.rectangle([x0, y0, x1, y1], fill=0)
        img.paste(img2, (0, 0), mask)
        d = ImageDraw.Draw(img)
        for (x0, y0, x1, y1) in [(60, 300, 520, 640), (560, 300, 1020, 640), (60, 700, 520, 1040), (560, 700, 1020, 1040)]:
            d.rectangle([x0, y0, x1, y1], outline=NEON, width=6)
        for i in range(5):
            avatar(d, 120 + i * 210, GY + 60, 36, npc(370 + i), T, 0, "up", "shock", look=0)
        ovl.append(DAY[sc])

    elif sc == "grandma":
        d = town(img, T)
        jump = abs(math.sin(T * 5)) * 120
        gx = W / 2 + 200 * math.sin(T * 1.5)
        top = avatar(d, gx, GY + 40 - jump, 64, dict(head=(255, 205, 160), torso=(170, 90, 160), legs=(120, 70, 120),
                                                    hair=None, logo=None), T, 0, "up", "angry")
        d.ellipse([gx - 45, top - 80, gx + 45, top + 10], fill=(200, 200, 205), outline=(120, 120, 125), width=3)
        for e in (-1, 1):
            d.ellipse([gx + e * 18 - 28, top + 30, gx + e * 18 + 28, top + 80], outline=(20, 20, 20), width=5)
        # red
        nx, ny = gx + 140, top - 260 + 80 * math.sin(T * 5)
        d.line([gx + 90, top + 140, nx, ny + 120], fill=(110, 70, 40), width=12)
        d.ellipse([nx - 120, ny - 120, nx + 120, ny + 120], outline=(240, 240, 240), width=8)
        for q in range(-2, 3):
            d.line([nx + q * 45, ny - 110, nx + q * 45, ny + 110], fill=(230, 230, 230), width=3)
            d.line([nx - 110, ny + q * 45, nx + 110, ny + q * 45], fill=(230, 230, 230), width=3)
        stk("EVEN GRANDMA", W / 2, 360, 120, (170, 90, 160), rot=-5, scale=1 + .05 * math.sin(T * 10))
        ovl.append(DAY[sc])

    elif sc == "location":
        sky(img, (10, 15, 35), (25, 20, 60)); d = ImageDraw.Draw(img)
        x0, y0, x1, y1 = 90, 330, 990, 1500
        d.rectangle([x0, y0, x1, y1], fill=(10, 30, 40), outline=NEON, width=8)
        for gx in range(x0, x1, 75): d.line([gx, y0, gx, y1], fill=(30, 80, 90), width=2)
        for gy in range(y0, y1, 75): d.line([x0, gy, x1, gy], fill=(30, 80, 90), width=2)
        for q in range(8):  # calles
            d.line([x0 + 60 + q * 110, y0, x0 + 60 + q * 110, y1], fill=(60, 140, 150), width=6)
        cx, cy = 620, 1000
        rr = (t * 500) % 400
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(255, 30, 30), width=6)
        d.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], fill=(255, 30, 30))
        ang = T * 3
        d.line([cx, cy, cx + 600 * math.cos(ang), cy + 600 * math.sin(ang)], fill=(80, 255, 140), width=4)
        d.rectangle([x0, y1 - 120, x1, y1], fill=PINK)
        d.text(((x0 + x1) / 2, y1 - 60), "LOCATION: HUSS STREET 7", font=font(58), fill=(255, 255, 255), anchor="mm")
        if u > .3: stk("LOCATION REVEALED", W / 2, 260, 95, (255, 30, 30), rot=-3, scale=1 + .05 * math.sin(T * 12))
        ovl.append(DAY[sc])

    elif sc in ("chase", "chase_b"):
        d = neon_city(img, T, cam=t * 1200)
        if sc == "chase":
            third = min(2, int(u * 3))
            hx, hy = helicopter(d, 300 + 200 * math.sin(T), 380 + 30 * math.sin(T * 2), 80, T)
            if third >= 0:
                beam = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(beam)
                bd.polygon([(hx - 30, hy), (hx + 30, hy), (880, GY + 80), (620, GY + 80)], fill=(255, 255, 200, 70))
                img.alpha_composite(beam); d = ImageDraw.Draw(img)
            for q in range(3):
                drone(d, 650 + q * 120 + 40 * math.sin(T * 3 + q), 700 + 50 * math.sin(T * 4 + q), 34, T)
            if third == 2:  # el del monopatín
                sx = 120 + 200 * ease((u * 3 - 2))
                block(d, [sx - 90, GY + 85, sx + 90, GY + 100], (240, 90, 40))
                for e in (-1, 1): d.ellipse([sx + e * 60 - 14, GY + 96, sx + e * 60 + 14, GY + 124], fill=(30, 30, 30))
                avatar(d, sx, GY + 85, 42, npc(380), T, 0, "out", "yell", look=1)
            stk(["DRONES", "HELICOPTER", "SKATEBOARD GUY"][third], W / 2, 1080, 100, PINK, rot=-4 + 4 * third)
            avatar(d, 750, GY + 60 - abs(math.sin(T * 10)) * 40, 52, ME, T * 2, 1.6, "up", "yell", look=1)
            amp = 4
        else:
            # tapa de alcantarilla y salto
            mx = 650
            d.ellipse([mx - 150, GY + 70, mx + 150, GY + 140], fill=(20, 20, 25))
            if u < .55:
                v = u / .55
                avatar(d, 300 + (mx - 300) * v, GY + 60 - math.sin(v * math.pi) * 250, 52, ME, T * 2, 0, "up", "yell", look=1)
            else:
                stk("SPLASH", mx, 1250, 120, (90, 170, 255), rot=-6)
                for q in range(8):
                    a = q * .8; r = 80 + (u - .55) * 500
                    d.ellipse([mx + r * math.cos(a) - 14, GY + 60 - r * abs(math.sin(a)) - 14, mx + r * math.cos(a) + 14, GY + 60 - r * abs(math.sin(a)) + 14], fill=(110, 160, 90))
            runners(d, T, 6, -100 + 300 * u, 70, seed=390, s=34)
        ovl.append(DAY[sc])

    elif sc == "sewer":
        sky(img, (25, 40, 30), (40, 60, 45)); d = ImageDraw.Draw(img)
        for yy in range(0, 1450, 90):
            for xx in range(-45 * ((yy // 90) % 2), W, 180):
                d.rectangle([xx + 4, yy + 4, xx + 176, yy + 86], fill=(55, 75, 60))
        d.ellipse([-200, 1300, W + 200, 1700], fill=(70, 110, 60))  # agua sucia
        for q in range(6):
            bx = (q * 197 + T * 60) % W; d.ellipse([bx - 10, 1460 + 10 * math.sin(T * 3 + q), bx + 10, 1480 + 10 * math.sin(T * 3 + q)], fill=(110, 160, 90))
        # vela
        fl = 1 + .15 * math.sin(T * 20)
        d.rectangle([520, 1260, 560, 1350], fill=(245, 240, 220))
        d.polygon([(527, 1260), (553, 1260), (540, 1260 - 50 * fl)], fill=(255, 190, 60))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
        for r in range(6, 0, -1):
            gd.ellipse([540 - r * 70, 1230 - r * 70, 540 + r * 70, 1230 + r * 70], fill=(255, 200, 100, 12))
        img.alpha_composite(glow); d = ImageDraw.Draw(img)
        avatar(d, 300, 1380, 58, ME, T, 0, "down", "smile", look=1)
        rat(d, 790, 1380, 55, T)
        if u > .55:
            stk("KEVIN", 790, 900, 130, (150, 150, 160), rot=5, scale=1 + .05 * math.sin(T * 10))
            stk("BEST FRIEND", 790, 1060, 70, (255, 140, 180), rot=-3)
        ovl.append(DAY[sc])

    elif sc in ("countdown", "final"):
        d = neon_city(img, T)
        if sc == "countdown":
            secs = max(0, 59 - int(t))
            screen(d, [90, 380, 990, 1150], [("LAST MINUTE", 80, (255, 255, 255)), (f"00:{secs:02d}", 260, GOLD),
                                               ("SURVIVE TO WIN $1,000,000", 46, NEON)])
        else:
            num = 5 - min(2, int(u * 3))
            pulse = 1 + .3 * max(0, 1 - ((u * 3) % 1) * 4)
            screen(d, [90, 380, 990, 1150], [("FINAL SECONDS", 80, (255, 255, 255)), (str(num), int(400 * pulse), (255, 60, 60))])
            tint(img, (255, 0, 0), 30 * max(0, 1 - ((u * 3) % 1) * 4))
        ovl.append(DAY[sc])

    elif sc in ("roof", "roof_huss", "roof_fall"):
        sky(img, (20, 10, 50), (150, 40, 130)); d = ImageDraw.Draw(img)
        d.ellipse([780, 200, 940, 360], fill=(255, 240, 220))
        block(d, [0, 1300, W, H], (70, 60, 90))  # azotea
        d.rectangle([0, 1300, W, 1330], fill=PINK)
        d.line([W / 2 + 300, 1300, W / 2 + 300, 700], fill=(150, 150, 160), width=14)  # antena
        d.ellipse([W / 2 + 280, 680, W / 2 + 320, 720], fill=(255, 30, 30) if int(T * 3) % 2 else (90, 0, 0))
        if sc == "roof_fall":
            # piscina abajo y todos cayendo
            d.rectangle([0, 1650, W, H], fill=(60, 170, 230))
            for i in range(8):
                fx = 80 + i * 130; fy = 1300 + ((t * 700 + i * 90) % 450)
                avatar(d, fx, fy, 30, npc(400 + i), T + i, 0, "up", "shock")
            stk("SPLASH", W / 2, 1550, 140, (90, 170, 255), rot=-5, scale=1 + .06 * math.sin(T * 12))
            avatar(d, W / 2, 1300, 66, ME, T, 0, "up", "laugh")
        else:
            climb = ease(u) * 90 if sc == "roof" else 90
            for side in (-1, 1):  # gente subiendo por los bordes
                for q in range(3):
                    x = W / 2 + side * (380 + q * 60)
                    avatar(d, x, 1330 + 300 - climb * 3 + q * 40, 36, npc(410 + q + (side > 0) * 3), T + q, 0, "up", "angry",
                           look=-side)
            z = 1 + .15 * hit
            avatar(d, W / 2, 1300, 70 * z, ME, T, 0, "out" if hit > .1 else "down",
                   "yell" if hit > .2 else ("shock" if sc == "roof" else "flat"))
            if sc == "roof_huss" and 0 <= k < seg["nh"]:
                for j in range(k + 1):
                    stk("HUSS", 190 + (j * 191) % 700, 420 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                        rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
            amp = int(28 * hit)
        ovl.append(DAY[sc])

    elif sc in ("grab", "kevin"):
        sky(img, (20, 10, 50), (150, 40, 130)); d = ImageDraw.Draw(img)
        block(d, [0, 1300, W, H], (70, 60, 90)); d.rectangle([0, 1300, W, 1330], fill=PINK)
        if sc == "grab":
            img_g = Image.new("RGBA", (W, H))
            top = avatar(d, W / 2 - 100, 1300, 75, ME, T * .1, 0, "down", "shock", look=1)
            # pata gris en el hombro
            px = W / 2 + 40 + 60 * (1 - ease(min(1, u / .5)))
            block(d, [px, top + 230, px + 220, top + 290], (150, 150, 160))
            for q in range(3): d.ellipse([px - 18, top + 228 + q * 22, px + 6, top + 250 + q * 22], fill=(255, 160, 180))
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(140 * u))))
            stk("...", W / 2, 420, 140, (0, 0, 0), rot=0)
        else:
            avatar(d, 280, 1300, 64, ME, T, 0, "up", "shock", look=1)
            rat(d, 760, 1300, 62, T, "smile")
            if u > .3: stk("KEVIN?!", W / 2, 420, 150, (150, 150, 160), rot=-6, scale=1 + .06 * math.sin(T * 12))
            if u < .1: flash(img, 1 - u / .1)
            amp = int(15 * max(0, 1 - u * 4))

    elif sc in ("kevin_rich", "end"):
        if sc == "kevin_rich":
            sky(img, (255, 60, 200), (120, 30, 200)); d = ImageDraw.Draw(img)
            for q in range(16):
                a = q * math.pi / 8 + T * .7
                d.polygon([(W / 2, 1000), (W / 2 + 2300 * math.cos(a), 1000 + 2300 * math.sin(a)),
                           (W / 2 + 2300 * math.cos(a + .18), 1000 + 2300 * math.sin(a + .18))], fill=(255, 120, 230))
            money_rain(d, T, 60)
            rat(d, W / 2 + 120, 1500 - abs(math.sin(T * 6)) * 60, 110, T, "smile", crown=True)
            stk("WINNER", W / 2, 330, 160, GOLD, fg=(255, 255, 255), rot=-5, scale=1 + .06 * math.sin(T * 10))
            stk("$1,000,000", W / 2, 560, 110, (90, 200, 90), rot=4)
        else:
            sky(img, (30, 20, 50), (60, 40, 90)); d = ImageDraw.Draw(img)
            screen(d, [140, 260, 940, 760], [("NEXT YEAR'S TARGET", 56, (255, 255, 255)), ("", 10, (0, 0, 0))])
            top = avatar(d, W / 2, 900, 46, ME, T, 0, "down", "shock")
            crosshair(d, W / 2, top + 30, 120, T)
            block(d, [0, 1250, W, H], (90, 60, 40))  # despacho
            block(d, [250, 1150, 830, 1300], (120, 80, 50))  # mesa
            rat(d, W / 2 + 40, 1150, 70, T, "smile", crown=True)
            d.rectangle([W / 2 - 160, 1100, W / 2 - 40, 1150], fill=(40, 40, 40))  # placa
            d.text((W / 2 - 100, 1125), "CEO", font=font(36), fill=GOLD, anchor="mm")
            if u > .6:
                stk("AGAIN?!", W / 2, 1450, 150, (255, 30, 30), rot=6, scale=1 + .06 * math.sin(T * 12))
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

# ------------------------------------------------------------------ subtítulos de UNA palabra en el centro
def captions_single(img, segs, T):
    seg = None
    for s in segs:
        if s["start"] - .05 <= T <= s["start"] + s["dur"] + .15: seg = s
    if not seg or not seg["words"]: return
    cur = None
    for w, a, b in seg["words"]:
        if T >= a: cur = (w, a, b)
    if not cur: return
    w, a, b = cur
    if T > b + .25 and w != seg["words"][-1][0]: return
    d = ImageDraw.Draw(img)
    pop = min(1, (T - a) / .08)
    sz = int(118 * (1.25 - .25 * pop))
    is_huss = "HUSS" in w.upper()
    d.text((W / 2, 1240), w.strip(".,").lower() if not is_huss else "HUSS!", font=font(sz),
           fill=GOLD if is_huss else (255, 255, 255), anchor="mm", stroke_width=14, stroke_fill=(0, 0, 0))

# ------------------------------------------------------------------ audio
def tone(f, dur, a=.3):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * np.minimum(1, t / .005) * np.exp(-t * 6) * a).astype(np.float32)

def alarm(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 900 + 400 * (np.sin(2 * np.pi * 2 * t) > 0)
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .07).astype(np.float32)

def crowd_roar(dur):
    n = int(SR * dur); x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 200) | (f > 2500)] = 0
    y = np.fft.irfft(X, n); y /= np.abs(y).max()
    t = np.arange(n) / SR
    return (y * .25 * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .3) * (.7 + .3 * np.sin(2 * np.pi * 3 * t))).astype(np.float32)

def heli(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    x = np.random.randn(n) * (np.sin(2 * np.pi * 14 * t) > .3)
    return (np.convolve(x, np.ones(60) / 60, "same") * .5 * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .3)).astype(np.float32)

def squeak():
    n = int(SR * .25); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (2200 + 900 * np.sin(2 * np.pi * 9 * t)) * t) * np.exp(-t * 10) * .25).astype(np.float32)

ORIG_MIX = m.mix_audio

def mix_audio(segs, total, out_wav):
    ORIG_MIX(segs, total, out_wav)
    with wave.open(out_wav) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = a.copy(); n = len(a); fx = np.zeros(n, np.float32)
    def put(x, t):
        s_ = int(t * SR); e = min(n, s_ + len(x))
        if e > s_: fx[s_:e] += x[:e - s_]
    by = {s["scene"]: s for s in segs}
    s = by["tv_intro"]; put(m.sfx("boom") * .8, s["start"]); put(tone(880, .4) + tone(1320, .4), s["start"] + .4)
    s = by["money"]; put(m.sfx("ding"), s["start"] + .2)
    s = by["target"]; put(alarm(s["dur"] * .45), s["start"] + s["dur"] * .55); put(m.sfx("boom") * .7, s["start"] + s["dur"] * .55)
    s = by["day1"]; put(crowd_roar(s["dur"] + .3), s["start"])
    s = by["disguise_c"]; put(m.sfx("boom") * .6, s["start"]); put(crowd_roar(s["dur"]) * .6, s["start"])
    s = by["screens"]
    for q in range(4): put(tone(600, .15), s["start"] + q * .25)
    s = by["location"]
    for q in range(int(s["dur"] / .5)): put(tone(1000, .12, .2), s["start"] + q * .5)
    s = by["chase"]; put(heli(s["dur"] + .3), s["start"])
    s = by["chase_b"]; put(m.sfx("whoosh"), s["start"] + .1); put(m.sfx("boom") * .5, s["start"] + s["dur"] * .55)
    s = by["sewer"]; put(squeak(), s["start"] + s["dur"] * .55); put(squeak(), s["start"] + s["dur"] * .65)
    s = by["countdown"]
    for q in range(int(s["dur"]) + 1): put(tone(1200, .1, .25), s["start"] + q)
    s = by["roof"]; put(crowd_roar(s["dur"]) * .7, s["start"])
    s = by["roof_fall"]; put(m.sfx("boom") * .6, s["start"] + .3); put(crowd_roar(.8) * .8, s["start"])
    s = by["final"]
    for q in range(3): put(tone(1500, .25, .35), s["start"] + q * (s["dur"] + .2) / 3)
    s = by["grab"]; put(m.riser(s["dur"]) * .6, s["start"])
    s = by["kevin"]; put(squeak() * 1.4, s["start"] + .05); put(m.sfx("boom") * .6, s["start"])
    s = by["kevin_rich"]; put(m.sfx("ding"), s["start"]); put(crowd_roar(s["dur"]) * .5, s["start"])
    s = by["end"]; put(alarm(1.2), s["start"] + s["dur"] * .6)
    voice = np.zeros(n, np.float32)
    for s in segs:
        st_ = int(s["start"] * SR); e = min(n, st_ + len(s["audio"])); voice[st_:e] += np.abs(s["audio"][:e - st_])
    talk = np.convolve(np.clip(np.convolve(voice, np.ones(2205) / 2205, "same") * 25, 0, 1), np.ones(4410) / 4410, "same")
    a += fx * (1 - .55 * talk)
    a /= max(1, np.abs(a).max() / .95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

ORIG_BUILD = m.build

def build(voice, tmp):
    segs, total = ORIG_BUILD(voice, tmp)
    print(f"duración natural: {total:.2f}s")
    if total >= MIN_DUR:
        return segs, total
    extra = MIN_DUR - total; n = len(segs)
    for i, sg in enumerate(segs):
        off = extra * i / n
        sg["start"] += off
        if sg.get("huss_t0") is not None: sg["huss_t0"] += off
        sg["hits"] = [h + off for h in sg.get("hits") or []]
        sg["words"] = [(w, a + off, b + off) for w, a, b in sg["words"]]
    segs[-1]["dur"] += extra / n
    return segs, MIN_DUR

ORIG_RENDER = m.render_scene
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "hunt.mp4"]
    m.main()
