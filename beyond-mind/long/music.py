"""10-minute procedural cinematic score following the chapter structure in build/timeline.json."""
import json, numpy as np, soundfile as sf
from scipy.signal import oaconvolve, butter, sosfilt

SR = 44100
TL = json.load(open('build/timeline.json'))
DUR = TL['total']; N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
BPM = 90; BEAT = 60 / BPM; BAR = 4 * BEAT


def hz(n): return 440 * 2 ** ((n - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, min(f, SR * 0.45), 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)


def add(sig, start, pan=0.0, gain=1.0):
    k = int(start * SR)
    if k >= N: return
    if k < 0: sig = sig[-k:]; k = 0
    sig = sig[:N - k].astype(np.float32) * gain
    L[k:k + len(sig)] += sig * np.float32(np.sqrt(0.5 * (1 - pan)))
    R[k:k + len(sig)] += sig * np.float32(np.sqrt(0.5 * (1 + pan)))


def env(n, a, r):
    e = np.ones(n); na, nr = min(n, max(1, int(a * SR))), min(n, max(1, int(r * SR)))
    e[:na] = np.linspace(0, 1, na) ** 2; e[-nr:] *= np.linspace(1, 0, nr) ** 2; return e


def saw(f, n, det=0.0):
    tt = np.arange(n) / SR; return 2 * ((f * (1 + det) * tt + rng.random()) % 1) - 1


# ---------- instruments ----------
def pad(notes, length, cutoff, gain):
    n = int(length * SR); s = np.zeros(n)
    for nt in notes:
        for d in (-0.004, 0, 0.0045): s += saw(hz(nt), n, d)
    return lp(s, cutoff) * env(n, min(1.2, length / 3), min(1.5, length / 3)) * gain


def piano(nt, length=2.5, vel=1.0):
    n = int(length * SR); tt = np.arange(n) / SR; f = hz(nt); s = np.zeros(n)
    for h, a in ((1, 1), (2, 0.45), (3, 0.2), (4, 0.12), (5, 0.06)):
        s += a * np.sin(2 * np.pi * f * h * np.sqrt(1 + 0.0004 * h * h) * tt) * np.exp(-tt * (1.2 + 0.9 * h))
    s *= np.minimum(1, tt / 0.004)
    return s * vel


def pluck(nt, length=0.25, bright=2500):
    n = int(length * SR); tt = np.arange(n) / SR
    s = (saw(hz(nt), n) + saw(hz(nt), n, 0.003)) * np.exp(-tt * 13)
    return lp(s, bright)


def brass(notes, length, gain):
    n = int(length * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for nt in notes:
        for d in (-0.003, 0.003): s += saw(hz(nt), n, d)
    cut = 300 + 1500 * np.minimum(1, tt / 0.25) * np.exp(-tt * 0.8)
    out = np.zeros(n); seg = 1024
    for i in range(0, n, seg): out[i:i + seg] = lp(s[i:i + seg], cut[i])
    return np.tanh(out * 0.8) * env(n, 0.05, 0.6) * gain


def kick(g=1.0):
    n = int(0.5 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9) * g


def tom(f=90, g=1.0):
    n = int(0.6 * SR); tt = np.arange(n) / SR
    b = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-tt * 25))) / SR) * np.exp(-tt * 7)
    return (b + 0.3 * lp(rng.standard_normal(n), 1500) * np.exp(-tt * 20)) * g


def snare(g=1.0):
    n = int(0.35 * SR); tt = np.arange(n) / SR
    return (hp(rng.standard_normal(n), 1200) * np.exp(-tt * 14) + 0.5 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25)) * g


def tick(g=1.0):
    n = int(0.05 * SR); tt = np.arange(n) / SR
    return hp(rng.standard_normal(n), 4000) * np.exp(-tt * 120) * g


def boom(size=1.0):
    n = int(4 * SR); tt = np.arange(n) / SR
    f = 30 + 70 * np.exp(-tt * 12)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * (1.6 / size))
    return np.tanh(1.6 * body) + 0.35 * lp(rng.standard_normal(n), 3000) * np.exp(-tt * 9) + 0.15 * hp(rng.standard_normal(n), 2000) * np.exp(-tt * 35)


def riser(length):
    n = int(length * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = 2048
    for i in range(0, n, seg): out[i:i + seg] = lp(x[i:i + seg], 300 + 7000 * (i / n) ** 2, 1)
    return out * (np.arange(n) / n) ** 2


def whoosh(length=0.7):
    n = int(length * SR); tt = np.arange(n) / SR
    return lp(hp(rng.standard_normal(n), 400), 3500) * np.sin(np.pi * tt / length) ** 3


# ---------- structure ----------
PROG = {  # chord roots/voicings per chapter (D minor world)
    'HOOK': [[38, 50, 57, 62, 65]],
    'TITLE': [[38, 50, 57, 62, 65, 69]],
    'I': [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64]],
    'II': [[50, 57, 62, 65], [50, 57, 62, 65], [46, 53, 58, 62], [45, 52, 57, 61]],
    'III': [[46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64], [50, 57, 62, 65]],
    'IV': [[53, 57, 60, 65], [48, 55, 60, 64], [50, 57, 62, 65], [46, 53, 58, 62]],
    'V': [[50, 57, 62, 65], [51, 58, 63, 66], [50, 57, 62, 65], [45, 52, 57, 61]],
    'VI': [[46, 53, 58, 62], [48, 55, 60, 64], [50, 57, 62, 65], [45, 52, 57, 61]],
    'VII': [[46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64], [50, 57, 62, 65]],
}
cards = [i for i in TL['items'] if i['type'] == 'card']
sections = [('HOOK', 0.0, cards[0]['start'])]
for k, c in enumerate(cards):
    name = 'TITLE' if c['kind'] == '@' else c['a']
    sections.append((name + '_CARD', c['start'], c['end']))
    nxt = cards[k + 1]['start'] if k + 1 < len(cards) else DUR
    sections.append((name, c['end'], nxt))
print([(s[0], round(s[1], 1), round(s[2], 1)) for s in sections])
LAST_LINE = [i for i in TL['items'] if i['type'] == 'line'][-1]['start']
END_HIT = LAST_LINE - 1.2

for name, st, en in sections:
    if name.endswith('_CARD'):
        add(boom(1.6), st, gain=0.5)
        add(pad(PROG.get(name[:-5], PROG['TITLE'])[0] + [74], en - st + 1.5, 1800, 0.018), st)
        continue
    prog = PROG[name]; ln = en - st
    x = st; bi = 0
    while x < en - 0.05:
        bl = min(BAR * 2, en - x)
        prog_pos = (x - st) / max(ln, 1)
        inten = 0.3 + 0.7 * prog_pos ** 1.3  # each chapter builds
        if name == 'VII' and x > END_HIT - 30: inten = 1.0
        chord = prog[bi % len(prog)]
        cut = 700 + 2600 * inten
        if name == 'VII' and x >= END_HIT: break
        add(pad(chord, bl + 1.0, cut, 0.016 + 0.006 * inten), x - 0.2)
        add(np.sin(2 * np.pi * hz(chord[0] - 24) * np.arange(int(bl * SR)) / SR) * env(int(bl * SR), 0.3, 0.3) * 0.09 * inten, x)
        nb = int(bl / BEAT + 0.5)
        for b in range(nb):
            tb = x + b * BEAT
            if tb >= en - 0.05: break
            if name in ('HOOK', 'V') and b % 2 == 0: add(kick(0.45), tb); add(kick(0.25), tb + 0.22)
            if name in ('I',):
                add(tick(0.12), tb); add(tick(0.06), tb + BEAT / 2)
                if b % 2 == 0: add(piano(chord[(b // 2) % len(chord)] + 12, 3, 0.10), tb, pan=0.2)
            if name in ('III', 'VII'):
                for s8 in range(2):
                    nt = chord[(b * 2 + s8) % len(chord)] + 12
                    add(piano(nt, 2.5, 0.07 + 0.03 * inten), tb + s8 * BEAT / 2, pan=-0.3 + 0.6 * ((b * 2 + s8) % 4) / 3)
            if name in ('II', 'IV', 'VI', 'VII') and inten > 0.35:
                for s16 in range(4):
                    pat = [0, 0, 12, 0, 7, 0, 12, 7]
                    nt = chord[0] - 12 + pat[(b * 4 + s16) % 8]
                    add(pluck(nt, 0.22, 1200 + 2500 * inten), tb + s16 * BEAT / 4, pan=0.3 * np.sin(b * 4 + s16), gain=0.05 * (0.5 + 0.7 * inten))
            if name == 'V' and b % 4 == 0 and inten > 0.3:
                add(brass([chord[0] - 12, chord[0] - 5], BEAT * 1.5, 0.05 + 0.04 * inten), tb)
            if name in ('II', 'IV', 'VI', 'VII') and inten > 0.55:
                if b % 4 == 0: add(tom(70, 0.7 * inten), tb)
                add(tom(110, 0.3 * inten), tb + BEAT / 2, pan=-0.3)
                if inten > 0.75 and b % 2 == 1: add(snare(0.35 * inten), tb, pan=0.2)
            if name in ('III',) and inten > 0.5 and b % 2 == 0: add(kick(0.4 * inten), tb)
        x += bl; bi += 1
    # riser into next card
    if en - st > 8 and name != 'VII': add(riser(3.0), en - 3.0, gain=0.25)

# final climax + end hit
add(riser(3.5), END_HIT - 3.5, gain=0.35)
add(boom(2.0), END_HIT, gain=0.7)
add(pad([38, 50, 57, 62, 65, 69, 74], DUR - END_HIT, 2200, 0.02), END_HIT)
n = int((DUR - END_HIT) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
for nt in (74, 77, 81): s += np.sin(2 * np.pi * hz(nt) * tt * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * tt)))
add(s * env(n, 1.0, 3.0) * 0.02, END_HIT)
# hook opening hit + heartbeat
add(boom(1.0), 0.0, gain=0.55)
# soft whooshes on some scene cuts are added in the mix step (not needed here)

# ---------- reverb + master ----------
irn = int(2.8 * SR); it = np.arange(irn) / SR
irL = (lp(rng.standard_normal(irn) * np.exp(-it * 2.4), 5000) / 30).astype(np.float32)
irR = (lp(rng.standard_normal(irn) * np.exp(-it * 2.4), 5000) / 30).astype(np.float32)
wL = oaconvolve(L, irL)[:N]; wR = oaconvolve(R, irR)[:N]
t = np.arange(N, dtype=np.float32) / SR
fade = np.clip((DUR - t) / 2.5, 0, 1) * np.clip(t / 0.02, 0, 1)
m = np.stack([(L * 0.8 + wL * 0.6) * fade, (R * 0.8 + wR * 0.6) * fade], 1)
m /= np.abs(m).max() * 1.05
m = np.tanh(m * 1.4) / np.tanh(1.4)
sf.write('build/music.wav', m.astype(np.float32), SR)
print('music ok', round(DUR, 1), 's')
