// « Mes leçons » : leçons à blocs par matière. Données : GET /api/eleve/cours/parcours (état réel de chaque
// notion, calculé par le serveur). Une notion sans leçon renvoie vers sa fiche visuelle quand elle existe.
import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, BookOpen, CheckCircle2, CircleDashed, Info, PlayCircle, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"
import { useMotion } from "@/lib/motion"
import { Badge } from "@/components/ui/badge"
import { surfaceVariants, titreVariants } from "@/components/ui/variantes"
import { cours, fiches, type Parcours, type NotionParcours } from "@/api/jules"
import { iconeMatiere, ORDRE_MATIERES } from "@/config/matieres"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"

/** Étiquette de l'état d'une notion (valeurs de jules/modules/cours.py). Inconnu → pas d'étiquette. */
const ETATS: Record<string, { texte: string; Icone: typeof CheckCircle2; ton: "succes" | "info" | "alerte" | "neutre" }> = {
  acquis: { texte: "Acquis", Icone: CheckCircle2, ton: "succes" },
  termine: { texte: "Terminée", Icone: CheckCircle2, ton: "succes" },
  en_cours: { texte: "En cours", Icone: PlayCircle, ton: "info" },
  a_revoir: { texte: "À revoir", Icone: RotateCcw, ton: "alerte" },
  a_faire: { texte: "À faire", Icone: CircleDashed, ton: "neutre" },
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
  const { entree, tap } = useMotion()

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
      <h1 className={titreVariants({ niveau: "ecran" })}>Mes leçons</h1>
      <p className="mt-2 mb-6 text-courant text-gris">Des leçons courtes, bloc par bloc : Jules corrige tes réponses et te donne des indices.</p>

      {/* Onglets matières */}
      <div role="tablist" aria-label="Matières" className="bandeau-fondu -mx-5 mb-7 flex gap-2 overflow-x-auto px-5 pt-1 pb-3 [scrollbar-width:none] md:mx-[-0.25rem] md:flex-wrap md:overflow-visible md:px-1">
        {matieres.map((m) => {
          const Icone = iconeMatiere(m.id), on = m.id === courante
          return (
            <button key={m.id} role="tab" aria-selected={on} onClick={() => onMatiere(m.id)} style={styleMatiere(m.id)}
              className={cn("relative flex min-h-11 shrink-0 items-center gap-2 rounded-full px-4 py-2 text-courant font-semibold transition-colors",
                on ? "text-white" : "bg-card text-encre hover:bg-(--m-fond)")}>
              {on && <motion.span layoutId="onglet-matiere" className="absolute inset-0 rounded-full bg-(--m-texte)" transition={{ type: "spring", stiffness: 380, damping: 32 }} />}
              <Icone size={17} className="relative" /><span className="relative">{m.nom.replace(/ \(.*\)$/, "")}</span>
            </button>
          )
        })}
      </div>

      <AnimatePresence mode="wait">
        {parcours && (
          <motion.div key={courante} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} style={courante ? styleMatiere(courante) : undefined}>
            {/* 1. Les leçons disponibles, en grand */}
            <h2 className={titreVariants({ niveau: "bloc", className: "mb-3 flex items-center gap-2" })}>
              <PlayCircle size={20} className="text-(--m-texte)" /> {nbLecons ? `${nbLecons} leçon${nbLecons > 1 ? "s" : ""} avec Jules` : "Pas encore de leçon dans cette matière"}
            </h2>
            {nbLecons > 0 && (
              <div className="mb-3 grid grid-cols-[repeat(auto-fill,minmax(290px,1fr))] gap-3">
                {avecLecon.map((n, i) => {
                  const etat = ETATS[n.etat]
                  return (
                    <motion.button key={n.id} onClick={() => onLecon(n.id)} {...entree} {...tap} transition={{ delay: 0.04 * i }}
                      className={surfaceVariants({ ton: "plat", lisere: true, className: "group relative flex min-h-[150px] flex-col justify-between overflow-hidden text-left" })}>
                      <span aria-hidden className="absolute -top-10 -right-10 size-32 rounded-full bg-(--m-fond) transition-transform duration-500 group-hover:scale-125" />
                      <span className="relative flex items-start justify-between gap-3">
                        <span className="text-petit font-semibold text-(--m-texte)">{n.chapitre}</span>
                        {etat && <Badge variant={etat.ton}><etat.Icone />{etat.texte}</Badge>}
                      </span>
                      <span className="relative mt-3 flex items-end justify-between gap-3">
                        <b className={titreVariants({ niveau: "bloc" })}>{n.titre}</b>
                        <span className="grid size-11 shrink-0 place-items-center rounded-full bg-(--m-texte) text-white transition-transform group-hover:translate-x-1">
                          <ArrowRight size={18} />
                        </span>
                      </span>
                    </motion.button>
                  )
                })}
              </div>
            )}
            {parcours.estimation && <p className="mt-0 mb-10 flex items-start gap-2 text-petit text-gris"><Info size={16} className="mt-0.5 shrink-0" /> {parcours.estimation}</p>}

            {/* 2. Le reste du programme : compact, renvoie vers la fiche visuelle */}
            {sansLecon.length > 0 && (
              <section>
                <h2 className={titreVariants({ niveau: "bloc", className: "mb-1" })}>Le reste du programme</h2>
                <p className="mt-0 mb-5 text-courant text-gris">Pas encore de leçon pour ces notions : leur fiche visuelle est là en attendant.</p>
                <div className="flex flex-col gap-5">
                  {chapitresSans.map((c) => (
                    <div key={c.titre}>
                      <p className="mt-0 mb-2 text-petit font-semibold text-(--m-texte)">{c.titre}</p>
                      <div className="flex flex-wrap gap-2">
                        {c.notions.map((n) => avecFiche.has(n.id) ? (
                          <button key={n.id} onClick={() => onFiche(n.id)}
                            className="group inline-flex min-h-10 items-center gap-1.5 rounded-full bg-card px-3.5 py-1.5 text-petit text-encre transition-colors hover:bg-(--m-fond)">
                            <BookOpen size={14} className="text-(--m-texte)" />{n.titre}
                          </button>
                        ) : (
                          <span key={n.id} className="inline-flex min-h-10 items-center rounded-full border border-dashed border-bord px-3.5 py-1.5 text-petit text-gris">{n.titre}</span>
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
