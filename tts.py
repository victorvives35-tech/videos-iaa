"""Motores de voz intercambiables.

Formatos de `voz` en el guion (o con --voz en la línea de comandos):
  piper:es_ES-davefx-medium      (local, gratis, sin internet tras descargar el modelo)
  kokoro:em_alex                 (local, gratis; voces es: em_alex, em_santa, ef_dora)
  chatterbox:                    (local, gratis, muy expresiva; admite exageración emocional)
  edge:es-ES-AlvaroNeural        (gratis, necesita internet; muy natural)
  elevenlabs:<voice_id>          (la mejor calidad; admite etiquetas [gritando], [emocionado], [ríe]...)
"""
import json
import os
import subprocess
import urllib.error
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
_cb = None
_wh = None


def _check(wav, text):
    """Parecido (0..1) entre lo que se oye en `wav` (whisper) y el texto esperado."""
    global _wh
    import difflib
    import re
    import numpy as np
    from faster_whisper import WhisperModel
    if _wh is None:
        _wh = WhisperModel("small", device="cpu", compute_type="int8")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    segs, _ = _wh.transcribe(np.frombuffer(raw, np.float32).copy(), language="es", beam_size=1)
    heard = " ".join(s.text for s in segs)
    n = lambda x: re.sub(r"[^a-zñáéíóúü0-9 ]", "", x.lower()).split()
    return difflib.SequenceMatcher(None, n(heard), n(text)).ratio()


def synth(text, out_wav, voice="piper:es_ES-davefx-medium", speed=1.0, opts=None):
    opts = opts or {}
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
    elif engine == "chatterbox":
        global _cb
        import torch
        import torchaudio as ta
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        if _cb is None:
            _cb = ChatterboxMultilingualTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
        ref = name if name and Path(name).exists() else str(ROOT / "assets" / "voz_ref_hombre.wav")
        ex = opts.get("exaggeration", 0.8)
        best = None
        for attempt in range(opts.get("tries", 3)):
            torch.manual_seed(opts.get("seed", 7) + attempt * 101)
            w = _cb.generate(text, language_id="es", audio_prompt_path=ref, exaggeration=ex,
                             cfg_weight=opts.get("cfg_weight", 0.35), temperature=0.8)
            cand = out_wav.with_suffix(f".try{attempt}.wav")
            ta.save(str(cand), w, _cb.sr)
            score = _check(cand, text)
            if best is None or score > best[0]:
                best = (score, cand)
            if score > 0.9:
                break
        best[1].rename(raw)
        for c in out_wav.parent.glob(out_wav.stem + ".try*.wav"):
            c.unlink()
        if abs(speed - 1) > 0.01:
            tmp = raw.with_suffix(".sp.wav")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", f"atempo={speed:.3f}", str(tmp)], check=True)
            tmp.rename(raw)
    elif engine == "elevenlabs":
        # La clave puede venir de ELEVENLABS_API_KEY o inyectarla un proxy.
        key = os.environ.get("ELEVENLABS_API_KEY", "proxy-injected")
        model = opts.get("model", "eleven_v3")
        settings = {"stability": opts.get("stability", 0.5 if model == "eleven_v3" else 0.3),
                    "similarity_boost": 0.8, "style": opts.get("style", 0.6), "use_speaker_boost": True}
        if model != "eleven_v3":
            settings["speed"] = speed
        body = {"text": text, "model_id": model, "voice_settings": settings, "language_code": "es"}
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{name}?output_format=mp3_44100_192",
            data=json.dumps(body).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json"})
        mp3 = out_wav.with_suffix(".mp3")
        try:
            mp3.write_bytes(urllib.request.urlopen(req, timeout=120).read())
        except urllib.error.HTTPError as e:
            raise SystemExit(f"ElevenLabs {e.code}: {e.read().decode()[:400]}")
        atempo = f",atempo={speed:.3f}" if model == "eleven_v3" and abs(speed - 1) > 0.01 else ""
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-af", "anull" + atempo, str(raw)], check=True)
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
        "deesser=i=0.4",
        "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=70:makeup=3",
    ])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", filt, "-ar", "48000", "-ac", "1", str(out_wav)], check=True)
    raw.unlink(missing_ok=True)
    return out_wav
