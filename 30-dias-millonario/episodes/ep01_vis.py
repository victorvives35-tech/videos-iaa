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

# ------------------------------------------------------------------ 1. HOOK
def s_hook(c, x):
    t, d = x.t, x.d
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [hexc("#07060d"), hexc("#141024"), hexc("#07060d")])))
    c.save(); camera(c, W / 2, H / 2, 1.0 + 0.06 * t / d, T=x.T)
    # números gigantes de fondo
    text(c, "30", W / 2, 1050, 900, hexc("#ffffff", 0.035 + 0.02 * math.sin(t)))
    # foco
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 700, 900, [hexc("#ffcf7a", .28), hexc("#ffcf7a", 0)])))
    c.drawPath(path([(W / 2 - 120, -50), (W / 2 + 120, -50), (W / 2 + 520, 1700), (W / 2 - 520, 1700)]),
               P(shader=lin(0, 0, 0, 1700, [hexc("#fff2c9", .18), hexc("#fff2c9", 0)]), blur=30))
    DUST.dust(c, t, alpha=.5)
    emo = "sad" if t < x.l(1)["s"] else "determined"
    character(c, "LEO", W / 2, 860, 1.35, emo=emo, talk=x.talk("LEO"), t=t, look=(0, .2 if emo == "sad" else 0),
              light=("#ffcf7a", .15))
    c.restore()
    # textos cinéticos
    l1, l2 = x.l(1), x.l(2)
    if t > l1["s"] + 0.6:
        k = out_back(seg(t, l1["s"] + .6, l1["s"] + 1.0))
        c.save(); c.translate(W / 2, 360); c.scale(k, k)
        text(c, "30 DÍAS", 0, 0, 150, shader=lin(0, -120, 0, 20, [hexc("#fff5b8"), hexc("#ffb21e")]), stroke=12,
             stroke_color=hexc("#3a2000"), shadow=20)
        c.restore()
    if t > l2["s"]:
        k = out_back(seg(t, l2["s"], l2["s"] + .35))
        p = in_cubic(seg(t, l2["s"] + .1, l2["s"] + 1.3))
        val = int(1_000_000 * p)
        s = f"{val:,} €".replace(",", ".")
        c.save(); c.translate(W / 2, 560); c.scale(k, k)
        glow(c, 0, -50, 420, "#ffc53d", .35 * k)
        text(c, s, 0, 0, 128, shader=lin(0, -110, 0, 10, [hexc("#ffffff"), hexc("#ffd34a"), hexc("#e09a0f")], [0, .4, 1]),
             stroke=10, stroke_color=hexc("#2a1700"), shadow=20)
        c.restore()
        coins(c, t, l2["s"] + 1.2, n=22)
    flash(c, pulse(t, l2["s"], .25) * .6, "#fff3c4")
    flash(c, 1 - seg(t, 0, .5), "#000000")

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
    text(c, "CAPÍTULO 1 · NO LLEGARÁS A NADA", 0, 15, 40, hexc("#ffffff"), weight=800)
    c.restore()
    c.restore()
    flash(c, 1 - seg(t, 0, .35))
    flash(c, seg(t, d - .25, d), "#000000")

# ------------------------------------------------------------------ 3. COCINA
def kitchen_bg(c, t, x):
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [hexc("#3d2b22"), hexc("#5a3f30"), hexc("#2a1d17")])))
    # azulejos
    tp = P(hexc("#ffffff", .04), stroke=2)
    for yy in range(500, 1300, 90): c.drawLine(0, yy, W, yy, tp)
    for xx in range(0, W, 90): c.drawLine(xx, 500, xx, 1300, tp)
    # ventana con tormenta
    lt = x.sfx_t("thunder")
    li = max(pulse(t, lt, .12), pulse(t, lt + .35, .1) * .7) if lt is not None else 0
    rrect(c, 640, 260, 360, 420, 16, P(hexc("#1a1210")))
    rrect(c, 660, 280, 320, 380, 8, P(shader=lin(0, 280, 0, 660, [mix_hex("#0d1430", "#e9efff", li), mix_hex("#1f2b55", "#aebcff", li)])))
    if li > .2:
        c.drawPath(path([(820, 280), (790, 400), (830, 410), (780, 560), (840, 430), (805, 420), (840, 280)]), P(hexc("#ffffff", li)))
    c.save(); c.clipRect(skia.Rect.MakeXYWH(660, 280, 320, 380)); RAIN.rain(c, t, (660, 280, 320, 380), .5); c.restore()
    c.drawLine(820, 280, 820, 660, P(hexc("#1a1210"), stroke=14)); c.drawLine(660, 470, 980, 470, P(hexc("#1a1210"), stroke=14))
    # armarios
    for i in range(3):
        rrect(c, 40 + i * 180, 230, 165, 280, 10, P(hexc("#6b4a37"))); rrect(c, 40 + i * 180, 230, 165, 280, 10, P(hexc("#000000", .25), stroke=4))
        rrect(c, 40 + i * 180 + 140, 360, 10, 50, 5, P(hexc("#c9a46a")))
    # lámpara colgante que oscila
    sw = math.sin(t * 1.4) * 6
    c.save(); c.translate(540, 0); c.rotate(sw)
    c.drawLine(0, 0, 0, 330, P(hexc("#111111"), stroke=5))
    c.drawPath(path([(-90, 420), (-40, 330), (40, 330), (90, 420)]), P(hexc("#e2b04a")))
    oval(c, 0, 420, 90, 18, P(hexc("#fff2c4")))
    c.drawPath(path([(-90, 420), (90, 420), (520, 1900), (-520, 1900)]), P(shader=lin(0, 420, 0, 1900, [hexc("#ffdf9e", .22), hexc("#ffdf9e", 0)]), blur=25, blend=skia.BlendMode.kScreen))
    c.restore()
    return li

def table(c):
    p = skia.Path(); p.moveTo(-40, 1330); p.lineTo(W + 40, 1330); p.lineTo(W + 40, H + 40); p.lineTo(-40, H + 40); p.close()
    c.drawPath(p, P(shader=lin(0, 1330, 0, H, [hexc("#8a5a35"), hexc("#5a3820")])))
    c.drawLine(-40, 1332, W + 40, 1332, P(hexc("#c08a58"), stroke=8))
    for yy in (1420, 1560, 1730): c.drawLine(0, yy, W, yy + 8, P(hexc("#000000", .12), stroke=3))
    # taza y plato
    oval(c, 880, 1420, 90, 22, P(hexc("#e8e2d6"))); rrect(c, 840, 1350, 80, 70, 12, P(hexc("#c94c3c")))

def report_card(c, t, t0, t1):
    k = out_back(seg(t, t0, t0 + .45)); ko = in_cubic(seg(t, t1 - .35, t1))
    if k <= 0 or ko >= 1: return
    c.save(); c.translate(W / 2, 760 + 1400 * ko + 600 * (1 - k)); c.rotate(-6 + 4 * k)
    rrect(c, -330, -380, 660, 760, 18, P(hexc("#000000", .4), blur=30))
    rrect(c, -330, -400, 660, 760, 18, P(hexc("#fbf8ef")))
    rect(c, -330, -400, 660, 120, P(hexc("#2c4a7a")))
    text(c, "BOLETÍN DE NOTAS", 0, -322, 46, hexc("#ffffff"))
    text(c, "Alumno: Leo M. · 4º ESO", 0, -220, 34, hexc("#444444"), weight=600)
    rows = [("Matemáticas", "3"), ("Lengua", "4"), ("Inglés", "4"), ("Historia", "2"), ("Ed. Física", "8")]
    for i, (a, n) in enumerate(rows):
        y = -130 + i * 95
        c.drawLine(-280, y + 30, 280, y + 30, P(hexc("#000000", .1), stroke=2))
        text(c, a, -280, y, 44, hexc("#222222"), weight=700, align="left")
        col = "#d81e2a" if int(n) < 5 else "#1f9a4a"
        text(c, n, 240, y + 4, 64, hexc(col), align="center")
        if a == "Historia":
            r = seg(t, t0 + .6, t0 + 1.2)
            if r > 0:
                arc = skia.Path(); arc.addArc(skia.Rect.MakeXYWH(185, y - 72, 110, 100), -90, 360 * r)
                c.drawPath(arc, P(hexc("#d81e2a"), stroke=8))
    c.restore()

def s_kitchen(c, x):
    t, d = x.t, x.d
    L = [x.l(i) for i in range(5)]  # papá, mamá, papá, leo, papá
    PAPA, MAMA, LEO = (300, 900), (790, 930), (540, 1150)
    keys = [(0, 540, 1000, 1.0), (L[0]["s"] + 1.6, 330, 1000, 1.45), (L[1]["s"], 760, 1020, 1.45),
            (L[2]["s"], 330, 1000, 1.5), (L[3]["s"] - .2, 540, 1180, 1.65), (L[4]["s"], 400, 1000, 1.3),
            (L[4]["e"] + .1, 540, 1050, 1.05)]
    cx, cy, z = shots(t, keys)
    li = x.sfx_t("thunder")
    shake = pulse(t, li, .3) * .8 if li else 0
    c.save(); camera(c, cx, cy, z, shake=shake, T=x.T)
    lt = kitchen_bg(c, t, x)
    ang = "angry"
    character(c, "PAPA", PAPA[0], PAPA[1], 1.12, emo=ang if t > L[0]["s"] else "neutral", talk=x.talk("PAPA"), t=t,
              pose="crossed" if t < L[2]["s"] else "point", look=(.6, .3), blink_seed=1, tilt=-3)
    character(c, "MAMA", MAMA[0], MAMA[1], 1.08, emo="worried", talk=x.talk("MAMA"), t=t, pose="hips",
              look=(-.6, .4), blink_seed=2, tilt=3)
    lemo = "sad" if t < L[3]["s"] - .3 else ("determined" if t < L[4]["s"] else "sad")
    character(c, "LEO", LEO[0], LEO[1], 0.95, emo=lemo, talk=x.talk("LEO"), t=t,
              look=(0, .8) if lemo == "sad" else (0, 0), blink_seed=3)
    table(c)
    c.restore()
    # tinte rojo y relámpago
    c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#ff2020", .12 * seg(t, L[0]["s"], L[0]["s"] + 1) * (1 - seg(t, L[3]["s"] - .5, L[3]["s"])))))
    flash(c, lt * .55, "#dfe8ff")
    report_card(c, t, L[0]["s"] - .3, L[0]["s"] + 2.4)
    # golpe de puerta al final
    dt = x.sfx_t("door")
    flash(c, seg(t, dt, dt + .05) * (1 - seg(t, dt + .1, d)) * 0 + seg(t, dt - .02, dt + .08), "#000000")
    flash(c, 1 - seg(t, 0, .3), "#000000")

# ------------------------------------------------------------------ 4. HABITACIÓN
def s_bedroom(c, x):
    t, d = x.t, x.d
    l0, l1, l2 = x.l(0), x.l(1), x.l(2)
    idea = x.sfx_t("idea")
    warm = smooth(seg(t, idea, idea + .8))
    c.save(); camera(c, 540, 1000 - 40 * warm, 1.05 + 0.18 * smooth(t / d), T=x.T, shake=pulse(t, idea, .2) * .4)
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=lin(0, 0, 0, H, [mix_hex("#0b1230", "#3a2a5a", warm), mix_hex("#141d45", "#5a3a5a", warm), mix_hex("#070a1c", "#24142a", warm)])))
    # ventana con luna y lluvia
    rrect(c, 90, 230, 380, 480, 16, P(hexc("#05070f")))
    rrect(c, 108, 248, 344, 444, 8, P(shader=lin(0, 248, 0, 692, [hexc("#0e1a44"), hexc("#26346e")])))
    glow(c, 360, 350, 160, "#cfe0ff", .5); oval(c, 360, 350, 46, 46, P(hexc("#eef3ff")))
    c.save(); c.clipRect(skia.Rect.MakeXYWH(108, 248, 344, 444)); RAIN.rain(c, t, (108, 248, 344, 444), .45, 1200); c.restore()
    c.drawLine(280, 248, 280, 692, P(hexc("#05070f"), stroke=12)); c.drawLine(108, 470, 452, 470, P(hexc("#05070f"), stroke=12))
    # luz de luna en la pared
    c.drawPath(path([(108, 248), (452, 248), (900, 1500), (300, 1500)]), P(shader=lin(0, 248, 0, 1500, [hexc("#9fb8ff", .12), hexc("#9fb8ff", 0)]), blur=20))
    # pósters
    c.save(); c.translate(760, 420); c.rotate(4)
    rrect(c, -130, -170, 260, 340, 6, P(hexc("#e43d3d"))); c.drawPath(path([(0, -110), (40, 40), (0, 20), (-40, 40)]), P(hexc("#ffffff")))
    oval(c, 0, 70, 14, 30, P(hexc("#ffc23d"))); text(c, "SUEÑA", 0, 140, 44, hexc("#ffffff"))
    c.restore()
    c.save(); c.translate(960, 820); c.rotate(-5)
    rrect(c, -90, -110, 180, 220, 6, P(hexc("#2f7de1"))); oval(c, 0, -10, 55, 55, P(hexc("#ff9b2f")))
    c.drawLine(-55, -10, 55, -10, P(hexc("#2f7de1"), stroke=5)); c.drawLine(0, -65, 0, 45, P(hexc("#2f7de1"), stroke=5))
    c.restore()
    # estantería con libros
    rect(c, 560, 700, 300, 14, P(hexc("#3b2a22")))
    for i, col in enumerate(["#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#f39c12"]):
        rect(c, 580 + i * 34, 590 + (i % 2) * 14, 28, 110 - (i % 2) * 14, P(hexc(col, .8)))
    # cama
    rrect(c, -40, 1280, 1160, 700, 40, P(hexc("#2b3a7a"))); rrect(c, -40, 1260, 1160, 90, 40, P(hexc("#3d52a8")))
    rrect(c, 60, 1210, 300, 110, 50, P(hexc("#dfe6ff")))
    # Leo con el móvil
    emo = "tired" if t < l1["s"] else ("sad" if t < idea else ("surprised" if t < idea + 1.2 else "excited"))
    phone_light = ("#7cc4ff", .45 * (1 - warm) + .1)
    character(c, "LEO", 540, 1000, 1.15, emo=emo, talk=x.talk("LEO"), t=t, pose="phone",
              look=(0, .9) if t < idea else (.2, -.8), light=phone_light, blink_seed=4)
    # bombilla
    if t > idea:
        k = out_elastic(seg(t, idea, idea + .9)); y0 = 690 + math.sin(t * 3) * 8
        c.save(); c.translate(540, y0); c.scale(k, k)
        rays(c, 0, 0, t, "#ffe27a", .25, 12, 500, 30)
        glow(c, 0, 0, 260, "#ffe27a", .7)
        oval(c, 0, 0, 70, 75, P(shader=rad(-20, -25, 90, [hexc("#ffffff"), hexc("#ffe680"), hexc("#ffc21a")])))
        rrect(c, -34, 62, 68, 50, 10, P(hexc("#9aa3b5"))); c.drawLine(-30, 80, 30, 80, P(hexc("#6b7385"), stroke=5)); c.drawLine(-30, 96, 30, 96, P(hexc("#6b7385"), stroke=5))
        c.drawPath(path([(-18, 30), (-8, -10), (0, 20), (8, -10), (18, 30)], close=False), P(hexc("#c27a00"), stroke=5))
        c.restore()
    c.restore()
    flash(c, pulse(t, idea, .3) * .7, "#fff3c0")
    # texto "¿y si...?" cinético
    if l2["s"] + 1.1 < t:
        k = out_back(seg(t, l2["s"] + 1.1, l2["s"] + 1.5))
        c.save(); c.translate(W / 2, 330); c.scale(k, k); c.rotate(-4)
        rrect(c, -300, -80, 600, 120, 30, P(hexc("#ffd400")))
        text(c, "APUNTES = JUEGO", 0, 0, 64, hexc("#1a1200"))
        c.restore()
    flash(c, 1 - seg(t, 0, .6), "#000000")

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
    l0, l1 = x.l(0), x.l(1)
    boom = x.sfx_t("boom")
    c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#050508")))
    red = seg(t, boom, boom + .1)
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(W / 2, 800, 1000, [mix_hex("#2a2a40", "#5a0a10", red, .9), hexc("#000000", 0)])))
    end0 = l1["e"] + .5
    c.save()
    z = 1.2 + .25 * smooth(seg(t, 0, boom)) + .15 * out_cubic(seg(t, boom, boom + .3))
    camera(c, W / 2, 860, z, shake=pulse(t, boom, .35) * 1.2, T=x.T)
    character(c, "LEO", W / 2, 860, 1.3, emo="worried" if t < boom else "shock", talk=x.talk("LEO"), t=t,
              look=(0, 0), light=("#ff2a2a", .25 * red))
    c.restore()
    if t > boom and t < end0 + .5:
        k = out_back(seg(t, boom, boom + .25), 2.5) * (1 - seg(t, end0, end0 + .4))
        g = pulse(t, boom, .5)
        c.save(); c.translate(W / 2, 400); c.scale(k, k); c.rotate(-3)
        for dx, col in ((-10 * g - 3, "#ff0040"), (10 * g + 3, "#00e5ff")):
            text(c, "NO SÉ", dx, -60, 170, hexc(col, .7)); text(c, "PROGRAMAR", dx, 110, 150, hexc(col, .7))
        text(c, "NO SÉ", 0, -60, 170, hexc("#ffffff"), stroke=14)
        text(c, "PROGRAMAR", 0, 110, 150, hexc("#ffffff"), stroke=14)
        c.restore()
        # líneas glitch
        r = random.Random(int(t * 30))
        for i in range(int(8 * g)):
            yy = r.random() * H
            rect(c, 0, yy, W, r.uniform(4, 30), P(hexc(r.choice(["#ff0040", "#00e5ff", "#ffffff"]), .25 * g)))
    # tarjeta final
    if t > end0:
        k = out_cubic(seg(t, end0, end0 + .5))
        c.drawRect(skia.Rect.MakeWH(W, H), P(hexc("#000000", .75 * k)))
        c.save(); c.translate(0, 80 * (1 - k))
        text(c, "MAÑANA", W / 2, 640, 70, hexc("#ffd400", k), weight=800, spacing=12)
        text(c, "DÍA 2", W / 2, 840, 220, hexc("#ffffff", k), stroke=14, stroke_color=hexc("#000000", k), shadow=20)
        text(c, "Aprender a programar", W / 2, 960, 60, hexc("#ffffff", .9 * k), weight=800)
        text(c, "en 24 horas", W / 2, 1035, 60, hexc("#ffffff", .9 * k), weight=800)
        kb = out_back(seg(t, end0 + .4, end0 + .8)) * (1 + .05 * math.sin(t * 8))
        c.save(); c.translate(W / 2, 1230); c.scale(kb, kb)
        rrect(c, -260, -70, 520, 140, 70, P(hexc("#e0262f")))
        text(c, "SÍGUEME ➜", 0, 22, 64, hexc("#ffffff"), fam="DejaVu Sans")
        c.restore()
        # progreso de la serie
        for i in range(30):
            xx = 90 + i * 30.5
            rrect(c, xx, 1420, 24, 24, 6, P(hexc("#ffd400", k) if i < 1 else hexc("#ffffff", .25 * k)))
        text(c, "1 de 30 capítulos", W / 2, 1520, 40, hexc("#ffffff", .7 * k), weight=700)
        c.restore()
    flash(c, pulse(t, boom, .12), "#ffffff")

SCENE_FUNCS = {"hook": s_hook, "title": s_title, "kitchen": s_kitchen, "bedroom": s_bedroom,
               "logo": s_logo, "plan": s_plan, "cliff": s_cliff}
# escenas en las que se muestra el HUD (día / dinero)
HUD_SCENES = {"kitchen", "bedroom", "logo", "plan"}
# escenas sin subtítulos (texto grande propio)
NO_SUBS = set()
