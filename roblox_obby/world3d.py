"""Mundo 3D (Blender/bpy) estilo Roblox: calle con casas, árboles, torre del reloj y personajes de bloques.

Se usa desde huss_counter.py. Todo se construye por código; solo funciona el motor CYCLES en este entorno.
"""
import math, random
import bpy
from mathutils import Vector

FONT_PATH = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
_FONT = None
_MATS = {}

# ------------------------------------------------------------------ utilidades
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    global _FONT; _FONT = None

def font():
    global _FONT
    if _FONT is None:
        _FONT = bpy.data.fonts.load(FONT_PATH)
    return _FONT

def mat(rgb, rough=.65, emit=0.0, name=None):
    key = name or (tuple(round(c, 3) for c in rgb), rough, emit)
    if key in _MATS: return _MATS[key]
    m = bpy.data.materials.new(str(key))
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    col = tuple((c / 255) ** 2.2 if max(rgb) > 1 else c for c in rgb)  # sRGB -> lineal
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    _MATS[key] = m
    return m

def box(name, size, loc, rgb, bevel=.08, parent=None, rough=.65, emit=0.0, origin=None):
    """Caja con borde redondeado. origin: punto (relativo al centro) que será el pivote."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.object; o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if origin is not None:
        for v in o.data.vertices: v.co -= Vector(origin)
    o.location = loc
    if bevel:
        mod = o.modifiers.new("bev", "BEVEL"); mod.width = bevel; mod.segments = 2
    o.data.materials.append(mat(rgb, rough, emit))
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(o)
    o.location = loc
    if parent: o.parent = parent
    return o

def text(name, body, size, rgb, loc=(0, 0, 0), parent=None, extrude=.02, emit=0.0):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.font = font(); cu.size = size
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = extrude
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat(rgb, .4, emit))
    o.location = loc
    if parent: o.parent = parent
    return o

# ------------------------------------------------------------------ escena / luz
def setup_scene(res=(540, 960), samples=10):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 1; sc.cycles.transmission_bounces = 1
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "PNG"
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB"); bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Window"], sep.inputs[0]); nt.links.new(sep.outputs["Y"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs[1].default_value = 1.0
    sun_d = bpy.data.lights.new("sun", "SUN"); sun_d.energy = 4.5; sun_d.angle = math.radians(8)
    sun = bpy.data.objects.new("sun", sun_d); bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), math.radians(-25), math.radians(-35))
    cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 32
    cam = bpy.data.objects.new("cam", cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
    return dict(scene=sc, ramp=ramp, bg=bg, sun=sun, cam=cam)

def set_sky(env, top, bottom, sun_rgb=(1, .96, .9), sun_energy=4.0, ambient=1.0):
    r = env["ramp"].color_ramp
    r.elements[0].color = (*[(c / 255) ** 2.2 for c in bottom], 1); r.elements[1].color = (*[(c / 255) ** 2.2 for c in top], 1)
    env["bg"].inputs[1].default_value = ambient
    env["sun"].data.color = sun_rgb; env["sun"].data.energy = sun_energy

def look_at(cam, eye, target, roll=0.0):
    cam.location = eye
    d = Vector(target) - Vector(eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.rotation_euler.rotate_axis("Z", roll)

# ------------------------------------------------------------------ ciudad
HOUSE_COLS = [(235, 130, 110), (120, 175, 235), (250, 215, 120), (150, 210, 150), (210, 160, 225), (245, 170, 90), (240, 240, 235)]
TREES = []
WINDOWS = []
LAMPS = []

def tree(x, y, s=1.0, seed=0):
    rnd = random.Random(seed)
    box(f"trunk{seed}", (.6 * s, .6 * s, 3.2 * s), (x, y, 1.6 * s), (120, 80, 50), .05)
    leaves = []
    for q, (dx, dy, dz, r) in enumerate([(0, 0, 4.2, 2.6), (.9, .3, 5.4, 2.0), (-.8, -.4, 5.0, 2.1), (.1, -.2, 6.3, 1.6)]):
        g = rnd.uniform(-.08, .08)
        o = box(f"leaf{seed}_{q}", (r * s, r * s, r * .85 * s), (x + dx * s, y + dy * s, dz * s), (80, 165 + 30 * g * 10, 70), .35)
        leaves.append(o)
    TREES.append(leaves)

def house(x, y, w, d, h, rgb, face=1, seed=0):
    """face: +1 si la fachada mira a +X (casas a la izquierda de la calle), -1 a -X."""
    rnd = random.Random(seed)
    box(f"house{seed}", (w, d, h), (x, y, h / 2), rgb, .05, rough=.8)
    # tejado a dos aguas
    roof_h = 1.8
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(w, d) * .78, depth=roof_h, location=(x, y, h + roof_h / 2))
    r = bpy.context.object; r.rotation_euler[2] = math.radians(45); r.scale = (w / max(w, d), d / max(w, d), 1)
    r.data.materials.append(mat((150, 70, 60) if seed % 2 else (70, 80, 110), .7))
    fx = x + face * (w / 2 + .02)
    for q in range(2):
        for k in range(2 if h > 4.5 else 1):
            win = box(f"win{seed}_{q}_{k}", (.06, .9, .9), (fx, y - d / 4 + q * d / 2, 1.9 + k * 2.2), (170, 210, 240), .02, rough=.1)
            WINDOWS.append(win)
    box(f"door{seed}", (.06, .9, 1.9), (fx, y, .95), (120, 80, 50), .02)
    # valla
    for q in range(5):
        box(f"fence{seed}_{q}", (.12, .12, .9), (x + face * (w / 2 + 2.2), y - d / 2 + q * d / 4, .45), (245, 245, 240), .02)
    box(f"fenceb{seed}", (.08, d, .12), (x + face * (w / 2 + 2.2), y, .7), (245, 245, 240), .02)
    # buzón rojo
    if seed % 3 == 0:
        box(f"mpost{seed}", (.12, .12, 1.0), (x + face * (w / 2 + 2.7), y + d / 2 - .3, .5), (90, 90, 90), .02)
        box(f"mbox{seed}", (.35, .6, .4), (x + face * (w / 2 + 2.7), y + d / 2 - .3, 1.15), (215, 50, 50), .08)

def lamp(x, y):
    box(f"lamp{x}_{y}", (.18, .18, 5.0), (x, y, 2.5), (60, 60, 70), .03)
    bulb = box(f"bulb{x}_{y}", (.6, .6, .45), (x, y, 5.1), (255, 230, 170), .1, emit=0.0)
    LAMPS.append(bulb)

def clock_tower(y):
    x = 0
    box("tower", (5, 5, 22), (x, y, 11), (175, 95, 70), .1, rough=.85)
    for q in range(10):
        box(f"band{q}", (5.15, 5.15, .25), (x, y, 2 + q * 2), (150, 80, 60), .03)
    box("towertop", (5.6, 5.6, 1.0), (x, y, 22.5), (235, 235, 225), .1)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=4.2, depth=6, location=(x, y, 26))
    cone = bpy.context.object; cone.rotation_euler[2] = math.radians(45); cone.data.materials.append(mat((55, 70, 120), .6))
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.8, depth=.3, location=(x, y - 2.6, 18), rotation=(math.radians(90), 0, 0))
    face = bpy.context.object; face.data.materials.append(mat((245, 245, 235), .4, emit=.0))
    hands = empty("hands", (x, y - 2.8, 18))
    hh = box("hourhand", (.18, .06, 1.0), (0, 0, 0), (30, 30, 30), .02, parent=hands, origin=(0, 0, -.45))
    mh = box("minhand", (.12, .06, 1.5), (0, 0, 0), (30, 30, 30), .02, parent=hands, origin=(0, 0, -.7))
    hh.rotation_euler = (0, 0, 0); mh.rotation_euler = (0, 0, 0)
    glow = box("towerwin", (1.2, .06, 2.2), (x, y - 2.53, 3.0), (255, 200, 120), .02, emit=2.5)
    return dict(face=face, hour=hh, minute=mh, glow=glow)

def palm(x, y, s=1.0, seed=0):
    rnd = random.Random(seed)
    lean = rnd.uniform(-.35, .35)
    for q in range(7):  # tronco curvado por segmentos
        z = .5 + q * .95 * s
        box(f"ptr{seed}_{q}", (.55 * s, .55 * s, 1.0 * s), (x + lean * (q / 7) ** 2 * 3, y, z), (150, 105, 60) if q % 2 else (130, 90, 50), .08)
    tx, tz = x + lean * 3, .5 + 7 * .95 * s
    leaves = []
    for k in range(7):
        ang = k * 2 * math.pi / 7 + rnd.uniform(-.2, .2)
        o = box(f"frond{seed}_{k}", (3.4 * s, .9 * s, .14), (0, 0, 0), (60, 170, 70), .05, origin=(-1.7 * s, 0, 0))
        o.location = (tx, y, tz)
        o.rotation_euler = (0, math.radians(28), ang)
        leaves.append(o)
    box(f"coco{seed}", (.6 * s, .6 * s, .5 * s), (tx, y, tz - .3), (110, 80, 40), .2)
    TREES.append(leaves)

def mountains(L):
    rnd = random.Random(9)
    for q in range(14):
        x = -110 + q * 17 + rnd.uniform(-5, 5); y = L + 70 + rnd.uniform(0, 50)
        r = rnd.uniform(20, 34); hgt = rnd.uniform(22, 42)
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=r, depth=hgt, location=(x, y, hgt / 2 - 1))
        o = bpy.context.object; o.rotation_euler[2] = rnd.uniform(0, 1)
        o.data.materials.append(mat(rnd.choice([(70, 165, 80), (60, 150, 75), (85, 180, 90)]), .9))
    for q in range(10):  # colinas laterales
        for side in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=24, depth=rnd.uniform(14, 24), location=(side * 75, q * 22 - 10, 6))
            bpy.context.object.data.materials.append(mat((75, 170, 85), .9))

def bank(x, y, face):
    W_, D_ = 16, 13
    for q in range(3):  # escalinata
        box(f"bstep{q}", (W_ + 2 - q * .7, D_ + 2 - q * .7, .4), (x, y, .2 + q * .4), (245, 245, 240), .03)
    box("bankbody", (W_ - 2, D_ - 4, 9), (x - face * 1.5, y, 5.7), (250, 248, 235), .05)
    fx = x + face * (W_ / 2 - 2)
    for q in range(6):  # columnas
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=.55, depth=8, location=(fx, y - D_ / 2 + 1.5 + q * (D_ - 3) / 5, 5.2))
        bpy.context.object.data.materials.append(mat((250, 250, 245), .4))
    box("bankroof", (W_, D_, 1.0), (x, y, 9.7), (245, 240, 220), .05)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=D_ * .55, depth=2.6, location=(fx - face * .3, y, 11.4), rotation=(0, math.radians(90), 0))
    o = bpy.context.object; o.scale = (1, 1, .35); o.data.materials.append(mat((245, 240, 220), .4))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3.2, location=(x - face * 1.5, y, 10.3), segments=24, ring_count=12)
    dome = bpy.context.object; dome.data.materials.append(mat((255, 200, 60), .2))
    box("bankspike", (.3, .3, 2.6), (x - face * 1.5, y, 14.6), (255, 200, 60), .05, rough=.2)
    t = text("banksign", "HUSS BANK", 1.4, (255, 190, 40), (fx + face * .6, y, 9.7), extrude=.1)
    t.rotation_euler = (math.radians(90), 0, math.radians(90 * face))
    # tablón de cuentas
    box("board", (.2, 5, 3), (fx + face * .4, y, 3.4), (25, 30, 45), .05)
    for q, (nm, v) in enumerate([("HUSS", "$1,000,000"), ("LIKE", "$6,240"), ("BRO", "$4,880"), ("WOW", "$990")]):
        tt = text(f"brd{q}", f"{nm}  {v}", .38, (255, 215, 80), (fx + face * .52, y, 4.4 - q * .6), extrude=.01, emit=1.5)
        tt.rotation_euler = (math.radians(90), 0, math.radians(90 * face))

def shop(x, y, w, face, rgb, label, seed):
    box(f"shop{seed}", (w, 8, 5.2), (x, y, 2.6), (250, 250, 250), .05)
    fx = x + face * (w / 2 + .02)
    box(f"glass{seed}", (.08, 6.2, 2.8), (fx, y, 1.9), (150, 215, 245), .02, rough=.05)
    for q in range(8):  # toldo de rayas
        box(f"awn{seed}_{q}", (1.6, .8, .2), (fx + face * .8, y - 3.2 + q * .8 + .4, 3.7), rgb if q % 2 else (255, 255, 255), .03)
    box(f"signb{seed}", (.15, 6.5, 1.3), (fx + face * .05, y, 4.6), rgb, .05)
    t = text(f"sign{seed}", label, 1.0, (255, 255, 255), (fx + face * .16, y, 4.6), extrude=.05)
    t.rotation_euler = (math.radians(90), 0, math.radians(90 * face))
    rnd = random.Random(seed)
    for q in range(10):  # productos de colores tras el cristal
        box(f"prod{seed}_{q}", (.3, .45, .5), (fx - face * .3, y - 2.7 + q * .6, 1.2 + (q % 2) * .9), rnd.choice(HOUSE_COLS), .05)

def court(x, y, face):
    box("courtfloor", (14, 20, .1), (x, y, .05), (60, 130, 220), 0, rough=.4)
    box("courtkey", (5, 6, .11), (x, y + 7, .06), (245, 175, 60), 0, rough=.4)
    for (sx, sy, lx, ly) in [(14, .15, 0, 0), (14, .15, 0, 10), (14, .15, 0, -10), (.15, 20, 7, 0), (.15, 20, -7, 0)]:
        box(f"cl{sx}{sy}{lx}{ly}", (sx, sy, .12), (x + lx, y + ly, .07), (255, 255, 255), 0)
    box("hoop_pole", (.4, .4, 7), (x, y + 10.5, 3.5), (60, 60, 70), .05)
    box("backboard", (3.6, .15, 2.2), (x, y + 9.9, 7), (255, 255, 255), .05)
    bpy.ops.mesh.primitive_torus_add(major_radius=.7, minor_radius=.07, location=(x, y + 9.2, 6.2))
    bpy.context.object.data.materials.append(mat((240, 110, 30), .4))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.6, location=(x - 2, y + 2, .6))
    bpy.context.object.data.materials.append(mat((240, 120, 40), .6))
    for q in range(3):  # gradas
        box(f"bleach{q}", (1.0, 10, .6 + q * .6), (x + face * -(8 + q), y, .3 + q * .3), (200, 200, 210), .03)

def pool(x, y):
    box("poolrim", (12, 9, .4), (x, y, .2), (245, 245, 245), .05)
    box("poolwater", (11, 8, .42), (x, y, .22), (60, 190, 240), 0, rough=.05)
    for q, col in enumerate([(255, 90, 120), (255, 210, 60), (90, 220, 140)]):
        bpy.ops.mesh.primitive_torus_add(major_radius=.9, minor_radius=.3, location=(x - 3 + q * 3, y + (q % 2) * 2 - 1, .55))
        bpy.context.object.data.materials.append(mat(col, .3))
    for q in range(2):  # sombrillas
        box(f"umb_p{q}", (.15, .15, 3), (x - 7 + q * 14, y + 3, 1.5), (240, 240, 240), .02)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=2.2, depth=1, location=(x - 7 + q * 14, y + 3, 3.2))
        bpy.context.object.data.materials.append(mat([(255, 80, 120), (60, 180, 250)][q], .5))

def string_lights(y, z=9.8, width=11.6):
    cols = [(255, 90, 90), (255, 220, 80), (90, 220, 140), (90, 170, 255), (240, 120, 255)]
    n = 16
    for q in range(n + 1):
        x = -width / 2 + q * width / n
        sag = .7 * (1 - (2 * q / n - 1) ** 2)
        b = box(f"sl{y}_{q}", (.28, .28, .34), (x, y, z - sag), cols[q % 5], .1, emit=4.0)
    for q in range(n):  # banderines
        x = -width / 2 + (q + .5) * width / n
        sag = .7 * (1 - (2 * (q + .5) / n - 1) ** 2)
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=.22, depth=.02, location=(x, y + .3, z - sag - .3), rotation=(math.radians(90), math.radians(180), 0))
        bpy.context.object.data.materials.append(mat(cols[(q + 2) % 5], .6))

def crosswalk(y):
    for q in range(6):
        box(f"cw{y}_{q}", (1.0, 3.2, .03), (-4 + q * 1.6, y, .05), (250, 250, 250), 0)

def build_city(seed=3):
    TREES.clear(); WINDOWS.clear(); LAMPS.clear()
    rnd = random.Random(seed)
    L = 150
    box("grass", (200, L + 120, .2), (0, L / 2 + 10, -.1), (105, 195, 85), 0, rough=.95)
    box("road", (11, L + 40, .22), (0, L / 2 - 10, -.08), (75, 80, 95), 0, rough=.85)
    for side in (-1, 1):
        box(f"walk{side}", (4.5, L + 40, .35), (side * 7.75, L / 2 - 10, 0), (232, 232, 238), 0, rough=.8)
        box(f"curb{side}", (.35, L + 40, .42), (side * 5.5, L / 2 - 10, 0), (205, 205, 210), .03)
        for q in range(int((L + 40) / 3)):
            box(f"tile{side}_{q}", (4.45, .06, .02), (side * 7.75, -25 + q * 3, .18), (210, 210, 218), 0)
    for q in range(int((L + 40) / 6)):
        box(f"dash{q}", (.25, 2.2, .02), (0, -25 + q * 6, .04), (255, 215, 70), 0)
    crosswalk(5); crosswalk(48)
    mountains(L)
    # hitos del pueblo (zona que más sale en cámara)
    shop(-14.5, 16, 7, 1, (255, 90, 120), "PIZZA", 1)
    shop(-14.5, 25, 7, 1, (90, 170, 255), "ARCADE", 2)
    bank(-21, 42, 1)
    court(19, 22, -1)
    pool(18, 44)
    shop(14.5, 60, 7, -1, (255, 190, 40), "CANDY", 3)
    for y in (12, 30, 52):
        string_lights(y)
    # casas en el resto
    y = -20; i = 0
    while y < L - 20:
        for side in (-1, 1):
            busy = (side < 0 and 10 < y < 52) or (side > 0 and 10 < y < 66)
            if not busy:
                w, d, h = rnd.uniform(6, 8), rnd.uniform(6.5, 8.5), rnd.uniform(4, 6.5)
                house(side * (14 + w / 2), y + rnd.uniform(-1, 1), w, d, h, rnd.choice(HOUSE_COLS), face=-side, seed=i * 2 + (side > 0))
            if side < 0 and 10 < y + 4.5 < 54: pass  # fachadas de tiendas y banco despejadas
            elif (i + (side > 0)) % 2 == 0: palm(side * 10.8, y + 4.5, rnd.uniform(.95, 1.15), seed=i * 2 + (side > 0) + 100)
            else: tree(side * 10.8, y + 4.5, rnd.uniform(.9, 1.1), seed=i * 2 + (side > 0) + 100)
            if i % 2 == 0: lamp(side * 6.0, y - 2)
        y += 11; i += 1
    tower = clock_tower(L - 5)
    for q in range(16):
        box(f"far{q}", (6, 6, rnd.uniform(4, 9)), (rnd.uniform(-60, 60), L + 20 + rnd.uniform(0, 30), 3), rnd.choice(HOUSE_COLS), .1)
    return tower

def set_season(season):
    """0 verano, 1 otoño, 2 invierno."""
    cols = [(80, 175, 70), (235, 140, 50), (240, 245, 250)]
    for leaves in TREES:
        for o in leaves:
            o.data.materials[0] = mat(cols[season], .8, name=f"leaf{season}")

def set_night(amount):
    for w in WINDOWS:
        w.data.materials[0] = mat((255, 210, 130), .3, emit=3.0 * amount, name=f"winN{round(amount, 1)}") if amount > .05 else mat((170, 210, 240), .1)
    for b in LAMPS:
        b.data.materials[0] = mat((255, 230, 170), .3, emit=12.0 * amount, name=f"lampN{round(amount, 1)}")

# ------------------------------------------------------------------ personajes
SKIN = (255, 205, 160)

class Char:
    def __init__(self, name, torso, legs, skin=SKIN, hair=None, hat=None, jersey=None, glasses=False, bun=False,
                 tophat=False, counter=True, scale=1.0):
        self.root = empty(name)
        self.root.scale = (scale, scale, scale)
        r = self.root
        self.legL = box(name + "_legL", (.95, 1, 2), (-.5, 0, 2), legs, .06, r, origin=(0, 0, 1))
        self.legR = box(name + "_legR", (.95, 1, 2), (.5, 0, 2), legs, .06, r, origin=(0, 0, 1))
        self.torso = box(name + "_torso", (2, 1, 2), (0, 0, 3), torso, .08, r)
        self.armL = box(name + "_armL", (.95, 1, 2), (-1.5, 0, 4), skin, .06, r, origin=(0, 0, 1))
        self.armR = box(name + "_armR", (.95, 1, 2), (1.5, 0, 4), skin, .06, r, origin=(0, 0, 1))
        self.head = empty(name + "_headp", (0, 0, 4.05), r)
        h = self.head
        box(name + "_head", (1.3, 1.2, 1.25), (0, 0, .65), skin, .18, h)
        # cara (mira hacia -Y)
        self.eyeL = box(name + "_eyeL", (.16, .05, .26), (-.28, -.6, .78), (25, 25, 30), .03, h)
        self.eyeR = box(name + "_eyeR", (.16, .05, .26), (.28, -.6, .78), (25, 25, 30), .03, h)
        self.brL = box(name + "_brL", (.32, .05, .07), (-.28, -.6, 1.02), (60, 40, 30), .01, h)
        self.brR = box(name + "_brR", (.32, .05, .07), (.28, -.6, 1.02), (60, 40, 30), .01, h)
        self.mouth = box(name + "_mouth", (.5, .05, .08), (0, -.6, .38), (40, 20, 20), .02, h)
        for e in (-1, 1):
            box(name + f"_cheek{e}", (.2, .04, .1), (e * .45, -.6, .52), (255, 160, 150), .02, h)
        if hair:
            box(name + "_hair", (1.42, 1.32, .4), (0, .05, 1.28), hair, .12, h)
            box(name + "_hairb", (1.42, .4, 1.0), (0, .52, .85), hair, .1, h)
        if bun:
            box(name + "_bun", (.7, .7, .6), (0, .1, 1.6), (205, 205, 210), .25, h)
        if glasses:
            for e in (-1, 1):
                box(name + f"_gl{e}", (.38, .04, .34), (e * .28, -.64, .78), (40, 40, 40), .03, h)
        if hat == "huss":
            box(name + "_cap", (1.45, 1.35, .45), (0, .02, 1.32), (35, 75, 195), .12, h)
            box(name + "_peak", (1.0, .7, .1), (.25, -.85, 1.12), (35, 75, 195), .05, h)
            t = text(name + "_H", "H", .42, (255, 205, 40), (0, -.69, 1.33), h, .02)
            t.rotation_euler = (math.radians(90), 0, 0)
        if tophat:
            box(name + "_brim", (1.7, 1.6, .1), (0, 0, 1.32), (20, 20, 25), .03, h)
            box(name + "_top", (1.1, 1.0, 1.1), (0, 0, 1.9), (20, 20, 25), .05, h)
            box(name + "_band", (1.12, 1.02, .2), (0, 0, 1.5), (190, 30, 40), .02, h)
        if jersey:
            t = text(name + "_jersey", jersey, .48, (255, 205, 40), (0, -.52, 3.25), r, .03)
            t.rotation_euler = (math.radians(90), 0, 0)
        self.face = "smile"
        self.tall = tophat
        self.counter = None
        if counter:
            self.cbox = box(name + "_cbox", (2.3, .12, .9), (0, 0, 0), (30, 32, 40), .12, rough=.4)
            self.ctext = text(name + "_ctext", "0", .58, (245, 245, 245), (0, -.09, 0), self.cbox, .01, emit=1.5)
            self.ctext.rotation_euler = (math.radians(90), 0, 0)
            self.cbox.parent = None
            self.counter = True
        self.walk_phase = 0.0

    def set_counter(self, value, rgb=(245, 245, 245), visible=True, cam=None, emit=1.5, width=None):
        if not self.counter: return
        body = value if isinstance(value, str) else f"{value:,}"
        self.ctext.data.body = body
        self.ctext.data.materials[0] = mat(rgb, .4, emit, name=f"ct{rgb}{emit}")
        w = width or max(1.6, .42 * len(body) + .6)
        self.cbox.scale = (w / 2.3, 1, 1)
        self.ctext.scale = (2.3 / w, 1, 1)
        s = self.root.scale[0]
        L = self.root.location
        self.cbox.location = (L.x, L.y, L.z + (7.5 if self.tall else 6.6) * s)
        if cam is not None:
            dvec = cam.location - self.cbox.location; dvec.z = 0
            self.cbox.rotation_euler = (0, 0, math.atan2(dvec.x, -dvec.y))
        self.cbox.hide_render = not visible; self.ctext.hide_render = not visible
        self.cbox.scale = (w / 2.3 * s, s, s)

    def pose(self, loc=None, yaw=None, walk=0.0, t=0.0, arms="down", face=None, head_yaw=0.0, jump=0.0, visible=True):
        r = self.root
        r.hide_render = not visible
        for o in r.children_recursive: o.hide_render = not visible
        if loc is not None: r.location = (loc[0], loc[1], loc[2] + jump if len(loc) > 2 else jump)
        if yaw is not None: r.rotation_euler = (0, 0, math.radians(yaw))
        sw = math.sin(t * 9) * .7 * walk
        self.legL.rotation_euler = (sw, 0, 0); self.legR.rotation_euler = (-sw, 0, 0)
        if arms == "down":
            self.armL.rotation_euler = (-sw, 0, 0); self.armR.rotation_euler = (sw, 0, 0)
        elif arms == "up":
            self.armL.rotation_euler = (0, math.radians(150) + .1 * math.sin(t * 8), 0)
            self.armR.rotation_euler = (0, -math.radians(150) - .1 * math.sin(t * 8), 0)
        elif arms == "out":
            self.armL.rotation_euler = (math.radians(-80), 0, 0); self.armR.rotation_euler = (math.radians(-80), 0, 0)
        elif arms == "wave":
            self.armL.rotation_euler = (-sw, 0, 0)
            self.armR.rotation_euler = (0, -math.radians(140) - .35 * math.sin(t * 10), 0)
        elif arms == "point":
            self.armL.rotation_euler = (0, 0, 0); self.armR.rotation_euler = (math.radians(-85), 0, 0)
        elif arms == "panic":
            self.armL.rotation_euler = (0, math.radians(160 + 15 * math.sin(t * 14)), 0)
            self.armR.rotation_euler = (0, -math.radians(160 + 15 * math.sin(t * 14 + 1)), 0)
        self.head.rotation_euler = (0, 0, math.radians(head_yaw))
        if face: self.set_face(face, t)

    def set_face(self, face, t=0.0):
        m, eL, eR, bL, bR = self.mouth, self.eyeL, self.eyeR, self.brL, self.brR
        for e in (eL, eR): e.scale = (1, 1, 1)
        bL.rotation_euler = (0, 0, 0); bR.rotation_euler = (0, 0, 0); bL.location.z = bR.location.z = 1.02
        blink = (int(t * 10) % 37 == 0)
        if face == "smile": m.scale = (1.0, 1, 1.0); m.location.z = .38
        elif face == "flat": m.scale = (.8, 1, .7); m.location.z = .38
        elif face == "laugh": m.scale = (1.1, 1, 3.0); m.location.z = .36
        elif face == "shock":
            m.scale = (.5, 1, 3.2); m.location.z = .34
            for e in (eL, eR): e.scale = (1.2, 1, 1.25)
            bL.location.z = bR.location.z = 1.12
        elif face == "yell":
            m.scale = (1.2, 1, 4.2); m.location.z = .32
            bL.rotation_euler = (0, math.radians(20), 0); bR.rotation_euler = (0, math.radians(-20), 0)
        elif face == "sad":
            m.scale = (.7, 1, .7); m.location.z = .34
            bL.rotation_euler = (0, math.radians(-18), 0); bR.rotation_euler = (0, math.radians(18), 0)
        elif face == "angry":
            m.scale = (.8, 1, .8); m.location.z = .36
            bL.rotation_euler = (0, math.radians(22), 0); bR.rotation_euler = (0, math.radians(-22), 0)
        elif face == "closed":
            m.scale = (.6, 1, .6)
            for e in (eL, eR): e.scale = (1.3, 1, .25)
        if blink and face not in ("shock", "yell"):
            for e in (eL, eR): e.scale = (1.2, 1, .2)
