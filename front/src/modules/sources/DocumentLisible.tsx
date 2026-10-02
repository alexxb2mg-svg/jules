// H : « Mon document », version lisible du document apporté (idée venue du Livre Scolaire / Doc'Adapt).
// Le texte de l'élève tel qu'il a été lu (rien n'est réécrit), mis en page pour la lecture : taille réglable,
// interligne et police des adaptations dys (variables --adapt-* posées par appliquerLeviers), paragraphes aérés,
// lecture à voix haute avec une voix INSTALLÉE sur l'appareil seulement (même règle que lecture-vocale.js).
import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { AArrowDown, AArrowUp, Pause, Volume2, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { sources } from "@/api/jules"

export const LISIBLE = {
  bouton: "Mon document",
  titre: "Ton document, en version lisible",
  aide: "C'est ton document tel que Jules l'a lu. La fiche à côté en est une mise en forme.",
  photos: "Tes photos",
  vide: "Ce document ne contient que des photos : Jules les a lues directement.",
  lire: "Écouter",
  arreter: "Arrêter",
  sansVoix: "Lecture à voix haute indisponible : aucune voix installée sur cet appareil.",
  plus: "Texte plus grand", moins: "Texte plus petit", fermer: "Fermer",
}

type Doc = { type: string; titre: string; texte: string; images: string[] }
const TAILLES = [1, 1.15, 1.3, 1.5]

function voixLocale(): SpeechSynthesisVoice | null {
  if (!("speechSynthesis" in window)) return null
  const fr = speechSynthesis.getVoices().filter((v) => v.localService && v.lang.toLowerCase().startsWith("fr"))
  return fr[0] ?? null
}

export function DocumentLisible({ id, onFermer }: { id: string; onFermer: () => void }) {
  const [doc, setDoc] = useState<Doc | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [taille, setTaille] = useState(1)
  const [lecture, setLecture] = useState(false)
  const [voix, setVoix] = useState<SpeechSynthesisVoice | null>(null)
  useEffect(() => { sources.source(id).then(setDoc).catch((e) => setErreur(e.message)) }, [id])
  useEffect(() => {
    const maj = () => setVoix(voixLocale())
    maj(); window.speechSynthesis?.addEventListener?.("voiceschanged", maj)
    return () => { window.speechSynthesis?.removeEventListener?.("voiceschanged", maj); window.speechSynthesis?.cancel() }
  }, [])
  useEffect(() => { const e = (ev: KeyboardEvent) => ev.key === "Escape" && onFermer(); addEventListener("keydown", e); return () => removeEventListener("keydown", e) }, [onFermer])

  // Une ligne du document = un paragraphe (les retours à la ligne de l'élève sont gardés), sauf les lignes
  // coupées au milieu d'une phrase (PDF) : une ligne qui ne finit ni par . : ! ? ni par une fin de titre est recollée.
  const paragraphes = useMemo(() => {
    const lignes = (doc?.texte ?? "").split(/\n/).map((l) => l.trim())
    const sortie: string[] = []
    let courant = ""
    for (const l of lignes) {
      if (!l) { if (courant) sortie.push(courant); courant = ""; continue }
      courant = courant ? `${courant} ${l}` : l
      if (/[.:!?»)]$/.test(l) || /^(\d+[.)]|[-•–])\s/.test(l) || l.length < 60) { sortie.push(courant); courant = "" }
    }
    if (courant) sortie.push(courant)
    return sortie
  }, [doc])
  const lire = () => {
    if (!voix || !doc) return
    if (lecture) { speechSynthesis.cancel(); setLecture(false); return }
    const u = new SpeechSynthesisUtterance(paragraphes.join("\n\n"))
    u.voice = voix; u.lang = voix.lang; u.rate = 0.95
    u.onend = u.onerror = () => setLecture(false)
    speechSynthesis.speak(u); setLecture(true)
  }

  return (
    <motion.div className="fixed inset-0 z-50 flex justify-end bg-encre/30 backdrop-blur-[2px]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onFermer}>
      <motion.aside role="dialog" aria-label={LISIBLE.titre} onClick={(e) => e.stopPropagation()}
        initial={{ x: 60, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 60, opacity: 0 }} transition={{ type: "spring", stiffness: 320, damping: 34 }}
        className="flex h-full w-full max-w-[720px] flex-col bg-[var(--adapt-fond,#FFFDF7)] shadow-relief-haut">
        <header className="flex flex-wrap items-center gap-2 border-b border-bord px-5 py-3">
          <div className="min-w-0 flex-1">
            <p className="m-0 text-[0.8rem] font-semibold tracking-wide text-perso">{doc?.titre ?? "…"}</p>
            <h2 className="m-0 truncate text-[1.15rem] font-bold text-encre">{LISIBLE.titre}</h2>
          </div>
          <div className="flex items-center gap-1 rounded-full bg-white p-1 shadow-relief">
            <button aria-label={LISIBLE.moins} title={LISIBLE.moins} disabled={taille === 0} onClick={() => setTaille((t) => Math.max(0, t - 1))}
              className="grid size-9 place-items-center rounded-full text-encre hover:bg-nav disabled:opacity-35"><AArrowDown size={18} /></button>
            <button aria-label={LISIBLE.plus} title={LISIBLE.plus} disabled={taille === TAILLES.length - 1} onClick={() => setTaille((t) => Math.min(TAILLES.length - 1, t + 1))}
              className="grid size-9 place-items-center rounded-full text-encre hover:bg-nav disabled:opacity-35"><AArrowUp size={18} /></button>
          </div>
          {paragraphes.length > 0 && (
            <button onClick={lire} disabled={!voix} title={voix ? undefined : LISIBLE.sansVoix}
              className={cn("inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-[0.9rem] font-semibold shadow-relief disabled:opacity-45",
                lecture ? "bg-perso text-white" : "bg-white text-perso")}>
              {lecture ? <Pause size={16} /> : <Volume2 size={16} />} {lecture ? LISIBLE.arreter : LISIBLE.lire}
            </button>
          )}
          <button onClick={onFermer} aria-label={LISIBLE.fermer} className="grid size-9 place-items-center rounded-full text-gris hover:bg-nav"><X size={18} /></button>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6 md:px-10">
          <p className="mt-0 mb-5 rounded-2xl bg-perso-clair px-4 py-2.5 text-[0.9rem] text-perso">{LISIBLE.aide}</p>
          {erreur && <p className="text-rouge">{erreur}</p>}
          {!doc && !erreur && <div className="h-40 animate-pulse rounded-2xl bg-nav" />}
          <article style={{ fontSize: `calc(1.12rem * var(--adapt-echelle-texte, 1) * ${TAILLES[taille]})` }}
            className="mx-auto max-w-[var(--adapt-longueur-ligne,62ch)] text-encre [font-family:var(--adapt-police,inherit)] [letter-spacing:var(--adapt-espacement-lettres,0.01em)] [line-height:var(--adapt-interligne,1.8)] [word-spacing:var(--adapt-espacement-mots,0.08em)]">
            {paragraphes.map((p, i) => <p key={i} className="mt-0 mb-[1.1em]">{exposants(p)}</p>)}
            {doc && paragraphes.length === 0 && doc.images.length > 0 && <p className="text-gris">{LISIBLE.vide}</p>}
          </article>
          {doc && doc.images.length > 0 && (
            <section className="mx-auto mt-6 max-w-[62ch]">
              <h3 className="mt-0 mb-3 text-[0.95rem] font-bold text-gris">{LISIBLE.photos}</h3>
              <div className="flex flex-col gap-4">
                {doc.images.map((src) => <img key={src} src={src} alt="" className="w-full rounded-2xl border border-bord bg-white shadow-relief" />)}
              </div>
            </section>
          )}
        </div>
      </motion.aside>
    </motion.div>
  )
}

/** « 10^8 » ou « 10^-3 » tapé au clavier → vrai exposant à l'affichage ; le texte lui-même ne change pas. */
function exposants(t: string): React.ReactNode[] {
  return t.split(/(\^-?\d+)/).map((m, i) => (m.startsWith("^") ? <sup key={i}>{m.slice(1)}</sup> : m))
}

export function BoutonDocument({ id }: { id: string }) {
  const [ouvert, setOuvert] = useState(false)
  return (
    <>
      <button onClick={() => setOuvert(true)}
        className="inline-flex items-center gap-1.5 rounded-full bg-white px-3.5 py-1.5 text-[0.9rem] font-semibold text-(--m-texte) shadow-relief">
        <Volume2 size={15} /> {LISIBLE.bouton}
      </button>
      <AnimatePresence>{ouvert && <DocumentLisible id={id} onFermer={() => setOuvert(false)} />}</AnimatePresence>
    </>
  )
}
