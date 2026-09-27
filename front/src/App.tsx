import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Nav, type Section } from "@/composants/Nav"
import { Accueil } from "@/ecrans/Accueil"

export default function App() {
  const [section, setSection] = useState<Section>("accueil")
  const [lance, setLance] = useState<string | null>(null)

  return (
    <div className="flex h-full">
      <Nav actif={section} onChange={(s) => { setSection(s); setLance(null) }} />
      <main className="relative flex-1 overflow-auto">
        <AnimatePresence mode="wait">
          {section === "accueil" && !lance && (
            <motion.div key="accueil" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Accueil onLancer={(e) => setLance(`${e.intention} · ${e.matiere.nom} · ${e.chapitre.titre}`)} />
            </motion.div>
          )}
          {lance && (
            <motion.div key="suite" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="grid h-full place-items-center text-gris">
              <div className="text-center">
                <p className="text-sm uppercase tracking-wide">Écran suivant (maquette à venir)</p>
                <p className="mt-2 font-titre text-2xl text-encre">{lance}</p>
                <button onClick={() => setLance(null)} className="mt-6 rounded-xl border-2 border-bleu px-5 py-2 font-semibold text-bleu">Retour</button>
              </div>
            </motion.div>
          )}
          {section !== "accueil" && !lance && (
            <motion.div key={section} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid h-full place-items-center text-gris">
              Maquette « {section} » à venir
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
