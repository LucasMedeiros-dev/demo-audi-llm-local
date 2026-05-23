import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em dev, o front roda em :5173 e o backend FastAPI em :8000.
// O proxy encaminha /api/* para o backend, evitando problemas de CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
