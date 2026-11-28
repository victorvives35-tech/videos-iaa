# -*- coding: utf-8 -*-
"""Música cinematográfica original sintetizada + ambientes/efectos + mezcla con ducking."""
import json, os, wave
import numpy as np
from scipy import signal

WORK = os.environ["WORK"]
SR = 44100
rng = np.random.default_rng(11)
tl = json.load(open(os.path.join(WORK, "timeline.json")))
shots = json.load(open(os.path.join(WORK, "shots.json")))
ev_path = os.path.join(WORK, "events.json")
events = json.load(open(ev_path)) if os.path.exists(ev_path) else {}
D = tl["duration"]
N = int(D * SR) + SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_adsr(n, a, r, sus=1.0):
    e = np.ones(n) * sus
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    e[:na] = np.linspace(0, sus, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    j = min(len(buf), i + len(x))
    buf[max(0, i):j] += x[max(0, -i):j - i]


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


# ============================================================== MÚSICA
BPM = 96
BEAT = 60 / BPM
BAR = BEAT * 4
PROG_A = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]   # Am F C G
PROG_B = [(57, [57, 60, 64]), (50, [50, 53, 57]), (53, [53, 57, 60]), (52, [52, 56, 59])]   # Am Dm F E

sec_bounds = [(s["id"], s["start"], s["end"]) for s in tl["sections"]]


def section_at(t):
    for sid, a, b in sec_bounds:
        if a <= t < b:
            return sid
    return "outro"


def intensity(t):
    sid = section_at(t)
    if t < 2.2:
        return 0
    if sid == "intro":
        return 1 if t < 9 else 2
    if sid == "outro":
        return 1
    n = int(sid[1:])
    return 1 if n in (4, 12, 15, 19) else (3 if n in (6, 17, 18, 20) else 2)


pad = np.zeros(N); bass = np.zeros(N); arp = np.zeros(N); drums = np.zeros(N)
chord_len = BAR * 2
nch = int(D / chord_len) + 2
for c in range(nch):
    t0 = c * chord_len
    prog = PROG_A if (c // 8) % 2 == 0 else PROG_B
    root, notes = prog[c % 4]
    n = int((chord_len + 1.2) * SR)
    tt = np.arange(n) / SR
    e = env_adsr(n, 0.9, 1.4)
    x = np.zeros(n)
    for nt in notes + [notes[0] + 12, notes[1] - 12]:
        f = midi(nt)
        for det in (0.9985, 1.0015):
            for h in range(1, 7):
                x += np.sin(2 * np.pi * f * det * h * tt + h * 0.7) / h ** 1.3
    vib = 1 + 0.15 * np.sin(2 * np.pi * 0.2 * tt)
    add(pad, x * e * vib * 0.012, t0)
    # bajo en corcheas
    for k in range(16):
        tb = t0 + k * BEAT / 2
        if intensity(tb) < 2:
            continue
        nb = int(BEAT / 2 * SR)
        tq = np.arange(nb) / SR
        f = midi(root - 24)
        b = (np.sin(2 * np.pi * f * tq) + 0.35 * np.sin(4 * np.pi * f * tq)) * np.exp(-tq * 5)
        add(bass, b * 0.16 * env_adsr(nb, 0.005, 0.03), tb)
    # arpegio en semicorcheas
    seq = [notes[0], notes[1], notes[2], notes[0] + 12, notes[2], notes[1], notes[0] + 12, notes[2] + 12]
    for k in range(32):
        ta = t0 + k * BEAT / 4
        if intensity(ta) < 1:
            continue
        na = int(0.35 * SR)
        tq = np.arange(na) / SR
        f = midi(seq[k % 8] + 12)
        a = (np.sin(2 * np.pi * f * tq) + 0.3 * np.sin(6 * np.pi * f * tq)) * np.exp(-tq * 11)
        add(arp, a * 0.05 * (1.0 if k % 4 == 0 else 0.7), ta)

# batería
kick_n = int(0.4 * SR); tq = np.arange(kick_n) / SR
kick = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-tq * 30)) / SR) * np.exp(-tq * 8)
sn_n = int(0.25 * SR); tq2 = np.arange(sn_n) / SR
snare = bp(rng.standard_normal(sn_n), 900, 6000) * np.exp(-tq2 * 18) * 0.5 + np.sin(2 * np.pi * 190 * tq2) * np.exp(-tq2 * 25) * 0.4
hat_n = int(0.06 * SR)
hat = hp(rng.standard_normal(hat_n), 7000) * np.exp(-np.arange(hat_n) / SR * 70) * 0.25
nbeats = int(D / BEAT) + 1
for k in range(nbeats):
    tb = k * BEAT
    it = intensity(tb)
    if it >= 2:
        if k % 2 == 0: add(drums, kick * 0.5, tb)
        if it >= 3 and k % 2 == 1: add(drums, snare * 0.35, tb)
        add(drums, hat * (0.5 if it >= 3 else 0.3), tb + BEAT / 2)
        if it >= 3: add(drums, hat * 0.25, tb)

# pump de sidechain al ritmo
pump = np.ones(N)
pl = int(BEAT * SR)
shape = 1 - 0.45 * np.exp(-np.arange(pl) / SR * 9)
for k in range(nbeats):
    i = int(k * BEAT * SR)
    if intensity(k * BEAT) >= 2:
        j = min(N, i + pl); pump[i:j] = shape[:j - i]

# reverb (IR de ruido exponencial)
irn = int(2.4 * SR)
ir = rng.standard_normal(irn) * np.exp(-np.arange(irn) / SR * 2.6)
ir = lp(ir, 5000)
ir /= np.sqrt(np.sum(ir ** 2))
wet_in = pad * 0.6 + arp
revL = signal.oaconvolve(wet_in, ir)[:N]
revR = signal.oaconvolve(wet_in, np.roll(ir, 331))[:N]
# delay estéreo del arpegio
dl = int(BEAT * 0.75 * SR)
arpL = arp.copy(); arpR = arp.copy()
arpR[dl:] += arp[:-dl] * 0.45; arpL[2 * dl:] += arp[:-2 * dl] * 0.3
musL = pad * 1.0 + bass * pump + arpL * pump + drums + revL * 0.35
musR = pad * 1.0 + bass * pump + arpR * pump + drums + revR * 0.35
# fades
fade_out = int(6 * SR)
for m in (musL, musR):
    m[:int(0.8 * SR)] *= np.linspace(0, 1, int(0.8 * SR))
    end = int(D * SR)
    m[end - fade_out:end] *= np.linspace(1, 0, fade_out)
    m[end:] = 0
music = np.stack([musL, musR], 1)
music /= np.max(np.abs(music)) + 1e-9

# ============================================================== EFECTOS Y AMBIENTES
sfx = np.zeros((N, 2))


def noise(n):
    return rng.standard_normal(n)


def place(x, t, gain=1.0, pan=0.0, fade=0.25):
    if x.ndim == 1:
        x = np.stack([x * (1 - max(0, pan)), x * (1 + min(0, pan))], 1)
    n = len(x)
    fn = min(n // 2, int(fade * SR))
    if fn:
        f = np.linspace(0, 1, fn)[:, None]
        x = x.copy(); x[:fn] *= f; x[-fn:] *= f[::-1]
    i = int(t * SR)
    j = min(N, i + n)
    if j > i >= 0:
        sfx[i:j] += x[:j - i] * gain


def amb(kind, n, t0):
    tt = np.arange(n) / SR + t0
    if kind == "waves":
        x = lp(noise(n), 700) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * tt) ** 2) * 1.6
        return x + hp(noise(n), 3000) * 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * tt - 1))
    if kind == "rain":
        return bp(noise(n), 1200, 9000) * 0.35 + lp(noise(n), 400) * 0.4
    if kind == "storm":
        return bp(noise(n), 1000, 9000) * 0.5 + lp(noise(n), 300) * (0.8 + 0.6 * np.sin(2 * np.pi * 0.2 * tt)) * 1.2
    if kind == "city":
        x = lp(noise(n), 350) * 0.9 + bp(noise(n), 400, 2000) * 0.05
        if rng.random() < 0.5:
            hn = int(0.35 * SR); th = np.arange(hn) / SR
            horn = (np.sign(np.sin(2 * np.pi * 392 * th)) + np.sign(np.sin(2 * np.pi * 330 * th))) * 0.03
            k = int(rng.uniform(0.2, 0.6) * n)
            x[k:k + hn] += lp(horn, 2000)[:len(x[k:k + hn])]
        return x
    if kind == "road":
        f = 70 + 10 * np.sin(2 * np.pi * 0.3 * tt)
        eng = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.08
        return lp(noise(n), 250) * 0.9 + lp(eng, 400)
    if kind == "siren":
        f = 900 + 350 * np.sin(2 * np.pi * 0.35 * tt)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.07
        rotor = lp(noise(n), 400) * (0.5 + 0.5 * (np.sin(2 * np.pi * 15 * tt) > 0.6)) * 0.4
        return s + rotor + lp(noise(n), 250) * 0.6
    if kind == "club":
        x = bp(noise(n), 300, 1500) * 0.15 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.5 * tt))
        bt = 60 / 124
        for k in range(int(n / SR / bt) + 1):
            i = int(k * bt * SR)
            m = min(n - i, len(kick))
            if m > 0: x[i:i + m] += lp(kick[:m], 150) * 0.8
        return x
    if kind == "swamp":
        cr = np.sin(2 * np.pi * 4800 * tt) * (np.sin(2 * np.pi * 28 * tt) > 0.3) * (np.sin(2 * np.pi * 0.9 * tt) > 0) * 0.03
        fr = np.sin(2 * np.pi * 140 * tt) * (np.sin(2 * np.pi * 1.3 * tt) > 0.9) * 0.12
        return cr + lp(fr, 600) + lp(noise(n), 300) * 0.2
    if kind == "nature":
        x = bp(noise(n), 200, 1200) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * tt))
        for _ in range(int(n / SR * 1.5)):
            bn = int(0.12 * SR); tb = np.arange(bn) / SR
            ch = np.sin(2 * np.pi * np.cumsum(3500 + 1500 * np.sin(2 * np.pi * 18 * tb)) / SR) * np.hanning(bn) * 0.04
            k = int(rng.uniform(0, max(1, n - bn)))
            x[k:k + bn] += ch
        return x
    if kind == "ui":
        x = lp(noise(n), 120) * 0.3 + np.sin(2 * np.pi * 55 * tt) * 0.04
        for k in range(int(n / SR / 0.8)):
            bn = int(0.07 * SR); tb = np.arange(bn) / SR
            i = int(k * 0.8 * SR + 0.1 * SR)
            if i + bn < n:
                x[i:i + bn] += np.sin(2 * np.pi * 1700 * tb) * np.exp(-tb * 40) * 0.05
        return x
    return np.zeros(n)


AMB = {"beach": "waves", "ocean": "waves", "bridge": "waves", "rainstreet": "rain", "storm": "storm", "skyline": "city",
       "aerial": "city", "shops": "city", "duo": "city", "highway": "road", "car": "road", "police": "siren",
       "policeheli": "siren", "club": "club", "swamp": "swamp", "mountains": "nature", "map": "ui"}
for sh in shots:
    n = int((sh["dur"] + 0.3) * SR)
    x = amb(AMB[sh["scene"]], n, sh["start"])
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.05
    place(x, sh["start"] - 0.1, 1.0, float(rng.uniform(-0.3, 0.3)), 0.15)
    if sh["scene"] in ("car", "highway") and rng.random() < 0.5:
        pn = int(1.2 * SR); tp = np.arange(pn) / SR
        pb = lp(noise(pn), 900) * np.exp(-((tp - 0.6) / 0.25) ** 2) * 0.25
        place(np.stack([pb * np.linspace(1, 0.2, pn), pb * np.linspace(0.2, 1, pn)], 1), sh["start"] + rng.uniform(0.2, 1.5), 1.0)

# truenos
for lst in events.values():
    for name, t in lst:
        n = int(3.0 * SR); tt = np.arange(n) / SR
        th = lp(noise(n), 160, 4) * np.exp(-tt * 1.4) * 3 + hp(noise(n), 2000) * np.exp(-tt * 25) * 0.4
        place(th / np.max(np.abs(th)) * 0.35, t, 1.0, 0.0, 0.01)

# whoosh + impacto en cada detalle
for s in tl["sections"][1:]:
    t = s["start"]
    n = int(0.9 * SR)
    x = noise(n)
    parts = []
    k = 8
    for i in range(k):
        seg = x[i * n // k:(i + 1) * n // k]
        f = 300 * (12 ** (i / (k - 1)))
        parts.append(bp(seg, f * 0.7, min(f * 1.6, 18000)))
    w = np.concatenate(parts) * np.hanning(n)
    place(w / np.max(np.abs(w)) * 0.22, t - 1.05, 1.0, 0.0, 0.05)
    bn = int(1.6 * SR); tb = np.arange(bn) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-tb * 12)) / SR) * np.exp(-tb * 3.2) + lp(noise(bn), 200) * np.exp(-tb * 9) * 0.5
    place(boom / np.max(np.abs(boom)) * 0.30, t - 0.12, 1.0, 0.0, 0.005)

# "tick" al aparecer cada etiqueta de confirmado/teoría
for s in tl["sections"]:
    for f in s["frases"]:
        if f["tag"]:
            n = int(0.12 * SR); tq = np.arange(n) / SR
            fr = 1320 if f["tag"] == "C" else 880
            tk = (np.sin(2 * np.pi * fr * tq) + np.sin(2 * np.pi * fr * 1.5 * tq) * 0.5) * np.exp(-tq * 35)
            place(tk * 0.05, f["start"] + 0.05, 1.0, 0.3, 0.003)

# ============================================================== VOZ Y MEZCLA
with wave.open(os.path.join(WORK, "narracion.wav")) as w:
    vsr = w.getframerate()
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
v = signal.resample_poly(v, SR, vsr)
v = hp(v, 70)
# ligera compresión y "presencia"
v = v + 0.25 * bp(v, 2500, 6000)
v = v / (np.percentile(np.abs(v), 99.5) + 1e-9) * 0.55
voice = np.zeros(N); voice[:min(N, len(v))] = v[:N]

# envolvente de voz para el ducking
win = int(0.05 * SR)
rms = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
act = (rms > 0.02).astype(float)
# ataque rápido / liberación lenta
duck = np.zeros(N)
a_, r_ = 1 - np.exp(-1 / (0.06 * SR)), 1 - np.exp(-1 / (0.5 * SR))
d_ = 0.0
step = 256
for i in range(0, N, step):
    tgt = act[i]
    d_ += (tgt - d_) * (1 - (1 - (a_ if tgt > d_ else r_)) ** step)
    duck[i:i + step] = d_
mus_gain = (0.30 - 0.21 * duck)[:, None]    # ~ -10 dB sin voz, ~ -21 dB bajo la voz
sfx_gain = (1.0 - 0.45 * duck)[:, None]
mix = music * mus_gain + sfx * sfx_gain + np.stack([voice, voice], 1)
mix /= max(1.0, np.max(np.abs(mix)) / 0.97)
pcm = (mix[:int(D * SR)] * 32767).astype(np.int16)
with wave.open(os.path.join(WORK, "mezcla.wav"), "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("mezcla.wav lista", D)
