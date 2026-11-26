"""Renderiza un capítulo.

  python3 render.py ep01                 -> output/ep01.mp4
  python3 render.py ep01 --preview 3 12  -> build/ep01/preview_*.png en esos segundos
"""
import importlib, json, os, subprocess, sys, time
from multiprocessing import Pool
import skia
from engine import W, H, subtitles, hud, post, seg

EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"
B = f"build/{EP}"
TL = json.load(open(f"{B}/timeline.json"))
FPS = TL["fps"]
VIS = importlib.import_module(f"episodes.{EP}_vis")
EPI = TL["episode"]

class Ctx:
    def __init__(self, sc, T):
        self.sc, self.T = sc, T
        self.t = T - sc["start"]; self.d = sc["dur"]
        self.lines = [TL["lines"][i] for i in sc["lines"]]
    def l(self, i):
        ln = self.lines[i]
        return {"s": ln["start"] - self.sc["start"], "e": ln["end"] - self.sc["start"]}
    def talk(self, spk):
        for ln in self.lines:
            if ln["speaker"] == spk and ln["start"] <= self.T < ln["end"]:
                k = int((self.T - ln["start"]) * FPS)
                env = ln["env"]
                return env[min(k, len(env) - 1)] if env else 0
        return 0.0
    def at(self, scene_id, t):
        sc = next(s for s in TL["scenes"] if s["id"] == scene_id)
        return Ctx(sc, sc["start"] + t)
    def sfx_all(self, name):
        return [e["t"] - self.sc["start"] for e in TL["sfx"] if e["scene"] == self.sc["id"] and e["name"] == name]
    def sfx_t(self, name):
        for e in TL["sfx"]:
            if e["scene"] == self.sc["id"] and e["name"] == name:
                return e["t"] - self.sc["start"]
        return None

def scene_at(T):
    cur = TL["scenes"][0]
    for sc in TL["scenes"]:
        if T >= sc["start"]: cur = sc
    return cur

def draw_frame(fi):
    T = fi / FPS
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    sc = scene_at(T)
    ctx = Ctx(sc, T)
    VIS.SCENE_FUNCS[sc["id"]](c, ctx)
    post(c, fi)
    if sc["id"] in VIS.HUD_SCENES:
        a = 1.0
        first = min(s["start"] for s in TL["scenes"] if s["id"] in VIS.HUD_SCENES)
        a = seg(T, first, first + .6)
        hud(c, T, EPI["num"], EPI["money"], a)
    if sc["id"] not in VIS.NO_SUBS:
        subtitles(c, ctx.lines, T)
    return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)

def render_chunk(args):
    ci, f0, f1 = args
    out = f"{B}/seg_{ci:02d}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        ff.stdin.write(draw_frame(fi).tobytes())
    ff.stdin.close(); ff.wait()
    return out

def main():
    if "--preview" in sys.argv:
        from PIL import Image
        for s in sys.argv[sys.argv.index("--preview") + 1:]:
            fi = int(float(s) * FPS)
            Image.fromarray(draw_frame(fi)).convert("RGB").resize((540, 960)).save(f"{B}/preview_{float(s):05.1f}.png")
        return
    n = int(TL["duration"] * FPS)
    k = os.cpu_count() or 4
    step = (n + k * 3 - 1) // (k * 3)
    chunks = [(i, a, min(n, a + step)) for i, a in enumerate(range(0, n, step))]
    t0 = time.time()
    with Pool(k) as p:
        segs = p.map(render_chunk, chunks)
    print(f"render {n} frames en {time.time() - t0:.0f}s")
    with open(f"{B}/segs.txt", "w") as f:
        for s in segs: f.write(f"file '{os.path.basename(s)}'\n")
    os.makedirs("output", exist_ok=True)
    out = f"output/{EP}_30_dias_millonario.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{B}/segs.txt",
                    "-i", f"{B}/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    for s in segs: os.remove(s)
    print("OK ->", out)

if __name__ == "__main__":
    main()
