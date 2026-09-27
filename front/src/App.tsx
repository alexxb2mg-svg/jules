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

const ROUTE_DE_SECTION: Partial<Record<SectionId, Route>> = {
  fiches: { ecran: "fiches", matiere: null },
  lecons: { ecran: "lecons", matiere: null },
  supports: { ecran: "supports", matiere: null },
}

export default function App() {
  const [route, aller] = useRoute()
  const [infos, setInfos] = useState<Infos | null>(null)
  useEffect(() => {
    lireInfos().then((i) => { setInfos(i); appliquerLeviers(i) }).catch(() => {})
  }, [])
  const Ecran = ECRANS[route.ecran]
  const cle = route.ecran === "fiche" || route.ecran === "lecon" ? `${route.ecran}-${route.notion}` : route.ecran === "support" ? `support-${route.id}` : route.ecran

  return (
    <TooltipProvider delayDuration={300}>
      <SidebarProvider className="h-full min-h-0">
        <Nav actif={sectionDe(route)} prenom={infos?.prenom || ""} onChange={(s) => { const r = ROUTE_DE_SECTION[s]; if (r) aller(r) }} />
        <SidebarInset className="relative h-full min-h-0 overflow-hidden bg-[#FBFBFE]">
          <SidebarTrigger className="absolute top-3 left-3 z-40 bg-white/80 text-gris shadow-relief backdrop-blur md:hidden" />
          <AnimatePresence mode="wait">
            <motion.div key={cle} className="h-full"
              initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              transition={{ type: "spring", stiffness: 300, damping: 32 }}>
              <Ecran route={route} aller={aller} infos={infos} />
            </motion.div>
          </AnimatePresence>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  )
}
