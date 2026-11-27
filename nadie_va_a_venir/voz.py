"""Genera la narración (Piper TTS local), la procesa y construye timeline.json."""
import json, subprocess, sys, wave, os
from pathlib import Path
from guion import GUION

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
VOICE = "/opt/piper/es_ES-davefx-medium.onnx"
(OUT / "voz").mkdir(parents=True, exist_ok=True)

from piper import PiperVoice
from piper.config import SynthesisConfig
voice = PiperVoice.load(VOICE)
cfg = SynthesisConfig(length_scale=1.18, noise_scale=0.6, noise_w_scale=0.7)

def dur(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(p)])
    return float(out)

# Cadena de voz: tono un poco más grave, cuerpo en graves, compresión y sala sutil
VOICE_FX = ("asetrate=22050*0.94,aresample=48000,atempo=1/0.94,"
            "highpass=f=70,equalizer=f=140:t=q:w=1:g=4,equalizer=f=3200:t=q:w=1.5:g=2,"
            "acompressor=threshold=-20dB:ratio=3.5:attack=8:release=120:makeup=4,"
            "aecho=0.8:0.55:60|110:0.18|0.10")

timeline, t = [], 1.2   # arranca tras 1.2 s de silencio
for i, item in enumerate(GUION):
    if item[0] == "PAUSE":
        t += item[1]; continue
    if item[0] == "CH":
        timeline.append(dict(kind="chapter", start=t, end=t + 4.2, num=item[1], title=item[2]))
        t += 4.2; continue
    text, onscreen, bg = item
    if not text:                              # tarjeta de título sin voz
        timeline.append(dict(kind="title", start=t, end=t + 5.0, onscreen=onscreen, bg=bg))
        t += 5.0; continue
    raw, fx = OUT / "voz" / f"{i:03d}_raw.wav", OUT / "voz" / f"{i:03d}.wav"
    if not fx.exists():
        with wave.open(str(raw), "wb") as wf:
            voice.synthesize_wav(text, wf, syn_config=cfg)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", VOICE_FX,
                        "-ar", "48000", "-ac", "1", str(fx)], check=True)
    d = dur(fx)
    gap = 0.55 + min(0.6, 0.04 * len(text.split()))   # respiración proporcional a la frase
    timeline.append(dict(kind="line", start=t, end=t + d + gap, voice_start=t, voice=str(fx),
                         voice_dur=d, text=text, onscreen=onscreen, bg=bg))
    t += d + gap

total = t + 1.0
json.dump(dict(total=total, items=timeline), open(OUT / "timeline.json", "w"), ensure_ascii=False, indent=1)
print(f"duración total: {total/60:.1f} min, {len(timeline)} bloques")
