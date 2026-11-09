/**
 * Gestor de acabados.
 *
 * El color se aplica sobre `albedoColor` del PBRMaterial. En glTF ese campo es el
 * baseColorFactor, que se multiplica con la textura de color: así conservamos el
 * grano, los mapas de normales y los calcados de la librea, y sólo cambia el tono.
 *
 * `gain` compensa que la textura de color sea más oscura o más clara que 1: para
 * una pieza metálica oscura hay que amplificar el color elegido para que el
 * resultado visible coincida con la muestra del HUD.
 */

import { Color3 } from '@babylonjs/core/Maths/math.color';

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

export class ColorManager {
  constructor() {
    /** @type {Map<string, {mat: any, meshes: any[], gain: number, original: Color3, current: number[]|null}>} */
    this.entries = new Map();
  }

  register(matName, mat, meshes, gain = 1, base = null) {
    const original = base ? new Color3(base[0], base[1], base[2]) : mat.albedoColor.clone();
    if (base) mat.albedoColor = original.clone();
    this.entries.set(matName, {
      mat,
      meshes,
      gain,
      original,
      current: null,
    });
  }

  has(matName) {
    return this.entries.has(matName);
  }

  get(matName) {
    return this.entries.get(matName);
  }

  /** rgb en espacio lineal 0..1 */
  apply(matName, rgb) {
    const entry = this.entries.get(matName);
    if (!entry) return null;

    const [r, g, b] = rgb;
    entry.mat.albedoColor = new Color3(
      clamp(r * entry.gain, 0, 24),
      clamp(g * entry.gain, 0, 24),
      clamp(b * entry.gain, 0, 24),
    );
    entry.current = [r, g, b];
    return entry;
  }

  reset(matName) {
    const entry = this.entries.get(matName);
    if (!entry) return;
    entry.mat.albedoColor = entry.original.clone();
    entry.current = null;
  }

  resetAll() {
    for (const name of this.entries.keys()) this.reset(name);
  }

  meshesOf(matName) {
    return this.entries.get(matName)?.meshes ?? [];
  }

  uniqueMaterials() {
    return [...this.entries.values()].map((e) => e.mat);
  }
}
