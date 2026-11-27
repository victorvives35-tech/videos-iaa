"""Música procedural + ambientes + efectos + voces con reverb por sala -> build/<ep>/mix.wav (-14 LUFS)."""
import json, subprocess, sys, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"
B = f"build/{EP}"
SR = 48000
rng = np.random.default_rng(7)
TL = json.load(open(f"{B}/timeline.json"))
N = int((TL["duration"] + 1.5) * SR)
SC = {s["id"]: s for s in TL["scenes"]}
LN = TL["lines"]

# ------------------------------------------------------------ utilidades DSP
def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], "band", fs=SR, output="sos"), x)
def tt(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))
def nf(n): return 440 * 2 ** ((n - 69) / 12)
def env_adsr(n, a=0.01, r=0.2):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    if na: e[:min(na, n)] = np.linspace(0, 1, min(na, n))
    if nr and nr < n: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def add(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    if i < 0: x, i = x[-i:], 0
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += g * x
def span(i): s = SC[i]; return s["start"], s["start"] + s["dur"]
def sfx_times(scene, name): return [e["t"] for e in TL["sfx"] if e["scene"] == scene and e["name"] == name]
def line(scene, k): return [l for l in LN if l["scene"] == scene][k]
def fade(x, a=0.3, r=0.6): return x * env_adsr(len(x), a, r)

def ir(rt, bright=6000, pre=0.012):
    """respuesta al impulso sintética (ruido con caída exponencial)"""
    t = tt(rt * 1.4)
    x = noise(rt * 1.4) * np.exp(-6.9 * t / rt)
    x = lp(x, bright)
    x = np.concatenate([np.zeros(int(pre * SR)), x])
    return x / np.sqrt((x ** 2).sum())
REVERB = {"small": ir(0.35, 5000), "room": ir(0.55, 4500), "big": ir(1.6, 7000), "hall": ir(2.4, 3500)}

# ------------------------------------------------------------ instrumentos
def kick(d=0.45):
    t = tt(d); f = 45 + 110 * np.exp(-t * 28)
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7))
def snare(d=0.25):
    t = tt(d)
    return 0.7 * bp(noise(d), 1500, 8000) * np.exp(-t * 18) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
def hat(d=0.06): return hp(noise(d), 7000) * np.exp(-tt(d) * 70) * 0.5
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
            f = nf(n) * (1 + dv * 0.01)
            x += 2 * ((t * f) % 1) - 1
    x = lp(x / (3 * len(notes)), bright, 2)
    return x * env_adsr(len(t), min(0.6, d / 3), min(0.8, d / 3))
def strings(notes, d, bright=2500):
    """cuerdas: sierras desafinadas con vibrato lento y ataque largo"""
    t = tt(d); x = np.zeros_like(t)
    for n in notes:
        for k, dv in enumerate((-0.15, -0.05, 0.05, 0.15)):
            f = nf(n) * (1 + dv * 0.01) * (1 + 0.003 * np.sin(2 * np.pi * (5 + k * 0.3) * t))
            x += 2 * ((np.cumsum(f) / SR) % 1) - 1
    x = lp(x / (4 * len(notes)), bright, 2)
    return x * env_adsr(len(t), min(1.2, d / 2.5), min(1.0, d / 3))
def piano(n, d=2.5, vel=1.0):
    t = tt(d); f = nf(n)
    x = sum(np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * (1.6 + h * 0.9)) / h for h in range(1, 7))
    return x * env_adsr(len(t), 0.002, 0.15) * vel * 0.6
def keys(n, d, dec=2.5):
    t = tt(d); f = nf(n)
    m = np.sin(2 * np.pi * f * 2 * t) * 1.2 * np.exp(-t * 3)
    return np.sin(2 * np.pi * f * t + m) * np.exp(-t * dec) * env_adsr(len(t), 0.003, 0.1)
def pluck(n, d):
    f = nf(n); L = int(SR / f); buf = rng.uniform(-1, 1, L); out = np.zeros(int(d * SR))
    for i in range(len(out)):
        out[i] = buf[i % L]
        buf[i % L] = 0.5 * (buf[i % L] + buf[(i + 1) % L]) * 0.996
    return out
def drone(n, d):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * nf(n) * k * t + k) / k for k in (1, 2, 3)) + 0.3 * lp(noise(d), 200)
    return x * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t)) * env_adsr(len(t), 1.0, 1.0)
def heartbeat(d, bpm=72):
    x = np.zeros(int(d * SR)); bt = 60 / bpm
    for k in np.arange(0, d, bt):
        for o, g in ((0, 1.0), (0.22, 0.7)):
            t = tt(0.25)
            add(x, lp(np.sin(2 * np.pi * (48 + 30 * np.exp(-t * 30)) * t) * np.exp(-t * 18), 200), k + o, g)
    return x
def riser(d):
    t = tt(d); f = 200 * (1 + 8 * (t / d) ** 2)
    return 0.4 * bp(noise(d), 400, 9000) * (t / d) ** 2 + 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 3

# ------------------------------------------------------------ efectos
def sfx(name):
    if name == "boom":
        d = 2.5; t = tt(d); f = 30 + 70 * np.exp(-t * 6)
        return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8)) + 0.6 * lp(noise(d), 900) * np.exp(-t * 4)
    if name == "hit":
        d = 1.8; t = tt(d); f = 38 + 60 * np.exp(-t * 9)
        return 0.9 * np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)) + 0.3 * lp(noise(d), 3000) * np.exp(-t * 10)
    if name == "cash":
        d = 1.2; t = tt(d); x = np.zeros(len(t))
        add(x, 0.5 * hp(noise(0.05), 2000) * np.exp(-tt(0.05) * 60), 0)
        for k, n in enumerate((88, 93, 97)):
            b = np.sin(2 * np.pi * nf(n) * t) * np.exp(-t * 4) + 0.3 * np.sin(2 * np.pi * nf(n) * 2.76 * t) * np.exp(-t * 7)
            add(x, 0.35 * b, 0.06 * (k > 0))
        return x
    if name == "slide":  # boletín deslizándose por la mesa
        d = 0.9; t = tt(d)
        return bp(noise(d), 400, 3000) * np.sin(np.pi * t / d) ** 2 * 0.5
    if name == "scoff":  # bufido del padre
        d = 0.45; t = tt(d)
        return bp(noise(d), 300, 2500) * np.exp(-t * 7) * env_adsr(len(t), 0.01, 0.1) * 0.7
    if name == "handshake":
        d = 0.5; t = tt(d); x = np.zeros(len(t))
        add(x, bp(noise(0.06), 800, 5000) * np.exp(-tt(0.06) * 70), 0, 1.0)
        add(x, lp(np.sin(2 * np.pi * 70 * tt(0.3)) * np.exp(-tt(0.3) * 15), 300), 0, 0.8)
        return x
    if name == "cards":
        d = 1.6; x = np.zeros(int(d * SR))
        for k in range(9):
            add(x, bp(noise(0.05), 1500, 7000) * np.exp(-tt(0.05) * 80), k * 0.13 + rng.uniform(0, .03), 0.6)
        return x
    if name == "scratch":
        d = 0.55; t = tt(d); x = noise(d)
        f = 1200 + 1000 * np.sin(2 * np.pi * 7 * t)
        y = bp(x, 600, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR / 40))
        return y * env_adsr(len(t), 0.005, 0.2) * 1.2
    if name == "rewind":
        d = 1.6; t = tt(d); f = 300 + 1800 * (t / d) ** 1.5
        x = 0.25 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) + 0.4 * bp(noise(d), 2000, 9000)
        return lp(x, 6000) * env_adsr(len(t), 0.05, 0.1) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t))
    if name == "idea":
        d = 1.6; t = tt(d); x = np.zeros(len(t))
        for k, n in enumerate((84, 88, 91, 96, 100)):
            add(x, np.sin(2 * np.pi * nf(n) * tt(1.2)) * np.exp(-tt(1.2) * 4), k * 0.06, 0.25)
        return x + 0.15 * hp(noise(d), 6000) * np.exp(-t * 3)
    if name == "whoosh":
        d = 0.9; t = tt(d); x = noise(d); e = np.sin(np.pi * t / d) ** 2
        return (lp(x, 800) * (1 - t / d) + lp(x, 5000) * (t / d)) * e * 0.9
    if name == "pop":
        d = 0.15; t = tt(d); f = 300 + 900 * np.exp(-t * 40)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * 0.7
    if name == "camera":
        x = np.zeros(int(0.35 * SR))
        add(x, hp(noise(0.03), 2000) * np.exp(-tt(0.03) * 100), 0, 0.8)
        add(x, bp(noise(0.08), 800, 4000) * np.exp(-tt(0.08) * 50), 0.09, 0.7)
        return x
    return np.zeros(10)

GAIN = {"boom": 0.75, "hit": 0.8, "cash": 0.45, "slide": 0.6, "scoff": 0.0, "handshake": 0.9, "cards": 0.5,
        "scratch": 0.6, "rewind": 0.45, "idea": 0.55, "whoosh": 0.55, "pop": 0.45, "camera": 0.55}

music = np.zeros(N); amb = np.zeros(N); fx = np.zeros(N)
BPM = 92; beat = 60 / BPM
Am, F, C, G, Dm, E = [57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62], [50, 53, 57], [52, 56, 59]

# ---- flash: trap épico
a, b = span("flash")
fl = np.zeros(int((b - a + 1) * SR)); bt = 60 / 140
for j, k in enumerate(np.arange(0, b - a + bt, bt)):
    add(fl, kick() if j % 2 == 0 else clap(), k, 0.9 if j % 2 == 0 else 0.6)
    for h in range(4): add(fl, hat(), k + h * bt / 4, 0.25)
add(fl, sub808(33, b - a + 0.5), 0, 0.5)
add(fl, pad([57, 61, 64, 69], b - a + 0.6, 3500), 0, 0.35)
for q, n in enumerate([81, 85, 88, 93, 88, 85] * 6): add(fl, pluck(n, 0.4) * 0.5, q * bt / 2, 0.25)
add(music, fl, a, 0.6)
# ---- freeze: frenazo de cinta
a2, _ = span("freeze")
tail = fl[int((b - a - 0.6) * SR): int((b - a) * SR)]
idx = np.cumsum(np.linspace(1.0, 0.05, int(0.9 * SR))); idx = idx[idx < len(tail) - 1].astype(int)
add(music, tail[idx] * np.linspace(1, 0, len(idx)), a2, 1.0)
# ---- rewind: música al revés acelerando
a3, b3 = span("rewind")
rv = fl[: int((b - a) * SR)][::-1]
idx = np.cumsum(np.linspace(1.5, 3.0, int((b3 - a3) * SR))); idx = idx[idx < len(rv) - 1].astype(int)
add(music, lp(rv[idx], 5000) * 0.7, a3, 1.0)
# ---- título: golpe + acorde épico
a, b = span("title")
add(music, strings([45, 52, 57, 60, 64], b - a + 2.0, 3000), a, 0.5)
add(music, kick(0.6), a, 0.9); add(music, sub808(33, 2.0), a, 0.5)

# ---- cocina
a, b = span("kitchen")
hit = sfx_times("kitchen", "hit")[0]; hand = sfx_times("kitchen", "handshake")[0]
# ambiente: reloj, nevera, lluvia fuera (amortiguada)
for k in np.arange(a, b, 1.0):
    add(amb, hp(noise(0.012), 2500) * np.exp(-tt(0.012) * 300), k, 0.10)
fr = np.sin(2 * np.pi * 50 * tt(b - a)) * 0.4 + np.sin(2 * np.pi * 100 * tt(b - a)) * 0.2 + lp(noise(b - a), 300) * 0.3
add(amb, fade(fr, 0.5, 0.5), a, 0.035)
add(amb, fade(lp(hp(noise(b - a), 300), 1800), 0.8, 0.8), a, 0.03)
# música: tensión baja que se corta antes del ultimátum
d1 = hit - a
add(music, fade(drone(33, d1 + 0.3), 1.5, 0.3), a, 0.16)
add(music, fade(strings([45, 48, 52], d1 + 0.3, 1200), 1.5, 0.3), a, 0.20)
for k, n in zip(np.arange(a + 1.0, hit - 0.5, beat * 2), [69, 72, 71, 69, 64, 65, 64, 62] * 3):
    add(music, piano(n, 3.0, 0.7), k, 0.10)
# ultimátum: latido + cuerdas en ascenso
add(music, heartbeat(hand - hit + 0.4, 80), hit, 0.45)
add(music, strings([45, 52, 57, 60], hand - hit + 0.6, 1600), hit, 0.28)
add(music, riser(hand - hit) * 0.6, hit, 0.35)
# trato: resolución épica
add(music, strings([41, 48, 53, 57, 60], b - hand + 1.5, 2800), hand, 0.38)
add(music, kick(0.6), hand, 0.6); add(music, sub808(29, 2.0), hand, 0.35)

# ---- habitación
a, b = span("bedroom")
idea = sfx_times("bedroom", "idea")[0]
rain = lp(hp(noise(b - a + 1), 500), 5500)
drops = np.zeros(len(rain))
for k in rng.uniform(0, b - a, int((b - a) * 7)):
    add(drops, bp(noise(0.02), 2000, 6000) * np.exp(-tt(0.02) * 200), k, rng.uniform(.2, .6))
add(amb, fade(rain * 0.05 + drops * 0.1, 1.0, 1.0), a, 1.0)
add(amb, lp(noise(3.0), 200, 3) * np.exp(-tt(3.0) * 1.5) * 1.5, a + 1.5, 0.25)  # trueno lejano
prog = [Am, F, C, G]
for j, k in enumerate(np.arange(a, idea, beat * 4)):
    ch = prog[j % 4]
    add(music, pad([n - 12 for n in ch], min(beat * 4.2, idea - k + .5), 1100), k, 0.14)
    for q, n in enumerate([ch[0], ch[2], ch[1] + 12, ch[2]]):
        if k + q * beat < idea: add(music, piano(n + 12, 2.5, 0.6), k + q * beat, 0.12)
# idea: cambia a mayor, esperanzador, y sube hacia el logo
prog2 = [F, C, G, Am]
for j, k in enumerate(np.arange(idea, b, beat * 2)):
    ch = prog2[j % 4]
    add(music, strings(ch, beat * 2.2, 2600), k, 0.16)
    for q in range(4): add(music, piano(ch[q % 3] + 12 + (12 if q == 3 else 0), 1.5, 0.7), k + q * beat / 2, 0.11)
lj = line("bedroom", -1)
add(music, riser(b - lj["start"] + 0.2), lj["start"], 0.35)

# ---- logo + plan: beat esperanzador
a, _ = span("logo"); _, b = span("plan")
prog = [F, C, G, Am]
for j, k in enumerate(np.arange(a, b, beat * 4)):
    ch = prog[j % 4]
    add(music, pad(ch, beat * 4.1, 2200), k, 0.15)
    add(music, sub808(ch[0] - 24 + (12 if ch[0] < 50 else 0), beat * 3.5), k, 0.30)
    for q in range(4):
        tq = k + q * beat
        if q in (0, 2) or (q == 3 and j % 2): add(music, kick(), tq, 0.55)
        if q in (1, 3): add(music, clap(), tq, 0.38)
        for h in range(4): add(music, hat(), tq + h * beat / 4, 0.16 if h % 2 else 0.25)
    arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24]
    for q in range(8): add(music, pluck(arp[q % 4], 0.5) * 0.6, k + q * beat / 2, 0.18)

# ---- cliffhanger: silencio, latido, golpe, y final épico en "Todavía"
a, b = span("cliff")
boom = sfx_times("cliff", "boom")[0]; last = sfx_times("cliff", "whoosh")[0]
add(music, heartbeat(boom - a, 66), a, 0.3)
add(music, fade(drone(38, last - boom + 0.3), 0.05, 0.4), boom, 0.22)
add(music, fade(strings([50, 53, 56], last - boom + 0.3, 900), 0.1, 0.4), boom, 0.2)
lt = line("cliff", -1)
add(music, strings([45, 52, 57, 61, 64], b - lt["start"] + 1.5, 3200), lt["start"], 0.45)
add(music, kick(0.6), lt["end"] + 0.05, 0.8); add(music, sub808(33, 2.5), lt["end"] + 0.05, 0.45)
for j, k in enumerate(np.arange(lt["end"] + 0.05, b + 1, 60 / 140)):
    if j % 2: add(music, clap(), k, 0.4)
    for h in range(2): add(music, hat(), k + h * 60 / 280, 0.2)

# ---- efectos puntuales
for e in TL["sfx"]:
    add(fx, sfx(e["name"]), e["t"], GAIN.get(e["name"], 0.5))

# ------------------------------------------------------------ voces con reverb por sala
ROOM = {"flash": ("big", .16), "freeze": ("room", .08), "rewind": ("room", .08), "kitchen": ("small", .12),
        "bedroom": ("room", .05), "logo": ("big", .10), "plan": ("room", .05), "cliff": ("hall", .14)}
voice = np.zeros(N)
for l in LN:
    a, _ = sf.read(sorted(__import__("glob").glob(f"{B}/lines/{l['i']:03d}_*.wav"))[0])
    a = hp(a, 80)
    a = a + 0.25 * hp(a, 4000)          # brillo y presencia
    # nivel común: RMS activo a -18 dBFS y compresión suave de picos
    act = a[np.abs(a) > 0.02 * np.abs(a).max()]
    a *= 10 ** (-18 / 20) / (np.sqrt(np.mean(act ** 2)) + 1e-9)
    a = np.tanh(a * 1.6) / 1.6
    kind, wet = ROOM.get(l["scene"], ("room", .06))
    rv = fftconvolve(a, REVERB[kind])[: len(a) + int(1.2 * SR)]
    out = np.zeros(len(rv)); out[:len(a)] = a
    add(voice, out + wet * rv * 2.2, l["start"])

# ------------------------------------------------------------ mezcla
venv = lp(np.abs(voice), 6, 1); venv /= (venv.max() or 1)
duck = 1 - 0.7 * np.clip(venv * 4, 0, 1)
bed = (music * duck * 0.85 + amb) * 0.45
fx *= 0.6 * (1 - 0.6 * np.clip(venv * 4, 0, 1))   # los efectos también ceden ante la voz
L = voice + bed + fx * 0.8
R = voice + bed + fx * 0.8
L += 0.08 * np.roll(music * duck, 480); R -= 0.08 * np.roll(music * duck, 480)
st = np.stack([L, R], 1)
st /= max(1e-6, np.abs(st).max()) / 0.9
sf.write(f"{B}/mix_raw.wav", st, SR)
import pyloudnorm as pyln
meter = pyln.Meter(SR)
lufs = meter.integrated_loudness(st)
g = 10 ** ((-14.0 - lufs) / 20)
for _ in range(4):  # el limitador baja algo el volumen: corregir hasta clavar -14 LUFS
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{B}/mix_raw.wav", "-af",
                    f"volume={g:.4f},alimiter=limit=0.89:attack=3:release=60:level=disabled", "-ar", str(SR),
                    f"{B}/mix.wav"], check=True)
    m2, _ = sf.read(f"{B}/mix.wav")
    got = meter.integrated_loudness(m2)
    if abs(got + 14.0) < 0.3: break
    g *= 10 ** ((-14.0 - got) / 20)
print(f"mix ok {N / SR:.1f}s  LUFS: {got:.1f}  pico: {np.abs(m2).max():.2f}")
# equilibrio voz / fondo por escena
for s_ in TL["scenes"]:
    i0, i1 = int(s_["start"] * SR), int((s_["start"] + s_["dur"]) * SR)
    mask = venv[i0:i1] > 0.08
    if mask.sum() < SR * 0.2: continue
    v = np.sqrt(np.mean(voice[i0:i1][mask] ** 2)) + 1e-9; bg = np.sqrt(np.mean((bed + fx * .8)[i0:i1][mask] ** 2)) + 1e-9
    print(f"  {s_['id']:8s} voz/fondo {20 * np.log10(v / bg):+5.1f} dB")
