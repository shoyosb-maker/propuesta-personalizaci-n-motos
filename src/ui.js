/**
 * Dashboard: pinta la lista de piezas, la paleta, los controles y sincroniza
 * todo con el ColorManager.
 */

import { PointerEventTypes } from '@babylonjs/core/Events/pointerEvents';
import { PARTS, PRESETS, linearToHex, hexToLinear } from './config.js';

const $ = (id) => document.getElementById(id);

const sameRgb = (a, b) => a && b && a.every((v, i) => Math.abs(v - b[i]) < 0.004);

export function createUI({ colors, viewer }) {
  const available = PARTS.filter((p) => colors.has(p.mat));

  const els = {
    panel: $('panel'),
    partHint: $('partHint'),
    dropdown: $('dropdown'),
    dropdownTrigger: $('ddTrigger'),
    dropdownMenu: $('ddMenu'),
    dropdownLabel: $('ddLabel'),
    selectDot: $('selectDot'),
    palette: $('palette'),
    colorInput: $('colorInput'),
    colorValue: $('colorValue'),
    resetPart: $('resetPart'),
    btnRotate: $('btnRotate'),
    btnWire: $('btnWire'),
    btnScreenshot: $('btnScreenshot'),
    btnReset: $('btnReset'),
    statTris: $('statTris'),
    statParts: $('statParts'),
    statFps: $('statFps'),
    loader: $('loader'),
    loaderText: $('loaderText'),
    loaderBar: $('loaderBar'),
  };

  let selected = available[0] ?? null;

  // ── paleta ───────────────────────────────────────────────
  const swatchButtons = PRESETS.map((preset) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'swatch';
    btn.title = preset.name;
    btn.setAttribute('aria-label', preset.name);
    btn.setAttribute('aria-pressed', 'false');
    btn.style.background = linearToHex(preset.rgb);
    btn.addEventListener('click', () => {
      if (!selected) return;
      colors.apply(selected.mat, preset.rgb);
      refresh();
    });
    els.palette.appendChild(btn);
    return btn;
  });

  // ── desplegable de piezas ────────────────────────────────
  const dropdownItems = new Map();

  for (const part of available) {
    const li = document.createElement('li');
    li.className = 'dropdown-item';
    li.dataset.id = part.id;
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', 'false');
    li.innerHTML = '<span class="dot"></span><span class="name"></span><span class="hex"></span>';
    li.querySelector('.name').textContent = part.name;
    li.addEventListener('click', () => {
      select(part);
      closeDropdown();
      // Elegir pieza con la hoja plegada implica que se quiere editar: abrirla.
      if (isMobileLayout() && els.panel.classList.contains('is-collapsed')) setSheet(true);
    });
    els.dropdownMenu.appendChild(li);
    dropdownItems.set(part.id, { li, part });
  }

  // El `backdrop-filter` del panel lo convierte en containing block de los
  // elementos `position:fixed`; para que el menú se ancle al viewport lo sacamos
  // del panel y lo colgamos del body.
  document.body.appendChild(els.dropdownMenu);

  const isOpen = () => els.dropdownMenu.classList.contains('is-open');

  function openDropdown() {
    // position:fixed con coordenadas del trigger: el menú se cuelga del body
    // (el backdrop-filter del panel rompería el `fixed`) y así no lo recorta
    // el `overflow-y:auto` del panel.
    const rect = els.dropdownTrigger.getBoundingClientRect();
    const maxMenu = Math.min(window.innerHeight * 0.52, 360);
    const menuHeight = Math.min(els.dropdownMenu.scrollHeight + 14, maxMenu);
    const spaceBelow = window.innerHeight - rect.bottom - 8;
    const spaceAbove = rect.top - 8;
    const opensUp = spaceBelow < menuHeight && spaceAbove > spaceBelow;

    els.dropdownMenu.style.left = `${rect.left}px`;
    els.dropdownMenu.style.width = `${rect.width}px`;
    els.dropdownMenu.style.maxHeight = `${Math.max(150, Math.min(maxMenu, opensUp ? spaceAbove : spaceBelow))}px`;

    if (opensUp) {
      els.dropdownMenu.style.top = 'auto';
      els.dropdownMenu.style.bottom = `${window.innerHeight - rect.top + 8}px`;
      els.dropdownMenu.style.transformOrigin = 'bottom center';
    } else {
      els.dropdownMenu.style.bottom = 'auto';
      els.dropdownMenu.style.top = `${rect.bottom + 8}px`;
      els.dropdownMenu.style.transformOrigin = 'top center';
    }

    els.dropdownMenu.classList.add('is-open');
    els.dropdownTrigger.setAttribute('aria-expanded', 'true');
    setActive(selected?.id);
  }

  function closeDropdown() {
    els.dropdownMenu.classList.remove('is-open');
    els.dropdownMenu.style.maxHeight = '';
    els.dropdownTrigger.setAttribute('aria-expanded', 'false');
  }

  function setActive(id, reveal = false) {
    for (const [key, { li }] of dropdownItems) li.classList.toggle('is-active', key === id);
    if (!reveal) return;

    // scrollIntoView también mueve el panel (y su evento 'scroll' cerraba el
    // menú). Desplazamos sólo la lista.
    const entry = dropdownItems.get(id);
    if (!entry) return;
    const li = entry.li;
    const menu = els.dropdownMenu;
    const pad = 6;
    if (li.offsetTop - pad < menu.scrollTop) {
      menu.scrollTop = Math.max(0, li.offsetTop - pad);
    } else if (li.offsetTop + li.offsetHeight + pad > menu.scrollTop + menu.clientHeight) {
      menu.scrollTop = li.offsetTop + li.offsetHeight + pad - menu.clientHeight;
    }
  }

  function activeId() {
    for (const [key, { li }] of dropdownItems) {
      if (li.classList.contains('is-active')) return key;
    }
    return selected?.id;
  }

  function stepActive(delta) {
    const ids = available.map((p) => p.id);
    const current = Math.max(0, ids.indexOf(activeId()));
    setActive(ids[(current + delta + ids.length) % ids.length], true);
  }

  els.dropdownTrigger.addEventListener('click', () => {
    if (isOpen()) closeDropdown();
    else openDropdown();
  });

  els.dropdownTrigger.addEventListener('keydown', (event) => {
    const key = event.key;

    if (!isOpen()) {
      if (key === 'ArrowDown' || key === 'Enter' || key === ' ') {
        event.preventDefault();
        openDropdown();
      }
      return;
    }

    if (key === 'Escape') {
      event.preventDefault();
      closeDropdown();
    } else if (key === 'ArrowDown' || key === 'ArrowUp') {
      event.preventDefault();
      stepActive(key === 'ArrowDown' ? 1 : -1);
    } else if (key === 'Enter' || key === ' ') {
      event.preventDefault();
      const entry = dropdownItems.get(activeId());
      if (entry) {
        select(entry.part);
        closeDropdown();
      }
    }
  });

  document.addEventListener('pointerdown', (event) => {
    const inside =
      els.dropdown.contains(event.target) || els.dropdownMenu.contains(event.target);
    if (isOpen() && !inside) closeDropdown();
  });
  window.addEventListener('resize', () => {
    if (isOpen()) openDropdown();
  });
  els.panel.addEventListener('scroll', () => {
    if (isOpen()) closeDropdown();
  }, { passive: true });

  function currentRgb(part) {
    const entry = colors.get(part.mat);
    if (!entry) return [1, 1, 1];
    return entry.current ?? [entry.original.r, entry.original.g, entry.original.b];
  }

  function select(part) {
    selected = part;
    viewer.outlineMeshes(colors.meshesOf(part.mat));
    refresh();
  }

  function refresh() {
    if (!selected) return;

    els.partHint.textContent = selected.hint;

    const rgb = currentRgb(selected);
    const hex = linearToHex(rgb);
    els.dropdownLabel.textContent = selected.name;
    els.selectDot.style.background = hex;
    els.colorValue.textContent = hex;
    els.colorInput.value = hex.toLowerCase();

    for (const [id, { li, part }] of dropdownItems) {
      const itemHex = linearToHex(currentRgb(part));
      li.setAttribute('aria-selected', String(id === selected.id));
      li.querySelector('.dot').style.background = itemHex;
      li.querySelector('.hex').textContent = itemHex;
    }

    swatchButtons.forEach((btn, i) =>
      btn.setAttribute('aria-pressed', String(sameRgb(rgb, PRESETS[i].rgb))),
    );
  }

  // ── hoja desplegable (móvil) ─────────────────────────────
  const sheetGrip = $('sheetGrip');
  const isMobileLayout = () => window.innerWidth <= 900;
  const COLLAPSED_HEIGHT = 44;

  function setSheet(expanded, animate = true) {
    const panel = els.panel;
    const isCollapsed = panel.classList.contains('is-collapsed');
    if (expanded === !isCollapsed) return;

    if (!expanded) closeDropdown();
    panel.classList.toggle('is-collapsed', !expanded);
    sheetGrip.setAttribute('aria-expanded', String(expanded));

    if (!animate) {
      panel.style.height = expanded ? 'auto' : `${COLLAPSED_HEIGHT}px`;
      return;
    }

    // Animamos una altura concreta (no `max-height`): así el contenido se
    // descubre a velocidad constante y la hoja se siente deslizar.
    const from = panel.getBoundingClientRect().height;
    panel.style.height = 'auto';
    const to = expanded ? panel.getBoundingClientRect().height : COLLAPSED_HEIGHT;

    panel.style.height = `${from}px`;
    void panel.offsetHeight;
    panel.style.height = `${to}px`;

    clearTimeout(panel._sheetTimer);
    panel._sheetTimer = setTimeout(() => {
      panel.style.height = expanded ? 'auto' : `${COLLAPSED_HEIGHT}px`;
    }, 480);
  }

  setSheet(!isMobileLayout(), false);

  sheetGrip.addEventListener('click', () => {
    setSheet(els.panel.classList.contains('is-collapsed'));
  });

  let wasMobile = isMobileLayout();
  window.addEventListener('resize', () => {
    const now = isMobileLayout();
    if (now === wasMobile) return;
    wasMobile = now;
    setSheet(!now);
  });

  // ── controles ────────────────────────────────────────────
  els.colorInput.addEventListener('input', () => {
    if (!selected) return;
    const linear = hexToLinear(els.colorInput.value);
    colors.apply(selected.mat, linear);
    refresh();
  });

  els.resetPart.addEventListener('click', () => {
    if (!selected) return;
    colors.reset(selected.mat);
    refresh();
  });

  els.btnRotate.addEventListener('click', () => {
    const next = !viewer.getAutoRotate();
    viewer.setAutoRotate(next);
    els.btnRotate.classList.toggle('is-on', next);
  });

  let wire = false;
  els.btnWire.addEventListener('click', () => {
    wire = !wire;
    viewer.setWireframe(wire);
    els.btnWire.classList.toggle('is-on', wire);
  });

  els.btnReset.addEventListener('click', () => {
    colors.resetAll();
    refresh();
  });

  els.btnScreenshot.addEventListener('click', async () => {
    const dataUrl = await viewer.screenshot();
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = `panigale-v4sp-${Date.now()}.png`;
    a.click();
  });

  // ── selección tocando el modelo ──────────────────────────
  viewer.scene.onPointerObservable.add((info) => {
    if (info.type !== PointerEventTypes.POINTERDOWN) return;
    const pick = viewer.scene.pick(viewer.scene.pointerX, viewer.scene.pointerY);
    const matName = pick?.pickedMesh?.material?.name;
    if (!matName) return;
    const part = available.find((p) => p.mat === matName);
    if (part) select(part);
  });

  // ── estadísticas y loader ────────────────────────────────
  els.statTris.textContent = Math.round(viewer.stats.triangles).toLocaleString('es-CO');
  els.statParts.textContent = String(viewer.stats.materials);
  setInterval(() => {
    els.statFps.textContent = String(Math.round(viewer.engine.getFps()));
  }, 500);

  els.loaderBar.style.width = '100%';
  els.loaderText.textContent = 'Listo';
  setTimeout(() => els.loader.classList.add('is-done'), 320);

  select(selected);

  return { refresh, select };
}

export function setLoadProgress(ratio) {
  const bar = $('loaderBar');
  const text = $('loaderText');
  if (bar) bar.style.width = `${Math.round(ratio * 100)}%`;
  if (text) text.textContent = `Cargando modelo… ${Math.round(ratio * 100)}%`;
}
