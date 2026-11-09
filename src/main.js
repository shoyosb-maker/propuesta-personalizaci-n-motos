import { PARTS } from './config.js';
import { ColorManager } from './paint.js';
import { setLoadProgress, createUI } from './ui.js';
import { createViewer } from './viewer.js';

const canvas = document.getElementById('renderCanvas');

async function boot() {
  const viewer = await createViewer(canvas, {
    onProgress: (ratio) => setLoadProgress(ratio),
  });

  const colors = new ColorManager();
  for (const part of PARTS) {
    const material = viewer.scene.getMaterialByName(part.mat);
    if (!material) {
      console.warn(`[panigale] material no encontrado en el glTF: ${part.mat}`);
      continue;
    }
    const meshes = viewer.meshes.filter((m) => m.material === material);
    colors.register(part.mat, material, meshes, part.gain, part.base);
  }

  viewer.start();
  createUI({ colors, viewer });

  window.__panigale = { viewer, colors };
}

boot().catch((error) => {
  console.error(error);
  const text = document.getElementById('loaderText');
  if (text) text.textContent = `No se pudo cargar el modelo — ${error.message}`;
});
