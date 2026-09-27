// « Mes fiches » : les fiches visuelles de la bibliothèque, par matière puis par chapitre.
// Données : GET /api/eleve/fiches_visuelles/notions (index seul, sans IA). Recherche locale sur les titres.
import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, LayoutGroup, motion } from "framer-motion"
import { ArrowRight, Search, Sparkles, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { fiches } from "@/api/jules"
import type { IndexFiches, MatiereIndex, NotionIndex } from "./types"
import { iconeMatiere, ORDRE_MATIERES } from "@/config/matieres"
import { styleMatiere } from "./FicheVisuelle"

/** Comparaison sans accents ni casse, pour la recherche. */
const plat = (s: string) => s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()

export function Bibliotheque({ matiere, onMatiere, onOuvrir }: {
  matiere: string | null
  onMatiere: (id: string | null) => void
  onOuvrir: (notion: string) => void
}) {
  const [index, setIndex] = useState<IndexFiches | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [recherche, setRecherche] = useState("")
  useEffect(() => { fiches.index().then(setIndex).catch((e) => setErreur(e.message)) }, [])

  const matieres = useMemo(() => {
    const liste = [...(index?.matieres || [])]
    const rang = (id: string) => { const i = ORDRE_MATIERES.indexOf(id); return i < 0 ? 99 : i }
    return liste.sort((a, b) => rang(a.id) - rang(b.id))
  }, [index])
  const total = matieres.reduce((n, m) => n + m.notions.length, 0)
  const choisie = matieres.find((m) => m.id === matiere) || null

  const trouvees = useMemo(() => {
    const q = plat(recherche.trim())
    if (q.length < 2) return null
    const mots = q.split(/\s+/)
    return matieres.flatMap((m) => m.notions.filter((n) => {
      const texte = plat(`${n.titre} ${n.chapitre} ${m.nom}`)
      return mots.every((w) => texte.includes(w))
    }).map((n) => ({ m, n }))).slice(0, 40)
  }, [recherche, matieres])

  if (erreur) return <div className="grid h-full place-items-center p-8 text-gris">La bibliothèque ne répond pas ({erreur}).</div>

  return (
    <div className="mx-auto max-w-[1180px] px-5 pt-16 pb-16 md:px-10 md:pt-8">
      {/* En-tête + recherche */}
      <div className="mb-7 flex flex-wrap items-end justify-between gap-5">
        <div>
          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={choisie?.id || "tout"} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}>
              {choisie ? (
                <>
                  <button onClick={() => onMatiere(null)} className="mb-1 text-[0.95rem] font-semibold text-gris hover:text-bleu">Mes fiches ›</button>
                  <h1 className="m-0 text-[2.2rem] leading-tight font-bold text-encre">{choisie.nom}</h1>
                </>
              ) : (
                <>
                  <h1 className="m-0 text-[2.2rem] leading-tight font-bold text-encre">Mes fiches</h1>
                  <p className="mt-1 mb-0 text-gris">{index ? `${total} fiches visuelles pour toute la 3e, rangées par matière.` : "Chargement de la bibliothèque…"}</p>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
        <label className="relative flex w-full items-center sm:w-[340px]">
          <Search size={18} className="pointer-events-none absolute left-4 text-gris" />
          <input value={recherche} onChange={(e) => setRecherche(e.target.value)} placeholder="Chercher une notion…" aria-label="Chercher une notion"
            className="h-12 w-full rounded-2xl border border-bord bg-white pr-10 pl-11 text-[1rem] shadow-relief outline-none transition-shadow focus:border-bleu focus:ring-4 focus:ring-bleu-clair" />
          {recherche && <button onClick={() => setRecherche("")} aria-label="Effacer" className="absolute right-3 rounded-full p-1 text-gris hover:bg-survol"><X size={16} /></button>}
        </label>
      </div>

      <AnimatePresence mode="wait" initial={false}>
        {trouvees ? (
          <motion.div key="recherche" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <p className="mt-0 mb-3 text-gris">{trouvees.length ? `${trouvees.length} fiche${trouvees.length > 1 ? "s" : ""} trouvée${trouvees.length > 1 ? "s" : ""}` : "Aucune fiche ne correspond."}</p>
            <div className="grid gap-3 md:grid-cols-2">
              {trouvees.map(({ m, n }, i) => <TuileNotion key={n.id} n={n} m={m} i={i} onOuvrir={onOuvrir} avecMatiere />)}
            </div>
          </motion.div>
        ) : choisie ? (
          <motion.div key={`m-${choisie.id}`} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
            transition={{ type: "spring", stiffness: 260, damping: 30 }}>
            <Chapitres m={choisie} onOuvrir={onOuvrir} />
          </motion.div>
        ) : (
          <motion.div key="grille" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, x: -20 }}>
            <LayoutGroup>
              <div className="grid grid-cols-[repeat(auto-fill,minmax(230px,1fr))] gap-4">
                {index
                  ? matieres.map((m, i) => <TuileMatiere key={m.id} m={m} i={i} onClick={() => onMatiere(m.id)} />)
                  : Array.from({ length: 12 }, (_, i) => <div key={i} className="h-[150px] animate-pulse rounded-3xl bg-nav" />)}
              </div>
            </LayoutGroup>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function TuileMatiere({ m, i, onClick }: { m: MatiereIndex; i: number; onClick: () => void }) {
  const Icone = iconeMatiere(m.id)
  const chapitres = new Set(m.notions.map((n) => n.chapitre)).size
  return (
    <motion.button onClick={onClick} style={styleMatiere(m.id)}
      initial={{ opacity: 0, y: 18, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: 0.03 * i, type: "spring", stiffness: 300, damping: 26 }}
      whileHover={{ y: -4 }} whileTap={{ scale: 0.97 }}
      className="group relative flex h-[150px] flex-col justify-between overflow-hidden rounded-3xl border border-bord bg-white p-5 text-left shadow-relief transition-shadow hover:shadow-relief-haut">
      <span aria-hidden className="absolute -right-10 -bottom-12 size-40 rounded-full bg-(--m-fond) transition-transform duration-500 group-hover:scale-125" />
      <span className="relative grid size-12 place-items-center rounded-2xl bg-(--m-fond) text-(--m-texte) ring-1 ring-(--m-accent)/20 transition-transform duration-300 group-hover:-rotate-6">
        <Icone size={24} />
      </span>
      <span className="relative">
        <b className="block text-[1.1rem] leading-tight text-encre">{m.nom.replace(/ \(.*\)$/, "")}</b>
        <span className="mt-1 flex items-center gap-1 text-[0.9rem] text-gris">
          {m.notions.length} fiches · {chapitres} chapitre{chapitres > 1 ? "s" : ""}
          <ArrowRight size={15} className="ml-auto text-(--m-texte) opacity-0 transition-all group-hover:translate-x-1 group-hover:opacity-100" />
        </span>
      </span>
    </motion.button>
  )
}

function Chapitres({ m, onOuvrir }: { m: MatiereIndex; onOuvrir: (notion: string) => void }) {
  const chapitres = useMemo(() => {
    const ordre: string[] = [], par = new Map<string, NotionIndex[]>()
    for (const n of m.notions) {
      if (!par.has(n.chapitre)) { par.set(n.chapitre, []); ordre.push(n.chapitre) }
      par.get(n.chapitre)!.push(n)
    }
    return ordre.map((c) => ({ titre: c, notions: par.get(c)! }))
  }, [m])
  let k = 0
  return (
    <div className="flex flex-col gap-8" style={styleMatiere(m.id)}>
      {chapitres.map((c, ci) => (
        <section key={c.titre}>
          <h2 className="mt-0 mb-3 flex items-baseline gap-3 text-[1.15rem] font-bold text-(--m-texte)">
            <span className="font-titre text-[0.85rem] font-semibold tabular-nums opacity-60">{String(ci + 1).padStart(2, "0")}</span>
            {c.titre}
          </h2>
          <div className="grid gap-3 md:grid-cols-2">
            {c.notions.map((n) => <TuileNotion key={n.id} n={n} m={m} i={k++} onOuvrir={onOuvrir} />)}
          </div>
        </section>
      ))}
    </div>
  )
}

function TuileNotion({ n, m, i, onOuvrir, avecMatiere }: { n: NotionIndex; m: MatiereIndex; i: number; onOuvrir: (id: string) => void; avecMatiere?: boolean }) {
  const Icone = iconeMatiere(m.id)
  return (
    <motion.button onClick={() => onOuvrir(n.id)} style={styleMatiere(m.id)}
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 14) * 0.025 }}
      whileHover={{ x: 4 }} whileTap={{ scale: 0.98 }}
      className="group flex items-center gap-4 rounded-2xl border border-bord bg-white px-4 py-3.5 text-left shadow-relief transition-[border-color,box-shadow] hover:border-(--m-accent) hover:shadow-relief-haut">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-(--m-fond) text-(--m-texte)">
        {avecMatiere ? <Icone size={19} /> : <Sparkles size={18} />}
      </span>
      <span className="min-w-0 flex-1">
        <b className="block leading-snug text-encre">{n.titre}</b>
        {avecMatiere && <span className="block truncate text-[0.85rem] text-gris">{m.nom} · {n.chapitre}</span>}
      </span>
      <ArrowRight size={18} className={cn("shrink-0 text-(--m-texte) transition-transform group-hover:translate-x-1")} />
    </motion.button>
  )
}
