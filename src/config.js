/**
 * Catálogo de piezas y acabados.
 *
 * Los materiales usan el nombre exacto con el que se exportaron desde Blender
 * (ver scripts de exportación). Si renombras un material en el .blend hay que
 * actualizarlo aquí.
 *
 * Los colores se declaran en espacio LINEAL (el mismo que usa el Base Color del
 * Principled BSDF en Blender), para que el resultado coincida con el render
 * original. La conversión a sRGB se hace sólo para pintar las muestras del HUD.
 */

export const PARTS = [
  { id: 'carroceria', mat: 'MAT_Livery',   name: 'Carrocería',      hint: 'Carenado, depósito y colín',      gain: 30,   base: [1.00, 1.00, 1.00] },
  { id: 'rines',      mat: 'MAT_Rim',      name: 'Rines',           hint: 'Llantas delantera y trasera',     gain: 2.9,  base: [0.30, 0.30, 0.33] },
  { id: 'chasis',     mat: 'MAT_Engine',   name: 'Chasis / motor',  hint: 'Motor, basculante y soportes',    gain: 2.6,  base: [0.26, 0.26, 0.28] },
  { id: 'espejos',    mat: 'MAT_Mirror',   name: 'Espejos',         hint: 'Carcasas de los retrovisores',    gain: 1.0,  base: [0.92, 0.92, 0.95] },
  { id: 'frenos',     mat: 'MAT_Brake',    name: 'Frenos',          hint: 'Discos, pinzas y bomba',          gain: 1.2,  base: [0.92, 0.92, 0.95] },
  { id: 'escape',     mat: 'MAT_Titanium', name: 'Escape',          hint: 'Colectores y silenciadores',      gain: 1.1,  base: [0.86, 0.87, 0.90] },
  { id: 'asiento',    mat: 'MAT_Seat',     name: 'Asiento',         hint: 'Tapizado del sillín',             gain: 1.0,  base: [0.013, 0.013, 0.014] },
  { id: 'cupula',     mat: 'MAT_Screen',   name: 'Cúpula',          hint: 'Cristal ahumado',                 gain: 1.0,  base: [0.085, 0.095, 0.115] },
  { id: 'gomas',      mat: 'MAT_Rubber',   name: 'Gomas',           hint: 'Neumáticos delantero y trasero',  gain: 1.0,  base: [0.011, 0.011, 0.012] },
  { id: 'cadena',     mat: 'MAT_AluDark',  name: 'Cadena',          hint: 'Transmisión y piñones',           gain: 2.5,  base: [0.30, 0.31, 0.33] },
  { id: 'tablero',    mat: 'MAT_Gauge',    name: 'Tablero',         hint: 'Instrumentación digital',         gain: 1.0,  base: [0.02, 0.02, 0.02] },
  { id: 'faro',       mat: 'MAT_HeadLamp', name: 'Faro',            hint: 'Óptica delantera',                gain: 1.0,  base: [0.02, 0.02, 0.02] },
];

export const PRESETS = [
  { name: 'Negro',      rgb: [0.012, 0.012, 0.014] },
  { name: 'Negro mate', rgb: [0.035, 0.035, 0.038] },
  { name: 'Grafito',    rgb: [0.180, 0.185, 0.195] },
  { name: 'Plata',      rgb: [0.520, 0.525, 0.545] },
  { name: 'Blanco',     rgb: [0.760, 0.760, 0.775] },
  { name: 'Rojo',       rgb: [0.420, 0.020, 0.028] },
  { name: 'Rojo vivo',  rgb: [0.620, 0.030, 0.030] },
  { name: 'Naranja',    rgb: [0.700, 0.200, 0.020] },
  { name: 'Amarillo',   rgb: [0.760, 0.550, 0.030] },
  { name: 'Oro',        rgb: [0.720, 0.500, 0.150] },
  { name: 'Verde',      rgb: [0.030, 0.300, 0.120] },
  { name: 'Azul',       rgb: [0.030, 0.100, 0.450] },
];

const clamp01 = (v) => Math.min(1, Math.max(0, v));

const linearToSrgb = (c) =>
  c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;

const srgbToLinear = (c) =>
  c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);

/** [r,g,b] lineal (0..1) → "#RRGGBB" sRGB para el HUD. */
export function linearToHex(rgb) {
  const hex = rgb
    .map((c) => Math.round(clamp01(linearToSrgb(clamp01(c))) * 255))
    .map((v) => v.toString(16).padStart(2, '0'))
    .join('');
  return `#${hex}`.toUpperCase();
}

/** "#RRGGBB" sRGB → [r,g,b] lineal (0..1). */
export function hexToLinear(hex) {
  const m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(hex.trim());
  if (!m) return [1, 1, 1];
  return [m[1], m[2], m[3]].map((h) => srgbToLinear(parseInt(h, 16) / 255));
}
