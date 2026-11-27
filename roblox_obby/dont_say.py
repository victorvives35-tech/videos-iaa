#!/usr/bin/env python3
"""Historia 6: DON'T SAY HUSS — concurso de TV (mismo estilo que THE HUNT).

Uso: python3 dont_say.py --voice ruta/en_US-ryan-high.onnx [--out dont_say.mp4]
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
GRANNY = dict(head=(255, 205, 160), torso=(170, 90, 160), legs=(120, 70, 120), hair=None, logo=None)
HOST = dict(head=(255, 205, 160), torso=(30, 30, 40), legs=(30, 30, 40), hair=(240, 200, 60), logo=(255, 40, 200))
CLOWN = dict(head=(255, 240, 240), torso=(255, 220, 40), legs=(60, 140, 230), hair=None, logo=(255, 40, 40))

SCRIPT = [
    ("In this town, there's a TV show called Don't Say Huss.", "intro", None),
    ("The rules are simple. Thirty days. If you say huss... you're out.", "rules", None),
    ("The winner gets ten million dollars.", "prize", None),
    ("One thousand people signed up. Including me. The guy who says huss every five seconds.", "signup", None),
    ("Day one. Two hundred people were out before breakfast.", "elim", None),
    ("There were cameras everywhere. In the bakery. In the bathroom. Inside my cereal.", "cams", None),
    ("Day five. A clown came to town and asked everyone: what's your favorite word?", "clown", None),
    ("Three hundred people said it.", "elim_b", None),
    ("Day twelve. I almost said it in my sleep. So I taped my mouth shut.", "tape", None),
    ("Day twenty. Only ten people left.", "elim_c", None),
    ("Then my best friend sneezed. It sounded a little bit like huss.", "sneeze", None),
    ("They kicked him out anyway.", "sneeze_b", None),
    ("Day twenty nine. Only two people left. Me... and my grandma.", "final_two", None),
    ("Day thirty. The last minute.", "countdown", None),
    ("Three. Two. One.", "final_count", None),
    ("ZERO! I WON! I was so happy, I screamed:", "win", "solo", 6),
    ("Then the host checked the clock. It still said eleven fifty nine.", "clock", None),
    ("I was out. Grandma won ten million dollars.", "granny_win", None),
    ("She grabbed the microphone, looked at the camera... and said:", "granny_mic", "baby", 3),
    ("The show was over. She was already rich.", "end", None),
]

DAY = {"elim": "DAY 1 OF 30", "cams": "DAY 1 OF 30", "clown": "DAY 5 OF 30", "elim_b": "DAY 5 OF 30",
       "tape": "DAY 12 OF 30", "elim_c": "DAY 20 OF 30", "sneeze": "DAY 20 OF 30", "sneeze_b": "DAY 20 OF 30",
       "final_two": "DAY 29 OF 30", "countdown": "DAY 30 OF 30", "final_count": "DAY 30 OF 30", "win": "DAY 30 OF 30",
       "clock": "DAY 30 OF 30"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.2, (.5, .45), (.5, .4)),
    "prize": (1.0, 1.15, (.5, .5), (.5, .55)), "signup": (1.2, 1.0, (.3, .6), (.7, .6)),
    "elim": (1.0, 1.15, (.5, .45), (.5, .45)), "cams": (1.0, 1.0, (.5, .5), (.5, .5)),
    "clown": (1.0, 1.3, (.5, .55), (.55, .5)), "elim_b": (1.15, 1.0, (.5, .45), (.5, .45)),
    "tape": (1.0, 1.5, (.5, .6), (.45, .6)), "elim_c": (1.0, 1.2, (.5, .45), (.5, .45)),
    "sneeze": (1.0, 1.4, (.5, .58), (.4, .55)), "sneeze_b": (1.2, 1.0, (.4, .6), (.5, .6)),
    "final_two": (1.0, 1.1, (.5, .5), (.5, .5)), "countdown": (1.0, 1.2, (.5, .45), (.5, .42)),
    "final_count": (1.0, 1.0, (.5, .5), (.5, .5)), "win": (1.2, 1.0, (.5, .55), (.5, .5)),
    "clock": (1.0, 1.25, (.5, .5), (.5, .45)), "granny_win": (1.0, 1.2, (.5, .55), (.5, .55)),
    "granny_mic": (1.3, 1.6, (.5, .5), (.5, .48)), "end": (1.0, 1.25, (.5, .55), (.5, .6)),
}

# ------------------------------------------------------------------ piezas
def granny(d, x, y, s, t, arms="down", face="smile", look=0, shades=False):
    top = avatar(d, x, y, s, GRANNY, t, 0, arms, face, look)
    d.ellipse([x - s * .7, top - s * 1.1, x + s * .7, top + s * .2], fill=(200, 200, 205), outline=(120, 120, 125), width=3)
    hs = s * 1.25
    for e in (-1, 1):
        cx, cy = x + e * s * .28 + s * .2 * look, top + hs * .42
        if shades:
            d.rectangle([cx - s * .3, cy - s * .18, cx + s * .3, cy + s * .2], fill=(10, 10, 10))
        else:
            d.ellipse([cx - s * .3, cy - s * .3, cx + s * .3, cy + s * .3], outline=(20, 20, 20), width=max(3, int(s * .08)))
    if shades: d.line([x - s * .3, top + hs * .42, x + s * .3, top + hs * .42], fill=(10, 10, 10), width=4)
    return top

def host(d, x, y, s, t, arms="out", face="smile", look=0):
    top = avatar(d, x, y, s, HOST, t, 0, arms, face, look)
    mx = x + (s * 2.6 if look >= 0 else -s * 2.6)
    d.rectangle([mx - s * .12, y - s * 3.4, mx + s * .12, y - s * 2.6], fill=(40, 40, 40))
    d.ellipse([mx - s * .25, y - s * 3.75, mx + s * .25, y - s * 3.25], fill=(90, 90, 100))
    return top

def tv_cam(d, x, y, s, t):
    block(d, [x - s, y - s * .6, x + s, y + s * .6], (40, 40, 50))
    d.ellipse([x - s * .5 + s, y - s * .45, x + s * .4 + s, y + s * .45], fill=(20, 20, 30), outline=(120, 120, 140), width=3)
    d.ellipse([x - s * .8, y - s * .5, x - s * .55, y - s * .25], fill=RED if int(t * 3) % 2 else (90, 0, 0))

def face_grid(d, box, total, out, t, seed=0):
    """Rejilla de concursantes en pantalla; 'out' se tachan con una X roja."""
    x0, y0, x1, y1 = box
    cols, rows = 8, 6
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    rnd = random.Random(seed)
    order = list(range(cols * rows)); rnd.shuffle(order)
    gone = set(order[:out])
    for i in range(cols * rows):
        cx, cy = x0 + (i % cols + .5) * cw, y0 + (i // cols + .5) * ch
        col = npc(500 + i)["torso"]
        d.rectangle([cx - cw * .4, cy - ch * .4, cx + cw * .4, cy + ch * .4], fill=(255, 205, 160))
        d.rectangle([cx - cw * .4, cy + ch * .15, cx + cw * .4, cy + ch * .4], fill=col)
        d.ellipse([cx - cw * .2 - 4, cy - ch * .12 - 4, cx - cw * .2 + 4, cy - ch * .12 + 4], fill=(20, 20, 20))
        d.ellipse([cx + cw * .2 - 4, cy - ch * .12 - 4, cx + cw * .2 + 4, cy - ch * .12 + 4], fill=(20, 20, 20))
        if i in gone:
            d.rectangle([cx - cw * .4, cy - ch * .4, cx + cw * .4, cy + ch * .4], fill=(60, 0, 0, 160))
            d.line([cx - cw * .35, cy - ch * .35, cx + cw * .35, cy + ch * .35], fill=RED, width=8)
            d.line([cx + cw * .35, cy - ch * .35, cx - cw * .35, cy + ch * .35], fill=RED, width=8)

def confetti(d, T, n=90, seed=3):
    rnd = random.Random(seed)
    for i in range(n):
        x0 = rnd.uniform(0, W); sp = rnd.uniform(300, 700)
        y = (rnd.uniform(-H, 0) + T * sp) % (H + 100) - 50
        d.rectangle([x0, y, x0 + 18, y + 30], fill=rnd.choice([PINK, GOLD, (60, 200, 255), (120, 255, 120)]))

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    sc = seg["scene"]; dur = seg["dur"] + .2; u = min(1, t / dur)
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]

    if sc in ("intro", "rules", "prize"):
        d = neon_city(img, T)
        if sc == "intro":
            p = ease(min(1, t / .5))
            screen(d, box, [("DON'T SAY", 110, (255, 255, 255)), ("HUSS", int(240 * (.6 + .4 * p)), NEON),
                            ("THE TV SHOW", 50, GOLD)])
            host(d, 300, GY + 40, 46, T, "out", "smile", look=1)
        elif sc == "rules":
            third = min(2, int(u * 3))
            lines = [[("RULE #1", 80, GOLD), ("30 DAYS", 190, (255, 255, 255))],
                     [("RULE #2", 80, GOLD), ("DON'T SAY", 120, (255, 255, 255)), ("HUSS", 150, NEON)],
                     [("SAY IT", 110, (255, 255, 255)), ("= OUT", 190, RED)]][third]
            screen(d, box, lines)
            host(d, 300, GY + 40, 46, T, "up", "laugh", look=1)
        else:
            screen(d, box, [("PRIZE", 80, (255, 255, 255)), ("$10,000,000", 120, (90, 220, 90))])
            money_rain(d, T)
            for i in range(5):
                avatar(d, 140 + i * 200, GY + 40 - abs(math.sin(T * 7 + i)) * 50, 36, npc(i + 520), T, 0, "up", "laugh")
        ovl.append(None)

    elif sc == "signup":
        d = neon_city(img, T, cam=t * 300)
        d.rectangle([0, 1000, W, 1090], fill=PINK); d.text((W / 2, 1045), "SIGN UP HERE", font=font(56), fill=(255, 255, 255), anchor="mm")
        for i in range(9):  # cola de concursantes con dorsales
            x = (i * 150 - t * 120) % (W + 300) - 150
            avatar(d, x, GY + 40, 38, npc(530 + i), T + i, .6, "down", "smile", look=1)
            d.rectangle([x - 26, GY + 40 - 140, x + 26, GY + 40 - 105], fill=(255, 255, 255))
            d.text((x, GY + 40 - 122), str(100 + i * 37), font=font(20), fill=(20, 20, 20), anchor="mm")
        top = avatar(d, W / 2, GY + 80, 66, ME, T, 0, "down", "smile")
        d.rectangle([W / 2 - 50, GY + 80 - 240, W / 2 + 50, GY + 80 - 180], fill=(255, 255, 255))
        d.text((W / 2, GY + 80 - 210), "#999", font=font(34), fill=RED, anchor="mm")
        if u > .55:
            stk("SAYS HUSS EVERY 5 SECONDS", W / 2, 420, 66, RED, rot=-3, scale=1 + .04 * math.sin(T * 10))
        ovl.append(None)

    elif sc in ("elim", "elim_b", "elim_c"):
        d = neon_city(img, T)
        start, end = {"elim": (1000, 800), "elim_b": (800, 500), "elim_c": (500, 10)}[sc]
        cnt = int(start + (end - start) * ease(min(1, u / .7)))
        frac = 1 - cnt / 1000
        d.rectangle([90, 330, 990, 1180], fill=(15, 10, 35), outline=NEON, width=8)
        face_grid(d, [120, 360, 960, 980], 48, int(48 * frac), T, seed=7)
        d.rectangle([90, 1000, 990, 1180], fill=PURPLE)
        d.text((W / 2, 1090), f"REMAINING: {cnt}", font=font(84), fill=(255, 255, 255), anchor="mm")
        if int(T * 4) % 2 and u < .7: tint(img, RED, 30)
        stk("ELIMINATED", W / 2, 230, 100, RED, rot=-4, scale=1 + .06 * math.sin(T * 12))
        ovl.append(DAY[sc])

    elif sc == "cams":
        third = min(2, int(u * 3))
        if third == 0:  # panadería
            sky(img, (255, 225, 180), (240, 190, 140)); d = ImageDraw.Draw(img)
            for j in range(7):
                d.ellipse([90 + j * 135, 800, 190 + j * 135, 860], fill=(200, 130, 60), outline=(90, 50, 20), width=4)
            d.rectangle([0, 1450, W, H], fill=(210, 180, 140))
            avatar(d, W / 2, GY, 64, ME, T, 0, "down", "flat")
            tv_cam(d, 860, 500, 70, T)
            stk("BAKERY", W / 2, 360, 100, (200, 130, 60), rot=-4)
        elif third == 1:  # baño
            sky(img, (200, 235, 240), (170, 215, 225)); d = ImageDraw.Draw(img)
            for yy in range(0, 1450, 110):
                for xx in range(0, W, 110):
                    d.rectangle([xx + 4, yy + 4, xx + 106, yy + 106], fill=(220, 245, 248))
            d.rectangle([0, 1450, W, H], fill=(150, 120, 100))
            block(d, [W / 2 - 120, 1250, W / 2 + 120, 1450], (250, 250, 250))
            avatar(d, W / 2, 1300, 60, ME, T, 0, "down", "shock")
            tv_cam(d, 220, 480, 70, T)
            stk("BATHROOM?!", W / 2, 360, 100, (60, 160, 200), rot=4)
        else:  # dentro de los cereales
            sky(img, (255, 240, 200), (255, 220, 160)); d = ImageDraw.Draw(img)
            d.chord([140, 900, 940, 1500], 0, 180, fill=(240, 240, 250), outline=(120, 120, 140), width=8)
            d.ellipse([140, 1100, 940, 1300], fill=(250, 250, 240))
            rnd = random.Random(5)
            for q in range(30):
                cx, cy = rnd.uniform(220, 860), rnd.uniform(1130, 1270)
                d.ellipse([cx - 22, cy - 14, cx + 22, cy + 14], fill=(230, 160, 60), outline=(150, 90, 30), width=3)
            tv_cam(d, W / 2, 1180 - 30 * abs(math.sin(T * 3)), 60, T)
            stk("IN MY CEREAL", W / 2, 420, 110, (230, 160, 60), rot=-5, scale=1 + .05 * math.sin(T * 10))
        if (u * 3) % 1 < .05: flash(img, .6)
        ovl.append(DAY[sc])

    elif sc == "clown":
        d = town(img, T)
        cx = W / 2 + 40 * math.sin(T * 2)
        top = avatar(d, cx, GY + 30, 72, CLOWN, T, 0, "out", "laugh")
        d.ellipse([cx - 25, top + 40, cx + 25, top + 90], fill=RED)  # nariz
        for q, col in enumerate([RED, (255, 160, 40), GOLD, (90, 200, 90), (60, 160, 255)]):
            d.ellipse([cx - 110 + q * 45, top - 60, cx - 40 + q * 45, top + 10], fill=col)  # pelo arcoíris
        for q in range(3):  # globos
            bx = 200 + q * 330; by = 600 + 40 * math.sin(T * 2 + q)
            d.ellipse([bx - 60, by - 80, bx + 60, by + 80], fill=[RED, PINK, (60, 160, 255)][q])
            d.line([bx, by + 80, bx, by + 300], fill=(60, 60, 60), width=3)
        for i, x in enumerate([110, 290, 800, 980]):
            avatar(d, x, GY + 60, 36, npc(560 + i), T, 0, "down", "smile", look=1 if x < W / 2 else -1)
        if u > .5:
            stk("FAVORITE WORD?", W / 2, 360, 100, (255, 255, 255), fg=(20, 20, 20), rot=-4, scale=1 + .05 * math.sin(T * 10))
        ovl.append(DAY[sc])

    elif sc == "tape":
        sky(img, (20, 20, 60), (60, 40, 110)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1450, W, H], fill=(90, 60, 50))
        block(d, [120, 1150, 960, 1450], (90, 140, 220))  # cama
        block(d, [120, 1050, 380, 1180], (250, 250, 250))  # almohada
        d.ellipse([780, 200, 940, 360], fill=(250, 250, 220))
        top = avatar(d, 260, 1500, 60, ME, T, 0, "down", "flat")
        if u > .45:  # cinta en la boca
            hs = 60 * 1.25
            d.line([260 - 55, top + hs * .6, 260 + 55, top + hs * .85], fill=(200, 200, 200), width=22)
            d.line([260 - 55, top + hs * .85, 260 + 55, top + hs * .6], fill=(200, 200, 200), width=22)
            stk("TAPED", W / 2, 420, 140, (200, 200, 200), fg=(40, 40, 40), rot=5)
        else:
            for q in range(3):
                zx, zy = 380 + q * 70, 900 - ((T * 120 + q * 60) % 200)
                d.text((zx, zy), "z", font=font(60 + q * 15), fill=(255, 255, 255), anchor="mm")
            stk("ALMOST...", W / 2, 420, 110, RED, rot=-4)
        ovl.append(DAY[sc])

    elif sc in ("sneeze", "sneeze_b"):
        sky(img, (20, 10, 50), (120, 30, 120)); d = ImageDraw.Draw(img)
        d.rectangle([0, 1450, W, H], fill=(60, 40, 80)); d.rectangle([0, 1450, W, 1470], fill=PINK)
        for i, x in enumerate([180, 400, 680, 900]):  # podios
            block(d, [x - 90, 1250, x + 90, 1450], (70, 50, 120))
        avatar(d, 180, 1250, 42, ME, T, 0, "down", "shock", look=1)
        for i, x in enumerate([680, 900]):
            avatar(d, x, 1250, 42, npc(570 + i), T, 0, "down", "flat", look=-1)
        fx = 400
        if sc == "sneeze":
            pre = u < .55
            top = avatar(d, fx, 1250, 46, CHARS["friend"], T, 0, "down" if pre else "out", "flat" if pre else "yell")
            if pre:
                stk("AH... AH...", fx, 700, 90, (255, 255, 255), fg=(20, 20, 20), rot=-4, scale=1 + .1 * u)
            else:
                stk("HUSS-CHOO!", fx + 120, 650, 120, (90, 200, 255), rot=6, scale=1.2 - .2 * min(1, (u - .55) * 4))
                rnd = random.Random(int(T * 10))
                for q in range(20):
                    a = rnd.uniform(-.6, .6); r = rnd.uniform(50, 260) * min(1, (u - .55) * 4)
                    d.ellipse([fx + 70 + r * math.cos(a) - 6, top + 60 + r * math.sin(a) - 6, fx + 70 + r * math.cos(a) + 6, top + 60 + r * math.sin(a) + 6], fill=(170, 230, 255))
                amp = int(16 * max(0, 1 - (u - .55) * 4))
        else:
            # trampilla: cae
            drop = 600 * ease(min(1, u / .4))
            d.rectangle([fx - 90, 1250, fx + 90, 1450], fill=(10, 5, 20))
            avatar(d, fx, 1250 + drop, 46, CHARS["friend"], T, 0, "up", "shock")
            d.rectangle([fx - 95, 1450, fx + 95, H], fill=(60, 40, 80))
            stk("ELIMINATED", W / 2, 420, 120, RED, rot=-4, scale=1 + .06 * math.sin(T * 12))
            if u > .5: stk("ANYWAY", W / 2, 640, 110, (255, 255, 255), fg=(20, 20, 20), rot=5)
            tint(img, RED, 30 if int(T * 4) % 2 else 0)
        ovl.append(DAY[sc])

    elif sc == "final_two":
        sky(img, (20, 10, 50), (120, 30, 120)); d = ImageDraw.Draw(img)
        d.rectangle([W / 2 - 6, 0, W / 2 + 6, H], fill=PINK)
        d.rectangle([0, 1450, W, H], fill=(60, 40, 80))
        avatar(d, W / 4, 1450, 70, ME, T, 0, "down", "flat", look=1)
        granny(d, W * 3 / 4, 1450, 70, T, "down", "smile", look=-1)
        p = min(1, t / .3)
        stk("VS", W / 2, 900, int(200 * (.5 + .5 * p)), RED, rot=-8)
        stk("ME", W / 4, 420, 110, (40, 90, 210), rot=-4)
        stk("GRANDMA", W * 3 / 4, 420, 90, (170, 90, 160), rot=4)
        ovl.append(DAY[sc])

    elif sc in ("countdown", "final_count"):
        d = neon_city(img, T)
        if sc == "countdown":
            secs = max(0, 59 - int(t * 6))  # el reloj corre rápido
            screen(d, box, [("LAST MINUTE", 80, (255, 255, 255)), (f"00:{secs:02d}", 260, GOLD), ("DON'T SAY IT", 50, NEON)])
        else:
            num = 3 - min(2, int(u * 3))
            pulse = 1 + .3 * max(0, 1 - ((u * 3) % 1) * 4)
            screen(d, box, [("FINAL SECONDS", 80, (255, 255, 255)), (str(num), int(400 * pulse), RED)])
            tint(img, RED, 30 * max(0, 1 - ((u * 3) % 1) * 4))
        avatar(d, 250, GY + 60, 52, ME, T, 0, "down", "flat", look=1)
        granny(d, 830, GY + 60, 52, T, "down", "smile", look=-1)
        ovl.append(DAY[sc])

    elif sc == "win":
        sky(img, (255, 60, 200), (120, 30, 200)); d = ImageDraw.Draw(img)
        for q in range(16):
            a = q * math.pi / 8 + T * .7
            d.polygon([(W / 2, 1000), (W / 2 + 2300 * math.cos(a), 1000 + 2300 * math.sin(a)),
                       (W / 2 + 2300 * math.cos(a + .18), 1000 + 2300 * math.sin(a + .18))], fill=(255, 120, 230))
        confetti(d, T)
        z = 1 + .15 * hit
        avatar(d, W / 2, 1650, 95 * z, ME, T, 0, "up", "yell" if hit > .2 else "laugh")
        if k < 0:
            stk("I WON!", W / 2, 380, 170, GOLD, fg=(255, 255, 255), rot=-5, scale=1 + .06 * math.sin(T * 10))
        elif k < seg["nh"]:
            for j in range(k + 1):
                stk("HUSS", 180 + (j * 191) % 720, 330 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                    rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
        amp = int(22 * hit)
        ovl.append(DAY[sc])

    elif sc == "clock":
        sky(img, (20, 10, 50), (60, 20, 80)); d = ImageDraw.Draw(img)
        x0, y0, x1, y1 = 90, 520, 990, 940
        d.rectangle([x0, y0, x1, y1], fill=(10, 10, 15), outline=NEON, width=10)
        blink = int(T * 2) % 2
        d.text(((x0 + x1) / 2, (y0 + y1) / 2), "23:59" if blink else "23 59", font=font(250), fill=RED, anchor="mm")
        host(d, 820, 1650, 60, T, "out", "shock" if u > .5 else "flat", look=-1)
        avatar(d, 260, 1650, 60, ME, T, 0, "up", "laugh" if u < .5 else "shock", look=1)
        if u > .5:
            stk("STILL 11:59", W / 2, 360, 110, RED, rot=-4, scale=1 + .06 * math.sin(T * 12))
            tint(img, RED, 40 if int(T * 4) % 2 else 0)
            amp = 4
        ovl.append(DAY[sc])

    elif sc in ("granny_win", "granny_mic", "end"):
        if sc == "end":
            sky(img, (120, 200, 255), (255, 240, 200)); d = ImageDraw.Draw(img)
            # montaña de dinero con la abuela encima, con gafas de sol
            for r in range(8):
                for q in range(9 - r):
                    x = W / 2 - (8 - r) * 55 + q * 110; y = 1650 - r * 50
                    d.rectangle([x - 50, y - 22, x + 50, y + 22], fill=(90, 200, 90), outline=(30, 110, 40), width=3)
            granny(d, W / 2, 1650 - 8 * 50 + 30, 62, T, "out", "laugh", shades=True)
            money_rain(d, T, 30)
            avatar(d, 160, 1800, 50, ME, T, 0, "down", "flat", look=1)
            stk("ALREADY RICH", W / 2, 380, 120, (90, 200, 90), rot=-4, scale=1 + .05 * math.sin(T * 10))
        else:
            sky(img, (255, 60, 200), (120, 30, 200)); d = ImageDraw.Draw(img)
            confetti(d, T)
            z = 1 + .12 * hit
            granny(d, W / 2, 1650, 85 * z, T, "up" if sc == "granny_win" else "out",
                   "yell" if hit > .2 else "laugh", shades=sc == "granny_win")
            if sc == "granny_win":
                stk("GRANDMA WINS", W / 2, 360, 120, GOLD, fg=(255, 255, 255), rot=-5)
                stk("$10,000,000", W / 2, 560, 100, (90, 200, 90), rot=4)
                avatar(d, 150, 1800, 46, ME, T, 0, "down", "flat", look=1)
            else:
                mx = W / 2 + 230
                d.rectangle([mx - 10, 1150, mx + 10, 1350], fill=(40, 40, 40)); d.ellipse([mx - 30, 1110, mx + 30, 1170], fill=(90, 90, 100))
                if 0 <= k < seg["nh"]:
                    stk("huss!", W / 2 + (k - 1) * 250, 450, 120, (170, 90, 160), rot=-8 + 8 * k, scale=1 + .4 * hit)
                amp = int(18 * hit)
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
def buzzer(dur=.6):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * 110 * t)) * .18 * np.minimum(1, (dur - t) / .1)).astype(np.float32)

def sneeze():
    n = int(SR * .5); t = np.arange(n) / SR
    x = np.random.randn(n) * np.exp(-t * 8) * (t > .05)
    return (np.convolve(x, np.ones(8) / 8, "same") * .6).astype(np.float32)

ORIG_MIX = hn.ORIG_MIX  # la mezcla base del motor (no la de THE HUNT)

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
    s = by["prize"]; put(m.sfx("ding"), s["start"] + .2)
    for key in ("elim", "elim_b", "elim_c"):
        s = by[key]
        for q in range(3): put(buzzer(.35), s["start"] + .2 + q * .5)
    s = by["cams"]
    for q in range(3): put(tone(1600, .08, .3), s["start"] + q * (s["dur"] + .2) / 3)
    s = by["clown"]; put(m.sfx("boing"), s["start"] + .2)
    s = by["sneeze"]; put(sneeze(), s["start"] + (s["dur"] + .2) * .55)
    s = by["sneeze_b"]; put(m.sfx("whoosh"), s["start"]); put(buzzer(.6), s["start"] + .1)
    s = by["final_two"]; put(m.sfx("boom") * .7, s["start"])
    s = by["countdown"]
    for q in range(int(s["dur"] * 2) + 1): put(tone(1200, .08, .2), s["start"] + q * .5)
    s = by["final_count"]
    for q in range(3): put(tone(1500, .25, .35), s["start"] + q * (s["dur"] + .2) / 3)
    s = by["win"]; put(crowd_roar(1.5) * .7, s["start"]); put(m.sfx("ding"), s["start"])
    s = by["clock"]; put(buzzer(1.0), s["start"] + (s["dur"] + .2) * .5)
    s = by["granny_win"]; put(m.sfx("ding"), s["start"]); put(crowd_roar(s["dur"]) * .5, s["start"])
    s = by["end"]; put(m.sfx("ding") * .6, s["start"] + .3)
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
hn.SHOW = "DON'T SAY"
hn.TICKER = "  LIVE · DON'T SAY HUSS · 30 DAYS · $10,000,000 · SAY IT AND YOU'RE OUT · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "dont_say.mp4"]
    m.main()
