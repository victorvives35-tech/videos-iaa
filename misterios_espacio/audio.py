# -*- coding: utf-8 -*-
"""Banda sonora original: ambiente cósmico misterioso + efectos discretos + mezcla con la voz (ducking)."""
import json, os, wave
import numpy as np
from scipy import signal

WORK = os.environ["WORK"]
SR = 44100
rng = np.random.default_rng(21)
tl = json.load(open(os.path.join(WORK, "timeline.json")))
plan = json.load(open(os.path.join(WORK, "plan.json")))
D = tl["duration"]; N = int(D * SR) + SR
tt = np.arange(N) / SR


def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "lowpass", fs=SR, output="sos"), x)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "highpass", fs=SR, output="sos"), x)
def bp(x, a, b, o=2): return signal.sosfilt(signal.butter(o, [a, b], "bandpass", fs=SR, output="sos"), x)
def midi(n): return 440 * 2 ** ((n - 69) / 12)


def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(x)); buf[max(0, i):j] += x[max(0, -i):j - i]


# ---------------- pads lentos (progresión menor misteriosa)
PROG = [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [43, 50, 55, 59, 62], [40, 47, 52, 56, 59],
        [45, 52, 57, 60, 63], [38, 45, 50, 53, 57], [41, 48, 53, 56, 60], [40, 47, 52, 55, 59]]
CL = 8.0
L = np.zeros(N); R = np.zeros(N)
for c in range(int(D / CL) + 2):
    notes = PROG[c % len(PROG)]
    n = int((CL + 4) * SR); t = np.arange(n) / SR
    env = np.minimum(1, t / 3.0) * np.minimum(1, np.maximum(0, (CL + 4 - t) / 4.0))
    xl = np.zeros(n); xr = np.zeros(n)
    for k, nt in enumerate(notes):
        f = midi(nt)
        for h, amp in ((1, 1), (2, 0.35), (3, 0.15), (4, 0.06)):
            ph = rng.uniform(0, 6)
            xl += amp * np.sin(2 * np.pi * f * h * 0.9992 * t + ph)
            xr += amp * np.sin(2 * np.pi * f * h * 1.0008 * t + ph + 0.4)
    add(L, xl * env * 0.010, c * CL); add(R, xr * env * 0.010, c * CL)
# drone grave
drone = np.sin(2 * np.pi * 55 * tt) * 0.05 + np.sin(2 * np.pi * 82.4 * tt + np.sin(tt * 0.2)) * 0.025
drone += lp(rng.standard_normal(N), 90) * 0.15
L += drone; R += drone
# campanillas brillantes ocasionales
for k in range(int(D / 3.3)):
    t0 = k * 3.3 + rng.uniform(0, 1.5)
    nt = rng.choice([69, 72, 76, 79, 81, 84])
    n = int(4 * SR); t = np.arange(n) / SR
    b = (np.sin(2 * np.pi * midi(nt) * t) + 0.4 * np.sin(2 * np.pi * midi(nt) * 2.76 * t)) * np.exp(-t * 1.3) * 0.012
    pan = rng.uniform(-0.8, 0.8)
    add(L, b * (1 - pan) / 1.5, t0); add(R, b * (1 + pan) / 1.5, t0)
# pulso suave en los misterios (latido lento)
for s in tl["sections"]:
    if s["id"] in ("intro", "outro"): continue
    for t0 in np.arange(s["start"], s["end"] - 1, 60 / 64):
        n = int(0.5 * SR); t = np.arange(n) / SR
        k = np.sin(2 * np.pi * np.cumsum(38 + 40 * np.exp(-t * 20)) / SR) * np.exp(-t * 7) * 0.06
        add(L, k, t0); add(R, k, t0)
# reverberación
irn = int(4 * SR)
ir = rng.standard_normal(irn) * np.exp(-np.arange(irn) / SR * 1.3); ir = lp(ir, 4000); ir /= np.sqrt((ir ** 2).sum())
L = L + signal.oaconvolve(L, ir)[:N] * 0.5
R = R + signal.oaconvolve(R, np.roll(ir, 777))[:N] * 0.5
mus = np.stack([L, R], 1)
mus /= np.max(np.abs(mus)) + 1e-9
fi = int(3 * SR); mus[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(8 * SR); e = int(D * SR); mus[e - fo:e] *= np.linspace(1, 0, fo)[:, None]

# ---------------- efectos
sfx = np.zeros((N, 2))
def place(x, t, g=1.0):
    if x.ndim == 1: x = np.stack([x, x], 1)
    i = int(t * SR); j = min(N, i + len(x))
    if 0 <= i < N: sfx[i:j] += x[:j - i] * g
for s in tl["sections"][1:]:
    t = s["start"]
    n = int(1.6 * SR); x = rng.standard_normal(n)
    parts = [bp(x[i * n // 10:(i + 1) * n // 10], 200 * 1.4 ** i, min(200 * 1.4 ** i * 2, 18000)) for i in range(10)]
    wsh = np.concatenate(parts) * np.hanning(n); place(wsh / np.max(np.abs(wsh)) * 0.12, t - 1.9)
    n = int(3.5 * SR); u = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(32 + 50 * np.exp(-u * 6)) / SR) * np.exp(-u * 1.2) + lp(rng.standard_normal(n), 120) * np.exp(-u * 2) * 0.6
    place(boom / np.max(np.abs(boom)) * 0.22, t - 0.35)
# sonidos temáticos según el plano
for sec in plan:
    for sh in sec["shots"]:
        n = int(sh["dur"] * SR); t0 = sh["start"]
        u = np.arange(n) / SR
        fade = np.minimum(1, np.minimum(u / 0.8, (sh["dur"] - u) / 0.8)).clip(0, 1)
        name = sh.get("name", "")
        if name in ("blackhole", "blackhole2") or (sh["kind"] == "V" and "SMBH" in sh.get("file", "")):
            x = lp(rng.standard_normal(n), 60, 4) * 3 * fade; place(x * 0.25, t0)
        elif name in ("frb", "radio_dish", "magnetar"):
            x = bp(rng.standard_normal(n), 1500, 6000) * 0.02 * fade
            for k in np.arange(0.6, sh["dur"] - 0.3, 1.7):
                m = int(0.25 * SR); v = np.arange(m) / SR
                x[int(k * SR):int(k * SR) + m] += np.sin(2 * np.pi * np.cumsum(2400 - 1800 * v / 0.25) / SR) * np.exp(-v * 10) * 0.08
            place(x, t0)
        elif name == "gw":
            f = 40 + 200 * (u / (sh["dur"] * 0.75)) ** 3
            ch = np.sin(2 * np.pi * np.cumsum(np.minimum(f, 300)) / SR) * (u < sh["dur"] * 0.75) * np.minimum(1, u) * 0.12
            place(ch, t0)
        elif name == "bigbang":
            x = lp(rng.standard_normal(n), 300) * np.exp(-u * 0.8) * 1.5; place(x * 0.3, t0)
        elif name == "titan_lake":
            x = bp(rng.standard_normal(n), 2000, 8000) * 0.05 * fade + lp(rng.standard_normal(n), 300) * 0.1 * fade; place(x, t0)
        elif name == "warp":
            x = bp(rng.standard_normal(n), 300, 1500) * 0.06 * fade; place(x, t0)

# ---------------- voz y mezcla
with wave.open(os.path.join(WORK, "narracion.wav")) as w:
    vsr = w.getframerate(); v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
v = signal.resample_poly(v, SR, vsr)
v = hp(v, 60)
v = v + 0.15 * bp(v, 2500, 6000) + 0.12 * lp(v, 180)     # presencia y cuerpo
v = v / (np.percentile(np.abs(v), 99.5) + 1e-9) * 0.6
voice = np.zeros(N); voice[:min(N, len(v))] = v[:N]
win = int(0.05 * SR)
rms = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
act = (rms > 0.02).astype(float)
duck = np.zeros(N); d_ = 0.0
for i in range(0, N, 256):
    tg = act[i]; k = 0.25 if tg > d_ else 0.012
    d_ += (tg - d_) * k; duck[i:i + 256] = d_
mix = mus * (0.34 - 0.24 * duck)[:, None] + sfx * (1 - 0.4 * duck)[:, None] + voice[:, None]
mix /= max(1, np.max(np.abs(mix)) / 0.97)
pcm = (mix[:int(D * SR)] * 32767).astype(np.int16)
with wave.open(os.path.join(WORK, "mezcla.wav"), "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("mezcla ok", D)
