# Frontend Vite + React + TypeScript

Aplicación React recién inicializada con Vite y TypeScript. En este punto todavía no consume el backend: sirve como base limpia para incorporar `fetch` durante la clase.

## Requisitos

- Node.js 22 o posterior.
- pnpm 11 (Corepack puede activar la versión declarada en `package.json`).

## Iniciar el proyecto

```bash
pnpm install
pnpm dev
```

Abrir <http://127.0.0.1:5173/>.

## Comandos

```bash
pnpm dev       # servidor de desarrollo
pnpm build     # chequeo de tipos y compilación de producción
pnpm lint      # análisis estático
pnpm preview   # previsualización de la compilación
```

La integración con Django se agregará después de construir la ruta JSON en el backend.
