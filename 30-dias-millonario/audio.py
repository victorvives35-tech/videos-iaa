"""Música procedural + efectos de sonido + mezcla final -> build/<ep>/mix.wav"""
import json, subprocess, sys, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"
B = f"build/{EP}"
SR = 48000
rng = np.random.default_rng(7)
TL = json.load(open(f"{B}/timeline.json"))
N = int((TL["duration"] + 1.0) * SR)

def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], "band", fs=SR, output="sos"), x)
def tt(d): return np.arange(int(d * SR)) / SR
def env_adsr(n, a=0.01, r=0.2):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr and nr < n: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def noise(d): return rng.standard_normal(int(d * SR))
def nf(n): return 440 * 2 ** ((n - 69) / 12)
def add(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    if i < 0: x, i = x[-i:], 0
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += g * x

# ---------------- instrumentos ----------------
def kick(d=0.45):
    t = tt(d); f = 45 + 110 * np.exp(-t * 28)
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7))
def snare(d=0.25):
    t = tt(d)
    return 0.7 * bp(noise(d), 1500, 8000) * np.exp(-t * 18) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
def hat(d=0.06):
    return hp(noise(d), 7000) * np.exp(-tt(d) * 70) * 0.5
def clap(d=0.3):
    x = bp(noise(d), 900, 5000); t = tt(d)
    e = sum(np.exp(-np.clip(t - k * 0.011, 0, None) * 60) * (t >= k * 0.011) for k in range(3))
    return x * (e + np.exp(-t * 12) * 0.5) * 0.5
def sub808(n, d):
    t = tt(d); f = nf(n)
    return np.tanh(1.6 * np.sin(2 * np.pi * f * t)) * np.exp(-t * 1.6) * env_adsr(len(t), 0.005, 0.05)
def pad(notes, d, bright=1800, det=0.12):
    t = tt(d); x = np.zeros_like(t)
    for n in notes:
        for dv in (-det, 0, det):
            f = nf(n + dv / 1.0 * 0.1)
            x += 2 * ((t * f) % 1) - 1
    x = lp(x / (3 * len(notes)), bright, 2)
    return x * env_adsr(len(t), min(0.6, d / 3), min(0.8, d / 3))
def keys(n, d, dec=2.5):  # piano eléctrico (FM)
    t = tt(d); f = nf(n)
    m = np.sin(2 * np.pi * f * 2 * t) * 1.2 * np.exp(-t * 3)
    return np.sin(2 * np.pi * f * t + m) * np.exp(-t * dec) * env_adsr(len(t), 0.003, 0.1)
def pluck(n, d):  # Karplus-Strong
    f = nf(n); L = int(SR / f); buf = rng.uniform(-1, 1, L); out = np.zeros(int(d * SR))
    for i in range(len(out)):
        out[i] = buf[i % L]
        buf[i % L] = 0.5 * (buf[i % L] + buf[(i + 1) % L]) * 0.996
    return out
def drone(n, d):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * nf(n) * k * t + k) / k for k in (1, 2, 3)) + 0.3 * lp(noise(d), 200)
    return x * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t)) * env_adsr(len(t), 1.0, 1.0)

# ---------------- efectos ----------------
def sfx(name):
    if name == "riser":
        d = 3.0; t = tt(d); f = 200 * (1 + 8 * (t / d) ** 2)
        x = 0.4 * bp(noise(d), 400, 9000) * (t / d) ** 2 + 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 3
        return x
    if name == "boom":
        d = 2.5; t = tt(d); f = 30 + 70 * np.exp(-t * 6)
        return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8)) + 0.6 * lp(noise(d), 900) * np.exp(-t * 4)
    if name == "cash":
        d = 1.2; t = tt(d); x = 0.5 * hp(noise(0.05), 2000) * np.exp(-tt(0.05) * 60)
        x = np.concatenate([x, np.zeros(len(t) - len(x))])
        for k, n in enumerate((88, 93, 97)):
            b = np.sin(2 * np.pi * nf(n) * t) * np.exp(-t * 4) + 0.3 * np.sin(2 * np.pi * nf(n) * 2.76 * t) * np.exp(-t * 7)
            x[int(0.06 * SR * (k > 0)):] += 0.35 * b[: len(t) - int(0.06 * SR * (k > 0))]
        return x
    if name == "paper":
        d = 0.7; t = tt(d); g = (rng.random(len(t)) > 0.985).astype(float)
        return bp(noise(d) * (0.3 + lp(g, 40) * 30), 1500, 7000) * env_adsr(len(t), 0.02, 0.3) * 0.6
    if name == "thunder":
        d = 3.5; t = tt(d)
        return lp(noise(d), 300, 3) * (np.exp(-t * 1.2) * (1 + 0.6 * np.sin(2 * np.pi * 3 * t))) * 3 + lp(noise(d), 2000) * np.exp(-t * 6) * 0.5
    if name == "door":
        d = 0.8; t = tt(d)
        return np.tanh(3 * lp(noise(d), 150, 3) * np.exp(-t * 9) * 4 + np.sin(2 * np.pi * 60 * t) * np.exp(-t * 10))
    if name == "idea":
        d = 1.6; t = tt(d); x = np.zeros(len(t))
        for k, n in enumerate((84, 88, 91, 96, 100)):
            add(x, np.sin(2 * np.pi * nf(n) * tt(1.2)) * np.exp(-tt(1.2) * 4), k * 0.06, 0.25)
        return x + 0.15 * hp(noise(d), 6000) * np.exp(-t * 3)
    if name == "whoosh":
        d = 0.9; t = tt(d); x = noise(d); e = np.sin(np.pi * t / d) ** 2
        lo = lp(x, 800); hi = lp(x, 5000)
        return (lo * (1 - t / d) + hi * (t / d)) * e * 0.9
    if name == "pop":
        d = 0.15; t = tt(d); f = 300 + 900 * np.exp(-t * 40)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * 0.7
    if name == "camera":
        d = 0.35; x = np.zeros(int(d * SR))
        add(x, hp(noise(0.03), 2000) * np.exp(-tt(0.03) * 100), 0, 0.8)
        add(x, bp(noise(0.08), 800, 4000) * np.exp(-tt(0.08) * 50), 0.09, 0.7)
        return x
    if name == "scratch":
        d = 0.55; t = tt(d); x = noise(d)
        f = 1200 + 1000 * np.sin(2 * np.pi * 7 * t)
        y = bp(x, 600, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR / 40))
        return y * env_adsr(len(t), 0.005, 0.2) * 1.2
    if name == "rewind":
        d = 1.5; t = tt(d); f = 300 + 1800 * (t / d) ** 1.5
        x = 0.25 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) + 0.4 * bp(noise(d), 2000, 9000)
        return lp(x, 6000) * env_adsr(len(t), 0.05, 0.1) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t))
    if name == "stamp":
        d = 0.6; t = tt(d)
        return np.tanh(3 * (np.sin(2 * np.pi * (50 + 80 * np.exp(-t * 30)) * t) * np.exp(-t * 12) + lp(noise(d), 1500) * np.exp(-t * 25)))
    if name == "tick":
        d = 3.2; x = np.zeros(int(d * SR))
        for k in range(int(d / 0.25)):
            add(x, hp(noise(0.02), 3000) * np.exp(-tt(0.02) * 200) + 0.3 * np.sin(2 * np.pi * (2400 if k % 2 else 1800) * tt(0.02)), k * 0.25, 0.8)
        return x
    return np.zeros(10)

# ---------------- música por escenas ----------------
music = np.zeros(N)
SC = {s["id"]: s for s in TL["scenes"]}
BPM = 92; beat = 60 / BPM
Am, F, C, G, Dm, E = [57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62], [50, 53, 57], [52, 56, 59]

def span(i): s = SC[i]; return s["start"], s["start"] + s["dur"]

# flash: trap épico a tope
a, b = span("flash")
fl = np.zeros(int((b - a + 1) * SR))
bt = 60 / 140
for j, k in enumerate(np.arange(0, b - a + bt, bt)):
    if j % 2 == 0: add(fl, kick(), k, 0.9)
    else: add(fl, clap(), k, 0.6)
    for h in range(4): add(fl, hat(), k + h * bt / 4, 0.25)
add(fl, sub808(33, b - a + 0.5), 0, 0.5)
add(fl, pad([57, 61, 64, 69], b - a + 0.6, 3500), 0, 0.35)
for q, n in enumerate([81, 85, 88, 93, 88, 85] * 6):
    add(fl, pluck(n, 0.4) * 0.5, q * bt / 2, 0.25)
add(music, fl, a, 1.0)
# freeze: frenazo de cinta (la cola de la música bajando de tono)
a2, b2 = span("freeze")
tail = fl[int((b - a - 0.6) * SR): int((b - a) * SR)]
idx = np.cumsum(np.linspace(1.0, 0.05, int(0.9 * SR)))
idx = idx[idx < len(tail) - 1].astype(int)
add(music, tail[idx] * np.linspace(1, 0, len(idx)), a2, 1.0)
# rewind: la música del flash al revés y acelerando
a3, b3 = span("rewind")
rv = fl[: int((b - a) * SR)][::-1]
idx = np.cumsum(np.linspace(1.5, 3.0, int((b3 - a3) * SR)))
idx = idx[idx < len(rv) - 1].astype(int)
add(music, lp(rv[idx], 5000) * 0.7, a3, 1.0)
# hook: drone oscuro + latido
a, b = span("hook")
add(music, drone(33, b - a + 0.5), a, 0.25)
for k in np.arange(a + 0.3, b, beat * 2):  # latido
    add(music, kick(0.4), k, 0.35); add(music, kick(0.4), k + 0.18, 0.2)
# title: golpe + pad épico
a, b = span("title")
add(music, pad([45, 52, 57, 60, 64], b - a + 1.2, 2500), a, 0.35)
add(music, kick(0.6), a, 0.9)
# kitchen: tensión (frigio) + pulso grave
a, b = span("kitchen")
add(music, drone(33, b - a + 1), a, 0.18)
add(music, pad([45, 46, 52], b - a + 1, 900), a, 0.25)
for k in np.arange(a, b, beat):
    add(music, sub808(33, beat * 0.9), k, 0.10)
for k in np.arange(a, b, beat / 2):
    add(music, hat(0.04), k, 0.10)
# bedroom: piano triste + lluvia
a, b = span("bedroom")
prog = [Am, F, C, G]
for j, k in enumerate(np.arange(a, b, beat * 4)):
    ch = prog[j % 4]
    add(music, pad([n - 12 for n in ch], beat * 4.2, 1200), k, 0.18)
    for q, n in enumerate([ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1], ch[0] + 12, ch[2]]):
        add(music, keys(n + 12, beat * 2, 3), k + q * beat / 2, 0.12)
rain = hp(lp(noise(b - a + 1), 6000), 400) * 0.06
add(music, rain * env_adsr(len(rain), 1, 1), a, 1)
# logo + plan: beat lo-fi esperanzador que crece
a, _ = span("logo"); _, b = span("plan")
prog = [F, C, G, Am]
for j, k in enumerate(np.arange(a, b, beat * 4)):
    ch = prog[j % 4]
    add(music, pad(ch, beat * 4.1, 2200), k, 0.16)
    add(music, sub808(ch[0] - 24 + (12 if ch[0] < 50 else 0), beat * 3.5), k, 0.30)
    for q in range(4):
        tq = k + q * beat
        if q in (0, 2) or (q == 3 and j % 2): add(music, kick(), tq, 0.55)
        if q in (1, 3): add(music, clap(), tq, 0.40)
        for h in range(4):
            add(music, hat(), tq + h * beat / 4, 0.18 if h % 2 else 0.28)
    arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24]
    for q in range(8):
        add(music, pluck(arp[q % 4], 0.5) * 0.6, k + q * beat / 2, 0.20)
# cliff: corte en seco, solo un drone de suspense y después el golpe
a, b = span("cliff")
add(music, drone(38, b - a + 1.5), a + 0.3, 0.22)
add(music, pad([50, 53, 56], b - a + 1.5, 700), a + 0.3, 0.2)

# ---------------- efectos ----------------
fx = np.zeros(N)
G = {"scratch": 0.7, "rewind": 0.5, "stamp": 0.8, "tick": 0.45, "riser": 0.35, "boom": 0.8, "cash": 0.5, "paper": 0.5, "thunder": 0.6, "door": 0.7,
     "idea": 0.6, "whoosh": 0.6, "pop": 0.5, "camera": 0.6}
for e in TL["sfx"]:
    x = sfx(e["name"])
    t0 = e["t"]
    add(fx, x, t0, G.get(e["name"], 0.5))

# ---------------- mezcla con ducking ----------------
voice, _ = sf.read(f"{B}/voice.wav")
voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]
venv = lp(np.abs(voice), 6, 1)
venv = venv / (venv.max() or 1)
duck = 1 - 0.55 * np.clip(venv * 4, 0, 1)
mix = 1.0 * voice + music * duck * 0.9 + fx * 0.8
stereo = np.stack([mix, mix], 1)
# un poco de anchura en la música
stereo[:, 0] += 0.08 * np.roll(music * duck, 480)
stereo[:, 1] -= 0.08 * np.roll(music * duck, 480)
stereo /= max(1e-6, np.abs(stereo).max()) / 0.9
sf.write(f"{B}/mix_raw.wav", stereo, SR)
sf.write(f"{B}/music.wav", music, SR)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{B}/mix_raw.wav", "-af",
                "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), f"{B}/mix.wav"], check=True)
print("mix ok", N / SR)
