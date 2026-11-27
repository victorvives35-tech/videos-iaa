#!/usr/bin/env python3
"""Historia 7: THE CIRCLE — concurso de TV (mismo estilo que THE HUNT / DON'T SAY HUSS).

Uso: python3 circle.py --voice ruta/en_US-ryan-high.onnx [--out circle.mp4]
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
import hunt as hn
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)
from hunt import neon_city, screen, tv_overlay, money_rain, captions_single, tint, flash, tone, crowd_roar, PINK, PURPLE, NEON, GOLD

ME = CHARS["me"]
GY = 1450
RED = (255, 40, 40)
GREG = dict(head=(230, 180, 140), torso=(60, 120, 60), legs=(90, 70, 50), hair=(120, 70, 30), logo=None)
MOM = dict(head=(255, 205, 160), torso=(230, 90, 120), legs=(80, 60, 120), hair=(110, 60, 30), logo=None, long_hair=True)
MIME = dict(head=(250, 250, 250), torso=(20, 20, 20), legs=(20, 20, 20), hair=(20, 20, 20), logo=None)

SCRIPT = [
    ("In this town, there's a TV show called The Circle.", "intro", None),
    ("A giant circle in the middle of town. The last person to leave it wins five million dollars.", "rules", None),
    ("Two hundred people jumped in. Including me.", "jump_in", None),
    ("Hour one. Someone's mom called him for dinner. He left.", "mom", None),
    ("Hour five. It started raining. Fifty people left.", "rain", None),
    ("Day two. They put a pizza... one inch outside the circle.", "pizza", None),
    ("Eighty people ran for it.", "pizza_b", None),
    ("Day three: bees. Day four: a mime. Nobody could handle the mime.", "bees", None),
    ("Day ten. Only two of us left. Me... and a guy named Greg.", "greg", None),
    ("Greg was a professional. He brought a tent. A toilet. And a llama.", "greg_b", None),
    ("So I looked Greg in the eyes... and said:", "greg_huss", "solo", 6),
    ("Greg ran away screaming. The llama stayed.", "greg_run", None),
    ("Day thirty. Day fifty. Day one hundred.", "days", None),
    ("Finally, I called the TV station and asked: did I win?", "phone", None),
    ("They said: the show got cancelled on day two. Nobody told you?", "cancelled", None),
    ("So now I just live in the circle. With the llama.", "end", None),
    ("Tourists come to take photos. And every time, I say:", "tourists", "solo", 3),
]

DAY = {"jump_in": "HOUR 0", "mom": "HOUR 1", "rain": "HOUR 5", "pizza": "DAY 2", "pizza_b": "DAY 2", "bees": "DAY 3",
       "greg": "DAY 10", "greg_b": "DAY 10", "greg_huss": "DAY 10", "greg_run": "DAY 10"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.2, (.5, .5), (.5, .6)),
    "jump_in": (1.2, 1.0, (.5, .65), (.5, .6)), "mom": (1.0, 1.35, (.5, .62), (.3, .6)),
    "rain": (1.15, 1.0, (.5, .55), (.5, .6)), "pizza": (1.0, 1.5, (.5, .6), (.78, .68)),
    "pizza_b": (1.3, 1.0, (.7, .65), (.5, .6)), "bees": (1.0, 1.2, (.5, .6), (.5, .6)),
    "greg": (1.0, 1.25, (.5, .6), (.5, .62)), "greg_b": (1.25, 1.05, (.6, .6), (.6, .6)),
    "greg_huss": (1.0, 1.2, (.5, .6), (.5, .58)), "greg_run": (1.2, 1.0, (.5, .6), (.5, .6)),
    "days": (1.0, 1.15, (.5, .55), (.5, .6)), "phone": (1.0, 1.4, (.5, .55), (.5, .48)),
    "cancelled": (1.2, 1.0, (.5, .45), (.5, .5)), "end": (1.0, 1.2, (.5, .6), (.5, .62)),
    "tourists": (1.15, 1.0, (.5, .6), (.5, .6)),
}

CX, CY, RX, RY = W / 2, 1420, 480, 175
GND = 1130   # el círculo en el suelo

# ------------------------------------------------------------------ piezas
def ground_circle(d, T, glow=True):
    for k in range(3, 0, -1):
        d.ellipse([CX - RX - k * 6, CY - RY - k * 3, CX + RX + k * 6, CY + RY + k * 3], outline=(255, 90, 230), width=6)
    d.ellipse([CX - RX, CY - RY, CX + RX, CY + RY], outline=(255, 255, 255), width=14)

def inside_spots(n, seed=0):
    rnd = random.Random(seed); pts = []
    while len(pts) < n:
        x, y = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
        if x * x + y * y < .8: pts.append((CX + x * RX * .9, CY + y * RY * .8))
    return sorted(pts, key=lambda p: p[1])

def square(img, T, sky_col=None):
    d = town(img, T, ground_y=GND)
    if sky_col: tint(img, sky_col, 90); d = ImageDraw.Draw(img)
    d.rectangle([0, GND, W, H], fill=(150, 140, 130))
    for q in range(0, W + 200, 120): d.line([q, GND, q - 250, H], fill=(135, 125, 115), width=3)
    ground_circle(d, T)
    return d

def contestants(d, T, n, seed=0, face="smile", arms_fn=None, skip=0):
    for i, (x, y) in enumerate(inside_spots(n, seed)):
        if i < skip: continue
        s = 30 + (y - (CY - RY)) / (2 * RY) * 20
        avatar(d, x, y, s, npc(600 + i), T + i, 0, arms_fn(i) if arms_fn else "down", face, look=0)

def llama(d, x, y, s, t, look=1):
    wool = (245, 240, 230)
    for lx in (-1.0, -.4, .4, 1.0):
        block(d, [x + lx * s - s * .18, y - s * 1.2, x + lx * s + s * .18, y], wool)
    block(d, [x - s * 1.4, y - s * 2.2, x + s * 1.4, y - s * 1.1], wool)
    nx = x + look * s * 1.1
    block(d, [nx - s * .3, y - s * 3.8, nx + s * .3, y - s * 2.0], wool)
    hx = nx + look * s * .25
    block(d, [hx - s * .45, y - s * 4.4, hx + s * .45, y - s * 3.7], wool)
    for e in (-1, 1):
        d.polygon([(hx + e * s * .3, y - s * 4.4), (hx + e * s * .45, y - s * 4.9), (hx + e * s * .15, y - s * 4.4)], fill=wool, outline=(180, 170, 160))
    d.ellipse([hx + look * s * .05 - 6, y - s * 4.2 - 6, hx + look * s * .05 + 6, y - s * 4.2 + 6], fill=(20, 20, 20))
    d.arc([hx - s * .2, y - s * 4.05, hx + s * .25, y - s * 3.8], 10, 170, fill=(20, 20, 20), width=3)
    d.rectangle([x - s * 1.0, y - s * 2.25, x + s * .6, y - s * 1.8], fill=(240, 80, 120))  # manta
    d.line([x - s * 1.4, y - s * 1.9, x - s * 1.9, y - s * 1.6 + s * .2 * math.sin(t * 5)], fill=wool, width=max(3, int(s * .2)))

def greg(d, x, y, s, t, arms="down", face="flat", look=0, walk=0.):
    top = avatar(d, x, y, s, GREG, t, walk, arms, face, look)
    hs = s * 1.25
    d.rectangle([x - hs / 2 - 4, top - s * .3, x + hs / 2 + 4, top + s * .2], fill=(40, 90, 40))
    d.rectangle([x - hs * .4, top + hs * .65, x + hs * .4, top + hs * 1.05], fill=(120, 70, 30))  # barba
    return top

def tent(d, x, y, s):
    d.polygon([(x - s * 2, y), (x, y - s * 2.2), (x + s * 2, y)], fill=(240, 140, 30), outline=(120, 60, 10))
    d.polygon([(x - s * .5, y), (x, y - s * 1.2), (x + s * .5, y)], fill=(90, 40, 10))

def toilet(d, x, y, s):
    block(d, [x - s * .5, y - s * 2.0, x + s * .5, y - s * 1.2], (250, 250, 250))
    d.ellipse([x - s * .8, y - s * 1.3, x + s * .8, y - s * .7], fill=(250, 250, 250), outline=(160, 160, 170), width=3)
    block(d, [x - s * .45, y - s * .9, x + s * .45, y], (250, 250, 250))

def pizza(d, x, y, s, t):
    block(d, [x - s * 1.2, y - s * .25, x + s * 1.2, y], (230, 220, 200))
    d.ellipse([x - s, y - s * .55, x + s, y - s * .05], fill=(240, 180, 70), outline=(190, 110, 40), width=4)
    for q in range(6):
        a = q * 1.05; d.ellipse([x + s * .6 * math.cos(a) - 10, y - s * .3 + s * .15 * math.sin(a) - 7, x + s * .6 * math.cos(a) + 10, y - s * .3 + s * .15 * math.sin(a) + 7], fill=(200, 40, 40))
    for q in range(3):  # vapor
        d.arc([x - 60 + q * 50, y - s * 1.6 - 15 * math.sin(t * 3 + q), x - 20 + q * 50, y - s * .6], 200, 340, fill=(255, 255, 255), width=5)

def beard(d, x, top, s, length):
    hs = s * 1.25
    d.rectangle([x - hs * .45, top + hs * .62, x + hs * .45, top + hs * (.95 + length)], fill=(120, 75, 35))

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
        screen(d, box, [("THE", 90, (255, 255, 255)), ("CIRCLE", int(200 * (.6 + .4 * p)), NEON), ("STAY INSIDE · WIN", 50, GOLD)])
        d.ellipse([W / 2 - 300, 1550, W / 2 + 300, 1700], outline=(255, 255, 255), width=12)
        ovl.append(None)

    elif sc == "rules":
        d = square(img, T)
        money_rain(d, T, 25)
        stk("LAST ONE OUT", W / 2, 360, 120, PINK, rot=-4)
        stk("$5,000,000", W / 2, 560, 120, (90, 200, 90), rot=4, scale=1 + .05 * math.sin(T * 10))
        ovl.append(None)

    elif sc == "jump_in":
        d = square(img, T)
        n = int(5 + 25 * ease(min(1, u / .7)))
        for i, (x, y) in enumerate(inside_spots(30, 1)[:n]):
            s = 30 + (y - (CY - RY)) / (2 * RY) * 20
            hop = abs(math.sin(T * 6 + i)) * 30
            avatar(d, x, y - hop, s, npc(600 + i), T + i, 0, "up", "laugh")
        avatar(d, CX, CY + 40, 72, ME, T, 0, "up", "laugh")
        stk("200 PEOPLE", W / 2, 400, 120, PINK, rot=-5)
        ovl.append(DAY[sc])

    elif sc == "mom":
        d = square(img, T, (255, 150, 60))
        contestants(d, T, 18, 2)
        mx = 140
        top = avatar(d, mx, CY + 120, 66, MOM, T, 0, "out", "yell", look=1)
        stk("DINNER!", mx + 180, 800, 110, (230, 90, 120), rot=-6, scale=1 + .08 * math.sin(T * 12))
        wx = CX - 200 - 300 * ease(max(0, (u - .45) / .55))
        avatar(d, wx, CY - 20, 46, npc(650), T * 2, 1 if u > .45 else 0, "down", "flat", look=-1)
        if u > .7: stk("OUT", wx, 1000, 100, RED, rot=4)
        ovl.append(DAY[sc])

    elif sc == "rain":
        d = square(img, T, (40, 50, 90))
        n = int(26 - 10 * ease(u))
        contestants(d, T, 26, 3, face="flat", skip=26 - n)
        avatar(d, CX, CY + 40, 72, ME, T, 0, "down", "flat")
        rnd = random.Random(int(T * 20))
        for q in range(90):
            x, y = rnd.uniform(0, W), rnd.uniform(0, H)
            d.line([x, y, x - 10, y + 50], fill=(170, 200, 255), width=4)
        for q in range(4):
            cx_ = 150 + q * 260; d.ellipse([cx_ - 140, 200, cx_ + 140, 330], fill=(90, 90, 110))
        if int(T * 3) % 5 == 0: flash(img, .35)
        stk("-50", W / 2, 420, 150, RED, rot=-5)
        ovl.append(DAY[sc])

    elif sc in ("pizza", "pizza_b"):
        d = square(img, T)
        px, py = CX + RX + 70, CY + 90
        pizza(d, px, py, 85, T)
        if sc == "pizza":
            contestants(d, T, 20, 4, face="shock", arms_fn=lambda i: "out")
            avatar(d, CX, CY + 40, 72, ME, T, 0, "down", "shock")
            if u > .45: stk("1 INCH OUTSIDE", px - 180, 1000, 85, (240, 180, 70), rot=5)
        else:
            for i, (x, y) in enumerate(inside_spots(16, 4)):
                v = ease(min(1, u * 1.5))
                xx = x + (px - x) * v * .9; yy = y + (py - y) * v * .9
                avatar(d, xx, yy, 40, npc(600 + i), T * 2 + i, 1.5, "up", "yell", look=1)
            avatar(d, CX - 120, CY + 40, 72, ME, T, 0, "down", "flat", look=1)
            stk("-80", W / 2, 420, 150, RED, rot=4)
            amp = 4
        ovl.append(DAY[sc])

    elif sc == "bees":
        d = square(img, T)
        half = u < .45
        contestants(d, T, 10, 5, face="shock" if half else "flat")
        avatar(d, CX, CY + 40, 72, ME, T, 0, "up" if half else "down", "shock")
        if half:
            for q in range(30):
                bx = CX + 380 * math.sin(T * 2.3 + q * 1.7); by = 1350 + 220 * math.sin(T * 3.1 + q)
                d.ellipse([bx - 12, by - 9, bx + 12, by + 9], fill=(250, 210, 40)); d.line([bx - 4, by - 9, bx - 4, by + 9], fill=(20, 20, 20), width=4)
            stk("BEES", W / 2, 420, 150, (250, 210, 40), fg=(20, 20, 20), rot=-5)
        else:
            mx = CX + 300
            top = avatar(d, mx, CY - 60, 60, MIME, T, 0, "out" if int(T * 2) % 2 else "up", "smile", look=-1)
            d.rectangle([mx - 34, top + 20, mx + 34, top + 40], fill=(20, 20, 20))
            for q in range(4): d.rectangle([mx - 60, CY - 60 - 230 + q * 45, mx + 60, CY - 60 - 210 + q * 45], fill=(250, 250, 250))
            stk("THE MIME", W / 2, 420, 140, (250, 250, 250), fg=(20, 20, 20), rot=5)
            if u > .75: stk("TOO MUCH", W / 2, 620, 100, RED, rot=-4)
        ovl.append(DAY[sc])

    elif sc in ("greg", "greg_b", "greg_huss", "greg_run"):
        d = square(img, T)
        gx = CX + 220
        if sc in ("greg_b", "greg_huss"):
            tent(d, CX + 330, CY - 30, 80)
            toilet(d, CX - 360, CY + 30, 50)
        if sc != "greg_run":
            llama(d, CX + 80, CY + 150, 72, T, look=-1) if sc != "greg" else None
            face = "flat"
            if sc == "greg_huss" and k >= 0:
                face = "shock"
            back = (25 * (k + 1)) if sc == "greg_huss" and k >= 0 else 0
            greg(d, gx + back, CY + 20, 72, T, "down" if sc != "greg_huss" else ("up" if k >= 0 else "down"), face, look=-1)
            z = 1 + .15 * hit
            avatar(d, CX - 220, CY + 30, 76 * z, ME, T, 0, "out" if hit > .1 else "down", "yell" if hit > .2 else "flat", look=1)
            if sc == "greg":
                stk("ME", CX - 220, 870, 90, (40, 90, 210), rot=-4)
                stk("GREG", gx, 870, 90, (60, 120, 60), rot=4)
                stk("FINAL 2", W / 2, 420, 140, GOLD, fg=(255, 255, 255), rot=-4)
            if sc == "greg_b":
                third = min(2, int(u * 3))
                stk(["A TENT", "A TOILET", "A LLAMA"][third], W / 2, 420, 130, [(240, 140, 30), (160, 160, 170), (240, 80, 120)][third], rot=-4 + 4 * third)
            if sc == "greg_huss" and 0 <= k < seg["nh"]:
                for j in range(k + 1):
                    stk("HUSS", 180 + (j * 191) % 720, 360 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                        rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
            amp = int(25 * hit)
        else:
            v = ease(u)
            greg(d, gx + 700 * v, CY + 20 - abs(math.sin(T * 10)) * 30, 72, T * 2, "up", "yell", look=1, walk=1.6)
            tent_x = CX + 330 + 900 * v; tent(d, tent_x, CY - 30 - 300 * v, 80)
            llama(d, CX + 80, CY + 150, 72, T, look=-1)
            avatar(d, CX - 220, CY + 30, 76, ME, T, 0, "down", "smile", look=1)
            stk("GREG: OUT", W / 2, 420, 120, RED, rot=-4)
            if u > .55: stk("LLAMA: STAYED", W / 2, 620, 90, (240, 80, 120), rot=4)
        ovl.append(DAY[sc])

    elif sc == "days":
        third = min(2, int(u * 3))
        night = (u * 6) % 1 > .5
        d = square(img, T, (20, 20, 60) if night else None)
        if third >= 1:  # hojas de otoño / nieve
            rnd = random.Random(int(T * 8))
            for q in range(40):
                x, y = rnd.uniform(0, W), (rnd.uniform(0, H) + T * 200) % H
                col = (240, 140, 40) if third == 1 else (255, 255, 255)
                d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=col)
        llama(d, CX + 200, CY + 150, 72, T, look=-1)
        top = avatar(d, CX - 80, CY + 40, 80, ME, T, 0, "down", "flat")
        beard(d, CX - 80, top, 80, [.1, .6, 1.4][third])
        stk(["DAY 30", "DAY 50", "DAY 100"][third], W / 2, 400, 160, GOLD, fg=(255, 255, 255), rot=-5 + 5 * third)
        if (u * 3) % 1 < .05: flash(img, .6)
        ovl.append(None)

    elif sc == "phone":
        d = square(img, T)
        llama(d, CX + 220, CY + 150, 72, T, look=-1)
        top = avatar(d, CX - 60, CY + 40, 84, ME, T, 0, "out", "smile", look=1)
        beard(d, CX - 60, top, 84, 1.4)
        block(d, [CX + 90, top + 20, CX + 130, top + 120], (30, 30, 30))
        stk("DID I WIN?", W / 2, 420, 130, (40, 90, 210), rot=-4, scale=1 + .05 * math.sin(T * 10))
        for q in range(3):
            r = 40 + ((T * 120 + q * 40) % 120)
            d.arc([CX + 110 - r, top + 70 - r, CX + 110 + r, top + 70 + r], -40, 40, fill=(255, 255, 255), width=5)
        ovl.append(None)

    elif sc == "cancelled":
        sky(img, (20, 20, 30), (40, 40, 50)); d = ImageDraw.Draw(img)
        x0, y0, x1, y1 = 90, 380, 990, 1180
        d.rectangle([x0 - 20, y0 - 20, x1 + 20, y1 + 20], fill=(60, 60, 70))
        rnd = random.Random(int(T * 20))
        for yy in range(y0, y1, 8):
            for xx in range(x0, x1, 30):
                g = rnd.randint(30, 220); d.rectangle([xx, yy, xx + 30, yy + 8], fill=(g, g, g))
        d.rectangle([x0, (y0 + y1) / 2 - 90, x1, (y0 + y1) / 2 + 90], fill=RED)
        d.text(((x0 + x1) / 2, (y0 + y1) / 2), "CANCELLED", font=font(130), fill=(255, 255, 255), anchor="mm")
        if u > .5: stk("ON DAY 2", W / 2, 1350, 120, (255, 255, 255), fg=RED, rot=-4)
        if u > .75: stk("NOBODY TOLD YOU?", W / 2, 1540, 85, (20, 20, 20), rot=4)
        ovl.append(None)

    elif sc in ("end", "tourists"):
        d = square(img, T)
        llama(d, CX + 230, CY + 150, 72, T, look=-1)
        z = 1 + .12 * hit
        top = avatar(d, CX - 80, CY + 50, 84 * z, ME, T, 0, "out" if hit > .1 else "down", "yell" if hit > .2 else "smile")
        beard(d, CX - 80, top, 84 * z, 1.4)
        if sc == "end":
            d.rectangle([CX - 160, CY - 360, CX - 150, CY - 150], fill=(110, 70, 40))
            block(d, [CX - 300, CY - 460, CX - 10, CY - 360], (255, 255, 255))
            d.text((CX - 155, CY - 410), "HOME", font=font(56), fill=(40, 40, 40), anchor="mm")
            stk("MY HOUSE NOW", W / 2, 420, 120, (240, 80, 120), rot=-4)
        else:
            for i, x in enumerate([90, 250, 830, 990]):
                avatar(d, x, CY + 230, 52, npc(700 + i), T, 0, "out", "laugh", look=1 if x < W / 2 else -1)
                block(d, [x + (50 if x < W / 2 else -120), CY + 230 - 170, x + (120 if x < W / 2 else -50), CY + 230 - 120], (30, 30, 30))
            if hit > .3: flash(img, .5)
            if 0 <= k < seg["nh"]:
                stk("HUSS!", W / 2 + (k - 1) * 250, 450, 130, (40, 90, 210), rot=-8 + 8 * k, scale=1 + .4 * hit)
            else:
                stk("TOURIST ATTRACTION", W / 2, 420, 85, GOLD, fg=(255, 255, 255), rot=-4)
            amp = int(15 * hit)
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
def buzzer(dur=.5):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * 110 * t)) * .18 * np.minimum(1, (dur - t) / .1)).astype(np.float32)

def rain(dur):
    n = int(SR * dur); x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 1500)] = 0
    y = np.fft.irfft(X, n); y /= np.abs(y).max()
    t = np.arange(n) / SR
    return (y * .12 * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .3)).astype(np.float32)

def buzz_bees(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * (210 + 15 * np.sin(2 * np.pi * 3 * t)) * t)) * .06 * np.minimum(1, (dur - t) / .2)).astype(np.float32)

def shutter():
    n = int(SR * .12); x = np.random.randn(n) * np.exp(-np.arange(n) / SR * 50)
    return (x * .4).astype(np.float32)

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
    s = by["jump_in"]; put(crowd_roar(s["dur"]) * .6, s["start"])
    s = by["mom"]; put(buzzer(), s["start"] + (s["dur"] + .2) * .7)
    s = by["rain"]; put(rain(s["dur"] + .3), s["start"]); put(m.sfx("boom") * .5, s["start"] + .5)
    s = by["pizza_b"]; put(crowd_roar(s["dur"]) * .8, s["start"]); put(buzzer(), s["start"] + .5)
    s = by["bees"]; put(buzz_bees((s["dur"] + .2) * .45), s["start"]); put(m.sfx("boing") * .6, s["start"] + (s["dur"] + .2) * .5)
    s = by["greg"]; put(m.sfx("boom") * .6, s["start"])
    s = by["greg_b"]
    for q in range(3): put(m.sfx("pop") * .8, s["start"] + q * (s["dur"] + .2) / 3)
    s = by["greg_run"]; put(m.sfx("whoosh"), s["start"]); put(buzzer(), s["start"] + .3)
    s = by["days"]
    for q in range(3): put(m.sfx("whoosh") * .7, s["start"] + q * (s["dur"] + .2) / 3)
    s = by["phone"]
    for q in range(2): put(tone(440, .4, .2) + tone(480, .4, .2), s["start"] + .2 + q * .6)
    s = by["cancelled"]; put(buzzer(.9), s["start"] + .1); put(rain(s["dur"]) * .6, s["start"])
    s = by["end"]; put(m.sfx("ding") * .5, s["start"] + .3)
    for s in segs:
        if s["scene"] == "tourists":
            for h in s["hits"]: put(shutter(), h)
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
hn.SHOW = "THE CIRCLE"
hn.TICKER = "  LIVE · THE CIRCLE · LAST ONE OUT WINS · $5,000,000 · DON'T STEP OUT · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "circle.mp4"]
    m.main()
