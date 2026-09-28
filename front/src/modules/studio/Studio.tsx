// « Exercices et supports » : par matière, les notions qui ont une leçon, leurs supports, et « + nouveau »
// (choix du type). Données : GET /api/eleve/studio/notions (docs/STUDIO-CONTRAT.md §3 et §6).
import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, BookOpen, Info, Layers, Plus, Trophy, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { studio, type CatalogueStudio, type NotionStudio, type TypeSupport } from "@/api/jules"
import { iconeMatiere, ORDRE_MATIERES } from "@/config/matieres"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import { ORDRE_TYPES, STATUTS, TYPES } from "./config"

export function Studio({ matiere, onMatiere, onOuvrir, onReviser, onBilan, onFiche }: {
  matiere: string | null
  onMatiere: (id: string) => void
  onOuvrir: (support: string, matiere: string) => void
  onBilan: () => void
  onReviser: () => void
  onFiche?: (notion: string) => void
}) {
  const [cat, setCat] = useState<CatalogueStudio | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [aReviser, setAReviser] = useState(0)
  const [choix, setChoix] = useState<NotionStudio | null>(null)
  const [creation, setCreation] = useState(false)

  useEffect(() => {
    let annule = false
    studio.notions(matiere || undefined).then((c) => !annule && setCat(c)).catch((e) => !annule && setErreur(e.message))
    return () => { annule = true }
  }, [matiere])
  useEffect(() => { studio.revisions().then((r) => setAReviser(r.nombre_du_jour)).catch(() => {}) }, [])

  const matieres = useMemo(() => {
    const rang = (id: string) => { const i = ORDRE_MATIERES.indexOf(id); return i < 0 ? 99 : i }
    return [...(cat?.matieres || [])].sort((a, b) => rang(a.id) - rang(b.id))
  }, [cat])
  const courante = cat?.matiere || matiere
  const notions = (cat?.notions || []).filter((n) => n.lecon)
  const sansLecon = (cat?.notions || []).length - notions.length

  const creer = async (type: TypeSupport) => {
    if (!choix || !courante) return
    setCreation(true)
    try { const r = await studio.creer(choix.id, type); onOuvrir(r.support.id, courante) }
    catch (e) { setErreur((e as Error).message) } finally { setCreation(false) }
  }

  if (erreur) return <div className="grid h-full place-items-center p-8 text-gris">Le studio ne répond pas ({erreur}).</div>

  return (
    <div className="mx-auto max-w-[1180px] px-5 pt-16 pb-16 md:px-10 md:pt-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="m-0 text-[2.2rem] leading-tight font-bold text-encre">Exercices et supports</h1>
          <p className="mt-1 mb-0 text-gris">Fabrique tes propres supports : fiche, carte mentale, quiz, cartes mémoire. Jules relit, il n'écrit jamais à ta place.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
        <motion.button whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }} onClick={onBilan}
          className="inline-flex items-center gap-2 rounded-2xl border-2 border-bord bg-white px-4 py-2.5 font-semibold text-encre shadow-relief">
          <Trophy size={18} className="text-[#1E7B34]" /> Mon bilan
        </motion.button>
        {aReviser > 0 && (
          <motion.button initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }} onClick={onReviser}
            className="relative inline-flex items-center gap-2.5 rounded-2xl bg-encre px-5 py-3 font-semibold text-white shadow-relief-haut">
            <Layers size={19} /> Réviser mes cartes
            <span className="grid min-w-7 place-items-center rounded-full bg-white px-1.5 py-0.5 text-[0.85rem] font-bold text-encre">{aReviser}</span>
          </motion.button>
        )}
        </div>
      </div>

      <div role="tablist" aria-label="Matières" className="-mx-1 mt-6 mb-7 flex flex-wrap gap-2 px-1 pt-1 pb-3">
        {matieres.map((m) => {
          const Icone = iconeMatiere(m.id), on = m.id === courante
          return (
            <button key={m.id} role="tab" aria-selected={on} onClick={() => onMatiere(m.id)} style={styleMatiere(m.id)}
              className={cn("relative flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-[0.95rem] font-semibold transition-colors",
                on ? "text-white" : "bg-white text-encre shadow-relief hover:bg-(--m-fond)")}>
              {on && <motion.span layoutId="onglet-studio" className="absolute inset-0 rounded-full bg-(--m-texte) shadow-relief" transition={{ type: "spring", stiffness: 380, damping: 32 }} />}
              <Icone size={17} className="relative" /><span className="relative">{m.nom.replace(/ \(.*\)$/, "")}</span>
            </button>
          )
        })}
      </div>

      <AnimatePresence mode="wait">
        {cat && (
          <motion.div key={courante} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} style={courante ? styleMatiere(courante) : undefined}>
            {notions.length === 0 ? (
              <p className="rounded-2xl bg-nav px-5 py-4 text-gris">Pas encore de leçon dans cette matière : le studio n'y est pas encore utilisable.</p>
            ) : (
              <div className="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4">
                {notions.map((n, i) => (
                  <motion.article key={n.id} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.04 * i }}
                    className="flex flex-col rounded-3xl border border-bord bg-white p-5 shadow-relief">
                    <span className="text-[0.82rem] font-semibold text-(--m-texte)">{n.chapitre}</span>
                    <h2 className="mt-1 mb-3 text-[1.1rem] leading-snug font-bold text-encre">{n.titre}</h2>
                    {onFiche && (
                      <button onClick={() => onFiche(n.id)}
                        className="mb-3 inline-flex w-fit items-center gap-1.5 rounded-full bg-(--m-fond) px-3 py-1.5 text-[0.85rem] font-semibold text-(--m-texte) hover:bg-(--m-accent) hover:text-white transition-colors">
                        <BookOpen size={14} /> Voir la fiche
                      </button>
                    )}
                    <ul className="m-0 mb-3 flex list-none flex-col gap-1.5 p-0">
                      {n.supports.map((s) => {
                        const d = TYPES[s.type], st = STATUTS[s.statut]
                        return (
                          <li key={s.id}>
                            <button onClick={() => courante && onOuvrir(s.id, courante)}
                              className="group flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left transition-colors hover:bg-(--m-fond)">
                              <d.Icone size={17} className="shrink-0 text-(--m-texte)" />
                              <span className="min-w-0 flex-1 truncate text-[0.95rem]">{s.titre || <i className="text-gris">{d.nom} sans titre</i>}</span>
                              {st && <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[0.75rem] font-semibold", st.classe)}>{st.texte}</span>}
                              <ArrowRight size={15} className="shrink-0 text-gris opacity-0 transition-opacity group-hover:opacity-100" />
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                    <button onClick={() => setChoix(n)}
                      className="mt-auto inline-flex w-fit items-center gap-1.5 rounded-full border-2 border-dashed border-(--m-accent)/40 px-3.5 py-1.5 text-[0.9rem] font-semibold text-(--m-texte) hover:border-(--m-accent) hover:bg-(--m-fond)">
                      <Plus size={15} /> Nouveau support
                    </button>
                  </motion.article>
                ))}
              </div>
            )}
            {sansLecon > 0 && notions.length > 0 && (
              <p className="mt-6 flex items-center gap-2 text-[0.88rem] text-gris"><Info size={14} /> Les {sansLecon} autres notions de la matière n'ont pas encore de leçon : le studio y arrivera avec elles.</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Choix du type de support */}
      <AnimatePresence>
        {choix && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setChoix(null)}
            className="fixed inset-0 z-50 grid place-items-center bg-encre/40 p-4 backdrop-blur-sm" style={courante ? styleMatiere(courante) : undefined}>
            <motion.div role="dialog" aria-modal aria-label="Choisir un type de support" onClick={(e) => e.stopPropagation()}
              initial={{ scale: 0.94, y: 16 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.96, opacity: 0 }}
              className="w-full max-w-[640px] rounded-3xl bg-white p-6 shadow-relief-haut">
              <div className="mb-1 flex items-start justify-between gap-3">
                <h2 className="m-0 text-[1.35rem] font-bold text-encre">Quel support pour « {choix.titre} » ?</h2>
                <button onClick={() => setChoix(null)} aria-label="Fermer" className="rounded-full p-1.5 text-gris hover:bg-nav"><X size={18} /></button>
              </div>
              <p className="mt-0 mb-5 text-gris">La trame est vide : c'est toi qui écris.</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {ORDRE_TYPES.map((t, i) => {
                  const d = TYPES[t]
                  return (
                    <motion.button key={t} disabled={creation} onClick={() => creer(t)}
                      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 * i }} whileHover={{ y: -3 }} whileTap={{ scale: 0.97 }}
                      className="flex items-start gap-3 rounded-2xl border-2 border-bord p-4 text-left transition-colors hover:border-(--m-accent) hover:bg-(--m-fond) disabled:opacity-50">
                      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-(--m-fond) text-(--m-texte)"><d.Icone size={22} /></span>
                      <span><b className="block text-[1.02rem]">{d.nom}</b><small className="text-[0.88rem] text-gris">{d.pitch}</small></span>
                    </motion.button>
                  )
                })}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
