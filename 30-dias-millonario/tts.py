"""Sintetiza las voces y construye la línea temporal (build/<ep>/timeline.json).

Motor principal: Chatterbox Multilingual (expresivo, control de emoción por línea).
Cada personaje tiene un clip de referencia de timbre (build/refs/<PERSONAJE>.wav),
generado una vez con Kokoro + transposición. Con TTS_ENGINE=kokoro se usa Kokoro directamente.
"""
import importlib, json, os, re, subprocess, sys, numpy as np, soundfile as sf
from voices import VOICES

EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"
mod = importlib.import_module(f"episodes.{EP}")
SCENES, EPISODE = mod.SCENES, mod.EPISODE
B = f"build/{EP}"
ENGINE = os.environ.get("TTS_ENGINE", "chatterbox")
SR = 48000
FPS = 30
MODELS = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro"))
os.makedirs(f"{B}/lines", exist_ok=True)
os.makedirs("build/refs", exist_ok=True)

PRON = [(r"ApruebaYa", "Aprueba Ya"), (r"tiktoker", "tiktóker"), (r"\bapp\b", "ap")]
REF_TEXT = {
    "LEO": "Bueno, hoy os voy a contar algo que me pasó en el instituto. La verdad es que todavía no me lo creo, pero es totalmente real.",
    "PAPA": "Mira, hijo, yo a tu edad ya trabajaba por las tardes. Las cosas no se consiguen solas, hay que esforzarse cada día.",
    "MAMA": "Cariño, ya sabes que solo queremos lo mejor para ti. Ven, siéntate, que tenemos que hablar un momento.",
    "MARTA": "¡Hala, qué pasada! ¿Esto lo has hecho tú solo? Pásamelo ahora mismo, que mañana tengo examen.",
    "ORTEGA": "Buenas tardes. Represento a una empresa de educación con presencia en toda Europa. Tenemos una propuesta para usted.",
}

def tts_text(t):
    for a, b in PRON:
        t = re.sub(a, b, t)
    return t

_K = None
def kokoro():
    global _K
    if _K is None:
        from kokoro_onnx import Kokoro
        k = Kokoro(f"{MODELS}/kokoro.onnx", f"{MODELS}/voices.bin")
        _K = (k, {n: k.get_voice_style(n) for n in ["em_alex", "ef_dora", "em_santa"]})
    return _K

def ffpost(src, dst, pitch=0.0):
    pre = f"rubberband=pitch={2 ** (pitch / 12):.4f}:formant=preserved," if pitch else ""
    af = (pre + "silenceremove=start_periods=1:start_threshold=-45dB,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "highpass=f=70,equalizer=f=3500:t=q:w=1.2:g=2,"
          "acompressor=threshold=-20dB:ratio=3:attack=5:release=90,"
          f"aresample={SR}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ac", "1", dst], check=True)

def kokoro_line(spk, text, path):
    k, styles = kokoro()
    v = VOICES[spk]
    st = sum(styles[n] * w for n, w in v["mix"].items())
    audio, sr = k.create(tts_text(text), voice=st, speed=v["speed"], lang="es")
    sf.write(path + ".raw.wav", audio, sr)
    ffpost(path + ".raw.wav", path, v["pitch"]); os.remove(path + ".raw.wav")

def ref_for(spk):
    p = f"build/refs/{spk}.wav"
    if not os.path.exists(p):
        kokoro_line(spk, REF_TEXT[spk], p)
    return p

_CB = None
def chatter():
    global _CB
    if _CB is None:
        import torch
        torch.set_num_threads(os.cpu_count() or 4)
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        _CB = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    return _CB

_WH = None
def score(path, text):
    """Transcribe con Whisper y devuelve parecido (0-1) con el texto del guion."""
    global _WH
    import difflib, unicodedata, librosa
    from faster_whisper import WhisperModel
    if _WH is None:
        _WH = WhisperModel("small", device="cpu", compute_type="int8")
    def norm(x):
        x = unicodedata.normalize("NFD", x.lower())
        x = "".join(ch for ch in x if unicodedata.category(ch) != "Mn")
        x = x.replace("15", "quince").replace("30", "treinta").replace("2", "dos")
        return re.sub(r"[^a-z0-9 ]", " ", x).split()
    a, sr = sf.read(path)
    a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
    segs, _ = _WH.transcribe(a, language="es", beam_size=5, word_timestamps=True)
    segs = list(segs)
    hyp = " ".join(s_.text for s_ in segs)
    ref = norm(tts_text(text))
    # recorta lo que sobre después de la última palabra del guion (ruido, palabras inventadas)
    words = [w for s_ in segs for w in (s_.words or [])]
    # fin = la última palabra transcrita que coincide con la última palabra del guion;
    # todo lo que venga después (ruido, palabras inventadas) se descarta
    end = words[-1].end if words else None
    last = ref[-1] if ref else None
    hits = [w for w in words if last and last in norm(w.word)]
    if hits:
        end = hits[-1].end
    start = words[0].start if words else 0.0
    return difflib.SequenceMatcher(None, ref, norm(hyp)).ratio(), hyp, start, end

def trim(path, start, end):
    a, sr = sf.read(path)
    i0 = 0; i1 = min(len(a), int((end + 0.14) * sr))
    a = a[i0:i1]
    f = int(0.03 * sr); a[-f:] *= np.linspace(1, 0, f); a[:f // 3] *= np.linspace(0, 1, f // 3)
    sf.write(path, a, sr)

def synth(spk, text, opts, path):
    if os.path.exists(path):
        return
    if ENGINE == "kokoro":
        return kokoro_line(spk, text, path)
    best = None
    for k in range(3):
        o = dict(opts); o["seed"] = opts.get("seed", 1234) + k * 101
        _synth_cb(spk, text, o, path + f".try{k}.wav")
        r, hyp, st, en = score(path + f".try{k}.wav", text)
        if en: trim(path + f".try{k}.wav", st, en)
        print(f"     intento {k}: {r:.2f}  «{hyp.strip()}»", flush=True)
        if best is None or r > best[0]: best = (r, k)
        if r >= 0.9: break
    os.replace(path + f".try{best[1]}.wav", path)
    for k in range(3):
        if os.path.exists(path + f".try{k}.wav"): os.remove(path + f".try{k}.wav")

def _synth_cb(spk, text, opts, path):
    import torch, torchaudio
    m = chatter()
    torch.manual_seed(opts.get("seed", 1234))
    wav = m.generate(tts_text(text), language_id="es", audio_prompt_path=ref_for(spk),
                     exaggeration=opts.get("exag", 0.5), cfg_weight=opts.get("cfg", 0.5),
                     temperature=opts.get("temp", 0.75))
    torchaudio.save(path + ".raw.wav", wav.cpu(), m.sr)
    # la referencia ya tiene el timbre; un retoque de tono opcional por personaje
    ffpost(path + ".raw.wav", path, VOICES[spk].get("cb_pitch", 0.0)); os.remove(path + ".raw.wav")
    # velocidad: Chatterbox habla algo pausado; acelerar un poco sin cambiar el tono
    sp = opts.get("speed", VOICES[spk].get("cb_speed", 1.0))
    if abs(sp - 1) > 0.01:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", f"rubberband=tempo={sp}",
                        path + ".s.wav"], check=True)
        os.replace(path + ".s.wav", path)

def main():
    timeline = {"episode": EPISODE, "fps": FPS, "sr": SR, "scenes": [], "lines": [], "sfx": []}
    t = 0.0; voice = []; li = 0
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
                spk, text = ev[1], ev[2]
                opts = ev[3] if len(ev) > 3 else {}
                path = f"{B}/lines/{li:03d}_{spk}.wav"
                synth(spk, text, opts, path)
                a, _ = sf.read(path)
                d = len(a) / SR
                hop = SR // FPS
                env = [float(np.sqrt(np.mean(a[i:i + hop] ** 2))) for i in range(0, len(a), hop)]
                m = max(env) or 1
                env = [round(min(1, e / (0.6 * m)), 3) for e in env]
                timeline["lines"].append({"i": li, "scene": sc["id"], "speaker": spk, "text": text,
                                          "start": round(t, 3), "end": round(t + d, 3), "env": env})
                voice.append((t, a)); lines.append(li)
                t += d + opts.get("gap", 0.22)
                li += 1
                print(f"{li:3d} {spk:6s} {d:5.2f}s  {text}", flush=True)
        t += sc.get("post", 0.4)
        if t - start < sc.get("min", 0):
            t = start + sc["min"]
        timeline["scenes"].append({"id": sc["id"], "start": round(start, 3),
                                   "dur": round(t - start, 3), "lines": lines})
    timeline["duration"] = round(t, 3)
    out = np.zeros(int(t * SR) + SR)
    for st, a in voice:
        i = int(st * SR); out[i:i + len(a)] += a
    sf.write(f"{B}/voice.wav", out, SR)
    json.dump(timeline, open(f"{B}/timeline.json", "w"), ensure_ascii=False)
    print("DURACIÓN TOTAL:", round(t, 1), "s")

if __name__ == "__main__":
    main()
