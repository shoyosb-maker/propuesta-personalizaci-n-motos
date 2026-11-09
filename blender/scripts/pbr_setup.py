"""Aplica el set de materiales PBR final al modelo unido."""
import bpy
import texture_lib as T


def run(ob, unwrap=True, verbose=True):
    if unwrap:
        name = T.unwrap(ob, angle_deg=66.0, margin=0.0015)
        if verbose:
            print(f"UVs listos: capa '{name}'")

    T.matte_paint("MAT_BodyMatte", (0.0105, 0.0105, 0.0125), roughness=0.58,
                  coat=0.0, variation=0.10, scale=150.0)
    T.matte_paint("MAT_Vent", (0.004, 0.004, 0.005), roughness=0.78,
                  variation=0.06, scale=260.0)
    T.matte_paint("MAT_Seam", (0.0015, 0.0015, 0.0018), roughness=0.85,
                  variation=0.03, scale=400.0)
    T.carbon_fiber("MAT_Carbon", tiling=110.0)

    # pintura Ducati: rojo con barniz
    red = T.matte_paint("MAT_DucatiRed", (0.36, 0.014, 0.022),
                        roughness=0.24, coat=1.0, variation=0.05, scale=180.0)
    b = red.node_tree.nodes["Principled BSDF"]
    if "Metallic" in b.inputs:
        b.inputs["Metallic"].default_value = 0.25
    if "Coat Roughness" in b.inputs:
        b.inputs["Coat Roughness"].default_value = 0.04

    T.metal_tint("MAT_Aluminium", (1.00, 1.00, 1.00), roughness=0.30, tiling=2.5)
    T.metal_tint("MAT_AluDark", (0.30, 0.31, 0.33), roughness=0.40, tiling=2.5)
    T.metal_tint("MAT_Rim", (0.17, 0.17, 0.19), roughness=0.33, tiling=3.0)
    T.metal_tint("MAT_Engine", (0.26, 0.26, 0.28), roughness=0.46, tiling=3.0)
    T.metal_tint("MAT_Steel", (0.92, 0.92, 0.95), roughness=0.18, tiling=3.5)
    T.metal_tint("MAT_Titanium", (0.86, 0.87, 0.90), roughness=0.30, tiling=2.0,
                 tex="Metal059A")
    T.metal_tint("MAT_Gold", (1.00, 0.70, 0.28), roughness=0.20, aniso=0.35, tiling=2.5)

    T.pbr("MAT_Seat", "Leather037", tiling=3.0, metallic=0.0, roughness=0.78,
          normal_strength=0.55, base_color=(0.013, 0.013, 0.014))
    T.tire_rubber("MAT_Rubber")

    T.glass_tint("MAT_Screen", tint=(0.085, 0.095, 0.115), rough=0.05, alpha=0.38)
    T.emissive("MAT_HeadLamp", (0.93, 0.95, 1.00), 6.0)
    T.emissive("MAT_DRL", (0.80, 0.90, 1.00), 10.0)
    T.emissive("MAT_TailLamp", (1.00, 0.03, 0.03), 8.0)

    if verbose:
        missing = [s.name for s in ob.material_slots if s.material is None]
        print("slots sin material:", missing if missing else "ninguno")
        for s in ob.material_slots:
            if s.material:
                n = s.material.node_tree
                imgs = sum(1 for nd in n.nodes if nd.type == 'TEX_IMAGE')
                print(f"  {s.material.name:<16} nodos={len(n.nodes):<3} imagenes={imgs}")
    return ob
