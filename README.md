# Ducati Panigale V4 SP · Configurador web 360

Dashboard web que muestra la moto en 3D con órbita de 360° y permite cambiar el
acabado de cada pieza en tiempo real. El modelo es el mismo que se modela y texturiza
en Blender; se exporta a glTF y se sirve como un único `.glb`.

![Configurador de escritorio](./preview.png)

<img src="./preview-mobile.png" alt="Vista móvil con el panel como hoja inferior" width="300" />

## Arrancar

Requiere Node 18+.

```bash
npm install      # crea node_modules aquí (ignorado por git)
npm run dev      # http://localhost:5173
```

```bash
npm run build    # genera dist/ listo para publicar
npm run preview  # sirve dist/ para comprobarlo
```

## Subir a GitHub

Esta carpeta es **todo** el proyecto web y no tiene nada más: 16 archivos, ~8 MB.
No incluye `node_modules`, `dist` ni cachés, así que se puede arrastrar tal cual a
un repositorio de GitHub (arrastrar los archivos de la carpeta a la página del repo,
o mejor: `git init && git add . && git commit && git push`).

Si arrastras, asegúrate de no tener `node_modules/` ni `dist/` dentro: se crean al
hacer `npm install` y `npm run build`, y están en [.gitignore](.gitignore) para que
git los ignore, pero la subida por arrastre no lee ese archivo.

## Qué hay dentro

```
web-panigale/
├── index.html                 # estructura del dashboard (canvas + HUD)
├── package.json               # Babylon 8 + Vite 7
├── vite.config.js             # base './', cacheDir fuera del proyecto
├── public/assets/
│   ├── panigale_web.glb       # modelo (8 MB, texturas WebP embebidas)
│   └── studio_env.jpg         # HDRI de estudio como JPEG equirectangular
└── src/
    ├── main.js                # arranque: escena + registro de materiales
    ├── viewer.js              # Babylon: cámara 360, luces, sombra, entorno
    ├── paint.js               # gestor de acabados (albedoColor + ganancias)
    ├── config.js              # catálogo de piezas, presets y conversión de color
    ├── ui.js                  # HUD: desplegable, paleta, hoja móvil, controles
    └── style.css              # tema oscuro glass
```

## Cómo se cambia el color

Cada pieza es un material del glTF. El color se aplica sobre `albedoColor` del
`PBRMaterial`, que en glTF equivale al `baseColorFactor` y **se multiplica** con la
textura de color. Así se conservan el grano de la pintura, los mapas de normales,
las rugosidades y los calcados de la librea (`DUCATI CORSE`, franjas rojas) — sólo
cambia el tono.

`gain` en [config.js](src/config.js) compensa que la textura sea más oscura o más
clara que 1: la carrocería se multiplica por 30 porque su textura es muy oscura,
mientras que las piezas metálicas usan ~2.5. `base` es el `baseColorFactor` de
fábrica, de modo que *Reset* devuelve exactamente la apariencia original.

## Regenerar el modelo

El `.blend` vive en la carpeta padre. Para volver a exportar:

```bash
blender -b ../moto_v6_panigale_sp.blend -P ../scripts/export_web_glb.py
```

Ese script restaura los colores de fábrica, puentea los nodos `Mix` de Base Color
(el exportador de glTF los interpreta mal), reduce las texturas, suelta las mallas
del rig y escribe `public/assets/panigale_web.glb`.

## Controles

| Acción | Cómo |
| --- | --- |
| Girar la moto | Arrastrar sobre el modelo |
| Zoom | Rueda / pinza |
| Elegir pieza | Desplegable **Pieza del modelo** (cada fila muestra su color actual), o clic directo sobre la pieza |
| Cambiar color | Muestra de la paleta o selector "Color personalizado" |
| Ver la malla | Botón **Malla** |
| Captura PNG | Botón **Captura** |
| Volver a fábrica | **Reset** (todo) o **Restablecer esta pieza** |

La moto se apoya en una plataforma plateada de dos piezas (tapa de aluminio y canto
grafitado) para que el carenado oscuro gane contraste. Es puramente decorativa: no
entra en el picking ni en el catálogo de piezas.

### El desplegable

No es un `<select>` nativo: es una lista propia para poder mostrar el color de cada
pieza y respetar el tema. Tres detalles que costaron sangre:

- El `backdrop-filter` del panel convierte al panel en *containing block* de los
  `position: fixed`, así que el menú se cuelga del `body` y se posiciona con las
  coordenadas del botón.
- Nada de `scrollIntoView()`: mueve también el panel, dispara su evento `scroll` y
  el propio manejador cerraba el menú. El desplazamiento se hace sobre la lista.
- Mide el alto real del contenido y el espacio libre arriba/abajo para abrir hacia
  arriba cuando no cabe, recortando el `max-height` al hueco disponible.

## Responsive

En móvil (< 900 px) el panel pasa a ser una **hoja inferior plegable**. Plegada mide
44 px y **no dibuja ninguna caja**: sólo queda un chevrón flotando sobre la escena
(anima arriba/abajo con `@keyframes`, y respeta `prefers-reduced-motion`), apuntando
hacia arriba. Al tocarlo, la hoja sube y aparece la tarjeta de cristal con el selector
de pieza, la paleta y el selector de color; el chevrón gira 180° para indicar que se
puede cerrar.

El contenido nunca se quita del DOM: lo recorta la altura de la hoja, así que se va
descubriendo a medida que sube. La altura la anima JS con valores medidos
(`from` → `to` reales) porque animar `max-height` hacía que el tope visible se
alcanzara en el primer tercio y el recorrido se sintiera de golpe.

Al elegir una pieza con la hoja plegada se despliega sola. También se ocultan el
divisor y la etiqueta "Color", y los textos largos se abrevian.

La cámara se reencuadra sola:

- `fitCamera()` retrocede lo necesario para que la moto quepa a lo ancho. El fov de
  Babylon es vertical, así que en un móvil en vertical el campo horizontal es muy
  estrecho y la moto salía cortada por los lados.
- `applyFramingOffset()` centra la moto en el hueco libre entre la cabecera y la hoja,
  recalculándolo **cada frame**: así el zoom no la saca de sitio y al desplegar el
  panel la moto sube acompañando la animación.

## Créditos

Modelo 3D: *2021 Ducati Panigale V4 SP* por **brainlesszombie5** en Sketchfab,
licencia **CC BY**. Las marcas y la librea Ducati son propiedad de Ducati Motor
Holding; este proyecto es una demostración técnica de configurador 3D.

Texturas PBR: [ambientCG](https://ambientcg.com) (CC0) y [Poly Haven](https://polyhaven.com) (CC0).
HDRI: `studio_small_09` de Poly Haven (CC0).
