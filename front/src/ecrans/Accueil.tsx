// Accueil : une question, deux intentions, puis les suggestions de Jules. Textes et cartes dans config/accueil.ts.
import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import { ACCUEIL } from "@/config/accueil"
import type { Intention } from "@/config/parcours"
import { ELEVE, SUGGESTIONS, trouver } from "@/donnees"
import { Parcours, type Lancement } from "@/composants/Parcours"
import { glisse, CarteIntention, CarteBouton, TitreSection } from "@/ui/briques"

function salutation() {
  const h = new Date().getHours()
  const s = h < 12 ? ACCUEIL.salutations.matin : h < 18 ? ACCUEIL.salutations.aprem : ACCUEIL.salutations.soir
  return ACCUEIL.bienvenue.replace("{salut}", s).replace("{prenom}", ELEVE.prenom)
}

export function Accueil({ onLancer }: { onLancer: (l: Lancement) => void }) {
  const [intention, setIntention] = useState<Intention | null>(null)

  return (
    <div className="mx-auto max-w-[1040px] px-10 py-10">
      <AnimatePresence mode="wait">
        {intention ? (
          <motion.div key={intention} {...glisse}>
            <Parcours intention={intention} onRetourAccueil={() => setIntention(null)} onLancer={onLancer} />
          </motion.div>
        ) : (
          <motion.section key="question" {...glisse}>
            <p className="text-lg text-gris">{salutation()}</p>
            <h1 className="mt-1 text-[38px] font-bold leading-tight">{ACCUEIL.question}</h1>

            <div className={cn("mt-8 grid gap-5", ACCUEIL.intentions.length === 2 ? "grid-cols-2" : "grid-cols-3")}>
              {ACCUEIL.intentions.map((c) => (
                <CarteIntention key={c.intention} {...c} onClick={() => setIntention(c.intention)} />
              ))}
            </div>

            {SUGGESTIONS.length > 0 && (
              <>
                <TitreSection>{ACCUEIL.titreSuggestions}</TitreSection>
                <div className="grid grid-cols-2 gap-4">
                  {SUGGESTIONS.map((s, i) => {
                    const t = ACCUEIL.typesSuggestion[s.type]
                    const { matiere, chapitre } = trouver(s.matiereId, s.chapitreId)
                    return (
                      <CarteBouton key={i} onClick={() => onLancer({ intention: "reviser", matiere, chapitre })} className="flex items-start gap-4 p-4">
                        <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", t.teinte === "bleu" ? "bg-bleu-clair text-bleu" : "bg-[#FDEEDC] text-orange")}>
                          <t.Icone size={20} />
                        </span>
                        <span className="flex-1">
                          <span className={cn("text-[13px] font-semibold uppercase tracking-wide", t.teinte === "bleu" ? "text-bleu" : "text-orange")}>{t.badge}</span>
                          <b className="block leading-snug">{chapitre.titre}</b>
                          <span className="text-[14px] text-gris">{matiere.nom} · {s.detail}</span>
                        </span>
                        <Sparkles size={18} className="mt-1 text-gris/60" />
                      </CarteBouton>
                    )
                  })}
                </div>
              </>
            )}
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  )
}
