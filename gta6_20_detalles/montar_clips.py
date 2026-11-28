# -*- coding: utf-8 -*-
"""Sustituye los planos recreados por fragmentos de TUS clips de gameplay.

Coloca tus grabaciones (mp4/mov/mkv) en subcarpetas de CLIPS_DIR según su contenido:
  ciudad, aereas, carreteras, playas, mar, naturaleza, lluvia, policia,
  jason_lucia, tiendas, interiores, clima, coches, cayos, accion
Cada plano del vídeo toma un fragmento distinto (2-4 s) de la categoría que
corresponde a lo que dice el narrador. Si una categoría está vacía, se usan las de
respaldo y, en último caso, el plano recreado original.
Salida: WORK/shots_mix/*.mp4 (1920x1080, 30 fps), WORK/concat_mix.txt y WORK/clips_audio.wav
"""
import json, os, random, subprocess, sys
import numpy as np

WORK = os.environ["WORK"]
CLIPS = os.environ.get("CLIPS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "clips"))
OUT = os.path.join(WORK, "shots_mix"); os.makedirs(OUT, exist_ok=True)
FPS, SR = 30, 48000

CAT = {
    "skyline": ["ciudad", "aereas"], "aerial": ["aereas", "ciudad"], "highway": ["carreteras", "coches"],
    "beach": ["playas", "mar"], "ocean": ["mar", "playas", "cayos"], "swamp": ["naturaleza"],
    "mountains": ["naturaleza"], "rainstreet": ["lluvia", "clima", "ciudad"], "storm": ["clima", "lluvia"],
    "police": ["policia", "accion"], "policeheli": ["policia", "aereas"], "duo": ["jason_lucia"],
    "shops": ["tiendas", "ciudad"], "club": ["interiores", "tiendas"], "car": ["coches", "carreteras"],
    "bridge": ["cayos", "carreteras", "mar"], "map": ["mapa"],
}
EXT = (".mp4", ".mov", ".mkv", ".webm", ".m4v")


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def has_audio(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


lib = {}
for cat in sorted(set(c for v in CAT.values() for c in v)) + ["accion"]:
    d = os.path.join(CLIPS, cat)
    if os.path.isdir(d):
        files = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(EXT)]
        lib[cat] = [(f, dur(f), has_audio(f)) for f in files if dur(f) > 2.5]
print({k: len(v) for k, v in lib.items() if v})

rng = random.Random(6)
used = {}   # clip -> lista de intervalos usados


def pick(cats, need):
    for c in cats:
        cand = lib.get(c) or []
        rng.shuffle(cand)
        for f, d, a in sorted(cand, key=lambda x: sum(b - a_ for a_, b in used.get(x[0], []))):
            if d < need + 0.5:
                continue
            for _ in range(25):
                s = rng.uniform(0.2, d - need - 0.2)
                if all(s + need < a_ or s > b for a_, b in used.get(f, [])):
                    used.setdefault(f, []).append((s, s + need))
                    return f, s, a
    return None


shots = json.load(open(os.path.join(WORK, "shots.json")))
total = shots[-1]["start"] + shots[-1]["dur"]
audio = np.zeros((int(total * SR) + SR, 2), np.float32)
lines, n_real = [], 0
for sh in shots:
    out = os.path.join(OUT, f"{sh['i']:04d}.mp4")
    n = sh["frames"]
    need = n / FPS
    p = pick(CAT[sh["scene"]], need)
    if p:
        f, s, a = p
        z = 1.06 if sh["z1"] >= sh["z0"] else 1.10
        # zoom/paneo suave sobre el clip real
        vf = (f"fps={FPS},scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
              f"scale={int(1920 * z) // 2 * 2}:{int(1080 * z) // 2 * 2},"
              f"crop=1920:1080:x='(iw-1920)*(0.5+0.5*sin(t/{need:.3f}*PI-PI/2))':y='(ih-1080)/2',setsar=1")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", f, "-frames:v", str(n), "-vf", vf, "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out]
        subprocess.run(cmd, check=True)
        if a:
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{need:.3f}", "-i", f, "-ac", "2",
                                "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
            x = np.frombuffer(r.stdout, np.float32).reshape(-1, 2)
            fd = min(len(x) // 2, int(0.08 * SR))
            if fd:
                x = x.copy(); x[:fd] *= np.linspace(0, 1, fd)[:, None]; x[-fd:] *= np.linspace(1, 0, fd)[:, None]
            i = int(sh["start"] * SR)
            audio[i:i + len(x)] += x[:len(audio) - i]
        n_real += 1
    else:
        src = os.path.join(WORK, "shots", f"{sh['i']:04d}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out], check=True)
    lines.append(f"file '{out}'\n")
    print(f"plano {sh['i']:3d} {sh['scene']:10s} -> {'CLIP ' + os.path.basename(p[0]) if p else 'recreación'}", flush=True)

open(os.path.join(WORK, "concat_mix.txt"), "w").writelines(lines)
import wave
pk = np.max(np.abs(audio)) + 1e-9
pcm = (audio / pk * 0.9 * 32767).astype(np.int16)
with wave.open(os.path.join(WORK, "clips_audio.wav"), "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(f"{n_real}/{len(shots)} planos con gameplay real")
