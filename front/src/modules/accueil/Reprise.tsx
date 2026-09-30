// En tête de « Mes fiches » : reprise en un clic (idée C) et légende d'origine (idée G).
// Reprise = la dernière fiche ouverte (noterOuverture) + les cartes mémoire dues aujourd'hui (studio).
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { ArrowRight, Layers, Play, Sparkles } from "lucide-react"
import { studio } from "@/api/jules"
import { iconeMatiere } from "@/config/matieres"
import { LEGENDE, REPRISE } from "@/config/veille"
import { stylePerso } from "@/config/sources"
import { useRecentes } from "@/modules/sources/etat"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"

export function Reprise({ onFiche, onPerso, onReviser }: {
  onFiche: (notion: string) => void; onPerso: (id: string) => void; onReviser: () => void
}) {
  const [derniere] = useRecentes()
  const [dues, setDues] = useState(0)
  useEffect(() => { studio.revisions().then((r) => setDues(r.cartes.length)).catch(() => {}) }, [])
  if (!derniere && dues === 0) return null
  const perso = derniere?.genre === "perso"
  const Icone = perso ? Sparkles : iconeMatiere(derniere?.matiere ?? "")
  return (
    <div className="mb-7 flex flex-col gap-3 sm:flex-row">
      {derniere && (
        <motion.button initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} whileHover={{ y: -3 }} whileTap={{ scale: 0.98 }}
          onClick={() => (perso ? onPerso(derniere.id) : onFiche(derniere.id))}
          style={perso ? stylePerso : styleMatiere(derniere.matiere)}
          className="group flex min-w-0 flex-1 items-center gap-4 rounded-3xl bg-(--m-texte) px-5 py-4 text-left text-white shadow-relief-haut">
          <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-white/15"><Play size={22} className="fill-white" /></span>
          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-1.5 text-[0.85rem] font-semibold opacity-85">
              <Icone size={14} /> {REPRISE.continuer} {perso ? REPRISE.perso : REPRISE.fiche}
            </span>
            <b className="block truncate text-[1.15rem] leading-snug">{derniere.titre}</b>
          </span>
          <ArrowRight size={22} className="shrink-0 transition-transform group-hover:translate-x-1" />
        </motion.button>
      )}
      {dues > 0 && (
        <motion.button initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
          whileHover={{ y: -3 }} whileTap={{ scale: 0.98 }} onClick={onReviser}
          className="group flex items-center gap-3 rounded-3xl border-2 border-bleu/20 bg-card px-5 py-4 text-left shadow-relief sm:w-[300px]">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-bleu-clair text-bleu"><Layers size={20} /></span>
          <span className="min-w-0 flex-1">
            <b className="block leading-snug text-encre">{REPRISE.cartes(dues)}</b>
            <span className="text-[0.88rem] font-semibold text-bleu">{REPRISE.reviser} →</span>
          </span>
        </motion.button>
      )}
    </div>
  )
}

/** G : ce que veulent dire les deux étiquettes (Jules / Perso). */
export function LegendeOrigine() {
  return (
    <p className="mt-2 mb-0 flex flex-wrap items-center gap-x-4 gap-y-1 text-[0.85rem] text-gris">
      <span className="inline-flex items-center gap-1.5">
        <span className="rounded-full bg-bleu-clair px-2 py-px text-[0.72rem] font-bold tracking-wide text-bleu uppercase">{LEGENDE.jules.nom}</span>
        {LEGENDE.jules.texte}
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="rounded-full bg-perso px-2 py-px text-[0.72rem] font-bold tracking-wide text-white uppercase">{LEGENDE.perso.nom}</span>
        {LEGENDE.perso.texte}
      </span>
    </p>
  )
}
