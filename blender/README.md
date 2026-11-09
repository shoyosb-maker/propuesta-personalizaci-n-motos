# Pipeline de Blender

Referencia de cómo se modeló y exportó el `panigale_web.glb` que consume el visor.

> **El archivo `.blend` no está en este repositorio** (49 MB, más que todo lo demás
> junto). Lo que sí viaja es el resultado: `public/assets/panigale_web.glb`. Si
> necesitas el fuente para reexportar, pide la escena `moto_v6_panigale_sp.blend` y
> colócala en esta carpeta.

```
blender/
├── ref/                        # fotos de referencia usadas para medir la moto
└── scripts/
    ├── export_web_glb.py       # exporta a web (esto es lo que se usa hoy)
    ├── pbr_setup.py            # asigna el set de materiales PBR al mesh unido
    ├── texture_lib.py          # constructor de materiales PBR + UV unwrap
    ├── vlib.py                 # primitivas de malla (loft, sweep, box, tube…)
    └── build_v5.py             # rebuild procedural completo (referencia de medidas)
```

## La escena

`moto_v6_panigale_sp.blend` (Blender 5.2 LTS) contiene:

| Colección | Contenido |
| --- | --- |
| `MODELO_TEXTURAS` | 19 mallas del modelo importado, una por material |
| `MODELO_POLIGONOS` | 19 duplicados con modificador *Wireframe* (vista de malla) |
| `MOTO_RIG` | armadura `RIG_Moto`, 9 huesos con límites en espacio LOCAL |
| `Collection` | panel y textos de la UI en pantalla + cámara y luces |

Los materiales llevan un custom property `pani_orig` con el `baseColorFactor` de
fábrica; el panel de Python que vive dentro del `.blend` (Text datablock
`panigale_panel.py`, con `use_module` activo) lo usa para el reset.

El rig: `root → body → steer → front_suspension → front_wheel`,
`body → swingarm → rear_wheel`, `body → shock`, `steer → handlebar`. Límites: dirección
±34°, basculante −4°…+13°, horquilla 0…115 mm.

## Exportar a web

```bash
blender -b blender/moto_v6_panigale_sp.blend -P blender/scripts/export_web_glb.py
```

Escribe `public/assets/panigale_web.glb`. Pasos que hace, en orden:

1. Restaura los colores de fábrica leyendo `pani_orig` de cada material.
2. **Puentea los nodos `Mix` de Base Color.** El exportador de glTF no entiende ese
   patrón y escribe un `baseColorFactor` corrupto (una librea con factor blanco salió
   como `[1, 0, 0.013]`, y en el visor todo quedaba casi negro). Dejando la imagen
   conectada directo al Principled, el factor sale `[1,1,1]` y el tinte se aplica
   luego en el navegador con `albedoColor`.
3. Reduce las texturas: color a 2048, normal y metallicRoughness a 1024, clearcoat a
   512. Con `export_image_format='WEBP'` y calidad 85, 30 MB de mapas bajan a ~1 MB.
4. Suelta las mallas del rig (`parent_clear` + quitar el modificador Armature) y aplica
   transformaciones, para que viajen como mallas independientes.
5. Exporta con `export_apply=True`, `export_tangents=False` y sin skins ni animaciones.

Resultado: **19 mallas, 12 materiales, 221.228 triángulos, 8 MB**.

## Trampas encontradas

- `export_apply=False` (el default) exporta el *blockout* sin modificadores.
- `bpy.context` queda incompleto si llamas `open_mainfile` y exportas en la misma
  ejecución del addon MCP: sepáralo en dos llamadas.
- `Image.scale()` sobre una imagen empaquetada que aún no está en memoria puede dar un
  buffer plano; hay que tocar `image.pixels[0]` antes.
- En Blender 5.x las aristas con crease son el atributo `crease_edge`, no
  `edge.crease`; `use_auto_smooth` ya no existe.
- Las restricciones de hueso nacen en `owner_space='WORLD'`: en un hueso inclinado no
  limitan nada. Hay que ponerlas en `'LOCAL'`.

## Fuente del modelo

*2021 Ducati Panigale V4 SP* por **brainlesszombie5** en Sketchfab, licencia **CC BY**.
Ver los créditos en el [README principal](../README.md).
