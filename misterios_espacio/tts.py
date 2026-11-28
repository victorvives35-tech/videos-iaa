# -*- coding: utf-8 -*-
"""Genera la narración frase a frase con Piper y construye la línea de tiempo."""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from guion import SECCIONES, PRONUNCIACION

WORK = os.environ["WORK"]
MODEL = os.path.join(WORK, "voice", "es_ES-davefx-medium.onnx")
OUT = os.path.join(WORK, "tts"); os.makedirs(OUT, exist_ok=True)
ENGINE = os.environ.get("TTS_ENGINE", "kokoro")
SR = 24000 if ENGINE == "kokoro" else 22050
_k = None


def synth(text, path):
    global _k
    if ENGINE == "kokoro":
        import soundfile as sf
        from kokoro_onnx import Kokoro
        if _k is None:
            kd = os.path.join(WORK, "kokoro")
            _k = Kokoro(os.path.join(kd, "kokoro-v1.0.onnx"), os.path.join(kd, "voices-v1.0.bin"))
        a, sr = _k.create(text, voice=os.environ.get("TTS_VOICE", "em_alex"), speed=float(os.environ.get("TTS_SPEED", "0.9")), lang="es")
        sf.write(path + ".raw.wav", a, sr, subtype="PCM_16")
        # voz más grave (-6 %) manteniendo el tempo
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path + ".raw.wav", "-af",
                        f"asetrate={sr}*0.94,aresample={sr},atempo=1.0638", path], check=True)
        os.remove(path + ".raw.wav")
    else:
        subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", path,
                        "--length-scale", "1.2", "--sentence-silence", "0.0"],
                       input=text.encode(), check=True, capture_output=True)
GAP = 0.75
SECTION_GAP = 2.4
INTRO_LEAD = 3.5

def voz(t):
    for a, b in PRONUNCIACION:
        t = t.replace(a, b)
    return t

def read_wav(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

timeline, chunks, t = [], [np.zeros(int(INTRO_LEAD * SR), np.float32)], INTRO_LEAD
for si, sec in enumerate(SECCIONES):
    sec_start = t
    frases = []
    for fi, (tag, txt) in enumerate(sec["frases"]):
        p = os.path.join(OUT, f"{sec['id']}_{fi:02d}.wav")
        if not os.path.exists(p):
            synth(voz(txt), p)
        a = read_wav(p)
        # recorta silencios de los extremos
        nz = np.where(np.abs(a) > 0.01)[0]
        a = a[max(0, nz[0] - 300): nz[-1] + 1500] if len(nz) else a
        d = len(a) / SR
        frases.append({"tag": tag, "text": txt, "start": round(t, 3), "end": round(t + d, 3)})
        chunks.append(a); t += d
        g = GAP if fi < len(sec["frases"]) - 1 else SECTION_GAP
        chunks.append(np.zeros(int(g * SR), np.float32)); t += g
    timeline.append({"id": sec["id"], "titulo": sec["titulo"], "temas": sec["temas"], "cgi": sec["cgi"],
                     "start": round(sec_start, 3), "end": round(t, 3), "frases": frases})

chunks.append(np.zeros(int(3.0 * SR), np.float32)); t += 3.0
audio = np.concatenate(chunks)
pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
with wave.open(os.path.join(WORK, "narracion.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
json.dump({"duration": round(t, 3), "sections": timeline},
          open(os.path.join(WORK, "timeline.json"), "w"), ensure_ascii=False, indent=1)
print("duración total: %.1f s (%.2f min)" % (t, t / 60))
