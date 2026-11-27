"""Transcribe cada línea con Whisper y la compara con el guion (detecta errores de TTS)."""
import glob, json, sys, re, unicodedata, difflib
from faster_whisper import WhisperModel

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9ñ ]", " ", s).split()

EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"
tl = json.load(open(f"build/{EP}/timeline.json"))
m = WhisperModel(sys.argv[2] if len(sys.argv) > 2 else "small", device="cpu", compute_type="int8")
bad = []
for ln in tl["lines"]:
    f = glob.glob(f"build/{EP}/lines/{ln['i']:03d}_*.wav")[0]
    import soundfile as sf, librosa, numpy as np
    a, sr = sf.read(f); a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
    a = np.concatenate([np.zeros(6400, np.float32), a, np.zeros(8000, np.float32)])
    segs, _ = m.transcribe(a, language="es", beam_size=5)
    hyp = " ".join(s.text for s in segs).strip()
    fix = lambda x: x.replace("30", "treinta").replace("15", "quince").replace("300", "trescientos")
    a = norm(ln["text"].replace("ApruebaYa", "Aprueba Ya")); b = norm(fix(hyp))
    r = difflib.SequenceMatcher(None, a, b).ratio()
    flag = "OK " if r > 0.85 else "!! "
    if r <= 0.85: bad.append(ln["i"])
    print(f"{flag}{ln['i']:3d} {r:.2f} | {ln['text']}\n          -> {hyp}")
print("REVISAR:", bad)
