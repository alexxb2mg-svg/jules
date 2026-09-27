// Parcours générique : enchaîne les étapes déclarées dans config/parcours.ts.
// Chaque étape est un composant enregistré dans ETAPES ; en ajouter une = une entrée ici + une dans la config.
import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, Check, AlertTriangle } from "lucide-react"
import { PARCOURS, FIL, ETATS, type Intention, type EtapeId } from "@/config/parcours"
import { MATIERES, type Matiere, type Chapitre } from "@/donnees"
import { FilAriane, type Cran } from "@/ui/FilAriane"
import { glisse, cascade, CarteBouton, Ligne, Numero, Pastille, Etiquette, Titre } from "@/ui/briques"

export type Choix = { intention: Intention; matiere?: Matiere; chapitre?: Chapitre }
export type Lancement = Required<Choix>

type PropsEtape = { choix: Choix; question: string; onChoix: (c: Partial<Choix>) => void }

/* ---- étapes disponibles ---- */

function EtapeMatiere({ question, onChoix }: PropsEtape) {
  return (
    <>
      <Titre>{question}</Titre>
      <div className="mt-7 grid grid-cols-3 gap-4">
        {MATIERES.map((m, i) => {
          const fragiles = m.chapitres.filter((c) => c.etat === "fragile").length
          return (
            <CarteBouton key={m.id} onClick={() => onChoix({ matiere: m })} className="flex items-center gap-4 p-4" {...cascade(i)}>
              <Pastille couleur={m.couleur} />
              <span className="flex-1">
                <b className="block font-titre text-lg">{m.nom}</b>
                <span className="text-[14px] text-gris">{m.chapitres.length} chapitre{m.chapitres.length > 1 ? "s" : ""}{fragiles ? ` · ${fragiles} à revoir` : ""}</span>
              </span>
              <ArrowRight size={18} className="text-gris" />
            </CarteBouton>
          )
        })}
      </div>
    </>
  )
}

function EtapeChapitre({ choix, question, onChoix }: PropsEtape) {
  const m = choix.matiere!
  const ICONES = { acquis: Check, fragile: AlertTriangle } as const
  return (
    <>
      <Titre avant={<Pastille couleur={m.couleur} />}>{question.replace("{matiere}", m.nom)}</Titre>
      <div className="mt-7 grid grid-cols-2 gap-3">
        {m.chapitres.map((c, i) => {
          const e = ETATS[c.etat]
          return (
            <Ligne key={c.id} index={i} axe="x" onClick={() => onChoix({ chapitre: c })}
              gauche={<Numero n={i + 1} />}
              droite={<Etiquette teinte={e.teinte} Icone={ICONES[c.etat as keyof typeof ICONES]}>{e.libelle}</Etiquette>}>
              <span className="font-medium">{c.titre}</span>
            </Ligne>
          )
        })}
      </div>
    </>
  )
}

const ETAPES: Record<EtapeId, (p: PropsEtape) => React.JSX.Element> = { matiere: EtapeMatiere, chapitre: EtapeChapitre }
const CLE: Record<EtapeId, keyof Choix> = { matiere: "matiere", chapitre: "chapitre" }

/* ---- moteur ---- */

export function Parcours({ intention, onRetourAccueil, onLancer }: {
  intention: Intention; onRetourAccueil: () => void; onLancer: (l: Lancement) => void
}) {
  const def = PARCOURS[intention]
  const [choix, setChoix] = useState<Choix>({ intention })

  // première étape dont la valeur manque
  const idx = def.etapes.findIndex((e) => !choix[CLE[e.id]])
  const etape = def.etapes[idx]

  const crans: Cran[] = [
    { libelle: FIL.racine, onClick: onRetourAccueil },
    { libelle: def.libelle, onClick: () => setChoix({ intention }), actif: idx === 0 },
    ...def.etapes.slice(0, idx).map((e, i) => {
      const v = choix[CLE[e.id]] as Matiere | Chapitre
      const libelle = "nom" in v ? v.nom : v.titre
      return { libelle, actif: i === idx - 1, onClick: () => setChoix(Object.fromEntries(Object.entries(choix).slice(0, i + 2)) as Choix) }
    }),
  ]

  const avancer = (c: Partial<Choix>) => {
    const suivant = { ...choix, ...c }
    setChoix(suivant)
    if (def.etapes.every((e) => suivant[CLE[e.id]])) onLancer(suivant as Lancement)
  }

  const Etape = ETAPES[etape.id]
  return (
    <>
      <FilAriane crans={crans} />
      <AnimatePresence mode="wait">
        <motion.section key={etape.id} {...glisse}>
          <Etape choix={choix} question={etape.question} onChoix={avancer} />
        </motion.section>
      </AnimatePresence>
    </>
  )
}
