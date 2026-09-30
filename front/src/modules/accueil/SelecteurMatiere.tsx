// A : sélecteur de matière global (inspiré de DinoBot : une pastille à la couleur de la matière, qui vaut pour
// tous les écrans). Couleurs = matieres-couleurs.css (via styleMatiere), icônes = config/matieres.ts.
import { useEffect, useMemo, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Check, ChevronsUpDown, Library } from "lucide-react"
import { cn } from "@/lib/utils"
import { useMotion } from "@/lib/motion"
import { fiches } from "@/api/jules"
import { iconeMatiere, ORDRE_MATIERES } from "@/config/matieres"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import { choisirMatiere, useMatiere } from "./etat"

export const TOUTES_MATIERES = "Toutes les matières"

export function SelecteurMatiere({ onChoix }: { onChoix: (m: string | null) => void }) {
  const courante = useMatiere()
  const [liste, setListe] = useState<{ id: string; nom: string }[]>([])
  const [ouvert, setOuvert] = useState(false)
  const boite = useRef<HTMLDivElement>(null)
  useEffect(() => { fiches.index().then((i) => setListe(i.matieres.map((m) => ({ id: m.id, nom: m.nom.replace(/ \(.*\)$/, "") })))).catch(() => {}) }, [])
  useEffect(() => {
    if (!ouvert) return
    const fermer = (e: MouseEvent) => { if (!boite.current?.contains(e.target as Node)) setOuvert(false) }
    const echap = (e: KeyboardEvent) => { if (e.key === "Escape") setOuvert(false) }
    addEventListener("mousedown", fermer); addEventListener("keydown", echap)
    return () => { removeEventListener("mousedown", fermer); removeEventListener("keydown", echap) }
  }, [ouvert])
  const triees = useMemo(() => {
    const rang = (id: string) => { const i = ORDRE_MATIERES.indexOf(id); return i < 0 ? 99 : i }
    return [...liste].sort((a, b) => rang(a.id) - rang(b.id))
  }, [liste])
  const nom = triees.find((m) => m.id === courante)?.nom ?? TOUTES_MATIERES
  const Icone = courante ? iconeMatiere(courante) : Library
  const choisir = (m: string | null) => { choisirMatiere(m); setOuvert(false); onChoix(m) }
  const { tap } = useMotion()

  return (
    <div ref={boite} className="relative" style={courante ? styleMatiere(courante) : undefined}>
      <motion.button {...tap} onClick={() => setOuvert((o) => !o)} aria-haspopup="listbox" aria-expanded={ouvert}
        aria-label={`Matière : ${nom}`} title={nom}
        className={cn("flex min-h-11 w-full items-center gap-2 rounded-full px-4 py-2 text-left text-petit font-semibold transition-colors",
          "group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0",
          courante ? "bg-(--m-texte) text-white" : "bg-surface-2 text-encre")}>
        <Icone size={17} className="shrink-0" />
        <span className="flex-1 truncate group-data-[collapsible=icon]:hidden">{nom}</span>
        <ChevronsUpDown size={15} className="shrink-0 opacity-70 group-data-[collapsible=icon]:hidden" />
      </motion.button>
      <AnimatePresence>
        {ouvert && (
          <motion.ul role="listbox" aria-label="Matières" initial={{ opacity: 0, y: -6, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 z-50 mt-1.5 max-h-[60vh] w-[250px] list-none overflow-y-auto rounded-surface bg-popover p-1.5 shadow-souleve">
            <Option on={!courante} onClick={() => choisir(null)} Icone={Library} nom={TOUTES_MATIERES} />
            {triees.map((m) => (
              <Option key={m.id} on={m.id === courante} onClick={() => choisir(m.id)} Icone={iconeMatiere(m.id)} nom={m.nom} matiere={m.id} />
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  )
}

function Option({ on, onClick, Icone, nom, matiere }: { on: boolean; onClick: () => void; Icone: typeof Library; nom: string; matiere?: string }) {
  return (
    <li role="option" aria-selected={on} style={matiere ? styleMatiere(matiere) : undefined}>
      <button onClick={onClick}
        className={cn("flex min-h-10 w-full items-center gap-2.5 rounded-full px-3 py-2 text-left text-petit font-semibold transition-colors",
          on ? "bg-(--m-texte,var(--j-bleu)) text-white" : "text-(--m-texte,var(--j-encre)) hover:bg-(--m-fond,var(--j-nav))")}>
        <Icone size={16} className="shrink-0" /><span className="flex-1">{nom}</span>{on && <Check size={15} />}
      </button>
    </li>
  )
}
