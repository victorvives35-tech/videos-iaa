#!/usr/bin/env python3
"""Historia 2: "In this town, every time you say HUSS, something magical happens..." (La Huss Ball)

Uso: python3 huss_ball.py --voice ruta/en_US-ryan-high.onnx --out huss_ball.mp4
Reutiliza el motor de in_this_town.py (HUSS real, fondo, narrador, subtítulos, personajes).
"""
import math, random, sys
from PIL import Image, ImageDraw
import in_this_town as m
from in_this_town import (W, H, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)

SCRIPT = [
    ("In this town, every time you say huss... something magical happens!", "intro", None),
    ("The baker said:", "baker", "solo", 1),
    ("And all his bread turned into GOLD!", "baker_gold", None),
    ("The mailman said:", "mailman", "solo", 1),
    ("And he got a FLYING car!", "mailman_car", None),
    ("Even grandma said:", "grandma", "solo", 1),
    ("And she started doing backflips!", "grandma_flip", None),
    ("So on my birthday, I took a deep breath, and said:", "me_try", "solo", 1),
    ("And... nothing happened.", "me_fail", None),
    ("I tried again! Louder!", "me_try2", "solo", 3),
    ("Still nothing. Everyone called me the broken huss kid.", "laugh", None),
    ("That night, I went to the basketball court... and whispered:", "night", "solo", 1),
    ("And a golden basketball fell from the sky!", "goldball", None),
    ("It was the legendary HUSS BALL! Whoever holds it gets every power in town!", "reveal", None),
    ("I bounced it once... and the whole town started floating!", "float", None),
    ("The gold bread flew away! The flying car crashed into a tree! Grandma was upside down!", "chaos", None),
    ("I had to fix it. So I held the ball up high... and said:", "hold", None),
    ("", "huss", "solo", 6),
    ("Everything came back down... and the ball started glowing!", "land", None),
    ("Now I'm the official guardian of the Huss Ball!", "guardian", None),
    ("And everyone in this town says:", "crowd", "crowd", 6),
    ("But tonight... someone is coming to steal it.", "thief", None),
    ("Who is it? Follow for part two!", "cta2", None),
]

C = dict(CHARS)
C["baker"] = dict(head=m.SKIN, torso=(245, 245, 245), legs=(60, 60, 70), hair=None, logo=None)
C["mailman"] = dict(head=(200, 150, 110), torso=(70, 110, 200), legs=(40, 50, 90), hair=None, logo=None)
C["grandma"] = dict(head=m.SKIN, torso=(170, 90, 160), legs=(120, 70, 120), hair=(200, 200, 205), logo=None)
C["thief"] = dict(head=(25, 25, 30), torso=(20, 20, 25), legs=(15, 15, 20), hair=None, logo=None, angry=True)
GY = 1450

def chef_hat(d, x, top, s):
    hs = s * 1.25
    d.rectangle([x - hs/2, top - s*.5, x + hs/2, top + s*.05], fill=(255, 255, 255), outline=(40, 40, 40), width=3)
    d.ellipse([x - hs*.7, top - s*1.4, x + hs*.7, top - s*.3], fill=(255, 255, 255), outline=(40, 40, 40), width=3)

def mail_cap(d, x, top, s):
    hs = s * 1.25
    d.rectangle([x - hs/2 - 4, top - s*.35, x + hs/2 + 4, top + s*.25], fill=(40, 60, 130), outline=(20, 20, 30), width=3)
    d.rectangle([x - hs/2, top + s*.15, x + hs/2 + hs*.35, top + s*.32], fill=(40, 60, 130))

def granny(d, x, top, s):
    d.ellipse([x - s*.45, top - s*.75, x + s*.45, top + s*.05], fill=(200, 200, 205), outline=(120, 120, 125), width=3)
    for e in (-1, 1):
        d.ellipse([x + e*s*.28 - s*.22, top + s*.32, x + e*s*.28 + s*.22, top + s*.72], outline=(20, 20, 20), width=max(3, int(s*.07)))

def ball(d, x, y, r, gold=False):
    col = (255, 205, 40) if gold else (240, 120, 30)
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(60, 35, 10), width=max(3, int(r * .08)))
    d.line([x, y - r, x, y + r], fill=(60, 35, 10), width=max(3, int(r * .07)))
    d.line([x - r, y, x + r, y], fill=(60, 35, 10), width=max(3, int(r * .07)))

def glow(img, x, y, r, col=(255, 230, 120), a=150):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for k in range(8, 0, -1):
        rr = r * k / 8
        gd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (int(a / 8),))
    img.alpha_composite(g)

def huss_moment(img, seg, T, x, y):
    """Bocadillo HUSS! que salta en el pico de cada HUSS."""
    k, hit = huss_hit(seg, T)
    if k >= 0 and k < seg["nh"]:
        sticker(img, "HUSS!", x, y, 120, (40, 90, 210), rot=-6 + 5 * k, scale=1 + .4 * hit)
    return hit

def scene(seg, t, T):
    sc = seg["scene"]; dur = seg["dur"] + .2; u = t / dur
    img = Image.new("RGBA", (W, H)); amp = 0

    if sc == "intro":
        d = town(img, T, cam=t * 60)
        for i in range(5):
            avatar(d, 120 + i * 210 + 20 * math.sin(t + i), GY, 34, npc(i + 60), T + i * .3, .7)
        if t > .7:
            sticker(img, "IN THIS TOWN...", W/2, 520, 110, (30, 30, 30), rot=-4)
        if t > 2.2:
            sticker(img, "SAY HUSS = MAGIC", W/2, 720, 80, (130, 40, 220), rot=3)

    elif sc in ("baker", "baker_gold"):
        sky(img, (255, 225, 180), (240, 190, 140)); d = ImageDraw.Draw(img)
        for row in range(3):  # estanterías con pan
            y = 520 + row * 200
            d.rectangle([60, y + 60, W - 60, y + 80], fill=(140, 90, 50))
            for j in range(7):
                x = 120 + j * 135
                gold = sc == "baker_gold" and (u > .15 + .05 * j)
                d.ellipse([x - 50, y + 10, x + 50, y + 62], fill=(255, 210, 40) if gold else (200, 130, 60), outline=(90, 50, 20), width=4)
                if gold and int(T * 8 + j + row) % 4 == 0:
                    d.regular_polygon((x + 40, y + 10, 14), 4, rotation=45, fill=(255, 255, 255))
        d.rectangle([0, GY, W, H], fill=(210, 180, 140))
        hit = huss_moment(img, seg, T, W/2, 330) if sc == "baker" else 0
        top = avatar(d, W/2, GY, 70 * (1 + .15 * hit), C["baker"], T, 0, "up" if sc == "baker_gold" else "out",
                     "yell" if hit > .2 else ("laugh" if sc == "baker_gold" else "smile"))
        chef_hat(d, W/2, top, 70 * (1 + .15 * hit))
        if sc == "baker_gold" and u > .3:
            sticker(img, "GOLD BREAD", W/2, 330, 120, (255, 200, 40), rot=-5, scale=1 + .05 * math.sin(t * 9))
        amp = int(20 * hit)

    elif sc in ("mailman", "mailman_car"):
        d = town(img, T)
        if sc == "mailman":
            hit = huss_moment(img, seg, T, W/2, 420)
            top = avatar(d, W/2, GY, 70 * (1 + .15 * hit), C["mailman"], T, 0, "out", "yell" if hit > .2 else "smile")
            mail_cap(d, W/2, top, 70 * (1 + .15 * hit))
            block(d, [W/2 + 90, 1100, W/2 + 230, 1210], (150, 100, 50))
            amp = int(20 * hit)
        else:
            cy = 1300 - 650 * ease(u / .6) + 25 * math.sin(T * 4)
            cx = W/2 + 60 * math.sin(T * 1.5)
            block(d, [cx - 260, cy - 70, cx + 260, cy + 80], (230, 60, 60))
            block(d, [cx - 140, cy - 190, cx + 140, cy - 70], (180, 220, 255))
            for wx in (-170, 170):
                d.ellipse([wx + cx - 60, cy + 40, wx + cx + 60, cy + 160], fill=(30, 30, 30))
                d.ellipse([wx + cx - 120, cy + 140, wx + cx + 120, cy + 175], fill=(120, 220, 255))
            top = avatar(d, cx, cy - 70, 32, C["mailman"], T, 0, "up", "laugh")
            mail_cap(d, cx, top, 32)
            sticker(img, "FLYING CAR", W/2, 330, 120, (230, 60, 60), rot=4)

    elif sc in ("grandma", "grandma_flip"):
        d = town(img, T)
        if sc == "grandma":
            hit = huss_moment(img, seg, T, W/2, 420)
            top = avatar(d, W/2, GY, 66, C["grandma"], T, 0, "out", "yell" if hit > .2 else "smile")
            granny(d, W/2, top, 66)
            d.line([W/2 + 150, 1180, W/2 + 170, GY], fill=(110, 70, 40), width=12)
            amp = int(20 * hit)
        else:
            ang = (t * 540) % 360
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            jy = 1250 - abs(math.sin(t * 3.2)) * 380
            top = avatar(ld, W/2, jy + 300, 60, C["grandma"], T, 0, "up", "laugh")
            granny(ld, W/2, top, 60)
            lay = lay.rotate(ang, center=(W/2, jy + 130), resample=Image.BICUBIC)
            img.alpha_composite(lay)
            sticker(img, "BACKFLIP GRANDMA", W/2, 330, 90, (170, 90, 160), rot=-4)

    elif sc in ("me_try", "me_try2", "night"):
        night = sc == "night"
        if night:
            sky(img, (10, 15, 50), (40, 30, 90)); d = ImageDraw.Draw(img)
            rnd = random.Random(1)
            for q in range(60):
                x, y = rnd.randint(0, W), rnd.randint(0, 1000)
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 230))
            d.ellipse([780, 180, 940, 340], fill=(250, 250, 220))
            d.rectangle([0, 1400, W, H], fill=(40, 70, 130)); d.line([0, 1600, W, 1600], fill=(200, 200, 230), width=8)
            d.rectangle([860, 600, 880, 1400], fill=(80, 80, 80)); block(d, [700, 520, 900, 660], (220, 220, 230))
        else:
            d = town(img, T)
            for i, x in enumerate([120, 300, 800, 980]):
                avatar(d, x, GY, 36, npc(i + 70), T, 0, "down", "smile", look=1 if x < W/2 else -1)
            if sc == "me_try":
                block(d, [W/2 + 170, 1290, W/2 + 330, 1380], (255, 160, 200))
                for c in range(3):
                    d.rectangle([W/2 + 200 + c * 45, 1240, W/2 + 210 + c * 45, 1290], fill=(250, 250, 250))
                    d.ellipse([W/2 + 197 + c * 45, 1220, W/2 + 213 + c * 45, 1242], fill=(255, 180, 40))
        k, hit = huss_hit(seg, T) if seg["huss_t0"] else (-1, 0)
        z = 1 + (.4 * ease(u) if sc == "me_try2" else .25 * ease(u)) + .15 * hit
        avatar(d, W/2 - (0 if not night else 150), GY + 40 * (z - 1), 62 * z, C["me"], T, 0,
               "out" if hit > .1 else "down", "yell" if hit > .2 else ("flat" if not night else "smile"))
        if seg["huss_t0"] and T >= seg["huss_t0"] + m.HIT_OFF - .03 and k < seg["nh"]:
            sticker(img, "huss..." if night else "HUSS!", W/2, 450, 90 if night else 130,
                    (30, 30, 60) if night else (40, 90, 210), rot=-5 + 6 * max(0, k), scale=1 + .4 * hit)
        if sc == "me_try" and t < 1.5:
            sticker(img, "BIRTHDAY", W/2, 330, 100, (255, 120, 200), rot=4)
        if sc == "me_try2":
            sticker(img, "LOUDER!", W/2, 300, 110, (240, 60, 60), rot=5)
        amp = int(25 * hit)

    elif sc == "me_fail":
        d = town(img, T)
        img.alpha_composite(Image.new("RGBA", (W, H), (60, 60, 90, 120)))
        d = ImageDraw.Draw(img)
        for i, x in enumerate([120, 300, 800, 980]):
            avatar(d, x, GY, 36, npc(i + 70), T, 0, "down", "flat", look=1 if x < W/2 else -1)
        avatar(d, W/2, GY, 62, C["me"], T, 0, "down", "flat")
        cx = W/2
        for dx, r in ((-80, 70), (0, 95), (90, 70)):
            d.ellipse([cx + dx - r, 650 - r, cx + dx + r, 650 + r], fill=(90, 90, 110))
        rnd = random.Random(int(T * 15))
        for q in range(14):
            x = cx + rnd.randint(-150, 150); y = 720 + rnd.randint(0, 400)
            d.line([x, y, x - 5, y + 35], fill=(120, 170, 255), width=5)
        if u > .4:
            sticker(img, "NOTHING", W/2, 380, 130, (90, 90, 110), rot=-4)
        # grillo
        if int(T * 6) % 2 == 0 and u > .4:
            d.text((900, 1350), "cri cri", font=font(40), fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))

    elif sc in ("goldball", "reveal"):
        if sc == "goldball":
            sky(img, (10, 15, 50), (40, 30, 90)); d = ImageDraw.Draw(img)
            rnd = random.Random(1)
            for q in range(60):
                x, y = rnd.randint(0, W), rnd.randint(0, 1000)
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 230))
            d.rectangle([0, 1400, W, H], fill=(40, 70, 130))
            by = -200 + 1350 * ease(min(1, u / .55))
            if u > .55: by = 1150 - abs(math.sin((u - .55) * 14)) * 150 * max(0, 1 - (u - .55) * 2)
            d = ImageDraw.Draw(img)
            glow(img, W/2 + 120, by, 260)
            d = ImageDraw.Draw(img)
            d.polygon([(W/2 + 120 - 60, 0), (W/2 + 120 + 60, 0), (W/2 + 120 + 150, by), (W/2 + 120 - 150, by)], fill=(255, 240, 160))
            ball(d, W/2 + 120, by, 90, gold=True)
            avatar(d, W/2 - 230, GY, 60, C["me"], T, 0, "up" if u > .55 else "down", "shock", look=1)
            if u > .55: amp = int(20 * max(0, 1 - (u - .55) * 4))
        else:
            sky(img, (40, 10, 90), (200, 40, 160)); d = ImageDraw.Draw(img)
            for q in range(20):
                a = q * math.pi / 10 + T * .8
                d.polygon([(W/2, 1000), (W/2 + 2300*math.cos(a), 1000 + 2300*math.sin(a)),
                           (W/2 + 2300*math.cos(a + .14), 1000 + 2300*math.sin(a + .14))], fill=(255, 200, 60))
            glow(img, W/2, 950, 330, a=200); d = ImageDraw.Draw(img)
            ball(d, W/2, 950 + 20 * math.sin(T * 3), 170, gold=True)
            cs = min(1, t / .3)
            if cs > .05:
                cw, ch, cy = 760 * cs, 300 * cs, 450
                d.rounded_rectangle([W/2 - cw/2, cy - ch/2, W/2 + cw/2, cy + ch/2], radius=int(40 * cs), fill=(255, 210, 40), outline=(0, 0, 0), width=10)
                if cs > .9:
                    d.text((W/2, cy - 80), "LEGENDARY ITEM", font=font(50), fill=(80, 30, 0), anchor="mm")
                    d.text((W/2, cy + 15), "HUSS BALL", font=font(120), fill=(40, 90, 210), anchor="mm", stroke_width=8, stroke_fill=(255, 255, 255))
                    d.text((W/2, cy + 105), "★ ALL POWERS ★", font=font(44), fill=(200, 40, 120), anchor="mm")
            avatar(d, W/2, 1650, 50, C["me"], T, 0, "up", "yell")
            if t < .12:
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(230 * (1 - t / .12)))))

    elif sc in ("float", "chaos"):
        sky(img, (90, 170, 255), (200, 235, 255)); d = ImageDraw.Draw(img)
        lift = 500 * ease(min(1, u / .5)) if sc == "float" else 500
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); town(lay, T)
        lay = lay.rotate(4 * math.sin(T * 1.3), center=(W/2, 1450), resample=Image.BICUBIC)
        img.alpha_composite(lay, (0, -int(lift)))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 1450, W, H], fill=(90, 70, 50)); d.rectangle([0, 1450, W, 1475], fill=(120, 190, 90))
        if sc == "float":
            ball(d, W/2, 1300 - abs(math.sin(T * 6)) * 120, 60, gold=True)
            avatar(d, W/2 - 160, 1450, 55, C["me"], T, 0, "out", "shock", look=1)
            if u > .5: sticker(img, "FLOATING TOWN", W/2, 330, 100, (60, 160, 255), rot=-3)
        else:
            rnd = random.Random(9)
            for q in range(10):  # pan de oro volando
                x = (rnd.uniform(0, W) + t * rnd.uniform(-200, 200)) % W; y = 300 + (rnd.uniform(0, 600) - t * 200) % 700
                d.ellipse([x - 40, y - 20, x + 40, y + 20], fill=(255, 210, 40), outline=(90, 50, 20), width=3)
            cx, cy = 250 + 80 * math.sin(T * 2), 500 + 60 * math.cos(T * 3)
            block(d, [cx - 150, cy - 40, cx + 150, cy + 50], (230, 60, 60))
            lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); l2 = ImageDraw.Draw(lay2)
            top = avatar(l2, 820, 900, 45, C["grandma"], T, 0, "up", "shock"); granny(l2, 820, top, 45)
            lay2 = lay2.rotate(180, center=(820, 780)); img.alpha_composite(lay2)
            d = ImageDraw.Draw(img)
            avatar(d, W/2, 1450, 55, C["me"], T, 0, "up", "shock")
            sticker(img, "CHAOS", W/2, 330, 130, (240, 60, 60), rot=4 + 3 * math.sin(t * 10))
            amp = 8

    elif sc == "hold":
        sky(img, (40, 10, 70), (120, 30, 120)); d = ImageDraw.Draw(img)
        z = 1 + .5 * ease(u)
        top = avatar(d, W/2, 1500 + 60 * (z - 1), 75 * z, C["me"], T, 0, "up", "flat")
        glow(img, W/2, top - 210 * z, 220 * z, a=180); d = ImageDraw.Draw(img)
        ball(d, W/2, top - 210 * z, 85 * z, gold=True)

    elif sc == "land":
        d = town(img, T)
        drop = 400 * (1 - ease(min(1, u / .3)))
        for i, x in enumerate([120, 300, 800, 980]):
            avatar(d, x, GY - drop, 38, npc(i + 80), T, 0, "up", "laugh")
        top = avatar(d, W/2, GY - drop, 66, C["me"], T, 0, "up", "smile")
        glow(img, W/2, top - 170, 250 + 40 * math.sin(T * 6), a=200); d = ImageDraw.Draw(img)
        ball(d, W/2, top - 170, 75, gold=True)
        if u > .4: sticker(img, "SAVED!", W/2, 380, 140, (40, 200, 90), rot=-5)
        if u < .35 and u > .28: amp = 25

    elif sc == "guardian":
        sky(img, (255, 210, 40), (255, 120, 40)); d = ImageDraw.Draw(img)
        for q in range(16):
            a = q * math.pi / 8 + T * .6
            d.polygon([(W/2, 1100), (W/2 + 2300*math.cos(a), 1100 + 2300*math.sin(a)),
                       (W/2 + 2300*math.cos(a + .2), 1100 + 2300*math.sin(a + .2))], fill=(255, 240, 140))
        top = avatar(d, W/2, 1600, 90, C["me"], T, 0, "out", "smile")
        d.polygon([(W/2 - 140, top - 10), (W/2 - 140, top - 110), (W/2 - 70, top - 50), (W/2, top - 130),
                   (W/2 + 70, top - 50), (W/2 + 140, top - 110), (W/2 + 140, top - 10)], fill=(255, 210, 30), outline=(0, 0, 0))
        glow(img, W/2 + 330, 1150, 160); d = ImageDraw.Draw(img)
        ball(d, W/2 + 330, 1150 - abs(math.sin(T * 7)) * 100, 65, gold=True)
        sticker(img, "GUARDIAN", W/2, 420, 150, (40, 90, 210), rot=-4, scale=1 + .05 * math.sin(t * 9))

    elif sc == "thief":
        sky(img, (5, 5, 20), (30, 10, 40)); d = ImageDraw.Draw(img)
        d.ellipse([780, 160, 960, 340], fill=(230, 230, 210))
        for i in range(-1, 6):
            x = i * 220
            d.rectangle([x, 900, x + 200, 1450], fill=(20, 20, 35))
            d.polygon([(x - 10, 900), (x + 100, 800), (x + 210, 900)], fill=(15, 15, 25))
            d.rectangle([x + 70, 1000, x + 130, 1060], fill=(255, 220, 120))
        d.rectangle([0, 1450, W, H], fill=(30, 30, 40))
        x = -200 + (W/2 + 300) * ease(min(1, u / .7))
        avatar(d, x, GY, 70, C["thief"], T, .6, "out", "angry", look=-1)
        for e in (-1, 1):  # ojos rojos brillantes
            hy = GY - 70 * 4 - 70 * 1.25 * 1.05
            d.ellipse([x + e * 22 - 12, hy + 30, x + e * 22 + 12, hy + 52], fill=(255, 30, 30))
        if u > .5:
            sticker(img, "???", W/2, 450, 180, (0, 0, 0), fg=(255, 40, 40), rot=-5, scale=1 + .05 * math.sin(t * 9))

    elif sc == "cta2":
        sky(img, (255, 40, 90), (120, 30, 200)); d = ImageDraw.Draw(img)
        avatar(d, W/2 - 220, 1450, 60, C["me"], T, 0, "up", "smile")
        ball(d, W/2 - 220, 960 - abs(math.sin(T * 7)) * 60, 55, gold=True)
        avatar(d, W/2 + 220, 1450, 60, C["thief"], T, 0, "down", "angry", look=-1)
        sticker(img, "PART 2", W/2, 560, 200, (0, 0, 0), fg=(255, 230, 40), rot=-5, scale=1 + .07 * math.sin(t * 9))
        sticker(img, "FOLLOW +", W/2, 820, 100, (255, 255, 255), fg=(255, 40, 90), rot=4)

    else:  # escenas compartidas (laugh, huss, crowd...)
        seg["no_monster"] = True
        return ORIG_RENDER(seg, t, T)

    if amp: img = shake_img(img, amp)
    return img

ORIG_RENDER = m.render_scene
m.SCRIPT = SCRIPT
m.render_scene = scene

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "huss_ball.mp4"]
    m.main()
