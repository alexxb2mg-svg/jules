import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Nav } from "@/composants/Nav"
import type { SectionId } from "@/config/navigation"
import { ECRANS } from "@/ecrans/registre"
import { EcranPartage } from "@/ecrans/EcranPartage"
import type { Lancement } from "@/composants/Parcours"
import { ELEVE, MATIERES } from "@/donnees"

/** Lien direct #/lecon/<notion> (favoris, tests) : retrouve le chapitre correspondant. */
function depuisAdresse(): Lancement | null {
  const m = window.location.hash.match(/^#\/lecon\/([\w-]+)/)
  if (!m) return null
  for (const matiere of MATIERES) {
    const chapitre = matiere.chapitres.find((c) => c.notion === m[1])
    if (chapitre) return { intention: "reviser", matiere, chapitre }
  }
  return null
}

export default function App() {
  const [section, setSection] = useState<SectionId>("accueil")
  const [lance, setLanceEtat] = useState<Lancement | null>(depuisAdresse)
  const setLance = (l: Lancement | null) => {
    setLanceEtat(l)
    if (!l || !window.location.hash.startsWith(`#/lecon/${l.chapitre.notion}`))
      history.replaceState(null, "", l?.chapitre.notion ? `#/lecon/${l.chapitre.notion}` : "#/")
  }
  const Ecran = ECRANS[section]

  return (
    <TooltipProvider delayDuration={300}>
      <SidebarProvider className="h-full min-h-0">
        <Nav actif={section} eleve={ELEVE} onChange={(s) => { setSection(s); setLance(null) }} />
        <SidebarInset className="relative h-full min-h-0 overflow-hidden">
          <SidebarTrigger className="absolute top-3 left-3 z-20 text-gris md:hidden" />
          <AnimatePresence mode="wait">
            {lance ? (
              <motion.div key={`lecon-${lance.chapitre.id}`} className="h-full"
                initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                transition={{ type: "spring", stiffness: 260, damping: 30 }}>
                {lance.chapitre.notion ? (
                  <EcranPartage notion={lance.chapitre.notion}
                    fil={`${lance.intention === "devoir" ? "Devoir" : "Révision"} · ${lance.matiere.nom} · ${lance.chapitre.titre}`}
                    onRetour={() => setLance(null)} />
                ) : (
                  <div className="grid h-full place-items-center text-center text-gris">
                    <div>
                      <p className="font-titre text-2xl text-encre">{lance.chapitre.titre}</p>
                      <p className="mt-2">Pas encore de leçon pour ce chapitre.</p>
                      <button onClick={() => setLance(null)} className="mt-6 rounded-xl border-2 border-bleu px-5 py-2 font-semibold text-bleu">Retour</button>
                    </div>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div key={section} className="h-full overflow-y-auto" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Ecran onLancer={setLance} />
              </motion.div>
            )}
          </AnimatePresence>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  )
}
