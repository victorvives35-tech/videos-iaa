# -*- coding: utf-8 -*-
"""Miniatura 1280x720: agujero negro gigante + galaxia misteriosa + texto grande."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cgi import BlackHole, Galaxy

WORK = os.environ["WORK"]
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "miniatura_10_misterios.png"))
bh = np.asarray(BlackHole(np.random.default_rng(7), 6.0, 0).frame(5.5), np.float32)
gal = np.asarray(Galaxy(np.random.default_rng(11), 6.0).frame(2.0), np.float32)
# agujero negro grande desplazado a la derecha
bhi = Image.fromarray(np.clip(bh * 1.3, 0, 255).astype(np.uint8)).resize((1760, 990), Image.LANCZOS)
img = Image.new("RGB", (1280, 720))
img.paste(bhi, (900 - 880, 380 - 495))
# galaxia misteriosa arriba a la derecha (fusión aditiva)
g = Image.fromarray(gal.astype(np.uint8)).resize((760, 428), Image.LANCZOS)
arr = np.asarray(img, np.float32)
gi = np.asarray(g, np.float32)
y0, x0 = -40, 640
ys, xs = max(0, y0), x0
gy0 = ys - y0
yy, xx = np.mgrid[0:428, 0:760]
mask = np.clip(1.4 - np.sqrt(((xx - 380) / 380) ** 2 + ((yy - 214) / 214) ** 2) * 1.4, 0, 1)[..., None]
gi = np.clip(gi - 45, 0, 255) * mask
arr[ys:ys + 428 - gy0, xs:xs + 640] = np.clip(arr[ys:ys + 428 - gy0, xs:xs + 640] + gi[gy0:, :640] * 1.1, 0, 255)
img = Image.fromarray(arr.astype(np.uint8))
img = ImageEnhance.Contrast(img).enhance(1.15)
img = ImageEnhance.Color(img).enhance(1.25)
# viñeta y degradado izquierdo para legibilidad
ov = Image.new("RGBA", (1280, 720))
a = np.zeros((720, 1280), np.float32)
a += np.clip(1 - np.linspace(0, 1, 1280)[None, :] * 1.6, 0, 1) * 200
ov.putalpha(Image.fromarray(a.astype(np.uint8)))
img = Image.alpha_composite(img.convert("RGBA"), ov)
d = ImageDraw.Draw(img)
F = lambda s: ImageFont.truetype(os.path.join(WORK, "fonts", "Anton-Regular.ttf"), s)
P = lambda s: ImageFont.truetype(os.path.join(WORK, "fonts", "Poppins-ExtraBold.ttf"), s)
glow = Image.new("RGBA", (1280, 720)); gd = ImageDraw.Draw(glow)
lines = [("10 MISTERIOS", 150, (255, 255, 255)), ("SIN RESOLVER", 122, (255, 196, 64))]
y = 150
for txt, s, c in lines:
    gd.text((50, y), txt, font=F(s), fill=c + (255,))
    y += s + 20
glow = glow.filter(ImageFilter.GaussianBlur(14))
img = Image.alpha_composite(img, glow)
d = ImageDraw.Draw(img)
y = 150
for txt, s, c in lines:
    d.text((50, y), txt, font=F(s), fill=c, stroke_width=6, stroke_fill=(0, 0, 0))
    y += s + 20
d.rounded_rectangle([50, 520, 560, 585], 12, fill=(220, 30, 40))
d.text((70, 528), "LA CIENCIA AÚN NO LO SABE", font=P(34), fill=(255, 255, 255))
img.convert("RGB").save(OUT)
print("OK", OUT)
