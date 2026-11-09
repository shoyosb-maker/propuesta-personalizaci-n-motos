"""Sistema de materiales PBR y UVs para Blender 5.2.

Mapas CC0 de ambientCG (nomenclatura: Color / NormalGL / Roughness / Metalness).
Espacios de color segun manual glTF 5.2:
    Base Color, Emission -> sRGB
    Normal, Roughness, Metalness, AO -> Non-Color
"""
import bpy
import math

TEX_ROOT = r"C:\Users\User1\Desktop\assets1\textures"


# ------------------------------------------------------------------ UV
def _active(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def unwrap(ob, angle_deg=66.0, margin=0.0015):
    """Smart UV Project + empaquetado de islas."""
    if not ob.data.uv_layers:
        ob.data.uv_layers.new(name="UVMap")
    _active(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_deg),
                             island_margin=margin,
                             area_weight=0.0,
                             correct_aspect=True,
                             scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob.data.uv_layers[0].name


# ------------------------------------------------------------------ nodos
def _clear(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (700, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (380, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return nt, bsdf


def _img(nt, path, non_color, x, y):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.location = (x, y)
    n.image = bpy.data.images.load(path, check_existing=True)
    n.interpolation = 'Smart'
    if non_color:
        n.image.colorspace_settings.name = 'Non-Color'
    return n


def _map(nt, tiling, x, y, rot=0.0):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (x - 400, y)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.location = (x - 220, y)
    mp.inputs["Scale"].default_value = (tiling, tiling, tiling)
    if rot:
        mp.inputs["Rotation"].default_value = (0.0, 0.0, rot)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    return mp


def _set(bsdf, key, val):
    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = val


def pbr(mat_name, tex_id, tiling=4.0,
        tint=(1, 1, 1), metallic=None, roughness=None, rough_contrast=1.0,
        normal_strength=1.0, coat=0.0, coat_rough=0.03, aniso=0.0,
        emit=None, emit_strength=0.0, ior=1.5, base_color=None):
    """Material PBR a partir de un set de ambientCG.

    base_color: si se pasa, ignora el mapa de color y usa un color plano
    (util para cuero negro, goma, etc. donde el mapa aporta ruido indeseado).
    """
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nt, bsdf = _clear(mat)
    base = f"{TEX_ROOT}\\{tex_id}\\{tex_id}_2K-JPG"
    mp = _map(nt, tiling, -600, 0)

    if base_color is not None:
        _set(bsdf, "Base Color", (base_color[0], base_color[1], base_color[2], 1.0))
    else:
        col = _img(nt, base + "_Color.jpg", False, -200, 260)
        nt.links.new(mp.outputs["Vector"], col.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        mx.location = (60, 260)
        mx.inputs[0].default_value = 1.0
        nt.links.new(col.outputs["Color"], mx.inputs[6])
        mx.inputs[7].default_value = (tint[0], tint[1], tint[2], 1.0)
        nt.links.new(mx.outputs[2], bsdf.inputs["Base Color"])

    try:
        nrm = _img(nt, base + "_NormalGL.jpg", True, -200, -60)
        nt.links.new(mp.outputs["Vector"], nrm.inputs["Vector"])
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.location = (60, -60)
        nmap.inputs["Strength"].default_value = normal_strength
        nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    except Exception:
        pass

    import os
    rp = base + "_Roughness.jpg"
    if roughness is not None:
        _set(bsdf, "Roughness", roughness)
    elif os.path.exists(rp):
        r = _img(nt, rp, True, -200, -300)
        nt.links.new(mp.outputs["Vector"], r.inputs["Vector"])
        if rough_contrast != 1.0:
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.location = (60, -300)
            mr.inputs["From Min"].default_value = 0.5 - 0.5 / rough_contrast
            mr.inputs["From Max"].default_value = 0.5 + 0.5 / rough_contrast
            nt.links.new(r.outputs["Color"], mr.inputs["Value"])
            nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
        else:
            nt.links.new(r.outputs["Color"], bsdf.inputs["Roughness"])

    mp_path = base + "_Metalness.jpg"
    if metallic is not None:
        _set(bsdf, "Metallic", metallic)
    elif os.path.exists(mp_path):
        m = _img(nt, mp_path, True, -200, -520)
        nt.links.new(mp.outputs["Vector"], m.inputs["Vector"])
        nt.links.new(m.outputs["Color"], bsdf.inputs["Metallic"])

    _set(bsdf, "IOR", ior)
    _set(bsdf, "Coat Weight", coat)
    _set(bsdf, "Coat Roughness", coat_rough)
    _set(bsdf, "Anisotropic", aniso)
    if emit is not None:
        _set(bsdf, "Emission Color", (emit[0], emit[1], emit[2], 1.0))
        _set(bsdf, "Emission Strength", emit_strength)
    return mat


# ------------------------------------------------------------------ procedurales
def _noise(nt, scale, detail, x, y, rough=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.location = (x, y)
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    return n


def matte_paint(mat_name, color, roughness=0.62, coat=0.0, variation=0.10, scale=140.0):
    """Pintura mate con microvariacion de rugosidad (aspecto real de carenado)."""
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nt, bsdf = _clear(mat)
    _set(bsdf, "Base Color", (color[0], color[1], color[2], 1.0))
    _set(bsdf, "Metallic", 0.0)
    _set(bsdf, "Roughness", roughness)
    _set(bsdf, "Coat Weight", coat)
    _set(bsdf, "Specular IOR Level", 0.42)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-700, 0)
    n = _noise(nt, scale, 4.0, -500, -120, 0.55)
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.location = (-260, -120)
    mr.inputs["To Min"].default_value = max(0.0, roughness - variation)
    mr.inputs["To Max"].default_value = min(1.0, roughness + variation)
    nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (100, -320)
    bump.inputs["Strength"].default_value = 0.045
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def carbon_fiber(mat_name, tiling=90.0):
    """Twill de carbono procedural: dos ondas cruzadas + relieve."""
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nt, bsdf = _clear(mat)
    _set(bsdf, "Base Color", (0.020, 0.020, 0.023, 1.0))
    _set(bsdf, "Metallic", 0.15)
    _set(bsdf, "Roughness", 0.24)
    _set(bsdf, "Coat Weight", 0.85)
    _set(bsdf, "Coat Roughness", 0.06)
    _set(bsdf, "Anisotropic", 0.55)

    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-1100, 0)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.location = (-920, 0)
    mp.inputs["Scale"].default_value = (tiling, tiling, tiling)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def wave(rot, y):
        w = nt.nodes.new("ShaderNodeTexWave")
        w.location = (-700, y)
        w.wave_type = 'BANDS'
        w.bands_direction = 'X'
        w.inputs["Scale"].default_value = 1.0
        w.inputs["Distortion"].default_value = 0.0
        mpr = nt.nodes.new("ShaderNodeMapping")
        mpr.location = (-820, y)
        mpr.inputs["Rotation"].default_value = (0.0, 0.0, rot)
        nt.links.new(mp.outputs["Vector"], mpr.inputs["Vector"])
        nt.links.new(mpr.outputs["Vector"], w.inputs["Vector"])
        return w

    w1 = wave(math.radians(45), 200)
    w2 = wave(math.radians(-45), -60)
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.location = (-400, 80)
    mul.inputs[0].default_value = 1.0
    nt.links.new(w1.outputs["Color"], mul.inputs[6])
    nt.links.new(w2.outputs["Color"], mul.inputs[7])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-200, 80)
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.008, 0.008, 0.010, 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.060, 0.060, 0.068, 1.0)
    nt.links.new(mul.outputs[2], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (100, -260)
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.0015
    nt.links.new(mul.outputs[2], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def tire_rubber(mat_name):
    """Goma: negro uniforme + rugosidad/normal suaves y surcos de rodadura."""
    mat = pbr(mat_name, "Rubber001", tiling=1.6, metallic=0.0,
              roughness=0.88, normal_strength=0.14,
              base_color=(0.011, 0.011, 0.012))
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-1200, -600)
    # surcos longitudinales: bandas suaves, sin ruido de alta frecuencia
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.location = (-980, -600)
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Y'
    wave.inputs["Scale"].default_value = 1.2
    wave.inputs["Distortion"].default_value = 0.35
    wave.inputs["Detail"].default_value = 1.0
    nt.links.new(tc.outputs["UV"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (-560, -600)
    bump.inputs["Strength"].default_value = 0.30
    bump.inputs["Distance"].default_value = 0.0025
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nrm = [l for l in nt.links if l.to_socket == bsdf.inputs["Normal"]]
    if nrm:
        nt.links.new(nrm[0].from_socket, bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def metal_tint(mat_name, tint, metallic=1.0, roughness=0.28, coat=0.0,
               aniso=0.0, tex="Metal032", tiling=6.0, normal=0.6):
    m = pbr(mat_name, tex, tiling=tiling, tint=tint, metallic=metallic,
            roughness=roughness, normal_strength=normal, coat=coat, aniso=aniso)
    return m


def emissive(mat_name, color, strength, base=(0.02, 0.02, 0.02)):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nt, bsdf = _clear(mat)
    _set(bsdf, "Base Color", (base[0], base[1], base[2], 1.0))
    _set(bsdf, "Roughness", 0.12)
    _set(bsdf, "Emission Color", (color[0], color[1], color[2], 1.0))
    _set(bsdf, "Emission Strength", strength)
    return mat


def glass_tint(mat_name, tint=(0.10, 0.11, 0.13), transmission=0.0, rough=0.06, alpha=0.42):
    """Cristal ahumado para EEVEE: alfa en vez de transmisión (sin lechosidad)."""
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    nt, bsdf = _clear(mat)
    _set(bsdf, "Base Color", (tint[0], tint[1], tint[2], 1.0))
    _set(bsdf, "Roughness", rough)
    _set(bsdf, "Metallic", 0.0)
    _set(bsdf, "Alpha", alpha)
    _set(bsdf, "IOR", 1.48)
    _set(bsdf, "Coat Weight", 1.0)
    _set(bsdf, "Coat Roughness", 0.02)
    if transmission:
        _set(bsdf, "Transmission Weight", transmission)
    return mat
