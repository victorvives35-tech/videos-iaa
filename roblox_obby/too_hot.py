#!/usr/bin/env python3
"""Historia 12: TOO HOT — concurso de guindillas. El último HUSS sale con FUEGO.

Uso: python3 too_hot.py --voice ruta/en_US-ryan-high.onnx [--out too_hot.mp4]
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
import hunt as hn
import dont_blink as db
from dont_say import granny, host, confetti
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)
from hunt import neon_city, screen, tv_overlay, money_rain, captions_single, tint, flash, tone, crowd_roar, PINK, PURPLE, NEON, GOLD

ME = CHARS["me"]
RED = (255, 40, 40)
FIRE = dict(head=(255, 205, 160), torso=(210, 40, 30), legs=(40, 40, 50), hair=None, logo=(255, 220, 40))

SCRIPT = [
    ("In this town, there's a TV show called Too Hot.", "intro", None),
    ("Ten peppers. Each one hotter than the last. Eat them all and win ten million dollars.", "rules", None),
    ("Fifty people sat at the table. Including me.", "start", None),
    ("Pepper one. A sweet little bell pepper. One guy cried anyway.", "p1", None),
    ("Pepper three. A jalapeño. Everybody started sweating.", "p3", None),
    ("Pepper five. Grandma ate it... and asked for more.", "p5", None),
    ("Pepper six. Steam came out of people's ears. Like tiny trains.", "p6", None),
    ("Pepper seven. One guy ran straight into the lake. He's still in there.", "p7", None),
    ("Pepper eight. It was so hot, it melted the plate.", "p8", None),
    ("Pepper nine. Firefighters had to deliver it. In a metal box.", "p9", None),
    ("Only two people left. Me... and Grandma.", "final2", None),
    ("Grandma took one bite... floated up to the ceiling... and said: nope.", "granny_out", None),
    ("The final pepper. The Huss Pepper. One million spicy units.", "final", None),
    ("I ate it. My face turned red. Then purple. I tried to say thank you... but instead I said:", "fire", "solo", 6),
    ("I set the trophy on fire. And the ten million dollars.", "burn", None),
    ("And the whole TV studio.", "burn_b", None),
    ("Now I work for the town. Every summer, I light the barbecue.", "bbq", None),
    ("Like this:", "bbq_huss", "solo", 1),
]

LEVEL = {"start": 0, "p1": 1, "p3": 3, "p5": 5, "p6": 6, "p7": 7, "p8": 8, "p9": 9, "final2": 9, "granny_out": 9, "final": 10, "fire": 10}
CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.15, (.5, .45), (.5, .4)),
    "start": (1.2, 1.0, (.5, .62), (.5, .6)), "p1": (1.0, 1.6, (.5, .6), (.22, .62)),
    "p3": (1.2, 1.0, (.5, .6), (.5, .6)), "p5": (1.0, 1.5, (.5, .6), (.78, .62)),
    "p6": (1.0, 1.3, (.5, .6), (.5, .58)), "p7": (1.15, 1.0, (.5, .6), (.5, .62)),
    "p8": (1.0, 1.5, (.5, .62), (.5, .7)), "p9": (1.2, 1.0, (.4, .6), (.5, .6)),
    "final2": (1.0, 1.15, (.5, .6), (.5, .6)), "granny_out": (1.0, 1.0, (.5, .55), (.5, .45)),
    "final": (1.0, 1.5, (.5, .6), (.5, .66)), "fire": (1.15, 1.0, (.5, .55), (.5, .55)),
    "burn": (1.0, 1.25, (.5, .55), (.6, .6)), "burn_b": (1.25, 1.0, (.5, .55), (.5, .55)),
    "bbq": (1.0, 1.2, (.5, .6), (.5, .62)), "bbq_huss": (1.2, 1.0, (.5, .62), (.5, .6)),
}

# ------------------------------------------------------------------ piezas
def pepper(d, x, y, s, kind, T):
    """Guindilla: bell, jalapeno, habanero, ghost, reaper, huss."""
    col = {"bell": (60, 180, 60), "jalapeno": (40, 140, 50), "habanero": (255, 140, 20), "ghost": (220, 30, 30),
           "reaper": (200, 20, 20), "huss": (150, 40, 220)}[kind]
    if kind == "bell":
        d.ellipse([x - s, y - s * .9, x + s, y + s * .9], fill=col, outline=(30, 100, 30), width=4)
    else:
        d.polygon([(x - s * .5, y - s * .8), (x + s * .5, y - s * .8), (x + s * .35, y + s * .2), (x + s * .1 if kind != "reaper" else x + s * .6, y + s * 1.2),
                   (x - s * .35, y + s * .2)], fill=col, outline=tuple(int(c * .6) for c in col))
    d.rectangle([x - s * .12, y - s * 1.15, x + s * .12, y - s * .8], fill=(40, 120, 40))
    if kind in ("huss", "reaper", "ghost"):
        for q in range(3):  # aura
            r = s * (1.4 + .2 * q + .1 * math.sin(T * 8 + q))
            d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 120 if kind != "huss" else 60, 0 if kind != "huss" else 255), width=3)
    if kind == "huss":
        d.text((x, y - s * .2), "H", font=font(int(s * .7)), fill=(255, 220, 40), anchor="mm")

def table(d, y=1460):
    block(d, [-20, y, W + 20, y + 60], (180, 40, 60))
    d.rectangle([0, y + 60, W, y + 260], fill=(140, 25, 45))
    for q in range(0, W, 80): d.rectangle([q, y + 60, q + 40, y + 260], fill=(160, 30, 50))

def flames(d, x, y, w, h, T, k=0):
    for i in range(5):
        fx = x + (i - 2) * w * .2; hgt = h * (.6 + .4 * abs(math.sin(T * 10 + i * 1.7 + k)))
        d.polygon([(fx - w * .14, y), (fx + w * .14, y), (fx, y - hgt)], fill=(255, 110, 0))
        d.polygon([(fx - w * .07, y), (fx + w * .07, y), (fx, y - hgt * .6)], fill=(255, 220, 60))

def fire_breath(d, x, y, length, T, dirx=1):
    rnd = random.Random(int(T * 30))
    for q in range(14):
        L = length * rnd.uniform(.6, 1.0); spread = rnd.uniform(-.35, .35)
        ex, ey = x + dirx * L, y + L * spread
        w = rnd.uniform(25, 60)
        col = rnd.choice([(255, 90, 0), (255, 160, 0), (255, 220, 60)])
        d.polygon([(x, y - 15), (ex, ey - w), (ex + dirx * 40, ey), (ex, ey + w), (x, y + 15)], fill=col)

def trophy(d, x, y, s):
    d.polygon([(x - s, y - s * 2.2), (x + s, y - s * 2.2), (x + s * .5, y - s * 1.1), (x - s * .5, y - s * 1.1)], fill=GOLD, outline=(150, 110, 10))
    d.rectangle([x - s * .15, y - s * 1.1, x + s * .15, y - s * .5], fill=GOLD)
    block(d, [x - s * .6, y - s * .5, x + s * .6, y], (120, 80, 30))

def money_stack(d, x, y, s, burnt=0.):
    for r in range(4):
        for q in range(4 - r):
            bx = x - (3 - r) * s * .5 + q * s; by = y - r * s * .45
            col = tuple(int(c * (1 - burnt) + 30 * burnt) for c in (90, 200, 90))
            d.rectangle([bx - s * .48, by - s * .2, bx + s * .48, by + s * .2], fill=col, outline=(30, 110, 40), width=2)

def heat_meter(d, level, T):
    """Termómetro de picante a la derecha (0..10)."""
    x0, y0, x1, y1 = W - 110, 330, W - 50, 1020
    d.rounded_rectangle([x0, y0, x1, y1], radius=30, fill=(30, 20, 40), outline=(255, 255, 255), width=5)
    fill = (y1 - y0 - 20) * level / 10
    col = (60, 200, 60) if level < 4 else (255, 160, 0) if level < 8 else (255, 40, 40) if level < 10 else (180, 60, 255)
    d.rounded_rectangle([x0 + 10, y1 - 10 - fill, x1 - 10, y1 - 10], radius=20, fill=col)
    d.ellipse([x0 - 18, y1 - 30, x1 + 18, y1 + 50], fill=col, outline=(255, 255, 255), width=5)
    d.text(((x0 + x1) / 2, y0 - 30), "HEAT", font=font(30), fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(20, 20, 20))

def players(d, T, n=5, out=(), face="flat", sweat=False, steam=False, skip_me=False, me_face="flat", me_z=1.0, me_col=None):
    xs = [130, 330, 540, 750, 950][:n]
    tops = {}
    for i, x in enumerate(xs):
        if i == 2:
            if skip_me: continue
            c = dict(ME);
            if me_col: c = dict(ME, head=me_col)
            top = avatar(d, x, 1560, 66 * me_z, c, T, 0, "down", me_face)
        elif i in out:
            continue
        else:
            top = avatar(d, x, 1560, 50, npc(1700 + i), T, 0, "down", face)
        tops[i] = (x, top)
        s = 66 * me_z if i == 2 else 50
        if sweat:
            for q in range(2):
                dy = (T * 200 + q * 60 + i * 30) % 120
                d.ellipse([x + s * .5 - 8, top + 10 + dy, x + s * .5 + 8, top + 30 + dy], fill=(120, 200, 255))
        if steam:
            for e in (-1, 1):
                for q in range(3):
                    r = 14 + q * 10; off = ((T * 80 + q * 25) % 90)
                    d.ellipse([x + e * (s * .8 + off) - r, top + s * .5 - off - r, x + e * (s * .8 + off) + r, top + s * .5 - off + r], fill=(240, 240, 250))
    return tops

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    sc = seg["scene"]; dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]
    lvl = LEVEL.get(sc)

    if sc in ("intro", "rules"):
        d = neon_city(img, T)
        if sc == "intro":
            p = ease(min(1, t / .5))
            screen(d, box, [("TOO", 120, (255, 255, 255)), ("HOT", int(230 * (.6 + .4 * p)), (255, 90, 30)), ("THE SPICY SHOW", 50, GOLD)])
            flames(d, W / 2, 1650, 700, 260, T)
        else:
            third = min(2, int(u * 3))
            screen(d, box, [[("10", 260, (255, 90, 30)), ("PEPPERS", 110, (255, 255, 255))],
                            [("EACH ONE", 90, (255, 255, 255)), ("HOTTER", 150, (255, 90, 30))],
                            [("PRIZE", 80, (255, 255, 255)), ("$10,000,000", 120, (90, 220, 90))]][third])
            for q, kind in enumerate(["bell", "jalapeno", "habanero", "ghost", "reaper"]):
                pepper(d, 150 + q * 195, 1350, 45, kind, T)
            if third == 2: money_rain(d, T)
        ovl.append(None)

    elif sc in ("start", "p1", "p3", "p5", "p6", "p8", "p9", "final2", "final", "fire"):
        d = db.studio(img, T)
        if sc == "start":
            players(d, T, face="smile", me_face="laugh")
            table(d)
            for q in range(5): pepper(d, [130, 330, 540, 750, 950][q], 1430, 28, "bell", T)
            stk("50 PLAYERS", W / 2, 400, 120, PINK, rot=-5)
        elif sc == "p1":
            tops = players(d, T)
            table(d)
            x, top = tops[0]
            for e in (-1, 1):
                for q in range(3):
                    ty = top + 70 + ((T * 260 + q * 40) % 160)
                    d.ellipse([x + e * 15 - 8, ty, x + e * 15 + 8, ty + 18], fill=(90, 170, 255))
            pepper(d, 540, 1410, 45, "bell", T)
            stk("BELL PEPPER", W / 2, 400, 110, (60, 180, 60), rot=-4)
            if u > .55: stk("CRYING", 200, 1000, 100, (90, 170, 255), rot=5)
        elif sc == "p3":
            players(d, T, out=(0,), sweat=True)
            table(d)
            pepper(d, 540, 1410, 40, "jalapeno", T)
            stk("JALAPEÑO", W / 2, 400, 120, (40, 140, 50), rot=-4)
            if u > .5: stk("SWEATING", W / 2, 600, 100, (120, 200, 255), rot=4)
        elif sc == "p5":
            players(d, T, out=(0, 4), sweat=True)
            gx = 900
            granny(d, gx, 1560, 54, T, "up", "laugh", look=-1)
            table(d)
            pepper(d, 540, 1410, 40, "habanero", T)
            stk("HABANERO", W / 2, 400, 120, (255, 140, 20), rot=-4)
            if u > .5: stk("MORE!", gx, 1000, 130, (170, 90, 160), rot=6, scale=1 + .08 * math.sin(T * 12))
        elif sc == "p6":
            players(d, T, out=(0,), steam=True)
            table(d)
            pepper(d, 540, 1410, 40, "ghost", T)
            stk("GHOST PEPPER", W / 2, 400, 110, (220, 30, 30), rot=-4)
            if u > .5: stk("CHOO CHOO", W / 2, 600, 110, (240, 240, 250), fg=(40, 40, 40), rot=4)
        elif sc == "p8":
            players(d, T, out=(0, 1, 4), sweat=True, me_col=(255, 150, 130))
            table(d)
            mlt = ease(u)
            d.ellipse([400, 1400 + 30 * mlt, 680, 1460], fill=(240, 240, 245), outline=(180, 180, 190), width=4)
            for q in range(5):  # el plato se derrite
                gx = 420 + q * 55
                d.rounded_rectangle([gx, 1440, gx + 22, 1460 + 160 * mlt + 20 * math.sin(T * 3 + q)], radius=11, fill=(240, 240, 245))
            pepper(d, 540, 1390, 40, "reaper", T)
            stk("THE REAPER", W / 2, 400, 120, (200, 20, 20), rot=-4)
            if u > .5: stk("PLATE: MELTED", W / 2, 600, 95, (240, 240, 245), fg=(40, 40, 40), rot=4)
        elif sc == "p9":
            players(d, T, out=(0, 1, 3), me_col=(255, 130, 110))
            table(d)
            fx_ = 1100 - 500 * ease(min(1, u / .6))
            top = avatar(d, fx_, 1560, 60, FIRE, T * 2, 1 if u < .6 else 0, "out", "shock", look=-1)
            d.ellipse([fx_ - 50, top - 30, fx_ + 50, top + 30], fill=(250, 210, 40))  # casco
            block(d, [fx_ - 130, 1350, fx_ - 20, 1440], (160, 160, 170))
            d.polygon([(fx_ - 75, 1365), (fx_ - 105, 1420), (fx_ - 45, 1420)], fill=(250, 210, 40)); d.text((fx_ - 75, 1402), "!", font=font(36), fill=(20, 20, 20), anchor="mm")
            stk("FIREFIGHTERS", W / 2, 400, 110, (210, 40, 30), rot=-4)
            if u > .5: stk("METAL BOX", W / 2, 600, 100, (160, 160, 170), fg=(20, 20, 20), rot=4)
        elif sc == "final2":
            players(d, T, out=(0, 1, 3, 4), me_col=(255, 130, 110))
            granny(d, 820, 1560, 54, T, "down", "smile", look=-1)
            table(d)
            stk("FINAL 2", W / 2, 400, 140, GOLD, fg=(255, 255, 255), rot=-4)
            stk("ME", 540, 1000, 90, (40, 90, 210), rot=-4); stk("GRANDMA", 820, 1000, 80, (170, 90, 160), rot=4)
        elif sc == "final":
            players(d, T, out=(0, 1, 3, 4), me_col=(255, 130, 110), me_face="shock")
            table(d)
            pepper(d, 540, 1360, 60 + 6 * math.sin(T * 8), "huss", T)
            stk("THE HUSS PEPPER", W / 2, 400, 110, (150, 40, 220), rot=-4, scale=1 + .05 * math.sin(T * 10))
            if u > .5: stk("1,000,000 UNITS", W / 2, 600, 95, RED, rot=4)
            tint(img, (150, 40, 220), 30 + 20 * math.sin(T * 6))
        else:  # fire: cada HUSS escupe fuego
            redness = min(1, u * 2.5)
            face_col = tuple(int(a * (1 - redness) + b * redness) for a, b in zip((255, 205, 160), (200, 40, 140) if u > .3 else (255, 60, 40)))
            table(d, 1530)
            trophy(d, 930, 1530, 60); money_stack(d, 760, 1525, 55, burnt=min(1, max(0, k + 1) / 6))
            z = 1 + .15 * hit
            top = avatar(d, 380, 1560, 80 * z, dict(ME, head=face_col), T, 0, "out" if hit > .1 else "down", "yell" if hit > .2 else "flat", look=1)
            if 0 <= k < seg["nh"]:
                fire_breath(d, 380 + 80 * z * .4, top + 80 * z * .95, 380 + 300 * hit, T)
                for j in range(k + 1):
                    stk("HUSS", 180 + (j * 191) % 720, 360 + (j % 3) * 130, 120, [(255, 90, 0), (255, 40, 40), (150, 40, 220)][j % 3],
                        rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
                if k >= 1: flames(d, 850, 1440, 280, 160 + 30 * k, T)
                tint(img, (255, 120, 0), 60 * hit)
            else:
                stk("RED" if u < .3 else "PURPLE", W / 2, 400, 150, (255, 60, 40) if u < .3 else (200, 40, 140), rot=-5)
            amp = int(30 * hit)
        if lvl is not None: heat_meter(d, lvl, T)
        ovl.append(f"PEPPER {lvl}/10" if lvl else None)

    elif sc == "p7":
        sky(img, (120, 200, 255), (220, 240, 255)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1200, W, H], fill=(60, 140, 220))
        d.rectangle([0, 1150, W, 1210], fill=(150, 200, 110))
        hx = 540 + 30 * math.sin(T * 2)
        if u < .45:
            v = u / .45
            avatar(d, 100 + 440 * v, 1200 + 300 * v ** 2, 50, npc(1750), T * 2, 1.6, "up", "yell", look=1)
            stk("TOO HOT", W / 2, 400, 130, RED, rot=-4)
        else:
            d.rectangle([hx - 40, 1290, hx + 40, 1370], fill=(255, 140, 130))  # cabeza asomando
            d.ellipse([hx - 25, 1305, hx - 10, 1320], fill=(20, 20, 20)); d.ellipse([hx + 10, 1305, hx + 25, 1320], fill=(20, 20, 20))
            for q in range(4):
                r = 25 + q * 15; off = (T * 90 + q * 30) % 140
                d.ellipse([hx - r + 20 * math.sin(q), 1260 - off - r, hx + r + 20 * math.sin(q), 1260 - off + r], fill=(245, 245, 250))
            stk("STILL IN THERE", W / 2, 400, 110, (60, 140, 220), fg=(255, 255, 255), rot=4)
            stk("SPLASH", hx, 1050, 110, (90, 170, 255), rot=-8) if u < .6 else None
        ovl.append("PEPPER 7/10")

    elif sc == "granny_out":
        d = db.studio(img, T)
        table(d)
        rise = ease(u) * 900
        top = granny(d, 820, 1560 - rise, 54, T, "up", "shock" if u < .6 else "flat", look=-1)
        for q in range(4):
            d.ellipse([820 - 60 + q * 30, 1560 - rise + 20 + q * 40, 820 - 20 + q * 30, 1560 - rise + 60 + q * 40], fill=(240, 240, 250))
        players(d, T, out=(0, 1, 3, 4), me_col=(255, 130, 110), me_face="shock")
        if u > .6: stk("NOPE", 820, 1000 - rise * .3, 140, (170, 90, 160), rot=6, scale=1 + .06 * math.sin(T * 12))
        heat_meter(d, 9, T)
        ovl.append("PEPPER 9/10")

    elif sc in ("burn", "burn_b"):
        d = db.studio(img, T)
        tint(img, (255, 80, 0), 70); d = ImageDraw.Draw(img)
        if sc == "burn":
            trophy(d, 760, 1450, 90)
            money_stack(d, 760, 1560, 90, burnt=.8)
            flames(d, 760, 1450, 360, 330, T)
            avatar(d, 300, 1650, 70, ME, T, 0, "down", "shock", look=1)
            stk("TROPHY: ON FIRE", W / 2, 400, 100, (255, 90, 0), rot=-4)
            if u > .45: stk("$10,000,000: ON FIRE", W / 2, 600, 80, RED, rot=4)
        else:
            for q in range(7):
                flames(d, 80 + q * 160, 1450 - (q % 2) * 300, 260, 300 + 60 * math.sin(T * 3 + q), T, q)
            for i, x in enumerate([200, 880]):
                top = avatar(d, x, 1650, 56, FIRE, T, 0, "out", "shock", look=1 if x < W / 2 else -1)
                d.ellipse([x - 46, top - 28, x + 46, top + 28], fill=(250, 210, 40))
                for q in range(10):  # chorro de agua
                    t_ = q / 10
                    wx = x + (1 if x < W / 2 else -1) * (60 + 360 * t_); wy = top + 100 - 300 * t_ + 400 * t_ ** 2
                    d.ellipse([wx - 14, wy - 14, wx + 14, wy + 14], fill=(120, 200, 255))
            avatar(d, 540, 1650, 64, ME, T, 0, "up", "shock")
            stk("THE WHOLE STUDIO", W / 2, 400, 100, (255, 90, 0), rot=-4, scale=1 + .05 * math.sin(T * 10))
            amp = 6
        ovl.append(None)

    elif sc in ("bbq", "bbq_huss"):
        sky(img, (120, 200, 255), (255, 230, 180)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1300, W, H], fill=(110, 180, 90))
        for q in range(0, W, 140):  # valla
            d.rectangle([q + 20, 1050, q + 70, 1300], fill=(240, 230, 210))
        d.rectangle([0, 1120, W, 1150], fill=(240, 230, 210))
        gx, gy = 700, 1480
        block(d, [gx - 170, gy - 160, gx + 170, gy - 60], (40, 40, 45))
        for e in (-1, 1): d.line([gx + e * 120, gy - 60, gx + e * 160, gy + 80], fill=(40, 40, 45), width=12)
        lit = sc == "bbq_huss" and k >= 0
        for q in range(4):  # salchichas
            d.rounded_rectangle([gx - 140 + q * 72, gy - 190, gx - 90 + q * 72, gy - 165], radius=12, fill=(190, 90, 60) if not lit else (140, 60, 30))
        if lit: flames(d, gx, gy - 160, 300, 140, T)
        for i, x in enumerate([120, 980]):
            avatar(d, x, 1700, 46, npc(1800 + i), T, 0, "up" if lit else "down", "laugh" if lit else "smile", look=1 if x < W / 2 else -1)
        z = 1 + .15 * hit
        top = avatar(d, 330, 1640, 70 * z, ME, T, 0, "out" if hit > .1 else "down", "yell" if hit > .2 else "smile", look=1)
        if sc == "bbq":
            stk("TOWN LIGHTER", W / 2, 400, 120, (255, 90, 0), rot=-4)
        else:
            if hit > .05: fire_breath(d, 330 + 30, top + 80, 300, T)
            if 0 <= k: stk("HUSS!", W / 2, 420, 150, (255, 90, 0), rot=-6, scale=1 + .4 * hit)
            if lit: confetti(d, T, 40)
            amp = int(20 * hit)
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
def whistle(dur=.9):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (900 + 80 * np.sin(2 * np.pi * 6 * t)) * t) * .12 * np.minimum(1, t / .05) * np.minimum(1, (dur - t) / .2)).astype(np.float32)

def roar_fire(dur=.45):
    n = int(SR * dur); x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 80) | (f > 2500)] = 0
    y = np.fft.irfft(X, n); y /= np.abs(y).max(); t = np.arange(n) / SR
    return (y * .45 * np.minimum(1, t / .02) * np.exp(-t * 3)).astype(np.float32)

def crackle(dur):
    n = int(SR * dur); out = np.zeros(n, np.float32); rnd = np.random.default_rng(3)
    for p in rnd.integers(0, n - 400, int(dur * 40)):
        out[p:p + 300] += rnd.standard_normal(300).astype(np.float32) * np.exp(-np.arange(300) / 40) * .25
    return out

def siren(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 700 + 250 * np.sin(2 * np.pi * .8 * t)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .1).astype(np.float32)

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
    s = by["intro"]; put(roar_fire(1.0), s["start"]); put(tone(880, .4) + tone(1320, .4), s["start"] + .4)
    s = by["rules"]
    for q in range(3): put(tone(700, .2), s["start"] + q * (s["dur"] + .2) / 3)
    for key in ("p1", "p3", "p5", "p6", "p8", "p9", "final"):
        put(m.sfx("ding") * .5, by[key]["start"] + .1)
    s = by["p6"]; put(whistle(), s["start"] + (s["dur"] + .2) * .55)
    s = by["p7"]; put(m.sfx("whoosh"), s["start"] + .2); put(m.sfx("boom") * .5, s["start"] + (s["dur"] + .2) * .45)
    s = by["p9"]; put(siren(s["dur"] + .2), s["start"])
    s = by["granny_out"]; put(m.riser(s["dur"]) * .5, s["start"])
    s = by["final"]; put(m.sfx("boom") * .7, s["start"])
    for h in by["fire"]["hits"]: put(roar_fire(), h)
    s = by["burn"]; put(crackle(s["dur"] + by["burn_b"]["dur"] + .4), s["start"])
    s = by["burn_b"]; put(siren(s["dur"] + .2), s["start"])
    for h in by["bbq_huss"]["hits"]: put(roar_fire(), h); put(crowd_roar(1.2) * .5, h + .2)
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
db.STUDIO_TITLE = "TOO HOT"
hn.SHOW = "TOO HOT"
hn.TICKER = "  LIVE · TOO HOT · 10 PEPPERS · $10,000,000 · DON'T DRINK THE MILK · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "too_hot.mp4"]
    m.main()
