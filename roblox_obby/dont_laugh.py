#!/usr/bin/env python3
"""Historia 10: DON'T LAUGH — concurso de TV (estilo THE HUNT / DON'T SAY HUSS / DON'T BLINK...).

Uso: python3 dont_laugh.py --voice ruta/en_US-ryan-high.onnx [--out dont_laugh.mp4]
"""
import math, random, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
import hunt as hn
import dont_blink as db
from dont_say import granny, CLOWN, confetti
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)
from hunt import neon_city, screen, tv_overlay, money_rain, captions_single, tint, flash, tone, crowd_roar, PINK, PURPLE, NEON, GOLD

ME = CHARS["me"]
RED = (255, 40, 40)
FLOOR = 1450

SCRIPT = [
    ("In this town, there's a TV show called Don't Laugh.", "intro", None),
    ("Seven days. If you laugh, you're out. The winner gets four million dollars.", "rules", None),
    ("Fifty people signed up. Including me.", "start", None),
    ("The host told one joke. Just one. Three people were already out.", "start_b", None),
    ("Day one. A clown walked in... and slipped on his own banana. Twenty people laughed.", "clown", None),
    ("Then the clown laughed at himself. He was out too.", "clown_b", None),
    ("Day two. A tickle machine. With feathers. Ten more were out.", "tickle", None),
    ("They tickled me for three hours. I just yawned.", "tickle_b", None),
    ("Day three. Grandma started breakdancing.", "grandma", None),
    ("Day four. A dog wearing a tiny hat. And tiny shoes.", "dog", None),
    ("The dog sneezed. Five people exploded.", "dog_b", None),
    ("Day five. The studio was totally silent... and then somebody farted.", "fart", None),
    ("Everyone laughed. Except me. I didn't move a single muscle.", "serious", None),
    ("Even the host laughed. They had to hire a new host.", "serious_b", None),
    ("Day seven. I was the last one. I won four million dollars!", "win", None),
    ("I tried to smile... but I couldn't.", "stuck", None),
    ("Seven days without laughing... and my face forgot how.", "stuck_b", None),
    ("I went to a doctor. He told me his best joke. Nothing.", "doctor", None),
    ("Now I'm rich. But I look like this. Forever.", "end", None),
    ("Even when I scream:", "end_huss", "solo", 6),
]

DAY = {"start_b": "DAY 0", "clown_b": "DAY 1", "tickle_b": "DAY 2", "dog_b": "DAY 4", "serious_b": "DAY 5", "doctor": "DAY 8",
       "start": "DAY 0", "clown": "DAY 1", "tickle": "DAY 2", "grandma": "DAY 3", "dog": "DAY 4", "fart": "DAY 5",
       "serious": "DAY 5", "win": "DAY 7", "stuck": "DAY 7", "stuck_b": "DAY 7"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.15, (.5, .45), (.5, .4)),
    "start": (1.2, 1.0, (.5, .6), (.5, .58)), "clown": (1.0, 1.35, (.5, .6), (.45, .66)),
    "tickle": (1.2, 1.0, (.4, .62), (.5, .6)), "grandma": (1.0, 1.3, (.5, .6), (.5, .64)),
    "dog": (1.3, 1.0, (.5, .68), (.5, .6)), "fart": (1.0, 1.25, (.5, .58), (.5, .52)),
    "serious": (1.0, 1.6, (.5, .6), (.5, .62)), "win": (1.2, 1.0, (.5, .55), (.5, .5)),
    "stuck": (1.0, 1.0, (.5, .5), (.5, .5)), "stuck_b": (1.1, 1.0, (.5, .5), (.5, .5)),
    "end": (1.0, 1.2, (.5, .55), (.5, .6)),
    "start_b": (1.0, 1.25, (.5, .58), (.5, .62)), "clown_b": (1.3, 1.6, (.45, .66), (.5, .68)),
    "tickle_b": (1.0, 1.5, (.6, .6), (.77, .6)), "dog_b": (1.0, 1.4, (.5, .62), (.35, .66)),
    "serious_b": (1.2, 1.0, (.5, .6), (.5, .6)), "doctor": (1.2, 1.0, (.5, .5), (.5, .5)), "end_huss": (1.15, 1.0, (.5, .55), (.5, .5)),
}

# ------------------------------------------------------------------ piezas
def audience(d, T, n_out=0, laughing=(), face="flat", seed=0):
    """Gradas con 16 concursantes; los n_out primeros están eliminados (asiento vacío con X)."""
    k = 0
    for r, (y, s, cnt) in enumerate([(1050, 22, 9), (1240, 28, 7)]):
        block(d, [0, y - 10, W, y + 30], (70, 40, 100))
        for j in range(cnt):
            x = 70 + j * (W - 140) / (cnt - 1)
            if k < n_out:
                d.line([x - s, y - s * 3, x + s, y - s], fill=RED, width=6); d.line([x + s, y - s * 3, x - s, y - s], fill=RED, width=6)
            else:
                lf = k in laughing
                bob = abs(math.sin(T * 12 + k)) * 18 if lf else 0
                avatar(d, x, y - bob, s, npc(1200 + k + seed), T + k, 0, "up" if lf else "down", "laugh" if lf else face)
            k += 1

def banana(d, x, y, s):
    d.arc([x - s, y - s * .6, x + s, y + s * .6], 20, 160, fill=(250, 220, 40), width=max(6, int(s * .35)))

def tickle_machine(d, x, y, T):
    block(d, [x - 140, y - 320, x + 140, y - 40], (150, 160, 180))
    d.rectangle([x - 100, y - 280, x + 100, y - 200], fill=(20, 30, 40))
    d.text((x, y - 240), "TICKLE 3000", font=font(30), fill=(80, 255, 140), anchor="mm")
    for e in (-1, 1):
        for q in range(2):
            a = T * 8 + q * 1.5 + (0 if e > 0 else 1)
            ax, ay = x + e * 140, y - 220 + q * 90
            ex, ey = ax + e * (160 + 40 * math.sin(a)), ay + 60 * math.cos(a)
            d.line([ax, ay, ex, ey], fill=(110, 120, 140), width=14)
            for f in range(5):  # pluma
                d.line([ex, ey, ex + e * 50 + 10 * math.sin(a + f), ey - 30 + f * 15], fill=(255, 140, 200), width=5)

def dog(d, x, y, s, T):
    bob = abs(math.sin(T * 6)) * 10
    col = (200, 150, 90)
    for lx in (-1, -.4, .4, 1):
        block(d, [x + lx * s - s * .15, y - s * .9, x + lx * s + s * .15, y], col)
        block(d, [x + lx * s - s * .22, y - s * .2, x + lx * s + s * .22, y], (220, 40, 60))  # zapatitos
    block(d, [x - s * 1.3, y - s * 1.7 - bob, x + s * 1.3, y - s * .8 - bob], col)
    hx = x + s * 1.3
    block(d, [hx - s * .2, y - s * 2.6 - bob, hx + s * .9, y - s * 1.6 - bob], col)
    d.ellipse([hx + s * .6, y - s * 2.2 - bob, hx + s * .95, y - s * 1.95 - bob], fill=(30, 20, 20))
    d.ellipse([hx + s * .2, y - s * 2.4 - bob, hx + s * .35, y - s * 2.25 - bob], fill=(20, 20, 20))
    d.polygon([(hx - s * .1, y - s * 2.6 - bob), (hx - s * .4, y - s * 2.0 - bob), (hx + s * .1, y - s * 2.2 - bob)], fill=(150, 100, 60))
    d.rectangle([hx + s * .05, y - s * 2.95 - bob, hx + s * .45, y - s * 2.6 - bob], fill=(30, 30, 40))  # sombrerito
    d.rectangle([hx - s * .05, y - s * 2.65 - bob, hx + s * .55, y - s * 2.58 - bob], fill=(30, 30, 40))
    wag = math.sin(T * 14) * s * .4
    d.line([x - s * 1.3, y - s * 1.5 - bob, x - s * 1.9, y - s * 2.1 - bob + wag], fill=col, width=max(4, int(s * .2)))

def fart_cloud(d, x, y, r, a):
    for q, (dx, dy, rr) in enumerate([(0, 0, 1), (-.7, .2, .7), (.7, .15, .75), (.2, -.5, .6), (-.4, -.4, .5)]):
        rrr = r * rr
        d.ellipse([x + dx * r - rrr, y + dy * r - rrr, x + dx * r + rrr, y + dy * r + rrr], fill=(150, 200, 90, int(200 * a)))

def stuck_face(img, T, strain=0., glitch=False):
    """Primer plano gigante: cara completamente seria, intentando sonreír."""
    sky(img, (40, 20, 70), (110, 40, 140)); d = ImageDraw.Draw(img)
    s = 330
    top = avatar(d, W / 2, 2480, s, ME, T, 0, "down", "flat", 0)
    hs = s * 1.25
    if strain > 0:
        wob = 8 * math.sin(T * 30) * strain
        d.line([W / 2 - s * .3, top + hs * .72 + wob, W / 2 + s * .3, top + hs * .72 - wob], fill=(15, 15, 15), width=int(s * .09))
        for e in (-1, 1):  # gotas de sudor / esfuerzo
            d.ellipse([W / 2 + e * hs * .45 - 14, top + hs * .1 + (T * 80 % 60), W / 2 + e * hs * .45 + 14, top + hs * .1 + 30 + (T * 80 % 60)], fill=(120, 200, 255))
            for q in range(3):
                d.line([W / 2 + e * (hs * .55 + q * 25), top + hs * .3, W / 2 + e * (hs * .62 + q * 25), top + hs * .4], fill=(255, 255, 255), width=6)
    return d, top

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    full = seg["scene"]
    sc = {"start_b": "start", "clown_b": "clown", "tickle_b": "tickle", "dog_b": "dog", "serious_b": "serious",
          "doctor": "stuck_b"}.get(full, full)
    dur = seg["dur"] + .2; u = min(1, t / dur)
    if full in ("clown_b",): u = 1.0
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]

    if sc in ("intro", "rules"):
        d = neon_city(img, T)
        if sc == "intro":
            p = ease(min(1, t / .5))
            screen(d, box, [("DON'T", 120, (255, 255, 255)), ("LAUGH", int(200 * (.6 + .4 * p)), NEON), ("THE TV SHOW", 50, GOLD)])
            avatar(d, W / 2, 1650, 70, ME, T, 0, "down", "flat")
        else:
            third = min(2, int(u * 3))
            screen(d, box, [[("7 DAYS", 190, (255, 255, 255))], [("LAUGH", 140, NEON), ("= OUT", 160, RED)],
                            [("PRIZE", 80, (255, 255, 255)), ("$4,000,000", 130, (90, 220, 90))]][third])
            if third == 2: money_rain(d, T)
        ovl.append(None)

    elif sc in ("start", "clown", "tickle", "grandma", "dog", "fart", "serious"):
        d = db.studio(img, T)
        hn_ = {"start": 0, "clown": 0, "tickle": 6, "grandma": 9, "dog": 10, "fart": 11, "serious": 11}[sc]
        if sc == "start":
            audience(d, T, 0, face="smile")
            avatar(d, W / 2, 1650, 70, ME, T, 0, "down", "flat")
            if full == "start_b":
                from dont_say import host
                host(d, 250, 1650, 60, T, "out", "laugh", look=1)
                stk("ONE JOKE", W / 2, 400, 120, (255, 220, 40), fg=(30, 30, 40), rot=-5)
                if u > .5: stk("-3", W / 2, 600, 150, RED, rot=5)
            else:
                stk("50 PLAYERS", W / 2, 400, 120, PINK, rot=-5)
        elif sc == "clown":
            out = u > .6
            audience(d, T, 6 if out and u > .8 else 0, laughing=tuple(range(0, 9)) if out else ())
            slip = ease(max(0, (u - .35) / .25))
            cx = 380 + 120 * slip
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            top = avatar(ld, cx, 1650, 64, CLOWN, T, 0, "up" if slip > 0 else "out", "shock" if slip > 0 else "laugh")
            ld.ellipse([cx - 22, top + 45, cx + 22, top + 89], fill=RED)
            lay = lay.rotate(-80 * slip, center=(cx, 1650), resample=Image.BICUBIC)
            img.alpha_composite(lay); d = ImageDraw.Draw(img)
            banana(d, 470, 1660, 40)
            avatar(d, 830, 1650, 66, ME, T, 0, "down", "flat", look=-1)
            if full == "clown_b":
                stk("HAHAHA", cx + 80, 1020, 100, (255, 220, 40), rot=-6 + 6 * math.sin(T * 10))
                stk("CLOWN: OUT", W / 2, 400, 120, RED, rot=4)
            else:
                if slip > .5: stk("SLIP", cx, 1000, 120, (250, 220, 40), fg=(255, 255, 255), rot=-10)
                if out: stk("-20", W / 2, 400, 150, RED, rot=4)
        elif sc == "tickle":
            audience(d, T, hn_, laughing=(7, 8, 12) if u > .5 else ())
            tickle_machine(d, 360, 1650, T)
            avatar(d, 830, 1650, 66, ME, T, 0, "down", "flat", look=-1)
            if full == "tickle_b":
                stk("3 HOURS LATER", W / 2, 400, 100, (30, 30, 40), fg=(255, 255, 255), rot=-4)
                if u > .5: stk("*YAWN*", 830, 1050, 110, (200, 200, 255), rot=6)
            else:
                stk("TICKLE MACHINE", W / 2, 400, 100, (255, 140, 200), rot=-4)
                if u > .6: stk("-10", W / 2, 600, 130, RED, rot=5)
        elif sc == "grandma":
            audience(d, T, hn_, laughing=(9, 13) if u > .5 else ())
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            granny(ld, 380, 1650, 60, T, "up", "laugh")
            lay = lay.rotate(180 + 40 * math.sin(T * 6), center=(380, 1450), resample=Image.BICUBIC)
            img.alpha_composite(lay); d = ImageDraw.Draw(img)
            for q in range(4):
                a = T * 6 + q * 1.57
                d.arc([380 - 160, 1450 - 160, 380 + 160, 1450 + 160], math.degrees(a), math.degrees(a) + 40, fill=(255, 255, 255), width=6)
            avatar(d, 830, 1650, 66, ME, T, 0, "down", "flat", look=-1)
            stk("BREAKDANCE GRANDMA", W / 2, 400, 85, (170, 90, 160), rot=-4, scale=1 + .05 * math.sin(T * 10))
        elif sc == "dog":
            audience(d, T, hn_, laughing=(10, 14) if u > .5 else ())
            dog(d, 360, 1650, 85, T)
            avatar(d, 830, 1650, 66, ME, T, 0, "down", "flat", look=-1)
            if full == "dog_b":
                if u > .3: stk("ACHOO!", 470, 1020, 120, (170, 230, 255), rot=-8); amp = int(10 * max(0, 1 - (u - .3) * 4))
                if u > .55: stk("-5", W / 2, 400, 150, RED, rot=4)
            else:
                stk("TINY HAT", W / 2, 400, 120, (30, 30, 40), rot=-4)
                if u > .5: stk("TINY SHOES", W / 2, 600, 110, (220, 40, 60), rot=4)
        elif sc == "fart":
            boom = u > .55
            audience(d, T, hn_, face="flat")
            avatar(d, W / 2, 1650, 66, ME, T, 0, "down", "flat")
            if not boom:
                stk("SILENCE...", W / 2, 400, 110, (30, 30, 40), fg=(255, 255, 255), rot=-3)
            else:
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                fart_cloud(ImageDraw.Draw(lay), 260, 1250, 130 * min(1, (u - .55) * 4 + .3), 1)
                img.alpha_composite(lay)
                stk("PFFFT", 260, 1000, 140, (150, 200, 90), fg=(255, 255, 255), rot=-8, scale=1.2 - .2 * min(1, (u - .55) * 4))
                amp = int(14 * max(0, 1 - (u - .55) * 4))
        else:  # serious: todos se ríen menos él
            audience(d, T, 0, laughing=tuple(range(16)))
            for i, x in enumerate([150, 330, 750, 930]):
                avatar(d, x, 1650 - abs(math.sin(T * 12 + i)) * 30, 50, npc(1300 + i), T, 0, "up", "laugh", look=1 if x < W / 2 else -1)
            avatar(d, W / 2, 1650, 72, ME, T, 0, "down", "flat")
            if full == "serious_b":
                from dont_say import host
                host(d, 900, 1700 - abs(math.sin(T * 12)) * 30, 60, T, "up", "laugh", look=-1)
                stk("HOST: OUT", W / 2, 400, 120, RED, rot=-4)
                if u > .55: stk("NEW HOST WANTED", W / 2, 600, 80, (255, 255, 255), fg=(30, 30, 40), rot=4)
            elif u > .4: stk("NOT A SINGLE MUSCLE", W / 2, 400, 85, (30, 30, 40), fg=(255, 255, 255), rot=-3)
            for q in range(5):
                stk("HAHA", 120 + q * 210, 620 + (q % 2) * 120, 70, (255, 220, 40), rot=-10 + 5 * q)
        ovl.append(DAY[full])

    elif sc == "win":
        sky(img, (255, 60, 200), (120, 30, 200)); d = ImageDraw.Draw(img)
        for q in range(16):
            a = q * math.pi / 8 + T * .7
            d.polygon([(W / 2, 1000), (W / 2 + 2300 * math.cos(a), 1000 + 2300 * math.sin(a)),
                       (W / 2 + 2300 * math.cos(a + .18), 1000 + 2300 * math.sin(a + .18))], fill=(255, 120, 230))
        confetti(d, T)
        avatar(d, W / 2, 1650, 95, ME, T, 0, "up", "flat")
        block(d, [W / 2 - 330, 1330, W / 2 + 330, 1510], (255, 255, 255))  # cheque gigante
        d.text((W / 2, 1390), "PAY TO: HUSS BOY", font=font(40), fill=(40, 40, 40), anchor="mm")
        d.text((W / 2, 1460), "$4,000,000", font=font(70), fill=(40, 160, 60), anchor="mm")
        stk("WINNER", W / 2, 380, 170, GOLD, fg=(255, 255, 255), rot=-5, scale=1 + .06 * math.sin(T * 10))
        ovl.append(DAY[sc])

    elif sc in ("stuck", "stuck_b"):
        d, top = stuck_face(img, T, strain=1.0 if sc == "stuck" else .4)
        if sc == "stuck":
            stk("SMILE.EXE", W / 2, 330, 120, (30, 30, 40), fg=(80, 255, 140), rot=-3)
            if u > .5: stk("NOT RESPONDING", W / 2, 520, 100, RED, rot=4, scale=1 + .05 * math.sin(T * 12))
        elif full == "doctor":
            stk("DOCTOR'S BEST JOKE", W / 2, 330, 90, (255, 255, 255), fg=(40, 120, 200), rot=-4)
            if u > .55: stk("NOTHING", W / 2, 520, 130, (30, 30, 40), fg=(255, 255, 255), rot=4)
        else:
            stk("FACE FORGOT HOW", W / 2, 330, 110, PURPLE, rot=-4)
            if int(T * 8) % 7 == 0: tint(img, (255, 255, 255), 60)
        ovl.append(DAY[full])

    elif sc in ("end", "end_huss"):
        sky(img, (120, 200, 255), (255, 240, 200)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1500, W, H], fill=(120, 190, 90))
        for r in range(7):  # montaña de dinero
            for q in range(8 - r):
                x = W / 2 - (7 - r) * 55 + q * 110; y = 1650 - r * 50
                d.rectangle([x - 50, y - 22, x + 50, y + 22], fill=(90, 200, 90), outline=(30, 110, 40), width=3)
        money_rain(d, T, 20)
        z = 1 + .15 * hit
        top = avatar(d, W / 2, 1650 - 7 * 50 + 30, 80 * z, ME, T, 0, "out" if hit > .1 else "down", "flat")
        if sc == "end":
            stk("RICH", W / 2, 380, 150, (90, 200, 90), rot=-5)
            if u > .5: stk("FOREVER", W / 2, 580, 120, (30, 30, 40), fg=(255, 255, 255), rot=4)
        else:
            if 0 <= k < seg["nh"]:
                for j in range(k + 1):
                    stk("HUSS", 180 + (j * 191) % 720, 360 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                        rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
            else:
                stk("SAME FACE", W / 2, 400, 120, (30, 30, 40), fg=(255, 255, 255), rot=-4)
            amp = int(20 * hit)
        ovl.append(None)

    else:
        return ORIG_RENDER(seg, t, T)

    img = camera(img, full if full in CAMS else sc, min(1, t / dur))
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
def laugh_track(dur, n_people=6):
    n = int(SR * dur); out = np.zeros(n, np.float32); rnd = random.Random(1)
    for p in range(n_people):
        f0 = rnd.uniform(180, 420); rate = rnd.uniform(5, 8); off = rnd.uniform(0, .3)
        t = np.arange(n) / SR
        env = (np.sin(2 * np.pi * rate * (t + off)) > .2).astype(np.float32) * np.minimum(1, t / .1) * np.minimum(1, (dur - t) / .3)
        x = np.sign(np.sin(2 * np.pi * f0 * t)) * .5 + np.random.randn(n) * .3
        out += (x * env * .035).astype(np.float32)
    return out

def fart():
    n = int(SR * .9); t = np.arange(n) / SR
    f = 90 + 40 * np.sin(2 * np.pi * 7 * t) + 30 * np.random.randn(n) * .1
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.minimum(1, t / .02) * np.exp(-t * 2.5)
    return (x * .3).astype(np.float32)

def buzzer(dur=.5):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * 110 * t)) * .18 * np.minimum(1, (dur - t) / .1)).astype(np.float32)

def error_beep():
    return np.concatenate([tone(300, .15, .3), tone(200, .25, .3)])

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
    s = by["clown"]; put(m.sfx("boing"), s["start"] + (s["dur"] + .2) * .4); put(laugh_track(1.6), s["start"] + (s["dur"] + .2) * .6)
    put(buzzer(), s["start"] + (s["dur"] + .2) * .8)
    s = by["tickle"]; put(laugh_track(1.2, 3), s["start"] + (s["dur"] + .2) * .5); put(buzzer(), s["start"] + (s["dur"] + .2) * .65)
    s = by["grandma"]; put(m.sfx("whoosh"), s["start"] + .2); put(laugh_track(1.0, 2), s["start"] + (s["dur"] + .2) * .55)
    s = by["dog"]; put(laugh_track(1.0, 2), s["start"] + (s["dur"] + .2) * .55)
    s = by["fart"]; put(fart(), s["start"] + (s["dur"] + .2) * .55)
    s = by["serious"]; put(laugh_track(s["dur"] + .2, 10), s["start"])
    s = by["win"]; put(crowd_roar(1.5) * .7, s["start"]); put(m.sfx("ding"), s["start"])
    s = by["stuck"]; put(error_beep(), s["start"] + (s["dur"] + .2) * .5)
    s = by["stuck_b"]; put(error_beep(), s["start"] + .3)
    s = by["end"]; put(m.sfx("ding") * .5, s["start"] + .3)
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
db.STUDIO_TITLE = "DON'T LAUGH"
hn.SHOW = "DON'T LAUGH"
hn.TICKER = "  LIVE · DON'T LAUGH · 7 DAYS · $4,000,000 · LAUGH AND YOU'RE OUT · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "dont_laugh.mp4"]
    m.main()
