#!/usr/bin/env python3
"""Historia 3D: "In this town, everyone has a number above their head" (contador de HUSS).

Renderizado real en 3D con Blender (Cycles) + motor de audio de in_this_town.py.
Fases (se pueden reanudar):
  python3 huss_counter.py prep   --voice VOZ.onnx   -> audio + línea de tiempo
  python3 huss_counter.py render                    -> fotogramas 3D (reanudable)
  python3 huss_counter.py encode                    -> subtítulos + vídeo final
"""
import json, math, os, random, subprocess, sys, tempfile, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
WORK = os.environ.get("HC_WORK", "/tmp/claude-0/-home-user-videos-iaa/ff2cc793-9d09-5acb-b247-6c15a06ec93f/scratchpad/hc")
OUT = os.path.join(HERE, "huss_counter.mp4")
FPS = 24
RES = (540, 960)

SCRIPT = [
    ("In this town, everyone has a number above their head.", "intro", None),
    ("It shows how many times you can say [HUSS] for the rest of your life.", "life", None),
    ("Most people have thousands. My grandma has nine million. She never says it.", "granny", None),
    ("And me? I have six.", "me6", None),
    ("Here, people count them like money. Kids trade them at school.", "kids", None),
    ("When I was born, I had one million. I said it... a little too much.", "born", None),
    ("Everyone told me: save them! Don't waste them!", "save", None),
    ("So for one whole year, I didn't say it. Not once.", "year", None),
    ("Then one night, the big clock on the tower stopped.", "clock", None),
    ("And everybody's numbers started going down. By themselves.", "drop", None),
    ("Ten thousand. One thousand. One hundred.", "drop_b", None),
    ("The mayor said: only a [HUSS] from the heart can restart the clock.", "mayor", None),
    ("Everyone tried. Nothing worked. Their hearts were not in it.", "tried", None),
    ("Grandma tried too. Her nine million didn't move at all.", "gran_try", None),
    ("Then everyone looked at me. I only had six left.", "look", None),
    ("If I used them, I could never say it again. Ever.", "look_b", None),
    ("I closed my eyes... and said:", "huss6", "solo", 6),
    ("The clock started again! But my number... was zero.", "restart", None),
    ("Then grandma walked over... and gave me all of hers.", "gift", None),
    ("She said: I never liked that word anyway.", "never", None),
    ("Now she's the only person in town with a zero. And the happiest.", "never_b", None),
    ("So now I have nine million. And this time... I'm not saving them.", "nine", None),
    ("", "end", "solo", 6),
]

# ======================================================================= fase 1: audio + tiempos
def prep(voice):
    import in_this_town as m
    m.SCRIPT = SCRIPT
    os.makedirs(WORK, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        segs, total = m.build(voice, tmp)
        m.mix_audio(segs, total, os.path.join(WORK, "mix.wav"))
    meta = [dict(scene=s["scene"], start=s["start"], dur=s["dur"], words=s["words"], hits=s.get("hits") or [],
                 nh=s.get("nh", 0), text=s["text"]) for s in segs]
    json.dump(dict(segs=meta, total=total), open(os.path.join(WORK, "timeline.json"), "w"))
    print(f"duración: {total:.1f}s  fotogramas: {int(total * FPS)}")

# ======================================================================= fase 2: render 3D
def ease(u): u = max(0., min(1., u)); return u * u * (3 - 2 * u)

def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))

def render():
    import bpy
    import world3d as w
    tl = json.load(open(os.path.join(WORK, "timeline.json")))
    segs, total = tl["segs"], tl["total"]
    preview = os.environ.get("HC_PREVIEW")
    fdir = os.path.join(WORK, "preview" if preview else "frames"); os.makedirs(fdir, exist_ok=True)
    only = None
    if preview:
        only = set(int((s["start"] + (s["dur"] + .2) * .6) * FPS) for s in segs)

    w.reset(); env = w.setup_scene((270, 480) if preview else RES, 4 if preview else 10); tower = w.build_city()
    cam = env["cam"]
    C = {}
    C["me"] = w.Char("me", (40, 90, 210), (40, 90, 210), hat="huss", jersey="HUSS")
    C["gran"] = w.Char("gran", (175, 95, 165), (120, 70, 120), bun=True, glasses=True)
    C["mayor"] = w.Char("mayor", (25, 25, 30), (25, 25, 30), tophat=True)
    C["a"] = w.Char("a", (235, 130, 60), (40, 50, 90), hair=(35, 25, 20))
    C["b"] = w.Char("b", (60, 190, 180), (50, 60, 100), hair=(120, 70, 40))
    C["c"] = w.Char("c", (150, 90, 220), (40, 40, 60), hair=(20, 20, 20))
    C["d"] = w.Char("d", (120, 200, 90), (70, 50, 40), hair=(200, 60, 40))
    C["e"] = w.Char("e", (250, 210, 70), (60, 60, 140), hair=(240, 200, 120))
    C["f"] = w.Char("f", (230, 80, 110), (40, 40, 50), hair=(60, 40, 20))
    C["kid"] = w.Char("kid", (90, 160, 250), (240, 120, 60), hair=(140, 90, 40), scale=.7)
    NPC = ["a", "b", "c", "d", "e", "f", "kid"]
    BASE = {"a": 3250, "b": 12480, "c": 870, "d": 45120, "e": 6300, "f": 25900, "kid": 99000, "mayor": 52000}

    def hide_all():
        for ch in C.values():
            ch.pose(visible=False); ch.set_counter(0, visible=False)

    def put(name, loc, yaw=None, face="smile", arms="down", walk=0., t=0., counter=None, crgb=(245, 245, 245),
            head_yaw=0., jump=0., face_cam=False):
        ch = C[name]
        if face_cam:
            dx, dy = cam.location.x - loc[0], cam.location.y - loc[1]
            yaw = math.degrees(math.atan2(dx, -dy))
        ch.pose((loc[0], loc[1], .18), yaw if yaw is not None else 0, walk=walk, t=t, arms=arms, face=face,
                head_yaw=head_yaw, jump=jump)
        if counter is None: ch.set_counter(0, visible=False)
        else: ch.set_counter(counter, crgb, cam=cam, emit=2.0)

    def walkers(T, names, count_fn=None, panic=False, y0=14, spread=34, face="smile"):
        lanes = [-7.2, 7.2, -6.2, 6.4, -2.5, 2.8, -7.6]
        for i, n in enumerate(names):
            y = y0 + (i * 9.3 + 6) % spread - (T * (2.4 if not panic else 5.5)) % spread * (0 if panic else 1)
            if panic: y = y0 + (i * 7.1) % spread
            x = lanes[i % len(lanes)] + (math.sin(T * 3 + i) * 1.5 if panic else 0)
            val = count_fn(n) if count_fn else BASE.get(n, 1000)
            put(n, (x, y), 0 if not panic else (math.degrees(math.sin(T * 2 + i)) * 2), face=face,
                arms="panic" if panic else "down", walk=1.0 if not panic else 1.6, t=T * (1 if not panic else 1.8) + i,
                counter=val, crgb=(245, 245, 245) if not panic else (255, 120, 100))

    def sky_day(): w.set_sky(env, (25, 130, 255), (160, 225, 255), (1, .95, .88), 5.0, 1.0); w.set_night(0)
    def sky_dusk(k=1.0):
        top = lerp((40, 110, 225), (45, 30, 110), k); bot = lerp((175, 215, 250), (245, 140, 120), k)
        w.set_sky(env, top, bot, lerp((1, .95, .88), (1, .55, .35), k), 4.5 - 2.6 * k, 1.0 - .4 * k); w.set_night(k)

    def clock_hands(running, T):
        a = (T * 2.0) if running else 1.9
        tower["minute"].rotation_euler = (0, a, 0); tower["hour"].rotation_euler = (0, a / 12 + 1.0, 0)

    def hit_of(seg, T):
        hits = seg["hits"]
        if not hits or T < hits[0] - .02: return -1, 0.
        k = max(i for i, h in enumerate(hits) if T >= h - .02)
        return k, max(0., 1 - (T - hits[k] + .02) / .18)

    def shake(eye, amt, T):
        return (eye[0] + amt * math.sin(T * 47), eye[1], eye[2] + amt * math.cos(T * 53))

    w.set_season(0)
    season_now = [0]

    n_frames = int(total * FPS)
    for fi in range(n_frames):
        if only is not None and fi not in only: continue
        path = os.path.join(fdir, f"f{fi:05d}.png")
        if os.path.exists(path) and not preview: continue
        T = fi / FPS
        seg = segs[0]
        for s in segs:
            if T >= s["start"] - .05: seg = s
        t = max(0., T - seg["start"]); dur = seg["dur"] + .2; u = min(1., t / dur)
        sc = seg["scene"]
        hide_all()
        k, hit = hit_of(seg, T)
        sky_day(); clock_hands(True, T)
        if season_now[0] != 0 and sc != "year":
            w.set_season(0); season_now[0] = 0

        if sc == "intro":
            w.look_at(cam, (0.8, -2 + 6 * ease(u), 3.6), (0, 40, 5.5))
            walkers(T, NPC)
        elif sc == "life":
            w.look_at(cam, (0.3 - .6 * u, 2.6 + 1.0 * u, 4.6), (0.8, 9, 5.4))
            walkers(T, ["b", "c", "d", "e"], y0=20)
            val = 3250 - (1 if k >= 0 else 0)
            put("a", (0.8, 9), face="yell" if hit > .2 else "smile", arms="out" if hit > .2 else "down", t=T,
                counter=val, crgb=(255, 210, 80) if hit > .1 else (245, 245, 245), face_cam=True)
        elif sc == "granny":
            ang = -.4 + .8 * ease(u)
            w.look_at(cam, (-0.5 + 6 * math.sin(ang), 9 - 6 * math.cos(ang), 4.4), (-0.5, 9, 5.2))
            walkers(T, ["a", "c", "e"], y0=22)
            put("gran", (-0.5, 9), face="closed" if u > .7 else "laugh", t=T, counter=9000000, crgb=(255, 205, 60), face_cam=True,
                arms="wave" if u < .5 else "down")
        elif sc == "me6":
            dist = 9 - 4.5 * ease(u)
            w.look_at(cam, (0, 9 - dist, 4.8), (0, 9, 5.6))
            put("me", (0, 9), face="flat" if u < .6 else "sad", t=T, counter=6, crgb=(255, 70, 60), face_cam=True)
        elif sc == "kids":
            w.look_at(cam, (3.5, 1.5, 4.2), (0, 12, 4.4))
            v = ease(min(1, max(0, (u - .35) / .3)))
            put("kid", (-1.6, 12), yaw=-90, face="laugh", arms="out", t=T, counter=int(99000 - 500 * v))
            put("c", (1.6, 12), yaw=90, face="smile", arms="out", t=T, counter=int(870 + 500 * v), crgb=(120, 255, 140) if v > .1 else (245, 245, 245))
            walkers(T, ["a", "e"], y0=24)
        elif sc == "born":
            w.look_at(cam, (2.5, 2.5, 2.2), (0, 10, 5.5))
            v = ease(min(1, u / .8))
            val = int(1000000 * (1 - v) ** 3 + 6 * v)
            put("me", (0, 10), face="laugh", arms="up", t=T, jump=abs(math.sin(T * 7)) * 1.2, counter=max(6, val),
                crgb=(255, 70, 60) if val < 100 else (255, 210, 80), face_cam=True)
            walkers(T, ["b", "d"], y0=24)
        elif sc == "save":
            w.look_at(cam, (7, 2, 8.5), (0, 12, 3.5))
            put("me", (0, 12), face="sad", t=T, counter=6, crgb=(255, 70, 60), yaw=180 + 20 * math.sin(T))
            for i, n in enumerate(["a", "b", "c", "gran", "d"]):
                ang = math.radians(-60 + i * 55)
                x, y = 3.4 * math.sin(ang), 12 + 3.4 * math.cos(ang)
                yaw = math.degrees(math.atan2(0 - x, -(12 - y)))  # mirando a Huss Boy
                put(n, (x, y), yaw=yaw,
                    face="angry", arms="point", t=T + i, counter=BASE.get(n, 9000000) if n != "gran" else 9000000,
                    crgb=(255, 205, 60) if n == "gran" else (245, 245, 245))
        elif sc == "year":
            season = min(2, int(u * 3))
            if season != season_now[0]: w.set_season(season); season_now[0] = season
            if season == 2: w.set_sky(env, (150, 185, 230), (230, 240, 250), (1, 1, 1), 3.5, 1.2)
            elif season == 1: w.set_sky(env, (90, 130, 200), (250, 200, 150), (1, .85, .7), 4.0, 1.0)
            y = 30 - 10 * u
            w.look_at(cam, (-1.5, y - 7, 4.0), (-1.5, y + 2, 5.0))
            put("me", (-1.5, y), yaw=0, face="closed", walk=1, t=T, counter=6, crgb=(255, 70, 60))
        elif sc == "clock":
            sky_dusk(ease(u)); clock_hands(False, T)
            w.look_at(cam, (3, 118, 6 + 6 * ease(u)), (0, 145, 17))
        elif sc == "drop_b":
            sky_dusk(1.0); clock_hands(False, T)
            w.look_at(cam, (0.6, 4.2, 4.6), (0.8, 10, 5.6))
            val = [10000, 1000, 100][min(2, int(u * 3))] - int(((u * 3) % 1) * 90)
            put("d", (0.8, 10), face="shock", arms="panic", t=T, counter=max(0, val), crgb=(255, 90, 80), face_cam=True)
        elif sc == "drop":
            sky_dusk(1.0); clock_hands(False, T)
            w.look_at(cam, (0, -1, 4.5), (0, 20, 5))
            walkers(T, NPC, count_fn=lambda n: max(0, int(BASE[n] - (T - seg["start"]) * BASE[n] * .25)), panic=True, y0=8, spread=26,
                    face="shock")
        elif sc == "mayor":
            sky_dusk(1.0); clock_hands(False, T)
            w.look_at(cam, (1.2, 4.5, 4.4), (0, 10, 5.6))
            val = max(0, int(BASE["mayor"] - (T - seg["start"]) * 3000))
            put("mayor", (0, 10), face="yell" if hit > .2 else "angry", arms="out" if hit > .2 else "point", t=T,
                counter=val, crgb=(255, 120, 100), face_cam=True)
        elif sc == "tried":
            sky_dusk(1.0); clock_hands(False, T)
            w.look_at(cam, (-6 + 12 * ease(u), 2, 5), (0, 14, 4.5))
            for i, n in enumerate(["a", "b", "c", "d", "e", "f"]):
                x = -6 + i * 2.4; y = 13 + (i % 2) * 2.5
                put(n, (x, y), face="yell" if int(T * 3 + i) % 2 else "sad", arms="out" if int(T * 3 + i) % 2 else "down", t=T + i,
                    counter=max(0, int(BASE[n] * .4 - (T - seg["start"]) * BASE[n] * .05)), crgb=(255, 120, 100), face_cam=True)
        elif sc == "gran_try":
            sky_dusk(1.0); clock_hands(False, T)
            w.look_at(cam, (-0.5, 5.2, 4.3), (-0.5, 11, 5.3))
            put("gran", (-0.5, 11), face="yell" if int(T * 3) % 2 else "angry", arms="out", t=T, counter=9000000, crgb=(255, 205, 60), face_cam=True)
        elif sc == "look_b":
            sky_dusk(1.0); clock_hands(False, T)
            w.look_at(cam, (0.5, 5.6 - 1.0 * ease(u), 5.0), (0, 10, 5.9))
            put("me", (0, 10), face="sad", t=T, counter=6, crgb=(255, 70, 60), face_cam=True)
        elif sc == "look":
            sky_dusk(1.0); clock_hands(False, T)
            w.look_at(cam, (0, 6, 5.3), (0, 16, 5.2))
            for i, n in enumerate(["a", "b", "c", "gran", "d", "e"]):
                x = -6 + i * 2.4; y = 14 + (i % 2) * 2.5
                turn = ease(min(1, u * 2 - i * .1))
                put(n, (x, y), yaw=180 - 180 * turn, face="shock" if turn > .5 else "flat", t=T + i,
                    counter=9000000 if n == "gran" else max(0, int(BASE[n] * .3 - (T - seg["start"]) * 200)),
                    crgb=(255, 205, 60) if n == "gran" else (255, 120, 100))
        elif sc == "huss6":
            light = max(0, k + 1) / 6
            sky_dusk(1 - .6 * light); clock_hands(False, T)
            val = 6 - max(0, k + 1)
            eye = (0, 5.0, 4.9) if k < 0 else shake((0, 5.4, 4.9), .18 * hit, T)
            w.look_at(cam, eye, (0, 10, 5.6))
            put("me", (0, 10), face="closed" if k < 0 else ("yell" if hit > .2 else "closed"),
                arms="out" if hit > .1 else "down", t=T, counter=val, crgb=(255, 70, 60), face_cam=True)
        elif sc == "restart":
            if u < .5:
                sky_dusk(.3 * (1 - u * 2)); clock_hands(True, T * 3)
                w.look_at(cam, (3, 125, 13), (0, 145, 17.5))
            else:
                sky_day()
                w.look_at(cam, (0, 4.8, 4.6), (0, 10, 5.6))
                put("me", (0, 10), face="sad", t=T, counter=0, crgb=(255, 70, 60), face_cam=True)
        elif sc == "gift":
            w.look_at(cam, (5.5, 4, 5), (0, 11, 5))
            gx = 5 - 3.6 * ease(min(1, u / .6))
            put("me", (-0.6, 11), yaw=70, face="sad" if u < .6 else "shock", t=T,
                counter=0 if u < .6 else int(9000000 * ease((u - .6) / .4)), crgb=(255, 70, 60) if u < .6 else (255, 205, 60))
            put("gran", (gx, 11), yaw=-90, face="smile", walk=1 if u < .6 else 0, t=T,
                counter=9000000 if u < .6 else int(9000000 * (1 - ease((u - .6) / .4))), crgb=(255, 205, 60))
        elif sc == "never":
            w.look_at(cam, (-0.5, 5.5, 4.4), (-0.5, 11, 5.3))
            put("gran", (-0.5, 11), face="laugh", arms="wave", t=T, counter=0, crgb=(200, 200, 200), face_cam=True)
        elif sc == "never_b":
            w.look_at(cam, (4, 3, 4.5), (-0.5, 12, 4.5))
            put("gran", (-0.5, 12), yaw=20, face="laugh", arms="up", t=T, jump=abs(math.sin(T * 5)) * .8, counter=0, crgb=(200, 200, 200))
            walkers(T, ["a", "b"], y0=24)
        elif sc == "nine":
            w.set_sky(env, (60, 120, 230), (255, 205, 150), (1, .85, .65), 4.5, 1.0)
            dist = 8 - 3 * ease(u)
            w.look_at(cam, (1.0, 10 - dist, 3.8), (0, 10, 5.8))
            put("me", (0, 10), face="laugh", arms="up" if u > .5 else "down", t=T, counter=9000000, crgb=(255, 205, 60), face_cam=True)
            walkers(T, ["a", "c", "e"], y0=22)
        elif sc == "end":
            w.set_sky(env, (60, 120, 230), (255, 205, 150), (1, .85, .65), 4.5, 1.0)
            eye = shake((0, 5.2, 4.6), .15 * hit, T)
            w.look_at(cam, eye, (0, 10, 5.6))
            val = 9000000 - max(0, k + 1)
            put("me", (0, 10), face="yell" if hit > .2 else "laugh", arms="up" if hit > .1 else "out", t=T, jump=.5 * hit,
                counter=val, crgb=(255, 205, 60), face_cam=True)
            for i, n in enumerate(["a", "b", "gran", "e"]):
                x = [-4, -2, 2.5, 4.5][i]
                put(n, (x, 15), face="laugh", arms="up" if hit > .1 else "down", t=T + i, jump=.6 * hit,
                    counter=9000000 if n == "gran" else BASE[n], crgb=(255, 205, 60) if n == "gran" else (245, 245, 245), face_cam=True)

        env["scene"].render.filepath = path
        bpy.ops.render.render(write_still=True)
        if fi % 24 == 0:
            print(f"frame {fi}/{n_frames}", flush=True)

# ======================================================================= fase 3: subtítulos + vídeo
def encode():
    from PIL import Image, ImageDraw, ImageFont
    tl = json.load(open(os.path.join(WORK, "timeline.json")))
    segs, total = tl["segs"], tl["total"]
    W, H = 1080, 1920
    F = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Black.otf", s)
    fdir = os.path.join(WORK, "frames")
    n_frames = int(total * FPS)
    vid = os.path.join(WORK, "video.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", vid],
                         stdin=subprocess.PIPE)
    last = None
    for fi in range(n_frames):
        T = fi / FPS
        path = os.path.join(fdir, f"f{fi:05d}.png")
        if os.path.exists(path):
            last = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
        img = last.copy()
        d = ImageDraw.Draw(img)
        seg = None
        for s in segs:
            if s["start"] - .05 <= T <= s["start"] + s["dur"] + .15: seg = s
        if seg and seg["words"]:
            cur = None
            for wd, a, b in seg["words"]:
                if T >= a: cur = (wd, a, b)
            if cur and (T <= cur[2] + .25 or cur is seg["words"][-1]):
                wd, a, b = cur
                pop = min(1, (T - a) / .08)
                is_h = "HUSS" in wd.upper()
                txt = "HUSS!" if is_h else wd.strip(".,:!?").lower()
                sz = int((130 if is_h else 104) * (1.22 - .22 * pop))
                d.text((W / 2, 1240), txt, font=F(sz), fill=(255, 235, 60), anchor="mm", stroke_width=13, stroke_fill=(20, 20, 20))
        p.stdin.write(img.tobytes())
        if fi % 240 == 0: print(f"encode {fi}/{n_frames}", flush=True)
    p.stdin.close(); p.wait()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", os.path.join(WORK, "mix.wav"), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", OUT], check=True)
    print("OK ->", OUT)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "prep": prep(sys.argv[sys.argv.index("--voice") + 1])
    elif mode == "render": render()
    elif mode == "encode": encode()
