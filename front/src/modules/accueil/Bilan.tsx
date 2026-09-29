// L : « Mon bilan », en verbes et points forts d'abord (idée d'Adaptiv'Collège). Données : GET /api/eleve/cours/bilan
// — état estimé du suivi (même source que le parcours) et attendus officiels du référentiel. Rien n'est généré.
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { ArrowRight, ChevronLeft, CircleDashed, Compass, Hourglass, Sparkles, Trophy, Wrench } from "lucide-react"
import { cn } from "@/lib/utils"
import { cours, type BilanNotions as DonneesBilan } from "@/api/jules"
import { iconeMatiere } from "@/config/matieres"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import { useMatiere } from "./etat"

export const TEXTES_BILAN = {
  titre: "Mon bilan",
  intro: "Ce que tu sais faire, d'abord. Puis ce qui est en route.",
  retour: "Exercices et supports",
  vide: "Rien encore : travaille une fiche ou une leçon avec Jules, ton bilan se remplira tout seul.",
  explorer: (n: number) => `${n} notion${n > 1 ? "s" : ""} encore à explorer`,
  ouvrir: "Revoir la fiche",
  toutes: "Toutes les matières",
}
const ASPECT: Record<string, { Icone: typeof Trophy; classe: string }> = {
  acquis: { Icone: Trophy, classe: "bg-[#E7F5EC] text-[#1E7B34]" },
  compris: { Icone: Sparkles, classe: "bg-[#EEFAF2] text-[#135C33]" },
  en_cours: { Icone: Hourglass, classe: "bg-bleu-clair text-bleu" },
  bloque: { Icone: Wrench, classe: "bg-[#FFF8EC] text-[#7A4B00]" },
}

export function Bilan({ onRetour, onFiche }: { onRetour: () => void; onFiche: (notion: string) => void }) {
  const matiere = useMatiere()
  const [bilan, setBilan] = useState<DonneesBilan | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  useEffect(() => { setBilan(null); cours.bilan(matiere ?? undefined).then(setBilan).catch((e) => setErreur(e.message)) }, [matiere])
  const vide = bilan && bilan.groupes.every((g) => g.notions.length === 0)

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[980px] px-5 pt-16 pb-16 md:px-10 md:pt-8">
        <button onClick={onRetour} className="mb-3 inline-flex items-center gap-1 rounded-full px-2 py-2 text-[0.9rem] font-semibold text-bleu hover:bg-nav">
          <ChevronLeft size={16} /> {TEXTES_BILAN.retour}
        </button>
        <h1 className="m-0 text-[2.2rem] leading-tight font-bold text-encre">{TEXTES_BILAN.titre}</h1>
        <p className="mt-1 mb-7 text-gris">{TEXTES_BILAN.intro}</p>
        {erreur && <p className="text-rouge">{erreur}</p>}
        {!bilan && !erreur && <div className="h-40 animate-pulse rounded-3xl bg-nav" />}
        {vide && <p className="rounded-2xl bg-nav px-5 py-4 text-gris">{TEXTES_BILAN.vide}</p>}
        <div className="flex flex-col gap-8">
          {bilan?.groupes.filter((g) => g.notions.length > 0).map((g, gi) => {
            const { Icone, classe } = ASPECT[g.etat] ?? ASPECT.en_cours!
            return (
              <motion.section key={g.etat} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: gi * 0.06 }}>
                <h2 className="mt-0 mb-3 flex items-center gap-2.5 text-[1.2rem] font-bold text-encre">
                  <span className={cn("grid size-9 place-items-center rounded-xl", classe)}><Icone size={18} /></span>
                  {g.titre}
                  <span className="text-[0.95rem] font-semibold text-gris">{g.notions.length}</span>
                </h2>
                <div className="grid gap-3 md:grid-cols-2">
                  {g.notions.map((n) => {
                    const IconeM = iconeMatiere(n.matiere)
                    return (
                      <article key={n.notion} style={styleMatiere(n.matiere)} className="flex flex-col gap-2 rounded-3xl border border-bord bg-white p-4 shadow-relief">
                        <p className="m-0 flex items-center gap-1.5 text-[0.82rem] font-semibold text-(--m-texte)"><IconeM size={14} /> {n.nom_matiere}</p>
                        <h3 className="m-0 text-[1.05rem] leading-snug font-bold text-encre">{n.titre}</h3>
                        {n.savoir_faire.length > 0 && (
                          <ul className="m-0 flex list-none flex-col gap-1 p-0 text-[0.92rem] leading-snug text-encre">
                            {n.savoir_faire.map((s, i) => (
                              <li key={i} className="flex gap-2"><CircleDashed size={14} className="mt-1 shrink-0 text-(--m-accent)" /><span>{s}</span></li>
                            ))}
                          </ul>
                        )}
                        <button onClick={() => onFiche(n.notion)} className="mt-auto inline-flex w-fit items-center gap-1 pt-1 text-[0.9rem] font-semibold text-(--m-texte) hover:underline">
                          {TEXTES_BILAN.ouvrir} <ArrowRight size={15} />
                        </button>
                      </article>
                    )
                  })}
                </div>
              </motion.section>
            )
          })}
        </div>
        {bilan && (
          <p className="mt-8 mb-0 flex items-center gap-2 text-[0.9rem] text-gris">
            <Compass size={16} /> {TEXTES_BILAN.explorer(bilan.a_explorer)} · {bilan.estimation}
          </p>
        )}
      </div>
    </div>
  )
}
