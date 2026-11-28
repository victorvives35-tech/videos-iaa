# -*- coding: utf-8 -*-
"""Planifica los planos según la narración y los renderiza en paralelo (reanudable)."""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx import W, H, Lights, ease, lerp
from scenes import SCENES

WORK = os.environ["WORK"]
FPS = 30
SHOTS = os.path.join(WORK, "shots")


def plan():
    tl = json.load(open(os.path.join(WORK, "timeline.json")))
    rng = np.random.default_rng(2026)
    secs = tl["sections"]
    shots, last = [], None
    for i, s in enumerate(secs):
        a = 0.0 if i == 0 else s["start"]
        b = secs[i + 1]["start"] if i + 1 < len(secs) else tl["duration"]
        pool = list(s["escenas"])
        fcur, fb, first = int(round(a * FPS)), int(round(b * FPS)), True
        order = []
        while fcur < fb:
            t = fcur / FPS
            if not order:
                order = list(rng.permutation(pool))
            sc = order.pop(0)
            if sc == last and len(set(pool)) > 1:
                order.append(sc); sc = order.pop(0)
            if sc == "police" and rng.random() < 0.4:
                sc = "policeheli"
            dur = float(rng.uniform(2.3, 3.9)) if s["id"] != "intro" else float(rng.uniform(1.8, 2.8))
            if sc == "map":
                dur += 1.2
            nf = int(round(dur * FPS))
            if fb - (fcur + nf) < 48:
                nf = fb - fcur
            cls = SCENES[sc]
            pan = float(rng.uniform(120, 360)) * rng.choice([-1, 1])
            z0 = float(rng.uniform(1.0, 1.06)); z1 = float(rng.uniform(1.0, 1.14))
            if rng.random() < 0.5: z0, z1 = z1, z0
            shots.append(dict(i=len(shots), sec=s["id"], scene=sc, variant=str(rng.choice(cls.variants)),
                              seed=int(rng.integers(1e9)), start=round(fcur / FPS, 4), frames=nf, dur=nf / FPS,
                              pan0=float(rng.uniform(-100, 100)), pan=pan, z0=z0, z1=z1,
                              dx=float(rng.uniform(-40, 40)), dy=float(rng.uniform(-20, 20)),
                              trans="flash" if first and i > 0 else ("leak" if rng.random() < 0.25 else "cut"),
                              shake=sc in ("police", "storm")))
            fcur += nf; last = sc; first = False
    json.dump(shots, open(os.path.join(WORK, "shots.json"), "w"), indent=0)
    return shots


def render_shot(sh):
    out = os.path.join(SHOTS, f"{sh['i']:04d}.mp4")
    if os.path.exists(out):
        return sh["i"], []
    rng = np.random.default_rng(sh["seed"])
    sc = SCENES[sh["scene"]](rng, sh["variant"], sh["dur"])
    tmp = out + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                          "-pix_fmt", "yuv420p", "-threads", "1", tmp], stdin=subprocess.PIPE)
    n = sh["frames"]
    for f in range(n):
        t = f / FPS
        u = f / max(1, n - 1)
        e = ease(u)
        pan = sh["pan0"] + sh["pan"] * e
        img = sc.frame(t, pan)
        z = lerp(sh["z0"], sh["z1"], e)
        if sh["trans"] == "flash" and f < 8:
            z *= 1 + 0.10 * (1 - f / 8) ** 2
        cw, ch = W / z, H / z
        cx = W / 2 + sh["dx"] * (e - 0.5)
        cy = H / 2 + sh["dy"] * (e - 0.5)
        if sh["shake"]:
            cx += math.sin(t * 37) * 3 + math.sin(t * 23) * 2
            cy += math.cos(t * 31) * 2.5
        l = min(max(0, cx - cw / 2), W - cw); tp = min(max(0, cy - ch / 2), H - ch)
        if z > 1.001:
            img = img.resize((W, H), Image.BILINEAR, box=(l, tp, l + cw, tp + ch))
        if sh["trans"] == "flash" and f < 9:
            a = (1 - f / 9) ** 1.5
            arr = np.asarray(img, np.float32)
            img = Image.fromarray(np.clip(arr * (1 - a) + 255 * a, 0, 255).astype(np.uint8))
        elif sh["trans"] == "leak" and f < 12:
            L = Lights()
            a = (1 - f / 12) ** 2
            L.add(W * (0.15 + 0.06 * f), H * 0.3, 700, (255, 150, 60), 0.8 * a, 1.2)
            L.add(W * 0.9, H * 0.8, 500, (255, 60, 120), 0.5 * a, 1.2)
            img = L.apply(img)
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    os.replace(tmp, out)
    return sh["i"], [(name, sh["start"] + tt) for name, tt in sc.events]


if __name__ == "__main__":
    os.makedirs(SHOTS, exist_ok=True)
    shots = plan()
    print(f"{len(shots)} planos, {sum(s['frames'] for s in shots)} fotogramas", flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == "plan":
        sys.exit()
    ev_path = os.path.join(WORK, "events.json")
    events = json.load(open(ev_path)) if os.path.exists(ev_path) else {}
    with Pool(int(os.environ.get("PROCS", "4"))) as pool:
        for i, ev in pool.imap_unordered(render_shot, shots):
            if ev:
                events[str(i)] = ev
                json.dump(events, open(ev_path, "w"))
            print(f"plano {i} ok", flush=True)
    # eventos (truenos) de todos los planos de tormenta, recalculados si faltan
    for sh in shots:
        if sh["scene"] == "storm" and str(sh["i"]) not in events:
            sc = SCENES["storm"](np.random.default_rng(sh["seed"]), sh["variant"], sh["dur"])
            events[str(sh["i"])] = [(n, sh["start"] + tt) for n, tt in sc.events]
    json.dump(events, open(ev_path, "w"))
    with open(os.path.join(WORK, "concat.txt"), "w") as f:
        for sh in shots:
            f.write(f"file '{SHOTS}/{sh['i']:04d}.mp4'\n")
    print("RENDER COMPLETO", flush=True)
