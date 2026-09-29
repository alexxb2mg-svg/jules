// Pièces d'affichage des fiches personnelles, réutilisées par la bibliothèque, la fiche native et la
// barre latérale : tuile, filtre, section « Mes dossiers », écran d'un dossier, rappel « à ranger ».
import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, ChevronLeft, Folder, Inbox, Plus, Sparkles, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { sources, type EntreePerso } from "@/api/jules"
import { FILTRES, PASTILLE_PERSO, TEXTES, stylePerso, type Filtre } from "@/config/sources"
import { NON_CLASSE, useFiltre, rechargerPerso, useBibliothequePerso } from "./etat"

export function PastillePerso({ className }: { className?: string }) {
  return <span className={cn("rounded-full bg-perso px-1.5 py-px text-[0.68rem] font-bold tracking-wide text-white uppercase", className)}>{PASTILLE_PERSO}</span>
}

/** Filtre « Toutes · Fiches Jules · Mes fiches » (segmenté, mémorisé). */
export function FiltreFiches({ compact }: { compact?: boolean }) {
  const [filtre, setFiltre] = useFiltre()
  return (
    <div role="radiogroup" aria-label="Afficher" className={cn("inline-flex rounded-2xl bg-nav p-1", compact && "grid w-full grid-cols-[auto_1fr_1fr] rounded-xl bg-white p-0.5 ring-1 ring-bord")}>
      {FILTRES.map((f) => (
        <button key={f.id} role="radio" aria-checked={filtre === f.id} onClick={() => setFiltre(f.id)}
          className={cn("relative rounded-xl px-3.5 py-1.5 text-[0.9rem] font-semibold transition-colors", compact && "rounded-lg px-2 py-1 text-[0.75rem] whitespace-nowrap",
            filtre === f.id ? (f.id === "perso" ? "text-white" : "text-encre") : "text-gris hover:text-encre")}>
          {filtre === f.id && <motion.span layoutId={compact ? "filtre-compact" : "filtre"} transition={{ type: "spring", stiffness: 420, damping: 34 }}
            className={cn("absolute inset-0 rounded-[inherit] shadow-relief", f.id === "perso" ? "bg-perso" : compact ? "bg-bleu-clair" : "bg-white")} />}
          <span className="relative">{f.nom}</span>
        </button>
      ))}
    </div>
  )
}

export const voitNatives = (f: Filtre) => f !== "perso"
export const voitPerso = (f: Filtre) => f !== "natives"

export function TuilePerso({ f, i, onOuvrir, avecLieu }: { f: EntreePerso; i: number; onOuvrir: (id: string) => void; avecLieu?: boolean }) {
  const lieu = f.titre_notion ?? f.suggestion.titre_notion ?? f.nom_matiere ?? TEXTES.nonClasse
  return (
    <motion.button onClick={() => onOuvrir(f.id)} style={stylePerso}
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 14) * 0.025 }}
      whileHover={{ x: 4 }} whileTap={{ scale: 0.98 }}
      className="group relative flex items-center gap-4 overflow-hidden rounded-2xl border border-(--m-accent)/30 bg-white px-4 py-3.5 text-left shadow-relief transition-[border-color,box-shadow] hover:border-(--m-accent) hover:shadow-relief-haut">
      <span aria-hidden className="absolute inset-y-0 left-0 w-1 bg-(--m-accent)" />
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-(--m-fond) text-(--m-texte)"><Sparkles size={18} /></span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2"><b className="truncate leading-snug text-encre">{f.titre}</b><PastillePerso /></span>
        <span className="block truncate text-[0.85rem] text-gris">
          {f.etat === "a_ranger" && <><span className="font-semibold text-(--m-texte)">{TEXTES.aRanger}</span> · </>}
          {avecLieu && f.etat !== "a_ranger" ? `${lieu} · ` : ""}{f.source.titre}
        </span>
      </span>
      <ArrowRight size={18} className="shrink-0 text-(--m-texte) transition-transform group-hover:translate-x-1" />
    </motion.button>
  )
}

/** « Mes dossiers » + Non classé (masqué s'il est vide) + « À ranger ». */
export function SectionDossiers({ onDossier, onOuvrir }: { onDossier: (id: string) => void; onOuvrir: (id: string) => void }) {
  const biblio = useBibliothequePerso()
  const [nom, setNom] = useState<string | null>(null)
  if (!biblio) return null
  const nonClasses = biblio.fiches.filter((f) => f.etat === "rangee" && !f.notion && !f.dossier)
  const aRanger = biblio.fiches.filter((f) => f.etat === "a_ranger")
  const creer = async () => {
    if (!nom?.trim()) return
    try { await sources.creerDossier(nom); setNom(null); rechargerPerso() } catch (e) { alert((e as Error).message) }
  }
  return (
    <section style={stylePerso} className="mt-10">
      <h2 className="mt-0 mb-3 flex items-center gap-2 text-[1.15rem] font-bold text-(--m-texte)"><Folder size={19} /> {TEXTES.mesDossiers}</h2>
      {aRanger.length > 0 && (
        <div className="mb-4 grid gap-3 md:grid-cols-2">{aRanger.map((f, i) => <TuilePerso key={f.id} f={f} i={i} onOuvrir={onOuvrir} />)}</div>
      )}
      <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
        {biblio.dossiers.map((d, i) => {
          const n = biblio.fiches.filter((f) => f.dossier === d.id).length
          return <CarteDossier key={d.id} i={i} nom={d.nom} n={n} onClick={() => onDossier(d.id)} />
        })}
        {nonClasses.length > 0 && <CarteDossier i={biblio.dossiers.length} nom={TEXTES.nonClasse} n={nonClasses.length} Icone={Inbox} onClick={() => onDossier(NON_CLASSE)} />}
        <AnimatePresence mode="wait" initial={false}>
          {nom === null ? (
            <motion.button key="plus" onClick={() => setNom("")} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex h-[84px] items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-(--m-accent)/40 font-semibold text-(--m-texte) hover:bg-(--m-fond)">
              <Plus size={18} /> {TEXTES.nouveauDossier}
            </motion.button>
          ) : (
            <motion.form key="form" onSubmit={(e) => { e.preventDefault(); creer() }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex h-[84px] items-center gap-2 rounded-2xl border border-(--m-accent) bg-white px-3">
              <input autoFocus value={nom} onChange={(e) => setNom(e.target.value.slice(0, 40))} onBlur={() => !nom && setNom(null)} aria-label={TEXTES.nomDossier} placeholder={TEXTES.nomDossier}
                className="h-10 min-w-0 flex-1 rounded-xl bg-nav px-3 outline-none" />
              <button type="submit" className="rounded-xl bg-(--m-accent) px-3 py-2 text-[0.9rem] font-semibold text-white">{TEXTES.creer}</button>
            </motion.form>
          )}
        </AnimatePresence>
      </div>
    </section>
  )
}

function CarteDossier({ nom, n, i, onClick, Icone = Folder }: { nom: string; n: number; i: number; onClick: () => void; Icone?: typeof Folder }) {
  return (
    <motion.button onClick={onClick} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} whileHover={{ y: -3 }} whileTap={{ scale: 0.97 }}
      className="group flex h-[84px] items-center gap-3 rounded-2xl border border-bord bg-white px-4 text-left shadow-relief hover:border-(--m-accent)">
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-(--m-fond) text-(--m-texte) transition-transform group-hover:-rotate-6"><Icone size={21} /></span>
      <span className="min-w-0"><b className="block truncate text-encre">{nom}</b><span className="text-[0.85rem] text-gris">{n} fiche{n > 1 ? "s" : ""}</span></span>
    </motion.button>
  )
}

/** Écran d'un dossier personnel (ou de Non classé). */
export function EcranDossier({ id, onRetour, onOuvrir }: { id: string; onRetour: () => void; onOuvrir: (id: string) => void }) {
  const biblio = useBibliothequePerso()
  const dossier = biblio?.dossiers.find((d) => d.id === id)
  const liste = (biblio?.fiches ?? []).filter((f) => (id === NON_CLASSE ? f.etat === "rangee" && !f.notion && !f.dossier : f.dossier === id))
  const supprimer = async () => {
    if (!confirm(TEXTES.confirmerSupprimerDossier)) return
    await sources.supprimerDossier(id); await rechargerPerso(); onRetour()
  }
  return (
    <div className="mx-auto max-w-[1180px] px-5 pt-16 pb-16 md:px-10 md:pt-8" style={stylePerso}>
      <button onClick={onRetour} className="mb-1 inline-flex items-center gap-1 py-2 text-[0.95rem] font-semibold text-gris hover:text-bleu"><ChevronLeft size={16} /> Mes fiches</button>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="m-0 flex items-center gap-3 text-[2.2rem] leading-tight font-bold text-encre">
          <span className="grid size-12 place-items-center rounded-2xl bg-(--m-fond) text-(--m-texte)">{id === NON_CLASSE ? <Inbox size={24} /> : <Folder size={24} />}</span>
          {id === NON_CLASSE ? TEXTES.nonClasse : dossier?.nom ?? "…"}
        </h1>
        {dossier && <button onClick={supprimer} className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[0.9rem] font-semibold text-gris hover:bg-survol hover:text-rouge"><Trash2 size={15} /> {TEXTES.supprimerDossier}</button>}
      </div>
      {biblio && liste.length === 0 && <p className="text-gris">{TEXTES.videDossier}</p>}
      <div className="grid gap-3 md:grid-cols-2">{liste.map((f, i) => <TuilePerso key={f.id} f={f} i={i} onOuvrir={onOuvrir} avecLieu />)}</div>
    </div>
  )
}

/** Au démarrage : les fiches laissées « à ranger » (fermeture brutale) rappellent la question (contrat §7). */
export function RappelARanger({ onOuvrir }: { onOuvrir: (id: string) => void }) {
  const biblio = useBibliothequePerso()
  const [vu, setVu] = useState(false)
  const aRanger = (biblio?.fiches ?? []).filter((f) => f.etat === "a_ranger")
  useEffect(() => { if (aRanger.length === 0) setVu(false) }, [aRanger.length])
  return (
    <AnimatePresence>
      {!vu && aRanger.length > 0 && (
        <motion.div role="status" style={stylePerso} initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 60, opacity: 0 }}
          className="fixed right-4 bottom-4 left-4 z-40 mx-auto flex max-w-[520px] items-center gap-3 rounded-2xl bg-encre px-4 py-3 text-white shadow-relief-haut md:left-auto">
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-(--m-accent)"><Inbox size={18} /></span>
          <span className="min-w-0 flex-1 text-[0.95rem]">{TEXTES.aRangerAuDemarrage(aRanger.length)}</span>
          <button onClick={() => { setVu(true); onOuvrir(aRanger[0].id) }} className="rounded-xl bg-white px-3 py-1.5 text-[0.9rem] font-semibold text-encre">{TEXTES.voir}</button>
          <button onClick={() => setVu(true)} aria-label="Fermer" className="rounded-full p-1 text-white/70 hover:text-white">×</button>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
