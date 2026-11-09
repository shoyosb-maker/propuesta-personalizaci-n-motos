"""vlib - primitivas y utilidades de malla para Blender 5.x.

Convencion: +X adelante, +Y izquierda, +Z arriba. Unidades: metros.
Todas las funciones devuelven objetos vinculados a una coleccion.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

TAU = math.pi * 2.0


# ------------------------------------------------------------------ escena
def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def purge(*names):
    for n in names:
        c = bpy.data.collections.get(n)
        if c is None:
            continue
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def active(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


# ------------------------------------------------------------------ mesh
def obj(name, verts, faces, col="MOTO", bone="body", smooth=True, recalc=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(verbose=False)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll(col).objects.link(ob)
    ob["rig_bone"] = bone
    return ob


def xform(verts, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    m = (Matrix.Translation(Vector(loc)) @
         Euler(rot, 'XYZ').to_matrix().to_4x4() @
         Matrix.Diagonal(Vector((scale[0], scale[1], scale[2], 1.0))))
    return [m @ Vector(v) for v in verts]


def box(name, loc, size, rot=(0, 0, 0), bev=0.0, col="MOTO", bone="body", smooth=False):
    sx, sy, sz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = obj(name, xform(v, loc, rot), f, col, bone, smooth=smooth)
    if bev > 0:
        bevel(ob, bev)
    return ob


def bevel(ob, width=0.003, segments=2, angle_deg=35.0):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    ang = math.radians(angle_deg)
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > ang]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def cylinder(name, loc, radius, depth, axis='Z', segs=32, rot=(0, 0, 0),
             col="MOTO", bone="body", smooth=True):
    verts, faces = [], []
    for i in range(segs):
        a = TAU * i / segs
        c, s = math.cos(a), math.sin(a)
        verts.append((radius * c, radius * s, -depth * 0.5))
        verts.append((radius * c, radius * s, depth * 0.5))
    for i in range(segs):
        j = (i + 1) % segs
        faces.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    faces.append(tuple(range(0, 2 * segs, 2))[::-1])
    faces.append(tuple(range(1, 2 * segs, 2)))
    base = {'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[axis]
    r = (rot[0] + base[0], rot[1] + base[1], rot[2] + base[2])
    return obj(name, xform(verts, loc, r), faces, col, bone, smooth=smooth)


def tube(name, loc, r_out, r_in, depth, axis='Y', segs=48, rot=(0, 0, 0),
         col="MOTO", bone="body", smooth=True):
    verts, faces = [], []
    for i in range(segs):
        a = TAU * i / segs
        c, s = math.cos(a), math.sin(a)
        for r, z in ((r_out, -depth / 2), (r_out, depth / 2), (r_in, depth / 2), (r_in, -depth / 2)):
            verts.append((r * c, r * s, z))
    for i in range(segs):
        j = (i + 1) % segs
        for k in range(4):
            faces.append((i * 4 + k, i * 4 + (k + 1) % 4, j * 4 + (k + 1) % 4, j * 4 + k))
    base = {'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[axis]
    r = (rot[0] + base[0], rot[1] + base[1], rot[2] + base[2])
    return obj(name, xform(verts, loc, r), faces, col, bone, smooth=smooth)


def torus(name, loc, r_major, ry, rz, seg_u=72, seg_v=24, col="MOTO", bone="body"):
    verts, faces = [], []
    for i in range(seg_u):
        u = TAU * i / seg_u
        cu, su = math.cos(u), math.sin(u)
        for j in range(seg_v):
            v = TAU * j / seg_v
            rad = r_major + rz * math.cos(v)
            verts.append((rad * cu, ry * math.sin(v), rad * su))
    for i in range(seg_u):
        i2 = (i + 1) % seg_u
        for j in range(seg_v):
            j2 = (j + 1) % seg_v
            faces.append((i * seg_v + j, i2 * seg_v + j, i2 * seg_v + j2, i * seg_v + j2))
    return obj(name, xform(verts, loc), faces, col, bone)


def loft(name, rings, caps=True, col="MOTO", bone="body", smooth=True, close_ring=True):
    """rings: lista de anillos (listas de Vector de igual longitud)."""
    n = len(rings[0])
    verts = []
    for r in rings:
        verts.extend(r)
    faces = []
    span = n if close_ring else n - 1
    for i in range(len(rings) - 1):
        for j in range(span):
            a = i * n + j
            b = i * n + (j + 1) % n
            c = (i + 1) * n + (j + 1) % n
            d = (i + 1) * n + j
            faces.append((a, b, c, d))
    if caps:
        faces.append(tuple(range(n - 1, -1, -1)))
        base = (len(rings) - 1) * n
        faces.append(tuple(range(base, base + n)))
    return obj(name, verts, faces, col, bone, smooth=smooth)


def sweep(name, points, radius, samples=6, segs=10, col="MOTO", bone="body"):
    """Tubo por polilinea suavizada (Catmull-Rom)."""
    P = [Vector(p) for p in points]
    n = len(P)
    pts = []
    for i in range(n - 1):
        p0 = P[max(i - 1, 0)]
        p1, p2 = P[i], P[i + 1]
        p3 = P[min(i + 2, n - 1)]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t +
                              (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    pts.append(P[-1])
    verts, faces = [], []
    m = len(pts)
    for i, p in enumerate(pts):
        if i == 0:
            tang = pts[1] - pts[0]
        elif i == m - 1:
            tang = pts[-1] - pts[-2]
        else:
            tang = pts[i + 1] - pts[i - 1]
        if tang.length < 1e-9:
            tang = Vector((1, 0, 0))
        tang.normalize()
        ref = Vector((0, 0, 1)) if abs(tang.z) < 0.9 else Vector((1, 0, 0))
        n1 = tang.cross(ref).normalized()
        n2 = tang.cross(n1).normalized()
        for k in range(segs):
            a = TAU * k / segs
            verts.append(p + (n1 * math.cos(a) + n2 * math.sin(a)) * radius)
    for i in range(m - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append((i * segs + k, i * segs + k2, (i + 1) * segs + k2, (i + 1) * segs + k))
    return obj(name, verts, faces, col, bone)


def cyl_between(name, p0, p1, radius, col="MOTO", bone="body", segs=24, mat=None):
    p0v, p1v = Vector(p0), Vector(p1)
    d = p1v - p0v
    rot = d.to_track_quat('Z', 'Y').to_euler()
    ob = cylinder(name, tuple((p0v + p1v) * 0.5), radius, d.length, axis='Z',
                  segs=segs, rot=(rot.x, rot.y, rot.z), col=col, bone=bone)
    return ob


def beam(name, p0, p1, w, h, col="MOTO", bone="body", bev=0.0, smooth=False):
    p0v, p1v = Vector(p0), Vector(p1)
    d = p1v - p0v
    rot = d.to_track_quat('X', 'Z').to_euler()
    return box(name, tuple((p0v + p1v) * 0.5), (d.length, w, h),
               rot=(rot.x, rot.y, rot.z), bev=bev, col=col, bone=bone, smooth=smooth)


def assign(ob, material):
    ob.data.materials.clear()
    ob.data.materials.append(material)
    return ob


# ------------------------------------------------------------------ secciones
def section(z_top, z_bot, hw, shoulder=0.62, n_up=4, n_dn=4):
    """Seccion cerrada (16 puntos con n_up=n_dn=4): dos semi-elipses con el
    ancho maximo a la altura `shoulder` (0=abajo, 1=arriba)."""
    h = max(z_top - z_bot, 1e-5)
    zw = z_bot + h * shoulder
    b_up = max(z_top - zw, 1e-5)
    b_dn = max(zw - z_bot, 1e-5)
    right = []
    for i in range(n_up + 1):
        t = math.radians(90.0 - 90.0 * i / n_up)
        right.append((hw * math.cos(t), zw + b_up * math.sin(t)))
    for i in range(1, n_dn + 1):
        t = math.radians(-90.0 * i / n_dn)
        right.append((hw * math.cos(t), zw + b_dn * math.sin(t)))
    left = [(-y, z) for (y, z) in right[1:-1]][::-1]
    return right + left


def ring_at(x, sec2d):
    return [Vector((x, y, z)) for (y, z) in sec2d]
