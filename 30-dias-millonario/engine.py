"""Motor gráfico (skia): utilidades, personajes, subtítulos y HUD de la serie."""
import math, random
import numpy as np
import skia

W, H = 1080, 1920

# ---------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def out_cubic(t): t = clamp(t); return 1 - (1 - t) ** 3
def in_cubic(t): t = clamp(t); return t ** 3
def in_out(t): t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def out_back(t, s=1.70158):
    t = clamp(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2
def out_elastic(t):
    t = clamp(t)
    if t in (0, 1): return t
    return 2 ** (-10 * t) * math.sin((t * 10 - .75) * (2 * math.pi) / 3) + 1
def pulse(t, a, d): return math.exp(-max(0, t - a) / d) if t >= a else 0.0

def hexc(h, a=1.0):
    h = h.lstrip('#')
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(clamp(a) * 255))
def mix_hex(h1, h2, t, a=1.0):
    c1 = [int(h1.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    c2 = [int(h2.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    c = [int(lerp(x, y, clamp(t))) for x, y in zip(c1, c2)]
    return skia.Color(*c, int(clamp(a) * 255))

def P(color=None, stroke=0, blur=0, shader=None, blend=None, cap_round=True, alpha=None):
    p = skia.Paint(AntiAlias=True)
    if color is not None: p.setColor(color)
    if alpha is not None: p.setAlphaf(clamp(alpha))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        if cap_round:
            p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None: p.setShader(shader)
    if blend is not None: p.setBlendMode(blend)
    return p

def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, pos)
def rad(cx, cy, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(1, r), cols, pos)

def oval(c, cx, cy, rx, ry, p): c.drawOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), p)
def rrect(c, x, y, w, h, r, p): c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)
def rect(c, x, y, w, h, p): c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)

def path(pts, close=True, curve=False):
    p = skia.Path()
    p.moveTo(*pts[0])
    if curve and len(pts) > 2:
        for i in range(1, len(pts) - 1):
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
            p.quadTo(pts[i][0], pts[i][1], mx, my)
        p.lineTo(*pts[-1])
    else:
        for q in pts[1:]: p.lineTo(*q)
    if close: p.close()
    return p

# ---------------------------------------------------------------- texto
_TF = {}
def tf(weight=900, fam="Inter Display", italic=False):
    k = (weight, fam, italic)
    if k not in _TF:
        _TF[k] = skia.Typeface(fam, skia.FontStyle(weight, skia.FontStyle.kNormal_Width,
                               skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant))
    return _TF[k]
def font(size, weight=900, fam="Inter Display"):
    f = skia.Font(tf(weight, fam), size); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True)
    return f
def tw(s, size, weight=900, fam="Inter Display"): return font(size, weight, fam).measureText(s)

def text(c, s, x, y, size, color=None, weight=900, align="center", stroke=0, stroke_color=None,
         shader=None, shadow=0, fam="Inter Display", alpha=1.0, spacing=0):
    f = font(size, weight, fam)
    w = f.measureText(s) + spacing * max(0, len(s) - 1)
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    def draw(p, dx=0, dy=0):
        if spacing:
            xx = x0
            for ch in s:
                c.drawString(ch, xx + dx, y + dy, f, p); xx += f.measureText(ch) + spacing
        else:
            c.drawString(s, x0 + dx, y + dy, f, p)
    if shadow:
        draw(P(skia.Color(0, 0, 0, int(150 * alpha)), blur=shadow), 0, shadow * 0.6)
    if stroke:
        sp = P(stroke_color if stroke_color is not None else hexc("#000000", alpha), stroke=stroke)
        draw(sp)
    p = P(color if color is not None else hexc("#ffffff", alpha), shader=shader)
    if shader is not None and alpha < 1: p.setAlphaf(alpha)
    draw(p)
    return w

# ---------------------------------------------------------------- grano / viñeta
_GRAIN = None
def grain_images():
    global _GRAIN
    if _GRAIN is None:
        r = np.random.default_rng(3); _GRAIN = []
        for _ in range(6):
            g = r.integers(0, 255, (480, 270), dtype=np.uint8)
            a = np.dstack([g, g, g, np.full_like(g, 255)])
            _GRAIN.append(skia.Image.fromarray(np.ascontiguousarray(a)))
    return _GRAIN

def post(c, frame, vignette=0.55, grain=0.06):
    p = P(shader=rad(W / 2, H * 0.48, H * 0.75, [hexc("#000000", 0), hexc("#000000", 0),
                                                  hexc("#000000", vignette)], [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    if grain:
        img = grain_images()[frame % 6]
        gp = skia.Paint(); gp.setAlphaf(grain); gp.setBlendMode(skia.BlendMode.kOverlay)
        c.drawImageRect(img, skia.Rect.MakeWH(W, H), skia.SamplingOptions(), gp)

# ---------------------------------------------------------------- partículas
class Particles:
    def __init__(self, n, seed=1, **kw):
        r = random.Random(seed)
        self.p = [dict(x=r.random() * W, y=r.random() * H, s=r.uniform(.4, 1), ph=r.random() * 6.28,
                       v=r.uniform(.5, 1.5)) for _ in range(n)]
    def dust(self, c, t, color="#ffd27a", alpha=0.6, rise=40):
        for q in self.p:
            y = (q["y"] - t * rise * q["v"]) % H
            x = q["x"] + math.sin(t * 0.7 + q["ph"]) * 25
            a = alpha * (0.5 + 0.5 * math.sin(t * 2 + q["ph"]))
            oval(c, x, y, 3 * q["s"] + 1, 3 * q["s"] + 1, P(hexc(color, a), blur=2 * q["s"] + .5))
    def rain(self, c, t, rect=None, alpha=0.35, speed=1500):
        x0, y0, w, h = rect or (0, 0, W, H)
        p = P(hexc("#bcd3ff", alpha), stroke=2)
        for q in self.p:
            y = y0 + (q["y"] / H * h + t * speed * q["v"]) % h
            x = x0 + (q["x"] / W * w - (y - y0) * 0.12) % w
            c.drawLine(x, y, x - 6, y + 40 * q["v"], p)

def coins(c, t, t0, n=40, seed=5):
    """lluvia de billetes y monedas desde t0"""
    if t < t0: return
    r = random.Random(seed); lt = t - t0
    for i in range(n):
        x = r.random() * W; d = r.uniform(0, 1.2); sp = r.uniform(500, 900); rot = r.uniform(-1, 1)
        y = -120 + (lt - d) * sp
        if lt < d or y > H + 100: continue
        c.save(); c.translate(x + math.sin(lt * 3 + i) * 40, y); c.rotate(rot * 180 + lt * 160 * rot)
        if i % 3:
            sx = abs(math.cos(lt * 4 + i))
            c.scale(1, 0.3 + 0.7 * sx)
            rrect(c, -55, -28, 110, 56, 6, P(hexc("#3f9e4d")))
            rrect(c, -47, -20, 94, 40, 4, P(hexc("#7fd18a"), stroke=3))
            text(c, "€", 0, 14, 36, hexc("#1f5e2a"))
        else:
            sx = abs(math.cos(lt * 5 + i))
            c.scale(0.25 + 0.75 * sx, 1)
            oval(c, 0, 0, 34, 34, P(shader=lin(-34, -34, 34, 34, [hexc("#fff1a6"), hexc("#f0b323"), hexc("#b8770b")])))
            oval(c, 0, 0, 25, 25, P(hexc("#a8690a", .6), stroke=3))
            text(c, "€", 0, 12, 32, hexc("#8a5205"))
        c.restore()

def rays(c, cx, cy, t, color="#ffffff", alpha=0.12, n=16, r=1600, speed=12):
    c.save(); c.translate(cx, cy); c.rotate(t * speed)
    p = P(shader=rad(0, 0, r, [hexc(color, alpha), hexc(color, 0)]))
    for i in range(n):
        a = 2 * math.pi * i / n; da = math.pi / n * 0.55
        c.drawPath(path([(0, 0), (math.cos(a - da) * r, math.sin(a - da) * r),
                         (math.cos(a + da) * r, math.sin(a + da) * r)]), p)
    c.restore()

def glow(c, x, y, r, color, a=0.6):
    c.drawCircle(x, y, r, P(shader=rad(x, y, r, [hexc(color, a), hexc(color, 0)]), blend=skia.BlendMode.kScreen))

# ---------------------------------------------------------------- personajes
CHARS = {
    "LEO": dict(skin="#f2c29b", skin2="#d99a74", hair="#4a2c1a", hair2="#6e4329", shirt="#ff7a2f",
                shirt2="#d9551a", style="spiky", kid=True, eye="#4a2f1d"),
    "PAPA": dict(skin="#e8b48e", skin2="#c98b66", hair="#2b2622", hair2="#5a514a", shirt="#3b6fb6",
                 shirt2="#294f86", style="short", mustache=True, glasses=True, eye="#2c1f16"),
    "MAMA": dict(skin="#f0bf9a", skin2="#d19774", hair="#8a3b20", hair2="#b5582f", shirt="#2fa58f",
                 shirt2="#1f7a69", style="long", earrings=True, lips="#c2455a", eye="#3d5a2a"),
}

def _brows(c, sp, emo, k):
    col = hexc(sp["hair"]); p = P(col, stroke=11 if not sp.get("kid") else 10)
    for s in (-1, 1):
        x0, x1 = s * 18, s * 56; y = -46
        if emo == "angry":   a0, a1 = y + 8, y - 8
        elif emo in ("sad", "worried"): a0, a1 = y - 9, y + 4
        elif emo in ("surprised", "shock"): a0, a1 = y - 16, y - 14
        elif emo == "determined": a0, a1 = y + 4, y - 4
        else: a0, a1 = y - 2, y - 4
        pp = skia.Path(); pp.moveTo(x0, a0); pp.quadTo((x0 + x1) / 2, min(a0, a1) - 6, x1, a1)
        c.drawPath(pp, p)

def _eyes(c, sp, emo, blink, look):
    lx, ly = look
    for s in (-1, 1):
        ex, ey = s * 37, -6
        ry = 21 * (1 - 0.92 * blink)
        if emo in ("surprised", "shock"): ry *= 1.15
        oval(c, ex, ey, 18, ry, P(hexc("#ffffff")))
        if ry > 4:
            c.save(); c.clipRRect(skia.RRect.MakeOval(skia.Rect.MakeLTRB(ex - 18, ey - ry, ex + 18, ey + ry)), True)
            ir = 12 if emo != "shock" else 9
            oval(c, ex + lx * 6, ey + ly * 6 + 2, ir, ir, P(hexc(sp["eye"])))
            oval(c, ex + lx * 6, ey + ly * 6 + 2, ir * .55, ir * .55, P(hexc("#120a06")))
            oval(c, ex + lx * 6 + 4, ey + ly * 6 - 3, 4, 4, P(hexc("#ffffff")))
            # párpado superior (cansado / triste / decidido)
            lid = {"sad": .35, "tired": .45, "determined": .3, "angry": .3, "smug": .4}.get(emo, 0.08)
            if lid: rect(c, ex - 20, ey - ry - 2, 40, 2 * ry * lid + 2, P(hexc(sp["skin2"])))
            c.restore()
        oval(c, ex, ey, 18, max(ry, 1.5), P(hexc("#3a2416", .9), stroke=3.5))

def _mouth(c, sp, emo, op):
    y = 52
    if op > 0.06:
        h = 6 + op * 30; w = 30 - op * 5
        if emo in ("happy", "excited", "proud"): w += 6
        c.save()
        oval(c, 0, y + h * 0.35, w, h, P(hexc("#5a1f22")))
        c.clipRRect(skia.RRect.MakeOval(skia.Rect.MakeLTRB(-w, y + h * .35 - h, w, y + h * .35 + h)), True)
        oval(c, 0, y + h * 1.1, w * .8, h * .6, P(hexc("#e0606b")))
        rect(c, -w, y + h * .35 - h - 2, 2 * w, h * .35 + 4, P(hexc("#ffffff")))
        c.restore()
        if sp.get("lips"): oval(c, 0, y + h * .35, w, h, P(hexc(sp["lips"]), stroke=4))
    else:
        pp = skia.Path()
        if emo in ("happy", "excited", "proud", "smug"):
            pp.moveTo(-26, y - 4); pp.quadTo(0, y + 20, 26, y - 4 - (8 if emo == "smug" else 0))
        elif emo in ("sad", "angry", "worried"):
            pp.moveTo(-22, y + 8); pp.quadTo(0, y - 8, 22, y + 8)
        elif emo in ("surprised", "shock"):
            oval(c, 0, y + 6, 12, 15, P(hexc("#5a1f22"))); return
        elif emo == "determined":
            pp.moveTo(-20, y + 2); pp.quadTo(0, y + 6, 22, y - 2)
        else:
            pp.moveTo(-20, y); pp.quadTo(0, y + 8, 20, y)
        c.drawPath(pp, P(hexc(sp.get("lips", "#7a3a2c")), stroke=6))

def _hair_back(c, sp):
    if sp["style"] == "long":
        p = path([(-108, -40), (-120, 60), (-125, 190), (-70, 230), (70, 230), (125, 190), (120, 60), (108, -40)], curve=True)
        c.drawPath(p, P(shader=lin(0, -100, 0, 230, [hexc(sp["hair2"]), hexc(sp["hair"])])))

def _hair_front(c, sp, t):
    if sp["style"] == "spiky":
        pts = [(-98, 10), (-104, -40), (-120, -70), (-88, -82), (-100, -120), (-55, -112), (-55, -150),
               (-15, -124), (5, -162), (30, -122), (70, -146), (72, -108), (112, -110), (96, -70),
               (118, -48), (100, -26), (98, 8), (82, -38), (52, -56), (40, -32), (14, -60), (-6, -36),
               (-34, -62), (-50, -38), (-78, -52)]
        sw = math.sin(t * 2) * 2
        pts = [(x + sw * (y < -100), y) for x, y in pts]
        p = path(pts, curve=False)
        c.drawPath(p, P(shader=lin(0, -160, 0, 0, [hexc(sp["hair2"]), hexc(sp["hair"])])))
        c.drawPath(path([(-40, -110), (-10, -130), (20, -112)], close=False, curve=True), P(hexc("#ffffff", .15), stroke=6))
    elif sp["style"] == "short":
        p = skia.Path(); p.moveTo(-98, -10); p.cubicTo(-108, -90, -60, -128, 0, -126)
        p.cubicTo(60, -128, 108, -90, 98, -10); p.cubicTo(90, -50, 70, -70, 40, -78)
        p.cubicTo(10, -84, -20, -84, -50, -76); p.cubicTo(-80, -68, -92, -40, -98, -10); p.close()
        c.drawPath(p, P(shader=lin(0, -130, 0, -20, [hexc(sp["hair2"]), hexc(sp["hair"])])))
        for s in (-1, 1): rect(c, s * 102 - 6, -30, 12, 34, P(hexc(sp["hair2"])))
    elif sp["style"] == "long":
        p = skia.Path(); p.moveTo(-104, 40); p.cubicTo(-120, -100, -50, -135, 10, -128)
        p.cubicTo(80, -124, 120, -80, 104, 40); p.cubicTo(96, -20, 80, -50, 50, -66)
        p.cubicTo(20, -40, -40, -40, -70, -50); p.cubicTo(-90, -20, -96, 0, -104, 40); p.close()
        c.drawPath(p, P(shader=lin(0, -130, 0, 40, [hexc(sp["hair2"]), hexc(sp["hair"])])))
        oval(c, 30, -128, 40, 30, P(hexc(sp["hair"])))  # moño

def _body(c, sp, pose, t, breath):
    sh, sh2 = hexc(sp["shirt"]), hexc(sp["shirt2"])
    c.save(); c.scale(1, 1 + breath * 0.01)
    # cuello
    rect(c, -26, 70, 52, 70, P(hexc(sp["skin2"])))
    # torso
    p = skia.Path(); p.moveTo(-70, 125); p.cubicTo(-150, 140, -175, 200, -180, 300)
    p.lineTo(-200, 1000); p.lineTo(200, 1000); p.lineTo(180, 300); p.cubicTo(175, 200, 150, 140, 70, 125); p.close()
    c.drawPath(p, P(shader=lin(-180, 120, 180, 600, [sh, sh2])))
    if sp.get("kid"):  # sudadera: capucha, cordones, bolsillo
        hood = skia.Path(); hood.moveTo(-85, 120); hood.cubicTo(-60, 190, 60, 190, 85, 120)
        hood.cubicTo(60, 160, -60, 160, -85, 120)
        c.drawPath(hood, P(sh2, stroke=22))
        for s in (-1, 1): c.drawLine(s * 22, 165, s * 26, 265, P(hexc("#ffffff", .9), stroke=6))
        rrect(c, -95, 420, 190, 110, 30, P(hexc("#000000", .12)))
    elif sp["style"] == "short":  # camisa con cuello
        for s in (-1, 1):
            c.drawPath(path([(0, 150), (s * 70, 118), (s * 60, 190)]), P(hexc("#e9eef7")))
        c.drawLine(0, 160, 0, 620, P(hexc("#000000", .15), stroke=4))
        for y in (220, 300, 380): oval(c, 0, y, 6, 6, P(hexc("#e9eef7")))
    else:
        c.drawPath(path([(-50, 128), (0, 175), (50, 128)], close=False, curve=True), P(sh2, stroke=14))
    # brazos
    arm = P(shader=lin(-200, 200, 200, 600, [sh, sh2]), stroke=78)
    skin = P(hexc(sp["skin"]))
    if pose == "crossed":
        c.drawPath(path([(-150, 220), (-150, 380), (60, 360)], close=False, curve=True), arm)
        c.drawPath(path([(150, 220), (150, 400), (-60, 380)], close=False, curve=True), arm)
        oval(c, 80, 356, 34, 30, skin); oval(c, -80, 378, 34, 30, skin)
    elif pose == "phone":
        c.drawPath(path([(-150, 220), (-140, 420), (-30, 420)], close=False, curve=True), arm)
        c.drawPath(path([(150, 220), (140, 420), (30, 420)], close=False, curve=True), arm)
        rrect(c, -48, 300, 96, 150, 14, P(hexc("#16161e")))
        rrect(c, -40, 308, 80, 134, 9, P(shader=lin(0, 300, 0, 450, [hexc("#7cc4ff"), hexc("#4a5bff")])))
        oval(c, -40, 420, 32, 28, skin); oval(c, 40, 420, 32, 28, skin)
    elif pose == "hips":
        for s in (-1, 1):
            c.drawPath(path([(s * 150, 220), (s * 230, 380), (s * 160, 480)], close=False, curve=True), arm)
            oval(c, s * 160, 490, 32, 30, skin)
    elif pose == "point":
        c.drawPath(path([(-150, 220), (-170, 420), (-160, 1000)], close=False, curve=True), arm)
        c.drawPath(path([(150, 220), (260, 230), (330, 140)], close=False, curve=True), arm)
        oval(c, 340, 125, 30, 30, skin)
        c.drawLine(350, 110, 380, 70, P(hexc(sp["skin"]), stroke=20))
    elif pose == "fist":
        c.drawPath(path([(-150, 220), (-170, 420), (-160, 1000)], close=False, curve=True), arm)
        c.drawPath(path([(150, 220), (240, 300), (210, 120)], close=False, curve=True), arm)
        oval(c, 205, 105, 40, 38, skin)
    else:
        for s in (-1, 1):
            c.drawPath(path([(s * 150, 220), (s * 172, 420), (s * 160, 1000)], close=False, curve=True), arm)
    c.restore()

def character(c, who, x, y, scale=1.0, emo="neutral", talk=0.0, t=0.0, pose="idle", look=(0, 0),
              tilt=0.0, blink_seed=0, light=None, flip=False):
    """Dibuja un personaje de busto. (x, y) = centro de la cabeza."""
    sp = CHARS[who]
    # parpadeo pseudoaleatorio
    bt = (t + blink_seed * 1.7) % 3.7
    blink = 1 - abs(bt - 0.08) / 0.08 if bt < 0.16 else 0.0
    if emo == "tired": blink = max(blink, .2)
    bob = math.sin(t * 2.1 + blink_seed) * 3 + talk * 4
    breath = math.sin(t * 2.1 + blink_seed)
    c.save(); c.translate(x, y + bob); c.scale(scale * (-1 if flip else 1), scale)
    # sombra suave detrás
    oval(c, 0, 360, 250, 380, P(hexc("#000000", .25), blur=40))
    _hair_back(c, sp)
    _body(c, sp, pose, t, breath)
    c.save(); c.rotate(tilt + math.sin(t * 1.3 + blink_seed) * 1.5 + talk * math.sin(t * 9) * 2)
    # orejas
    for s in (-1, 1):
        oval(c, s * 92, 5, 18, 26, P(hexc(sp["skin2"])))
    # cabeza
    hp = skia.Path(); hp.addOval(skia.Rect.MakeLTRB(-95, -115, 95, 110))
    c.drawPath(hp, P(shader=rad(-30, -50, 200, [hexc(sp["skin"]), hexc(sp["skin"]), hexc(sp["skin2"])], [0, .5, 1])))
    oval(c, 0, -2, 95, 112, P(hexc(sp["skin2"], .9), stroke=4))
    if sp.get("kid"):
        for s in (-1, 1): oval(c, s * 52, 30, 18, 10, P(hexc("#ff7f7f", .35), blur=5))
    _eyes(c, sp, emo, blink, look)
    _brows(c, sp, emo, 0)
    # nariz
    np_ = skia.Path(); np_.moveTo(-4, 8); np_.quadTo(8, 26, -6, 30)
    c.drawPath(np_, P(hexc(sp["skin2"]), stroke=5))
    if sp.get("mustache"):
        m = skia.Path(); m.moveTo(-40, 46); m.cubicTo(-30, 26, -6, 30, 0, 38); m.cubicTo(6, 30, 30, 26, 40, 46)
        m.cubicTo(20, 40, 8, 44, 0, 44); m.cubicTo(-8, 44, -20, 40, -40, 46); m.close()
    _mouth(c, sp, emo, talk)
    if sp.get("mustache"): c.drawPath(m, P(hexc(sp["hair"])))
    if sp.get("glasses"):
        g = P(hexc("#1b1b1b"), stroke=5)
        for s in (-1, 1): rrect(c, s * 37 - 28, -28, 56, 42, 12, g)
        c.drawLine(-9, -10, 9, -10, g)
        for s in (-1, 1): rrect(c, s * 37 - 24, -24, 26, 12, 6, P(hexc("#ffffff", .25)))
    if sp.get("earrings"):
        for s in (-1, 1): oval(c, s * 94, 38, 8, 8, P(hexc("#ffd34a")))
    _hair_front(c, sp, t)
    if light:  # luz de color sobre la cara (pantalla del móvil, rayos...)
        col, a = light
        c.drawPath(hp, P(shader=rad(0, 80, 230, [hexc(col, a), hexc(col, 0)]), blend=skia.BlendMode.kScreen))
    c.restore()
    c.restore()

# ---------------------------------------------------------------- subtítulos
def chunk_line(text, max_chars=18):
    words = text.split(); chunks = []; cur = []
    for w in words:
        if cur and (len(" ".join(cur + [w])) > max_chars):
            chunks.append(cur); cur = []
        cur.append(w)
        if w[-1] in ".?!:" and len(" ".join(cur)) > 6:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

SPK_COLOR = {"LEO": "#ffd400", "PAPA": "#6fb6ff", "MAMA": "#5fe3c0", "MARTA": "#ff8fd0", "ORTEGA": "#c9a7ff"}

def subtitles(c, lines, T, y=1450):
    for ln in lines:
        if not (ln["start"] - 0.05 <= T <= ln["end"] + 0.15): continue
        chunks = chunk_line(ln["text"])
        allw = [w for ch in chunks for w in ch]
        tot = sum(len(w) + 2 for w in allw)
        d = ln["end"] - ln["start"]
        # tiempo de cada palabra proporcional a sus letras
        times = []; acc = 0
        for w in allw:
            times.append(ln["start"] + d * acc / tot); acc += len(w) + 2
        times.append(ln["end"])
        k = 0; ci = len(chunks) - 1
        for i, ch in enumerate(chunks):
            if T < times[k + len(ch)] or i == len(chunks) - 1: ci = i; break
            k += len(ch)
        ch = chunks[ci]; t0 = times[k]
        pop = out_back(seg(T, t0, t0 + 0.18))
        size = 84
        words = [w for w in ch]
        sp = 30
        ws = [tw(w, size) for w in words]
        total = sum(ws) + sp * (len(ws) - 1)
        x = W / 2 - total / 2
        c.save(); c.translate(W / 2, y); c.scale(0.85 + 0.15 * pop, 0.85 + 0.15 * pop); c.translate(-W / 2, -y)
        hl = SPK_COLOR.get(ln["speaker"], "#ffd400")
        for j, w in enumerate(words):
            wi = k + j
            active = times[wi] <= T < times[wi + 1]
            said = T >= times[wi]
            col = hexc(hl) if active else hexc("#ffffff", 1 if said else 0.92)
            s = 1.07 if active else 1.0
            cx = x + ws[j] / 2
            c.save(); c.translate(cx, y); c.scale(s, s); c.rotate(-1.5 if active else 0)
            text(c, w, 0, 0, size, col, stroke=16, stroke_color=hexc("#000000"), shadow=10)
            c.restore()
            x += ws[j] + sp
        c.restore()
        # etiqueta de quién habla (si no es el narrador)
        if ln["speaker"] != "LEO" or ln.get("tag"):
            name = {"PAPA": "PAPÁ", "MAMA": "MAMÁ"}.get(ln["speaker"], ln["speaker"])
            a = seg(T, ln["start"] - .05, ln["start"] + .15)
            wbox = tw(name, 34, 800) + 40
            rrect(c, W / 2 - wbox / 2, y - 150, wbox, 54, 27, P(hexc(hl, a)))
            text(c, name, W / 2, y - 111, 34, hexc("#101010", a), weight=800)
        break

# ---------------------------------------------------------------- HUD serie
def hud(c, T, day, money, alpha=1.0, money_flash=0.0, money_override=None):
    if alpha <= 0: return
    c.saveLayerAlpha(None, int(255 * alpha))
    # pastilla de día
    rrect(c, 44, 70, 300, 92, 46, P(hexc("#000000", .55)))
    rrect(c, 44, 70, 300, 92, 46, P(hexc("#ffffff", .25), stroke=3))
    text(c, "DÍA", 124, 132, 34, hexc("#ffd400"), weight=800)
    text(c, f"{day}/30", 240, 135, 50, hexc("#ffffff"))
    # barra de 30 días
    for i in range(30):
        x = 44 + i * 33.2
        rrect(c, x, 180, 27, 12, 6, P(hexc("#ffd400") if i < day else hexc("#ffffff", .25)))
    # dinero
    s = money_override or (f"{money:,.0f} €".replace(",", "."))
    wbox = tw(s, 50) + 120
    x0 = W - 44 - wbox
    rrect(c, x0, 70, wbox, 92, 46, P(hexc("#000000", .55)))
    rrect(c, x0, 70, wbox, 92, 46, P(hexc("#ffd400", .35 + .6 * money_flash), stroke=3 + 4 * money_flash))
    oval(c, x0 + 52, 116, 26, 26, P(shader=lin(x0 + 26, 90, x0 + 78, 142, [hexc("#fff1a6"), hexc("#e6a417")])))
    text(c, "€", x0 + 52, 128, 30, hexc("#8a5205"))
    text(c, s, x0 + 92, 135, 50, mix_hex("#ffffff", "#ffd400", money_flash), align="left")
    c.restore()
