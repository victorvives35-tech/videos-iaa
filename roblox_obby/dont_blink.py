#!/usr/bin/env python3
"""Historia 9: DON'T BLINK — concurso de TV (estilo THE HUNT / DON'T SAY HUSS / THE CIRCLE / HANDS ON).

Uso: python3 dont_blink.py --voice ruta/en_US-ryan-high.onnx [--out dont_blink.mp4]
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
HOST = dict(head=(255, 205, 160), torso=(30, 30, 40), legs=(30, 30, 40), hair=(240, 200, 60), logo=(255, 40, 200))
MOM = dict(head=(255, 205, 160), torso=(230, 90, 120), legs=(80, 60, 120), hair=(110, 60, 30), logo=None, long_hair=True)
FLOOR = 1450
STUDIO_TITLE = "DON'T BLINK"

SCRIPT = [
    ("In this town, there's a TV show called Don't Blink.", "intro", None),
    ("The last person to blink wins three million dollars.", "rules", None),
    ("One hundred people sat down. Including me.", "start", None),
    ("Minute one. A fly landed on a guy's eyeball. He blinked.", "fly", None),
    ("Then the fly landed on MY eyeball. I didn't blink. We became friends.", "fly_me", None),
    ("Minute ten. They turned on a giant fan.", "fan", None),
    ("A lady's wig flew away. She blinked... out of shame.", "fan_b", None),
    ("Hour one. Somebody's mom walked in and yelled: clean your room! Twenty people blinked.", "mom", None),
    ("Hour two. They started chopping onions. Forty people cried.", "onion", None),
    ("Hour three. My eyes were so dry... they looked like raisins.", "dry", None),
    ("I hadn't blinked in so long... I could hear colors.", "dry_b", None),
    ("Hour five. Only two players left. Me... and Bubbles.", "final2", None),
    ("Bubbles was a goldfish.", "fish", None),
    ("I made funny faces. I danced. I even screamed:", "huss", "solo", 6),
    ("I showed him a picture of a cat. Nothing.", "cat", None),
    ("Bubbles didn't blink.", "fish_b", None),
    ("Because fish don't have eyelids.", "fact", None),
    ("I blinked. Bubbles won three million dollars.", "lose", None),
    ("Now Bubbles lives in a mansion. With a pool shaped like a fish bowl.", "end", None),
    ("I asked for a rematch. Bubbles said nothing. Because he's a fish.", "end_b", None),
]

DAY = {"fly_me": "MINUTE 2", "fan_b": "MINUTE 10", "dry_b": "HOUR 4", "cat": "HOUR 5", "start": "MINUTE 0", "fly": "MINUTE 1", "fan": "MINUTE 10", "mom": "HOUR 1", "onion": "HOUR 2",
       "dry": "HOUR 3", "final2": "HOUR 5", "fish": "HOUR 5", "huss": "HOUR 5", "fish_b": "HOUR 5", "fact": "HOUR 5"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.15, (.5, .45), (.5, .4)),
    "start": (1.2, 1.0, (.5, .62), (.5, .58)), "fly": (1.0, 2.0, (.5, .6), (.28, .55)),
    "fan": (1.15, 1.0, (.6, .6), (.5, .58)), "mom": (1.0, 1.2, (.3, .6), (.5, .6)),
    "onion": (1.2, 1.0, (.5, .6), (.5, .58)), "dry": (1.0, 1.0, (.5, .5), (.5, .5)),
    "final2": (1.0, 1.15, (.5, .55), (.5, .58)), "fish": (1.0, 2.0, (.5, .6), (.72, .6)),
    "huss": (1.15, 1.0, (.5, .58), (.5, .58)), "fish_b": (1.8, 2.4, (.72, .6), (.72, .6)),
    "fact": (1.0, 1.1, (.5, .45), (.5, .45)), "lose": (1.0, 1.3, (.5, .58), (.32, .55)),
    "end": (1.2, 1.0, (.5, .5), (.5, .55)),
    "fly_me": (1.0, 1.15, (.5, .5), (.42, .5)), "fan_b": (1.0, 1.3, (.5, .58), (.3, .58)),
    "dry_b": (1.2, 1.0, (.5, .5), (.5, .5)), "cat": (1.0, 1.2, (.5, .58), (.55, .58)), "end_b": (1.0, 1.3, (.5, .55), (.6, .6)),
}

# ------------------------------------------------------------------ piezas
def studio(img, T):
    sky(img, (25, 15, 55), (90, 30, 110)); d = ImageDraw.Draw(img)
    for q in range(7):  # focos
        x = 80 + q * 160
        beam = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(beam)
        sw = 60 * math.sin(T * .8 + q)
        bd.polygon([(x - 20, 0), (x + 20, 0), (x + 160 + sw, FLOOR), (x - 160 + sw, FLOOR)], fill=(255, 120, 230, 22))
        img.alpha_composite(beam)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 230, W, 300], fill=(15, 10, 35)); d.text((W / 2, 265), STUDIO_TITLE, font=font(52), fill=NEON, anchor="mm")
    d.rectangle([0, FLOOR, W, H], fill=(50, 30, 70))
    for q in range(0, W, 90): d.rectangle([q, FLOOR, q + 45, FLOOR + 30], fill=PINK)
    return d

def chair(d, x, y, s):
    block(d, [x - s * 1.3, y - s * 2.4, x + s * 1.3, y - s * 1.9], (200, 40, 80))
    block(d, [x - s * 1.3, y - s * 4.6, x + s * 1.3, y - s * 2.4], (170, 30, 70))
    for e in (-1, 1): d.rectangle([x + e * s * 1.1 - 6, y - s * 1.9, x + e * s * 1.1 + 6, y], fill=(60, 60, 70))

def eyes_open(d, x, top, s, big=1.0, dry=0.):
    """Ojos muy abiertos (o pasas secas)."""
    hs = s * 1.25
    for e in (-1, 1):
        cx, cy = x + e * s * .3, top + hs * .42
        r = s * .26 * big
        if dry > .5:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 70, 40), outline=(70, 40, 20), width=3)
            for q in range(3):
                d.arc([cx - r * .7, cy - r * .7 + q * r * .4, cx + r * .7, cy - r * .2 + q * r * .4], 200, 340, fill=(80, 45, 20), width=3)
        else:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=(20, 20, 20), width=3)
            for q in range(3):  # venitas rojas
                a = q * 2.1
                d.line([cx + r * .9 * math.cos(a), cy + r * .9 * math.sin(a), cx + r * .4 * math.cos(a), cy + r * .4 * math.sin(a)], fill=(230, 60, 60), width=2)
            d.ellipse([cx - r * .4, cy - r * .4, cx + r * .4, cy + r * .4], fill=(20, 20, 20))

def blink_face(d, x, top, s):
    hs = s * 1.25
    for e in (-1, 1):
        cx, cy = x + e * s * .3, top + hs * .42
        d.line([cx - s * .22, cy, cx + s * .22, cy], fill=(20, 20, 20), width=max(3, int(s * .1)))

def player(d, x, y, s, c, T, face="flat", blinked=False, dry=0., arms="down", eyes=1.0):
    chair(d, x, y, s)
    top = avatar(d, x, y - s * .9, s, c, T, 0, arms, face, 0)
    hs = s * 1.25
    d.rectangle([x - hs / 2 + 3, top + hs * .2, x + hs / 2 - 3, top + hs * .62], fill=c["head"])  # tapa ojos base
    if blinked: blink_face(d, x, top, s)
    else: eyes_open(d, x, top, s, eyes, dry)
    return top

def rows_of_players(d, T, n_out=0, seed=0, face="flat", blink_ids=()):
    """Gradas con concursantes sentados; los n_out primeros ya no están (silla vacía con X)."""
    k = 0
    for r, (y, s, cnt) in enumerate([(1060, 20, 9), (1250, 26, 7)]):
        for j in range(cnt):
            x = 70 + j * (W - 140) / (cnt - 1)
            if k < n_out:
                chair(d, x, y, s)
                d.line([x - s, y - s * 4, x + s, y - s * 2], fill=RED, width=6); d.line([x + s, y - s * 4, x - s, y - s * 2], fill=RED, width=6)
            else:
                player(d, x, y, s, npc(1000 + k + seed), T, face, blinked=k in blink_ids)
            k += 1

def fishbowl(d, x, y, s, T, crown=False):
    d.ellipse([x - s * 2.2, y - s * 3.8, x + s * 2.2, y + s * .2], fill=(170, 220, 255), outline=(230, 245, 255), width=6)
    d.rectangle([x - s * 2.2, y - s * 3.8, x + s * 2.2, y - s * 3.0], fill=None)
    fx = x + s * .7 * math.sin(T * 1.5); fy = y - s * 1.8 + s * .2 * math.sin(T * 2)
    d.ellipse([fx - s * .9, fy - s * .55, fx + s * .9, fy + s * .55], fill=(255, 150, 30))
    d.polygon([(fx + s * .8, fy), (fx + s * 1.5, fy - s * .5), (fx + s * 1.5, fy + s * .5)], fill=(255, 120, 20))
    d.ellipse([fx - s * .6, fy - s * .3, fx - s * .2, fy + s * .1], fill=(255, 255, 255)); d.ellipse([fx - s * .5, fy - s * .2, fx - s * .3, fy], fill=(10, 10, 10))
    for q in range(3):
        by = fy - s * .5 - ((T * 60 + q * 40) % (s * 2))
        d.ellipse([fx - s * .9 - 8, by - 8, fx - s * .9 + 8, by + 8], outline=(255, 255, 255), width=3)
    if crown:
        cy = fy - s * .55
        d.polygon([(fx - s * .5, cy), (fx - s * .5, cy - s * .5), (fx - s * .25, cy - s * .25), (fx, cy - s * .6),
                   (fx + s * .25, cy - s * .25), (fx + s * .5, cy - s * .5), (fx + s * .5, cy)], fill=GOLD, outline=(0, 0, 0))
    return fx, fy

def fly(d, x, y, T):
    d.ellipse([x - 10, y - 7, x + 10, y + 7], fill=(20, 20, 20))
    w = 12 * abs(math.sin(T * 40))
    d.ellipse([x - 14, y - 6 - w, x - 2, y - 6], fill=(220, 230, 240)); d.ellipse([x + 2, y - 6 - w, x + 14, y - 6], fill=(220, 230, 240))

def big_fan(d, x, y, s, T):
    d.rectangle([x - 15, y, x + 15, y + s * 2.2], fill=(90, 90, 100))
    d.ellipse([x - s, y - s, x + s, y + s], fill=(60, 60, 70), outline=(200, 200, 210), width=8)
    for q in range(3):
        a = T * 20 + q * 2.09
        d.polygon([(x, y), (x + s * .9 * math.cos(a - .3), y + s * .9 * math.sin(a - .3)), (x + s * .9 * math.cos(a + .3), y + s * .9 * math.sin(a + .3))], fill=(180, 180, 190))

def wind(d, T):
    rnd = random.Random(int(T * 10))
    for q in range(25):
        x, y = rnd.uniform(0, W), rnd.uniform(700, 1500)
        d.line([x, y, x - 120, y], fill=(255, 255, 255), width=3)

def mansion(d, T):
    block(d, [140, 760, 940, 1300], (250, 245, 235))
    d.polygon([(100, 760), (540, 520), (980, 760)], fill=(60, 60, 90))
    for q in range(4):
        d.rectangle([200 + q * 180, 850, 280 + q * 180, 980], fill=(150, 210, 255), outline=(120, 120, 140), width=4)
        d.rectangle([200 + q * 180, 1050, 280 + q * 180, 1180], fill=(150, 210, 255), outline=(120, 120, 140), width=4)
    d.rectangle([480, 1150, 600, 1300], fill=(120, 80, 50))
    d.ellipse([260, 1340, 820, 1560], fill=(90, 190, 240), outline=(240, 240, 250), width=10)  # piscina pecera
    d.text((540, 1450), "BUBBLES", font=font(48), fill=(255, 255, 255), anchor="mm")

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    full = seg["scene"]
    sc = {"fly_me": "dry", "fan_b": "fan", "dry_b": "dry", "cat": "fish"}.get(full, full)
    dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]

    if sc in ("intro", "rules", "fact"):
        d = neon_city(img, T)
        if sc == "intro":
            p = ease(min(1, t / .5))
            screen(d, box, [("DON'T", 120, (255, 255, 255)), ("BLINK", int(200 * (.6 + .4 * p)), NEON), ("THE TV SHOW", 50, GOLD)])
            # ojo gigante que no parpadea
            ex, ey = W / 2, 1300
            d.ellipse([ex - 230, ey - 120, ex + 230, ey + 120], fill=(255, 255, 255), outline=(20, 20, 20), width=8)
            d.ellipse([ex - 90, ey - 90, ex + 90, ey + 90], fill=(60, 140, 220)); d.ellipse([ex - 45, ey - 45, ex + 45, ey + 45], fill=(10, 10, 10))
        elif sc == "rules":
            screen(d, box, [("LAST TO BLINK", 80, (255, 255, 255)), ("$3,000,000", 140, (90, 220, 90))])
            money_rain(d, T)
        else:
            screen(d, box, [("FUN FACT", 90, GOLD), ("FISH HAVE", 90, (255, 255, 255)), ("NO EYELIDS", 110, NEON)])
            fishbowl(d, W / 2, 1600, 60, T)
            if u > .5: stk("?!?!", W / 2, 1180, 150, RED, rot=6)
        ovl.append(DAY.get(sc))

    elif sc in ("start", "fly", "fan", "mom", "onion"):
        d = studio(img, T)
        if sc == "start":
            rows_of_players(d, T, face="smile")
            player(d, W / 2, 1650, 70, ME, T, "smile")
            stk("100 PLAYERS", W / 2, 400, 120, PINK, rot=-5)
        elif sc == "fly":
            rows_of_players(d, T)
            gx, gy = 300, 1650
            blinked = u > .55
            top = player(d, gx, gy, 70, npc(1100), T, "flat" if not blinked else "shock", blinked=blinked)
            land = ease(min(1, u / .45))
            fly(d, gx - 25 + 400 * (1 - land) + 20 * math.sin(T * 9) * (1 - land), top + 75 - 500 * (1 - land), T)
            player(d, 760, gy, 70, ME, T, "flat")
            if blinked: stk("BLINKED", gx, 1050, 110, RED, rot=-5); tint(img, RED, 40 if int(T * 4) % 2 else 0)
        elif sc == "fan":
            big_fan(d, 900, 650, 180, T)
            rows_of_players(d, T, n_out=3, blink_ids=(5, 8, 11))
            player(d, W / 2 - 100, 1650, 70, ME, T, "shock", eyes=1.2)
            wind(d, T)
            if full == "fan_b":
                lx = 200
                top = avatar(d, lx, 1650, 60, dict(head=(255, 205, 160), torso=(200, 90, 160), legs=(80, 60, 120), hair=None, logo=None),
                             T, 0, "up", "shock", look=1)
                wv = ease(u)
                wx, wy = lx + 900 * wv, top - 40 - 500 * wv
                d.ellipse([wx - 70, wy - 45, wx + 70, wy + 45], fill=(240, 200, 60), outline=(180, 140, 30), width=4)
                for q in range(5): d.arc([wx - 70 + q * 25, wy - 30, wx - 30 + q * 25, wy + 30], 0, 180, fill=(200, 160, 40), width=4)
                if u > .4: stk("HER WIG", W / 2, 400, 120, (240, 200, 60), fg=(255, 255, 255), rot=4)
                if u > .7: stk("BLINKED", lx, 1050, 100, RED, rot=-5)
            else:
                stk("GIANT FAN", W / 2, 400, 120, (60, 160, 255), rot=4)
            amp = 3
        elif sc == "mom":
            rows_of_players(d, T, n_out=6, blink_ids=tuple(range(6, 14)) if u > .7 else ())
            mx = 160 + 100 * ease(min(1, u / .3))
            avatar(d, mx, 1650, 70, MOM, T, 0, "out", "yell", look=1)
            player(d, 760, 1650, 70, ME, T, "flat")
            if u > .35: stk("CLEAN YOUR ROOM!", W / 2, 400, 100, (230, 90, 120), rot=-5, scale=1 + .08 * math.sin(T * 12))
            if u > .7: stk("-20", W / 2, 620, 130, RED, rot=4)
        else:
            rows_of_players(d, T, n_out=9, face="shock")
            # cocinero con cebollas
            cx = 260
            avatar(d, cx, 1650, 64, dict(head=(255, 205, 160), torso=(250, 250, 250), legs=(60, 60, 70), hair=None, logo=None), T, 0, "out", "smile", look=1)
            block(d, [cx + 80, 1440, cx + 330, 1480], (160, 110, 60))
            for q in range(3):
                d.ellipse([cx + 110 + q * 70, 1385, cx + 170 + q * 70, 1445], fill=(220, 190, 230), outline=(150, 110, 160), width=3)
            top = player(d, 790, 1650, 70, ME, T, "flat", eyes=1.1)
            for e in (-1, 1):  # lágrimas
                ty = top + 120 + (T * 300) % 120
                d.ellipse([790 + e * 21 - 8, ty, 790 + e * 21 + 8, ty + 20], fill=(90, 170, 255))
            stk("ONIONS", W / 2, 400, 130, (180, 140, 200), rot=-4)
            if u > .6: stk("-40", W / 2, 620, 130, RED, rot=5)
        ovl.append(DAY[sc])

    elif sc == "dry":
        sky(img, (40, 20, 30), (90, 40, 50)); d = ImageDraw.Draw(img)
        # primer plano extremo de sus ojos
        s = 340
        top = avatar(d, W / 2, 1900 + 600, s, ME, T, 0, "down", "flat", 0)
        hs = s * 1.25
        d.rectangle([W / 2 - hs / 2 + 3, top + hs * .2, W / 2 + hs / 2 - 3, top + hs * .62], fill=ME["head"])
        if full == "fly_me":
            eyes_open(d, W / 2, top, s, 1.0)
            land = ease(min(1, u / .4))
            fx, fy = W / 2 - s * .3 - 45 + 500 * (1 - land), top + hs * .42 - 55 - 300 * (1 - land)
            w = 70 * abs(math.sin(T * 40))
            d.ellipse([fx - 80, fy - 40 - w, fx - 10, fy - 30], fill=(230, 240, 255), outline=(120, 140, 160), width=3)
            d.ellipse([fx + 10, fy - 40 - w, fx + 80, fy - 30], fill=(230, 240, 255), outline=(120, 140, 160), width=3)
            d.ellipse([fx - 55, fy - 38, fx + 55, fy + 38], fill=(40, 110, 60), outline=(255, 255, 255), width=5)
            for e in (-1, 1): d.ellipse([fx + e * 30 - 16, fy - 30, fx + e * 30 + 16, fy + 2], fill=(200, 20, 20))
            if u > .6: stk("BEST FRIENDS", W / 2, 360, 120, (90, 200, 90), rot=-4)
        elif full == "dry_b":
            eyes_open(d, W / 2, top, s, 1.0, dry=1.0)
            rnd = random.Random(int(T * 6))
            for q in range(14):  # colores que "suenan"
                cx_, cy_ = rnd.uniform(100, W - 100), rnd.uniform(300, 900)
                col = rnd.choice([PINK, GOLD, (60, 200, 255), (120, 255, 120), (200, 90, 255)])
                d.text((cx_, cy_), "♪", font=font(80), fill=col, anchor="mm") if False else d.ellipse([cx_ - 30, cy_ - 30, cx_ + 30, cy_ + 30], fill=col)
            stk("I CAN HEAR COLORS", W / 2, 360, 95, (200, 90, 255), rot=4, scale=1 + .05 * math.sin(T * 10))
        else:
            eyes_open(d, W / 2, top, s, 1.0, dry=1.0 if u > .45 else 0)
            stk("RAISINS", W / 2, 360, 150, (120, 70, 40), rot=-5) if u > .45 else stk("SO DRY...", W / 2, 360, 120, (200, 120, 60), rot=4)
        ovl.append(DAY[full])

    elif sc in ("final2", "fish", "huss", "fish_b", "lose"):
        d = studio(img, T)
        chair(d, 780, 1640, 60)
        fishbowl(d, 780, 1460, 55, T, crown=sc == "lose")
        if sc == "huss":
            z = 1 + .15 * hit
            arms = "dance" if k < 0 else ("out" if hit > .1 else "up")
            top = player(d, 300, 1650, 72 * z, ME, T, "yell" if hit > .2 else "laugh", arms=arms)
            if 0 <= k < seg["nh"]:
                for j in range(k + 1):
                    stk("HUSS", 180 + (j * 191) % 720, 360 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                        rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
            else:
                stk("FUNNY FACES", W / 2, 400, 110, GOLD, fg=(255, 255, 255), rot=-4)
            amp = int(20 * hit)
        elif sc == "lose":
            blinked = u > .25
            player(d, 300, 1650, 72, ME, T, "shock" if blinked else "flat", blinked=blinked and u < .45)
            if blinked:
                stk("BLINKED", 300, 1050, 110, RED, rot=-5)
                stk("BUBBLES WINS", W / 2, 400, 110, GOLD, fg=(255, 255, 255), rot=4)
                money_rain(d, T, 20)
        else:
            player(d, 300, 1650, 72, ME, T, "flat", dry=1.0 if sc != "final2" else 0)
            if sc == "final2":
                stk("FINAL 2", W / 2, 400, 140, GOLD, fg=(255, 255, 255), rot=-4)
                stk("ME", 300, 1040, 90, (40, 90, 210), rot=-4)
                stk("BUBBLES", 780, 1040, 90, (255, 150, 30), rot=4)
            elif full == "cat":
                block(d, [330, 1150, 560, 1350], (255, 255, 255))  # foto de gato
                cx_, cy_ = 445, 1260
                d.ellipse([cx_ - 60, cy_ - 50, cx_ + 60, cy_ + 60], fill=(240, 160, 60))
                for e in (-1, 1): d.polygon([(cx_ + e * 55, cy_ - 30), (cx_ + e * 30, cy_ - 80), (cx_ + e * 10, cy_ - 40)], fill=(240, 160, 60))
                for e in (-1, 1): d.ellipse([cx_ + e * 25 - 8, cy_ - 5, cx_ + e * 25 + 8, cy_ + 11], fill=(20, 20, 20))
                stk("CAT PICTURE", W / 2, 400, 110, (240, 160, 60), rot=-4)
                if u > .6: stk("NOTHING", 780, 1100, 100, (60, 160, 255), rot=5)
            elif sc == "fish":
                if u > .35: stk("A GOLDFISH", W / 2, 400, 130, (255, 150, 30), rot=-5, scale=1 + .05 * math.sin(T * 10))
            else:
                stk("NO BLINK", W / 2, 400, 130, (60, 160, 255), rot=4)
        ovl.append(DAY.get(sc, "HOUR 5"))

    elif sc in ("end", "end_b"):
        sky(img, (120, 200, 255), (255, 240, 200)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1300, W, H], fill=(120, 190, 90))
        mansion(d, T)
        money_rain(d, T, 15)
        if sc == "end":
            fx, fy = fishbowl(d, 540, 1700, 50, T, crown=True)
            stk("MANSION", W / 2, 400, 130, GOLD, fg=(255, 255, 255), rot=-4)
        else:
            fishbowl(d, 760, 1650, 50, T, crown=True)
            avatar(d, 280, 1800, 62, ME, T, 0, "out", "angry", look=1)
            stk("REMATCH?", 300, 1000, 110, (40, 90, 210), rot=-5)
            if u > .55: stk("...", 760, 1350, 140, (255, 150, 30), rot=0)
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

def bzz(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * (190 + 30 * np.sin(2 * np.pi * 5 * t)) * t)) * .05).astype(np.float32)

def whoosh_long(dur):
    n = int(SR * dur); x = np.random.randn(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 200) | (f > 1500)] = 0
    y = np.fft.irfft(X, n); y /= np.abs(y).max()
    t = np.arange(n) / SR
    return (y * .15 * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .3)).astype(np.float32)

def blub():
    n = int(SR * .2); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (300 + 900 * t) * t) * np.exp(-t * 18) * .3).astype(np.float32)

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
    s = by["rules"]; put(m.sfx("ding"), s["start"] + .2)
    s = by["start"]; put(crowd_roar(s["dur"]) * .4, s["start"])
    s = by["fly"]; put(bzz((s["dur"] + .2) * .5), s["start"]); put(buzzer(), s["start"] + (s["dur"] + .2) * .55)
    s = by["fan"]; put(whoosh_long(s["dur"] + .2), s["start"])
    s = by["mom"]; put(buzzer(.8), s["start"] + (s["dur"] + .2) * .7)
    s = by["onion"]; put(buzzer(.8), s["start"] + (s["dur"] + .2) * .6)
    s = by["dry"]; put(m.sfx("pop"), s["start"] + (s["dur"] + .2) * .45)
    s = by["final2"]; put(m.sfx("boom") * .6, s["start"])
    s = by["fish"]
    for q in range(3): put(blub(), s["start"] + .3 + q * .4)
    s = by["fish_b"]; put(blub(), s["start"] + .2)
    s = by["fact"]; put(m.sfx("ding"), s["start"] + .1)
    s = by["lose"]; put(buzzer(.8), s["start"] + (s["dur"] + .2) * .25); put(crowd_roar(1.2) * .6, s["start"] + (s["dur"] + .2) * .3)
    s = by["end_b"]; put(blub(), s["start"] + (s["dur"] + .2) * .6)
    voice = np.zeros(n, np.float32)
    for s in segs:
        st_ = int(s["start"] * SR); e = min(n, st_ + len(s["audio"])); voice[st_:e] += np.abs(s["audio"][:e - st_])
    talk = np.convolve(np.clip(np.convolve(voice, np.ones(2205) / 2205, "same") * 25, 0, 1), np.ones(4410) / 4410, "same")
    a += fx * (1 - .55 * talk)
    a /= max(1, np.abs(a).max() / .95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

def setup():
    hn.SHOW = "DON'T BLINK"
    hn.TICKER = "  LIVE · DON'T BLINK · LAST ONE TO BLINK WINS · $3,000,000 · EYES OPEN · "
    m.SCRIPT = SCRIPT
    m.render_scene = scene
    m.mix_audio = mix_audio
    m.build = hn.build
    m.draw_captions = captions_single

ORIG_RENDER = hn.ORIG_RENDER
setup()

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "dont_blink.mp4"]
    m.main()
