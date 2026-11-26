"""Motores de voz intercambiables.

Formatos de `voz` en el guion (o con --voz en la línea de comandos):
  piper:es_ES-davefx-medium      (local, gratis, sin internet tras descargar el modelo)
  kokoro:em_alex                 (local, gratis; voces es: em_alex, em_santa, ef_dora)
  edge:es-ES-AlvaroNeural        (gratis, necesita internet; muy natural)
  elevenlabs:<voice_id>          (de pago, la mejor calidad; requiere ELEVENLABS_API_KEY)
"""
import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOICES = ROOT / "voices"

PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
KOKORO_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"


def _download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    print(f"  descargando {dest.name} ...")
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dest)


def _piper_model(name):
    lang_region, speaker, quality = name.split("-")
    lang = lang_region.split("_")[0]
    base = f"{PIPER_BASE}/{lang}/{lang_region}/{speaker}/{quality}/{name}"
    onnx = VOICES / f"{name}.onnx"
    _download(base + ".onnx", onnx)
    _download(base + ".onnx.json", VOICES / f"{name}.onnx.json")
    return onnx


_kokoro = None


def synth(text, out_wav, voice="piper:es_ES-davefx-medium", speed=1.0):
    """Genera `out_wav` con el texto dado. Devuelve la ruta."""
    engine, _, name = voice.partition(":")
    out_wav = Path(out_wav)
    raw = out_wav.with_suffix(".raw.wav")
    if engine == "piper":
        model = _piper_model(name)
        subprocess.run(
            ["python3", "-m", "piper", "-m", str(model), "-f", str(raw),
             "--length-scale", f"{1.0 / speed:.3f}", "--noise-scale", "0.6", "--noise-w-scale", "0.75"],
            input=text.encode(), check=True, capture_output=True)
    elif engine == "kokoro":
        global _kokoro
        import soundfile as sf
        from kokoro_onnx import Kokoro
        if _kokoro is None:
            _download(f"{KOKORO_BASE}/kokoro-v1.0.onnx", VOICES / "kokoro.onnx")
            _download(f"{KOKORO_BASE}/voices-v1.0.bin", VOICES / "voices.bin")
            _kokoro = Kokoro(str(VOICES / "kokoro.onnx"), str(VOICES / "voices.bin"))
        samples, sr = _kokoro.create(text, voice=name, speed=speed, lang="es")
        sf.write(raw, samples, sr)
    elif engine == "edge":
        pct = int(round((speed - 1) * 100))
        mp3 = out_wav.with_suffix(".mp3")
        cmd = ["edge-tts", "--voice", name, f"--rate={pct:+d}%", "--text", text, "--write-media", str(mp3)]
        if os.environ.get("HTTPS_PROXY"):
            cmd += ["--proxy", os.environ["HTTPS_PROXY"]]
        subprocess.run(cmd, check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), str(raw)], check=True)
    elif engine == "elevenlabs":
        key = os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            raise SystemExit("Falta ELEVENLABS_API_KEY")
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{name}?output_format=mp3_44100_128",
            data=json.dumps({
                "text": text, "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.35, "similarity_boost": 0.8, "style": 0.45, "speed": speed},
            }).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json"})
        mp3 = out_wav.with_suffix(".mp3")
        mp3.write_bytes(urllib.request.urlopen(req).read())
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), str(raw)], check=True)
    else:
        raise SystemExit(f"Motor de voz desconocido: {engine}")

    # limpieza: 48 kHz mono, recorta silencios, EQ de presencia y compresión suave
    filt = ",".join([
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02",
        "areverse",
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05",
        "areverse",
        "highpass=f=75",
        "equalizer=f=220:t=q:w=1.2:g=1.5",
        "equalizer=f=3200:t=q:w=1.5:g=2.5",
        "equalizer=f=9000:t=h:w=2000:g=1.5",
        "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2",
    ])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", filt, "-ar", "48000", "-ac", "1", str(out_wav)], check=True)
    raw.unlink(missing_ok=True)
    return out_wav
