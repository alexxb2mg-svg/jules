import fs from "node:fs"
import path from "node:path"
import { defineConfig, type Plugin } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// Le build sort dans jules/web/static/app : servi par FastAPI à côté de /static, aucune requête externe.
// En dev/preview : les fichiers communs de /static sont lus dans CE dépôt (jules/web/static), les routes
// dynamiques du serveur (API, rappels.js et gabarits.js assemblés depuis les extensions) sont relayées.
const SERVEUR = "http://127.0.0.1:8799"
const STATIQUE = path.resolve(__dirname, "../jules/web/static")
const COMMUNS = ["matieres-couleurs.css", "fiche-contenu.css", "symboles.css", "adaptations.css", "symboles.js"]
const proxy = Object.fromEntries(["/api", "/static/polices", "/rappels.js", "/gabarits.js", "/discuter"].map((p) => [p, SERVEUR]))

function statiqueCommun(): Plugin {
  const servir = (req: { url?: string }, res: import("node:http").ServerResponse, suite: () => void) => {
    const nom = (req.url || "").split("?")[0].replace(/^\/static\//, "")
    if (!COMMUNS.includes(nom)) return suite()
    res.setHeader("Content-Type", nom.endsWith(".css") ? "text/css; charset=utf-8" : "text/javascript; charset=utf-8")
    res.end(fs.readFileSync(path.join(STATIQUE, nom)))
  }
  return {
    name: "jules-statique-commun",
    configureServer: (s) => { s.middlewares.use(servir) },
    configurePreviewServer: (s) => { s.middlewares.use(servir) },
  }
}

export default defineConfig({
  plugins: [statiqueCommun(), react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  base: "/static/app/",
  build: { outDir: "../jules/web/static/app", emptyOutDir: true },
  server: { proxy },
  preview: { proxy },
})
