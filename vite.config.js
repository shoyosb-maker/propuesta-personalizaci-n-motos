import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  // Dependencias y caché viven fuera de esta carpeta para que el proyecto se
  // pueda subir a GitHub tal cual, sin miles de archivos de node_modules.
  cacheDir: '../.vite-cache',
  server: {
    port: 5173,
    strictPort: false,
    open: false,
  },
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 4000,
  },
});
