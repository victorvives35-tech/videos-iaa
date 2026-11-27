"""Inserta pausas dramáticas reales donde el guion tiene "..." en mitad de una frase.

El TTS suele ignorar los puntos suspensivos; aquí se localiza con Whisper (marcas por palabra)
el final de la palabra que precede a "..." y se inserta silencio en ese punto.
Uso: python3 pauses.py ep01   (luego volver a ejecutar tts.py para rehacer la línea temporal)
"""
import glob, importlib, json, os, re, sys, unicodedata
import numpy as np, soundfile as sf, librosa
from faster_whisper import WhisperModel

EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"
PAUSE = 0.5
SCENES = importlib.import_module(f"episodes.{EP}").SCENES
texts = [ev[2] for sc in SCENES for ev in sc["events"] if ev[0] == "say"]
done_f = f"build/{EP}/lines/.paused.json"
done = json.load(open(done_f)) if os.path.exists(done_f) else []

def norm(x):
    x = unicodedata.normalize("NFD", x.lower())
    return re.sub(r"[^a-z0-9ñ]", "", "".join(ch for ch in x if unicodedata.category(ch) != "Mn"))

m = None
for i, text in enumerate(texts):
    body = text.strip()
    marks = [mt.start() for mt in re.finditer(r"\.\.\.", body) if mt.end() < len(body) - 1]
    if not marks or i in done:
        continue
    f = glob.glob(f"build/{EP}/lines/{i:03d}_*.wav")[0]
    if m is None:
        m = WhisperModel("small", device="cpu", compute_type="int8")
    a, sr = sf.read(f)
    a16 = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
    segs, _ = m.transcribe(a16, language="es", beam_size=5, word_timestamps=True)
    words = [w for s in segs for w in (s.words or [])]
    cuts = []
    for pos in marks:
        before = norm(body[:pos].split()[-1])
        cand = [w for w in words if norm(w.word) == before or (before and before in norm(w.word))]
        if cand:
            # siguiente palabra: cortar en el hueco entre las dos
            w = cand[0]; nxt = words[words.index(w) + 1] if words.index(w) + 1 < len(words) else None
            cut = (w.end + nxt.start) / 2 if nxt else w.end
            cuts.append(cut)
    if not cuts:
        print(f"{i}: no encontré la palabra antes de '...'  ({text})"); continue
    out = []; prev = 0
    for cut in sorted(cuts):
        k = int(cut * sr)
        seg_ = a[prev:k].copy()
        n = int(0.012 * sr); seg_[-n:] *= np.linspace(1, 0, n)
        out += [seg_, np.zeros(int(PAUSE * sr))]
        prev = k
    rest = a[prev:].copy(); n = int(0.012 * sr); rest[:n] *= np.linspace(0, 1, n)
    out.append(rest)
    sf.write(f, np.concatenate(out), sr)
    done.append(i)
    print(f"{i}: +{PAUSE}s de pausa en {[round(c, 2) for c in cuts]}  «{text}»")
json.dump(done, open(done_f, "w"))
