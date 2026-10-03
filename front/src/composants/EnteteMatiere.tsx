// En-tête commun des listes par matière (leçons, fiches, supports) : la matière en grand (icône dans une pastille
// de sa couleur + nom), puis le bandeau des matières en pastilles pleines (active = accent de la matière).
import { createElement, type ReactNode } from "react"
import { motion } from "framer-motion"
import { Pastille } from "@/components/ui/pastille"
import { choixVariants, titreVariants } from "@/components/ui/variantes"
import { iconeMatiere } from "@/config/matieres"
import { useMotion } from "@/lib/motion"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"

const court = (nom: string) => nom.replace(/ \(.*\)$/, "")

export function EnteteMatiere({ rubrique, matiere, nom, sousTitre, children }: {
  /** « Mes leçons », « Mes fiches »… : au-dessus du nom de la matière. */
  rubrique: string; matiere: string | null; nom: string; sousTitre?: ReactNode; children?: ReactNode
}) {
  return (
    <header className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-3" style={matiere ? styleMatiere(matiere) : undefined}>
      {matiere && <Pastille ton="matiere-accent" taille="entete" aria-hidden>{createElement(iconeMatiere(matiere), { size: 28 })}</Pastille>}
      <div className="min-w-0 flex-1">
        <p className={titreVariants({ niveau: "surtitre" })}>{rubrique}</p>
        <h1 className={titreVariants({ niveau: "matiere" })}>{court(nom)}</h1>
      </div>
      {sousTitre && <p className="m-0 w-full text-courant text-(--m-texte,var(--j-gris))">{sousTitre}</p>}
      {children}
    </header>
  )
}

export function BandeauMatieres({ matieres, courante, onChoix }: {
  matieres: { id: string; nom: string }[]; courante: string | null; onChoix: (id: string) => void
}) {
  const { tap } = useMotion()
  return (
    <div role="tablist" aria-label="Matières" className="bandeau-fondu -mx-5 mb-6 flex gap-2 overflow-x-auto px-5 pt-1 pb-3 [scrollbar-width:none] md:mx-[-0.25rem] md:flex-wrap md:overflow-visible md:px-1">
      {matieres.map((m) => {
        const on = m.id === courante
        return (
          <motion.button key={m.id} role="tab" aria-selected={on} onClick={() => onChoix(m.id)} style={styleMatiere(m.id)} {...tap} className={choixVariants({ actif: on })}
            ref={on ? (e) => { e?.scrollIntoView({ inline: "center", block: "nearest" }) } : undefined}>
            {createElement(iconeMatiere(m.id), { size: 18 })}{court(m.nom)}
          </motion.button>
        )
      })}
    </div>
  )
}
