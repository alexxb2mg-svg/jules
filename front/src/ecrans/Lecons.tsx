// « Mes leçons » : leçons à blocs par matière. Données : GET /api/eleve/cours/parcours (état réel de chaque
// notion, calculé par le serveur). Une notion sans leçon renvoie vers sa fiche visuelle quand elle existe.
import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, BookOpen, CheckCircle2, CircleDashed, Info, PlayCircle, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"
import { cours, fiches, type Parcours, type NotionParcours } from "@/api/jules"
import { iconeMatiere, ORDRE_MATIERES } from "@/config/matieres"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"

/** Étiquette de l'état d'une notion (valeurs de jules/modules/cours.py). Inconnu → pas d'étiquette. */
const ETATS: Record<string, { texte: string; Icone: typeof CheckCircle2; classe: string }> = {
  acquis: { texte: "Acquis", Icone: CheckCircle2, classe: "bg-[#E7F5EC] text-[#1E7B34]" },
  termine: { texte: "Terminée", Icone: CheckCircle2, classe: "bg-[#E7F5EC] text-[#1E7B34]" },
  en_cours: { texte: "En cours", Icone: PlayCircle, classe: "bg-bleu-clair text-bleu" },
  a_revoir: { texte: "À revoir", Icone: RotateCcw, classe: "bg-[#FFF1E0] text-[#A65A00]" },
  a_faire: { texte: "À faire", Icone: CircleDashed, classe: "bg-nav text-gris" },
}

export function Lecons({ matiere, onMatiere, onLecon, onFiche }: {
  matiere: string | null
  onMatiere: (id: string) => void
  onLecon: (notion: string) => void
  onFiche: (notion: string) => void
}) {
  const [parcours, setParcours] = useState<Parcours | null>(null)
  const [avecFiche, setAvecFiche] = useState<Set<string>>(new Set())
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    let annule = false
    cours.parcours(matiere || undefined).then((p) => !annule && setParcours(p)).catch((e) => !annule && setErreur(e.message))
    return () => { annule = true }
  }, [matiere])
  useEffect(() => {
    fiches.index().then((i) => setAvecFiche(new Set(i.matieres.flatMap((m) => m.notions.map((n) => n.id))))).catch(() => {})
  }, [])

  const matieres = useMemo(() => {
    const rang = (id: string) => { const i = ORDRE_MATIERES.indexOf(id); return i < 0 ? 99 : i }
    return [...(parcours?.matieres || [])].sort((a, b) => rang(a.id) - rang(b.id))
  }, [parcours])
  const courante = parcours?.matiere || matiere
  const avecLecon = (parcours?.notions || []).filter((n) => n.lecon)
  const sansLecon = (parcours?.notions || []).filter((n) => !n.lecon)
  const chapitresSans = useMemo(() => {
    const ordre: string[] = [], par = new Map<string, NotionParcours[]>()
    for (const n of (parcours?.notions || []).filter((x) => !x.lecon)) {
      if (!par.has(n.chapitre)) { par.set(n.chapitre, []); ordre.push(n.chapitre) }
      par.get(n.chapitre)!.push(n)
    }
    return ordre.map((c) => ({ titre: c, notions: par.get(c)! }))
  }, [parcours])
  const nbLecons = avecLecon.length

  if (erreur) return <div className="grid h-full place-items-center p-8 text-gris">Les leçons ne répondent pas ({erreur}).</div>

  return (
    <div className="mx-auto max-w-[1180px] px-5 pt-16 pb-16 md:px-10 md:pt-8">
      <h1 className="m-0 text-[2.2rem] leading-tight font-bold text-encre">Mes leçons</h1>
      <p className="mt-1 mb-6 text-gris">Des leçons courtes, bloc par bloc : Jules corrige tes réponses et te donne des indices.</p>

      {/* Onglets matières */}
      <div role="tablist" aria-label="Matières" className="bandeau-fondu -mx-5 mb-7 flex gap-2 overflow-x-auto px-5 pt-1 pb-3 [scrollbar-width:none] md:mx-[-0.25rem] md:flex-wrap md:overflow-visible md:px-1">
        {matieres.map((m) => {
          const Icone = iconeMatiere(m.id), on = m.id === courante
          return (
            <button key={m.id} role="tab" aria-selected={on} onClick={() => onMatiere(m.id)} style={styleMatiere(m.id)}
              className={cn("relative flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-[0.95rem] font-semibold transition-colors",
                on ? "text-white" : "bg-white text-encre shadow-relief hover:bg-(--m-fond)")}>
              {on && <motion.span layoutId="onglet-matiere" className="absolute inset-0 rounded-full bg-(--m-texte) shadow-relief" transition={{ type: "spring", stiffness: 380, damping: 32 }} />}
              <Icone size={17} className="relative" /><span className="relative">{m.nom.replace(/ \(.*\)$/, "")}</span>
            </button>
          )
        })}
      </div>

      <AnimatePresence mode="wait">
        {parcours && (
          <motion.div key={courante} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} style={courante ? styleMatiere(courante) : undefined}>
            {/* 1. Les leçons disponibles, en grand */}
            <h2 className="mt-0 mb-3 flex items-center gap-2 text-[1.2rem] font-bold text-encre">
              <PlayCircle size={20} className="text-(--m-texte)" /> {nbLecons ? `${nbLecons} leçon${nbLecons > 1 ? "s" : ""} avec Jules` : "Pas encore de leçon dans cette matière"}
            </h2>
            {nbLecons > 0 && (
              <div className="mb-3 grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
                {avecLecon.map((n, i) => {
                  const etat = ETATS[n.etat]
                  return (
                    <motion.button key={n.id} onClick={() => onLecon(n.id)}
                      initial={{ opacity: 0, y: 14, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: 0.04 * i, type: "spring", stiffness: 300, damping: 26 }}
                      whileHover={{ y: -4 }} whileTap={{ scale: 0.98 }}
                      className="group relative flex min-h-[150px] flex-col justify-between overflow-hidden rounded-3xl border border-bord bg-white p-5 text-left shadow-relief transition-shadow hover:shadow-relief-haut">
                      <span aria-hidden className="absolute -top-10 -right-10 size-32 rounded-full bg-(--m-fond) transition-transform duration-500 group-hover:scale-125" />
                      <span className="relative flex items-start justify-between gap-3">
                        <span className="text-[0.85rem] font-semibold text-(--m-texte)">{n.chapitre}</span>
                        {etat && (
                          <span className={cn("flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-[0.8rem] font-semibold", etat.classe)}>
                            <etat.Icone size={14} />{etat.texte}
                          </span>
                        )}
                      </span>
                      <span className="relative mt-3 flex items-end justify-between gap-3">
                        <b className="text-[1.1rem] leading-snug text-encre">{n.titre}</b>
                        <span className="grid size-10 shrink-0 place-items-center rounded-full bg-(--m-texte) text-white shadow-relief transition-transform group-hover:translate-x-1">
                          <ArrowRight size={18} />
                        </span>
                      </span>
                    </motion.button>
                  )
                })}
              </div>
            )}
            {parcours.estimation && <p className="mt-0 mb-8 flex items-center gap-2 text-[0.85rem] text-gris"><Info size={14} /> {parcours.estimation}</p>}

            {/* 2. Le reste du programme : compact, renvoie vers la fiche visuelle */}
            {sansLecon.length > 0 && (
              <section>
                <h2 className="mt-0 mb-1 text-[1.05rem] font-bold text-encre">Le reste du programme</h2>
                <p className="mt-0 mb-4 text-[0.95rem] text-gris">Pas encore de leçon pour ces notions : leur fiche visuelle est là en attendant.</p>
                <div className="flex flex-col gap-5">
                  {chapitresSans.map((c) => (
                    <div key={c.titre}>
                      <p className="mt-0 mb-2 text-[0.9rem] font-semibold text-(--m-texte)">{c.titre}</p>
                      <div className="flex flex-wrap gap-2">
                        {c.notions.map((n) => avecFiche.has(n.id) ? (
                          <button key={n.id} onClick={() => onFiche(n.id)}
                            className="group inline-flex items-center gap-1.5 rounded-full border border-bord bg-white px-3.5 py-1.5 text-[0.92rem] text-encre transition-colors hover:border-(--m-accent) hover:bg-(--m-fond)">
                            <BookOpen size={14} className="text-(--m-texte)" />{n.titre}
                          </button>
                        ) : (
                          <span key={n.id} className="inline-flex items-center rounded-full border border-dashed border-bord px-3.5 py-1.5 text-[0.92rem] text-gris">{n.titre}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
