"""Mezcla de audio, montaje final, subtítulos SRT, capítulos de YouTube y miniatura."""
import json, sys, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(sys.argv[1]); DEST = Path(sys.argv[2]); DEST.mkdir(parents=True, exist_ok=True)
TL = json.load(open(OUT / "timeline.json"))
SR = 48000; N = int(TL["total"] * SR)

def run(*a): subprocess.run(a, check=True)

# ---------------- pista de voz ----------------
voice = np.zeros(N, np.float32)
for it in TL["items"]:
    if it["kind"] != "line": continue
    sr, v = wavfile.read(it["voice"]); v = v.astype(np.float32) / 32768
    i0 = int(it["voice_start"] * SR); e = min(N, i0 + len(v)); voice[i0:e] += v[:e - i0]
wavfile.write(OUT / "voz.wav", SR, (np.clip(voice, -1, 1) * 32767).astype(np.int16))

def audio_mix(dst):
    run("ffmpeg", "-y", "-v", "error", "-i", str(OUT / "voz.wav"), "-i", str(OUT / "musica.wav"), "-filter_complex",
        "[0:a]loudnorm=I=-16:TP=-2:LRA=9,aformat=channel_layouts=stereo,asplit=2[v][vsc];"
        "[1:a]volume=-11dB[m];"
        "[m][vsc]sidechaincompress=threshold=0.03:ratio=4:attack=40:release=600:makeup=1[md];"
        "[v][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]",
        "-map", "[out]", "-ar", "48000", "-c:a", "pcm_s16le", str(dst))
if not (OUT / "mezcla.wav").exists(): audio_mix(OUT / "mezcla.wav")

# ---------------- vídeo final ----------------
if "--audio-only" not in sys.argv:
    run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(OUT / "parts.txt"),
        "-i", str(OUT / "mezcla.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart",
        str(DEST / "NADIE_VA_A_VENIR_A_SALVARTE.mp4"))

# ---------------- subtítulos ----------------
def ts(s, sep=","):
    h, m = int(s // 3600), int(s % 3600 // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{int(sec):02d}{sep}{int((sec % 1) * 1000):03d}"
with open(DEST / "subtitulos_es.srt", "w") as f:
    n = 0
    for it in TL["items"]:
        if it["kind"] != "line": continue
        n += 1
        f.write(f"{n}\n{ts(it['voice_start'])} --> {ts(it['voice_start'] + it['voice_dur'] + 0.2)}\n{it['text']}\n\n")

# ---------------- capítulos + descripción ----------------
def yt(s): s = int(s); return f"{s // 60}:{s % 60:02d}"
chaps = [("0:00", "Nadie va a venir a salvarte")]
for it in TL["items"]:
    if it["kind"] == "chapter":
        chaps.append((yt(it["start"]), (("Capítulo " + it['num'].split()[-1]) if it['num'].startswith("CAP") else it['num'].capitalize()) + " – " + it['title'].capitalize()))
desc = f"""Nadie va a venir a salvarte. Ni tus padres, ni tus amigos, ni el momento perfecto.
Y el día que lo aceptas, empieza tu verdadera vida.

Este vídeo es para el que está cansado de ser quien es. Para el que sabe que nació para algo más.
Escúchalo hasta el final. Y luego levántate.

⏱️ CAPÍTULOS
{chr(10).join(f'{t} {c}' for t, c in chaps)}

🔥 Si este mensaje te ha llegado, suscríbete y compártelo con alguien que necesite escucharlo hoy.

#motivacion #disciplina #mentalidad #superacionpersonal #estoicismo #desarrollopersonal #renacer
"""
meta = f"""TÍTULO (opciones):
1. NADIE VA A VENIR A SALVARTE | El vídeo que cambiará tu forma de pensar
2. Nadie Va a Venir a Salvarte – Motivación Brutal en Español
3. Escucha Esto Cuando Sientas Que Vas Tarde en la Vida

DESCRIPCIÓN:
{desc}
ETIQUETAS:
motivación, motivacion en español, disciplina, mentalidad, nadie va a venir a salvarte, superación personal, estoicismo, marco aurelio, desarrollo personal, autodisciplina, renacer, cambia tu vida, video motivacional, discurso motivacional

DURACIÓN: {yt(TL['total'])}
"""
(DEST / "youtube_metadatos.txt").write_text(meta)

# ---------------- miniatura 1280x720 ----------------
Wt, Ht = 1280, 720
y, x = np.mgrid[0:Ht, 0:Wt].astype(np.float32)
img = np.zeros((Ht, Wt, 3), np.float32)
d = np.sqrt(((x - 900) / 560) ** 2 + ((y - 600) / 330) ** 2)
img += np.exp(-d ** 2)[..., None] * np.array([150, 55, 15]) / 255
d2 = np.sqrt(((x - 900) / 200) ** 2 + ((y - 600) / 60) ** 2)
img += np.exp(-d2 ** 2)[..., None] * np.array([255, 170, 80]) / 255
img += np.array([8, 8, 12]) / 255
rng = np.random.default_rng(3)
for _ in range(220):
    px, py = rng.uniform(450, 1280), rng.uniform(200, 720); r = rng.uniform(1, 3.5)
    m = np.exp(-(((x - px) ** 2 + (y - py) ** 2) / (r * r)))
    img += m[..., None] * np.array([1, 0.55, 0.2]) * rng.uniform(0.3, 1)
vig = np.clip(1 - 0.8 * (((x - 640) / 900) ** 2 + ((y - 360) / 520) ** 2), 0.15, 1)
img = np.clip(img * vig[..., None], 0, 1)
im = Image.fromarray((img * 255).astype(np.uint8))
# horizonte: suelo oscuro bajo la línea del amanecer
hz = 600
arr = np.asarray(im).copy(); arr[hz:] = (arr[hz:] * 0.12).astype(np.uint8)
im = Image.fromarray(arr)
F = ImageFont.truetype("/opt/fonts/Anton.ttf", 150)
txt = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0)); td = ImageDraw.Draw(txt)
lines = [("NADIE VA A", (245, 240, 230)), ("SALVARTE", (240, 182, 70))]
yy = 120
for t_, c in lines:
    td.text((60, yy), t_, font=F, fill=c + (255,)); yy += 190
shadow = txt.split()[3].filter(ImageFilter.GaussianBlur(14))
im.paste((0, 0, 0), (0, 0), shadow.point(lambda v: int(v * 0.9)))
im.paste(txt, (0, 0), txt)
im.save(DEST / "miniatura.jpg", quality=95)
print("listo:", DEST)
