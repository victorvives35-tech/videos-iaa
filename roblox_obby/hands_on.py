#!/usr/bin/env python3
"""Historia 8: HANDS ON — concurso de TV (mismo estilo que THE HUNT / DON'T SAY HUSS / THE CIRCLE).

Uso: python3 hands_on.py --voice ruta/en_US-ryan-high.onnx [--out hands_on.mp4]
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
import hunt as hn
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)
from hunt import neon_city, screen, tv_overlay, money_rain, captions_single, tint, flash, tone, crowd_roar, PINK, PURPLE, NEON, GOLD

ME = CHARS["me"]
RED = (255, 40, 40)
GND = 1130
CARX, CARY = 540, 1430     # centro del coche (base de las ruedas en CARY)
HOST = dict(head=(255, 205, 160), torso=(30, 30, 40), legs=(30, 30, 40), hair=(240, 200, 60), logo=(255, 40, 200))
BUFF = dict(head=(210, 150, 110), torso=(220, 60, 60), legs=(40, 40, 50), hair=(20, 20, 20), logo=None)
OLD = dict(head=(255, 215, 180), torso=(150, 130, 110), legs=(90, 80, 70), hair=(235, 235, 235), logo=None)
CHOC = (110, 60, 30)

SCRIPT = [
    ("In this town, there's a TV show called Hands On.", "intro", None),
    ("One golden car. Keep one hand on it. The last person still touching it wins it.", "rules", None),
    ("Fifty people put their hands on the car. Including me.", "start", None),
    ("Hour two. A guy needed to scratch his nose. He used the wrong hand.", "nose", None),
    ("Hour ten. An ice cream truck drove by. Twelve people ran after it.", "icecream", None),
    ("Day two. Nobody had slept. People were sleeping standing up.", "sleep", None),
    ("One guy fell asleep... and slid off the car. Like butter.", "sleep_b", None),
    ("Then a pigeon landed on my head. I didn't move. It built a nest.", "pigeon", None),
    ("Then it laid three eggs. I was a dad now.", "pigeon_b", None),
    ("Day three. Only three of us left. Me, a bodybuilder... and a tiny old man.", "final3", None),
    ("The bodybuilder flexed so hard... his hand slipped off.", "flex", None),
    ("The old man had been sleeping since day one. Standing up. Holding the car.", "oldman_a", None),
    ("Then he fell asleep even harder... and woke up at home. Nobody knows how.", "oldman", None),
    ("I won! I was so happy, I screamed:", "win", "solo", 6),
    ("Then the host said: congratulations! The car is made of chocolate.", "choco", None),
    ("And it was a very, very sunny day.", "melt", None),
    ("Now my prize is a chocolate puddle... and a pigeon.", "end", None),
    ("But honestly? Best prize ever.", "end_b", "solo", 3),
]

DAY = {"sleep_b": "DAY 2", "pigeon_b": "DAY 2", "oldman_a": "DAY 3", "start": "HOUR 0", "nose": "HOUR 2", "icecream": "HOUR 10", "sleep": "DAY 2", "pigeon": "DAY 2",
       "final3": "DAY 3", "flex": "DAY 3", "oldman": "DAY 3", "win": "DAY 3"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.15, (.5, .55), (.5, .62)),
    "start": (1.2, 1.0, (.5, .65), (.5, .62)), "nose": (1.0, 1.5, (.5, .62), (.25, .6)),
    "icecream": (1.15, 1.0, (.6, .6), (.5, .6)), "sleep": (1.0, 1.25, (.5, .62), (.5, .6)),
    "pigeon": (1.0, 1.7, (.5, .62), (.3, .64)), "final3": (1.25, 1.0, (.5, .6), (.5, .62)),
    "flex": (1.0, 1.4, (.5, .62), (.3, .6)), "oldman": (1.0, 1.4, (.5, .62), (.75, .62)),
    "win": (1.2, 1.0, (.5, .55), (.5, .5)), "choco": (1.0, 1.3, (.5, .62), (.5, .66)),
    "melt": (1.0, 1.15, (.5, .6), (.5, .66)), "end": (1.15, 1.0, (.5, .66), (.5, .62)),
    "end_b": (1.0, 1.25, (.5, .6), (.45, .55)),
    "sleep_b": (1.3, 1.0, (.7, .62), (.5, .62)), "pigeon_b": (1.7, 2.0, (.3, .64), (.29, .62)),
    "oldman_a": (1.0, 1.7, (.5, .62), (.85, .62)),
}

# ------------------------------------------------------------------ piezas
def plaza(img, T, tint_col=None, night=False):
    d = town(img, T, tint="night" if night else None, ground_y=GND)
    if tint_col: tint(img, tint_col, 80); d = ImageDraw.Draw(img)
    d.rectangle([0, GND, W, H], fill=(150, 140, 130))
    for q in range(0, W + 200, 120): d.line([q, GND, q - 250, H], fill=(135, 125, 115), width=3)
    return d

def car(d, T, choc=0., melt=0., s=1.0):
    """Deportivo dorado (choc: 0 dorado -> 1 chocolate; melt: 0 entero -> 1 charco)."""
    col = tuple(int(GOLD[i] * (1 - choc) + CHOC[i] * choc) for i in range(3))
    dark = tuple(int(c * .7) for c in col)
    hgt = 1 - melt
    if melt > 0:  # charco
        pw = 380 + 260 * melt
        d.ellipse([CARX - pw, CARY - 40, CARX + pw, CARY + 70], fill=CHOC)
    if hgt <= .02: return
    bw = 370 * s
    by0 = CARY - 210 * hgt * s
    block(d, [CARX - bw, by0, CARX + bw, CARY - 40 * hgt], col)
    cab0 = CARY - 330 * hgt * s
    d.polygon([(CARX - bw * .55, by0), (CARX - bw * .3, cab0), (CARX + bw * .35, cab0), (CARX + bw * .6, by0)], fill=col, outline=dark)
    d.polygon([(CARX - bw * .45, by0 - 5), (CARX - bw * .25, cab0 + 20 * hgt), (CARX + bw * .3, cab0 + 20 * hgt), (CARX + bw * .5, by0 - 5)],
              fill=(170, 220, 255) if choc < .5 else (90, 50, 25))
    for wx in (-1, 1):
        r = 75 * hgt * s
        d.ellipse([CARX + wx * bw * .62 - r, CARY - 40 * hgt - r, CARX + wx * bw * .62 + r, CARY - 40 * hgt + r], fill=(30, 30, 30) if choc < .5 else (80, 45, 20))
    if choc < .5:  # brillo
        sx = CARX - bw + ((T * 400) % (2 * bw))
        d.line([sx, by0 + 10, sx + 60, CARY - 60 * hgt], fill=(255, 255, 230), width=14)
        for q in range(3):
            px, py = CARX - 250 + q * 250, by0 - 40 + 20 * math.sin(T * 4 + q)
            d.regular_polygon((px, py, 18 + 6 * math.sin(T * 8 + q)), 4, rotation=45, fill=(255, 255, 255))
    if melt > 0:  # gotas
        for q in range(8):
            gx = CARX - bw + q * bw / 3.5
            d.rounded_rectangle([gx, by0 + 20, gx + 24, by0 + 60 + 120 * melt + 20 * math.sin(T * 3 + q)], radius=12, fill=CHOC)

def people_at_car(d, T, n, seed=0, face="flat", skip=(), sleep=False):
    """Concursantes alrededor del coche, cada uno con una mano encima."""
    spots = []
    for i in range(n):
        side = -1 if i % 2 == 0 else 1
        row = i // 2
        x = CARX + side * (430 + (row % 3) * 70) if row < 3 else CARX - 330 + (i * 97) % 660
        y = CARY + 40 + (row % 3) * 25 if row < 3 else CARY - 260
        spots.append((x, y, side))
    for i, (x, y, side) in enumerate(spots):
        if i in skip: continue
        lean = 18 * math.sin(T * 1.5 + i) if sleep else 0
        avatar(d, x + lean, y, 34, npc(800 + i + seed), T + i, 0, "out", face, look=-side)

def host(d, x, y, s, t, arms="out", face="smile", look=0):
    top = avatar(d, x, y, s, HOST, t, 0, arms, face, look)
    mx = x + (s * 2.6 if look >= 0 else -s * 2.6)
    d.rectangle([mx - s * .12, y - s * 3.4, mx + s * .12, y - s * 2.6], fill=(40, 40, 40))
    d.ellipse([mx - s * .25, y - s * 3.75, mx + s * .25, y - s * 3.25], fill=(90, 90, 100))
    return top

def pigeon(d, x, y, s, t):
    bob = 4 * math.sin(t * 6)
    d.ellipse([x - s, y - s * .6 + bob, x + s, y + s * .4 + bob], fill=(140, 140, 155))
    d.ellipse([x + s * .5, y - s * 1.1 + bob, x + s * 1.2, y - s * .3 + bob], fill=(120, 120, 140))
    d.ellipse([x + s * .85, y - s * .85 + bob, x + s * .98, y - s * .7 + bob], fill=(255, 140, 0))
    d.polygon([(x + s * 1.15, y - s * .7 + bob), (x + s * 1.45, y - s * .6 + bob), (x + s * 1.15, y - s * .5 + bob)], fill=(250, 190, 60))
    d.polygon([(x - s, y - s * .2 + bob), (x - s * 1.6, y - s * .5 + bob), (x - s * 1.4, y + bob)], fill=(110, 110, 125))

def nest(d, x, y, s):
    d.ellipse([x - s * 1.6, y - s * .5, x + s * 1.6, y + s * .5], fill=(140, 100, 50))
    for q in range(-3, 4):
        d.line([x + q * s * .4 - s * .3, y - s * .4, x + q * s * .4 + s * .3, y + s * .3], fill=(100, 70, 30), width=4)

def me_at_car(d, T, face="flat", z=1.0, arms="out", nest_on=False, x=None):
    x = CARX - 230 if x is None else x
    top = avatar(d, x, CARY + 140, 60 * z, ME, T, 0, arms, face, look=1)
    if nest_on:
        nest(d, x, top - 10, 28 * z)
        pigeon(d, x - 10, top - 30, 26 * z, T)
    return top

def zzz(d, x, y, T):
    for q in range(3):
        zy = y - ((T * 100 + q * 50) % 160)
        d.text((x + q * 30, zy), "z", font=font(44 + q * 10), fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(40, 40, 80))

def ice_cream_truck(d, x, y, T):
    block(d, [x - 260, y - 300, x + 260, y - 40], (250, 250, 250))
    block(d, [x + 260, y - 220, x + 380, y - 40], (120, 200, 255))
    d.rectangle([x - 200, y - 260, x + 100, y - 160], fill=(255, 160, 200))
    d.text((x - 50, y - 210), "ICE CREAM", font=font(36), fill=(255, 255, 255), anchor="mm")
    for wx in (-160, 260):
        d.ellipse([x + wx - 50, y - 90, x + wx + 50, y + 10], fill=(30, 30, 30))
    cone_y = y - 380 + 10 * math.sin(T * 4)
    d.polygon([(x - 40, cone_y), (x + 40, cone_y), (x, cone_y + 110)], fill=(220, 170, 90))
    d.ellipse([x - 55, cone_y - 70, x + 55, cone_y + 20], fill=(255, 170, 200))
    for q in range(3):  # notas musicales
        nx, ny = x + 300 + q * 60, y - 380 - ((T * 120 + q * 40) % 160)
        d.ellipse([nx, ny, nx + 30, ny + 24], fill=(255, 255, 255)); d.rectangle([nx + 24, ny - 60, nx + 30, ny + 12], fill=(255, 255, 255))

def sun(d, x, y, r, T):
    for q in range(12):
        a = q * math.pi / 6 + T * .5
        d.line([x + r * 1.2 * math.cos(a), y + r * 1.2 * math.sin(a), x + r * 1.8 * math.cos(a), y + r * 1.8 * math.sin(a)], fill=(255, 200, 40), width=14)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 220, 60))

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    full = seg["scene"]; sc = {"sleep_b": "sleep", "pigeon_b": "pigeon", "oldman_a": "final3"}.get(full, full)
    dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]

    if sc == "intro":
        d = neon_city(img, T)
        p = ease(min(1, t / .5))
        screen(d, box, [("HANDS", int(170 * (.6 + .4 * p)), NEON), ("ON", int(170 * (.6 + .4 * p)), (255, 255, 255)),
                        ("DON'T LET GO", 50, GOLD)])
        host(d, 280, 1500, 46, T, "out", "smile", look=1)
        ovl.append(None)

    elif sc == "rules":
        d = plaza(img, T)
        car(d, T)
        third = min(2, int(u * 3))
        stk(["ONE GOLDEN CAR", "ONE HAND ON IT", "LAST ONE WINS IT"][third], W / 2, 400, 110, [GOLD, PINK, (90, 200, 90)][third],
            fg=(255, 255, 255), rot=-4 + 4 * third, scale=1 + .05 * math.sin(T * 10))
        if third >= 1:
            me_at_car(d, T, "smile")
        ovl.append(None)

    elif sc == "start":
        d = plaza(img, T)
        n = int(4 + 10 * ease(min(1, u / .6)))
        people_at_car(d, T, 14, skip=range(n, 14), face="smile")
        car(d, T)
        me_at_car(d, T, "laugh")
        stk("50 PEOPLE", W / 2, 400, 130, PINK, rot=-5)
        ovl.append(DAY[sc])

    elif sc == "nose":
        d = plaza(img, T)
        people_at_car(d, T, 12, skip=(0,), face="flat")
        car(d, T)
        me_at_car(d, T, "flat", x=CARX + 230)
        gx = CARX - 470
        scratched = u > .45
        top = avatar(d, gx, CARY + 140, 52, npc(900), T, 0, "up" if scratched else "out", "laugh" if scratched else "flat", look=1)
        if not scratched:
            stk("ITCHY...", gx + 60, 820, 80, (255, 255, 255), fg=(20, 20, 20), rot=-6, scale=1 + .1 * math.sin(T * 14))
        else:
            stk("WRONG HAND", gx + 120, 820, 90, RED, rot=5)
            tint(img, RED, 40 if int(T * 4) % 2 else 0)
        ovl.append(DAY[sc])

    elif sc == "icecream":
        d = plaza(img, T)
        tx = W + 300 - (W + 700) * u
        ice_cream_truck(d, tx, 1250, T)
        people_at_car(d, T, 12, skip=range(0, int(8 * ease(u))), face="smile")
        for i in range(int(8 * ease(u))):  # los que se van tras el camión
            x = CARX - 300 + i * 80 - 500 * ease(u) + 20 * math.sin(T * 9 + i)
            avatar(d, x, CARY + 220, 32, npc(800 + i), T * 2 + i, 1.5, "up", "laugh", look=-1)
        car(d, T)
        me_at_car(d, T, "shock")
        stk("-12", W / 2, 380, 150, RED, rot=-4)
        ovl.append(DAY[sc])

    elif sc == "sleep":
        d = plaza(img, T, night=True)
        people_at_car(d, T, 8, skip=range(0, 3), face="flat", sleep=True)
        car(d, T)
        me_at_car(d, T, "flat")
        for x in (CARX - 450, CARX + 470, CARX - 230):
            zzz(d, x + 40, 1100, T)
        if full == "sleep_b":
            sl = ease(min(1, u / .6))
            avatar(d, CARX + 470 + 60 * sl, CARY + 140 + 160 * sl, 40, npc(950), T * .3, 0, "out", "flat", look=-1)
            if u > .5: stk("LIKE BUTTER", W / 2, 400, 120, (250, 220, 120), fg=(255, 255, 255), rot=4)
        else:
            stk("NO SLEEP", W / 2, 400, 130, PURPLE, rot=-4)
        ovl.append(DAY[sc])

    elif sc == "pigeon":
        d = plaza(img, T)
        people_at_car(d, T, 6, skip=range(0, 2), face="flat")
        car(d, T)
        land = ease(min(1, u / .35))
        x0 = CARX - 230
        top = avatar(d, x0, CARY + 140, 60, ME, T, 0, "out", "flat", look=1)
        if full == "pigeon_b":
            nest(d, x0, top - 10, 28)
            for q in range(3):
                if u > .15 + q * .15:
                    d.ellipse([x0 - 40 + q * 30, top - 40, x0 - 18 + q * 30, top - 12], fill=(250, 250, 240), outline=(200, 200, 190))
            pigeon(d, x0 + 60, top - 40, 22, T)
            if u > .6: stk("DAD NOW", W / 2, 400, 140, (140, 140, 155), rot=-5, scale=1 + .05 * math.sin(T * 10))
            ovl.append(DAY[full]); land = 2
        if land <= 1 and u > .55: nest(d, x0, top - 10, 28)
        px, py = x0 - 10 + 500 * (1 - min(1, land)), top - 30 - 600 * (1 - min(1, land))
        if land <= 1: pigeon(d, px, py, 26, T)
        if full == "pigeon" and u > .6:
            stk("IT BUILT A NEST", W / 2, 400, 100, (140, 100, 50), rot=4, scale=1 + .05 * math.sin(T * 10))
        if full == "pigeon": ovl.append(DAY[sc])

    elif sc in ("final3", "flex", "oldman"):
        d = plaza(img, T)
        car(d, T)
        bx, ox = CARX - 430, CARX + 470
        # culturista
        if sc != "oldman" or True:
            if sc == "flex":
                flexing = u > .3
                slip = ease(max(0, (u - .55) / .3))
                avatar(d, bx - 150 * slip, CARY + 140, 70, BUFF, T, 0, "up" if flexing else "out", "yell" if flexing else "angry", look=1)
                if flexing: stk("FLEX", bx, 760, 120, RED, rot=-6, scale=1 + .1 * math.sin(T * 14))
                if slip > .5: stk("SLIPPED", W / 2, 400, 120, RED, rot=4)
            elif sc == "final3":
                avatar(d, bx, CARY + 140, 70, BUFF, T, 0, "out", "angry", look=1)
        # viejecito
        if sc == "oldman":
            gone = u > .55
            if not gone:
                top = avatar(d, ox, CARY + 140, 36, OLD, T * .3, 0, "out", "flat", look=-1)
                zzz(d, ox + 30, top - 30, T)
            else:
                d.ellipse([ox - 70, CARY + 120, ox + 70, CARY + 160], fill=(130, 125, 115))
                stk("HE WENT HOME?!", W / 2, 400, 100, (150, 130, 110), rot=-4)
                if u < .62: flash(img, 1 - (u - .55) / .07)
        elif sc != "flex" or True:
            if sc in ("final3", "flex"):
                avatar(d, ox, CARY + 140, 36, OLD, T, 0, "out", "smile", look=-1)
        me_at_car(d, T, "flat", nest_on=True)
        if full == "final3":
            stk("FINAL 3", W / 2, 400, 140, GOLD, fg=(255, 255, 255), rot=-4)
        elif full == "oldman_a":
            zzz(d, ox + 30, CARY - 60, T)
            if u > .4: stk("ASLEEP SINCE DAY 1", W / 2, 400, 85, (150, 130, 110), rot=4)
        ovl.append(DAY[full])

    elif sc == "win":
        sky(img, (255, 60, 200), (120, 30, 200)); d = ImageDraw.Draw(img)
        for q in range(16):
            a = q * math.pi / 8 + T * .7
            d.polygon([(W / 2, 1000), (W / 2 + 2300 * math.cos(a), 1000 + 2300 * math.sin(a)),
                       (W / 2 + 2300 * math.cos(a + .18), 1000 + 2300 * math.sin(a + .18))], fill=(255, 120, 230))
        rnd = random.Random(3)
        for i in range(80):
            x0 = rnd.uniform(0, W); y = (rnd.uniform(-H, 0) + T * rnd.uniform(300, 700)) % (H + 100) - 50
            d.rectangle([x0, y, x0 + 18, y + 30], fill=rnd.choice([PINK, GOLD, (60, 200, 255), (120, 255, 120)]))
        z = 1 + .15 * hit
        top = avatar(d, W / 2, 1650, 95 * z, ME, T, 0, "up", "yell" if hit > .2 else "laugh")
        nest(d, W / 2, top - 10, 40 * z); pigeon(d, W / 2 - 10, top - 40, 36 * z, T)
        if k < 0:
            stk("I WON!", W / 2, 380, 170, GOLD, fg=(255, 255, 255), rot=-5, scale=1 + .06 * math.sin(T * 10))
        elif k < seg["nh"]:
            for j in range(k + 1):
                stk("HUSS", 180 + (j * 191) % 720, 330 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                    rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
        amp = int(22 * hit)
        ovl.append(DAY[sc])

    elif sc in ("choco", "melt", "end", "end_b"):
        d = plaza(img, T, tint_col=(255, 200, 80) if sc == "melt" else None)
        if sc == "choco":
            c = ease(max(0, (u - .45) / .25))
            car(d, T, choc=c)
            host(d, CARX + 400, CARY + 140, 56, T, "out", "laugh", look=-1)
            me_at_car(d, T, "shock" if c > .5 else "laugh", nest_on=True)
            if c > .5:
                stk("100% CHOCOLATE", W / 2, 400, 110, CHOC, rot=-4, scale=1 + .05 * math.sin(T * 10))
                if u < .75: flash(img, .5 * (1 - (u - .6) / .15))
        elif sc == "melt":
            sun(d, 820, 330, 120, T)
            mlt = ease(u)
            car(d, T, choc=1, melt=mlt)
            me_at_car(d, T, "shock", nest_on=True, arms="up")
            for q in range(3):  # ondas de calor
                d.arc([100 + q * 300, 900 - 30 * math.sin(T * 4 + q), 260 + q * 300, 980], 200, 340, fill=(255, 240, 200), width=5)
            stk("VERY SUNNY", W / 2, 640, 110, (255, 200, 40), fg=(255, 255, 255), rot=4)
        else:
            car(d, T, choc=1, melt=1)
            if sc == "end":
                me_at_car(d, T, "flat", nest_on=True, x=CARX - 200)
                stk("MY PRIZE", W / 2, 400, 130, CHOC, rot=-4)
                if u > .5: stk("+ A PIGEON", W / 2, 600, 100, (140, 140, 155), rot=4)
            else:
                z = 1 + .12 * hit
                top = me_at_car(d, T, "yell" if hit > .2 else "laugh", z=z, nest_on=True, arms="up", x=CARX - 160)
                d.rectangle([CARX + 40, CARY - 120, CARX + 60, CARY + 20], fill=(200, 200, 210))  # cuchara
                d.ellipse([CARX + 20, CARY - 170, CARX + 80, CARY - 100], fill=(200, 200, 210))
                if k < 0:
                    stk("BEST PRIZE EVER", W / 2, 400, 110, GOLD, fg=(255, 255, 255), rot=-4, scale=1 + .05 * math.sin(T * 10))
                elif k < seg["nh"]:
                    stk("HUSS!", W / 2 + (k - 1) * 250, 450, 130, (40, 90, 210), rot=-8 + 8 * k, scale=1 + .4 * hit)
                amp = int(15 * hit)
        ovl.append(None)

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
def buzzer(dur=.5):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * 110 * t)) * .18 * np.minimum(1, (dur - t) / .1)).astype(np.float32)

def jingle(dur):
    notes = [784, 659, 784, 880, 784, 659, 587, 659]
    n = int(SR * dur); out = np.zeros(n, np.float32); step = .25
    for i in range(int(dur / step)):
        s = int(i * step * SR); f = notes[i % len(notes)]
        k = min(n - s, int(.22 * SR)); t = np.arange(k) / SR
        out[s:s + k] += (np.sin(2 * np.pi * f * t) * np.exp(-t * 8) * .12).astype(np.float32)
    return out

def coo():
    n = int(SR * .5); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (380 + 60 * np.sin(2 * np.pi * 6 * t)) * t) * np.exp(-t * 4) * .2).astype(np.float32)

def sizzle(dur):
    n = int(SR * dur); x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[f < 3000] = 0
    y = np.fft.irfft(X, n); y /= np.abs(y).max()
    return (y * .08 * np.minimum(1, np.arange(n) / SR / .3)).astype(np.float32)

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
    s = by["start"]; put(crowd_roar(s["dur"]) * .5, s["start"])
    s = by["nose"]; put(buzzer(), s["start"] + (s["dur"] + .2) * .47)
    s = by["icecream"]; put(jingle(s["dur"] + .2), s["start"]); put(buzzer(), s["start"] + s["dur"] * .7)
    s = by["pigeon"]; put(coo(), s["start"] + (s["dur"] + .2) * .35); put(coo(), s["start"] + (s["dur"] + .2) * .7)
    s = by["final3"]; put(m.sfx("boom") * .6, s["start"])
    s = by["flex"]; put(m.sfx("boing"), s["start"] + (s["dur"] + .2) * .6); put(buzzer(), s["start"] + (s["dur"] + .2) * .7)
    s = by["oldman"]; put(m.sfx("pop") * 1.2, s["start"] + (s["dur"] + .2) * .55)
    s = by["win"]; put(crowd_roar(1.5) * .7, s["start"]); put(m.sfx("ding"), s["start"])
    s = by["choco"]; put(m.sfx("ding") * .7, s["start"] + (s["dur"] + .2) * .55)
    s = by["melt"]; put(sizzle(s["dur"] + .2), s["start"])
    s = by["end"]; put(coo(), s["start"] + (s["dur"] + .2) * .6)
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
hn.SHOW = "HANDS ON"
hn.TICKER = "  LIVE · HANDS ON · LAST HAND ON THE CAR WINS IT · DON'T LET GO · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "hands_on.mp4"]
    m.main()
