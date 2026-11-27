"""Banda sonora cinematográfica sintetizada, sincronizada con timeline.json."""
import json, sys
import numpy as np
from pathlib import Path
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile

OUT = Path(sys.argv[1])
TL = json.load(open(OUT / "timeline.json"))
SR = 48000
N = int(TL["total"] * SR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)

# ---------- curva de intensidad por capítulo ----------
chap_starts = [it["start"] for it in TL["items"] if it["kind"] == "chapter"]
def intensity(sec):
    # 0.35 al inicio -> 1.0 en el epílogo
    idx = sum(1 for c in chap_starts if c <= sec)
    return [0.35, 0.45, 0.55, 0.62, 0.75, 0.82, 0.78, 1.0][min(idx, 7)]
inten = np.array([intensity(s) for s in np.arange(0, TL["total"] + 1, 1.0)])
inten = np.interp(t_all, np.arange(len(inten)), inten)
inten = lp(inten, 0.08, 1)   # transiciones suaves

# ---------- pad de acordes ----------
# D menor: i - VI - III - VII  /  i - iv - VI - V
prog = [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64],
        [50, 57, 62, 65], [55, 58, 62, 67], [46, 53, 58, 65], [45, 52, 57, 61]]
CH = 8.0
pad = np.zeros((N, 2))
n_ch = int(np.ceil(TL["total"] / CH)) + 1
for k in range(n_ch):
    s0 = int((k * CH - 1.5) * SR); L = int((CH + 3.0) * SR)
    s0c = max(0, s0); e = min(N, s0 + L)
    if e <= s0c: continue
    tt = (np.arange(s0c, e) - s0) / SR
    env = np.clip(tt / 2.5, 0, 1) * np.clip((CH + 3.0 - tt) / 2.5, 0, 1)
    env = env ** 1.5
    for ch_i, side in enumerate((-1, 1)):
        sig = np.zeros(e - s0c)
        for m in prog[k % len(prog)]:
            f0 = hz(m)
            for h, a in ((1, 1.0), (2, 0.35), (3, 0.15), (4, 0.06)):
                det = 1 + side * 0.0025 * h
                sig += a * np.sin(2 * np.pi * f0 * h * det * tt + rng.uniform(0, 6.28))
        pad[s0c:e, ch_i] += sig * env
pad = np.stack([lp(pad[:, 0], 1400), lp(pad[:, 1], 1400)], 1)
pad *= 0.018

# ---------- sub drone ----------
drone = (np.sin(2 * np.pi * hz(26) * t_all) + 0.5 * np.sin(2 * np.pi * hz(38) * t_all))
drone *= 0.08 * (0.7 + 0.3 * np.sin(2 * np.pi * t_all / 13))

# ---------- piano (notas sueltas) ----------
scale = [62, 65, 67, 69, 72, 74, 77, 81]
piano = np.zeros((N, 2))
def piano_note(m, dur=4.5, vel=1.0):
    tt = np.arange(int(dur * SR)) / SR
    f0 = hz(m); s = np.zeros_like(tt)
    for h, a, dcy in ((1, 1, 1.6), (2, .45, 2.4), (3, .2, 3.5), (4, .1, 5), (5, .05, 7)):
        s += a * np.sin(2 * np.pi * f0 * h * (1 + 0.0004 * h * h) * tt) * np.exp(-dcy * tt)
    s *= np.clip(tt / 0.004, 0, 1)
    return s * vel
t = 3.0
while t < TL["total"] - 6:
    m = scale[rng.integers(len(scale))]
    v = 0.5 + 0.5 * rng.random()
    s = piano_note(m, vel=v); i0 = int(t * SR); e = min(N, i0 + len(s))
    pan = rng.uniform(0.3, 0.7)
    piano[i0:e, 0] += s[:e - i0] * (1 - pan); piano[i0:e, 1] += s[:e - i0] * pan
    if rng.random() < 0.35:   # a veces una segunda nota (intervalo)
        s2 = piano_note(m - 5, vel=v * 0.6); e2 = min(N, i0 + len(s2))
        piano[i0:e2] += (s2[:e2 - i0] * 0.5)[:, None]
    t += rng.choice([1.0, 2.0, 2.0, 3.0, 4.0])
piano *= 0.05

# ---------- percusión épica (capítulo IV en adelante) ----------
perc = np.zeros(N)
def tom(dur=1.2):
    tt = np.arange(int(dur * SR)) / SR
    f = 55 * np.exp(-tt * 3) + 38
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4.5)
    click = lp(rng.standard_normal(len(tt)), 900) * np.exp(-tt * 40) * 0.4
    return body + click
TOM = tom()
if len(chap_starts) >= 4:
    bpm = 68; beat = 60 / bpm
    pattern = [1, 0, 0, 0.5, 1, 0, 0.6, 0]   # en corcheas
    t = chap_starts[3]
    while t < TL["total"] - 8:
        for j, a in enumerate(pattern):
            tt = t + j * beat / 2
            if a and tt < TL["total"] - 8:
                i0 = int(tt * SR); e = min(N, i0 + len(TOM))
                perc[i0:e] += TOM[:e - i0] * a
        t += 4 * beat
perc *= 0.20 * np.clip((inten - 0.6) / 0.4, 0, 1)

# ---------- impactos y whooshes ----------
fx = np.zeros((N, 2))
def braam(dur=5.0):
    tt = np.arange(int(dur * SR)) / SR
    env = np.clip(tt / 0.03, 0, 1) * np.exp(-tt * 0.9)
    s = np.zeros_like(tt)
    for m in (26, 38, 45, 50):
        for d in (0.997, 1.0, 1.003):
            s += np.sign(np.sin(2 * np.pi * hz(m) * d * tt)) * 0.3   # cuadrada = metálico
    s = lp(s, 500, 4) + 1.2 * np.sin(2 * np.pi * 36 * tt) * np.exp(-tt * 2)
    return s * env
def whoosh(dur=1.6):
    n = int(dur * SR); tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    env = np.sin(np.pi * tt / dur) ** 3
    return hp(lp(noise, 2500), 200) * env * np.linspace(0.3, 1, n)
BR, WH = braam(), whoosh()
def add(buf, sig, sec, g):
    i0 = int(sec * SR)
    if i0 < 0: sig = sig[-i0:]; i0 = 0
    e = min(N, i0 + len(sig))
    buf[i0:e] += (sig[:e - i0] * g)[:, None] if buf.ndim == 2 else sig[:e - i0] * g
for it in TL["items"]:
    if it["kind"] == "chapter":
        add(fx, WH, it["start"] - 1.3, 0.10)
        add(fx, BR, it["start"] + 0.25, 0.10)
    elif it["kind"] == "title":
        add(fx, WH, it["start"] - 1.3, 0.12)
        add(fx, BR, it["start"] + 0.2, 0.14)
    elif it["kind"] == "line" and it["bg"] == "void" and len(it["onscreen"]) < 16:
        add(fx, BR[: int(2.5 * SR)] * np.linspace(1, 0, int(2.5 * SR)), it["start"], 0.05)

# ---------- mezcla + reverb ----------
dry = pad * (0.6 + 0.6 * inten[:, None]) + drone[:, None] + piano
ir_n = int(3.2 * SR); tt = np.arange(ir_n) / SR
ir = np.stack([rng.standard_normal(ir_n), rng.standard_normal(ir_n)], 1) * np.exp(-tt * 2.2)[:, None]
ir[:, 0] = lp(ir[:, 0], 6000); ir[:, 1] = lp(ir[:, 1], 6000)
ir /= np.sqrt((ir ** 2).sum(0))
wet = np.stack([fftconvolve(dry[:, c] + fx[:, c] * 0.5, ir[:, c])[:N] for c in range(2)], 1)
mix = 0.55 * dry + 0.75 * wet + fx + perc[:, None]
# fade in / out
fade = np.ones(N); fi = int(4 * SR); fo = int(6 * SR)
fade[:fi] = np.linspace(0, 1, fi) ** 2; fade[-fo:] = np.linspace(1, 0, fo) ** 2
mix *= fade[:, None]
mix = np.tanh(mix * 1.4) / 1.4
mix /= np.abs(mix).max() / 0.89
wavfile.write(OUT / "musica.wav", SR, (mix * 32767).astype(np.int16))
print("música lista", mix.shape[0] / SR, "s")
