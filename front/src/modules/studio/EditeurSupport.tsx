// Un support ouvert : écran partagé trame | relecture de Jules (docs/STUDIO-CONTRAT.md §6).
// L'élève écrit, Jules relit l'existant (route relire, garde-fou serveur), le serveur seul décide de la
// validation (pret_a_valider, anti-copie). Validé = lecture seule, dévalidation possible (avec confirmation
// pour les cartes mémoire, dont la programmation des révisions est perdue).
import { useCallback, useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { CheckCircle2, ChevronLeft, Lock, LockOpen, Search, Trash2, TriangleAlert } from "lucide-react"
import { cn } from "@/lib/utils"
import { infos as lireInfos, studio, type Support } from "@/api/jules"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import { Riche } from "@/modules/fiches/texte"
import { STATUTS, TYPES, elementsComptes } from "./config"
import { Champ, EDITEURS, type Chemin } from "./editeurs"

const TEXTES = {
  relire: "Demander à Jules de relire",
  relit: "Jules relit…",
  valider: "Valider mon support",
  devalider: "Dévalider pour modifier",
  supprimer: "Supprimer ce brouillon",
  verrouille: "Validé : en lecture seule. Il compte dans ton travail de la notion.",
  verrouilleCartes: "Validé : tes cartes entrent dans tes révisions (1, 3, 7, 15, 30, 60 jours).",
  confirmerCartes: "Dévalider efface la programmation des révisions de ces cartes. Elles repartiront de zéro. On y va ?",
  confirmerSuppression: "Supprimer ce brouillon ? C'est définitif.",
  oui: "Oui", non: "Non",
  julesVide: "Écris d'abord, puis demande-moi de relire : je te pose des questions sur ce que tu as écrit, je n'écris jamais à ta place.",
  pret: "Prêt à être validé.",
}

type Retour = { id: number; message: string }

export function EditeurSupport({ id, matiere, onRetour, onSupprime }: {
  id: string; matiere: string | null; onRetour: () => void; onSupprime: () => void
}) {
  const [support, setSupport] = useState<Support | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [message, setMessage] = useState<{ texte: string; ton: "erreur" | "ok" } | null>(null)
  const [retours, setRetours] = useState<Retour[]>([])
  const [relit, setRelit] = useState(false)
  const [confirmer, setConfirmer] = useState<"devalider" | "supprimer" | null>(null)
  const [nomJules, setNomJules] = useState("Jules")

  useEffect(() => {
    let annule = false
    studio.lire(id).then((r) => !annule && setSupport(r.support)).catch((e) => !annule && setErreur(e.message))
    lireInfos().then((i) => !annule && setNomJules(i.persona.nom)).catch(() => {})
    return () => { annule = true }
  }, [id])

  const ecrire = useCallback(async (chemin: Chemin, valeur: string) => {
    try { const r = await studio.ecrire(id, chemin, valeur); setSupport(r.support); setMessage(null) }
    catch (e) { setMessage({ texte: (e as Error).message, ton: "erreur" }); throw e }
  }, [id])

  const ajouter = useCallback(async (parent?: string | null) => {
    if (!support) return
    const def = TYPES[support.type]
    const liste = (support.contenu[def.liste] || []) as unknown[]
    const champ = { noeuds: "texte", sections: "titre", questions: "question", cartes: "recto" }[def.liste]
    try {
      let r = await studio.ecrire(id, [def.liste, liste.length, champ], "")
      if (support.type === "carte_mentale" && parent) r = await studio.rattacher(id, liste.length, parent)
      setSupport(r.support); setMessage(null)
    } catch (e) { setMessage({ texte: (e as Error).message, ton: "erreur" }) }
  }, [id, support])

  const rattacher = useCallback(async (index: number, parent: string | null) => {
    const r = await studio.rattacher(id, index, parent); setSupport(r.support)
  }, [id])

  const action = async (f: () => Promise<{ support: Support }>, ok?: string) => {
    setMessage(null)
    try { const r = await f(); setSupport(r.support); if (ok) setMessage({ texte: ok, ton: "ok" }) }
    catch (e) { setMessage({ texte: (e as Error).message, ton: "erreur" }) }
  }

  const relire = async () => {
    // Laisser le champ en cours s'enregistrer (blur) avant la relecture.
    ;(document.activeElement as HTMLElement | null)?.blur()
    await new Promise((r) => setTimeout(r, 150))
    setRelit(true)
    try {
      const r = await studio.relire(id)
      setSupport(r.support)
      setRetours((prec) => [...prec, ...r.retours.map((x, k) => ({ id: Date.now() + k, message: x.message }))])
    } catch (e) { setMessage({ texte: (e as Error).message, ton: "erreur" }) } finally { setRelit(false) }
  }

  const supprimer = async () => {
    try { await studio.supprimer(id); onSupprime() } catch (e) { setMessage({ texte: (e as Error).message, ton: "erreur" }) }
  }

  if (erreur) return <div className="grid h-full place-items-center p-8 text-gris">Impossible d'ouvrir ce support ({erreur}).</div>
  if (!support) return <div className="grid h-full place-items-center"><div className="size-10 animate-spin rounded-full border-4 border-bord border-t-(--m-accent)" /></div>

  const def = TYPES[support.type]
  const verrouille = support.statut === "valide"
  const compte = elementsComptes(support)
  const manque = Math.max(0, def.minimum - compte)
  const statut = STATUTS[support.statut]!
  const Editeur = EDITEURS[support.type]

  return (
    <div className="flex h-full flex-col lg:flex-row" style={styleMatiere(matiere || "")}>
      {/* Trame */}
      <div className="min-h-0 flex-1 overflow-y-auto">
        <header className="sticky top-0 z-20 border-b border-bord bg-[#FBFBFE]/85 px-5 pt-4 pb-3 pl-16 backdrop-blur md:px-10">
          <button onClick={onRetour} className="mb-2 inline-flex items-center gap-1 rounded-full px-2 py-2 text-[0.88rem] font-semibold text-(--m-texte) hover:bg-(--m-fond)">
            <ChevronLeft size={16} /> Exercices et supports
          </button>
          <div className="flex flex-wrap items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-(--m-fond) text-(--m-texte)"><def.Icone size={21} /></span>
            <div className="min-w-[200px] flex-1">
              <Champ valeur={support.titre} chemin={["titre"]} ecrire={ecrire} verrouille={verrouille} label="Titre du support"
                placeholder={`Titre de ta ${def.nom.toLowerCase()}…`} className="font-titre text-[1.5rem] font-bold text-encre" />
            </div>
            <span className={cn("rounded-full px-3 py-1 text-[0.82rem] font-semibold", statut.classe)}>{statut.texte}</span>
          </div>
          {/* Jauge vers la validation : même règle que le serveur, le serveur reste seul juge */}
          {!verrouille && (
            <div className="mt-3 flex items-center gap-3">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-bord">
                <motion.div className="h-full rounded-full bg-(--m-accent)" initial={false} animate={{ width: `${Math.min(100, (compte / def.minimum) * 100)}%` }} />
              </div>
              <span className={cn("text-[0.85rem] font-semibold", manque ? "text-gris" : "text-vert")}>{manque ? def.manque(manque) : TEXTES.pret}</span>
            </div>
          )}
        </header>

        <div className="mx-auto max-w-[900px] px-5 pt-6 pb-32 md:px-10">
          {verrouille && (
            <p className="mt-0 mb-5 flex items-center gap-2 rounded-2xl bg-[#E7F5EC] px-4 py-2.5 text-[0.92rem] text-[#135C33]">
              <Lock size={16} /> {support.type === "cartes_memoire" ? TEXTES.verrouilleCartes : TEXTES.verrouille}
            </p>
          )}
          {!verrouille && compte === 0 && <p className="mt-0 mb-5 text-gris">{def.vide}</p>}
          <Editeur support={support} verrouille={verrouille} ecrire={ecrire} ajouter={ajouter} rattacher={rattacher} />
        </div>
      </div>

      {/* Jules + actions */}
      <aside className="flex max-h-[45vh] shrink-0 flex-col border-t border-bord bg-white lg:max-h-none lg:w-[360px] lg:border-t-0 lg:border-l">
        <div className="flex items-center gap-2.5 border-b border-bord px-4 py-3">
          <img src="/api/persona/avatar" alt="" className="size-9 rounded-full bg-(--m-fond)" onError={(e) => ((e.target as HTMLImageElement).style.visibility = "hidden")} />
          <b className="text-[1rem]">{nomJules} relit</b>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3" aria-live="polite">
          {retours.length === 0 && !relit && <p className="m-0 rounded-2xl bg-nav px-3.5 py-2.5 text-[0.92rem] leading-relaxed text-gris">{TEXTES.julesVide}</p>}
          <div className="flex flex-col gap-2.5">
            <AnimatePresence initial={false}>
              {retours.map((r) => (
                <motion.div key={r.id} initial={{ opacity: 0, y: 10, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
                  className="rounded-2xl rounded-tl-md bg-(--m-fond) px-3.5 py-2.5 text-[0.95rem] leading-relaxed whitespace-pre-line text-encre">
                  <Riche texte={r.message} />
                </motion.div>
              ))}
            </AnimatePresence>
            {relit && (
              <div className="flex w-fit items-center gap-1 rounded-2xl bg-nav px-4 py-3" aria-label={TEXTES.relit}>
                {[0, 1, 2].map((k) => <motion.span key={k} className="size-2 rounded-full bg-gris" animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 0.8, delay: k * 0.15 }} />)}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2 border-t border-bord p-4">
          <AnimatePresence>
            {message && (
              <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} role="status"
                className={cn("m-0 flex items-start gap-2 rounded-xl px-3 py-2 text-[0.88rem]", message.ton === "erreur" ? "bg-[#FFF8EC] text-[#7A4B00]" : "bg-[#EEFAF2] text-[#135C33]")}>
                {message.ton === "erreur" ? <TriangleAlert size={16} className="mt-0.5 shrink-0" /> : <CheckCircle2 size={16} className="mt-0.5 shrink-0" />}{message.texte}
              </motion.p>
            )}
          </AnimatePresence>

          {confirmer ? (
            <div className="rounded-xl border-2 border-[#F3D9A6] bg-[#FFF8EC] p-3">
              <p className="mt-0 mb-2 text-[0.9rem] text-[#7A4B00]">{confirmer === "supprimer" ? TEXTES.confirmerSuppression : TEXTES.confirmerCartes}</p>
              <div className="flex gap-2">
                <button className="rounded-full bg-[#7A4B00] px-4 py-1.5 text-[0.9rem] font-semibold text-white" autoFocus
                  onClick={() => { const c = confirmer; setConfirmer(null); if (c === "supprimer") supprimer(); else action(() => studio.devalider(id)) }}>{TEXTES.oui}</button>
                <button className="rounded-full px-4 py-1.5 text-[0.9rem] font-semibold text-[#7A4B00] hover:bg-white" onClick={() => setConfirmer(null)}>{TEXTES.non}</button>
              </div>
            </div>
          ) : verrouille ? (
            <button onClick={() => (support.type === "cartes_memoire" ? setConfirmer("devalider") : action(() => studio.devalider(id)))}
              className="inline-flex items-center justify-center gap-2 rounded-full border-2 border-bord px-4 py-2 font-semibold text-encre hover:border-(--m-accent)">
              <LockOpen size={16} /> {TEXTES.devalider}
            </button>
          ) : (
            <>
              <motion.button whileTap={{ scale: 0.97 }} onClick={relire} disabled={relit || compte === 0}
                className="inline-flex items-center justify-center gap-2 rounded-full border-2 border-(--m-accent) px-4 py-2 font-semibold text-(--m-texte) hover:bg-(--m-fond) disabled:opacity-40">
                <Search size={16} /> {relit ? TEXTES.relit : TEXTES.relire}
              </motion.button>
              <motion.button whileTap={{ scale: 0.97 }} disabled={manque > 0} onClick={() => action(() => studio.valider(id))}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-(--m-texte) px-4 py-2.5 font-semibold text-white shadow-relief disabled:opacity-40">
                <CheckCircle2 size={17} /> {TEXTES.valider}
              </motion.button>
              <button onClick={() => setConfirmer("supprimer")} className="inline-flex items-center justify-center gap-1.5 py-1 text-[0.85rem] text-gris hover:text-rouge">
                <Trash2 size={14} /> {TEXTES.supprimer}
              </button>
            </>
          )}
        </div>
      </aside>
    </div>
  )
}
