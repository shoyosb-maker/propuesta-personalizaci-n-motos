"""
Exporta la moto a un GLB optimizado para web (Babylon.js / three.js).

Uso, desde la raíz del repo:
    blender -b blender/moto_v6_panigale_sp.blend -P blender/scripts/export_web_glb.py

Qué hace, en orden:
  1. Restaura los colores de fábrica (el GLB no debe llevar los tintes del panel).
  2. Puentea los nodos Mix de Base Color: el exportador de glTF interpreta mal ese
     Mix y escribe un baseColorFactor erróneo, así que dejamos la textura conectada
     directamente al Principled. El tinte se aplica luego en el navegador con
     `albedoColor`, que en glTF equivale a baseColorFactor.
  3. Reduce las texturas (color 2048, normal/MR 1024, clearcoat 512).
  4. Suelta las mallas del rig y les aplica la transformación, para que viajen como
     mallas independientes con transformación identidad.
  5. Exporta GLB con texturas WebP y sin tangentes (Babylon las deriva en shader).

No guarda el .blend: todos los cambios son sólo para la exportación.
"""

import os

import bpy

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # ejecutado con exec() desde el addon MCP
    HERE = bpy.path.abspath("//scripts")

# <repo>/blender/scripts -> <repo>
BASE = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(BASE, "public", "assets", "panigale_web.glb")

TEXTURE_COL = "MODELO_TEXTURAS"

# material -> tamaño destino de sus texturas
SIZES = {
    "Metal059A_2K-JPG_Color.jpg": 1024,
    "Metal059A_2K-JPG_NormalGL.jpg": 1024,
    "Metal032_2K-JPG_Color.jpg": 1024,
    "Metal032_2K-JPG_NormalGL.jpg": 1024,
    "Rubber001_2K-JPG_NormalGL.jpg": 1024,
    "Leather037_2K-JPG_NormalGL.jpg": 1024,
    "mat_livery_0_160_001_baseColor.png.001": 2048,
    "mat_livery_0_160_001_normal.png.001": 1024,
    "mat_livery_0_160_001_metallicRoughness.png.001": 1024,
    "mat_livery_0_160_001_clearcoat.png.001": 512,
}


def reset_factory_colors():
    """Vuelve a los valores originales guardados por el panel del .blend."""
    for mat in bpy.data.materials:
        if "pani_orig" not in mat:
            continue
        original = mat["pani_orig"]
        rgb = (original[0], original[1], original[2])
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        socket = bsdf.inputs["Base Color"]
        if socket.is_linked:
            source = socket.links[0].from_node
            if source.type == "MIX" and source.data_type == "RGBA":
                source.inputs[7].default_value = (*rgb, 1.0)
        else:
            socket.default_value = (*rgb, 1.0)
        mat.diffuse_color = (*rgb, 1.0)


def bypass_base_color_mix():
    """Conecta la textura de color directo al Principled, sin el nodo Mix."""
    fixed = []
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        socket = bsdf.inputs["Base Color"]
        if not socket.is_linked:
            continue
        mix = socket.links[0].from_node
        if mix.type != "MIX" or mix.data_type != "RGBA":
            continue
        upstream = [l.from_socket for l in mix.inputs[6].links] or [
            l.from_socket for l in mix.inputs[7].links
        ]
        if not upstream:
            continue
        mat.node_tree.links.remove(socket.links[0])
        mat.node_tree.links.new(upstream[0], socket)
        fixed.append(mat.name)
    return fixed


def shrink_textures():
    resized = []
    for name, size in SIZES.items():
        image = bpy.data.images.get(name)
        if image is None or image.size[0] <= size:
            continue
        _ = image.pixels[0]  # fuerza la carga del buffer antes de escalar
        image.scale(size, size)
        resized.append((name, size))
    return resized


def flatten_meshes():
    meshes = [o for o in bpy.data.collections[TEXTURE_COL].all_objects if o.type == "MESH"]
    for obj in meshes:
        for modifier in list(obj.modifiers):
            if modifier.type == "ARMATURE":
                obj.modifiers.remove(modifier)
        if obj.parent:
            world = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = world

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return meshes


def main():
    reset_factory_colors()
    print("[export] materiales puenteados:", bypass_base_color_mix())
    print("[export] texturas reducidas:", [n for n, _ in shrink_textures()])

    meshes = flatten_meshes()
    print(f"[export] mallas: {len(meshes)}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_image_format="WEBP",
        export_image_quality=85,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_skins=False,
        export_normals=True,
        export_tangents=False,
        export_extras=False,
        export_attributes=False,
        export_morph=False,
    )

    size_mb = os.path.getsize(OUT) / 1e6
    print(f"[export] {OUT} -> {size_mb:.2f} MB")


main()
