#!/usr/bin/env python3
"""Historia 3: EVERYONE BECAME A BABY (60 s exactos).

Uso: python3 babies.py --voice ruta/en_US-ryan-high.onnx [--out babies.mp4]
Reutiliza el motor de in_this_town.py (HUSS real, música de fondo, narrador, subtítulos).
"""
import math, os, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)

TARGET = 60.0
GY = 1450

SCRIPT = [
    # ESCENA 1 (0-5 s): pueblo normal + destello
    ("In this town, it was a normal Monday morning. Then, a giant flash hit the whole town!", "morning", None),
    # ESCENA 2 (5-15 s): todos bebés
    ("And everyone turned into a BABY!", "babies", None),
    ("Babies everywhere! Crying, running, eating sand!", "babies_b", None),
    ("The baker. The mailman. Even grandma!", "babies2", None),
    ("Grandma was finally younger than me.", "babies3", None),
    # ESCENA 3 (15-25 s): Huss Boy es el único
    ("Everyone... except me.", "shock", None),
    ("I checked my hands. Still big. I checked my face. Still handsome.", "shock_b", None),
    ("I was the last grown-up in the whole town.", "shock_c", None),
    # ESCENA 4 (25-40 s): el alcalde bebé y el caos
    ("Then the baby mayor took control. His first law? Nap time is illegal!", "mayor", None),
    ("His second law? Free candy for everyone, forever!", "mayor_b", None),
    ("Babies were driving tiny cars! Babies were robbing the candy store!", "chaos", None),
    ("The police? Also babies. They arrested me for being too tall.", "police", None),
    ("So I tried to stop them. I said:", "huss_try", "solo", 3),
    ("And they all said it back!", "baby_huss", "babies", 6),
    ("Worst. Plan. Ever.", "baby_huss_b", None),
    # ESCENA 5 (40-52 s): laboratorio
    ("Plan B. I found a secret laboratory.", "lab", None),
    ("Inside, there was a giant red button that said: do not press.", "lab_b", None),
    ("So obviously... I pressed it.", "press", None),
    # ESCENA 6 (52-60 s): giro final
    ("Everything went back to normal!", "normal", None),
    ("The mayor was a grown-up again. Grandma was old again.", "normal_b", None),
    ("Everyone... except me.", "twist", "baby", 3),
    ("Now the whole town has to babysit me. Worth it.", "twist_b", None),
]

SKIN = (255, 210, 170)
CLOTHES = [(255, 140, 180), (120, 200, 255), (255, 220, 90), (150, 230, 150), (200, 160, 255), (255, 170, 90)]

# ------------------------------------------------------------------ bebé
def baby(d, x, y, s, t, face="cry", hat=None, walk=0., look=0, clothes=None, pacifier=False, arms="up", seed=0):
    """Bebé de bloques: cabeza enorme, cuerpo pequeño, pañal. (x,y)=pies."""
    clothes = clothes or CLOTHES[seed % len(CLOTHES)]
    sw = math.sin(t * 16 + seed) * walk
    # piernas
    for side, ph in ((-1, sw), (1, -sw)):
        lx = x + side * s * .45 + ph * s * .3
        block(d, [lx - s*.3, y - s*.6, lx + s*.3, y], SKIN)
    # pañal + cuerpo
    block(d, [x - s*.85, y - s*1.15, x + s*.85, y - s*.5], (250, 250, 250))
    block(d, [x - s*.8, y - s*2.2, x + s*.8, y - s*1.1], clothes)
    if hat == "huss":
        d.text((x, y - s*1.65), "HUSS", font=font(max(8, int(s * .5))), fill=(255, 205, 40), anchor="mm",
               stroke_width=max(1, int(s * .04)), stroke_fill=(20, 30, 90))
    # brazos (agitándose)
    wave_ = math.sin(t * 12 + seed) * s * .3
    for side in (-1, 1):
        ax = x + side * s * 1.05
        if arms == "up":
            block(d, [ax - s*.25, y - s*3.0 + side * wave_, ax + s*.25, y - s*2.0], SKIN)
        else:
            block(d, [ax - s*.25, y - s*2.2, ax + s*.25, y - s*1.3 + side * wave_ * .5], SKIN)
    # cabeza grande
    hs = s * 2.3
    hx, hy = x, y - s*2.2 - hs
    block(d, [hx - hs/2, hy, hx + hs/2, hy + hs], SKIN)
    # rizo
    d.arc([hx - s*.25, hy - s*.45, hx + s*.25, hy + s*.05], 180, 450, fill=(120, 70, 30), width=max(3, int(s * .1)))
    ex = s * .25 * look
    ey = hy + hs * .42
    if face == "cry":
        for e in (-1, 1):
            cx = hx + e * hs * .22 + ex
            d.arc([cx - s*.25, ey - s*.2, cx + s*.25, ey + s*.2], 200, 340, fill=(20, 20, 20), width=max(3, int(s*.1)))
            # lágrimas a chorro
            for k in range(3):
                ty = ey + ((t * 300 + k * 40 + seed * 7) % (s * 3))
                d.ellipse([cx - s*.1 + e*s*.15, ty, cx + s*.1 + e*s*.15, ty + s*.22], fill=(90, 170, 255))
        d.ellipse([hx - s*.45 + ex, hy + hs*.6, hx + s*.45 + ex, hy + hs*.92], fill=(130, 20, 30), outline=(20, 20, 20), width=3)
    else:
        for e in (-1, 1):
            cx = hx + e * hs * .22 + ex
            r = s * (.28 if face in ("shock", "smile", "yell") else .22)
            d.ellipse([cx - r, ey - r, cx + r, ey + r], fill=(255, 255, 255), outline=(20, 20, 20), width=3)
            d.ellipse([cx - r*.55 + ex*.3, ey - r*.55, cx + r*.55 + ex*.3, ey + r*.55], fill=(30, 30, 30))
            d.ellipse([cx - r*.2, ey - r*.4, cx + r*.05, ey - r*.15], fill=(255, 255, 255))
        if face == "laugh":
            d.chord([hx - s*.5 + ex, hy + hs*.58, hx + s*.5 + ex, hy + hs*.9], 0, 180, fill=(130, 20, 30), outline=(20, 20, 20))
        elif face in ("shock", "yell"):
            d.ellipse([hx - s*.3 + ex, hy + hs*.6, hx + s*.3 + ex, hy + hs*.92], fill=(130, 20, 30), outline=(20, 20, 20), width=3)
        elif face == "evil":
            d.arc([hx - s*.45 + ex, hy + hs*.55, hx + s*.45 + ex, hy + hs*.85], 10, 170, fill=(20, 20, 20), width=max(3, int(s*.1)))
            for e in (-1, 1):
                d.line([hx + e*hs*.38 + ex, hy + hs*.24, hx + e*hs*.1 + ex, hy + hs*.32], fill=(20, 20, 20), width=max(3, int(s*.12)))
        else:
            d.arc([hx - s*.4 + ex, hy + hs*.55, hx + s*.4 + ex, hy + hs*.85], 10, 170, fill=(20, 20, 20), width=max(3, int(s*.1)))
        # mofletes
        for e in (-1, 1):
            d.ellipse([hx + e*hs*.36 - s*.18, hy + hs*.6, hx + e*hs*.36 + s*.18, hy + hs*.72], fill=(255, 160, 160))
    if pacifier:
        py = hy + hs * .76
        d.ellipse([hx - s*.35 + ex, py - s*.18, hx + s*.35 + ex, py + s*.18], fill=(80, 180, 255), outline=(20, 20, 20), width=2)
        d.ellipse([hx - s*.12 + ex, py - s*.12, hx + s*.12 + ex, py + s*.12], fill=(255, 255, 255))
    # sombreros / accesorios
    if hat == "chef":
        d.rectangle([hx - hs*.4, hy - s*.4, hx + hs*.4, hy + s*.05], fill=(255, 255, 255), outline=(40, 40, 40), width=3)
        d.ellipse([hx - hs*.5, hy - s*1.3, hx + hs*.5, hy - s*.25], fill=(255, 255, 255), outline=(40, 40, 40), width=3)
    elif hat == "mail":
        d.rectangle([hx - hs/2 - 4, hy - s*.3, hx + hs/2 + 4, hy + s*.25], fill=(40, 60, 130))
        d.rectangle([hx, hy + s*.12, hx + hs*.75, hy + s*.3], fill=(40, 60, 130))
    elif hat == "granny":
        d.ellipse([hx - s*.6, hy - s*.9, hx + s*.6, hy + s*.1], fill=(200, 200, 205), outline=(120, 120, 125), width=3)
        for e in (-1, 1):
            cx = hx + e * hs * .22 + ex
            d.ellipse([cx - s*.33, ey - s*.33, cx + s*.33, ey + s*.33], outline=(20, 20, 20), width=max(3, int(s*.08)))
    elif hat == "tophat":
        d.rectangle([hx - hs*.45, hy - s*.15, hx + hs*.45, hy + s*.05], fill=(20, 20, 20))
        d.rectangle([hx - hs*.3, hy - s*1.3, hx + hs*.3, hy - s*.1], fill=(20, 20, 20))
        d.rectangle([hx - hs*.3, hy - s*.5, hx + hs*.3, hy - s*.32], fill=(200, 30, 30))
    elif hat == "police":
        d.rectangle([hx - hs/2 - 4, hy - s*.5, hx + hs/2 + 4, hy + s*.2], fill=(30, 40, 90))
        d.rectangle([hx - hs/2 - 10, hy + s*.1, hx + hs/2 + 10, hy + s*.3], fill=(20, 20, 30))
        d.regular_polygon((hx, hy - s*.15, s*.22), 6, fill=(255, 210, 40))
    elif hat == "huss":
        d.rectangle([hx - hs/2 - 4, hy - s*.4, hx + hs/2 + 4, hy + s*.3], fill=(30, 70, 190), outline=(20, 20, 30), width=3)
        d.rectangle([hx, hy + s*.18, hx + hs*.7, hy + s*.36], fill=(30, 70, 190))
        d.text((hx, hy - s*.05), "H", font=font(max(8, int(s * .55))), fill=(255, 205, 40), anchor="mm")
    return hy

def flash(img, a):
    if a > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * min(1, a)))))

def tiny_car(d, x, y, s, col, t, driver_seed):
    block(d, [x - s*1.6, y - s*.9, x + s*1.6, y - s*.1], col)
    for wx in (-1, 1):
        d.ellipse([x + wx*s - s*.4, y - s*.45, x + wx*s + s*.4, y + s*.35], fill=(30, 30, 30))
    baby(d, x - s*.2, y - s*.6, s * .35, t, "laugh", seed=driver_seed, arms="up")

# ------------------------------------------------------------------ cámara (movimiento cinematográfico)
CAMS = {  # escena: (zoom inicial, zoom final, (x0,y0)->(x1,y1) centro normalizado)
    "morning": (1.25, 1.0, (.5, .62), (.5, .5)), "babies": (1.0, 1.22, (.5, .5), (.5, .62)),
    "babies2": (1.2, 1.05, (.3, .6), (.7, .55)), "shock": (1.0, 1.45, (.5, .5), (.5, .58)),
    "mayor": (1.3, 1.0, (.5, .45), (.5, .5)), "chaos": (1.1, 1.1, (.35, .6), (.65, .6)),
    "police": (1.0, 1.3, (.5, .55), (.45, .6)), "huss_try": (1.0, 1.15, (.5, .55), (.5, .55)),
    "baby_huss": (1.15, 1.0, (.5, .6), (.5, .5)), "lab": (1.0, 1.25, (.5, .5), (.6, .55)),
    "press": (1.0, 1.6, (.5, .55), (.5, .45)), "normal": (1.2, 1.0, (.5, .55), (.5, .5)),
    "twist": (1.0, 1.4, (.5, .5), (.5, .62)),
    "babies_b": (1.3, 1.05, (.25, .65), (.75, .6)), "babies3": (1.0, 1.35, (.5, .5), (.5, .6)),
    "shock_b": (1.5, 1.3, (.45, .55), (.55, .52)), "shock_c": (1.35, .999, (.5, .58), (.5, .5)),
    "lab_b": (1.25, 1.5, (.5, .6), (.5, .55)),
    "mayor_b": (1.0, 1.35, (.5, .5), (.5, .42)), "baby_huss_b": (1.4, 1.1, (.5, .62), (.5, .55)),
    "normal_b": (1.0, 1.25, (.4, .55), (.6, .6)), "twist_b": (1.4, 1.1, (.5, .62), (.5, .55)),
}

def camera(img, sc, u):
    if sc not in CAMS: return img
    z0, z1, (x0, y0), (x1, y1) = CAMS[sc]
    k = ease(u)
    z = z0 + (z1 - z0) * k
    cx, cy = (x0 + (x1 - x0) * k) * W, (y0 + (y1 - y0) * k) * H
    cw, ch = W / z, H / z
    l = min(max(0, cx - cw/2), W - cw); tp = min(max(0, cy - ch/2), H - ch)
    return img.crop((int(l), int(tp), int(l + cw), int(tp + ch))).resize((W, H), Image.BILINEAR)

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    full = seg["scene"]
    sc = {"babies_b": "babies", "babies3": "babies2", "shock_b": "shock", "shock_c": "shock", "lab_b": "lab",
          "mayor_b": "mayor", "baby_huss_b": "baby_huss", "normal_b": "normal", "twist_b": "twist"}.get(full, full)
    dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []
    def stk(*a, **k): later.append((a, k))  # carteles: se dibujan después de la cámara para que no se recorten
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    me = CHARS["me"]

    if sc == "morning":
        d = town(img, T, cam=t * 80)
        d.ellipse([820, 160, 980, 320], fill=(255, 230, 90))
        for i in range(6):
            x = (100 + i * 190 + t * (60 if i % 2 else -50)) % (W + 100) - 50
            avatar(d, x, GY, 36, npc(i + 200), T + i, .8, "down", "smile", look=1 if i % 2 else -1)
        avatar(d, W/2, GY + 10, 44, me, T, .8, "down", "smile")
        if t < 2.0:  # gancho: título que golpea
            p = min(1, t / .25)
            stk("EVERYONE", W/2, 520, 150, (255, 60, 120), rot=-6, scale=.5 + .5 * p + .06 * math.sin(T * 14))
            stk("BECAME A BABY", W/2, 720, 120, (30, 30, 30), fg=(255, 230, 40), rot=4, scale=.5 + .5 * p)
            baby(ImageDraw.Draw(img), W/2, 1250 + 20 * math.sin(T * 10), 70, T, "cry", seed=3)
            amp = int(10 * max(0, 1 - t / 1.5))
        fl = max(0, (u - .7) / .3)
        if fl > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            r = 200 + 2200 * fl
            ld.ellipse([W/2 - r, 500 - r, W/2 + r, 500 + r], fill=(255, 250, 200, int(230 * fl)))
            img.alpha_composite(lay)
            amp = int(25 * fl)

    elif sc in ("babies", "babies2"):
        d = town(img, T)
        rnd = random.Random(5)
        if sc == "babies":
            for i in range(9):
                bx = (rnd.uniform(0, W) + math.sin(T * (1.5 + i * .2) + i) * 200) % W
                by = GY - abs(math.sin(T * 6 + i)) * 60
                baby(d, bx, by, 44 + (i % 3) * 8, T, ["cry", "laugh", "shock", "cry"][i % 4], walk=1, seed=i, look=math.sin(T + i))
            if full == "babies": flash(img, max(0, 1 - t / .25))
            for j in range(3):
                if t > .3 + j * .4:
                    stk("WAAAH", 200 + j * 330, 500 + (j % 2) * 160, 90, (90, 170, 255), rot=-8 + 8 * j,
                            scale=1 + .1 * math.sin(T * 12 + j))
        else:
            third = 2 if full == "babies3" else min(2, int(u * 3))
            hat = ["chef", "mail", "granny"][third]
            label = ["BABY BAKER", "BABY MAILMAN", "BABY GRANDMA"][third]
            bx = W/2 + 60 * math.sin(T * 3)
            baby(d, bx, GY - abs(math.sin(T * 7)) * 40, 85, T, ["laugh", "cry", "evil"][third], hat=hat, seed=third + 10, walk=.6)
            if third == 0:
                for q in range(4):  # pan lanzado
                    px = bx + 200 * math.cos(T * 3 + q * 1.6); py = 900 + 150 * math.sin(T * 4 + q)
                    d.ellipse([px - 45, py - 22, px + 45, py + 22], fill=(200, 130, 60), outline=(90, 50, 20), width=3)
            if third == 1:
                for q in range(6):  # cartas volando
                    px = (q * 190 + T * 300) % W; py = 800 + 120 * math.sin(T * 5 + q)
                    d.rectangle([px, py, px + 70, py + 45], fill=(255, 255, 255), outline=(40, 40, 40), width=3)
            if third == 2:  # andador
                d.rectangle([bx - 140, GY - 160, bx + 140, GY - 140], fill=(160, 160, 170))
                for e in (-1, 1): d.line([bx + e * 130, GY - 150, bx + e * 130, GY], fill=(160, 160, 170), width=10)
            stk(label, W/2, 420, 110, (255, 140, 180), rot=-4 + 4 * third)
            if full == "babies3":
                avatar(d, 200, GY, 52, me, T, 0, "down", "flat", look=1)
                if u > .45: stk("YOUNGER THAN ME", W/2, 600, 80, (170, 90, 160), rot=4)
            else:
                flash(img, max(0, 1 - ((u * 3) % 1) * dur / 3 / .12) * .7)

    elif sc == "shock":
        d = town(img, T)
        for i, bx in enumerate([110, 280, 800, 970]):
            baby(d, bx + 20 * math.sin(T * 4 + i), GY - abs(math.sin(T * 6 + i)) * 30, 30, T, "laugh", seed=i + 20, look=1 if bx < W/2 else -1)
        z = 1 + .3 * ease(u)
        if full == "shock_b":
            look_hands = u < .5
            avatar(d, W/2, GY + 20, 70, me, T, 0, "out" if look_hands else "down", "shock" if look_hands else "smile",
                   look=-1 if look_hands else 0)
            stk("STILL BIG" if look_hands else "STILL HANDSOME", W/2, 380, 100,
                    (40, 200, 90) if look_hands else (255, 140, 180), rot=-5 if look_hands else 5)
            if not look_hands:  # destello de guapo
                d.regular_polygon((W/2 + 120, 870, 30 + 10 * math.sin(T * 15)), 4, rotation=45, fill=(255, 255, 255))
        elif full == "shock_c":
            avatar(d, W/2, GY + 20, 66, me, T, 0, "up", "yell")
            stk("LAST GROWN-UP", W/2, 380, 100, (220, 30, 30), rot=-4, scale=1 + .05 * math.sin(T * 10))
            amp = 5
        else:
            avatar(d, W/2, GY + 20, 62 * z, me, T, 0, "up" if u > .5 else "down", "shock")
            if u > .5:
                stk("ONLY ONE LEFT", W/2, 380, 100, (255, 210, 40), rot=-5, scale=1 + .05 * math.sin(T * 10))
                amp = 6

    elif sc == "mayor":
        sky(img, (120, 200, 255), (255, 240, 200)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1450, W, H], fill=(200, 40, 40))
        block(d, [W/2 - 330, 1080, W/2 + 330, 1450], (230, 230, 240))  # escenario
        block(d, [W/2 - 80, 950, W/2 + 80, 1080], (110, 70, 40))  # atril
        bounce = abs(math.sin(T * 5)) * 30
        top = baby(d, W/2, 980 - bounce, 70, T, "evil", hat="tophat", seed=30, arms="up")
        d.polygon([(W/2 - 90, top - 110), (W/2 - 90, top - 170), (W/2 - 45, top - 135), (W/2, top - 190),
                   (W/2 + 45, top - 135), (W/2 + 90, top - 170), (W/2 + 90, top - 110)], fill=(255, 210, 30), outline=(0, 0, 0))
        for i, bx in enumerate([110, 280, 800, 970]):
            baby(d, bx, GY + 300, 32, T, "laugh", seed=i + 40, arms="up")
        for q in range(3):  # banderas
            fx = 150 + q * 390
            d.line([fx, 300, fx, 700], fill=(80, 80, 80), width=8)
            d.rectangle([fx, 300 + 15 * math.sin(T * 4 + q), fx + 160, 400 + 15 * math.sin(T * 4 + q)], fill=(255, 140, 180))
            d.text((fx + 80, 350 + 15 * math.sin(T * 4 + q)), "BABY", font=font(40), fill=(255, 255, 255), anchor="mm")
        if u > .2:
            stk("BABY MAYOR", W/2, 230, 110, (20, 20, 20), fg=(255, 210, 40), rot=-4)
        if u > .6 or full == "mayor_b":
            law = "LAW #2: FREE CANDY" if full == "mayor_b" else "LAW #1: NO NAPS"
            stk(law, W/2, 800, 80, (220, 30, 30) if full == "mayor" else (255, 90, 160), rot=4,
                    scale=1 + .05 * math.sin(T * 10))
        if full == "mayor_b":
            rnd = random.Random(int(T * 3))
            for q in range(14):  # lluvia de caramelos
                cx = (q * 83 + T * 40) % W; cy = (q * 157 + T * 500) % 1500
                d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=CLOTHES[q % 6], outline=(40, 40, 40), width=2)

    elif sc == "chaos":
        d = town(img, T, cam=t * 200)
        half = u < .5
        if half:
            for i in range(4):
                cx = (i * 330 + t * (420 + i * 60)) % (W + 400) - 200
                tiny_car(d, cx, GY + 120 + (i % 2) * 140, 70, CLOTHES[i], T, i + 50)
            stk("BABY DRIVERS", W/2, 400, 110, (255, 220, 90), rot=-5)
        else:
            block(d, [140, 880, 940, 1450], (255, 150, 200))
            block(d, [140, 830, 940, 930], (255, 90, 160))
            d.text((540, 880), "CANDY", font=font(80), fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(150, 30, 90))
            d.rectangle([440, 1150, 640, 1450], fill=(80, 40, 30))
            for i in range(5):
                bx = (540 + (i - 2) * 160 + t * 300 * (1 if i % 2 else -1)) % W
                top = baby(d, bx, GY + 80, 36, T, "evil", seed=i + 60, walk=1.4)
                d.ellipse([bx - 40, top - 70, bx + 40, top - 10], fill=CLOTHES[i], outline=(40, 40, 40), width=3)  # caramelo
            stk("ROBBERY", W/2, 400, 120, (220, 30, 30), rot=5)
            amp = 4

    elif sc == "police":
        d = town(img, T)
        lights = int(T * 6) % 2
        img.alpha_composite(Image.new("RGBA", (W, H), ((255, 40, 40) if lights else (40, 80, 255)) + (40,)))
        d = ImageDraw.Draw(img)
        block(d, [W/2 - 300, 1180, W/2 + 300, 1400], (240, 240, 250))
        d.text((W/2, 1290), "POLICE", font=font(70), fill=(30, 40, 90), anchor="mm")
        d.rectangle([W/2 - 80, 1140, W/2 + 80, 1180], fill=(255, 40, 40) if lights else (40, 80, 255))
        top = baby(d, W/2 + 40, 1140, 60, T, "evil", hat="police", seed=70, pacifier=True)
        d.rounded_rectangle([W/2 + 150, top + 80, W/2 + 215, top + 230], radius=20, fill=(255, 255, 255), outline=(40, 40, 40), width=3)  # biberón
        if u > .3:
            stk("ALSO BABIES", W/2, 420, 120, (30, 40, 90), rot=-5)
        if u > .6:
            avatar(d, 150, GY + 20, 55, me, T, 0, "up", "shock", look=1)
            stk("ARRESTED: TOO TALL", W/2, 620, 75, (255, 255, 255), fg=(220, 30, 30), rot=4)

    elif sc in ("huss_try", "baby_huss"):
        d = town(img, T)
        if sc == "huss_try":
            z = 1 + .15 * hit
            avatar(d, W/2, GY + 20, 70 * z, me, T, 0, "out" if hit > .1 else "down", "yell" if hit > .2 else "flat")
            for i, bx in enumerate([110, 270, 810, 970]):
                baby(d, bx, GY, 32, T, "shock" if k >= 0 else "laugh", seed=i + 80, look=1 if bx < W/2 else -1)
            if 0 <= k < seg["nh"]:
                stk("HUSS!", W/2 + (k - 1) * 260, 450, 120, (40, 90, 210), rot=-8 + 8 * k, scale=1 + .4 * hit)
            amp = int(22 * hit)
        else:
            avatar(d, W/2, GY + 20, 60, me, T, 0, "down", "shock")
            jump = 70 * hit
            for i in range(8):
                bx = 70 + i * 135 + (0 if i < 4 else 0)
                if abs(bx - W/2) < 110: continue
                baby(d, bx, GY + 220 - jump * (1 + (i % 2) * .4), 38, T, "yell" if hit > .2 else "laugh", seed=i + 90, arms="up")
            if k >= 0:
                for j in range(min(k + 1, seg["nh"])):
                    stk("huss", 160 + (j * 173) % 760, 330 + (j % 3) * 120, 80, CLOTHES[j], rot=-12 + 6 * j,
                            scale=1 + (.4 * hit if j == k else 0))
            amp = int(18 * hit)
            if full == "baby_huss_b":
                stk("WORST PLAN EVER", W/2, 420, 100, (30, 30, 30), fg=(255, 230, 40), rot=-5,
                        scale=1 + .05 * math.sin(T * 10))

    elif sc == "lab":
        sky(img, (20, 30, 40), (40, 60, 70)); d = ImageDraw.Draw(img)
        for yy in range(0, 1450, 120):
            d.line([0, yy, W, yy], fill=(50, 70, 80), width=3)
        d.rectangle([0, 1450, W, H], fill=(60, 70, 80))
        for q, tx in enumerate([110, 290, 790, 970]):  # tubos burbujeantes
            col = [(80, 255, 140), (120, 200, 255), (255, 120, 220), (255, 220, 80)][q]
            block(d, [tx - 60, 700, tx + 60, 1300], (40, 50, 60))
            d.rectangle([tx - 45, 760, tx + 45, 1280], fill=col)
            for b in range(5):
                by = 1280 - ((T * 200 + b * 110 + q * 50) % 520)
                d.ellipse([tx - 12 + 15 * math.sin(T * 3 + b), by - 12, tx + 12 + 15 * math.sin(T * 3 + b), by + 12], fill=(255, 255, 255))
        for sx in (380, 620):  # pantallas
            block(d, [sx - 90, 300, sx + 90, 430], (20, 20, 25))
            for ln in range(4):
                d.line([sx - 70, 330 + ln * 25, sx - 70 + ((T * 150 + ln * 40) % 140), 330 + ln * 25], fill=(80, 255, 140), width=6)
        # botón rojo gigante en pedestal
        block(d, [W/2 - 110, 1150, W/2 + 110, 1450], (150, 150, 160))
        g = 1 + .06 * math.sin(T * 8)
        d.ellipse([W/2 - 150 * g, 1040 - 60 * g, W/2 + 150 * g, 1160], fill=(230, 20, 30), outline=(60, 0, 0), width=8)
        uu = 1 if full == "lab_b" else u
        wx = -100 + (W/2 - 150) * ease(min(1, uu / .6))
        avatar(d, wx, GY + 40, 60, me, T, 1 if uu < .6 else 0, "down", "shock" if uu > .6 else "smile", look=1)
        if full == "lab_b" or u > .55:
            stk("DO NOT PRESS", W/2, 900, 70, (255, 255, 255), fg=(230, 20, 30), rot=-3)
            stk("SECRET LAB", W/2, 200, 100, (80, 255, 140), fg=(20, 30, 40), rot=4)

    elif sc == "press":
        sky(img, (20, 30, 40), (40, 60, 70)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1450, W, H], fill=(60, 70, 80))
        block(d, [W/2 - 110, 1150, W/2 + 110, 1450], (150, 150, 160))
        down = 30 if u > .45 else 0
        d.ellipse([W/2 - 150, 1040 - 60 + down, W/2 + 150, 1160], fill=(230, 20, 30), outline=(60, 0, 0), width=8)
        hand = 700 + 300 * ease(min(1, u / .45))
        block(d, [W/2 - 50, hand - 300, W/2 + 50, hand], CHARS["me"]["head"])
        if u > .45:
            stk("CLICK", W/2 + 260, 850, 110, (255, 255, 255), fg=(30, 30, 30), rot=10)
            flash(img, (u - .45) / .4)
            amp = int(30 * (u - .45))

    elif sc == "normal":
        d = town(img, T, cam=t * 60)
        for i in range(6):
            x = (100 + i * 190 + t * (70 if i % 2 else -60)) % (W + 100) - 50
            avatar(d, x, GY, 38, npc(i + 200), T + i, .8, "up", "laugh", look=1 if i % 2 else -1)
        if full == "normal_b":
            avatar(d, 300, GY, 60, CHARS["mayor"], T, 0, "out", "smile", look=1)
            d.rectangle([300 - 38, GY - 60 * 4 - 60 * 1.25 * 1.05 - 110, 300 + 38, GY - 60 * 4 - 60 * 1.25 * 1.05 - 10], fill=(20, 20, 20))
            stk("GRANDMA: OLD AGAIN", W/2, 420, 90, (170, 90, 160), rot=4)
        else:
            flash(img, max(0, 1 - t / .4))
            stk("BACK TO NORMAL", W/2, 420, 110, (40, 200, 90), rot=-4, scale=1 + .05 * math.sin(T * 9))

    elif sc == "twist":
        d = town(img, T)
        for i, x in enumerate([120, 310, 770, 960]):
            avatar(d, x, GY + 10 * abs(math.sin(T * 9 + i)), 42, npc(i + 200), T, 0, "down", "laugh", look=1 if x < W/2 else -1)
        sh = 1 + .12 * hit
        baby(d, W/2, GY + 40, 80 * sh, T, "cry" if k < 0 else ("yell" if hit > .2 else "cry"), hat="huss",
             clothes=(40, 90, 210), seed=7, pacifier=k < 0)
        if u > .15 or full == "twist_b":
            stk("BABY HUSS BOY", W/2, 330, 110, (40, 90, 210), rot=-5, scale=1 + .05 * math.sin(T * 9))
        if full == "twist_b" and u > .5:
            stk("WORTH IT", W/2, 560, 130, (40, 200, 90), rot=6, scale=1 + .06 * math.sin(T * 10))
        if 0 <= k < seg["nh"]:
            stk("huss!", W/2 + (k - 1) * 240, 560, 90, (255, 140, 180), rot=-8 + 8 * k, scale=1 + .4 * hit)
        amp = int(14 * hit)

    else:
        return ORIG_RENDER(seg, t, T)

    img = camera(img, full, u)
    for a_, k_ in later:
        sticker(img, *a_, **k_)
    if amp: img = shake_img(img, amp)
    return img

# ------------------------------------------------------------------ audio extra: llantos de bebé, clic, flash
def cry(dur=0.9, f0=520, seed=0):
    n = int(SR * dur); t = np.arange(n) / SR
    f = f0 * (1 + .25 * np.sin(2 * np.pi * 1.4 * t)) * (1 + .03 * np.sin(2 * np.pi * 7 * t)) * (1 - .3 * t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(ph * h) / h for h in range(1, 8))
    env = np.minimum(1, t / .05) * np.minimum(1, (dur - t) / .15)
    return (x * env * .22).astype(np.float32)

ORIG_MIX = m.mix_audio

def mix_audio(segs, total, out_wav):
    ORIG_MIX(segs, total, out_wav)
    with wave.open(out_wav) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = a.copy(); n = len(a)
    loud = np.zeros(n, np.float32)   # llantos y sirena: chocan con la voz
    hits = np.zeros(n, np.float32)   # golpes, pops...
    def put(buf, x, t):
        s_ = int(t * SR); e = min(n, s_ + len(x))
        if e > s_: buf[s_:e] += x[:e - s_]
    for s in segs:
        st, du = s["start"], s["dur"]
        if s["scene"] == "morning":
            put(loud, cry(1.2, 560) * .8, 0.05)
            put(hits, m.riser(1.0), st + du * .7 - .9); put(hits, m.sfx("boom") * .7, st + du * .95)
        if s["scene"] == "babies":
            for j, f0 in enumerate((480, 600, 540, 650)):
                put(loud, cry(1.0, f0, j) * .6, st + .2 + j * .45)
        if s["scene"] == "babies2":
            for j in range(3): put(hits, m.sfx("pop") * .8, st + j * du / 3)
        if s["scene"] == "chaos":
            put(hits, m.sfx("boing") * .6, st + .3); put(hits, m.sfx("boing") * .6, st + 1.1)
        if s["scene"] == "police":
            n_ = int(SR * 1.6); tt = np.arange(n_) / SR
            put(loud, (np.sin(2 * np.pi * np.cumsum(700 + 250 * np.sign(np.sin(2 * np.pi * 2.5 * tt))) / SR) * .12).astype(np.float32), st)
        if s["scene"] == "press":
            put(hits, m.sfx("pop") * 1.2, st + du * .45); put(hits, m.sfx("boom"), st + du * .5)
        if s["scene"] == "twist":
            put(loud, cry(1.4, 600) * .5, st + du * .85)
    # 1) quitar a los llantos la zona de frecuencias de la voz (700-3500 Hz, -14 dB)
    X = np.fft.rfft(loud); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f > 700) & (f < 3500)] *= .2
    loud = np.fft.irfft(X, n).astype(np.float32) * .7
    # 2) ducking: cuando habla el narrador, llantos al 15 % y golpes al 50 %
    voice = np.zeros(n, np.float32)
    for s in segs:
        put(voice, np.abs(s["audio"]), s["start"])
    env = np.convolve(voice, np.ones(2205) / 2205, "same")
    talk = np.clip(env * 25, 0, 1)
    talk = np.convolve(talk, np.ones(4410) / 4410, "same")  # suavizado ~100 ms para que no "bombee"
    a += loud * (1 - .85 * talk) + hits * (1 - .5 * talk)
    a /= max(1, np.abs(a).max() / .95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

ORIG_BUILD = m.build

def build(voice, tmp):
    """Igual que el motor, pero el vídeo dura exactamente 60 s."""
    segs, total = ORIG_BUILD(voice, tmp)
    print(f"duración natural: {total:.2f}s")
    if total > TARGET:
        raise SystemExit(f"El guion dura {total:.1f}s (> {TARGET}s): acórtalo.")
    extra = TARGET - total
    n = len(segs)
    for i, sg in enumerate(segs):  # reparte el tiempo sobrante entre las pausas de todas las escenas
        off = extra * i / n
        sg["start"] += off
        if sg.get("huss_t0") is not None: sg["huss_t0"] += off
        sg["hits"] = [h + off for h in sg.get("hits") or []]
        sg["words"] = [(w, a + off, b + off) for w, a, b in sg["words"]]
        if sg.get("reveal"): sg["reveal"] += off
    segs[-1]["dur"] += extra / n
    return segs, TARGET

ORIG_RENDER = m.render_scene
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = build

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "babies.mp4"]
    m.main()
