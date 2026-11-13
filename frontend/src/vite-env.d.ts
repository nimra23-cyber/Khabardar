/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the backend API for the deployed frontend (build-time). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
