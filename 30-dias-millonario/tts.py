"""Sintetiza las voces y construye la línea temporal (build/timeline.json)."""
import importlib, json, os, re, subprocess, sys, numpy as np, soundfile as sf
from voices import VOICES

EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"
mod = importlib.import_module(f"episodes.{EP}")
SCENES, EPISODE = mod.SCENES, mod.EPISODE
B = f"build/{EP}"

SR = 48000
FPS = 30
MODELS = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro"))
os.makedirs(f"{B}/lines", exist_ok=True)

PRON = [(r"ApruebaYa", "Aprueba Ya"), (r"tiktoker", "tiktóker"), (r"app\b", "ap")]

def tts_text(t):
    for a, b in PRON:
        t = re.sub(a, b, t)
    return t

def synth(kok, styles, speaker, text, path):
    if os.path.exists(path):
        return
    v = VOICES[speaker]
    st = sum(styles[n] * w for n, w in v["mix"].items())
    audio, sr = kok.create(tts_text(text), voice=st, speed=v["speed"], lang="es")
    raw = path + ".raw.wav"
    sf.write(raw, audio, sr)
    p = 2 ** (v["pitch"] / 12)
    af = (f"rubberband=pitch={p:.4f}:formant=preserved,"
          "silenceremove=start_periods=1:start_threshold=-45dB,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,"
          f"aresample={SR}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af,
                    "-ac", "1", path], check=True)
    os.remove(raw)

def main():
    from kokoro_onnx import Kokoro
    kok = Kokoro(f"{MODELS}/kokoro.onnx", f"{MODELS}/voices.bin")
    styles = {n: kok.get_voice_style(n) for n in ["em_alex", "ef_dora", "em_santa"]}
    timeline = {"episode": EPISODE, "fps": FPS, "sr": SR, "scenes": [], "lines": [], "sfx": []}
    t = 0.0
    voice = []
    li = 0
    for sc in SCENES:
        start = t
        t += sc.get("pre", 0.4)
        lines = []
        for ev in sc["events"]:
            if ev[0] == "pause":
                t += ev[1]
            elif ev[0] == "sfx":
                off = ev[2] if len(ev) > 2 else 0.0
                timeline["sfx"].append({"t": round(t + off, 3), "name": ev[1], "scene": sc["id"]})
            elif ev[0] == "say":
                _, spk, text = ev
                path = f"{B}/lines/{li:03d}_{spk}.wav"
                synth(kok, styles, spk, text, path)
                a, _ = sf.read(path)
                d = len(a) / SR
                # envolvente para sincronía labial (a FPS)
                hop = SR // FPS
                env = [float(np.sqrt(np.mean(a[i:i + hop] ** 2))) for i in range(0, len(a), hop)]
                m = max(env) or 1
                env = [round(min(1, e / (0.6 * m)), 3) for e in env]
                ln = {"i": li, "scene": sc["id"], "speaker": spk, "text": text,
                      "start": round(t, 3), "end": round(t + d, 3), "env": env}
                voice.append((t, a))
                lines.append(li)
                timeline["lines"].append(ln)
                t += d + 0.28
                li += 1
                print(f"{li:3d} {spk:6s} {d:5.2f}s  {text}")
        t += sc.get("post", 0.4)
        if t - start < sc.get("min", 0):
            t = start + sc["min"]
        timeline["scenes"].append({"id": sc["id"], "start": round(start, 3),
                                   "dur": round(t - start, 3), "lines": lines})
    timeline["duration"] = round(t, 3)
    out = np.zeros(int(t * SR) + SR)
    for st, a in voice:
        i = int(st * SR)
        out[i:i + len(a)] += a
    sf.write(f"{B}/voice.wav", out, SR)
    json.dump(timeline, open(f"{B}/timeline.json", "w"), ensure_ascii=False)
    print("DURACIÓN TOTAL:", round(t, 1), "s")

if __name__ == "__main__":
    main()
