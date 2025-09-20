export const appConfig = {
  backendBaseUrl: (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, ''),
};
