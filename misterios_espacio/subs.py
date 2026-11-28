# -*- coding: utf-8 -*-
"""Subtítulos sincronizados, rótulos de cada misterio, etiquetas HECHO/HIPÓTESIS y créditos de imagen (ASS)."""
import json, os, re

WORK = os.environ["WORK"]
tl = json.load(open(os.path.join(WORK, "timeline.json")))
plan = json.load(open(os.path.join(WORK, "plan.json")))
D = tl["duration"]


def ts(t):
    t = max(0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Poppins,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,1,0,0,0,100,100,0.5,0,1,3,2,2,200,200,70,1
Style: Num,Poppins,40,&H00F0C85A,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,18,0,1,0,0,5,0,0,0,1
Style: Title,Anton,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,6,0,1,0,6,5,0,0,0,1
Style: Badge,Poppins,26,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,6,0,1,0,0,7,60,40,50,1
Style: Credit,Poppins,22,&H90FFFFFF,&H90FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,1,0,3,40,50,30,1
Style: Draw,Poppins,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
E = lambda a, b, st, tx, l=0: ev.append(f"Dialogue: {l},{ts(a)},{ts(b)},{st},,0,0,0,,{tx}")


def chunks(text):
    w = text.split(); out, cur = [], []
    for x in w:
        cur.append(x); n = len(" ".join(cur))
        if (n > 46 and len(cur) > 3) or (re.search(r"[.:;?!]$", x) and n > 20) or (x.endswith(",") and n > 34):
            out.append(cur); cur = []
    if cur:
        if out and len(" ".join(cur)) < 12: out[-1] += cur
        else: out.append(cur)
    return out


for s in tl["sections"]:
    for f in s["frases"]:
        a, b = f["start"], f["end"]
        cs = chunks(f["text"]); tot = sum(len(" ".join(c)) + 4 for c in cs); t = a
        for c in cs:
            d = (b - a) * (len(" ".join(c)) + 4) / tot
            E(t, t + d - 0.02, "Sub", "{\\fad(120,80)}" + " ".join(c), 5); t += d
        if f["tag"]:
            col, txt = ("&H00E8C84A&", "DATO CONTRASTADO") if f["tag"] == "H" else ("&H0040A8FF&", "HIPÓTESIS CIENTÍFICA")
            E(a, b + 0.3, "Badge", "{\\fad(250,250)\\pos(60,50)\\1c" + col + "\\p1}m 0 6 l 14 6 14 20 0 20{\\p0}", 6)
            E(a, b + 0.3, "Badge", "{\\fad(250,250)\\pos(88,46)}" + txt, 6)

# rótulos de cada misterio
for i, s in enumerate(tl["sections"]):
    if not s["titulo"]: continue
    n = int(s["id"][1:]); a = s["start"] - 0.2; b = a + 4.2
    E(a, b, "Num", "{\\pos(960,400)\\fad(400,500)\\fsp40\\t(0,900,\\fsp18)}MISTERIO Nº " + str(n), 4)
    E(a + 0.15, b, "Title", "{\\pos(960,520)\\fad(500,500)\\blur1\\fscx108\\fscy108\\t(0,3800,\\fscx100\\fscy100)}" + s["titulo"], 4)
    E(a + 0.3, b, "Draw", "{\\pos(760,610)\\fad(400,500)\\1c&H00F0C85A&\\p1}m 0 0 l 400 0 400 3 0 3{\\p0}", 4)

# portada del vídeo durante la intro
intro = tl["sections"][0]
f4 = intro["frases"][4]
E(f4["start"] - 0.2, f4["end"] + 0.6, "Num", "{\\pos(960,330)\\fad(500,600)}10 MISTERIOS DEL ESPACIO", 4)
E(f4["start"], f4["end"] + 0.6, "Title", "{\\pos(960,450)\\fad(600,600)\\fs96}QUE LA NASA TODAVÍA", 4)
E(f4["start"] + 0.2, f4["end"] + 0.6, "Title", "{\\pos(960,570)\\fad(600,600)\\fs96\\1c&H00F0C85A&}NO HA PODIDO RESOLVER", 4)

# pregunta final
out = tl["sections"][-1]; q = out["frases"][-1]
E(q["start"], D, "Title", "{\\pos(960,380)\\fad(600,800)\\fs84}¿CUÁL SE RESOLVERÁ PRIMERO?", 4)
E(q["start"] + 1, D, "Num", "{\\pos(960,490)\\fad(600,800)}DÉJALO EN LOS COMENTARIOS", 4)

# créditos de cada plano
for sec in plan:
    for sh in sec["shots"]:
        E(sh["start"] + 0.3, sh["start"] + sh["dur"] - 0.2, "Credit", "{\\fad(300,300)}" + sh["credit"], 1)

open(os.path.join(WORK, "subs.ass"), "w", encoding="utf-8").write(HEAD + "\n".join(ev) + "\n")
print(len(ev), "eventos")
