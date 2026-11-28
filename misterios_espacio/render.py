# -*- coding: utf-8 -*-
"""Plan de montaje y render del documental (1920x1080, 30 fps).
Mezcla: vídeo real de la NASA (V), imágenes de telescopios con movimiento de cámara (I)
y animaciones propias (C). Fundidos encadenados entre planos y fundido a negro entre misterios."""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cgi import CGI_SCENES, ease

WORK = os.environ["WORK"]
W, H, FPS = 1920, 1080, 30
XF = 15                      # fotogramas de fundido encadenado
OUT = os.path.join(WORK, "secs"); os.makedirs(OUT, exist_ok=True)
VD = os.path.join(WORK, "media", "video")
IMGS = [os.path.join(WORK, l.split("\t")[1].strip()) for l in open(os.path.join(WORK, "imglist.txt"))]

# --- fragmentos de vídeo NASA revisados a mano (archivo, inicio, fin) ---
V = {
    "smbh": [("blackhole/GSFC_20181002_SMBH_m13043_Simulation.mp4", a, b) for a, b in [(9, 14.5), (18, 23), (58, 67), (76, 85), (98, 103.5), (107, 116)]],
    "nustar": [("blackhole/JPL-20250409-NUSTARf-0001-Hunting_Hidden_Black_Holes_2160cc.mp4", a, b) for a, b in [(16, 22), (31, 41), (51, 56), (72, 77), (78, 88), (133, 143)]],
    "eht": [("blackhole/JPL-20250409-NUSTARf-0001-Hunting_Hidden_Black_Holes_2160cc.mp4", a, b) for a, b in [(42, 51)]],
    "pulsar": [("blackhole/Gravity_Assist_Listening_to_the_Universe.mp4", a, b) for a, b in [(137, 142), (150, 158), (177, 185)]],
    "milkyway": [("blackhole/Gravity_Assist_Listening_to_the_Universe.mp4", a, b) for a, b in [(2, 7), (72, 79)]],
    "earth": [("earth/NHQ_2019_0626_Earth_Views_from_the_ISS.mp4", a, a + 8) for a in (60, 300, 700, 1100, 1500, 1900, 2300)]
             + [("earth/Earth_Views_from_the_International_Space_Station.mp4", a, b) for a, b in [(15, 38), (48, 72), (160, 186)]],
    "clipper": [("europa/JPL-20220310-CLIPPRf-0001-Europa_Clipper_Mission_Animations.mp4", a, b) for a, b in
                [(296, 320), (398, 410), (418, 426), (455, 470), (478, 490), (498, 512), (518, 532), (558, 570), (600, 612)]],
    "planets": [("europa/JPL-20230601-CLIPPRf-0001-Ada_Limon_In_Praise_of_Mystery.mp4", a, b) for a, b in [(60, 70), (72, 82), (84, 90)]],
    "streaks": [("europa/JPL-20230601-CLIPPRf-0001-Ada_Limon_In_Praise_of_Mystery.mp4", 8, 16)],
    "cosmicweb": [("galaxy/GSFC_20080520_HST_m10223_COS.mp4", a, b) for a, b in [(2, 12), (14, 20), (140, 165), (165, 192)]],
    "spherex": [("galaxy/JPL-20250130-SPHERX-0001-SPHEREx_Media_Reel.mp4", a, b) for a, b in [(22, 34), (78, 90)]],
    "hubble": [("hubble/" + f, 0, 9) for f in ("GSFC_20080822_HST_m10329_Bottom_Shot_014.mp4", "GSFC_20080822_HST_m10329_Capture_005.mp4",
                                              "GSFC_20080822_HST_m10329_Coupling_Shot_BTY_007.mp4")],
    "webbfirst": [("nebula/First_Images_from_the_James_Webb_Space_Telescope__Official_NASA_Highlights_.mp4", a, b) for a, b in [(44, 52), (90, 100), (109, 115), (171, 178)]],
    "orion": [("nebula/JPL-20221122-SOLSYSf-0001-Orion_Dust_and_Death.mp4", a, b) for a, b in [(39, 44), (55, 61), (72, 78)]],
    "supernova": [("supernova/GSFC_20100126_Nova_m10547_SuperNova.mp4", 0, 7)],
    "webbdeploy": [("webb/GSFC_20101028_JWST_m10660_Webb_Deploy_Short.mp4", a, a + 10) for a in (1, 14, 28, 42, 55)],
}
# --- imágenes revisadas (índices de imglist.txt) ---
I = {
    "bigbang": [1, 2], "blackhole": [6, 7, 8, 9, 10, 11], "cassini": [12, 15, 16, 17], "cepheid": [18],
    "deepfield": [21, 22, 23, 30, 31], "dwarf": [33, 34, 35, 36, 37, 38], "earth": [46, 49, 50],
    "europa": [53, 54, 57, 58, 61, 62], "clipper": [65, 67, 68], "galaxy": [75, 76, 77, 78, 79, 80, 85, 86],
    "cluster": [87, 88, 89, 90, 91], "gw": [93, 97], "hubble": [102, 103, 104], "titan_surf": [109, 110],
    "ice": [111, 112, 114, 115], "jupiter": [117, 118, 121], "lensing": [125, 126, 127], "m87": [128],
    "magnetar": [129, 130, 131, 133, 134, 152], "nebula": [135, 136, 137, 138, 142, 143, 145, 146],
    "cmb": [153, 157, 158], "saturn": [170, 171, 172, 175], "supernova": [176, 177, 178, 179, 180, 181],
    "titan": [184, 185, 186, 188, 189, 191, 192],
}
POOLS = {
    "intro": dict(V=["earth", "webbfirst", "orion", "smbh", "milkyway"], I=["nebula", "galaxy", "saturn", "blackhole"], C=None),
    "m1": dict(V=["cosmicweb", "webbfirst", "milkyway"], I=["cluster", "lensing", "galaxy"], C=None),
    "m2": dict(V=["supernova", "cosmicweb", "spherex"], I=["supernova", "deepfield", "galaxy"], C=None),
    "m3": dict(V=["pulsar", "milkyway"], I=["magnetar", "galaxy"], C=None),
    "m4": dict(V=["smbh", "nustar", "eht"], I=["blackhole", "m87", "gw"], C=None),
    "m5": dict(V=["hubble", "webbdeploy", "supernova"], I=["hubble", "cepheid", "cmb", "supernova"], C=None),
    "m6": dict(V=["cosmicweb", "streaks", "spherex"], I=["cmb", "bigbang", "deepfield"], C=None),
    "m7": dict(V=["cosmicweb", "webbfirst"], I=["dwarf", "galaxy"], C=None),
    "m8": dict(V=["clipper", "planets"], I=["europa", "ice", "jupiter", "clipper"], C=None),
    "m9": dict(V=["planets"], I=["titan", "titan_surf", "saturn", "cassini"], C=None),
    "m10": dict(V=["webbdeploy", "webbfirst", "cosmicweb"], I=["deepfield", "galaxy", "nebula"], C=None),
    "outro": dict(V=["earth", "orion", "milkyway"], I=["nebula", "galaxy"], C=None),
}
CREDIT_V = "Vídeo: NASA"
EXPLAIN = {"rotation_curve", "pie", "hubble_chart", "frb", "europa_cut", "timeline", "expansion", "gw", "collision", "multiverse"}


def plan():
    tl = json.load(open(os.path.join(WORK, "timeline.json")))
    secs = tl["sections"]
    rng = np.random.default_rng(14)
    used_v, used_i = {}, set()
    allplan = []
    for si, s in enumerate(secs):
        a = 0.0 if si == 0 else s["start"] - 0.4
        b = secs[si + 1]["start"] - 0.4 if si + 1 < len(secs) else tl["duration"]
        pool = POOLS[s["id"]]
        cg = list(s["cgi"])
        order = ["C", "V", "I", "V", "I", "C", "I", "V"]
        shots, t, k = [], a, 0
        while t < b - 0.3:
            kind = order[k % len(order)]; k += 1
            dur = float(rng.uniform(3.6, 5.2))
            sh = None
            if kind == "C" and cg:
                name = cg.pop(0); cg.append(name)
                dur = 6.5 if name in EXPLAIN else dur + 0.6
                sh = dict(kind="C", name=name, seed=int(rng.integers(1e9)), credit="Animación ilustrativa")
            elif kind == "V":
                cands = [(g, c) for g in pool["V"] for c in V[g]]
                cands.sort(key=lambda gc: used_v.get(gc[1], 0))
                for g, (f, s0, s1) in cands:
                    st = used_v.get((f, s0, s1), 0) + s0
                    if s1 - st >= min(dur, 3.0):
                        dur = min(dur, s1 - st)
                        used_v[(f, s0, s1)] = st - s0 + dur
                        sh = dict(kind="V", file=f, ss=st, credit=CREDIT_V); break
            if sh is None and kind in ("I", "V", "C"):
                cands = [i for g in pool["I"] for i in I[g] if i not in used_i] or [i for g in pool["I"] for i in I[g]]
                i = cands[int(rng.integers(len(cands)))]
                used_i.add(i)
                sh = dict(kind="I", img=i, credit="Imagen: NASA", move=int(rng.integers(0, 4)))
            if b - (t + dur) < 2.5:
                dur = b - t
            sh.update(start=round(t, 3), dur=round(dur, 3))
            shots.append(sh); t += dur
        allplan.append(dict(id=s["id"], start=a, end=b, shots=shots))
    json.dump(allplan, open(os.path.join(WORK, "plan.json"), "w"), indent=1)
    return allplan


def video_frames(f, ss, n):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-i", os.path.join(VD, f), "-frames:v", str(n),
                        "-vf", f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    m = len(a) // (W * H * 3)
    fr = a[:m * W * H * 3].reshape(m, H, W, 3)
    if m == 0:
        fr = np.zeros((1, H, W, 3), np.uint8)
    if m < n:
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - m, 0)])
    return fr


_imgcache = {}


def load_img(i):
    if i not in _imgcache:
        im = Image.open(IMGS[i]).convert("RGB")
        iw, ih = im.size
        # fondo desenfocado si la proporción no es 16:9
        s = max(W * 1.25 / iw, H * 1.25 / ih)
        big = im.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
        if abs(iw / ih - W / H) > 0.25 or min(iw, ih) < 500:
            bg = im.resize((int(W * 1.25), int(H * 1.25))).filter(ImageFilter.GaussianBlur(40))
            bg = Image.eval(bg, lambda v: int(v * 0.45))
            s2 = min(W * 1.12 / iw, H * 1.12 / ih)
            fg = im.resize((int(iw * s2), int(ih * s2)), Image.LANCZOS)
            bg.paste(fg, ((bg.size[0] - fg.size[0]) // 2, (bg.size[1] - fg.size[1]) // 2))
            big = bg
        _imgcache[i] = big
    return _imgcache[i]


def shot_frames(sh, n):
    """Devuelve un generador de n fotogramas (np.uint8 HxWx3)."""
    if sh["kind"] == "V":
        fr = video_frames(sh["file"], sh["ss"], n)
        for k in range(n):
            u = k / max(1, n - 1)
            z = 1.0 + 0.05 * u
            im = Image.fromarray(fr[k])
            cw, ch = W / z, H / z
            yield np.asarray(im.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H - ch) / 2 + ch)))
    elif sh["kind"] == "I":
        big = load_img(sh["img"])
        bw, bh = big.size
        mv = sh["move"]
        for k in range(n):
            u = ease(k / max(1, n - 1))
            if mv == 0: z = 1.0 + 0.18 * u; cx, cy = 0.5, 0.5
            elif mv == 1: z = 1.18 - 0.16 * u; cx, cy = 0.5, 0.5
            elif mv == 2: z = 1.08; cx, cy = 0.42 + 0.16 * u, 0.5
            else: z = 1.1 + 0.08 * u; cx, cy = 0.55 - 0.1 * u, 0.45 + 0.1 * u
            vw, vh = bw / 1.25 / z * 1.0, bh / 1.25 / z
            l = min(max(0, cx * bw - vw / 2), bw - vw); t = min(max(0, cy * bh - vh / 2), bh - vh)
            yield np.asarray(big.resize((W, H), Image.BILINEAR, box=(l, t, l + vw, t + vh)))
    else:
        sc = CGI_SCENES[sh["name"]](np.random.default_rng(sh["seed"]), n / FPS)
        for k in range(n):
            yield np.asarray(sc.frame(k / FPS).convert("RGB"))


def render_section(sec):
    out = os.path.join(OUT, f"{sec['id']}.mp4")
    if os.path.exists(out):
        return sec["id"]
    total = int(round((sec["end"] - sec["start"]) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-threads", "2",
                          out + ".tmp.mp4"], stdin=subprocess.PIPE)
    written = 0
    tail = None
    shots = sec["shots"]
    for i, sh in enumerate(shots):
        last = i == len(shots) - 1
        n = int(round(sh["dur"] * FPS)) if not last else total - written
        extra = 0 if last else XF
        frames = shot_frames(sh, n + extra)
        for k, f in enumerate(frames):
            if k < XF and tail is not None:
                a = (k + 1) / (XF + 1)
                f = (tail[k].astype(np.float32) * (1 - a) + f.astype(np.float32) * a).astype(np.uint8)
            if k < n:
                if written < total:
                    # fundido desde negro al inicio y a negro al final de cada sección
                    g = min(1.0, (written + 1) / 12, (total - written) / 12)
                    ff = f if g >= 1 else (f.astype(np.float32) * g).astype(np.uint8)
                    p.stdin.write(np.ascontiguousarray(ff).tobytes()); written += 1
            else:
                if k == n: tail = []
                tail.append(f)
        if last:
            break
    while written < total:
        p.stdin.write(np.zeros((H, W, 3), np.uint8).tobytes()); written += 1
    p.stdin.close(); p.wait()
    os.replace(out + ".tmp.mp4", out)
    print("sección", sec["id"], "ok", flush=True)
    return sec["id"]


if __name__ == "__main__":
    pl = plan()
    n = sum(len(s["shots"]) for s in pl)
    kinds = {}
    for s in pl:
        for sh in s["shots"]:
            kinds[sh["kind"]] = kinds.get(sh["kind"], 0) + 1
    print(f"{n} planos {kinds}", flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == "plan":
        sys.exit()
    order = sorted(pl, key=lambda s: -(s["end"] - s["start"]))
    with Pool(int(os.environ.get("PROCS", "4"))) as po:
        for _ in po.imap_unordered(render_section, order):
            pass
    with open(os.path.join(WORK, "concat.txt"), "w") as f:
        for s in pl:
            f.write(f"file '{os.path.join(OUT, s['id'] + '.mp4')}'\n")
    print("RENDER COMPLETO", flush=True)
