# -*- coding: utf-8 -*-
"""Genera el archivo ASS: subtítulos karaoke, tarjetas de detalle, etiquetas y rótulos."""
import json, os, re

WORK = os.environ["WORK"]
tl = json.load(open(os.path.join(WORK, "timeline.json")))
D = tl["duration"]


def ts(t):
    t = max(0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Poppins ExtraBold,62,&H0033D6FF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,5,3,2,120,120,64,1
Style: Big,Anton,200,&H00FFFFFF,&H00FFFFFF,&H00B43CFF,&H00000000,0,0,0,0,100,100,2,0,1,6,0,5,0,0,0,1
Style: Card,Anton,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,3,0,1,4,0,5,0,0,0,1
Style: Kicker,Anton,58,&H00B43CFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,12,0,1,3,0,5,0,0,0,1
Style: BadgeC,Poppins Bold,30,&H00FFFFFF,&H00FFFFFF,&H0059AA1F,&H0059AA1F,0,0,0,0,100,100,1,0,3,10,0,9,40,48,48,1
Style: BadgeT,Poppins Bold,30,&H00FFFFFF,&H00FFFFFF,&H00288CF2,&H00288CF2,0,0,0,0,100,100,1,0,3,10,0,9,40,48,48,1
Style: Label,Poppins Bold,28,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,3,1,7,48,40,46,1
Style: Water,Poppins Bold,22,&H50FFFFFF,&H50FFFFFF,&H90000000,&H00000000,0,0,0,0,100,100,1,0,1,2,0,3,40,40,30,1
Style: Draw,Poppins Bold,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

ev = []


def E(a, b, style, text, layer=0):
    ev.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")


# ---------------------------------------------------------- subtítulos
def chunks(text):
    words = text.split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        n = len(" ".join(cur))
        if (n > 30 and len(cur) >= 3) or (re.search(r"[,.:;?!]$", w) and n > 16) or len(cur) >= 7:
            out.append(cur); cur = []
    if cur:
        if out and len(" ".join(cur)) < 10:
            out[-1] += cur
        else:
            out.append(cur)
    return out


for s in tl["sections"]:
    for f in s["frases"]:
        a, b = f["start"], f["end"]
        cs = chunks(f["text"])
        tot = sum(len(w) + 1.5 for c in cs for w in c)
        t = a
        for c in cs:
            w8 = sum(len(w) + 1.5 for w in c)
            d = (b - a) * w8 / tot
            ks = "".join(f"{{\\k{max(1, int(round(d * 100 * (len(w) + 1.5) / w8)))}}}{w} " for w in c)
            E(t, t + d + 0.05, "Sub", "{\\fad(70,50)\\fscx90\\fscy90\\t(0,110,\\fscx100\\fscy100)}" + ks.strip(), 5)
            t += d
        if f["tag"]:
            st = "BadgeC" if f["tag"] == "C" else "BadgeT"
            txt = "✔ CONFIRMADO POR ROCKSTAR" if f["tag"] == "C" else "⚠ TEORÍA / ESPECULACIÓN"
            txt = txt[2:]
            E(a, b + 0.2, st, "{\\fad(120,150)\\move(2200,48,1880,48,0,180)}" + txt, 6)

# ---------------------------------------------------------- tarjetas de detalle
secs = tl["sections"]
for i, s in enumerate(secs):
    if not s["titulo"]:
        continue
    n = int(s["id"][1:])
    a = s["start"] - 0.15
    b = a + 3.3
    E(a, b, "Kicker", "{\\pos(960,350)\\fad(80,250)\\fsp30\\t(0,400,\\fsp12)}DETALLE", 4)
    E(a, b, "Big", "{\\pos(960,500)\\fad(60,250)\\blur3\\fscx160\\fscy160\\t(0,180,\\fscx100\\fscy100)}#" + str(n), 4)
    E(a + 0.12, b, "Card", "{\\pos(960,665)\\fad(120,250)\\clip(0,600,0,740)\\t(0,350,\\clip(0,600,1920,740))}" + s["titulo"], 4)
    # barra decorativa
    E(a + 0.05, b, "Draw", "{\\pos(560,725)\\fad(100,250)\\1c&H00B43CFF&\\p1}m 0 0 l 800 0 800 8 0 8{\\p0}", 3)
    # rótulo persistente arriba a la izquierda + barra de progreso
    end = secs[i + 1]["start"] - 0.3 if i + 1 < len(secs) else s["end"]
    E(b - 0.3, end, "Label", "{\\fad(250,200)}{\\1c&H00B43CFF&}DETALLE " + f"{n}/20" + "{\\1c&H00FFFFFF&}  ·  " + s["titulo"], 2)
    E(s["start"], end + 0.3, "Draw", f"{{\\pos(0,0)\\1c&H00B43CFF&\\1a&H20&\\p1}}m 0 0 l {int(1920 * n / 20)} 0 {int(1920 * n / 20)} 7 0 7{{\\p0}}", 2)

# ---------------------------------------------------------- intro y final
intro = secs[0]
E(0.15, 2.3, "Card", "{\\pos(960,540)\\fad(300,250)\\fs46\\fsp8}RECREACIÓN VISUAL ORIGINAL", 4)
E(0.15, 2.3, "Label", "{\\an5\\pos(960,610)\\fad(300,250)\\fs30}Imágenes creadas para este vídeo · no es gameplay oficial", 4)
f3 = intro["frases"][2]
a, b = f3["start"] - 0.1, intro["frases"][3]["start"] + 1.0
E(a, b, "Kicker", "{\\pos(960,300)\\fad(150,300)\\fs70\\1c&H0040A0FF&}20 DETALLES DE", 4)
E(a, b, "Big", "{\\pos(960,450)\\fad(100,300)\\fscx140\\fscy140\\t(0,250,\\fscx100\\fscy100)\\blur2}GTA 6", 4)
E(a + 0.2, b, "Card", "{\\pos(960,610)\\fad(150,300)\\fs64}QUE SEGURAMENTE NO CONOCÍAS", 4)

out = secs[-1]
q = out["frases"][2]
E(q["start"] - 0.1, D, "Card", "{\\pos(960,250)\\fad(200,400)\\fs76}¿CUÁL TE HA SORPRENDIDO MÁS?", 4)
sub_t = out["frases"][3]["start"]
E(sub_t, D, "Draw", "{\\pos(760,440)\\fad(200,400)\\1c&H000000E6&\\p1}m 30 0 l 370 0 b 390 0 400 10 400 30 l 400 100 b 400 120 390 130 370 130 l 30 130 b 10 130 0 120 0 100 l 0 30 b 0 10 10 0 30 0{\\p0}", 4)
E(sub_t, D, "Card", "{\\pos(960,505)\\fad(200,400)\\fs62\\t(300,500,\\fscx112\\fscy112)\\t(500,700,\\fscx100\\fscy100)}SUSCRÍBETE", 5)
E(sub_t + 0.6, D, "Label", "{\\an5\\pos(960,620)\\fad(200,400)\\fs34}Déjame tu respuesta en los comentarios", 4)

# ---------------------------------------------------------- marca de agua permanente
E(0, D, "Water", "RECREACIÓN VISUAL ORIGINAL · NO ES GAMEPLAY OFICIAL", 1)

open(os.path.join(WORK, "subs.ass"), "w", encoding="utf-8").write(HEAD + "\n".join(ev) + "\n")
print(len(ev), "eventos ASS")
