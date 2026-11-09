"""Panigale V4 SP2 - build v5 (planos de referencia + jaula de subdivisión).

Ejes: +X adelante, +Y izquierda, +Z arriba. Unidades: metros.
Cotas de carrocería medidas de ref/side.png (alturas) y ref/top.png (anchos).
"""
import bpy
import os
import sys
import math
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

REF = r"C:\Users\User1\Desktop\assets1\ref"

# ------------------------------------------------------------------ cotas
FA = Vector((0.7345, 0.0, 0.3000))
RA = Vector((-0.7345, 0.0, 0.3355))
PIVOT = Vector((-0.1500, 0.0, 0.4200))
RAKE = math.radians(24.5)
UD = Vector((-math.sin(RAKE), 0.0, math.cos(RAKE)))

SCALE_SIDE = 0.002688   # m/px  (batalla 530.5 px = 1.469 m)
GROUND_Y = 41.0
REAR_AXLE_PX = 245.5
SCALE_TOP = 0.002459    # m/px  (largo 859 px = 2.112 m)
TOP_Y_CENTER = 280.5

MAT = {}


# ------------------------------------------------------------------ materiales
def materials():
    import texture_lib as T
    MAT['body'] = T.matte_paint("MAT_BodyMatte", (0.0105, 0.0105, 0.0125),
                                roughness=0.58, variation=0.10, scale=150.0)
    MAT['carbon'] = T.carbon_fiber("MAT_Carbon", tiling=110.0)
    MAT['red'] = T.matte_paint("MAT_DucatiRed", (0.36, 0.014, 0.022),
                               roughness=0.24, coat=1.0, variation=0.05, scale=180.0)
    MAT['vent'] = T.matte_paint("MAT_Vent", (0.004, 0.004, 0.005), roughness=0.78,
                                variation=0.06, scale=260.0)
    MAT['seam'] = T.matte_paint("MAT_Seam", (0.0015, 0.0015, 0.0018), roughness=0.85,
                                variation=0.03, scale=400.0)
    MAT['alu'] = T.metal_tint("MAT_Aluminium", (1.00, 1.00, 1.00), roughness=0.30, tiling=2.5)
    MAT['alud'] = T.metal_tint("MAT_AluDark", (0.30, 0.31, 0.33), roughness=0.40, tiling=2.5)
    MAT['rim'] = T.metal_tint("MAT_Rim", (0.17, 0.17, 0.19), roughness=0.33, tiling=3.0)
    MAT['engine'] = T.metal_tint("MAT_Engine", (0.26, 0.26, 0.28), roughness=0.46, tiling=3.0)
    MAT['steel'] = T.metal_tint("MAT_Steel", (0.92, 0.92, 0.95), roughness=0.18, tiling=3.5)
    MAT['titan'] = T.metal_tint("MAT_Titanium", (0.86, 0.87, 0.90), roughness=0.30,
                                tiling=2.0, tex="Metal059A")
    MAT['gold'] = T.metal_tint("MAT_Gold", (1.00, 0.70, 0.28), roughness=0.20,
                               aniso=0.35, tiling=2.5)
    MAT['rubber'] = T.tire_rubber("MAT_Rubber")
    MAT['seat'] = T.pbr("MAT_Seat", "Leather037", tiling=3.0, metallic=0.0,
                        roughness=0.78, normal_strength=0.55,
                        base_color=(0.013, 0.013, 0.014))
    MAT['glass'] = T.glass_tint("MAT_Screen", tint=(0.085, 0.095, 0.115),
                                rough=0.05, alpha=0.38)
    MAT['lamp'] = T.emissive("MAT_HeadLamp", (0.93, 0.95, 1.00), 6.0)
    MAT['drl'] = T.emissive("MAT_DRL", (0.80, 0.90, 1.00), 10.0)
    MAT['tail'] = T.emissive("MAT_TailLamp", (1.00, 0.03, 0.03), 8.0)


def M(ob, key):
    return V.assign(ob, MAT[key]) if key in MAT else ob


# ------------------------------------------------------------------ RIG
def build_rig():
    old = bpy.data.objects.get("RIG_Moto")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    col = V.coll("MOTO_RIG")
    arm = bpy.data.armatures.new("MotoArmature")
    rig = bpy.data.objects.new("RIG_Moto", arm)
    col.objects.link(rig)
    arm.display_type = 'OCTAHEDRAL'
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones
    specs = [
        ("root",             (0.0, 0.0, 0.0),       (0.25, 0.0, 0.0),        None,               False),
        ("body",             (0.0, 0.0, 0.55),      (0.40, 0.0, 0.55),       "root",             True),
        ("steer",            (0.468, 0.0, 0.945),   (0.385, 0.0, 1.127),     "body",             True),
        ("front_suspension", (0.7345, 0.0, 0.300),  (0.525, 0.0, 0.760),     "steer",            True),
        ("front_wheel",      (0.7345, 0.0, 0.300),  (0.7345, 0.160, 0.300),  "front_suspension", True),
        ("handlebar",        (0.400, 0.0, 1.060),   (0.400, 0.0, 1.140),     "steer",            True),
        ("swingarm",         (-0.150, 0.0, 0.420),  (-0.7345, 0.0, 0.420),   "body",             True),
        ("rear_wheel",       (-0.7345, 0.0, 0.3355), (-0.7345, 0.160, 0.3355), "swingarm",       True),
        ("shock",            (-0.205, 0.108, 0.755), (-0.290, 0.108, 0.430), "body",             True),
    ]
    for name, h, t, parent, deform in specs:
        b = eb.new(name)
        b.head = Vector(h)
        b.tail = Vector(t)
        b.roll = 0.0
        b.use_deform = deform
        if parent:
            b.parent = eb[parent]
            b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


# ------------------------------------------------------------------ RUEDAS
def build_wheels():
    # delantera 120/70-17
    M(V.torus("W_F_Tire", FA, 0.2580, 0.0600, 0.0420, 80, 28), 'rubber')
    M(V.tube("W_F_Rim", FA, 0.2160, 0.1930, 0.088, 'Y', 64), 'rim')
    M(V.tube("W_F_Lip", FA, 0.2165, 0.2080, 0.040, 'Y', 64), 'rim')
    M(V.cylinder("W_F_Hub", FA, 0.050, 0.115, 'Y', 32), 'alud')
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        c = (FA.x + 0.126 * math.cos(a), 0.0, FA.z + 0.126 * math.sin(a))
        M(V.box(f"W_F_Spoke{k}", c, (0.162, 0.050, 0.028), rot=(0, -a, 0), bev=0.008), 'rim')
    for s, tag in ((1, "L"), (-1, "R")):
        y = 0.070 * s
        M(V.tube(f"W_F_Disc_{tag}", (FA.x, y, FA.z), 0.1650, 0.1020, 0.0055, 'Y', 64), 'steel')
        M(V.tube(f"W_F_Carrier_{tag}", (FA.x, y, FA.z), 0.1020, 0.0620, 0.0060, 'Y', 48), 'alud')
    # trasera 200/60-17
    M(V.torus("W_R_Tire", RA, 0.2758, 0.1000, 0.0598, 84, 30), 'rubber')
    M(V.tube("W_R_Rim", RA, 0.2160, 0.1930, 0.150, 'Y', 64), 'rim')
    M(V.tube("W_R_Lip", RA, 0.2165, 0.2080, 0.100, 'Y', 64), 'rim')
    M(V.cylinder("W_R_Hub", RA, 0.088, 0.175, 'Y', 40), 'alud')
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        c = (RA.x + 0.134 * math.cos(a), 0.0, RA.z + 0.134 * math.sin(a))
        M(V.box(f"W_R_Spoke{k}", c, (0.148, 0.086, 0.032), rot=(0, -a, 0), bev=0.009), 'rim')
    M(V.tube("W_R_Sprocket", (RA.x, 0.093, RA.z), 0.1120, 0.0930, 0.0085, 'Y', 56), 'steel')
    M(V.tube("W_R_Disc", (RA.x, -0.086, RA.z), 0.1225, 0.0760, 0.0050, 'Y', 56), 'steel')


# ------------------------------------------------------------------ TREN DELANTERO
def build_front():
    def fp(t):
        return FA + UD * t

    for s, tag in ((1, "L"), (-1, "R")):
        y = 0.105 * s
        p0, p1 = fp(0.13), fp(0.50)
        M(V.cyl_between(f"F_ForkTube_{tag}", (p0.x, y, p0.z), (p1.x, y, p1.z),
                        0.0215, bone="front_suspension", segs=32), 'gold')
        p0, p1 = fp(0.01), fp(0.35)
        M(V.cyl_between(f"F_ForkLeg_{tag}", (p0.x, y, p0.z), (p1.x, y, p1.z),
                        0.0245, bone="front_suspension", segs=32), 'alud')
        p = fp(0.505)
        M(V.cylinder(f"F_ForkCap_{tag}", (p.x, y, p.z), 0.0235, 0.018, 'Z', 24,
                     rot=(0, -RAKE, 0), bone="front_suspension"), 'alu')
        M(V.box(f"F_Caliper_{tag}", (0.6240, 0.089 * s, 0.3480), (0.095, 0.052, 0.135),
                rot=(0, math.radians(30), 0), bev=0.010, smooth=True,
                bone="front_suspension"), 'alud')

    for t, nm, sz in ((0.440, "F_ClampLow", (0.105, 0.245, 0.040)),
                      (0.535, "F_ClampTop", (0.100, 0.230, 0.034))):
        p = fp(t)
        M(V.box(nm, (p.x, 0.0, p.z), sz, rot=(0, -RAKE, 0), bev=0.012,
                smooth=True, bone="steer"), 'alud')

    # guardabarros con placas (radial)
    rings = []
    for i in range(31):
        a = math.radians(-32 + 154 * i / 30)
        ca, sa = math.cos(a), math.sin(a)
        rings.append([Vector((FA.x + 0.314 * ca, -0.068, FA.z + 0.314 * sa)),
                      Vector((FA.x + 0.330 * ca, -0.068, FA.z + 0.330 * sa)),
                      Vector((FA.x + 0.330 * ca, 0.068, FA.z + 0.330 * sa)),
                      Vector((FA.x + 0.314 * ca, 0.068, FA.z + 0.314 * sa))])
    M(V.loft("F_Fender", rings, bone="front_suspension"), 'carbon')

    for s, tag in ((1, "L"), (-1, "R")):
        y0, y1 = 0.055 * s, 0.190 * s
        M(V.cyl_between(f"H_Clipon_{tag}", (0.475, y0, 1.020), (0.412, y1, 1.008),
                        0.0125, bone="handlebar", segs=20), 'alud')
        M(V.cyl_between(f"H_Grip_{tag}", (0.436, y1 * 0.92, 1.014), (0.412, y1 * 1.22, 1.004),
                        0.0180, bone="handlebar", segs=20), 'rubber')
        M(V.box(f"H_Mirror_{tag}", (0.552, 0.228 * s, 1.052), (0.026, 0.070, 0.042),
                rot=(0, 0, s * math.radians(14)), bev=0.012, smooth=True,
                bone="handlebar"), 'carbon')


# ------------------------------------------------------------------ CHASIS
def build_chassis():
    M(V.box("E_Crankcase", (0.155, 0.0, 0.435), (0.40, 0.295, 0.285),
            bev=0.020, smooth=True), 'engine')
    M(V.box("E_BankFront", (0.300, 0.0, 0.585), (0.175, 0.255, 0.235),
            rot=(0, math.radians(-14), 0), bev=0.016, smooth=True), 'engine')
    M(V.box("E_BankRear", (0.055, 0.0, 0.625), (0.175, 0.255, 0.235),
            rot=(0, math.radians(16), 0), bev=0.016, smooth=True), 'engine')
    M(V.cylinder("E_ClutchCover", (0.150, -0.152, 0.415), 0.118, 0.052, 'Y', 48), 'gold')
    M(V.box("C_Headstock", (0.395, 0.0, 0.845), (0.245, 0.150, 0.215),
            rot=(0, -RAKE, 0), bev=0.018, smooth=True), 'alu')
    for s, tag in ((1, "L"), (-1, "R")):
        M(V.box(f"C_FramePlate_{tag}", (0.300, 0.118 * s, 0.680), (0.335, 0.030, 0.245),
                rot=(0, math.radians(-12), 0), bev=0.012, smooth=True), 'alu')
        M(V.box(f"C_FrameSpar_{tag}", (0.135, 0.118 * s, 0.520), (0.300, 0.028, 0.115),
                rot=(0, math.radians(6), 0), bev=0.010, smooth=True), 'alu')
        p0 = (PIVOT.x, 0.108 * s, PIVOT.z + 0.030)
        p1 = (RA.x, 0.098 * s, RA.z + 0.010)
        M(V.beam(f"S_Arm_{tag}", p0, p1, 0.032, 0.076, bone="swingarm",
                 bev=0.010, smooth=True), 'alud')
        M(V.box(f"S_AxleBlock_{tag}", (-0.690, 0.098 * s, RA.z + 0.005),
                (0.110, 0.048, 0.090), bev=0.010, smooth=True, bone="swingarm"), 'alu')
    M(V.box("S_Cross", (-0.300, 0.0, 0.395), (0.070, 0.215, 0.070),
            rot=(0, math.radians(-2.5), 0), bev=0.012, smooth=True, bone="swingarm"), 'alu')
    M(V.cylinder("S_Pivot", PIVOT, 0.030, 0.245, 'Y', 28, bone="swingarm"), 'alu')
    # amortiguador
    sh0 = Vector((-0.205, 0.108, 0.755))
    sh1 = Vector((-0.290, 0.108, 0.430))
    M(V.cyl_between("D_Body", sh0, sh0 + (sh1 - sh0) * 0.55, 0.0245, bone="shock", segs=28), 'alud')
    M(V.cyl_between("D_Rod", sh0 + (sh1 - sh0) * 0.55, sh1, 0.0110, bone="shock", segs=20), 'steel')
    M(V.cylinder("D_TopEye", sh0, 0.020, 0.040, 'Y', 20, bone="shock"), 'alud')


# ------------------------------------------------------------------ CARROCERIA
# (x, z_top, z_bot, half_w, shoulder)  -- alturas de ref/side.png, anchos de ref/top.png
FAIRING = [
    (0.790, 0.952, 0.470, 0.078, 0.58),
    (0.762, 0.950, 0.398, 0.140, 0.58),
    (0.724, 0.944, 0.330, 0.182, 0.59),
    (0.686, 0.936, 0.278, 0.208, 0.60),
    (0.644, 0.928, 0.238, 0.228, 0.60),
    (0.596, 0.918, 0.208, 0.250, 0.61),
    (0.544, 0.906, 0.192, 0.268, 0.61),
    (0.486, 0.892, 0.184, 0.281, 0.61),
    (0.428, 0.876, 0.182, 0.288, 0.60),
    (0.368, 0.856, 0.184, 0.286, 0.59),
    (0.308, 0.818, 0.188, 0.283, 0.58),
    (0.248, 0.778, 0.194, 0.281, 0.56),
    (0.188, 0.744, 0.202, 0.278, 0.54),
    (0.128, 0.720, 0.214, 0.268, 0.52),
    (0.070, 0.706, 0.234, 0.248, 0.50),
    (0.020, 0.700, 0.262, 0.222, 0.50),
]
TANK = [
    (0.430, 0.938, 0.812, 0.048, 0.55),
    (0.392, 0.982, 0.804, 0.104, 0.56),
    (0.322, 1.018, 0.798, 0.152, 0.58),
    (0.232, 1.046, 0.792, 0.174, 0.58),
    (0.132, 1.060, 0.790, 0.172, 0.58),
    (0.046, 1.052, 0.792, 0.156, 0.57),
    (-0.010, 1.016, 0.796, 0.132, 0.56),
    (-0.052, 0.972, 0.802, 0.100, 0.55),
]
SEAT = [
    (0.002, 0.902, 0.822, 0.112, 0.50),
    (-0.058, 0.897, 0.818, 0.114, 0.50),
    (-0.128, 0.890, 0.816, 0.110, 0.50),
    (-0.190, 0.887, 0.818, 0.100, 0.50),
    (-0.246, 0.890, 0.822, 0.082, 0.50),
]
TAIL = [
    (-0.210, 0.902, 0.828, 0.098, 0.50),
    (-0.300, 0.930, 0.842, 0.094, 0.50),
    (-0.400, 0.966, 0.860, 0.084, 0.50),
    (-0.490, 0.996, 0.874, 0.069, 0.50),
    (-0.560, 1.012, 0.884, 0.050, 0.50),
    (-0.610, 1.018, 0.890, 0.032, 0.50),
    (-0.642, 1.018, 0.894, 0.016, 0.50),
]


def _shell(name, table, bone="body"):
    rings = [V.ring_at(x, V.section(t, b, w, s)) for (x, t, b, w, s) in table]
    return V.loft(name, rings, bone=bone)


def build_body():
    M(_shell("B_Fairing", FAIRING), 'body')
    M(_shell("B_Tank", TANK), 'body')
    M(_shell("B_Seat", SEAT), 'seat')
    M(_shell("B_Tail", TAIL), 'body')
    M(V.cylinder("B_TankCap", (0.215, 0.0, 1.050), 0.043, 0.022, 'Z', 32), 'alud')

    # acentos rojos del deposito y del colin (siguen el contorno de la seccion)
    for tag, sgn in (("L", 1), ("R", -1)):
        rings = []
        for (x, t, b, w, s) in TANK[2:8]:
            p = V.section(t, b, w, s)
            # indice del punto cercano al hombro superior
            i = 2 if sgn > 0 else len(p) - 3
            y, z = p[i]
            rings.append([Vector((x, y + sgn * 0.002, z + 0.002)),
                          Vector((x, y + sgn * 0.004, z - 0.004))])
        M(V.loft(f"B_AccentTank_{tag}", rings), 'red')

    # cupula
    lv = [(0.976, 0.610, 0.094, 0.006), (1.018, 0.572, 0.114, 0.011),
          (1.062, 0.532, 0.126, 0.015), (1.106, 0.492, 0.130, 0.018),
          (1.146, 0.456, 0.122, 0.018), (1.178, 0.428, 0.102, 0.015)]
    rings = []
    for (z, xc, hw, dome) in lv:
        front, back = [], []
        N = 15
        for i in range(N):
            t = -1.0 + 2.0 * i / (N - 1)
            y = hw * t
            x = xc - dome * (t * t)
            front.append(Vector((x, y, z)))
            back.append(Vector((x - 0.004, y, z)))
        rings.append(front + back[::-1])
    M(V.loft("B_Screen", rings), 'glass')

    # opticas
    for s, tag in ((1, "L"), (-1, "R")):
        M(V.box(f"B_HeadHousing_{tag}", (0.742, 0.056 * s, 0.866), (0.078, 0.078, 0.082),
                rot=(0, math.radians(-8), s * math.radians(-9)), bev=0.008, smooth=True), 'vent')
        M(V.box(f"B_HeadLens_{tag}", (0.7805, 0.056 * s, 0.866), (0.014, 0.070, 0.064),
                rot=(0, math.radians(-12), s * math.radians(-11)), bev=0.005, smooth=True), 'lamp')
        M(V.box(f"B_DRL_{tag}", (0.7855, 0.058 * s, 0.897), (0.007, 0.062, 0.007),
                rot=(0, math.radians(-16), s * math.radians(-11)), bev=0.002), 'drl')
        # aleron frontal
        M(V.box(f"B_Winglet_{tag}", (0.596, 0.196 * s, 0.742), (0.150, 0.086, 0.018),
                rot=(s * math.radians(24), math.radians(-10), 0), bev=0.005, smooth=True), 'carbon')
    M(V.box("B_TailLamp", (-0.646, 0.0, 1.008), (0.012, 0.038, 0.013), bev=0.003), 'tail')
    # escape
    for i, (y0, y1, z0, z1) in enumerate(((-0.030, -0.028, 0.582, 0.654),
                                          (-0.100, -0.096, 0.596, 0.668))):
        p0 = Vector((-0.720, y0, z0))
        p1 = Vector((-0.432, y1, z1))
        M(V.cyl_between(f"X_Can{i}", p0, p1, 0.040, segs=32), 'titan')


# ------------------------------------------------------------------ ESTUDIO
def studio(quick=False):
    for nm in ("KeyLight", "FillLight", "RimLight", "Cam_Moto", "STUDIO_Floor"):
        ob = bpy.data.objects.get(nm)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)

    def area(nm, loc, rot, size, power):
        d = bpy.data.lights.new(nm, 'AREA')
        d.size = size
        d.energy = power
        o = bpy.data.objects.new(nm, d)
        o.location = loc
        o.rotation_euler = rot
        bpy.context.scene.collection.objects.link(o)

    area("KeyLight", (1.9, -2.3, 2.8), (math.radians(44), 0, math.radians(38)), 1.6, 700)
    area("FillLight", (-2.4, -1.8, 1.5), (math.radians(76), 0, math.radians(-54)), 3.0, 70)
    area("RimLight", (-1.6, 2.4, 2.1), (math.radians(56), 0, math.radians(196)), 2.0, 350)

    cam_d = bpy.data.cameras.new("Cam_Moto")
    cam_d.lens = 62.0
    cam = bpy.data.objects.new("Cam_Moto", cam_d)
    cam.location = (3.10, -2.70, 1.35)
    bpy.context.scene.collection.objects.link(cam)
    d = Vector((0.0, 0.0, 0.58)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam

    w = bpy.context.scene.world
    if w is None:
        w = bpy.data.worlds.new("World")
        bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (520, 0)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (300, 0)
    lp = nt.nodes.new("ShaderNodeLightPath")
    lp.location = (60, 260)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.location = (-260, 140)
    hdri = os.path.join(REF, "..", "textures", "hdri", "studio_small_09_2k.hdr")
    try:
        env.image = bpy.data.images.load(hdri, check_existing=True)
    except Exception:
        pass
    hb = nt.nodes.new("ShaderNodeBackground")
    hb.location = (40, 140)
    hb.inputs["Strength"].default_value = 0.85
    fl = nt.nodes.new("ShaderNodeBackground")
    fl.location = (40, -120)
    fl.inputs["Color"].default_value = (0.012, 0.013, 0.016, 1.0)
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(hb.outputs["Background"], mix.inputs[1])
    nt.links.new(fl.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    vs = bpy.context.scene.view_settings
    try:
        vs.view_transform = 'AgX'
        vs.look = 'AgX - Punchy'
    except Exception:
        pass
    return cam


# ------------------------------------------------------------------ BUILD
def build():
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.length_unit = 'METERS'
    sc.unit_settings.scale_length = 1.0
    V.purge("MOTO", "MOTO_RIG", "REF_PLANES")
    materials()
    build_rig()
    build_wheels()
    build_front()
    build_chassis()
    build_body()
    studio()
    print("BUILD v5 OK -> objetos MOTO:", len(V.coll("MOTO").objects))
    return bpy.data.objects["RIG_Moto"]


if __name__ == "__main__":
    build()
