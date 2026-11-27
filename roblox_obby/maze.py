#!/usr/bin/env python3
"""Historia 11: THE MAZE — concurso de TV. Huss Boy usa el HUSS como sónar de murciélago.

Uso: python3 maze.py --voice ruta/en_US-ryan-high.onnx [--out maze.mp4]
"""
import math, random, sys, wave
from collections import deque
import numpy as np
from PIL import Image, ImageDraw
import in_this_town as m
import hunt as hn
from in_this_town import (W, H, SR, CHARS, npc, avatar, town, sky, block, sticker, font, ease, shake_img, huss_hit)
from hunt import neon_city, screen, tv_overlay, money_rain, captions_single, tint, flash, tone, crowd_roar, PINK, PURPLE, NEON, GOLD

ME = CHARS["me"]
RED = (255, 40, 40)
HEDGE, HEDGE_D, GRASS = (60, 150, 60), (40, 110, 45), (190, 220, 150)

SCRIPT = [
    ("In this town, there's a TV show called The Maze.", "intro", None),
    ("A giant maze. Ten million dollars in the middle. The first one to get there wins it.", "rules", None),
    ("One hundred people ran in. Including me.", "start", None),
    ("Hour one. Twenty people were already lost.", "lost", None),
    ("One guy walked in circles for six hours. He made a path in the grass.", "lost_b", None),
    ("Hour six. One guy gave up and built a little house in a corner.", "house", None),
    ("Day two. Two people got lost together... fell in love... and got married. In the maze.", "wedding", None),
    ("Then they had a baby. They named him Hedge.", "wedding_b", None),
    ("The TV show sent a drone to film us. The drone got lost too.", "drone", None),
    ("Day three. One guy found the exit by accident. He was so mad.", "exit", None),
    ("But I had a plan. Bats find their way with sound. So I said:", "echo", "solo", 3),
    ("The echo showed me the way!", "echo_b", None),
    ("Left. Right. Right. Left. Under a very confused cow.", "run", None),
    ("The cow followed me. Now the cow is my best friend.", "run_b", None),
    ("I made it to the center! I opened the treasure chest...", "chest", None),
    ("Inside, there was a note. It said: Congratulations! Now find the exit.", "note", None),
    ("That was three years ago.", "years", None),
    ("I'm still in here. But hey... I'm rich. And every night, I still say:", "end", "solo", 6),
]

DAY = {"lost_b": "HOUR 6", "wedding_b": "DAY 2", "drone": "DAY 2", "run_b": "DAY 3", "start": "HOUR 0", "lost": "HOUR 1", "house": "HOUR 6", "wedding": "DAY 2", "exit": "DAY 3", "echo": "DAY 3",
       "echo_b": "DAY 3", "run": "DAY 3", "chest": "DAY 3", "note": "DAY 3", "years": "YEAR 3", "end": "YEAR 3"}

CAMS = {
    "intro": (1.6, 1.0, (.5, .35), (.5, .5)), "rules": (1.0, 1.0, (.5, .5), (.5, .5)),
    "start": (1.2, 1.0, (.5, .6), (.5, .58)), "lost": (1.0, 1.2, (.5, .5), (.4, .45)),
    "house": (1.0, 1.3, (.5, .6), (.6, .62)), "wedding": (1.25, 1.0, (.5, .58), (.5, .58)),
    "exit": (1.0, 1.2, (.5, .55), (.5, .58)), "echo": (1.0, 1.0, (.5, .5), (.5, .5)),
    "echo_b": (1.0, 1.0, (.5, .5), (.5, .5)), "run": (1.0, 1.15, (.5, .6), (.5, .6)),
    "chest": (1.0, 1.4, (.5, .62), (.5, .66)), "note": (1.0, 1.15, (.5, .5), (.5, .48)),
    "years": (1.25, 1.0, (.5, .6), (.5, .6)), "end": (1.0, 1.2, (.5, .55), (.5, .58)),
    "lost_b": (1.0, 1.6, (.5, .5), (.3, .7)), "wedding_b": (1.0, 1.3, (.5, .6), (.5, .64)),
    "drone": (1.2, 1.0, (.5, .5), (.5, .5)), "run_b": (1.0, 1.2, (.5, .62), (.5, .64)),
}

# ------------------------------------------------------------------ laberinto
COLS, ROWS, CELL, MX, MY = 12, 17, 80, 60, 300

def make_maze(seed=11):
    rnd = random.Random(seed)
    walls = {(c, r): {"N", "S", "E", "W"} for c in range(COLS) for r in range(ROWS)}
    seen = {(0, ROWS - 1)}; stack = [(0, ROWS - 1)]
    dirs = {"N": (0, -1, "S"), "S": (0, 1, "N"), "E": (1, 0, "W"), "W": (-1, 0, "E")}
    while stack:
        c, r = stack[-1]
        opts = [(dn, c + dx, r + dy, op) for dn, (dx, dy, op) in dirs.items() if (c + dx, r + dy) in walls and (c + dx, r + dy) not in seen]
        if not opts: stack.pop(); continue
        dn, nc, nr, op = rnd.choice(opts)
        walls[(c, r)].discard(dn); walls[(nc, nr)].discard(op)
        seen.add((nc, nr)); stack.append((nc, nr))
    walls[(0, ROWS - 1)].discard("S")  # entrada
    return walls

WALLS = make_maze()
START, GOAL = (0, ROWS - 1), (COLS // 2, ROWS // 2)

def solve():
    dirs = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
    prev = {START: None}; q = deque([START])
    while q:
        cur = q.popleft()
        if cur == GOAL: break
        for dn, (dx, dy) in dirs.items():
            nb = (cur[0] + dx, cur[1] + dy)
            if dn not in WALLS[cur] and nb in WALLS and nb not in prev:
                prev[nb] = cur; q.append(nb)
    path, c = [], GOAL
    while c: path.append(c); c = prev[c]
    return path[::-1]

PATH = solve()

def cell_xy(c, r): return MX + (c + .5) * CELL, MY + (r + .5) * CELL

def draw_maze(d, T, glow_path=0., treasure=True):
    d.rectangle([MX - 20, MY - 20, MX + COLS * CELL + 20, MY + ROWS * CELL + 20], fill=GRASS)
    if glow_path > 0:
        n = int(len(PATH) * glow_path)
        pts = [cell_xy(*p) for p in PATH[:max(2, n)]]
        d.line(pts, fill=(255, 230, 80), width=30, joint="curve")
    for (c, r), ws in WALLS.items():
        x0, y0 = MX + c * CELL, MY + r * CELL
        for wdir in ws:
            if wdir == "N": seg = [x0, y0, x0 + CELL, y0]
            elif wdir == "S": seg = [x0, y0 + CELL, x0 + CELL, y0 + CELL]
            elif wdir == "W": seg = [x0, y0, x0, y0 + CELL]
            else: seg = [x0 + CELL, y0, x0 + CELL, y0 + CELL]
            d.line(seg, fill=HEDGE_D, width=22)
            d.line(seg, fill=HEDGE, width=14)
    if treasure:
        gx, gy = cell_xy(*GOAL)
        g = 1 + .1 * math.sin(T * 6)
        d.rectangle([gx - 26 * g, gy - 20 * g, gx + 26 * g, gy + 20 * g], fill=GOLD, outline=(120, 80, 10), width=4)
        d.text((gx, gy), "$", font=font(30), fill=(120, 80, 10), anchor="mm")

def dot(d, x, y, col, me=False, r=20):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(20, 20, 20), width=3)
    if me: d.text((x, y), "H", font=font(int(r * 1.2)), fill=(255, 205, 40), anchor="mm")
    else:
        d.ellipse([x - r * .45 - 3, y - r * .25 - 3, x - r * .45 + 3, y - r * .25 + 3], fill=(20, 20, 20))
        d.ellipse([x + r * .45 - 3, y - r * .25 - 3, x + r * .45 + 3, y - r * .25 + 3], fill=(20, 20, 20))

def wanderers(d, T, n, seed=0):
    rnd = random.Random(seed)
    cells = list(WALLS.keys())
    for i in range(n):
        c, r = rnd.choice(cells)
        x, y = cell_xy(c, r)
        x += 18 * math.sin(T * (1 + i * .1) + i); y += 18 * math.cos(T * (1.2 + i * .1) + i)
        dot(d, x, y, npc(1400 + i)["torso"])
        if i % 4 == 0: d.text((x + 22, y - 26), "?", font=font(30), fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(20, 20, 20))

def corridor(img, T, cam=0.):
    """Vista a pie de pasillo: dos setos altos en perspectiva."""
    sky(img, (120, 200, 255), (210, 240, 255)); d = ImageDraw.Draw(img)
    d.rectangle([0, 1150, W, H], fill=(150, 190, 110))
    vx, vy = W / 2, 980
    d.polygon([(0, 300), (vx - 140, vy - 120), (vx - 140, vy + 100), (0, 1900)], fill=HEDGE)
    d.polygon([(W, 300), (vx + 140, vy - 120), (vx + 140, vy + 100), (W, 1900)], fill=HEDGE)
    d.rectangle([vx - 140, vy - 120, vx + 140, vy + 100], fill=HEDGE_D)  # fondo (otro seto)
    rnd = random.Random(2)
    for q in range(70):  # textura de hojas
        side = rnd.choice((-1, 1)); t_ = rnd.uniform(0, 1)
        x = (W / 2 + side * (W / 2 - t_ * (W / 2 - 140))) - side * rnd.uniform(0, 80)
        y = 300 + t_ * (vy - 120 - 300) + rnd.uniform(0, 900 * (1 - t_) + 200)
        d.ellipse([x - 14, y - 10, x + 14, y + 10], fill=(80, 170, 70))
    return d

def cow(d, x, y, s, T):
    block(d, [x - s * 1.6, y - s * 1.9, x + s * 1.6, y - s * .8], (250, 250, 250))
    for q, (dx, dy) in enumerate([(-.8, -1.5), (.3, -1.2), (.9, -1.7)]):
        d.ellipse([x + dx * s - s * .35, y + dy * s - s * .25, x + dx * s + s * .35, y + dy * s + s * .25], fill=(30, 30, 30))
    for lx in (-1.2, -.5, .5, 1.2):
        block(d, [x + lx * s - s * .15, y - s * .9, x + lx * s + s * .15, y], (250, 250, 250))
    hx = x + s * 1.7
    block(d, [hx - s * .2, y - s * 2.5, hx + s * .9, y - s * 1.5], (250, 250, 250))
    d.rectangle([hx + s * .3, y - s * 1.8, hx + s * .95, y - s * 1.5], fill=(255, 170, 180))
    d.ellipse([hx + s * .2, y - s * 2.3, hx + s * .4, y - s * 2.1], fill=(20, 20, 20))
    d.text((hx + s * .3, y - s * 2.9), "?", font=font(int(s * .8)), fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(20, 20, 20))

def chest(d, x, y, s, open_=0.):
    block(d, [x - s * 1.5, y - s, x + s * 1.5, y], (150, 90, 40))
    d.rectangle([x - s * 1.5, y - s * .55, x + s * 1.5, y - s * .45], fill=GOLD)
    lid = s * .8
    if open_ > 0:
        d.polygon([(x - s * 1.5, y - s), (x + s * 1.5, y - s), (x + s * 1.3, y - s - lid * open_ * 1.4), (x - s * 1.3, y - s - lid * open_ * 1.4)], fill=(170, 110, 50))
        glow = Image.new("RGBA", (1, 1))
    else:
        block(d, [x - s * 1.5, y - s - lid * .5, x + s * 1.5, y - s], (170, 110, 50))
    d.rectangle([x - s * .2, y - s * .8, x + s * .2, y - s * .3], fill=GOLD)

def beard(d, x, top, s, length):
    hs = s * 1.25
    d.rectangle([x - hs * .45, top + hs * .62, x + hs * .45, top + hs * (.95 + length)], fill=(120, 75, 35))

# ------------------------------------------------------------------ escenas
def scene(seg, t, T):
    full = seg["scene"]
    sc = {"lost_b": "lost", "wedding_b": "wedding", "drone": "lost", "run_b": "run"}.get(full, full)
    dur = seg["dur"] + .2; u = min(1, t / dur)
    if full == "run_b": u = .75 + .25 * u
    img = Image.new("RGBA", (W, H)); amp = 0
    later = []; ovl = []
    def stk(*a, **k): later.append((a, k))
    k, hit = huss_hit(seg, T) if seg.get("hits") else (-1, 0)
    box = [110, 330, 970, 980]

    if sc == "intro":
        d = neon_city(img, T)
        p = ease(min(1, t / .5))
        screen(d, box, [("THE", 90, (255, 255, 255)), ("MAZE", int(220 * (.6 + .4 * p)), NEON), ("FIND THE MONEY", 50, GOLD)])
        ovl.append(None)

    elif sc in ("rules", "lost", "echo", "echo_b"):
        sky(img, (110, 180, 90), (90, 160, 80)); d = ImageDraw.Draw(img)
        if sc == "rules":
            draw_maze(d, T)
            gx, gy = cell_xy(*GOAL)
            for q in range(3):  # brillo del tesoro
                r = 40 + ((T * 80 + q * 40) % 120)
                d.ellipse([gx - r, gy - r, gx + r, gy + r], outline=GOLD, width=4)
            stk("$10,000,000", W / 2, 230, 110, (90, 200, 90), rot=-3, scale=1 + .05 * math.sin(T * 10))
        elif full == "lost_b":
            draw_maze(d, T)
            cx_, cy_ = cell_xy(2, ROWS - 3)
            d.ellipse([cx_ - 60, cy_ - 60, cx_ + 60, cy_ + 60], outline=(150, 120, 70), width=18)  # surco
            a_ = T * 4
            dot(d, cx_ + 60 * math.cos(a_), cy_ + 60 * math.sin(a_), npc(1450)["torso"])
            stk("6 HOURS", W / 2, 230, 130, (150, 120, 70), fg=(255, 255, 255), rot=-4)
        elif full == "drone":
            draw_maze(d, T)
            wanderers(d, T, 8, 5)
            dx_, dy_ = W / 2 + 300 * math.sin(T * .9), 900 + 400 * math.sin(T * 1.3)
            block(d, [dx_ - 40, dy_ - 14, dx_ + 40, dy_ + 14], (40, 40, 50))
            for e in (-1, 1):
                rw = 34 * abs(math.cos(T * 40 + e))
                d.line([dx_ + e * 50 - rw, dy_ - 24, dx_ + e * 50 + rw, dy_ - 24], fill=(220, 220, 230), width=5)
            d.text((dx_ + 60, dy_ - 60), "?", font=font(70), fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(20, 20, 20))
            stk("DRONE: LOST", W / 2, 230, 120, (40, 40, 50), fg=(255, 255, 255), rot=-4)
        elif sc == "lost":
            draw_maze(d, T)
            wanderers(d, T, 22, 3)
            stk("LOST", W / 2, 230, 150, RED, rot=-4)
        else:
            draw_maze(d, T, glow_path=ease(u) if sc == "echo_b" else 0)
            # Huss Boy en su punto del camino
            i0 = len(PATH) // 3
            hx, hy = cell_xy(*PATH[i0 if sc == "echo" else min(len(PATH) - 1, i0 + int((len(PATH) - i0) * ease(u)))])
            if sc == "echo":
                for h in seg.get("hits") or []:  # anillos de sónar desde cada HUSS
                    age = T - h
                    if 0 <= age < 1.6:
                        r = 40 + age * 700
                        d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=(80, 220, 255, 255), width=int(10 * (1 - age / 1.6)) + 2)
                if 0 <= k < seg["nh"]:
                    stk("HUSS!", W / 2 + (k - 1) * 250, 230, 120, (40, 90, 210), rot=-8 + 8 * k, scale=1 + .4 * hit)
                else:
                    stk("BAT MODE", W / 2, 230, 120, (30, 30, 40), fg=(80, 220, 255), rot=-4)
            else:
                stk("THE WAY!", W / 2, 230, 130, GOLD, fg=(255, 255, 255), rot=-4, scale=1 + .05 * math.sin(T * 10))
            dot(d, hx, hy, (40, 90, 210), me=True, r=26)
            amp = int(10 * hit)
        ovl.append(DAY.get(full))

    elif sc == "start":
        town(img, T); d = ImageDraw.Draw(img)
        block(d, [0, 900, W, 1450], HEDGE)
        d.rectangle([380, 1000, 700, 1450], fill=(150, 190, 110))  # hueco de entrada
        d.rectangle([340, 880, 740, 960], fill=PINK); d.text((540, 920), "ENTRANCE", font=font(50), fill=(255, 255, 255), anchor="mm")
        for i in range(14):
            x = 100 + (i * 73) % 880 + 380 * ease(u) * (1 if i % 2 else -1) * .3
            y = 1550 + (i % 3) * 60 - 300 * ease(u)
            avatar(d, x, y, 30 + (i % 3) * 5, npc(1500 + i), T * 2 + i, 1.4, "up", "yell", look=0)
        avatar(d, 540, 1720 - 250 * ease(u), 56, ME, T * 2, 1.4, "up", "laugh")
        stk("100 PEOPLE", W / 2, 400, 120, PINK, rot=-5)
        ovl.append(DAY[sc])

    elif sc in ("house", "wedding", "exit", "run", "chest"):
        d = corridor(img, T)
        if sc == "house":
            hx = 620
            block(d, [hx - 160, 1180, hx + 160, 1420], (230, 200, 150))
            d.polygon([(hx - 190, 1180), (hx, 1040), (hx + 190, 1180)], fill=(180, 70, 50))
            d.rectangle([hx - 40, 1300, hx + 40, 1420], fill=(120, 80, 50))
            d.rectangle([hx + 70, 1220, hx + 130, 1270], fill=(180, 220, 255))
            avatar(d, 300, 1550, 50, npc(1600), T, 0, "out", "smile", look=1)
            d.rectangle([hx - 130, 1440, hx + 130, 1460], fill=(160, 120, 80))
            d.text((hx, 1490), "HOME SWEET MAZE", font=font(36), fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(40, 40, 40))
            stk("GAVE UP", W / 2, 400, 120, (180, 70, 50), rot=-4)
        elif sc == "wedding":
            a = (255, 205, 160)
            avatar(d, 420, 1550, 56, dict(head=a, torso=(30, 30, 40), legs=(30, 30, 40), hair=(60, 40, 20), logo=None), T, 0, "out", "laugh", look=1)
            top = avatar(d, 660, 1550, 56, dict(head=a, torso=(250, 250, 250), legs=(250, 250, 250), hair=(240, 200, 60), logo=None, long_hair=True), T, 0, "out", "laugh", look=-1)
            d.polygon([(600, top - 10), (720, top - 10), (760, top + 200), (560, top + 200)], fill=(255, 255, 255, 180))  # velo
            for q in range(6):
                hx, hy = 540 + 200 * math.sin(T * 1.5 + q), 900 - ((T * 120 + q * 70) % 400)
                d.polygon([(hx, hy + 18), (hx - 18, hy), (hx - 9, hy - 10), (hx, hy - 2), (hx + 9, hy - 10), (hx + 18, hy)], fill=(255, 80, 120))
            if full == "wedding_b":
                avatar(d, 540, 1580, 28, dict(head=a, torso=(60, 150, 60), legs=(60, 150, 60), hair=None, logo=None), T, 0, "up", "laugh")
                stk("BABY HEDGE", W / 2, 400, 120, HEDGE, fg=(255, 255, 255), rot=-4, scale=1 + .05 * math.sin(T * 10))
            else:
                stk("JUST MARRIED", W / 2, 400, 110, (255, 80, 120), rot=-4, scale=1 + .05 * math.sin(T * 10))
                if u > .6: stk("IN THE MAZE", W / 2, 600, 100, HEDGE_D, fg=(255, 255, 255), rot=4)
        elif sc == "exit":
            d.rectangle([W / 2 - 140, 860, W / 2 + 140, 1080], fill=(255, 255, 255))
            d.rectangle([W / 2 - 160, 800, W / 2 + 160, 860], fill=(40, 200, 90)); d.text((W / 2, 830), "EXIT", font=font(50), fill=(255, 255, 255), anchor="mm")
            avatar(d, W / 2, 1550, 60, npc(1610), T, 0, "up", "angry")
            stk("EXIT?!", W / 2, 400, 140, (40, 200, 90), rot=-5)
            if u > .5: stk("SO MAD", W / 2, 600, 120, RED, rot=5, scale=1 + .08 * math.sin(T * 14))
            amp = 4 if u > .5 else 0
        elif sc == "run":
            third = min(3, int(u * 4))
            dirs = ["LEFT", "RIGHT", "RIGHT", "LEFT"]
            arrow_x = W / 2 + (-260 if dirs[third] == "LEFT" else 260)
            d.polygon([(arrow_x - 90 * (1 if dirs[third] == "RIGHT" else -1), 1000), (arrow_x + 60 * (1 if dirs[third] == "RIGHT" else -1), 900),
                       (arrow_x + 60 * (1 if dirs[third] == "RIGHT" else -1), 1100)], fill=GOLD)
            if u > .7:
                cow(d, W / 2, 1450, 90, T)
                avatar(d, W / 2 - 60 + 200 * (u - .7) / .3, 1560, 40, ME, T * 2, 1.6, "down", "shock")
                if full == "run_b":
                    stk("BEST FRIEND", W / 2, 400, 120, (255, 140, 180), rot=-4)
                else:
                    stk("CONFUSED COW", W / 2, 400, 110, (250, 250, 250), fg=(30, 30, 30), rot=-4)
            else:
                avatar(d, W / 2, 1600, 62, ME, T * 2, 1.6, "up", "yell")
                stk(dirs[third], W / 2, 400, 150, GOLD, fg=(255, 255, 255), rot=-5 + 5 * third)
            if (u * 4) % 1 < .05: flash(img, .4)
        else:  # chest
            sky(img, (255, 220, 120), (255, 190, 80)); d = ImageDraw.Draw(img)
            for q in range(16):
                a = q * math.pi / 8 + T * .7
                d.polygon([(W / 2, 1300), (W / 2 + 2300 * math.cos(a), 1300 + 2300 * math.sin(a)),
                           (W / 2 + 2300 * math.cos(a + .18), 1300 + 2300 * math.sin(a + .18))], fill=(255, 235, 160))
            d.rectangle([0, 1450, W, H], fill=(150, 190, 110))
            op = ease(max(0, (u - .5) / .3))
            chest(d, W / 2 + 120, 1450, 110, op)
            avatar(d, W / 2 - 260, 1460, 64, ME, T, 0, "out" if op > 0 else "up", "laugh", look=1)
            stk("THE CENTER", W / 2, 400, 130, GOLD, fg=(255, 255, 255), rot=-4)
        ovl.append(DAY[full])

    elif sc == "note":
        sky(img, (60, 40, 30), (100, 70, 50)); d = ImageDraw.Draw(img)
        d.polygon([(130, 420), (950, 400), (970, 1300), (110, 1330)], fill=(245, 235, 200), outline=(170, 150, 110))
        lines = ["CONGRATULATIONS!", "", "NOW FIND", "THE EXIT :)"]
        for q, ln in enumerate(lines):
            if u > .15 + q * .15:
                d.text((540, 560 + q * 170), ln, font=font(68 if q == 0 else 110), fill=(60, 40, 20), anchor="mm")
        if u > .75:
            stk("?!?!", W / 2, 1500, 170, RED, rot=6); amp = 6
        ovl.append(DAY[sc])

    elif sc in ("years", "end"):
        d = corridor(img, T)
        night = sc == "end"
        if night:
            tint(img, (20, 20, 70), 150); d = ImageDraw.Draw(img)
            d.ellipse([800, 160, 940, 300], fill=(250, 250, 220))
        # el pueblo dentro del laberinto: casita, la pareja con niños, la vaca
        block(d, [690, 1200, 980, 1420], (230, 200, 150)); d.polygon([(660, 1200), (835, 1070), (1010, 1200)], fill=(180, 70, 50))
        for i, (x, s_) in enumerate([(130, 46), (230, 46), (300, 26), (350, 26)]):
            avatar(d, x, 1560, s_, npc(1620 + i), T, 0, "down", "smile", look=1)
        cow(d, 880, 1620, 50, T)
        z = 1 + .12 * hit
        top = avatar(d, 560, 1640, 70 * z, ME, T, 0, "out" if hit > .1 else "down", "yell" if hit > .2 else "flat")
        beard(d, 560, top, 70 * z, 1.4)
        chest(d, 560, 1760, 50, 1)
        money_rain(d, T, 10) if not night else None
        if sc == "years":
            stk("3 YEARS LATER", W / 2, 400, 120, (30, 30, 40), fg=(255, 255, 255), rot=-4)
        else:
            if 0 <= k < seg["nh"]:
                for j in range(k + 1):
                    stk("HUSS", 180 + (j * 191) % 720, 360 + (j % 3) * 130, 120, [PINK, PURPLE, (40, 90, 210)][j % 3],
                        rot=-12 + 6 * j, scale=1 + (.4 * hit if j == k else 0))
            else:
                stk("STILL HERE", W / 2, 400, 120, HEDGE_D, fg=(255, 255, 255), rot=-4)
                if u > .3: stk("BUT RICH", W / 2, 600, 110, GOLD, fg=(255, 255, 255), rot=4)
            amp = int(16 * hit)
        ovl.append(DAY[sc])

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
def sonar():
    n = int(SR * 1.2); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 3.5) * .18 * (1 + .5 * np.sin(2 * np.pi * 9 * t))).astype(np.float32)

def moo():
    n = int(SR * 1.0); t = np.arange(n) / SR
    f = 140 - 30 * t
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .5 + np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (x * np.minimum(1, t / .1) * np.minimum(1, (1 - t) / .3) * .12).astype(np.float32)

def wedding_bells():
    out = np.zeros(int(SR * 1.6), np.float32)
    for q, f in enumerate([1047, 1319, 1568, 1319]):
        s = int(q * .35 * SR); b = tone(f, 1.0, .18); out[s:s + len(b)] += b[:len(out) - s]
    return out

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
    s = by["start"]; put(crowd_roar(s["dur"] + .2) * .6, s["start"])
    s = by["house"]; put(m.sfx("pop"), s["start"] + .3)
    s = by["wedding"]; put(wedding_bells(), s["start"] + .2)
    s = by["exit"]; put(m.sfx("boom") * .5, s["start"] + (s["dur"] + .2) * .5)
    for h in by["echo"]["hits"]: put(sonar(), h + .05)
    s = by["echo_b"]; put(m.sfx("ding"), s["start"] + .1); put(m.riser(s["dur"]) * .5, s["start"])
    s = by["run"]
    for q in range(4): put(m.sfx("whoosh") * .6, s["start"] + q * (s["dur"] + .2) / 4)
    put(moo(), s["start"] + (s["dur"] + .2) * .72)
    s = by["chest"]; put(m.sfx("ding"), s["start"] + (s["dur"] + .2) * .55); put(crowd_roar(1.0) * .5, s["start"] + (s["dur"] + .2) * .55)
    s = by["note"]; put(m.sfx("boom") * .7, s["start"] + (s["dur"] + .2) * .75)
    s = by["years"]; put(m.sfx("whoosh"), s["start"]); put(moo() * .7, s["start"] + 1.0)
    for h in by["end"]["hits"]: put(sonar() * .7, h + .05)
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
hn.SHOW = "THE MAZE"
hn.TICKER = "  LIVE · THE MAZE · $10,000,000 IN THE CENTER · FIRST ONE THERE WINS · "
m.SCRIPT = SCRIPT
m.render_scene = scene
m.mix_audio = mix_audio
m.build = hn.build
m.draw_captions = captions_single

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", "maze.mp4"]
    m.main()
