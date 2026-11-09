/**
 * Escena Babylon: cámara orbital 360°, iluminación de estudio, entorno PBR y
 * carga del glTF exportado desde Blender.
 */

import {
  ArcRotateCamera,
  Color3,
  Color4,
  DirectionalLight,
  Engine,
  EquiRectangularCubeTexture,
  HemisphericLight,
  ImageProcessingConfiguration,
  MeshBuilder,
  PBRMaterial,
  Scene,
  SceneLoader,
  ShadowGenerator,
  Tools,
  TransformNode,
  Vector3,
} from '@babylonjs/core';

import '@babylonjs/loaders/glTF';

const BASE = import.meta.env.BASE_URL;
const MODEL_URL = `${BASE}assets/panigale_web.glb`;
const ENV_URL = `${BASE}assets/studio_env.jpg`;

export async function createViewer(canvas, { onProgress } = {}) {
  const engine = new Engine(canvas, true, {
    preserveDrawingBuffer: true,
    stencil: true,
    alpha: true,
    antialias: true,
  });
  engine.setHardwareScalingLevel(1 / Math.min(window.devicePixelRatio || 1, 2));

  const scene = new Scene(engine);
  scene.clearColor = new Color4(0, 0, 0, 0);

  const camera = new ArcRotateCamera('cam', 2.2, 1.22, 3.6, new Vector3(0, 0.6, 0), scene);
  camera.attachControl(canvas, true);
  camera.lowerRadiusLimit = 1.5;
  camera.upperRadiusLimit = 8;
  camera.lowerBetaLimit = 0.12;
  camera.upperBetaLimit = 1.53;
  camera.wheelDeltaPercentage = 0.012;
  camera.pinchDeltaPercentage = 0.012;
  camera.inertia = 0.84;
  camera.angularSensibilityX = 900;
  camera.angularSensibilityY = 900;
  camera.minZ = 0.03;
  camera.maxZ = 60;

  // ── iluminación de estudio ───────────────────────────────
  const key = new DirectionalLight('key', new Vector3(-0.62, -1, -0.42), scene);
  key.position = new Vector3(2.6, 4.4, 1.9);
  key.intensity = 3.4;
  key.shadowMinZ = 0.4;
  key.shadowMaxZ = 14;

  const fill = new HemisphericLight('fill', new Vector3(0.15, 1, 0.1), scene);
  fill.intensity = 0.5;
  fill.diffuse = new Color3(0.72, 0.78, 0.9);
  fill.groundColor = new Color3(0.05, 0.055, 0.07);

  const rim = new DirectionalLight('rim', new Vector3(0.85, -0.35, 0.9), scene);
  rim.intensity = 2.0;
  rim.diffuse = new Color3(0.58, 0.66, 0.85);

  const shadow = new ShadowGenerator(2048, key);
  shadow.useBlurExponentialShadowMap = true;
  shadow.blurKernel = 28;
  shadow.depthScale = 45;
  shadow.darkness = 0.45;
  shadow.bias = 0.008;
  shadow.normalBias = 0.008;

  // ── entorno PBR (reflejos) ───────────────────────────────
  const envTexture = new EquiRectangularCubeTexture(ENV_URL, scene, 256);
  envTexture.gammaSpace = true;
  scene.environmentTexture = envTexture;
  scene.environmentIntensity = 0.62;

  const ip = scene.imageProcessingConfiguration;
  ip.toneMappingEnabled = true;
  ip.toneMappingType = ImageProcessingConfiguration.TONEMAPPING_ACES;
  ip.exposure = 0.88;
  ip.contrast = 1.22;

  // ── carga del modelo ─────────────────────────────────────
  const result = await SceneLoader.ImportMeshAsync(null, '', MODEL_URL, scene, (evt) => {
    if (!onProgress) return;
    const ratio = evt.total ? evt.loaded / evt.total : 0;
    onProgress(Math.min(0.99, ratio), evt.loaded, evt.total);
  });

  const root = new TransformNode('bikeRoot', scene);
  const meshes = [];

  for (const mesh of result.meshes) {
    if (!mesh.getTotalVertices || mesh.getTotalVertices() === 0) continue;
    mesh.setParent(root);
    mesh.receiveShadows = true;
    shadow.addShadowCaster(mesh);
    meshes.push(mesh);
  }

  // ── encuadre automático ──────────────────────────────────
  const bounds = computeBounds(meshes);
  const center = bounds.min.add(bounds.max).scale(0.5);
  const span = bounds.max.subtract(bounds.min);
  const radius = Math.max(span.x, span.y, span.z);

  camera.setTarget(new Vector3(center.x, bounds.min.y + span.y * 0.44, center.z));

  /**
   * Distancia mínima para que la moto quepa a lo ancho. El fov de Babylon es
   * vertical, así que en un móvil en vertical el campo horizontal es muy
   * estrecho y hay que retroceder. En escritorio manda el encuadre "de estudio".
   */
  function fitCamera() {
    const aspect = engine.getAspectRatio(camera) || 1;
    const horizontalFov = 2 * Math.atan(Math.tan(camera.fov / 2) * aspect);
    const fitWidth = (Math.max(span.x, span.z) * 1.12) / (2 * Math.tan(horizontalFov / 2));

    camera.radius = Math.max(radius * 1.72, fitWidth);
    camera.lowerRadiusLimit = radius * 0.72;
    camera.upperRadiusLimit = Math.max(radius * 3.6, camera.radius * 1.6);
  }

  fitCamera();

  // ── encuadre: dejar la moto en el hueco libre de la interfaz ─────────────
  const framing = { brandBottom: 0 };

  function updateLayout() {
    const brand = document.querySelector('.brand');
    framing.brandBottom = brand ? brand.getBoundingClientRect().bottom : 0;
  }

  /**
   * Desplaza el objetivo en espacio de vista para centrar la moto donde no hay
   * interfaz: a la izquierda en escritorio (panel de 336 px) y arriba en móvil
   * (hoja inferior). Se recalcula cada frame porque tanto el zoom como la altura
   * de la hoja cambian la escala y el hueco disponible.
   */
  function applyFramingOffset() {
    if (window.innerWidth > 900) {
      camera.targetScreenOffset.x = -0.42;
      camera.targetScreenOffset.y = 0;
      return;
    }

    const viewH = window.innerHeight;
    const panel = document.getElementById('panel');
    const panelTop = panel ? panel.getBoundingClientRect().top : viewH;
    const targetY = (framing.brandBottom + panelTop) / 2;

    const worldPerPixel = (2 * camera.radius * Math.tan(camera.fov / 2)) / viewH;
    const centerY = (bounds.min.y + bounds.max.y) / 2;
    const lift = (centerY - camera.target.y) / worldPerPixel;
    const projectedY = viewH / 2 - lift;

    camera.targetScreenOffset.x = 0;
    camera.targetScreenOffset.y = (projectedY - targetY) * worldPerPixel;
  }

  updateLayout();
  applyFramingOffset();

  // ── plataforma plateada ──────────────────────────────────
  // Da contraste con la moto (que es muy oscura) y un punto de apoyo físico.
  const platformRadius = Math.max(span.x, span.z) * 0.6 + 0.1;
  const platformTop = bounds.min.y;

  const silver = new PBRMaterial('PlatformSilver', scene);
  silver.albedoColor = new Color3(0.66, 0.68, 0.72);
  silver.metallic = 0.5;
  silver.roughness = 0.3;
  silver.environmentIntensity = 1.15;
  silver.specularIntensity = 1.1;

  const graphite = new PBRMaterial('PlatformRim', scene);
  graphite.albedoColor = new Color3(0.03, 0.034, 0.042);
  graphite.metallic = 0.6;
  graphite.roughness = 0.45;

  // La base queda 5 mm por debajo de la tapa: si comparten plano, el fan de
  // triángulos de ambas tapas produce z-fighting en forma de estrías radiales.
  const platformBase = MeshBuilder.CreateCylinder(
    'platformBase',
    { diameter: platformRadius * 2, height: 0.14, tessellation: 128 },
    scene,
  );
  platformBase.position.y = platformTop - 0.075;
  platformBase.receiveShadows = true;
  platformBase.isPickable = false;
  platformBase.material = graphite;

  const platformTopDisc = MeshBuilder.CreateCylinder(
    'platformTop',
    { diameter: platformRadius * 2 - 0.045, height: 0.11, tessellation: 128 },
    scene,
  );
  platformTopDisc.position.y = platformTop - 0.055;
  platformTopDisc.receiveShadows = true;
  platformTopDisc.isPickable = false;
  platformTopDisc.material = silver;

  // ── resaltado de la pieza seleccionada ───────────────────
  // Contorno fino en vez de HighlightLayer: con 221k triángulos el glow por
  // post-proceso cuesta ~4x más frames.
  const OUTLINE_COLOR = new Color3(0.86, 0.13, 0.24);
  let outlined = [];

  // ── estado y utilidades ──────────────────────────────────
  let autoRotate = true;

  scene.onBeforeRenderObservable.add(() => {
    applyFramingOffset();
    if (!autoRotate) return;
    camera.alpha += engine.getDeltaTime() * 0.00019;
  });

  const stats = {
    triangles: meshes.reduce((sum, m) => sum + m.getTotalIndices() / 3, 0),
    meshes: meshes.length,
    materials: new Set(meshes.map((m) => m.material?.name).filter(Boolean)).size,
    bounds,
  };

  return {
    engine,
    scene,
    camera,
    meshes,
    root,
    stats,

    start() {
      engine.runRenderLoop(() => scene.render());
      window.addEventListener('resize', () => {
        engine.resize();
        fitCamera();
        updateLayout();
        applyFramingOffset();
      });
      // El panel cambia de alto (paleta, textos); reencuadrar cuando pase.
      if (typeof ResizeObserver !== 'undefined') {
        const panel = document.getElementById('panel');
        if (panel) {
          new ResizeObserver(() => {
            updateLayout();
            applyFramingOffset();
          }).observe(panel);
        }
      }
    },

    setAutoRotate(value) {
      autoRotate = value;
    },

    getAutoRotate() {
      return autoRotate;
    },

    setWireframe(value) {
      const seen = new Set();
      for (const mesh of meshes) {
        const mat = mesh.material;
        if (!mat || seen.has(mat)) continue;
        seen.add(mat);
        mat.wireframe = value;
      }
    },

    outlineMeshes(list) {
      for (const mesh of outlined) mesh.renderOutline = false;
      outlined = list ?? [];
      for (const mesh of outlined) {
        mesh.renderOutline = true;
        mesh.outlineColor = OUTLINE_COLOR;
        mesh.outlineWidth = 0.004;
      }
    },

    clearOutline() {
      for (const mesh of outlined) mesh.renderOutline = false;
      outlined = [];
    },

    async screenshot() {
      return Tools.CreateScreenshotAsync(engine, camera, { precision: 1 });
    },
  };
}

function computeBounds(meshes) {
  const min = new Vector3(Infinity, Infinity, Infinity);
  const max = new Vector3(-Infinity, -Infinity, -Infinity);

  for (const mesh of meshes) {
    mesh.computeWorldMatrix(true);
    const bb = mesh.getBoundingInfo().boundingBox;
    min.minimizeInPlace(bb.minimumWorld);
    max.maximizeInPlace(bb.maximumWorld);
  }

  return { min, max };
}
