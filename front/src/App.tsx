// Coquille de l'interface : barre latérale + écran de la route courante (routes.ts), transitions animées.
// Aucune donnée fictive : prénom, persona et leviers d'adaptation viennent de /api/infos.
import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Nav } from "@/composants/Nav"
import { infos as lireInfos, type Infos } from "@/api/jules"
import { appliquerLeviers } from "@/modules/fiches/ponts"
import { sectionDe, useRoute, type Route } from "@/routes"
import { ECRANS } from "@/ecrans/registre"
import type { SectionId } from "@/config/navigation"
import { RappelARanger } from "@/modules/sources/pieces"
import { choisirMatiere, lireMatiere } from "@/modules/accueil/etat"

/** Entrée d'une section : ouverte sur la matière choisie en haut de la barre (idée A), sinon toutes. */
const routeDeSection = (s: SectionId, m = lireMatiere()): Route | null =>
  s === "fiches" ? { ecran: "fiches", matiere: m } : s === "lecons" ? { ecran: "lecons", matiere: m }
    : s === "supports" ? { ecran: "supports", matiere: m } : null

/** Matière portée par la route (écrans par matière) : elle devient la matière courante. */
const matiereDe = (r: Route): string | null | undefined =>
  r.ecran === "fiches" || r.ecran === "lecons" || r.ecran === "supports" ? r.matiere : r.ecran === "support" ? r.matiere : undefined

export default function App() {
  const [route, aller] = useRoute()
  const [infos, setInfos] = useState<Infos | null>(null)
  useEffect(() => {
    lireInfos().then((i) => { setInfos(i); appliquerLeviers(i) }).catch(() => {})
  }, [])
  useEffect(() => { const m = matiereDe(route); if (m) choisirMatiere(m) }, [route])
  const Ecran = ECRANS[route.ecran]
  const cle = route.ecran === "fiche" || route.ecran === "lecon" ? `${route.ecran}-${route.notion}`
    : route.ecran === "support" || route.ecran === "perso" || route.ecran === "dossier" ? `${route.ecran}-${route.id}` : route.ecran

  return (
    <TooltipProvider delayDuration={300}>
      <SidebarProvider className="h-full min-h-0">
        <Nav actif={sectionDe(route)} prenom={infos?.prenom || ""} route={route} aller={aller} onChange={(s) => { const r = routeDeSection(s); if (r) aller(r) }}
          onMatiere={(m) => { const r = routeDeSection(sectionDe(route), m); if (r) aller(r) }} />
        <SidebarInset className="relative h-full min-h-0 overflow-hidden bg-[#FBFBFE]">
          <SidebarTrigger className="absolute top-3 left-3 z-40 bg-white/80 text-gris shadow-relief backdrop-blur md:hidden" />
          <AnimatePresence mode="wait">
            <motion.div key={cle} className="h-full"
              initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              transition={{ type: "spring", stiffness: 300, damping: 32 }}>
              <Ecran route={route} aller={aller} infos={infos} />
            </motion.div>
          </AnimatePresence>
          {route.ecran !== "perso" && <RappelARanger onOuvrir={(id) => aller({ ecran: "perso", id })} />}
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  )
}
