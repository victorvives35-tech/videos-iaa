#!/usr/bin/env python3
"""Historia 3D: MAYOR FOR A DAY — búsqueda de la llave dorada por todo el pueblo.

Usa world3d.py (ciudad 3D) y el pipeline de huss_counter.py (audio, subtítulos, codificación).
  python3 mayor_day.py prep --voice VOZ.onnx
  python3 mayor_day.py render        (reanudable; HC_PREVIEW=1 para vista previa)
  python3 mayor_day.py encode
"""
import json, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import huss_counter as hc

hc.WORK = os.environ.get("HC_WORK", "/tmp/claude-0/-home-user-videos-iaa/ff2cc793-9d09-5acb-b247-6c15a06ec93f/scratchpad/md")
hc.OUT = os.path.join(HERE, "mayor_day.mp4")
FPS, RES = hc.FPS, hc.RES

SCRIPT = [
    ("In this town, once a year, the mayor hides a golden key somewhere in town.", "aerial", None),
    ("Whoever finds it... becomes mayor for one whole day.", "mayor_key", None),
    ("This year, everybody was looking.", "search", None),
    ("People dug holes. People climbed trees. One guy checked under his own hat.", "search_b", None),
    ("I checked the pool. Only floaties. And one very surprised duck.", "pool", None),
    ("I checked the basketball court. I made the best shot of my life... no key.", "court", None),
    ("I checked the pizza shop. I ate eleven slices. For research.", "pizza", None),
    ("The arcade? I lost all my money. Still no key.", "arcade", None),
    ("Then I saw grandma at the bank... with a golden key around her neck!", "bank", None),
    ("I ran up the stairs and said:", "bank_huss", "solo", 3),
    ("She said: sweetie, that's my house key.", "bank_b", None),
    ("Then, the clock tower started to glow.", "glow", None),
    ("The key was inside the clock! So I climbed. And climbed. And climbed.", "climb", None),
    ("The whole town was watching from below.", "below", None),
    ("At the very top, I grabbed the key... and screamed:", "top", "solo", 6),
    ("I was mayor for one day!", "mayor_me", None),
    ("My first law: everybody has to say it before breakfast.", "law1", "crowd", 6),
    ("My second law: pizza is free. Forever.", "law2", None),
    ("My third law: grandma has to come to every pool party.", "law3", None),
    ("At midnight, the real mayor came back. He looked at the town... and said:", "end", "deep", 3),
]

def ease(u): u = max(0., min(1., u)); return u * u * (3 - 2 * u)
def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))

# ======================================================================= render
def render():
    import bpy
    import world3d as w
    tl = json.load(open(os.path.join(hc.WORK, "timeline.json")))
    segs, total = tl["segs"], tl["total"]
    preview = os.environ.get("HC_PREVIEW")
    fdir = os.path.join(hc.WORK, "preview" if preview else "frames"); os.makedirs(fdir, exist_ok=True)
    only = set(int((s["start"] + (s["dur"] + .2) * .6) * FPS) for s in segs
               if not os.environ.get("HC_ONLY") or s["scene"] in os.environ["HC_ONLY"].split(",")) if preview else None

    w.reset(); env = w.setup_scene((270, 480) if preview else RES, 4 if preview else 10); tower = w.build_city()
    cam = env["cam"]
    C = {}
    C["me"] = w.Char("me", (40, 90, 210), (40, 90, 210), hat="huss", jersey="HUSS", counter=False)
    C["gran"] = w.Char("gran", (175, 95, 165), (120, 70, 120), bun=True, glasses=True, counter=False)
    C["mayor"] = w.Char("mayor", (25, 25, 30), (25, 25, 30), tophat=True, counter=False)
    pal = [((235, 130, 60), (40, 50, 90), (35, 25, 20)), ((60, 190, 180), (50, 60, 100), (120, 70, 40)),
           ((150, 90, 220), (40, 40, 60), (20, 20, 20)), ((120, 200, 90), (70, 50, 40), (200, 60, 40)),
           ((250, 210, 70), (60, 60, 140), (240, 200, 120)), ((230, 80, 110), (40, 40, 50), (60, 40, 20)),
           ((255, 150, 40), (30, 40, 80), (90, 60, 30)), ((90, 160, 250), (240, 120, 60), (140, 90, 40))]
    NPC = []
    for i, (t_, l_, h_) in enumerate(pal):
        n = f"n{i}"; C[n] = w.Char(n, t_, l_, hair=h_, counter=False, scale=.75 if i == 7 else 1.0); NPC.append(n)

    # --- utilería
    me_head = C["me"].head
    tophat = [w.box("me_brim", (1.7, 1.6, .1), (0, 0, 1.55), (20, 20, 25), .03, me_head),
              w.box("me_top", (1.1, 1.0, 1.1), (0, 0, 2.1), (20, 20, 25), .05, me_head),
              w.box("me_band", (1.12, 1.02, .2), (0, 0, 1.7), (190, 30, 40), .02, me_head)]
    key = w.empty("key")
    bpy.ops.mesh.primitive_torus_add(major_radius=.45, minor_radius=.12, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
    kr = bpy.context.object; kr.parent = key; kr.data.materials.append(w.mat((255, 200, 50), .15, emit=1.5))
    w.box("keyshaft", (.18, .14, 1.3), (0, 0, -1.05), (255, 200, 50), .03, key, rough=.15, emit=1.5)
    w.box("keytooth", (.4, .14, .18), (.25, 0, -1.55), (255, 200, 50), .03, key, rough=.15, emit=1.5)
    key_parts = [key] + list(key.children)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.55, location=(0, 0, 0)); ball = bpy.context.object
    ball.data.materials.append(w.mat((240, 120, 40), .6))
    duck = w.empty("duck")
    w.box("duckb", (.9, .7, .6), (0, 0, .3), (255, 215, 40), .25, duck)
    w.box("duckh", (.5, .5, .5), (.35, 0, .8), (255, 215, 40), .2, duck)
    w.box("duckbk", (.3, .25, .12), (.65, 0, .75), (255, 140, 30), .04, duck)
    pizza_box = w.box("pizzabox", (1.6, .2, 1.6), (0, 0, 0), (230, 200, 150), .03)
    pizza_txt = w.text("pizzatxt", "11", .6, (200, 40, 40), (0, -.12, 0), pizza_box, .02); pizza_txt.rotation_euler = (math.radians(90), 0, 0)
    conf = []
    rnd = random.Random(5)
    for q in range(70):
        conf.append(w.box(f"conf{q}", (.18, .05, .28), (0, 0, -50), rnd.choice(w.HOUSE_COLS + [(255, 80, 120), (80, 200, 255)]), 0))
    props = key_parts + [ball, duck, pizza_box, pizza_txt] + list(duck.children) + tophat + conf
    tower_glow_mat = (tower["face"], tower["face"].data.materials[0])

    def hide_props():
        for o in props: o.hide_render = True
    def show(o, loc=None, rot=None):
        o.hide_render = False
        for c in o.children_recursive: c.hide_render = False
        if loc is not None: o.location = loc
        if rot is not None: o.rotation_euler = rot
    def show_key(loc, spin_t):
        show(key, loc, (0, 0, spin_t * 2.5))
    def confetti(T, center, h=12):
        for q, o in enumerate(conf):
            r = random.Random(q)
            x = center[0] + r.uniform(-8, 8); y = center[1] + r.uniform(-6, 6)
            z = h - ((T * r.uniform(2, 4) + r.uniform(0, h)) % h)
            o.hide_render = False; o.location = (x, y, z); o.rotation_euler = (T * 3 + q, q, T * 2)

    def hide_all():
        for ch in C.values(): ch.pose(visible=False)
        hide_props()
    hat_on = [False]
    cap_objs = [bpy.data.objects[n] for n in ("me_cap", "me_peak", "me_H")]
    def put(name, loc, yaw=None, face="smile", arms="down", walk=0., t=0., head_yaw=0., jump=0., face_cam=False, z=.18):
        ch = C[name]
        if face_cam:
            dx, dy = cam.location.x - loc[0], cam.location.y - loc[1]
            yaw = math.degrees(math.atan2(dx, -dy))
        ch.pose((loc[0], loc[1], z), yaw if yaw is not None else 0, walk=walk, t=t, arms=arms, face=face, head_yaw=head_yaw, jump=jump)
        if name == "me":
            for o in tophat: o.hide_render = not hat_on[0]
            for o in cap_objs: o.hide_render = hat_on[0]
    def face_to(x, y, tx, ty): return math.degrees(math.atan2(tx - x, -(ty - y)))
    def crowd_walk(T, n=8, y0=12, spread=40, run=False, lanes=(-7.6, 7.6, -6.5, 6.8, -2.8, 3.0, -7.2, 7.2)):
        for i, nm in enumerate(NPC[:n]):
            sp = 2.4 if not run else 6.0
            y = y0 + (i * 9.3 + 6) % spread - (T * sp) % spread
            put(nm, (lanes[i % len(lanes)], y), 0, face="laugh" if run else "smile", arms="up" if run else "down",
                walk=1.0 if not run else 1.7, t=T * (1.8 if run else 1) + i)
    def hit_of(seg, T):
        hits = seg["hits"]
        if not hits or T < hits[0] - .02: return -1, 0.
        k = max(i for i, h in enumerate(hits) if T >= h - .02)
        return k, max(0., 1 - (T - hits[k] + .02) / .18)
    def shake(e, a, T): return (e[0] + a * math.sin(T * 47), e[1], e[2] + a * math.cos(T * 53))
    def sky_day(): w.set_sky(env, (25, 130, 255), (160, 225, 255), (1, .95, .88), 5.0, 1.0); w.set_night(0)
    def sky_gold(): w.set_sky(env, (50, 110, 230), (255, 190, 130), (1, .8, .6), 4.5, 1.0); w.set_night(.3)
    def sky_night(): w.set_sky(env, (20, 20, 70), (90, 50, 130), (.6, .6, 1), 1.2, .5); w.set_night(1)
    def clock_glow(a):
        f = tower["face"]
        f.data.materials[0] = w.mat((255, 235, 140), .3, emit=6 * a, name=f"clockglow{round(a, 1)}") if a > .02 else tower_glow_mat[1]
    def clock_hands(T, fast=False):
        a = T * (6 if fast else 1.5)
        tower["minute"].rotation_euler = (0, a, 0); tower["hour"].rotation_euler = (0, a / 12 + 1, 0)

    TY = 145.0  # torre
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
        sc = seg["scene"]; k, hit = hit_of(seg, T)
        hide_all(); sky_day(); clock_glow(0); clock_hands(T)
        hat_on[0] = sc in ("mayor_me", "law1", "law2", "law3")

        if sc == "aerial":
            # vuelo de dron desde lo alto del pueblo hasta la plaza
            v = ease(u)
            eye = lerp((-35, -55, 85), (2, -2, 8), v); tgt = lerp((0, 70, 0), (0, 20, 5), v)
            w.look_at(cam, eye, tgt)
            crowd_walk(T)
        elif sc == "mayor_key":
            # escalinata del banco: el alcalde enseña la llave
            mx, my = -13.2, 42
            w.look_at(cam, lerp((-3, 36, 4.5), (-5, 39, 5.2), ease(u)), (mx, my, 5.5))
            put("mayor", (mx, my), face_cam=True, face="laugh", arms="up", t=T, z=1.3)
            show_key((mx, my, 9.6 + .3 * math.sin(T * 3)), T)
        elif sc == "search":
            v = ease(u)
            w.look_at(cam, lerp((25, -10, 40), (12, 0, 18), v), (0, 30, 0))
            crowd_walk(T, run=True, spread=50)
        elif sc == "pool":
            px, py = 18, 44
            w.look_at(cam, lerp((9, 31, 6.5), (10.5, 33, 5.5), ease(u)), (px - 1, py, 2))
            put("me", (15, 38.6), face_cam=True, face="shock" if u > .55 else "smile", t=T, arms="out" if u > .55 else "down")
            show(duck, (px + 1.5 + math.sin(T) * .5, py + .5, .45), (0, 0, T))
            if u > .55: duck.location.z = .45 + abs(math.sin(T * 10)) * .4
        elif sc == "court":
            cx, cy = 19, 22
            hx, hy, hz = cx, cy + 9.2, 6.2
            sx, sy = cx - 1, cy + 1
            w.look_at(cam, (cx + 6, cy - 8, 6.5), (cx - 1, cy + 5, 4))
            v = min(1, max(0, (u - .25) / .45))
            put("me", (sx, sy), face_to(sx, sy, hx, hy), face="laugh" if v >= 1 else "smile", arms="up" if 0 < v < .3 or v >= 1 else "down", t=T,
                jump=1.0 * math.sin(min(1, v * 3) * math.pi) if v < .34 else 0)
            if v <= 0: show(ball, (sx + .9, sy, 3.6))
            elif v < 1:
                bx = sx + (hx - sx) * v; by = sy + (hy - sy) * v; bz = 6 + (hz - 6) * v + 6 * math.sin(v * math.pi)
                show(ball, (bx, by, bz))
            else:
                show(ball, (hx, hy, max(.6, hz - (u - .7) * 25)))
                confetti(T, (cx, cy + 4), 9)
        elif sc == "pizza":
            sx, sy = -11, 16
            w.look_at(cam, lerp((2, 9, 4.6), (0, 10.5, 4.6), ease(u)), (sx, sy + .5, 3.8))
            put("me", (sx + 1.8, sy - 1), face_cam=True, face="laugh", t=T, jump=abs(math.sin(T * 3)) * .2)
            show(pizza_box, (sx + 3.2, sy - 1.6, 3.2), (0, 0, math.radians(30)))
            pizza_txt.data.body = str(min(11, 1 + int(u * 14)))
        elif sc == "arcade":
            sx, sy = -11, 25
            w.look_at(cam, lerp((1, 18, 4), (-1, 19.5, 4.4), ease(u)), (sx, sy, 3.6))
            put("me", (sx + 1.8, sy - .5), face_cam=True, face="sad" if u > .4 else "laugh", t=T,
                arms="out" if u > .4 else "down")
        elif sc in ("bank", "bank_huss", "bank_b"):
            gx, gy = -13.2, 42
            show_key((gx + .62, gy, 5.05), 0)
            if sc == "bank":
                w.look_at(cam, lerp((2, 34, 7), (-4, 37, 5.5), ease(u)), (gx, gy + 1, 4.5))
                put("gran", (gx, gy), face_cam=True, face="smile", t=T, z=1.3)
                put("me", (-7.5, 46), face_to(-7.5, 46, gx, gy), face="shock" if u > .5 else "smile", t=T)
            elif sc == "bank_huss":
                z_me = 1.3
                w.look_at(cam, shake((-4, 37.5, 5.2), .15 * hit, T), (gx + 1, gy + 1.5, 5.2))
                put("gran", (gx, gy), face_cam=True, face="shock" if k >= 0 else "smile", t=T, z=1.3)
                put("me", (gx + 2.2, gy + 2.6), face_to(gx + 2.2, gy + 2.6, gx, gy), face="yell" if hit > .2 else "smile",
                    arms="out" if hit > .1 else "down", t=T, z=.18)
            else:
                w.look_at(cam, (gx + 7, gy - 3, 5.6), (gx + 1, gy + 1.3, 5.2))
                put("gran", (gx, gy), face_cam=True, face="laugh", arms="wave", t=T, z=1.3)
                put("me", (gx + 2.2, gy + 2.6), face_to(gx + 2.2, gy + 2.6, gx, gy), face="sad", t=T, z=.18)
            key.location = (gx + .62, gy, 1.3 + 3.75); key.rotation_euler = (0, 0, math.radians(90))
        elif sc == "glow":
            clock_glow(ease(u)); sky_gold()
            v = ease(u)
            w.look_at(cam, lerp((2, 60, 5), (3, 110, 14), v), (0, TY, 18))
            put("me", (2, 70 + 40 * v), 180, face="shock", walk=1, t=T * 1.5)
        elif sc == "climb":
            clock_glow(1); sky_gold()
            z = 1 + 19 * ease(u)
            w.look_at(cam, (5, TY - 12, z - 2), (0, TY - 2.6, z + 2.5))
            put("me", (0, TY - 3.1), 180, face="yell", arms="up" if int(T * 4) % 2 else "out", t=T, z=z, walk=.8)
        elif sc == "top":
            clock_glow(1); sky_gold()
            ang = math.radians(-150 + 70 * ease(u))
            r = 16 if k < 0 else 12
            eye = (r * math.sin(ang), TY + r * math.cos(ang), 30)
            w.look_at(cam, shake(eye, .3 * hit, T), (0, TY - 3.0, 26))
            put("me", (0, TY - 3.0), face_cam=True, face="yell" if hit > .2 else "laugh", arms="up", t=T, z=23)
            show_key((0, TY - 3.0, 23 + 7.4), T)
        elif sc == "mayor_me":
            mx, my = -13.2, 42
            w.look_at(cam, lerp((-2, 34, 4), (-5, 38, 5), ease(u)), (mx, my, 5.6))
            put("me", (mx, my), face_cam=True, face="laugh", arms="up", t=T, z=1.3, jump=abs(math.sin(T * 5)) * .5)
            for o in tophat: o.hide_render = False
            for i, nm in enumerate(NPC[:6]):
                x = -9.5 + (i % 3) * 1.8; y = 45 + (i // 3) * 2.6
                put(nm, (x, y), face_to(x, y, mx, my), face="laugh", arms="up", t=T + i, jump=abs(math.sin(T * 5 + i)) * .5)
            confetti(T, (mx - 1, my + 6), 12)
        elif sc == "search_b":
            w.look_at(cam, lerp((-8, 2, 1.2), (-6, 4, 2.0), ease(u)), (0, 18, 4))
            for i, nm in enumerate(NPC[:6]):
                x = [-7.5, 7.5, -3, 3.5, -6.5, 6.8][i]; y = 10 + i * 3
                put(nm, (x, y), face_cam=True, face="shock" if i % 2 else "laugh", arms="up" if i % 2 else "out", t=T + i, jump=abs(math.sin(T * 4 + i)) * .6)
            put("n6", (-2.5, 9), face_cam=True, face="shock", arms="up", t=T)
        elif sc == "below":
            clock_glow(1); sky_gold()
            w.look_at(cam, (0, TY - 4, 31), (0, TY - 40, 0))
            for i, nm in enumerate(NPC):
                x = -6 + (i % 4) * 4; y = TY - 24 - (i // 4) * 4
                put(nm, (x, y), face_to(x, y, 0, TY), face="shock", arms="up", t=T + i, jump=abs(math.sin(T * 4 + i)) * .4)
            put("gran", (0, TY - 20), face_to(0, TY - 20, 0, TY), face="laugh", arms="wave", t=T)
        elif sc == "law3":
            px, py = 18, 44
            w.look_at(cam, lerp((8, 33, 7), (10, 35, 5.5), ease(u)), (px, py, 2))
            put("gran", (16, 38.7), face_cam=True, face="laugh", arms="up", t=T, jump=abs(math.sin(T * 5)) * .8)
            for i, nm in enumerate(NPC[:4]):
                x = 13 + i * 3; y = 38.4 if i % 2 else 49.5
                put(nm, (x, y), face_cam=True, face="laugh", arms="up", t=T + i, jump=abs(math.sin(T * 5 + i)) * .6)
            put("me", (11, 40), face_cam=True, face="laugh", arms="wave", t=T)
            show(duck, (px + 1.5 + math.sin(T) * .5, py + .5, .45), (0, 0, T))
            confetti(T, (px, py), 10)
        elif sc == "law1":
            w.look_at(cam, shake((0, 2, 5), .2 * hit, T), (0, 16, 5))
            for i, nm in enumerate(NPC):
                x = -7 + (i % 4) * 4.5; y = 12 + (i // 4) * 4
                put(nm, (x, y), face_cam=True, face="yell" if hit > .2 else "smile", arms="up" if hit > .1 else "down", t=T + i, jump=.6 * hit)
            put("me", (0, 9), face_cam=True, face="yell" if hit > .2 else "laugh", arms="up", t=T, jump=.6 * hit)
            for o in tophat: o.hide_render = False
        elif sc == "law2":
            sx, sy = -11, 16
            w.look_at(cam, lerp((8, 6, 6), (4, 9, 5), ease(u)), (sx, sy, 3))
            for i, nm in enumerate(NPC[:6]):
                x = -6 + (i % 3) * 1.8; y = 10 + (i // 3) * 2.4 + 2 * math.sin(T + i)
                put(nm, (x, y), face_to(x, y, sx, sy), face="laugh", walk=1, t=T * 1.5 + i)
            put("me", (-2, 13), face_cam=True, face="laugh", arms="wave", t=T)
            for o in tophat: o.hide_render = False
            show(pizza_box, (-2.8 + .0, 12, 6.8 + .3 * math.sin(T * 3)), (0, 0, T))
            pizza_txt.data.body = "FREE"
        elif sc == "end":
            sky_night()
            w.look_at(cam, shake((0, 3, 4.6), .2 * hit, T), (0, 9, 5.8))
            put("mayor", (0, 9), face_cam=True, face="yell" if hit > .2 else "flat", arms="out" if hit > .1 else "down", t=T)
            for i, nm in enumerate(NPC[:4]):
                x = [-5, -3, 3, 5][i]
                put(nm, (x, 14), face_cam=True, face="shock" if k >= 0 else "smile", arms="up" if hit > .1 else "down", t=T + i)

        env["scene"].render.filepath = path
        bpy.ops.render.render(write_still=True)
        if fi % 24 == 0: print(f"frame {fi}/{n_frames}", flush=True)

if __name__ == "__main__":
    hc.SCRIPT = SCRIPT
    mode = sys.argv[1]
    if mode == "prep": hc.prep(sys.argv[sys.argv.index("--voice") + 1])
    elif mode == "render": render()
    elif mode == "encode": hc.encode()
