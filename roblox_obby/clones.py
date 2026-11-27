#!/usr/bin/env python3
"""Historia 4: EVERYONE LOOKS THE SAME (60 s exactos).

Uso: python3 clones.py --voice ruta/en_US-ryan-high.onnx [--out clones.mp4]
Reutiliza el motor de in_this_town.py (HUSS real, música de fondo, narrador, subtítulos).
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
from in_this_town import (W, H, SR, CHARS, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)

TARGET = 60.0
GY = 1450
ME = CHARS["me"]

SCRIPT = [
    # 1 (0-5 s) gancho
    ("In this town, I opened my front door... and saw THIS.", "door", None),
    ("Another me. And another. And another.", "stare", None),
    ("Same face. Same hat. Same amazing jersey.", "stare_b", None),
    # 2 (5-15 s) todos son él
    ("The shopkeeper? Me. The police officer? Also me.", "jobs", None),
    ("The kids? Tiny me. Even the mayor was me... with a mustache.", "jobs_b", None),
    ("I went to buy bread. Even the bread had my face.", "bread", None),
    # 3 (15-25 s) le copian
    ("Okay. Who's real? I raised my hand...", "copy", None),
    ("I did a little dance. They did the EXACT same dance.", "dance", None),
    ("I did a backflip. They ALL did a backflip.", "flip", None),
    ("So I said:", "huss_me", "solo", 3),
    ("And the whole town said it back.", "huss_all", "crowd", 6),
    # 4 (25-38 s) el clon malvado
    ("But then... one of them didn't stop.", "odd", None),
    ("His eyes turned red.", "evil", None),
    ("He snapped his fingers... and every single clone turned to look at me.", "control", None),
    ("And they all said, very slowly:", "control_b", "deep", 3),
    # 5 (38-50 s) persecución
    ("I RAN!", "chase", None),
    ("They jumped over cars! They smashed the fruit stand!", "chase_b", None),
    ("They came out of the trash cans! They jumped off the roofs!", "chase_c", None),
    ("I made it home and locked the door.", "home", None),
    # 6 (50-60 s) giro
    ("Safe. I looked in the mirror...", "mirror", None),
    ("My reflection smiled. I did not.", "mirror_b", None),
    ("Then I saw the tag on my shirt. Clone number 348.", "tag", None),
    ("The real me waved goodbye... from inside the mirror.", "tag_c", None),
]

VAR = {"control_b": "control", "chase_c": "chase", "mirror_b": "mirror", "tag_c": "tag_c"}

RED = (255, 30, 30)

# ------------------------------------------------------------------ personaje
def clone(d, x, y, s, t, walk=0., arms="down", face="flat", look=0, evil=False, hat=None, tag=False):
    top = avatar(d, x, y, s, ME, t, walk, arms, face, look)
    hs = s * 1.25
    if hat == "shop":
        d.rectangle([x - s * .75, y - s * 3.7, x + s * .75, y - s * 2.1], fill=(250, 250, 250), outline=(60, 60, 60), width=2)
    elif hat == "police":
        d.rectangle([x - hs/2 - 5, top - s * .45, x + hs/2 + 5, top + s * .3], fill=(25, 35, 80))
        d.rectangle([x - hs/2 - 10, top + s * .2, x + hs/2 + 10, top + s * .36], fill=(15, 15, 25))
        d.regular_polygon((x, top - s * .1, s * .2), 6, fill=(255, 210, 40))
    elif hat == "mayor":
        d.rectangle([x - hs * .45, top - s * .15, x + hs * .45, top + s * .05], fill=(20, 20, 20))
        d.rectangle([x - hs * .3, top - s * 1.2, x + hs * .3, top - s * .1], fill=(20, 20, 20))
        my = top + hs * .66
        d.polygon([(x - s * .45, my + s * .1), (x - s * .1, my - s * .06), (x, my + s * .02), (x + s * .1, my - s * .06),
                   (x + s * .45, my + s * .1), (x + s * .2, my + s * .14), (x, my + s * .08), (x - s * .2, my + s * .14)], fill=(50, 30, 15))
    if evil:
        ex = s * .2 * look
        for e in (-1, 1):
            cx, cy = x + e * s * .28 + ex, top + hs * .35 + s * .11
            g = 1 + .2 * math.sin(t * 10)
            d.ellipse([cx - s * .2 * g, cy - s * .16 * g, cx + s * .2 * g, cy + s * .16 * g], fill=(255, 90, 0))
            d.ellipse([cx - s * .12, cy - s * .1, cx + s * .12, cy + s * .1], fill=RED)
            d.line([x + e * s * .48 + ex, top + hs * .2, x + e * s * .1 + ex, top + hs * .33], fill=(15, 15, 15), width=max(2, int(s * .1)))
    if tag:
        d.rectangle([x - s * .75, y - s * 3.2, x + s * .75, y - s * 2.55], fill=(255, 255, 255), outline=(40, 40, 40), width=2)
        d.text((x, y - s * 2.88), "CLONE #348", font=font(max(8, int(s * .22))), fill=(220, 30, 30), anchor="mm")
    return top

def crowd(d, t, rows=8, y0=1000, y1=1880, arms_fn=None, face="flat", look_fn=None, evil_fn=None, walk=0., skip=None):
    """Cientos de clones idénticos en perspectiva (filas del fondo pequeñas)."""
    n = 0
    rows = min(rows, 4); y0 = max(y0, 1200)
    for r in range(rows):
        k = r / max(1, rows - 1)
        s = 20 + 26 * k
        y = y0 + (y1 - y0) * k
        sp = s * 4.4
        off = (r % 2) * sp / 2
        x = -sp + off
        while x < W + sp:
            if not (skip and skip(x, r)):
                arms = arms_fn(x, r) if arms_fn else "down"
                lk = look_fn(x, r) if look_fn else 0
                ev = evil_fn(x, r) if evil_fn else False
                clone(d, x, y, s, t + (0 if not walk else x * .001), walk, arms, face, lk, ev)
                n += 1
            x += sp
    return n

def camera(img, key, u):
    if key not in CAMS: return img
    z0, z1, (x0, y0), (x1, y1) = CAMS[key]
    k = ease(u)
    z = z0 + (z1 - z0) * k
    cx, cy = (x0 + (x1 - x0) * k) * W, (y0 + (y1 - y0) * k) * H
    cw, ch = W / z, H / z
    l = min(max(0, cx - cw/2), W - cw); tp = min(max(0, cy - ch/2), H - ch)
    return img.crop((int(l), int(tp), int(l + cw), int(tp + ch))).resize((W, H), Image.BILINEAR)

CAMS = {
    "door": (1.0, 1.15, (.5, .55), (.55, .55)), "stare": (1.25, 1.0, (.5, .62), (.5, .55)),
    "jobs": (1.2, 1.0, (.35, .55), (.65, .55)), "jobs_b": (1.0, 1.3, (.5, .55), (.5, .5)),
    "copy": (1.15, 1.0, (.5, .6), (.5, .5)), "dance": (1.0, 1.2, (.3, .55), (.7, .55)),
    "huss_me": (1.0, 1.25, (.5, .55), (.5, .5)), "huss_all": (1.25, 1.0, (.5, .62), (.5, .5)),
    "odd": (1.0, 1.5, (.5, .5), (.5, .6)), "evil": (1.3, 2.7, (.5, .6), (.5, .66)),
    "control": (1.0, 1.0, (.5, .5), (.5, .5)), "chase": (1.15, 1.15, (.4, .6), (.6, .6)),
    "chase_b": (1.1, 1.3, (.5, .55), (.5, .6)), "home": (1.0, 1.25, (.5, .55), (.45, .6)),
    "mirror": (1.0, 1.2, (.4, .5), (.55, .5)), "tag": (1.0, 1.0, (.5, .5), (.5, .5)),
    "stare_b": (1.0, 1.05, (.5, .55), (.5, .55)), "bread": (1.0, 1.3, (.5, .55), (.5, .5)),
    "flip": (1.2, 1.0, (.5, .6), (.5, .5)), "control_b": (1.0, 1.4, (.5, .55), (.5, .6)),
    "chase_c": (1.2, 1.0, (.5, .5), (.5, .55)), "mirror_b": (1.3, 1.9, (.68, .55), (.7, .56)),
    "tag_c": (1.0, 1.25, (.5, .5), (.6, .45)),
}

def tint(img, col, a):
    if a > 0: img.alpha_composite(Image.new("RGBA", (W, H), col + (int(a),)))

_VIG = None

def vignette(img, a=200):
    global _VIG
    if _VIG is None:  # máscara difuminada calculada una sola vez
        from PIL import ImageFilter
        v = Image.new("L", (W, H), 0); ImageDraw.Draw(v).ellipse([-250, 150, W + 250, H - 150], fill=255)
        _VIG = np.asarray(v.filter(ImageFilter.GaussianBlur(160)), np.float32) / 255
    a = int(a)
    alpha = Image.fromarray((a * (1 - _VIG)).astype(np.uint8), "L")
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(alpha)
    img.alpha_composite(dark)

def bathroom(img):
    sky(img, (200, 235, 240), (170, 215, 225)); d = ImageDraw.Draw(img)
    for yy in range(0, 1450, 110):
        for xx in range(0, W, 110):
            d.rectangle([xx + 4, yy + 4, xx + 106, yy + 106], fill=(220, 245, 248))
    d.rectangle([0, 1450, W, H], fill=(150, 120, 100))
    return d

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    full = seg["scene"]; sc = VAR.get(full, full); dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)

    if sc == "door":
        # interior: Huss Boy abre la puerta... y al otro lado hay OTRO Huss Boy, cara a cara
        sky(img, (240, 225, 200), (225, 205, 175)); d = ImageDraw.Draw(img)
        for yy in range(0, H, 60):
            d.line([0, yy, W, yy], fill=(230, 212, 185), width=3)
        d.rectangle([0, 1600, W, H], fill=(150, 105, 70))
        open_ = ease(min(1, max(0, (u - .3) / .15)))
        dx0, dx1, dy0, dy1 = 460, 1000, 450, 1600
        # exterior por el hueco de la puerta
        out = Image.new("RGBA", (W, H)); town(out, T)
        od = ImageDraw.Draw(out)
        if open_ > 0:
            clone(od, 730, 1760, 110, T, 0, "down", "flat", look=-1)
        hole = Image.new("L", (W, H), 0); ImageDraw.Draw(hole).rectangle([dx0, dy0, dx1, dy1], fill=255)
        img.paste(out, (0, 0), hole); d = ImageDraw.Draw(img)
        d.rectangle([dx0 - 30, dy0 - 30, dx1 + 30, dy0], fill=(110, 70, 40))
        d.rectangle([dx0 - 30, dy0, dx0, dy1], fill=(110, 70, 40)); d.rectangle([dx1, dy0, dx1 + 30, dy1], fill=(110, 70, 40))
        # hoja de la puerta que se abre
        dw = (dx1 - dx0) * (1 - open_)
        if dw > 4:
            d.rectangle([dx1 - dw, dy0, dx1, dy1], fill=(140, 90, 50), outline=(70, 40, 20), width=6)
            d.ellipse([dx1 - dw + 20, 1020, dx1 - dw + 50, 1050], fill=(240, 200, 60))
        # Huss Boy recién levantado (bostezo -> susto)
        shock = open_ > .5
        clone(d, 250, 1800, 125, T, 0, "up" if shock else "out", "shock" if shock else ("yell" if u < .25 else "flat"), look=1)
        if t < 2.0:
            p = min(1, t / .2)
            stk("EVERYONE", W/2, 330, 150, (40, 90, 210), rot=-6, scale=.5 + .5 * p + .05 * math.sin(T * 14))
            stk("LOOKS THE SAME", W/2, 520, 110, (255, 210, 40), fg=(40, 90, 210), rot=4, scale=.5 + .5 * p)
        elif shock:
            stk("?!", 730, 330, 220, (220, 30, 30), rot=8, scale=1 + .1 * math.sin(T * 12))
            amp = int(14 * max(0, 1 - (u - .45) * 3))

    elif sc == "stare":
        # van apareciendo, uno a uno, en fila
        d = town(img, T)
        n_show = min(5, 1 + int(u * 5.5))
        xs = [W/2, W/2 - 300, W/2 + 300, W/2 - 600 + 160, W/2 + 600 - 160]
        order = sorted(range(n_show), key=lambda i: -abs(xs[i] - W/2))
        for i in order:
            born = i / 5.5 * dur
            pop = min(1, max(0, (t - born) / .15))
            sz = (105 if i == 0 else 78) * (.6 + .4 * pop) * (1 + .15 * max(0, 1 - (t - born) / .25))
            clone(d, xs[i], 1800 if i == 0 else 1600, sz, T, 0, "down", "flat", look=0)
        stk(["ANOTHER ME", "AND ANOTHER", "AND ANOTHER"][min(2, int(u * 3))], W/2, 380, 110, (40, 90, 210), rot=-4 + 4 * int(u * 3),
            scale=1 + .05 * math.sin(T * 10))

    elif sc == "stare_b":
        # primeros planos: misma cara, mismo gorro, misma camiseta
        d = town(img, T)
        third = min(2, int(u * 3))
        for i, x in enumerate([W/2 - 330, W/2 + 330]):
            clone(d, x, 1500, 50, T, 0, "down", "flat", look=1 if i == 0 else -1)
        clone(d, W/2, 1950, 140 + third * 15, T, 0, "down", "smile")
        stk(["SAME FACE", "SAME HAT", "SAME JERSEY"][third], W/2, 380, 110, [(40, 90, 210), (30, 70, 190), (255, 210, 40)][third],
            fg=(255, 255, 255), rot=-4 + 4 * third)
        if (u * 3) % 1 < .06: tint(img, (255, 255, 255), 150)

    elif sc in ("jobs", "jobs_b"):
        d = town(img, T)
        part = min(1, int(u * 2))
        role = ["shop", "police"][part] if sc == "jobs" else ["kids", "mayor"][part]
        if role == "shop":
            block(d, [140, 850, 940, 1450], (255, 200, 120)); block(d, [140, 800, 940, 900], (230, 90, 60))
            d.text((540, 850), "SHOP", font=font(80), fill=(255, 255, 255), anchor="mm")
            for q in range(5):
                d.ellipse([220 + q * 140, 1180, 300 + q * 140, 1260], fill=[(240, 60, 60), (255, 200, 40), (90, 200, 90), (255, 140, 30), (200, 80, 200)][q])
            clone(d, W/2, GY, 70, T, 0, "out", "smile", hat="shop")
            stk("SHOPKEEPER = ME", W/2, 380, 95, (230, 90, 60), rot=-4)
        elif role == "police":
            lights = int(T * 6) % 2
            block(d, [W/2 - 330, 1200, W/2 + 330, 1420], (240, 240, 250))
            d.text((W/2 - 120, 1310), "POLICE", font=font(60), fill=(30, 40, 90), anchor="mm")
            d.rectangle([W/2 - 260, 1160, W/2 - 140, 1200], fill=RED if lights else (40, 80, 255))
            clone(d, W/2 + 200, GY, 70, T, 0, "out", "angry", look=-1, hat="police")
            tint(img, RED if lights else (40, 80, 255), 30)
            stk("POLICE = ALSO ME", W/2, 380, 95, (30, 40, 90), rot=4)
        elif role == "kids":
            for i in range(6):
                x = 120 + i * 170
                clone(d, x, GY - abs(math.sin(T * 8 + i)) * 60, 26, T, 0, "up", "laugh")
            stk("TINY ME", W/2, 380, 120, (255, 140, 180), rot=-5)
        else:
            block(d, [W/2 - 300, 1150, W/2 + 300, 1450], (230, 230, 240))
            clone(d, W/2, 1150, 75, T, 0, "out", "smile", hat="mayor")
            if u > .75:
                stk("MUSTACHE", W/2, 380, 130, (50, 30, 15), rot=6, scale=1 + .08 * math.sin(T * 12))
                amp = 4
            else:
                stk("MAYOR = ME", W/2, 380, 100, (20, 20, 20), fg=(255, 210, 40), rot=-4)
        # destello de transición entre los dos roles
        tr = abs(u - .5)
        if tr < .03: tint(img, (255, 255, 255), 180 * (1 - tr / .03))

    elif sc == "bread":
        d = town(img, T)
        block(d, [100, 820, 980, 1450], (255, 225, 170)); block(d, [100, 770, 980, 870], (200, 130, 60))
        d.text((540, 820), "BAKERY", font=font(80), fill=(255, 255, 255), anchor="mm")
        for q in range(6):  # panes con su cara
            bx = 200 + q * 135; by = 1000 + 12 * math.sin(T * 5 + q)
            d.rounded_rectangle([bx - 55, by - 45, bx + 55, by + 45], radius=25, fill=(210, 140, 70), outline=(110, 60, 20), width=4)
            d.rectangle([bx - 40, by - 50, bx + 40, by - 30], fill=(30, 70, 190))
            d.ellipse([bx - 22, by - 10, bx - 10, by + 4], fill=(30, 20, 10)); d.ellipse([bx + 10, by - 10, bx + 22, by + 4], fill=(30, 20, 10))
            d.arc([bx - 20, by, bx + 20, by + 25], 10, 170, fill=(30, 20, 10), width=4)
        clone(d, 300, GY, 62, T, 0, "out", "smile", look=1, hat="shop")
        clone(d, 780, GY, 62, T, 0, "down", "shock" if u > .4 else "flat", look=-1)
        if u > .45: stk("EVEN THE BREAD", W/2, 380, 100, (200, 130, 60), rot=5, scale=1 + .05 * math.sin(T * 10))

    elif sc == "flip":
        d = town(img, T)
        ph = min(1, u / .7)
        jump = math.sin(ph * math.pi) * 260
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        crowd(ld, T, rows=6, y0=1050, y1=1450, arms_fn=lambda x, r: "up", face="laugh")
        lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay2.paste(lay, (0, -int(jump * .6)))
        img.alpha_composite(lay2)
        me_l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); md = ImageDraw.Draw(me_l)
        clone(md, W/2, 1800, 90, T, 0, "up", "yell")
        me_l = me_l.rotate(-360 * ease(ph), center=(W/2, 1550), resample=Image.BICUBIC)
        img2 = Image.new("RGBA", (W, H)); img2.paste(me_l, (0, -int(jump)))
        img.alpha_composite(img2)
        if u > .6: stk("SAME BACKFLIP", W/2, 380, 110, (255, 140, 180), rot=-5)

    elif sc in ("copy", "dance"):
        d = town(img, T)
        if sc == "copy":
            arms = "up" if u > .45 else "down"
            crowd(d, T, rows=7, y0=1050, y1=1500, arms_fn=lambda x, r: arms)
            clone(d, W/2, 1800, 95, T, 0, arms, "shock" if u > .45 else "flat")
            if u > .5: stk("EVERYONE RAISED THEIR HAND", W/2, 380, 70, (40, 90, 210), rot=-3)
        else:
            # el baile sincronizado (momento para repetir)
            ph = math.sin(T * 9)
            arms = "dance"
            def af(x, r): return arms
            lay_shift = int(40 * ph)
            crowd(d, T, rows=7, y0=1050, y1=1500, arms_fn=af, face="laugh")
            img2 = Image.new("RGBA", (W, H)); img2.paste(img, (lay_shift, 0)); img = img2
            d = ImageDraw.Draw(img)
            clone(d, W/2 + 40 * ph, 1800 - abs(ph) * 40, 95, T, 0, "dance", "laugh")
            stk("SYNCHRONIZED", W/2, 380, 110, (255, 140, 180), rot=-5 + 6 * ph)

    elif sc in ("huss_me", "huss_all"):
        d = town(img, T)
        if sc == "huss_me":
            crowd(d, T, rows=7, y0=1050, y1=1500, face="flat")
            z = 1 + .12 * hit
            clone(d, W/2, 1800, 95 * z, T, 0, "out" if hit > .1 else "down", "yell" if hit > .2 else "flat")
            if 0 <= k < seg["nh"]:
                stk("HUSS!", W/2 + (k - 1) * 250, 470, 120, (40, 90, 210), rot=-8 + 8 * k, scale=1 + .4 * hit)
            amp = int(18 * hit)
        else:
            jump = 50 * hit
            crowd(d, T, rows=10, arms_fn=lambda x, r: "up" if hit > .2 else "down", face="yell" if hit > .2 else "flat")
            if jump:
                img2 = Image.new("RGBA", (W, H)); img2.paste(img, (0, -int(jump))); img = img2
            if 0 <= k:
                for j in range(min(k + 1, seg["nh"])):
                    stk("HUSS", 170 + (j * 197) % 740, 300 + (j % 3) * 130, 120, (40, 90, 210), rot=-12 + 6 * j,
                        scale=1 + (.4 * hit if j == k else 0))
            amp = int(30 * hit)

    elif sc in ("odd", "evil", "control"):
        d = town(img, T, tint="night")
        cx_odd = W/2
        if sc == "odd":
            crowd(d, T, rows=7, y0=1050, y1=1700, skip=lambda x, r: r == 5 and abs(x - cx_odd) < 60)
            d = ImageDraw.Draw(img)
            # el único que sigue bailando
            spot = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(spot)
            sd.polygon([(cx_odd - 60, 0), (cx_odd + 60, 0), (cx_odd + 160, 1620), (cx_odd - 160, 1620)], fill=(255, 250, 200, 90))
            img.alpha_composite(spot); d = ImageDraw.Draw(img)
            clone(d, cx_odd, 1620, 40, T, 0, "dance", "laugh")
            if u > .5: stk("...", cx_odd, 1200, 110, (30, 30, 30), rot=0)
            vignette(img, 150)
        elif sc == "evil":
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
            d = ImageDraw.Draw(img)
            crowd(d, T, rows=5, y0=1000, y1=1400)
            ev = u > .25
            clone(d, W/2, 1650, 75, T, 0, "down", "flat", evil=ev)
            if ev:
                tint(img, (120, 0, 0), 60 + 30 * math.sin(T * 8))
                if u < .4: tint(img, (255, 255, 255), 200 * (1 - (u - .25) / .15))
                amp = int(16 * max(0, 1 - (u - .25) * 3))
            vignette(img, 220)
            if u > .35: stk("RED EYES", W/2, 380, 120, (0, 0, 0), fg=RED, rot=-5)
        else:
            # el clon malvado chasquea los dedos y los ojos rojos se propagan
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 100)))
            d = ImageDraw.Draw(img)
            wave_r = 9 if full == "control_b" else u * 1.6
            crowd(d, T, rows=8, y0=1000, y1=1700, look_fn=lambda x, r: -1 if x > W/2 else 1,
                  evil_fn=lambda x, r: abs(x - W/2) / W + (1 - r / 7) * .4 < wave_r)
            if u < .25 and full == "control":
                stk("SNAP", W/2, 700, 130, (255, 255, 255), fg=(30, 30, 30), rot=8)
            tint(img, (120, 0, 0), 50)
            vignette(img, 200)
            if full == "control_b":
                if 0 <= k < seg["nh"]:
                    stk("huss...", W/2 + (k - 1) * 240, 520 + k * 60, 110, (0, 0, 0), fg=RED, rot=-6 + 6 * k, scale=1 + .3 * hit)
                amp = int(12 * hit)
            elif u > .6: stk("THEY ALL LOOKED AT ME", W/2, 380, 75, (0, 0, 0), fg=RED, rot=-3)

    elif sc in ("chase", "chase_b"):
        d = town(img, T, tint="night", cam=t * 1400)
        tint(img, (120, 0, 0), 40); d = ImageDraw.Draw(img)
        if sc == "chase_b":  # coche que los clones saltan y puesto de fruta que se cae
            carx = W - ((t * 900) % (W + 600))
            block(d, [carx - 170, 1520, carx + 170, 1640], (60, 160, 230))
            for wx in (-100, 100): d.ellipse([carx + wx - 35, 1610, carx + wx + 35, 1680], fill=(30, 30, 30))
            stall = 700 - t * 500
            ang = min(90, max(0, (t - .8) * 160))
            block(d, [stall - 120, 1500 + ang, stall + 120, 1640], (200, 140, 80))
            rnd = random.Random(2)
            for q in range(12):
                fx = stall + rnd.uniform(-120, 120) + (t - .8) * rnd.uniform(-300, 300) * (t > .8)
                fy = 1490 + ((t - .8) * rnd.uniform(200, 600) + 400 * (t - .8) ** 2) * (t > .8)
                d.ellipse([fx - 22, fy - 22, fx + 22, fy + 22], fill=[(240, 60, 60), (255, 200, 40), (90, 200, 90), (255, 140, 30)][q % 4])
            if t > .8 and t < 1.6: stk("CRASH", stall, 1250, 110, (255, 220, 40), fg=(220, 30, 30), rot=-8)
        # cosas cayendo desde arriba
        rnd = random.Random(int(T))
        for q in range(4):
            ox = rnd.uniform(100, W - 100); oy = ((T * 900 + q * 300) % 1700) - 100
            block(d, [ox - 35, oy - 35, ox + 35, oy + 35], [(160, 110, 60), (230, 80, 80), (120, 170, 230), (250, 210, 110)][q])
        # la horda de clones malvados (detrás) y el real (delante, a la derecha)
        for r in range(4):
            for j in range(9):
                x = -80 + j * 70 + r * 25 + 30 * math.sin(T * 3 + j)
                y = 1560 + r * 70 - abs(math.sin(T * 9 + j + r)) * (110 if (j + r) % 3 == 0 else 40)
                clone(d, x, y, 22 + r * 4, T * 2 + j, 1.6, "out", "angry", 1, evil=True)
        if full == "chase_c":
            for q, (bx, by) in enumerate([(180, 1450), (520, 1450)]):  # cubos de basura con clones saliendo
                pop = min(1, max(0, (u - .1 - q * .15) * 4))
                clone(d, bx, by - 120 * pop + 40, 34, T, 0, "up", "angry", evil=True)
                block(d, [bx - 70, by - 110, bx + 70, by + 40], (110, 120, 120)); d.rectangle([bx - 80, by - 125, bx + 80, by - 100], fill=(90, 100, 100))
            for q in range(3):  # clones saltando desde los tejados
                rx = 260 + q * 300; fall = ((t * 1.3 + q * .4) % 1.4)
                clone(d, rx, 800 + fall * 600, 30, T, 0, "up", "yell", evil=True)
        clone(d, 860, 1700 - abs(math.sin(T * 10)) * 50, 55, T * 2, 1.6, "up", "yell", 1)
        if sc == "chase": stk("RUN!", W/2, 400, 170, (220, 30, 30), rot=-6, scale=1 + .08 * math.sin(T * 14))
        amp = 7

    elif sc == "home":
        d = town(img, T)
        block(d, [150, 850, 930, 1450], (120, 170, 230))
        d.polygon([(120, 850), (540, 560), (960, 850)], fill=(150, 60, 50), outline=(20, 20, 30))
        slam = u > .55
        d.rectangle([460, 1150, 620, 1450], fill=(110, 70, 40), outline=(20, 20, 30), width=6)
        if not slam:
            clone(d, 300 + 240 * ease(u / .55), GY, 50, T * 2, 1.5, "up", "yell", 1)
        # caras de clones pegadas a la ventana (momento gracioso)
        for wx in (260, 820):
            block(d, [wx - 90, 950, wx + 90, 1100], (180, 220, 255))
            if slam:
                for q in range(2):
                    cx = wx - 40 + q * 80
                    d.rectangle([cx - 35, 970, cx + 35, 1050], fill=(255, 205, 160))
                    d.ellipse([cx - 22, 995, cx - 8, 1012], fill=RED); d.ellipse([cx + 8, 995, cx + 22, 1012], fill=RED)
                    d.ellipse([cx - 20, 1020, cx + 20, 1048], fill=(240, 160, 150))  # cara aplastada
        if slam:
            stk("SLAM", 540, 1000, 130, (255, 255, 255), fg=(30, 30, 30), rot=-6, scale=1 + .3 * max(0, 1 - (u - .55) * 6))
            stk("LOCKED", W/2, 380, 110, (40, 200, 90), rot=4)
            amp = int(20 * max(0, 1 - (u - .55) * 4))

    elif sc == "mirror":
        d = bathroom(img)
        mx0, mx1, my0, my1 = 520, 1000, 520, 1300
        block(d, [mx0 - 25, my0 - 25, mx1 + 25, my1 + 25], (200, 170, 90))
        d.rectangle([mx0, my0, mx1, my1], fill=(170, 200, 215))
        # reflejo (dentro del espejo)
        refl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(refl)
        smile = full == "mirror_b"
        clone(rd, 760, 1450, 78, T, 0, "down", "smile" if smile else "flat", look=-1)
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rectangle([mx0, my0, mx1, my1], fill=255)
        img.paste(refl, (0, 0), Image.composite(refl.getchannel("A"), Image.new("L", (W, H), 0), mask))
        d = ImageDraw.Draw(img)
        d.line([mx0 + 40, my0 + 40, mx0 + 160, my0 + 160], fill=(255, 255, 255), width=10)  # brillo del espejo
        # el real (de perfil, mirando al espejo)
        clone(d, 260, 1650, 85, T, 0, "down", "shock" if smile else "flat", look=1)
        if smile:
            stk("I DID NOT SMILE", W/2, 380, 95, (0, 0, 0), fg=RED, rot=-4)
            vignette(img, 120 + 60 * min(1, (u - .55) * 4))

    elif sc == "tag_c":
        d = bathroom(img)
        mx0, mx1, my0, my1 = 520, 1000, 480, 1300
        block(d, [mx0 - 25, my0 - 25, mx1 + 25, my1 + 25], (200, 170, 90))
        d.rectangle([mx0, my0, mx1, my1], fill=(170, 200, 215))
        refl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(refl)
        wave_ = "up" if int(T * 4) % 2 else "out"
        clone(rd, 760, 1420, 74, T, 0, wave_, "smile", look=-1)
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rectangle([mx0, my0, mx1, my1], fill=255)
        img.paste(refl, (0, 0), Image.composite(refl.getchannel("A"), Image.new("L", (W, H), 0), mask))
        d = ImageDraw.Draw(img)
        clone(d, 260, 1650, 85, T, 0, "down", "shock", look=1, tag=True, evil=True)
        stk("THE REAL ME", 760, 400, 100, (40, 200, 90), rot=5, scale=1 + .05 * math.sin(T * 10))
        if u > .5: stk("BYE!", 760, 600, 110, (255, 255, 255), fg=(40, 90, 210), rot=-6)
        tint(img, (120, 0, 0), 30)
        vignette(img, 140)

    elif sc == "tag":
        d = bathroom(img)
        mx0, mx1, my0, my1 = 160, 920, 380, 1500
        block(d, [mx0 - 25, my0 - 25, mx1 + 25, my1 + 25], (200, 170, 90))
        d.rectangle([mx0, my0, mx1, my1], fill=(170, 200, 215))
        refl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(refl)
        reveal = u > .5
        clone(rd, W/2, 1650, 110 * (1 + .25 * ease(u)), T, 0, "down", "laugh" if reveal else "flat", tag=True, evil=reveal)
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rectangle([mx0, my0, mx1, my1], fill=255)
        img.paste(refl, (0, 0), Image.composite(refl.getchannel("A"), Image.new("L", (W, H), 0), mask))
        d = ImageDraw.Draw(img)
        if reveal:
            tint(img, (120, 0, 0), 60 + 30 * math.sin(T * 6))
            if u < .58: tint(img, (255, 255, 255), 220 * (1 - (u - .5) / .08))
            stk("CLONE #348", W/2, 300, 140, (255, 255, 255), fg=RED, rot=-5, scale=1 + .06 * math.sin(T * 10))
            stk("WAIT... I'M THE CLONE?!", W/2, 470, 75, (0, 0, 0), fg=(255, 230, 40), rot=3)
            amp = int(14 * max(0, 1 - (u - .5) * 5))
        vignette(img, 160)

    else:
        return ORIG_RENDER(seg, t, T)

    img = camera(img, full, u)
    for a_, k_ in later:
        sticker(img, *a_, **k_)
    if amp: img = shake_img(img, amp)
    return img

# ------------------------------------------------------------------ audio: música de suspense y efectos
def drone(dur, f=55):
    n = int(SR * dur); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 1.5 * t) + .3 * np.sin(2 * np.pi * f * 2.02 * t)
    return (x * (.6 + .4 * np.sin(2 * np.pi * .7 * t)) * np.minimum(1, t / .5) * np.minimum(1, (dur - t) / .5) * .18).astype(np.float32)

def heartbeat(dur, bpm=110):
    n = int(SR * dur); out = np.zeros(n, np.float32); step = 60 / bpm
    for b in np.arange(0, dur - .3, step):
        for o, a in ((0, 1), (.18, .7)):
            s = int((b + o) * SR); kk = min(n - s, int(.15 * SR)); tt = np.arange(kk) / SR
            out[s:s + kk] += (np.sin(2 * np.pi * 50 * tt) * np.exp(-tt * 25) * .5 * a).astype(np.float32)
    return out

def sting():
    n = int(SR * 1.2); t = np.arange(n) / SR
    hi = sum(np.sin(2 * np.pi * f * t + f) for f in (1250, 1330, 1410)) / 3
    return ((hi * np.exp(-t * 2.5) * .25) + m.sfx("boom")[:n] * 1.0).astype(np.float32)

def footsteps(dur, rate=9):
    n = int(SR * dur); out = np.zeros(n, np.float32)
    for b in np.arange(0, dur, 1 / rate):
        s = int(b * SR); kk = min(n - s, int(.05 * SR))
        out[s:s + kk] += (np.random.randn(kk) * np.exp(-np.arange(kk) / SR * 60) * .2).astype(np.float32)
    return out

ORIG_MIX = m.mix_audio

def mix_audio(segs, total, out_wav):
    ORIG_MIX(segs, total, out_wav)
    with wave.open(out_wav) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = a.copy(); n = len(a)
    fx = np.zeros(n, np.float32)
    def put(x, t):
        s_ = int(t * SR); e = min(n, s_ + len(x))
        if e > s_: fx[s_:e] += x[:e - s_]
    by = {s["scene"]: s for s in segs}
    s0 = by["door"]; put(m.sfx("whoosh") * .6, s0["start"]); put(sting() * .9, s0["start"] + (s0["dur"] + .2) * .38)
    s1 = by["stare"]
    for i in range(5): put(m.sfx("pop") * .9, s1["start"] + i / 5.5 * (s1["dur"] + .2))
    s2 = by["stare_b"]
    for i in range(3): put(m.sfx("pop") * .7, s2["start"] + i * (s2["dur"] + .2) / 3)
    for key in ("jobs", "jobs_b"):
        s = by[key]; put(m.sfx("pop") * .8, s["start"]); put(m.sfx("pop") * .8, s["start"] + s["dur"] / 2)
    s = by["jobs_b"]; put(m.sfx("boing") * .8, s["start"] + s["dur"] * .76)
    s = by["dance"]; put(m.sfx("ding") * .5, s["start"] + .3)
    # suspense: del clon raro al final de la persecución
    st = by["odd"]["start"]; en = by["home"]["start"]
    put(drone(en - st + .5), st)
    put(heartbeat(by["evil"]["dur"] + by["control"]["dur"] + .4), by["evil"]["start"])
    put(sting(), by["evil"]["start"] + by["evil"]["dur"] * .25)
    put(m.sfx("pop") * 1.4, by["control"]["start"] + .05)
    put(footsteps(by["home"]["start"] - by["chase"]["start"]), by["chase"]["start"])
    put(m.sfx("boom") * .8, by["chase_b"]["start"] + .8)
    put(m.sfx("boom") * 1.1, by["home"]["start"] + by["home"]["dur"] * .55)
    s = by["mirror"]; put(drone(by["tag_c"]["start"] + by["tag_c"]["dur"] - s["start"], 46) * 1.2, s["start"])
    put(m.sfx("ding") * .4, by["mirror_b"]["start"] + .2)
    s = by["flip"]; put(m.sfx("whoosh"), s["start"] + .1); put(m.sfx("boing") * .8, s["start"] + s["dur"] * .7)
    s = by["bread"]; put(m.sfx("pop"), s["start"] + s["dur"] * .45)
    s = by["chase_c"]; put(m.sfx("boing") * .7, s["start"] + .3); put(m.sfx("boing") * .7, s["start"] + .9)
    s = by["tag_c"]; put(m.sfx("ding") * .6, s["start"] + s["dur"] * .5)
    s = by["tag"]; put(sting() * 1.1, s["start"] + s["dur"] * .5)
    # ducking de los efectos bajo la voz
    voice = np.zeros(n, np.float32)
    for s in segs:
        st_ = int(s["start"] * SR); e = min(n, st_ + len(s["audio"])); voice[st_:e] += np.abs(s["audio"][:e - st_])
    talk = np.convolve(np.clip(np.convolve(voice, np.ones(2205) / 2205, "same") * 25, 0, 1), np.ones(4410) / 4410, "same")
    a += fx * (1 - .45 * talk)
    a /= max(1, np.abs(a).max() / .95)
    with wave.open(out_wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

ORIG_BUILD = m.build

def build(voice, tmp):
    segs, total = ORIG_BUILD(voice, tmp)
    print(f"duración natural: {total:.2f}s")
    if total >= TARGET:  # mínimo 1 minuto; si dura más, se deja tal cual
        return segs, total
    extra = TARGET - total; n = len(segs)
    for i, sg in enumerate(segs):  # reparte el tiempo sobrante entre las pausas
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
        sys.argv += ["--out", "clones.mp4"]
    m.main()
