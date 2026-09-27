import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Nav } from "@/composants/Nav"
import type { SectionId } from "@/config/navigation"
import { ECRANS } from "@/ecrans/registre"
import type { Lancement } from "@/composants/Parcours"
import { ELEVE } from "@/donnees"

export default function App() {
  const [section, setSection] = useState<SectionId>("accueil")
  const [lance, setLance] = useState<Lancement | null>(null)
  const Ecran = ECRANS[section]

  return (
    <div className="flex h-full">
      <Nav actif={section} eleve={ELEVE} onChange={(s) => { setSection(s); setLance(null) }} />
      <main className="relative flex-1 overflow-auto">
        <AnimatePresence mode="wait">
          {lance ? (
            <motion.div key="suite" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="grid h-full place-items-center text-gris">
              <div className="text-center">
                <p className="text-sm uppercase tracking-wide">Écran suivant (maquette à venir)</p>
                <p className="mt-2 font-titre text-2xl text-encre">{lance.intention} · {lance.matiere.nom} · {lance.chapitre.titre}</p>
                <button onClick={() => setLance(null)} className="mt-6 rounded-xl border-2 border-bleu px-5 py-2 font-semibold text-bleu">Retour</button>
              </div>
            </motion.div>
          ) : (
            <motion.div key={section} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
              <Ecran onLancer={setLance} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
