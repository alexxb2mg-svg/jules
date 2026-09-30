// E : le chemin d'une notion, en étapes courtes (inspiré du parcours de chapitre de Knowunity) :
// lire la fiche → faire la leçon (si elle existe) → m'entraîner (si la fiche v2 est servable) → cartes mémoire.
// Une seule étape « à faire » est mise en avant ; les étapes faites sont cochées.
// Fait : fiche lue jusqu'au bout, leçon terminée, série finie (mémorisé ici) ; cartes = support validé (serveur).
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { BookOpen, Check, Dumbbell, FileText, Layers } from "lucide-react"
import { cn } from "@/lib/utils"
import { studio } from "@/api/jules"
import { useEtapes, type Etape } from "./etat"

export const CHEMIN = {
  titre: "Ton chemin",
  fiche: "Lire la fiche",
  lecon: "Faire la leçon",
  exercices: "M'entraîner",
  cartes: "Mes cartes mémoire",
  aFaire: "à faire",
}

type Pas = { id: Etape | "cartes"; nom: string; Icone: typeof Check; fait: boolean; aller: () => void }

export function Chemin({ notion, matiere, avecLecon, avecExercices, onFiche, onLecon, onExercices, onCartes, horizontal }: {
  notion: string; matiere: string; avecLecon: boolean; avecExercices: boolean
  onFiche: () => void; onLecon: () => void; onExercices: () => void; onCartes: () => void; horizontal?: boolean
}) {
  const faites = useEtapes(notion)
  const [cartes, setCartes] = useState(false)
  useEffect(() => {
    let annule = false
    studio.notions(matiere).then((c) => {
      const n = c.notions.find((x) => x.id === notion)
      if (!annule) setCartes(!!n?.supports.some((s) => s.type === "cartes_memoire" && s.statut === "valide"))
    }).catch(() => {})
    return () => { annule = true }
  }, [notion, matiere])

  const pas: Pas[] = [
    { id: "fiche", nom: CHEMIN.fiche, Icone: FileText, fait: faites.includes("fiche"), aller: onFiche },
    ...(avecLecon ? [{ id: "lecon" as const, nom: CHEMIN.lecon, Icone: BookOpen, fait: faites.includes("lecon"), aller: onLecon }] : []),
    ...(avecExercices ? [{ id: "exercices" as const, nom: CHEMIN.exercices, Icone: Dumbbell, fait: faites.includes("exercices"), aller: onExercices }] : []),
    { id: "cartes", nom: CHEMIN.cartes, Icone: Layers, fait: cartes, aller: onCartes },
  ]
  const suivant = pas.find((p) => !p.fait)?.id

  return (
    <nav data-sans-symboles aria-label={CHEMIN.titre}>
      <p className={cn("mt-0 mb-2 text-petit font-semibold tracking-wide text-gris", horizontal && "sr-only")}>{CHEMIN.titre}</p>
      <ol className={cn("m-0 list-none p-0", horizontal ? "-mr-6 flex gap-1.5 overflow-x-auto pr-6 pb-1 [scrollbar-width:none]" : "relative flex flex-col gap-1")}>
        {pas.map((p, i) => {
          const actif = p.id === suivant
          return (
            <li key={p.id} className={cn("relative", !horizontal && i < pas.length - 1 && "pb-1")}>
              {!horizontal && i < pas.length - 1 && (
                <span aria-hidden className={cn("absolute top-9 bottom-0 left-[17px] w-0.5", p.fait ? "bg-(--m-accent)" : "bg-bord")} />
              )}
              <motion.button onClick={p.aller} whileHover={{ x: horizontal ? 0 : 2 }} whileTap={{ scale: 0.97 }}
                aria-current={actif ? "step" : undefined}
                className={cn("relative flex items-center gap-2.5 rounded-2xl text-left transition-colors",
                  horizontal ? "shrink-0 px-3 py-1.5 text-petit whitespace-nowrap" : "w-full px-1 py-1 text-petit",
                  actif && (horizontal ? "bg-(--m-texte) text-white" : "bg-(--m-fond) pr-3"),
                  !actif && "hover:bg-(--m-fond)")}>
                <span className={cn("grid shrink-0 place-items-center rounded-full",
                  horizontal ? "size-5" : "size-8",
                  p.fait ? "bg-(--m-accent) text-white" : actif ? (horizontal ? "bg-white/20" : "bg-(--m-texte) text-white shadow-relief") : "bg-card text-gris ring-2 ring-bord")}>
                  {p.fait ? <Check size={horizontal ? 12 : 16} strokeWidth={3} /> : <p.Icone size={horizontal ? 12 : 15} />}
                </span>
                <span className={cn("leading-tight", actif ? "font-bold" : p.fait ? "text-gris" : "text-encre")}>
                  {p.nom}
                  {actif && !horizontal && <small className="block text-petit font-semibold text-(--m-texte)">{CHEMIN.aFaire}</small>}
                </span>
              </motion.button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
