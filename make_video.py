#!/usr/bin/env python3
"""Genera un vídeo vertical (1080x1920, 30 fps) a partir de un guion JSON.

  python3 make_video.py guiones/dentista.json
  python3 make_video.py guiones/dentista.json --voz kokoro:em_alex
  python3 make_video.py guiones/dentista.json --preview     # solo una hoja de fotogramas
"""
import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf

import tts

ROOT = Path(__file__).resolve().parent
SR = 48000
FPS = 30


# ---------------------------------------------------------------- texto
def parse_words(text):
    """Separa palabras y marca las que van entre *asteriscos* (énfasis)."""
    out, em = [], False
    for tok in text.split():
        start_em = tok.startswith("*")
        if start_em:
            em = True
            tok = tok[1:]
        end_em = tok.rstrip(".,!?;:…»\"").endswith("*")
        tok = tok.replace("*", "")
        if tok:
            out.append({"w": tok, "em": em})
        if end_em:
            em = False
    return out


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ]", "", w)


# ---------------------------------------------------------------- tiempos
_whisper = None


def word_times(wav, words):
    """Tiempo (inicio, fin) de cada palabra del guion usando faster-whisper + alineado."""
    global _whisper
    audio, _ = sf.read(wav, dtype="float32")
    dur = len(audio) / SR
    try:
        from faster_whisper import WhisperModel
        if _whisper is None:
            _whisper = WhisperModel("small", device="cpu", compute_type="int8")
        a16 = np.interp(np.arange(0, len(audio), SR / 16000), np.arange(len(audio)), audio).astype(np.float32)
        segs, _ = _whisper.transcribe(a16, language="es", word_timestamps=True, beam_size=1)
        hw = [(w.word, w.start, w.end) for s in segs for w in s.words]
    except Exception as e:  # sin whisper: reparto proporcional
        print("  (aviso) sin alineado whisper:", e)
        hw = []
    times = [None] * len(words)
    if hw:
        a = [norm(w["w"]) for w in words]
        b = [norm(w[0]) for w in hw]
        for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = (hw[blk.b + k][1], hw[blk.b + k][2])
    # interpolar huecos por longitud de palabra
    anchors = [(-1, 0.0)] + [(i, t[0]) for i, t in enumerate(times) if t] + [(len(words), dur)]
    for (i0, t0), (i1, t1) in zip(anchors, anchors[1:]):
        gap = list(range(i0 + 1, i1))
        if not gap:
            continue
        start = times[i0][1] if i0 >= 0 and times[i0] else t0
        weights = [len(words[g]["w"]) + 2 for g in gap]
        span = max(0.05, t1 - start)
        acc = start
        for g, wt in zip(gap, weights):
            d = span * wt / sum(weights)
            times[g] = (acc, acc + d)
            acc += d
    return [(max(0.0, s), min(dur, max(e, s + 0.08))) for s, e in times]


def chunk_words(words, max_words=3, max_chars=15):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(x["w"] for x in cur)
        if len(cur) >= max_words or len(text) >= max_chars or re.search(r"[.,!?;:…]$", w["w"]):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return [{"s": c[0]["s"], "words": c} for c in chunks]


# ---------------------------------------------------------------- audio
def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def sfx(kind):
    if kind == "pop":
        n = int(0.09 * SR); t = np.arange(n) / SR
        f = 950 * np.exp(-t * 18) + 280
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.03)
    if kind == "whoosh":
        n = int(0.38 * SR); t = np.arange(n) / SR
        rng = np.random.default_rng(3)
        x = rng.standard_normal(n)
        y = np.zeros(n); acc = 0.0
        cut = 0.02 + 0.25 * np.sin(np.pi * t / t[-1])
        for i in range(n):
            acc += cut[i] * (x[i] - acc); y[i] = acc
        return 0.35 * y * np.sin(np.pi * t / t[-1]) ** 2
    if kind == "ding":
        n = int(0.9 * SR); t = np.arange(n) / SR
        return 0.22 * (np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 1975.5 * t) + 0.25 * np.sin(2 * np.pi * 2637 * t)) * env(n, 0.002, 0.25)
    if kind == "buzz":
        n = int(0.32 * SR); t = np.arange(n) / SR
        sq = np.sign(np.sin(2 * np.pi * 98 * t)) * 0.5 + np.sin(2 * np.pi * 196 * t) * 0.5
        return 0.16 * sq * env(n, 0.005, 0.12)
    if kind == "tick":
        n = int(0.06 * SR); t = np.arange(n) / SR
        return 0.3 * np.sin(2 * np.pi * 1800 * t) * env(n, 0.0005, 0.012)
    if kind == "boing":
        n = int(0.45 * SR); t = np.arange(n) / SR
        f = 180 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
        return 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.18)
    raise ValueError(kind)


def music(duration, bpm=112, gain=0.075):
    """Base musical alegre (marimba sintética, I-vi-IV-V)."""
    n = int(duration * SR) + SR
    out = np.zeros(n)
    beat = 60 / bpm
    chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
    pat = [0, 2, 1, 2, 0, 2, 1, 3]

    def note(midi, length, amp):
        f = 440 * 2 ** ((midi - 69) / 12)
        m = int(length * SR); t = np.arange(m) / SR
        return amp * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 30)) * env(m, 0.002, 0.22)

    t, bar = 0.0, 0
    while t < duration + 1:
        ch = chords[bar % 4]
        for k in range(8):
            idx = pat[k]
            midi = ch[idx % 3] + 12 * (1 if idx == 3 else 0) + 12
            s = int((t + k * beat / 2) * SR)
            x = note(midi, 0.6, 0.5 if k % 2 == 0 else 0.35)
            if s < n:
                e = min(n, s + len(x)); out[s:e] += x[: e - s]
        for k in (0, 2):  # bajo
            s = int((t + k * beat) * SR)
            x = note(ch[0] - 12, 0.9, 0.7)
            if s < n:
                e = min(n, s + len(x)); out[s:e] += x[: e - s]
        t += 4 * beat; bar += 1
    return gain * out[: int(duration * SR)] / np.max(np.abs(out))


def add(track, x, t, gain=1.0):
    s = int(t * SR)
    if s >= len(track):
        return
    e = min(len(track), s + len(x))
    track[s:e] += gain * x[: e - s]


# ---------------------------------------------------------------- principal
def build(script_path, voice_override=None, preview=False, workers=3, keep=False):
    script = json.loads(Path(script_path).read_text())
    name = Path(script_path).stem
    work = ROOT / "salida" / f".tmp_{name}"
    work.mkdir(parents=True, exist_ok=True)
    vcfg = script.get("voice", {})
    voice = voice_override or vcfg.get("id", "piper:es_ES-davefx-medium")
    if voice_override and not voice_override.startswith("elevenlabs"):
        vcfg = {k: v for k, v in vcfg.items() if k == "speed"}
    speed = vcfg.get("speed", 1.1)

    beats = script["beats"]
    print(f"▶ {name}: {len(beats)} frases · voz {voice}")

    # 1) voz por frase (con caché)
    timeline_beats, cursor = [], 0.15
    voice_track = []
    state = {"mood": {}, "cam": "wide", "meter": None}
    for i, b in enumerate(beats):
        words = parse_words(b["text"])
        say = b.get("say") or " ".join(w["w"] for w in words)
        if b.get("tag"):
            say = f"[{b['tag']}] {say}"
        if not voice.startswith("elevenlabs"):
            say = re.sub(r"\[[^\]]*\]\s*", "", say)
        key = hashlib.md5(f"{voice}|{speed}|{say}|{json.dumps(vcfg, sort_keys=True)}".encode()).hexdigest()[:12]
        wav = work / f"v_{key}.wav"
        if not wav.exists():
            tts.synth(say, wav, voice=voice, speed=b.get("speed", speed), opts=vcfg)
        audio, _ = sf.read(wav, dtype="float32")
        dur = len(audio) / SR
        times_cache = wav.with_suffix(".times.json")
        if times_cache.exists() and json.loads(times_cache.read_text())["n"] == len(words):
            times = json.loads(times_cache.read_text())["t"]
        else:
            times = word_times(wav, words)
            times_cache.write_text(json.dumps({"n": len(words), "t": times}))
        for w, (s, e) in zip(words, times):
            w["s"], w["e"] = round(cursor + s, 3), round(cursor + e, 3)
        voice_track.append((cursor, audio))

        mood = dict(state["mood"]); mood.update(b.get("mood", {})); state["mood"] = mood
        state["cam"] = b.get("cam", state["cam"])
        if "meter" in b:
            state["meter"] = b["meter"]
        is_summary = (b.get("card") or {}).get("type") == "summary"
        tb = {k: v for k, v in b.items() if k not in ("text", "say", "pause", "speed")}
        tb.update(start=round(cursor, 3), text=b["text"].replace("*", ""), mood=mood, cam=state["cam"],
                  meter=state["meter"], chunks=chunk_words(words))
        if is_summary:
            tb["hideSubs"] = b.get("hideSubs", True)
        timeline_beats.append(tb)
        pause = b.get("pause", 0.22 if not re.search(r"[.!?…]$", b["text"].strip()) else 0.32)
        cursor += dur + pause
        print(f"  [{i + 1:02d}] {dur:4.1f}s  {say}", flush=True)

    tail = script.get("tail", 2.2)
    duration = cursor + tail
    for i, tb in enumerate(timeline_beats):
        tb["end"] = timeline_beats[i + 1]["start"] if i + 1 < len(timeline_beats) else duration

    # 2) pista de voz + boca (RMS por fotograma)
    n = int(duration * SR)
    vt = np.zeros(n, dtype=np.float32)
    for t0, a in voice_track:
        add(vt, a, t0)
    hop = SR // FPS
    frames = int(np.ceil(duration * FPS))
    rms = np.array([np.sqrt(np.mean(vt[k * hop:(k + 1) * hop] ** 2) + 1e-12) for k in range(frames)])
    ref = np.percentile(rms[rms > 0.01], 90) if np.any(rms > 0.01) else 1
    mouth = np.clip((rms / ref) ** 0.8, 0, 1)
    mouth[mouth < 0.12] = 0
    sm = np.copy(mouth)
    for k in range(1, frames):
        sm[k] = max(mouth[k], sm[k - 1] * 0.55)
    mouth = np.round(sm, 3).tolist()

    tips, seen = [], set()
    for tb in timeline_beats:
        tip = tb.get("tip")
        if tip and json.dumps(tip, sort_keys=True) not in seen:
            seen.add(json.dumps(tip, sort_keys=True)); tips.append(tip)

    timeline = {
        "fps": FPS, "duration": round(duration, 3), "scene": script.get("scene", "salon"),
        "cast": script["cast"], "positions": script.get("positions", {}), "meter": script.get("meter"),
        "handle": script.get("handle"), "tips": tips, "beats": timeline_beats, "mouth": mouth,
    }
    tl_path = work / "timeline.json"
    tl_path.write_text(json.dumps(timeline, ensure_ascii=False))

    # 3) efectos de sonido + música
    fx = np.zeros(n, dtype=np.float32)
    prev = {}
    for i, tb in enumerate(timeline_beats):
        t = tb["start"]
        card = tb.get("card") or {}
        pcard = prev.get("card") or {}
        if tb.get("tip") and tb.get("tip") != prev.get("tip"):
            add(fx, sfx("ding"), t, 0.9)
        if card and not (card.get("id") and card.get("id") == pcard.get("id")) and card.get("type") not in ("summary",):
            add(fx, sfx("pop"), t + 0.03, 0.9)
        if i > 0 and tb["cam"] != prev.get("cam"):
            add(fx, sfx("whoosh"), max(0, t - 0.08), 0.6)
        if prev.get("meter") is not None and tb.get("meter") is not None and tb["meter"] < prev["meter"]:
            add(fx, sfx("buzz"), t + 0.3, 0.8)
        for f in tb.get("fx", []):
            if f["type"] in ("pain", "bite"):
                add(fx, sfx("boing"), t + 0.05, 0.9)
            if f["type"] in ("exclaim", "question"):
                add(fx, sfx("pop"), t, 0.7)
        if tb.get("quote"):
            add(fx, sfx("pop"), t + 0.05, 0.6)
        if card.get("type") == "summary":
            for j in range(len(tips)):
                add(fx, sfx("tick"), t + 0.2 + j * 0.22, 1.0)
                add(fx, sfx("buzz"), t + 0.55 + j * 0.22, 0.35)
            add(fx, sfx("ding"), t + 0.4 + len(tips) * 0.22, 1.0)
        prev = tb
    mix = vt + fx
    if script.get("music", True):
        mix += music(duration, gain=script.get("music_gain", 0.07)).astype(np.float32)
    mix_path = work / "mix.wav"
    sf.write(mix_path, mix / max(1.0, np.max(np.abs(mix)) * 1.05), SR)

    # 4) render
    frames_dir = work / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    out_dir = ROOT / "salida"
    if preview:
        picks = [int(tb["start"] * FPS + min(0.9, (tb["end"] - tb["start"]) * 0.6) * FPS) for tb in timeline_beats]
        subprocess.run(["node", str(ROOT / "engine/render.js"), str(tl_path), str(frames_dir), str(workers), ",".join(map(str, picks))], check=True)
        cols = 6
        files = sorted(frames_dir.glob("*.jpg"))
        sheet = out_dir / f"{name}_preview.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-pattern_type", "glob", "-i", str(frames_dir / "*.jpg"),
                        "-vf", f"scale=270:480,tile={cols}x{int(np.ceil(len(files) / cols))}:padding=6:color=white", "-frames:v", "1", str(sheet)], check=True)
        print("✔ vista previa:", sheet)
        return sheet
    subprocess.run(["node", str(ROOT / "engine/render.js"), str(tl_path), str(frames_dir), str(workers)], check=True)
    out = out_dir / f"{name}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(frames_dir / "f%05d.jpg"), "-i", str(mix_path),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    if not keep:
        shutil.rmtree(frames_dir)
    print(f"✔ {out}  ({duration:.1f}s)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("guiones", nargs="+")
    ap.add_argument("--voz", help="p. ej. piper:es_ES-davefx-medium, kokoro:em_alex, edge:es-ES-AlvaroNeural, elevenlabs:<id>")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--keep", action="store_true", help="conservar fotogramas")
    a = ap.parse_args()
    for g in a.guiones:
        build(g, a.voz, a.preview, a.workers, a.keep)
