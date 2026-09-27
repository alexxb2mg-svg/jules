import path from "node:path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// Le build sort dans jules/web/static/app : servi par FastAPI, aucune requête externe.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  base: "/static/app/",
  build: { outDir: "../jules/web/static/app", emptyOutDir: true },
  server: { proxy: { "/api": "http://127.0.0.1:8799", "/static/polices": "http://127.0.0.1:8799" } },
})
