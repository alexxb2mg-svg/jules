// « Mes leçons » : leçons à blocs par matière. Données : GET /api/eleve/cours/parcours (état réel de chaque
// notion, calculé par le serveur). Une notion sans leçon renvoie vers sa fiche visuelle quand elle existe.
import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { BookOpen, ChevronRight, Info } from "lucide-react"
import { useMotion } from "@/lib/motion"
import { Progress } from "@/components/ui/progress"
import { choixVariants, etatVariants, surfaceVariants, titreVariants } from "@/components/ui/variantes"
import { cours, fiches, type Parcours, type NotionParcours } from "@/api/jules"
import { ORDRE_MATIERES } from "@/config/matieres"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import { BandeauMatieres, EnteteMatiere } from "@/composants/EnteteMatiere"

/** État estimé d'une notion (statuts du suivi, jules/modules/cours.py) : texte, point de couleur, avancée de la barre.
 *  Inconnu ou pas encore travaillé → « À faire ». */
const ETATS: Record<string, { texte: string; point: "a_faire" | "en_cours" | "bloque" | "compris" | "acquis"; pct: number }> = {
  a_venir: { texte: "À faire", point: "a_faire", pct: 0 },
  en_cours: { texte: "En cours", point: "en_cours", pct: 40 },
  bloque: { texte: "À revoir", point: "bloque", pct: 40 },
  compris: { texte: "Compris", point: "compris", pct: 75 },
  acquis: { texte: "Acquis", point: "acquis", pct: 100 },
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
  const { apparition, entree, tap } = useMotion()

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
      <EnteteMatiere rubrique="Mes leçons" matiere={courante} nom={matieres.find((m) => m.id === courante)?.nom ?? "Mes leçons"}
        sousTitre={!parcours ? "Chargement…" : nbLecons ? `${nbLecons} leçon${nbLecons > 1 ? "s" : ""} bloc par bloc : Jules corrige tes réponses et te donne des indices.` : "Pas encore de leçon dans cette matière."} />

      <BandeauMatieres matieres={matieres} courante={courante} onChoix={onMatiere} />

      <AnimatePresence mode="wait">
        {parcours && (
          <motion.div key={courante} {...apparition} exit={{ opacity: 0 }} style={courante ? styleMatiere(courante) : undefined}>
            {/* 1. Les leçons disponibles : des cartes qui disent où l'élève en est */}
            {nbLecons > 0 && (
              <div className="mb-3 grid grid-cols-[repeat(auto-fill,minmax(290px,1fr))] gap-3">
                {avecLecon.map((n) => {
                  const etat = ETATS[n.etat] ?? ETATS.a_venir
                  return (
                    <motion.button key={n.id} onClick={() => onLecon(n.id)} {...entree} {...tap}
                      className={surfaceVariants({ ton: "degrade", className: "group flex flex-col gap-2 text-left" })}>
                      <span className="flex items-start justify-between gap-3">
                        <span className={titreVariants({ niveau: "surtitre" })}>{n.chapitre}</span>
                        <ChevronRight size={20} className="shrink-0 text-(--m-texte) transition-transform group-hover:translate-x-1" />
                      </span>
                      <b className={titreVariants({ niveau: "bloc", className: "block" })}>{n.titre}</b>
                      <span className="mt-1 flex items-center gap-2 text-petit font-semibold text-(--m-texte)">
                        {n.duree_minutes
                          ? <><span>{`${n.duree_minutes} min`}</span><span aria-hidden>·</span><span className={etatVariants({ etat: etat.point })} />{etat.texte.toLowerCase()}</>
                          : <><span className={etatVariants({ etat: etat.point })} />{etat.texte}<span aria-hidden>·</span>Leçon guidée par Jules</>}
                      </span>
                      <Progress value={etat.pct} ton="matiere" aria-label={`Avancée : ${etat.texte}`} className="mt-1 h-1.5 bg-(--m-fond)" />
                    </motion.button>
                  )
                })}
              </div>
            )}
            {parcours.estimation && <p className="mt-0 mb-10 flex items-start gap-2 text-petit text-(--m-texte)"><Info size={16} className="mt-0.5 shrink-0" /> {parcours.estimation}</p>}

            {/* 2. Le reste du programme : compact, renvoie vers la fiche visuelle */}
            {sansLecon.length > 0 && (
              <section>
                <h2 className={titreVariants({ niveau: "bloc", className: "mb-1" })}>Le reste du programme</h2>
                <p className="mt-0 mb-5 text-courant text-(--m-texte)">Pas encore de leçon pour ces notions : leur fiche visuelle est là en attendant.</p>
                <div className="flex flex-col gap-5">
                  {chapitresSans.map((c) => (
                    <div key={c.titre}>
                      <p className="mt-0 mb-2 text-petit font-semibold text-(--m-texte)">{c.titre}</p>
                      <div className="flex flex-wrap gap-2">
                        {c.notions.map((n) => avecFiche.has(n.id) ? (
                          <motion.button key={n.id} onClick={() => onFiche(n.id)} {...tap} className={choixVariants({ forme: "suggestion", className: "text-petit" })}>
                            <BookOpen size={15} />{n.titre}
                          </motion.button>
                        ) : (
                          <span key={n.id} className="inline-flex min-h-10 items-center rounded-full bg-surface-2 px-3.5 py-1.5 text-petit text-encre">{n.titre}</span>
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
