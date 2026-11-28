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

def build_city(seed=3):
    TREES.clear(); WINDOWS.clear(); LAMPS.clear()
    rnd = random.Random(seed)
    L = 150
    # suelo: hierba, aceras, bordillos, carretera, líneas
    box("grass", (120, L + 60, .2), (0, L / 2 - 10, -.1), (110, 185, 90), 0, rough=.95)
    box("road", (10, L + 40, .22), (0, L / 2 - 10, -.08), (70, 72, 80), 0, rough=.9)
    for side in (-1, 1):
        box(f"walk{side}", (4.5, L + 40, .35), (side * 7.25, L / 2 - 10, 0), (215, 215, 220), 0, rough=.9)
        box(f"curb{side}", (.35, L + 40, .42), (side * 5.0, L / 2 - 10, 0), (190, 190, 195), .03)
        for q in range(int((L + 40) / 3)):
            box(f"tile{side}_{q}", (4.45, .06, .02), (side * 7.25, -25 + q * 3, .18), (195, 195, 200), 0)
    for q in range(int((L + 40) / 6)):
        box(f"dash{q}", (.25, 2.2, .02), (0, -25 + q * 6, .04), (250, 220, 90), 0)
    # casas, árboles, farolas
    y = -20
    i = 0
    while y < L - 20:
        for side in (-1, 1):
            w, d, h = rnd.uniform(6, 8), rnd.uniform(6.5, 8.5), rnd.uniform(4, 6.5)
            house(side * (14 + w / 2), y + rnd.uniform(-1, 1), w, d, h, rnd.choice(HOUSE_COLS), face=-side, seed=i * 2 + (side > 0))
            tree(side * 10.5, y + 4.5, rnd.uniform(.9, 1.15), seed=i * 2 + (side > 0) + 100)
            if i % 2 == 0: lamp(side * 5.6, y - 2)
        y += 11; i += 1
    tower = clock_tower(L - 5)
    # pueblo de fondo: bloques lejanos
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
