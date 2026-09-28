// Une fiche personnelle : le MÊME rendu que les fiches natives (FicheVisuelle), habillé à la couleur perso,
// et la question « On garde cette fiche ? » posée avant de la quitter tant qu'elle est à ranger (contrat §7).
import { useCallback, useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { FolderPlus, Folder, Inbox, RefreshCw, Sparkles, Trash2, TriangleAlert, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { sources, type EtapeSource, type FichePerso, type ModeRangement } from "@/api/jules"
import { FicheVisuelle } from "@/modules/fiches/FicheVisuelle"
import { PASTILLE_PERSO, TEXTES, stylePerso } from "@/config/sources"
import { noterOuverture, oublierRecente, poserGarde, rechargerPerso, useBibliothequePerso } from "./etat"

export function FichePersonnelle({ id, onRetour, onOuvrirLecon, onRegeneree }: {
  id: string
  onRetour: () => void
  onOuvrirLecon: (notion: string) => void
  onRegeneree: (id: string) => void
}) {
  const [fiche, setFiche] = useState<FichePerso | null>(null)
  const [question, setQuestion] = useState<(() => void) | null>(null)
  const [refaire, setRefaire] = useState<string | null>(null)
  const aRanger = fiche?.rangement.etat === "a_ranger"

  // Garde : tant que la fiche est à ranger, toute sortie (nav, retour, lien) passe par la question.
  useEffect(() => {
    if (!aRanger) { poserGarde(null); return }
    poserGarde((continuer) => setQuestion(() => continuer))
    return () => poserGarde(null)
  }, [aRanger])
  // Fermeture brutale : le navigateur n'autorise pas de question personnalisée. La fiche reste « à ranger »
  // et la question revient à la prochaine ouverture (contrat §7).
  useEffect(() => {
    if (!aRanger) return
    const avant = (e: BeforeUnloadEvent) => { e.preventDefault() }
    addEventListener("beforeunload", avant)
    return () => removeEventListener("beforeunload", avant)
  }, [aRanger])

  const charger = useCallback((x: string) => sources.lire(x) as Promise<FichePerso>, [])
  const chargee = useCallback((f: unknown) => {
    const p = f as FichePerso
    setFiche(p)
    noterOuverture({ genre: "perso", id, titre: p.titre, matiere: p.matiere })
  }, [id])

  const supprimer = async () => {
    if (!confirm(TEXTES.confirmerSupprimer)) return
    poserGarde(null)
    await sources.supprimer(id)
    oublierRecente(id)
    await rechargerPerso()
    onRetour()
  }

  const regenerer = async () => {
    setRefaire(TEXTES.refaire + "…")
    try {
      const fin: EtapeSource = await sources.regenerer(id, () => {})
      if (fin.etape === "fin") {
        await sources.supprimer(id) // l'ancienne version part, la source reste à la nouvelle
        oublierRecente(id)
        await rechargerPerso()
        poserGarde(null)
        onRegeneree(fin.fiche.id)
      } else if (fin.etape === "erreur") setRefaire(fin.message)
    } catch (e) { setRefaire((e as Error).message) }
  }

  const matiere = fiche?.nom_matiere && fiche.matiere ? ` · ${fiche.nom_matiere}` : ""
  return (
    <>
      <FicheVisuelle notion={id} retour="Mes fiches" onRetour={onRetour} onOuvrirLecon={onOuvrirLecon}
        charger={charger} onChargee={chargee}
        habillage={{
          style: stylePerso,
          accueil: TEXTES.accueilJulesPerso,
          mention: fiche ? TEXTES.mentionSource(fiche.source.titre) : "",
          surtitre: (
            <span className="inline-flex items-center gap-2">
              <span className="rounded-full bg-(--m-accent) px-2 py-0.5 text-[0.75rem] font-bold tracking-wide text-white uppercase">{PASTILLE_PERSO}</span>
              {TEXTES.enteteFichePerso}{matiere}
            </span>
          ),
          actions: fiche && (
            <>
              {aRanger && (
                <button onClick={() => setQuestion(() => () => {})}
                  className="inline-flex items-center gap-1.5 rounded-full bg-(--m-accent) px-3.5 py-1.5 text-[0.9rem] font-semibold text-white shadow-relief">
                  <Inbox size={15} /> {TEXTES.questionGarder}
                </button>
              )}
              <button onClick={regenerer} disabled={!!refaire && refaire.endsWith("…")}
                className="inline-flex items-center gap-1.5 rounded-full bg-white px-3.5 py-1.5 text-[0.9rem] font-semibold text-(--m-texte) shadow-relief disabled:opacity-60">
                <RefreshCw size={15} className={cn(refaire?.endsWith("…") && "animate-spin")} /> {TEXTES.refaire}
              </button>
              <button onClick={supprimer}
                className="inline-flex items-center gap-1.5 rounded-full bg-white px-3.5 py-1.5 text-[0.9rem] font-semibold text-gris shadow-relief hover:text-rouge">
                <Trash2 size={15} /> {TEXTES.supprimer}
              </button>
              {refaire && !refaire.endsWith("…") && <span role="alert" className="text-[0.88rem] text-rouge">{refaire}</span>}
            </>
          ),
        }} />
      <AnimatePresence>
        {question && fiche && (
          <QuestionRangement fiche={fiche}
            onFermer={() => setQuestion(null)}
            onFait={async (garde) => {
              const continuer = question
              setQuestion(null)
              poserGarde(null)
              if (!garde) oublierRecente(id)
              await rechargerPerso()
              if (garde) setFiche({ ...fiche, rangement: { ...fiche.rangement, etat: "rangee" } })
              continuer()
            }} />
        )}
      </AnimatePresence>
    </>
  )
}

/** « On garde cette fiche ? » : notion suggérée, dossier, Non classé, ou ne pas garder. Pas de « plus tard ». */
export function QuestionRangement({ fiche, onFermer, onFait }: {
  fiche: Pick<FichePerso, "id" | "titre" | "rangement">
  onFermer: () => void
  onFait: (garde: boolean) => void
}) {
  const biblio = useBibliothequePerso()
  const [dossiers, setDossiers] = useState(false)
  const [nouveau, setNouveau] = useState("")
  const [erreur, setErreur] = useState<string | null>(null)
  const [occupe, setOccupe] = useState(false)
  const boite = useRef<HTMLDivElement>(null)
  const suggestion = fiche.rangement.suggestion
  const avecNotion = !!suggestion?.notion

  useEffect(() => { boite.current?.querySelector<HTMLButtonElement>("button[data-principal]")?.focus() }, [dossiers])
  useEffect(() => {
    const echap = (e: KeyboardEvent) => { if (e.key === "Escape") onFermer() }
    addEventListener("keydown", echap)
    return () => removeEventListener("keydown", echap)
  }, [onFermer])

  const ranger = async (mode: ModeRangement, dossier?: string) => {
    setOccupe(true); setErreur(null)
    try { await sources.ranger(fiche.id, mode, dossier); onFait(true) }
    catch (e) { setErreur((e as Error).message); setOccupe(false) }
  }
  const creerEtRanger = async () => {
    if (!nouveau.trim()) return
    setOccupe(true); setErreur(null)
    try { const d = await sources.creerDossier(nouveau); await ranger("dossier", d.id) }
    catch (e) { setErreur((e as Error).message); setOccupe(false) }
  }
  const jeter = async () => {
    setOccupe(true)
    try { await sources.supprimer(fiche.id); onFait(false) } catch (e) { setErreur((e as Error).message); setOccupe(false) }
  }

  const bouton = "flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-[1rem] font-semibold transition-colors disabled:opacity-50"
  return (
    <motion.div className="fixed inset-0 z-50 grid place-items-end bg-encre/40 p-3 backdrop-blur-[2px] sm:place-items-center" style={stylePerso}
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onFermer}>
      <motion.div ref={boite} role="dialog" aria-modal="true" aria-labelledby="question-garder" onClick={(e) => e.stopPropagation()}
        initial={{ y: 40, scale: 0.97, opacity: 0 }} animate={{ y: 0, scale: 1, opacity: 1 }} exit={{ y: 30, opacity: 0 }}
        transition={{ type: "spring", stiffness: 380, damping: 32 }}
        className="relative w-full max-w-[460px] rounded-3xl bg-white p-5 shadow-relief-haut sm:p-6">
        <button onClick={onFermer} aria-label={TEXTES.annuler} className="absolute top-4 right-4 rounded-full p-1.5 text-gris hover:bg-survol"><X size={18} /></button>
        <div className="mb-4 flex items-center gap-3 pr-8">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-(--m-fond) text-(--m-texte)"><Sparkles size={22} /></span>
          <div className="min-w-0">
            <h2 id="question-garder" className="m-0 text-[1.25rem] font-bold text-encre">{TEXTES.questionGarder}</h2>
            <p className="m-0 truncate text-[0.92rem] text-gris">{fiche.titre}</p>
          </div>
        </div>
        {!avecNotion && <p className="mt-0 mb-3 flex items-start gap-2 rounded-2xl bg-[#FFF8EC] px-3.5 py-2.5 text-[0.9rem] text-[#7A4B00]"><TriangleAlert size={16} className="mt-0.5 shrink-0" />{TEXTES.aucuneNotion}</p>}

        <AnimatePresence mode="wait" initial={false}>
          {!dossiers ? (
            <motion.div key="choix" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} className="flex flex-col gap-2">
              {avecNotion && (
                <button data-principal disabled={occupe} onClick={() => ranger("notion")} className={cn(bouton, "bg-(--m-accent) text-white shadow-relief hover:brightness-110")}>
                  <Sparkles size={19} className="shrink-0" /><span className="min-w-0">{TEXTES.garderNotion(suggestion!.titre_notion!)}</span>
                </button>
              )}
              <button disabled={occupe} onClick={() => setDossiers(true)} className={cn(bouton, "bg-(--m-fond) text-(--m-texte) hover:brightness-95")}>
                <Folder size={19} className="shrink-0" />{TEXTES.garderDossier}
              </button>
              <button data-principal={!avecNotion || undefined} disabled={occupe} onClick={() => ranger("non_classe")}
                className={cn(bouton, avecNotion ? "bg-nav text-encre hover:bg-survol" : "bg-(--m-accent) text-white shadow-relief hover:brightness-110")}>
                <Inbox size={19} className="shrink-0" />{TEXTES.garderNonClasse}
              </button>
              <button disabled={occupe} onClick={jeter} className={cn(bouton, "mt-1 justify-center bg-transparent text-[0.95rem] text-gris hover:text-rouge")}>
                {TEXTES.pasGarder}
              </button>
            </motion.div>
          ) : (
            <motion.div key="dossiers" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }} className="flex flex-col gap-2">
              {(biblio?.dossiers ?? []).map((d, i) => (
                <button key={d.id} data-principal={i === 0 || undefined} disabled={occupe} onClick={() => ranger("dossier", d.id)} className={cn(bouton, "bg-nav text-encre hover:bg-(--m-fond)")}>
                  <Folder size={19} className="shrink-0 text-(--m-texte)" /><span className="truncate">{d.nom}</span>
                </button>
              ))}
              <form onSubmit={(e) => { e.preventDefault(); creerEtRanger() }} className="flex gap-2">
                <label className="sr-only" htmlFor="nouveau-dossier">{TEXTES.nomDossier}</label>
                <input id="nouveau-dossier" value={nouveau} onChange={(e) => setNouveau(e.target.value.slice(0, 40))} placeholder={TEXTES.nouveauDossier}
                  autoFocus={!(biblio?.dossiers.length)} className="h-12 min-w-0 flex-1 rounded-2xl border border-bord px-4 outline-none focus:border-(--m-accent) focus:ring-4 focus:ring-(--m-fond)" />
                <button type="submit" disabled={occupe || !nouveau.trim()} className="inline-flex items-center gap-1.5 rounded-2xl bg-(--m-accent) px-4 font-semibold text-white disabled:opacity-40">
                  <FolderPlus size={17} />{TEXTES.creer}
                </button>
              </form>
              <button onClick={() => setDossiers(false)} className="mt-1 self-start rounded-full px-2 py-1 text-[0.92rem] font-semibold text-gris hover:text-encre">‹ Retour</button>
            </motion.div>
          )}
        </AnimatePresence>
        {erreur && <p role="alert" className="mt-3 mb-0 text-[0.92rem] text-rouge">{erreur}</p>}
      </motion.div>
    </motion.div>
  )
}
