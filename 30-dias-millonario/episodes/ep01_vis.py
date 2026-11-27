"""Escenas visuales del Capítulo 1."""
import math, random
import skia
from engine import *

DUST = Particles(70, seed=2)
RAIN = Particles(140, seed=4)
RAIN2 = Particles(60, seed=9)

# ------------------------------------------------------------------ cámara
def camera(c, cx, cy, z, rot=0.0, shake=0.0, T=0.0):
    sx = sy = 0
    if shake:
        sx = (math.sin(T * 91) + math.sin(T * 57)) * 12 * shake
        sy = (math.cos(T * 83) + math.sin(T * 41)) * 12 * shake
    c.translate(W / 2 + sx, H / 2 + sy); c.scale(z, z); c.rotate(rot); c.translate(-cx, -cy)

def shots(t, keys, tr=0.55):
    """keys: [(t0, cx, cy, z)] -> interpolación suave entre planos"""
    cur = keys[0][1:]
    for i in range(1, len(keys)):
        t0 = keys[i][0]
        if t >= t0:
            k = in_out(seg(t, t0, t0 + tr))
            cur = tuple(lerp(a, b, k) for a, b in zip(cur, keys[i][1:]))
    return cur

def flash(c, a, color="#ffffff"):
    if a > 0.002: c.drawRect(skia.Rect.MakeWH(W, H), P(hexc(color, a)))

# ------------------------------------------------------------------ 0. FLASH-FORWARD (día 30)
CONF = [dict(x=random.Random(i).uniform(-1, 1), y=random.Random(i + 99).uniform(-1, 1),
             c=random.Random(i + 7).choice(["#ffd400", "#ff4fa0", "#2fd0ff", "#7cff6b", "#ffffff"]),
             s=random.Random(i + 3).uniform(.6, 1.4)) for i in range(90)]

def confetti(c, lt, cx=W / 2, cy=900, power=1500):
    for i, q in enumerate(CONF):
        x = cx + q["x"] * power * out_cubic(min(1, lt * 1.6)) + math.sin(lt * 3 + i) * 30
        y = cy + q["y"] * power * .6 * out_cubic(min(1, lt * 1.6)) + 600 * lt * lt
        c.save(); c.translate(x, y); c.rotate(lt * 400 * q["s"] + i * 37)
        c.scale(1, abs(math.cos(lt * 6 + i)))
        rect(c, -9 * q["s"], -5 * q["s"], 18 * q["s"], 10 * q["s"], P(hexc(q["c"])))
        c.restore()

def s_flash(c, x):
    t, d = x.t, x.d
    l0 = x.l(0)
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 800, 1400, [hexc("#ffe27a"), hexc("#ff9a1f"), hexc("#7a2a00")], [0, .45, 1])))
    rays(c, W / 2, 800, t, "#ffffff", .3, 22, 1800, 40)
    zoom = 1.25 - .25 * out_cubic(seg(t, 0, .35)) + .04 * t
    c.save(); camera(c, W / 2, 1000, zoom, rot=-3 + 3 * out_cubic(seg(t, 0, .4)), shake=pulse(t, 0, .35) * 1.6, T=x.T)
    # montaña de billetes
    r = random.Random(11)
    for i in range(60):
        bx = r.uniform(-80, W + 80); by = r.uniform(1450, 2000) - (1 - abs(bx - W / 2) / 700) * 260
        c.save(); c.translate(bx, by); c.rotate(r.uniform(-40, 40))
        rrect(c, -80, -38, 160, 76, 8, P(hexc(r.choice(["#3f9e4d", "#4fb35c", "#2f8a3f"]))))
        rrect(c, -68, -27, 136, 54, 5, P(hexc("#9fe0a8"), stroke=3)); text(c, "€", 0, 15, 40, hexc("#1f5e2a"))
        c.restore()
    character(c, "LEO", W / 2, 1000, 1.3, emo="excited", talk=x.talk("LEO"), t=t * 1.6, pose="fist", shades=True,
              light=("#fff3c0", .25))
    c.restore()
    coins(c, t + 1.0, 0, n=46, seed=21)
    confetti(c, t)
    # contador que golpea
    k = out_back(seg(t, .05, .4), 3.0)
    c.save(); c.translate(W / 2, 470); c.scale(k, k); c.rotate(-4)
    glow(c, 0, -50, 520, "#ffffff", .5)
    text(c, "1.000.000 €", 0, 0, 150, shader=lin(0, -130, 0, 10, [hexc("#ffffff"), hexc("#ffe066"), hexc("#f0a000")], [0, .4, 1]),
         stroke=14, stroke_color=hexc("#3a1800"), shadow=24)
    c.restore()
    k2 = out_back(seg(t, l0["s"] + 1.0, l0["s"] + 1.3), 2.5)
    if k2 > 0:
        c.save(); c.translate(W / 2 + 230, 640); c.scale(k2, k2); c.rotate(8)
        rrect(c, -190, -62, 380, 124, 24, P(hexc("#e0262f"))); rrect(c, -190, -62, 380, 124, 24, P(hexc("#ffffff"), stroke=6))
        text(c, "15 AÑOS", 0, 26, 76, hexc("#ffffff"))
        c.restore()
    hud(c, x.T, 30, 1_000_000, 1.0, money_flash=pulse(t, 0, .6))
    flash(c, pulse(t, 0, .12))

def gray_layer(c):
    p = skia.Paint()
    m = [0.30, 0.59, 0.11, 0, 0] * 3 + [0, 0, 0, 1, 0]
    p.setColorFilter(skia.ColorFilters.Matrix(m))
    c.saveLayer(None, p)

def s_freeze(c, x):
    t, d = x.t, x.d
    fx = x.at("flash", x.at("flash", 0).d - 0.02)
    c.save(); camera(c, W / 2, H / 2, 1 + .06 * out_cubic(seg(t, 0, .25)), rot=-1.5, T=x.T)
    gray_layer(c); s_flash(c, fx); c.restore()
    c.restore()
    c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#000000", .25)))
    k = out_back(seg(t, .05, .3), 2.5)
    c.save(); c.translate(W / 2, 1180); c.scale(k, k); c.rotate(-5)
    rrect(c, -330, -90, 660, 180, 30, P(hexc("#ffd400"))); rrect(c, -330, -90, 660, 180, 30, P(hexc("#000000"), stroke=8))
    text(c, "ESPERA...", 0, 36, 110, hexc("#000000"))
    c.restore()
    flash(c, pulse(t, 0, .08) * .8)

def vhs(c, t, amt=1.0, seed=0):
    r = random.Random(int(t * 60) + seed)
    for _ in range(int(14 * amt)):
        y = r.random() * H; h = r.uniform(6, 60)
        rect(c, 0, y, W, h, P(hexc(r.choice(["#ffffff", "#ff2a6a", "#2adfff"]), .12 * amt)))
    for yy in range(0, H, 6): c.drawLine(0, yy, W, yy, P(hexc("#000000", .18), stroke=2))

def s_rewind(c, x):
    t, d = x.t, x.d
    p = seg(t, 0, d - .15)
    fl = x.at("flash", 0); fd = fl.d
    rt = fd * (1 - in_cubic(p)) * 1.0
    c.save(); camera(c, W / 2 + math.sin(t * 40) * 14, H / 2, 1.05 + .3 * in_cubic(p), rot=math.sin(t * 30) * 2, T=x.T)
    gray_layer(c) if p > .5 else c.save()
    s_flash(c, x.at("flash", max(0.01, rt)))
    c.restore()
    c.restore()
    c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#10204a", .35 + .4 * p)))
    vhs(c, t, 1.0)
    day = max(1, int(round(30 - 29 * in_out(p))))
    text(c, "◀◀", 150, 230, 90, hexc("#ffffff"), fam="DejaVu Sans", alpha=.5 + .5 * (int(t * 6) % 2))
    text(c, "REBOBINANDO", 230, 225, 54, hexc("#ffffff"), align="left", fam="DejaVu Sans Mono", weight=700)
    c.save(); c.translate(W / 2, 1100)
    rrect(c, -300, -170, 600, 300, 40, P(hexc("#000000", .65)))
    text(c, "DÍA", 0, -80, 60, hexc("#ffd400"), weight=800, spacing=8)
    text(c, f"{day}", 0, 90, 200, hexc("#ffffff"), stroke=10)
    c.restore()
    flash(c, seg(t, d - .15, d), "#ffffff")

STAMPS = [("2", "HISTORIA", 200, 640, -14), ("3", "MATES", 880, 560, 12), ("4", "INGLÉS", 870, 1120, 9)]

def s_hook(c, x):
    t, d = x.t, x.d
    l0, l1 = x.l(0), x.l(1)
    st = x.sfx_all("stamp")
    tick = x.sfx_t("tick")
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [hexc("#07060d"), hexc("#1a1030"), hexc("#07060d")])))
    sh = sum(pulse(t, s, .18) for s in st)
    c.save(); camera(c, W / 2, H / 2, 1.0 + 0.08 * t / d, shake=sh * .8, T=x.T)
    text(c, "30", W / 2, 1050, 900, hexc("#ffffff", 0.04))
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 700, 900, [hexc("#9fb8ff", .22), hexc("#9fb8ff", 0)])))
    c.drawPath(path([(W / 2 - 120, -50), (W / 2 + 120, -50), (W / 2 + 520, 1700), (W / 2 - 520, 1700)]),
               P(shader=lin(0, 0, 0, 1700, [hexc("#dfe8ff", .16), hexc("#dfe8ff", 0)]), blur=30))
    DUST.dust(c, t, "#cfe0ff", alpha=.4)
    emo = "sad" if t < l1["s"] else "determined"
    character(c, "LEO", W / 2, 990, 1.2, emo=emo, talk=x.talk("LEO"), t=t, look=(0, .3) if emo == "sad" else (0, 0),
              light=("#9fb8ff", .12), pose="idle" if emo == "sad" else "fist")
    c.restore()
    # sellos de suspenso
    out = out_cubic(seg(t, l1["s"] - .2, l1["s"] + .2))
    for i, (n, sub, sx, sy, rot) in enumerate(STAMPS):
        if i >= len(st) or t < st[i]: continue
        k = 1 + 2.2 * (1 - out_cubic(seg(t, st[i], st[i] + .14)))
        a = seg(t, st[i], st[i] + .06) * (1 - out)
        c.save(); c.translate(sx, sy - out * 200); c.rotate(rot); c.scale(k, k)
        c.saveLayerAlpha(None, int(255 * a))
        rrect(c, -170, -120, 340, 240, 26, P(hexc("#e0262f"), stroke=12))
        rrect(c, -150, -100, 300, 200, 18, P(hexc("#e0262f"), stroke=4))
        text(c, n, 0, 50, 150, hexc("#e0262f"))
        text(c, sub, 0, -55, 38, hexc("#e0262f"), weight=800, spacing=4)
        text(c, "SUSPENSO", 0, 92, 34, hexc("#e0262f"), weight=800, spacing=6)
        c.restore(); c.restore()
    # reto + cuenta atrás
    if tick is not None and t > tick:
        k = out_back(seg(t, tick, tick + .35), 2)
        c.save(); c.translate(W / 2, 300); c.scale(k, k)
        rrect(c, -320, -60, 640, 100, 50, P(hexc("#e0262f")))
        text(c, "RETO", 0, 12, 58, hexc("#ffffff"), spacing=14)
        rrect(c, -420, 80, 840, 200, 34, P(hexc("#000000", .75))); rrect(c, -420, 80, 840, 200, 34, P(hexc("#ffd400"), stroke=5))
        rem = 30 * 86400 - (t - tick) * 3600 * 3
        dd = int(rem // 86400); hh = int(rem % 86400 // 3600); mm = int(rem % 3600 // 60); ss = int(rem % 60)
        text(c, f"{dd:02d}d {hh:02d}:{mm:02d}:{ss:02d}", 0, 215, 110, hexc("#ffd400"), fam="JetBrains Mono", weight=800)
        c.restore()
        ko = out_back(seg(t, tick + 1.6, tick + 2.0))
        if ko > 0:
            c.save(); c.translate(W / 2, 700); c.scale(ko, ko)
            text(c, "→ 1.000.000 €", 0, 0, 90, shader=lin(0, -80, 0, 10, [hexc("#ffffff"), hexc("#ffd34a"), hexc("#e09a0f")], [0, .4, 1]), stroke=10, stroke_color=hexc("#2a1700"))
            c.restore()
    flash(c, 1 - seg(t, 0, .2))

# ------------------------------------------------------------------ 2. TÍTULO
def s_title(c, x):
    t, d = x.t, x.d
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, H / 2, 1300, [hexc("#3a2a00"), hexc("#120c00"), hexc("#000000")], [0, .5, 1])))
    rays(c, W / 2, 860, t, "#ffd34a", .16, 18)
    c.save(); camera(c, W / 2, H / 2, 1 + .04 * t, shake=pulse(t, 0.1, .25), T=x.T)
    k = out_back(seg(t, 0.05, .5), 2.2)
    c.save(); c.translate(W / 2, 880); c.scale(k * 1.0, k * 1.0)
    gold = lin(0, -260, 0, 30, [hexc("#fffbe0"), hexc("#ffd34a"), hexc("#d18a00")], [0, .45, 1])
    text(c, "30", 0, -40, 460, shader=gold, stroke=18, stroke_color=hexc("#2b1a00"), shadow=30)
    text(c, "DÍAS", 0, 140, 190, shader=gold, stroke=14, stroke_color=hexc("#2b1a00"), shadow=20)
    # brillo que barre
    sh = (t * 900) % 2200 - 900
    c.restore()
    k2 = out_cubic(seg(t, .45, .9))
    text(c, "PARA SER MILLONARIO", W / 2, 1150 + 60 * (1 - k2), 78, hexc("#ffffff", k2), stroke=10,
         stroke_color=hexc("#000000", k2), spacing=4)
    k3 = out_back(seg(t, .9, 1.25))
    c.save(); c.translate(W / 2, 1300); c.scale(k3, k3)
    rrect(c, -330, -55, 660, 110, 55, P(hexc("#e0262f")))
    text(c, "CAPÍTULO 1 · EL TRATO", 0, 15, 40, hexc("#ffffff"), weight=800)
    c.restore()
    c.restore()
    flash(c, 1 - seg(t, 0, .35))
    flash(c, seg(t, d - .25, d), "#000000")

# ------------------------------------------------------------------ 3. COCINA
def kitchen_bg(c, t, x, dim=0.0):
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [hexc("#3d2b22"), hexc("#5a3f30"), hexc("#2a1d17")])))
    tp = P(hexc("#ffffff", .04), stroke=2)
    for yy in range(500, 1300, 90): c.drawLine(0, yy, W, yy, tp)
    for xx in range(0, W, 90): c.drawLine(xx, 500, xx, 1300, tp)
    li = 0.0
    rrect(c, 640, 260, 360, 420, 16, P(hexc("#1a1210")))
    rrect(c, 660, 280, 320, 380, 8, P(shader=lin(0, 280, 0, 660, [hexc("#0d1430"), hexc("#1f2b55")])))
    c.save(); c.clipRect(skia.Rect.MakeXYWH(660, 280, 320, 380)); RAIN.rain(c, t, (660, 280, 320, 380), .45); c.restore()
    c.drawLine(820, 280, 820, 660, P(hexc("#1a1210"), stroke=14)); c.drawLine(660, 470, 980, 470, P(hexc("#1a1210"), stroke=14))
    for i in range(3):
        rrect(c, 40 + i * 180, 230, 165, 280, 10, P(hexc("#6b4a37"))); rrect(c, 40 + i * 180, 230, 165, 280, 10, P(hexc("#000000", .25), stroke=4))
        rrect(c, 40 + i * 180 + 140, 360, 10, 50, 5, P(hexc("#c9a46a")))
    # reloj de pared
    oval(c, 560, 640, 62, 62, P(hexc("#efe6d6"))); oval(c, 560, 640, 62, 62, P(hexc("#3a2a20"), stroke=8))
    ang = t * 6
    c.drawLine(560, 640, 560 + 40 * math.sin(math.radians(ang)), 640 - 40 * math.cos(math.radians(ang)), P(hexc("#c0392b"), stroke=3))
    c.drawLine(560, 640, 590, 625, P(hexc("#222222"), stroke=6)); c.drawLine(560, 640, 556, 600, P(hexc("#222222"), stroke=5))
    sw = math.sin(t * 1.4) * 5
    c.save(); c.translate(540, 0); c.rotate(sw)
    c.drawLine(0, 0, 0, 330, P(hexc("#111111"), stroke=5))
    c.drawPath(path([(-90, 420), (-40, 330), (40, 330), (90, 420)]), P(hexc("#e2b04a")))
    oval(c, 0, 420, 90, 18, P(hexc("#fff2c4")))
    c.drawPath(path([(-90, 420), (90, 420), (520, 1900), (-520, 1900)]), P(shader=lin(0, 420, 0, 1900, [hexc("#ffdf9e", .22 * (1 - dim)), hexc("#ffdf9e", 0)]), blur=25, blend=skia.BlendMode.kScreen))
    c.restore()

def table(c):
    p = skia.Path(); p.moveTo(-200, 1330); p.lineTo(W + 200, 1330); p.lineTo(W + 200, H + 400); p.lineTo(-200, H + 400); p.close()
    c.drawPath(p, P(shader=lin(0, 1330, 0, H, [hexc("#8a5a35"), hexc("#5a3820")])))
    c.drawLine(-200, 1332, W + 200, 1332, P(hexc("#c08a58"), stroke=8))
    for yy in (1420, 1560, 1730): c.drawLine(-200, yy, W + 200, yy + 8, P(hexc("#000000", .12), stroke=3))
    oval(c, 900, 1420, 90, 22, P(hexc("#e8e2d6"))); rrect(c, 860, 1350, 80, 70, 12, P(hexc("#c94c3c")))
    # boletín sobre la mesa
    c.save(); c.translate(540, 1420); c.scale(1, .35); c.rotate(-8)
    rrect(c, -170, -210, 340, 420, 10, P(hexc("#fbf8ef"))); rect(c, -170, -210, 340, 70, P(hexc("#2c4a7a")))
    c.restore()

def report_insert(c, t, t0, t1, red_t):
    """primer plano del boletín deslizándose sobre la mesa"""
    k = out_cubic(seg(t, t0, t0 + .8)); ko = in_cubic(seg(t, t1 - .3, t1))
    if k <= 0 or ko >= 1: return
    c.save()
    c.saveLayerAlpha(None, int(255 * (1 - ko)))
    # mesa en primer plano (desenfocada en los bordes)
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [hexc("#7a4e2d"), hexc("#4e301b")])))
    for yy in range(0, H, 140): c.drawLine(0, yy + 30, W, yy + 60, P(hexc("#000000", .10), stroke=4))
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 900, 1000, [hexc("#ffdf9e", .25), hexc("#000000", 0)])))
    c.translate(W / 2 - 900 * (1 - k), 800); c.rotate(-8 + 6 * k); sc_ = 1.02 + .05 * seg(t, t0, t1); c.scale(sc_, sc_)
    rrect(c, -360, -440, 720, 900, 18, P(hexc("#000000", .45), blur=35))
    rrect(c, -360, -470, 720, 900, 18, P(hexc("#fbf8ef")))
    rect(c, -360, -470, 720, 130, P(hexc("#2c4a7a")))
    text(c, "BOLETÍN DE NOTAS", 0, -385, 50, hexc("#ffffff"))
    text(c, "Leo Martín · 4º ESO · 2ª evaluación", 0, -280, 34, hexc("#555555"), weight=600)
    rows = [("Matemáticas", "3"), ("Lengua", "4"), ("Inglés", "4"), ("Historia", "2"), ("Ed. Física", "9")]
    for i, (a, n) in enumerate(rows):
        y = -180 + i * 105
        c.drawLine(-310, y + 34, 310, y + 34, P(hexc("#000000", .1), stroke=2))
        text(c, a, -310, y, 48, hexc("#222222"), weight=700, align="left")
        text(c, n, 260, y + 4, 70, hexc("#d81e2a" if int(n) < 5 else "#1f9a4a"))
        if a == "Historia":
            r = seg(t, red_t, red_t + .5)
            if r > 0:
                arc = skia.Path(); arc.addArc(skia.Rect.MakeXYWH(195, y - 78, 130, 112), -90, 360 * r)
                c.drawPath(arc, P(hexc("#d81e2a"), stroke=9))
    text(c, "Observaciones: no muestra interés.", -310, 400, 32, hexc("#d81e2a"), weight=600, align="left", fam="DejaVu Serif")
    c.restore(); c.restore()

def handshake_insert(c, t, t0, t1):
    k = out_cubic(seg(t, t0, t0 + .28)); ko = seg(t, t1 - .2, t1)
    if t < t0 or ko >= 1: return
    c.saveLayerAlpha(None, int(255 * (1 - ko)))
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 900, 1100, [hexc("#5a3f30"), hexc("#1a100c")])))
    rays(c, W / 2, 900, t, "#ffd27a", .12 * k, 14)
    sh = pulse(t, t0 + .28, .2)
    c.save(); c.translate(math.sin(t * 90) * 14 * sh, 0)
    gap = 260 * (1 - k)
    # brazo de papá (camisa azul) desde la izquierda, de Leo (sudadera naranja) desde la derecha
    for side, col, col2, skin in ((-1, "#3b6fb6", "#294f86", "#e8b48e"), (1, "#ff7a2f", "#d9551a", "#f2c29b")):
        x0 = W / 2 + side * (70 + gap)
        c.drawPath(path([(x0 + side * 40, 860), (x0 + side * 700, 780), (x0 + side * 700, 1080), (x0 + side * 40, 1000)]),
                   P(shader=lin(0, 780, 0, 1080, [hexc(col), hexc(col2)])))
        rrect(c, x0 + (side - 1) * 55 + side * 30, 850, 110, 160, 30, P(hexc(col2)))
        oval(c, x0 - side * 30, 930, 120, 82, P(hexc(skin)))
        for f in range(4):
            oval(c, x0 - side * (120 - f * 4), 880 + f * 32, 34, 18, P(hexc(skin)))
            oval(c, x0 - side * (120 - f * 4), 880 + f * 32, 34, 18, P(hexc("#000000", .12), stroke=2))
    c.restore()
    if t > t0 + .25:
        ks = 1 + 1.6 * (1 - out_cubic(seg(t, t0 + .25, t0 + .4)))
        c.save(); c.translate(W / 2, 520); c.rotate(-6); c.scale(ks, ks)
        rrect(c, -300, -110, 600, 220, 30, P(hexc("#ffd400", .95)))
        rrect(c, -300, -110, 600, 220, 30, P(hexc("#1a1200"), stroke=10))
        text(c, "TRATO", 0, 55, 160, hexc("#1a1200"), spacing=8)
        c.restore()
        text(c, "30 DÍAS · 1.000.000 €", W / 2, 1300, 64, hexc("#ffffff"), stroke=10, alpha=seg(t, t0 + .5, t0 + .8))
    flash(c, pulse(t, t0 + .25, .15) * .8, "#fff3c4")
    c.restore()

def s_kitchen(c, x):
    t, d = x.t, x.d
    L = [x.l(i) for i in range(7)]  # 0 papá ¿un dos? 1 papá mírame 2 mamá 3 leo 4 papá ¿tú? 5 papá ultimátum 6 leo trato
    hit = x.sfx_t("hit"); hand = x.sfx_t("handshake")
    PAPA, MAMA, LEO = (300, 880), (790, 910), (540, 1150)
    keys = [(0, 540, 1000, 1.0),
            (L[1]["s"] - .15, 320, 960, 1.75),       # papá: "Leo. Mírame."
            (L[2]["s"] - .2, 770, 1000, 1.7),        # mamá
            (L[3]["s"] - .25, 540, 1150, 1.8),       # leo
            (L[4]["s"] - .1, 420, 1000, 1.25),       # papá + leo
            (L[5]["s"] - .05, 330, 950, 1.55),       # ultimátum
            (L[6]["s"] - .2, 540, 1160, 2.0)]        # leo: trato
    cx, cy, z = shots(t, keys, .45)
    if L[5]["s"] - .05 < t < L[6]["s"]:
        z += .35 * seg(t, L[5]["s"], L[6]["s"])     # empuje lento durante el ultimátum
    dim = smooth(seg(t, hit - .1, hit + .3)) * (1 - smooth(seg(t, hand, hand + .5)))
    c.save(); camera(c, cx, cy, z, shake=pulse(t, hit, .25) * .6, T=x.T)
    blur_begin(c, max(0, (z - 1.0)) * 9)
    kitchen_bg(c, t, x, dim)
    blur_end(c)
    # quién está desenfocado depende del plano
    def focus(px): return max(0, (z - 1.15)) * 7 * min(1, abs(px - cx) / 300)
    papa_emo = "neutral" if t < L[0]["s"] else ("smug" if L[4]["s"] - .1 < t < L[5]["s"] else "angry")
    blur_begin(c, focus(PAPA[0]))
    character(c, "PAPA", PAPA[0], PAPA[1], 1.12, emo=papa_emo, talk=x.talk("PAPA"), t=t,
              pose="point" if L[5]["s"] < t < L[6]["s"] else "crossed", look=(.6, .3), blink_seed=1, tilt=-3,
              rim=("#ffd9a0", .5))
    blur_end(c)
    blur_begin(c, focus(MAMA[0]))
    character(c, "MAMA", MAMA[0], MAMA[1], 1.08, emo="worried", talk=x.talk("MAMA"), t=t, pose="hips",
              look=(-.6, .4) if t < L[3]["s"] else (-.3, .5), blink_seed=2, tilt=3, rim=("#ffd9a0", .4))
    blur_end(c)
    if t < L[3]["s"] - .3: lemo, look = "sad", (0, .9)
    elif t < L[4]["e"]: lemo, look = "determined", (-.2, -.2)
    elif t < L[6]["s"] - .1: lemo, look = "worried", (-.5, -.1)
    else: lemo, look = "determined", (-.4, -.3)
    blur_begin(c, focus(LEO[0]) * .6)
    character(c, "LEO", LEO[0], LEO[1], 0.95, emo=lemo, talk=x.talk("LEO"), t=t, look=look, blink_seed=3, rim=("#ffd9a0", .45))
    blur_end(c)
    table(c)
    c.restore()
    # luz roja durante el ultimátum
    c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#7a0010", .28 * dim)))
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, H / 2, 1100, [hexc("#000000", 0), hexc("#000000", .5 * dim)])))
    # condiciones del trato, palabra a palabra
    if L[5]["s"] < t < hand:
        s5, e5 = L[5]["s"], L[5]["e"]; du = e5 - s5
        items = [(.0, "30 DÍAS", "#ffd400"), (.38, "SIN MÓVIL", "#ff4d5a"), (.68, "ACADEMIA EN VERANO", "#ff4d5a")]
        for i, (fr, s, col) in enumerate(items):
            ta = s5 + fr * du
            k = out_back(seg(t, ta, ta + .3), 2)
            if k <= 0: continue
            c.save(); c.translate(W / 2 + (i - 1) * 40, 330 + i * 120); c.rotate(-4 + i * 4); c.scale(k, k)
            wbox = tw(s, 66) + 70
            rrect(c, -wbox / 2, -55, wbox, 100, 22, P(hexc("#0b0b0b", .85)))
            rrect(c, -wbox / 2, -55, wbox, 100, 22, P(hexc(col), stroke=6))
            text(c, s, 0, 20, 66, hexc(col))
            c.restore()
    # rótulo de tiempo al principio
    if t < 2.2:
        a = seg(t, .2, .5) * (1 - seg(t, 1.7, 2.1))
        c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#000000", .35 * a)))
        text(c, "HACE 30 DÍAS", W / 2, 960, 110, hexc("#ffffff", a), stroke=10, stroke_color=hexc("#000000", a), spacing=6)
        text(c, "Martes, 21:47", W / 2, 1050, 48, hexc("#ffd400", a), weight=700, fam="JetBrains Mono")
    report_insert(c, t, L[0]["s"] - .9, L[1]["s"] - .15, L[0]["s"] + .3)
    handshake_insert(c, t, hand - .05, d + .1)
    flash(c, 1 - seg(t, 0, .35), "#000000")

# ------------------------------------------------------------------ 4. HABITACIÓN
CARDS = [("DEL", 91, "#f5c542"), ("MED", 88, "#cfd8e3"), ("DEF", 86, "#f5c542"), ("POR", 89, "#9ad1ff"),
         ("DEL", 93, "#ff9bd2"), ("MED", 90, "#f5c542"), ("EXT", 87, "#cfd8e3"), ("DEL", 94, "#b38cff"), ("MED", 85, "#9ad1ff")]

def player_card(c, x, y, s, rot, pos, ovr, col, seed):
    r = random.Random(seed)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    rrect(c, -95, -130, 190, 260, 22, P(hexc("#000000", .4), blur=14))
    rrect(c, -95, -135, 190, 260, 22, P(shader=lin(-95, -135, 95, 125, [hexc(col), mix_hex(col, "#000000", .35)])))
    rrect(c, -85, -125, 170, 240, 16, P(hexc("#ffffff", .35), stroke=3))
    text(c, str(ovr), -50, -72, 54, hexc("#1a1a1a"))
    text(c, pos, -50, -36, 26, hexc("#1a1a1a"), weight=800)
    oval(c, 25, -45, 40, 46, P(hexc("#1a1a1a", .25)))  # silueta
    rrect(c, -5, -5, 60, 40, 20, P(hexc("#1a1a1a", .25)))
    for i, lab in enumerate(["VEL", "TIR", "PAS", "REG"]):
        text(c, f"{r.randint(70, 97)} {lab}", -60 + (i % 2) * 85, 62 + (i // 2) * 34, 22, hexc("#1a1a1a"), weight=800, align="left")
    c.restore()

def s_bedroom(c, x):
    t, d = x.t, x.d
    L = [x.l(i) for i in range(6)]
    idea = x.sfx_t("idea")
    warm = smooth(seg(t, idea, idea + .8))
    zoom = 1.05 + 0.10 * smooth(t / d) + 0.25 * in_out(seg(t, L[1]["s"] - .2, L[1]["s"] + .4)) * (1 - in_out(seg(t, L[3]["s"] - .3, L[3]["s"] + .3)))
    c.save(); camera(c, 540, 1000 - 60 * warm, zoom, T=x.T, shake=pulse(t, idea, .2) * .4)
    blur_begin(c, (zoom - 1.0) * 8)
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [mix_hex("#0b1230", "#3a2a5a", warm), mix_hex("#141d45", "#5a3a5a", warm), mix_hex("#070a1c", "#24142a", warm)])))
    rrect(c, 90, 230, 380, 480, 16, P(hexc("#05070f")))
    rrect(c, 108, 248, 344, 444, 8, P(shader=lin(0, 248, 0, 692, [hexc("#0e1a44"), hexc("#26346e")])))
    glow(c, 360, 350, 160, "#cfe0ff", .5); oval(c, 360, 350, 46, 46, P(hexc("#eef3ff")))
    c.save(); c.clipRect(skia.Rect.MakeXYWH(108, 248, 344, 444)); RAIN.rain(c, t, (108, 248, 344, 444), .45, 1200); c.restore()
    c.drawLine(280, 248, 280, 692, P(hexc("#05070f"), stroke=12)); c.drawLine(108, 470, 452, 470, P(hexc("#05070f"), stroke=12))
    c.drawPath(path([(108, 248), (452, 248), (900, 1500), (300, 1500)]), P(shader=lin(0, 248, 0, 1500, [hexc("#9fb8ff", .12), hexc("#9fb8ff", 0)]), blur=20))
    c.save(); c.translate(760, 420); c.rotate(4)
    rrect(c, -130, -170, 260, 340, 6, P(hexc("#e43d3d"))); c.drawPath(path([(0, -110), (40, 40), (0, 20), (-40, 40)]), P(hexc("#ffffff")))
    oval(c, 0, 70, 14, 30, P(hexc("#ffc23d"))); text(c, "SUEÑA", 0, 140, 44, hexc("#ffffff"))
    c.restore()
    rect(c, 560, 700, 300, 14, P(hexc("#3b2a22")))
    for i, col in enumerate(["#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#f39c12"]):
        rect(c, 580 + i * 34, 590 + (i % 2) * 14, 28, 110 - (i % 2) * 14, P(hexc(col, .8)))
    # despertador digital
    rrect(c, 820, 1180, 200, 90, 14, P(hexc("#111111")))
    text(c, "03:12", 920, 1242, 54, hexc("#ff3b3b", .9 if int(t * 2) % 2 or t > 2 else .5), fam="JetBrains Mono", weight=800)
    rrect(c, -40, 1280, 1160, 700, 40, P(hexc("#2b3a7a"))); rrect(c, -40, 1260, 1160, 90, 40, P(hexc("#3d52a8")))
    rrect(c, 60, 1210, 300, 110, 50, P(hexc("#dfe6ff")))
    blur_end(c)
    if t < L[1]["s"]: emo, look = "tired", (0, .9)
    elif t < L[2]["s"]: emo, look = "happy", (.5, -.6)
    elif t < idea: emo, look = "sad", (0, .9)
    elif t < idea + 1.0: emo, look = "surprised", (.2, -.8)
    else: emo, look = "excited", (0, -.2)
    character(c, "LEO", 540, 1000, 1.15, emo=emo, talk=x.talk("LEO"), t=t, pose="phone", look=look,
              light=("#7cc4ff", .45 * (1 - warm) + .1), blink_seed=4, rim=("#9fb8ff", .5 * (1 - warm) + .2))
    if t > idea:
        k = out_elastic(seg(t, idea, idea + .9)); y0 = 700 + math.sin(t * 3) * 8
        c.save(); c.translate(540, y0); c.scale(k, k)
        rays(c, 0, 0, t, "#ffe27a", .25, 12, 500, 30)
        glow(c, 0, 0, 260, "#ffe27a", .7)
        oval(c, 0, 0, 70, 75, P(shader=rad(-20, -25, 90, [hexc("#ffffff"), hexc("#ffe680"), hexc("#ffc21a")])))
        rrect(c, -34, 62, 68, 50, 10, P(hexc("#9aa3b5")))
        c.drawLine(-30, 80, 30, 80, P(hexc("#6b7385"), stroke=5)); c.drawLine(-30, 96, 30, 96, P(hexc("#6b7385"), stroke=5))
        c.drawPath(path([(-18, 30), (-8, -10), (0, 20), (8, -10), (18, 30)], close=False), P(hexc("#c27a00"), stroke=5))
        c.restore()
    c.restore()
    # cromos de futbolistas en abanico (300 futbolistas)
    k_in = out_back(seg(t, L[1]["s"], L[1]["s"] + .6)); k_out = in_cubic(seg(t, L[2]["s"], L[2]["s"] + .5))
    if k_in > 0 and k_out < 1:
        n = len(CARDS)
        for i, (pos, ovr, col) in enumerate(CARDS):
            ki = out_back(seg(t, L[1]["s"] + i * .07, L[1]["s"] + .4 + i * .07))
            if ki <= 0.01: continue
            a = -60 + 120 * i / (n - 1)
            r_ = 380
            cx = W / 2 + math.sin(math.radians(a)) * r_ * ki
            cy = 820 - math.cos(math.radians(a)) * r_ * .55 * ki + k_out * (900 + i * 60)
            c.save(); c.saveLayerAlpha(None, int(255 * (1 - k_out * .6)))
            player_card(c, cx, cy, .85 * min(1, ki), a * .5 + k_out * (i - 4) * 30, pos, ovr, col, i)
            c.restore(); c.restore()
        cnt = int(300 * out_cubic(seg(t, L[1]["s"] + .2, L[1]["e"])))
        text(c, f"{cnt}", W / 2, 380, 170, hexc("#ffd400", 1 - k_out), stroke=12, stroke_color=hexc("#000000", 1 - k_out))
        text(c, "FUTBOLISTAS", W / 2, 450, 54, hexc("#ffffff", 1 - k_out), weight=800, spacing=8)
    # examen de historia en blanco
    ke = out_back(seg(t, L[2]["s"] + .2, L[2]["s"] + .6)); ko = in_cubic(seg(t, idea - .2, idea + .1))
    if ke > 0 and ko < 1:
        c.save(); c.translate(W / 2, 720 - ko * 1200); c.rotate(5); c.scale(ke * .9, ke * .9)
        rrect(c, -300, -330, 600, 640, 14, P(hexc("#000000", .4), blur=20))
        rrect(c, -300, -340, 600, 640, 14, P(hexc("#fdfcf5")))
        text(c, "EXAMEN DE HISTORIA", 0, -270, 42, hexc("#1d3a8a"))
        for i, q in enumerate(["1. ¿Año del descubrimiento?", "2. ¿Quién fue Carlos V?", "3. Revolución Francesa:",
                               "4. ¿Qué pasó en 1812?", "5. Fecha de la Constitución:"]):
            yy = -190 + i * 95
            text(c, q, -260, yy, 30, hexc("#333333"), weight=600, align="left", fam="DejaVu Serif")
            text(c, "???", -230, yy + 42, 30, hexc("#999999"), weight=700, align="left")
        k2 = out_back(seg(t, L[2]["s"] + 1.0, L[2]["s"] + 1.3), 2.5)
        if k2 > 0:
            c.save(); c.translate(190, -190); c.scale(k2, k2); c.rotate(-10)
            oval(c, 0, 0, 80, 70, P(hexc("#d81e2a"), stroke=8)); text(c, "2", 0, 34, 100, hexc("#d81e2a"))
            c.restore()
        c.restore()
    # tipografía cinética del descubrimiento
    if L[4]["s"] - .1 < t < L[5]["s"] + .1:
        s4, e4 = L[4]["s"], L[4]["e"]; mid = s4 + (e4 - s4) * .38
        k1 = out_back(seg(t, s4, s4 + .3)); strike = out_cubic(seg(t, mid - .1, mid + .25))
        c.save(); c.translate(W / 2, 330); c.scale(k1, k1)
        text(c, "EL PROBLEMA ERA YO", 0, 0, 74, hexc("#ffffff", 1 - .5 * strike), stroke=10)
        if strike > 0:
            c.drawLine(-380, -24, -380 + 760 * strike, -20, P(hexc("#ff3b3b"), stroke=14))
        c.restore()
        k2 = out_back(seg(t, mid + .2, mid + .5), 2)
        if k2 > 0:
            c.save(); c.translate(W / 2, 450); c.scale(k2, k2); c.rotate(-3)
            rrect(c, -440, -66, 880, 112, 24, P(hexc("#ffd400")))
            text(c, "ES CÓMO NOS HACEN ESTUDIAR", 0, 14, 56, hexc("#1a1200"))
            c.restore()
    if t > L[5]["s"] + .4:
        k = out_back(seg(t, L[5]["s"] + .4, L[5]["s"] + .8), 2)
        c.save(); c.translate(W / 2, 360); c.scale(k, k); c.rotate(-4)
        rrect(c, -380, -90, 760, 160, 36, P(hexc("#8b5cff")))
        text(c, "ESTUDIAR = JUGAR", 0, 25, 84, hexc("#ffffff"))
        c.restore()
    flash(c, pulse(t, idea, .3) * .7, "#fff3c0")
    flash(c, 1 - seg(t, 0, .5), "#000000")

# ------------------------------------------------------------------ 5. LOGO
def app_icon(c, x, y, s, t):
    c.save(); c.translate(x, y); c.scale(s, s)
    rrect(c, -150, -130, 300, 300, 74, P(hexc("#000000", .45), blur=30))
    rrect(c, -150, -150, 300, 300, 74, P(shader=lin(-150, -150, 150, 150, [hexc("#8b5cff"), hexc("#ff4fa0"), hexc("#ffb03b")], [0, .55, 1])))
    rrect(c, -150, -150, 300, 150, 74, P(hexc("#ffffff", .12)))
    c.drawPath(path([(-70, 5), (-20, 60), (75, -55)], close=False), P(hexc("#ffffff"), stroke=40))
    c.drawPath(path([(55, -105), (20, -40), (48, -40), (25, 15), (85, -60), (55, -60), (80, -105)]), P(hexc("#ffe14a")))
    c.restore()

def vibrant_bg(c, t, a="#1a0b3d", b="#3b0f5a"):
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, W, H, [hexc(a), hexc(b)])))
    for i, (col, r) in enumerate([("#8b5cff", 520), ("#ff4fa0", 460), ("#2fd0ff", 420)]):
        cx = W / 2 + math.sin(t * .5 + i * 2.1) * 380; cy = H / 2 + math.cos(t * .4 + i * 1.7) * 640
        c.drawCircle(cx, cy, r, P(shader=rad(cx, cy, r, [hexc(col, .35), hexc(col, 0)])))
    gp = P(hexc("#ffffff", .05), stroke=2)
    off = (t * 40) % 120
    for yy in range(-120, H + 120, 120): c.drawLine(0, yy + off, W, yy + off, gp)
    for xx in range(0, W + 1, 120): c.drawLine(xx, 0, xx, H, gp)

def s_logo(c, x):
    t, d = x.t, x.d
    pop = x.sfx_t("pop")
    vibrant_bg(c, t)
    rays(c, W / 2, 820, t, "#ffffff", .1 + .1 * seg(t, pop, pop + .3), 20)
    c.save(); camera(c, W / 2, H / 2, 1 + .05 * t, shake=pulse(t, pop, .2) * .5, T=x.T)
    k = out_back(seg(t, .25, .8), 2.0)
    app_icon(c, W / 2, 800, k * (1 + .05 * math.sin(t * 4)), t)
    name = "ApruebaYa"
    xx = W / 2 - tw(name, 150) / 2
    for i, ch in enumerate(name):
        kk = out_back(seg(t, pop - .25 + i * .04, pop + .05 + i * .04))
        wch = tw(ch, 150)
        c.save(); c.translate(xx + wch / 2, 1160 + 80 * (1 - kk)); c.scale(kk, kk)
        col = hexc("#ffffff") if i < 7 else hexc("#ffe14a")
        text(c, ch, 0, 0, 150, col, stroke=12, stroke_color=hexc("#2a0b45"), shadow=16)
        c.restore(); xx += wch
    k3 = out_cubic(seg(t, pop + .3, pop + .7))
    text(c, "ESTUDIA JUGANDO", W / 2, 1270, 52, hexc("#ffffff", .85 * k3), weight=700, spacing=10)
    c.restore()
    DUST.dust(c, t, "#ffffff", .5, 80)
    flash(c, pulse(t, pop, .25) * .6)
    flash(c, 1 - seg(t, 0, .3))

# ------------------------------------------------------------------ 6. EL PLAN
def phone_frame(c, x, y, s):
    c.save(); c.translate(x, y); c.scale(s, s)
    rrect(c, -290, -560, 580, 1140, 80, P(hexc("#000000", .5), blur=40))
    rrect(c, -290, -580, 580, 1160, 80, P(shader=lin(-290, 0, 290, 0, [hexc("#3a3a46"), hexc("#14141a"), hexc("#3a3a46")])))
    rrect(c, -270, -560, 540, 1120, 64, P(hexc("#0b0b12")))
    c.restore()

def phone_screen(c, x, y, s, t, x_):
    l0, l1 = x_.l(0), x_.l(1)
    shot = x_.sfx_t("camera")
    c.save(); c.translate(x, y); c.scale(s, s)
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-262, -552, 262, 552), 58, 58), True)
    gen0, quiz0 = shot + .5, shot + 2.6
    if t < gen0:
        # cámara apuntando a los apuntes
        rect(c, -262, -552, 524, 1104, P(hexc("#1b1b1b")))
        c.save(); c.rotate(-3 + math.sin(t * 2) * 1.5); c.translate(math.sin(t * 1.7) * 8, 0)
        rrect(c, -220, -380, 440, 700, 10, P(hexc("#fdfcf5")))
        for i in range(14): c.drawLine(-200, -330 + i * 46, 200, -330 + i * 46, P(hexc("#9fc3ff", .7), stroke=2))
        c.drawLine(-150, -380, -150, 320, P(hexc("#ff8a8a", .7), stroke=2))
        text(c, "Tema 5: Colón", -130, -345, 30, hexc("#1d3a8a"), weight=700, align="left", fam="DejaVu Serif")
        r = random.Random(3)
        for i in range(12):
            wv = skia.Path(); xx = -130; yy = -290 + i * 46; wv.moveTo(xx, yy)
            for k in range(r.randint(8, 14)): xx += 22; wv.quadTo(xx - 11, yy - r.uniform(6, 14) * (1 if k % 2 else -1), xx, yy)
            c.drawPath(wv, P(hexc("#2a3f8f", .85), stroke=3))
        text(c, "1492 →", -130, 280, 44, hexc("#c0392b"), weight=800, align="left", fam="DejaVu Serif")
        c.restore()
        # visor
        for sx in (-1, 1):
            for sy in (-1, 1):
                c.drawPath(path([(sx * 200, sy * 300 - sy * 60), (sx * 200, sy * 300), (sx * 200 - sx * 60, sy * 300)], close=False), P(hexc("#ffffff"), stroke=8))
        oval(c, 0, 460, 52, 52, P(hexc("#ffffff"))); oval(c, 0, 460, 62, 62, P(hexc("#ffffff"), stroke=6))
        flash_a = pulse(t, shot, .15)
        if flash_a: rect(c, -262, -552, 524, 1104, P(hexc("#ffffff", flash_a)))
    elif t < quiz0:
        rect(c, -262, -552, 524, 1104, P(shader=lin(0, -552, 0, 552, [hexc("#2a1060"), hexc("#7a1f86")])))
        app_icon(c, 0, -230, .55, t)
        for i in range(8):
            a = t * 4 + i * math.pi / 4
            oval(c, math.cos(a) * 110, 60 + math.sin(a) * 110, 13 - i, 13 - i, P(hexc("#ffffff", 1 - i / 9)))
        text(c, "La IA está creando", 0, 260, 44, hexc("#ffffff"), weight=800)
        text(c, "tu juego...", 0, 316, 44, hexc("#ffffff"), weight=800)
        pr = seg(t, gen0, quiz0 - .1)
        rrect(c, -200, 380, 400, 26, 13, P(hexc("#ffffff", .2))); rrect(c, -200, 380, 400 * pr, 26, 13, P(hexc("#ffe14a")))
        text(c, f"{int(pr * 100)}%", 0, 460, 36, hexc("#ffe14a"))
    else:
        qt = t - quiz0
        rect(c, -262, -552, 524, 1104, P(shader=lin(0, -552, 0, 552, [hexc("#1c1048"), hexc("#3d1470")])))
        # barra superior: puntos y racha
        pts = 100 * (t > l1["s"] + .2) + 250 * (t > l1["s"] + 1.2)
        text(c, f"{pts} pts", -220, -470, 40, hexc("#ffe14a"), align="left")
        streak = 3 + (t > l1["s"] + .7) * 1 + (t > l1["s"] + 1.4) * 1
        fl = skia.Path(); fl.moveTo(150, -470); fl.cubicTo(120, -500, 150, -530, 160, -560); fl.cubicTo(175, -530, 200, -510, 185, -470); fl.close()
        c.drawPath(fl, P(shader=lin(0, -560, 0, -470, [hexc("#ffe14a"), hexc("#ff5a1f")])))
        text(c, f"x{streak}", 240, -470, 40, hexc("#ffffff"), align="right")
        k = out_back(seg(qt, 0, .4))
        c.save(); c.scale(k, k)
        rrect(c, -230, -400, 460, 260, 30, P(hexc("#ffffff")))
        text(c, "PREGUNTA 4/10", 0, -345, 28, hexc("#8b5cff"), weight=800)
        text(c, "¿En qué año llegó", 0, -270, 42, hexc("#1a1a2e"), weight=800)
        text(c, "Colón a América?", 0, -215, 42, hexc("#1a1a2e"), weight=800)
        opts = ["1453", "1492", "1517", "1610"]
        pick = l0["e"] - .2
        for i, o in enumerate(opts):
            ki = out_back(seg(qt, .2 + i * .08, .5 + i * .08))
            yy = -90 + i * 140
            col = "#ffffff"; tcol = "#ffffff"
            if i == 1 and t > pick: col = "#22c55e"
            c.save(); c.translate(0, yy); c.scale(ki, ki)
            sel = i == 1 and t > pick
            rrect(c, -230, -55, 460, 110, 26, P(hexc(col, .95 if sel else .14)))
            rrect(c, -230, -55, 460, 110, 26, P(hexc("#ffffff", .5), stroke=3))
            text(c, o, 0, 16, 50, hexc(tcol))
            c.restore()
        c.restore()
        # +100 flotante
        for tt0, val in ((l1["s"] + .2, "+100"), (l1["s"] + 1.2, "+250")):
            if tt0 < t < tt0 + 1.0:
                q = seg(t, tt0, tt0 + 1.0)
                text(c, val, 150, -290 - 110 * q, 80, hexc("#ffe14a", 1 - q), stroke=8, stroke_color=hexc("#3a1a00", 1 - q))
        # ranking de amigos
        kr = out_cubic(seg(t, l1["s"] + 1.7, l1["s"] + 2.2))
        if kr > 0:
            c.save(); c.translate(0, 600 * (1 - kr))
            rrect(c, -240, 160, 480, 380, 30, P(hexc("#0d0820", .95)))
            text(c, "RANKING DE CLASE", 0, 215, 30, hexc("#ffe14a"), weight=800)
            for i, (n, p_) in enumerate([("Leo", 1350), ("Marta", 1200), ("Hugo", 980), ("Sara", 720)]):
                yy = 275 + i * 64
                text(c, f"{i + 1}.  {n}", -200, yy, 38, hexc("#ffffff" if i else "#ffe14a"), weight=800, align="left")
                text(c, f"{p_}", 200, yy, 38, hexc("#ffffff", .8), weight=700, align="right")
            c.restore()
    c.restore()

def s_plan(c, x):
    t, d = x.t, x.d
    l0, l1, l2 = x.l(0), x.l(1), x.l(2)
    vibrant_bg(c, t, "#0d1440", "#2a0f55")
    up = in_out(seg(t, l2["s"], l2["s"] + .6))
    c.save(); camera(c, W / 2, H / 2, 1 + .03 * math.sin(t * .8), rot=math.sin(t * .6) * .6, T=x.T)
    # tarjetas flotantes alrededor (paralaje)
    chips = [("+100 pts", "#ffe14a", 140, 380, -8), ("Racha x5", "#ff7a2f", 930, 520, 7),
             ("Nivel 12", "#5fe3c0", 150, 1300, 6), ("1º de clase", "#ff8fd0", 930, 1220, -6)]
    for i, (s, col, cx, cy, r) in enumerate(chips):
        ki = out_back(seg(t, l1["s"] + i * .25, l1["s"] + .4 + i * .25))
        if ki <= 0: continue
        ki *= 1 - up
        if ki <= 0.01: continue
        c.save(); c.translate(cx, cy + math.sin(t * 2 + i) * 14); c.rotate(r); c.scale(ki, ki)
        wbox = tw(s, 44) + 60
        rrect(c, -wbox / 2, -45, wbox, 90, 45, P(hexc(col)))
        text(c, s, 0, 15, 44, hexc("#14102a"))
        c.restore()
    ph_y = 900 - up * 220; ph_s = .95 - up * .3
    phone_frame(c, W / 2, ph_y, ph_s)
    phone_screen(c, W / 2, ph_y, ph_s, t, x)
    c.restore()
    if t > l2["s"] + .2:
        k = out_back(seg(t, l2["s"] + .2, l2["s"] + .6))
        c.save(); c.translate(W / 2, 1180); c.scale(k, k)
        glow(c, 0, -40, 460, "#ffc53d", .4)
        text(c, "1.000.000 €", 0, 0, 140, shader=lin(0, -120, 0, 10, [hexc("#ffffff"), hexc("#ffd34a"), hexc("#e09a0f")], [0, .4, 1]),
             stroke=12, stroke_color=hexc("#2a1700"), shadow=20)
        text(c, "EN 30 DÍAS", 0, 90, 60, hexc("#ffffff"), stroke=8)
        c.restore()
        coins(c, t, l2["s"] + .3, n=36, seed=8)
    flash(c, pulse(t, l2["s"], .25) * .5, "#fff3c4")
    flash(c, 1 - seg(t, 0, .25))

# ------------------------------------------------------------------ 7. CLIFFHANGER
def s_cliff(c, x):
    t, d = x.t, x.d
    l0, l1, l2 = x.l(0), x.l(1), x.l(2)
    boom = x.sfx_t("boom"); tod = l2["s"]
    end0 = l2["e"] + .7
    gold = smooth(seg(t, tod - .1, tod + .3))
    c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#050508")))
    red = seg(t, boom, boom + .1) * (1 - gold)
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 800, 1100, [mix_hex("#2a2a40", "#5a0a10", red, .95), hexc("#000000", 0)])))
    if gold > 0: c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 800, 1100, [hexc("#7a5200", .95 * gold), hexc("#000000", 0)])))
    if gold > 0: rays(c, W / 2, 760, t, "#ffd34a", .14 * gold, 18)
    c.save()
    z = 1.2 + .25 * smooth(seg(t, 0, boom)) + .15 * out_cubic(seg(t, boom, boom + .3)) - .2 * out_cubic(seg(t, tod, tod + .5))
    camera(c, W / 2, 900, z, shake=pulse(t, boom, .35) * 1.2 + pulse(t, tod, .2) * .5, T=x.T)
    emo = "worried" if t < boom else ("shock" if t < tod - .2 else ("sad" if t < tod else "determined"))
    character(c, "LEO", W / 2, 900, 1.3, emo=emo, talk=x.talk("LEO"), t=t, look=(0, .4) if emo == "sad" else (0, 0),
              light=("#ff2a2a", .25 * red), rim=("#ffd34a", .7 * gold) if gold > 0 else ("#9fb8ff", .3),
              pose="fist" if t > tod + .2 else "idle")
    c.restore()
    if boom < t < end0 + .5:
        kout = seg(t, end0, end0 + .4)
        k = out_back(seg(t, boom, boom + .25), 2.5) * (1 - kout)
        g = pulse(t, boom, .5)
        c.save(); c.translate(W / 2, 360 - 60 * gold); c.scale(k * (1 - .25 * gold), k * (1 - .25 * gold)); c.rotate(-3)
        for dx, col in ((-10 * g - 3, "#ff0040"), (10 * g + 3, "#00e5ff")):
            text(c, "NO SÉ", dx, -60, 170, hexc(col, .7 * (1 - gold))); text(c, "PROGRAMAR", dx, 110, 150, hexc(col, .7 * (1 - gold)))
        text(c, "NO SÉ", 0, -60, 170, hexc("#ffffff"), stroke=14)
        text(c, "PROGRAMAR", 0, 110, 150, hexc("#ffffff"), stroke=14)
        c.restore()
        if t > tod:
            kt = out_back(seg(t, tod, tod + .3), 3) * (1 - kout)
            c.save(); c.translate(W / 2 + 120, 600); c.rotate(-8); c.scale(kt, kt)
            glow(c, 0, -40, 380, "#ffc53d", .5)
            text(c, "...TODAVÍA", 0, 0, 130, shader=lin(0, -110, 0, 10, [hexc("#ffffff"), hexc("#ffd34a"), hexc("#e09a0f")], [0, .4, 1]),
                 stroke=12, stroke_color=hexc("#2a1700"), shadow=20)
            c.restore()
        r = random.Random(int(t * 30))
        for i in range(int(8 * g)):
            yy = r.random() * H
            rect(c, 0, yy, W, r.uniform(4, 30), P(hexc(r.choice(["#ff0040", "#00e5ff", "#ffffff"]), .25 * g)))
    if t > end0:
        k = out_cubic(seg(t, end0, end0 + .5))
        c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#000000", .78 * k)))
        c.save(); c.translate(0, 80 * (1 - k))
        text(c, "MAÑANA", W / 2, 600, 70, hexc("#ffd400", k), weight=800, spacing=12)
        text(c, "DÍA 2", W / 2, 800, 220, hexc("#ffffff", k), stroke=14, stroke_color=hexc("#000000", k), shadow=20)
        text(c, "Aprender a programar", W / 2, 920, 60, hexc("#ffffff", .9 * k), weight=800)
        text(c, "en 24 horas", W / 2, 995, 60, hexc("#ffffff", .9 * k), weight=800)
        kb = out_back(seg(t, end0 + .4, end0 + .8)) * (1 + .05 * math.sin(t * 8))
        c.save(); c.translate(W / 2, 1190); c.scale(kb, kb)
        rrect(c, -260, -70, 520, 140, 70, P(hexc("#e0262f")))
        text(c, "SÍGUEME ➜", 0, 22, 64, hexc("#ffffff"), fam="DejaVu Sans")
        c.restore()
        for i in range(30):
            xx = 90 + i * 30.5
            rrect(c, xx, 1380, 24, 24, 6, P(hexc("#ffd400", k) if i < 1 else hexc("#ffffff", .25 * k)))
        text(c, "Capítulo 1 de 30 · El trato", W / 2, 1480, 40, hexc("#ffffff", .7 * k), weight=700)
        c.restore()
    flash(c, pulse(t, boom, .12), "#ffffff")
    flash(c, pulse(t, tod, .15) * .7, "#fff3c4")
    flash(c, 1 - seg(t, 0, .4), "#000000")

SCENE_FUNCS = {"flash": s_flash, "freeze": s_freeze, "rewind": s_rewind, "title": s_title, "kitchen": s_kitchen, "bedroom": s_bedroom,
               "logo": s_logo, "plan": s_plan, "cliff": s_cliff}
# escenas en las que se muestra el HUD (día / dinero)
HUD_SCENES = {"kitchen", "bedroom", "logo", "plan"}
# escenas sin subtítulos (texto grande propio)
NO_SUBS = set()

WHIP_IN = {"kitchen", "logo", "plan"}
VIGNETTE = {"cliff": 0.75, "kitchen": 0.62, "bedroom": 0.62}
