// « Un souci, une idée ? » : le petit bouton gris présent sur chaque page. Il prend l'adresse exacte de la page
// (fragment compris), le titre et la taille de l'écran, et envoie un bug, un dysfonctionnement, une suggestion ou
// une amélioration au module 'retours' (jules/modules/retours.py). Rien ne part hors de la machine ; le parent lit.
import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Bug, Check, Lightbulb, MessageSquareWarning, Sparkles, Wrench, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { retours, type TypeRetour } from "@/api/jules"

export const TEXTES_RETOUR = {
  bouton: "Un souci, une idée ?",
  titre: "Un souci, une idée ?",
  aide: "Dis-nous ce qui ne va pas ou ce qui serait mieux. La page où tu es est jointe toute seule.",
  page: "Page",
  placeholder: {
    bug: "Qu'est-ce qui s'est passé ? Qu'est-ce que tu attendais ?",
    dysfonctionnement: "Qu'est-ce qui marche mal ou bizarrement ?",
    suggestion: "Quelle idée as-tu ?",
    amelioration: "Qu'est-ce qui pourrait être plus clair, plus simple, plus joli ?",
  } as Record<TypeRetour, string>,
  envoyer: "Envoyer",
  qui: "Qui écrit ?",
  merci: "Merci ! C'est noté.",
  fermer: "Fermer",
}

export const TYPES_RETOUR: { id: TypeRetour; nom: string; Icone: typeof Bug; classe: string }[] = [
  { id: "bug", nom: "Bug", Icone: Bug, classe: "border-[#F2B8B5] bg-[#FDF1F0] text-[#8A1F17]" },
  { id: "dysfonctionnement", nom: "Ça marche mal", Icone: Wrench, classe: "border-[#F3D9A6] bg-[#FFF8EC] text-[#7A4B00]" },
  { id: "suggestion", nom: "Suggestion", Icone: Lightbulb, classe: "border-[#C9DBF5] bg-bleu-clair text-bleu" },
  { id: "amelioration", nom: "Amélioration", Icone: Sparkles, classe: "border-[#D8C7FA] bg-perso-clair text-perso" },
]

/** `testeurs` : prénoms déclarés dans le profil (profil de test) ; vide = l'élève, pas de question. */
export function BoutonRetour({ testeurs = [] }: { testeurs?: string[] }) {
  const [ouvert, setOuvert] = useState(false)
  return (
    <>
      <motion.button onClick={() => setOuvert(true)} whileHover={{ scale: 1.06 }} whileTap={{ scale: 0.94 }}
        aria-label={TEXTES_RETOUR.bouton} title={TEXTES_RETOUR.bouton}
        className="absolute bottom-16 left-4 z-40 grid size-10 place-items-center rounded-full border border-bord bg-white/90 text-gris opacity-70 shadow-relief backdrop-blur transition-[opacity,color] hover:text-encre hover:opacity-100 focus-visible:opacity-100 sm:bottom-4">
        <MessageSquareWarning size={18} />
      </motion.button>
      <AnimatePresence>{ouvert && <FenetreRetour testeurs={testeurs} onFermer={() => setOuvert(false)} />}</AnimatePresence>
    </>
  )
}

const CLE_AUTEUR = "jules.retour-auteur"

function FenetreRetour({ testeurs, onFermer }: { testeurs: string[]; onFermer: () => void }) {
  // L'adresse est prise à l'ouverture : c'est la page que l'élève regardait.
  const [adresse] = useState(() => window.location.pathname + window.location.hash)
  const [type, setType] = useState<TypeRetour>("bug")
  const [texte, setTexte] = useState("")
  // Le dernier auteur choisi est retenu sur l'appareil (chacun teste en général sur le sien).
  const [auteur, setAuteur] = useState<string>(() => {
    try { const a = localStorage.getItem(CLE_AUTEUR) ?? ""; return testeurs.includes(a) ? a : "" } catch { return "" }
  })
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [fait, setFait] = useState(false)
  const zone = useRef<HTMLTextAreaElement>(null)
  useEffect(() => { zone.current?.focus() }, [])
  useEffect(() => { const e = (ev: KeyboardEvent) => ev.key === "Escape" && onFermer(); addEventListener("keydown", e); return () => removeEventListener("keydown", e) }, [onFermer])
  useEffect(() => { if (fait) { const t = setTimeout(onFermer, 1400); return () => clearTimeout(t) } }, [fait, onFermer])

  const envoyer = async () => {
    if (texte.trim().length < 3 || envoi || (testeurs.length > 0 && !auteur)) return
    setEnvoi(true); setErreur(null)
    try {
      await retours.deposer({ type, texte: texte.trim(), adresse, titre_page: document.title, ecran: `${innerWidth}x${innerHeight}`, auteur: auteur || undefined })
      try { if (auteur) localStorage.setItem(CLE_AUTEUR, auteur) } catch { /* stockage indisponible */ }
      setFait(true)
    } catch (e) { setErreur((e as Error).message) } finally { setEnvoi(false) }
  }

  return (
    <motion.div className="fixed inset-0 z-50 grid place-items-end bg-encre/25 p-4 backdrop-blur-[2px] sm:place-items-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onFermer}>
      <motion.div role="dialog" aria-modal aria-label={TEXTES_RETOUR.titre} onClick={(e) => e.stopPropagation()}
        initial={{ y: 24, opacity: 0, scale: 0.98 }} animate={{ y: 0, opacity: 1, scale: 1 }} exit={{ y: 16, opacity: 0 }}
        transition={{ type: "spring", stiffness: 340, damping: 30 }}
        className="w-full max-w-[520px] rounded-3xl bg-white p-5 shadow-relief-haut">
        {fait ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 14 }}
              className="grid size-14 place-items-center rounded-full bg-[#E7F5EC] text-[#1E7B34]"><Check size={28} /></motion.span>
            <p className="m-0 text-[1.1rem] font-bold text-encre">{TEXTES_RETOUR.merci}</p>
          </div>
        ) : (
          <>
            <div className="mb-1 flex items-start justify-between gap-3">
              <h2 className="m-0 text-[1.25rem] font-bold text-encre">{TEXTES_RETOUR.titre}</h2>
              <button onClick={onFermer} aria-label={TEXTES_RETOUR.fermer} className="grid size-8 place-items-center rounded-full text-gris hover:bg-nav"><X size={17} /></button>
            </div>
            <p className="mt-0 mb-4 text-[0.92rem] text-gris">{TEXTES_RETOUR.aide}</p>
            {testeurs.length > 0 && (
              <div role="radiogroup" aria-label={TEXTES_RETOUR.qui} className="mb-3 flex flex-wrap items-center gap-2">
                <span className="text-[0.9rem] font-semibold text-encre">{TEXTES_RETOUR.qui}</span>
                {testeurs.map((t) => (
                  <button key={t} role="radio" aria-checked={auteur === t} onClick={() => setAuteur(t)}
                    className={cn("rounded-full border-2 px-3.5 py-1 text-[0.9rem] font-semibold transition-colors",
                      auteur === t ? "border-bleu bg-bleu text-white" : "border-bord bg-white text-encre hover:border-bleu/40")}>
                    {t}
                  </button>
                ))}
              </div>
            )}
            <div role="radiogroup" aria-label="Type" className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {TYPES_RETOUR.map((t) => (
                <button key={t.id} role="radio" aria-checked={type === t.id} onClick={() => setType(t.id)}
                  className={cn("flex flex-col items-center gap-1 rounded-2xl border-2 px-2 py-2.5 text-[0.85rem] font-semibold transition-all",
                    type === t.id ? cn(t.classe, "shadow-relief") : "border-bord bg-white text-gris hover:border-gris/40")}>
                  <t.Icone size={18} /> {t.nom}
                </button>
              ))}
            </div>
            <textarea ref={zone} value={texte} onChange={(e) => setTexte(e.target.value)} maxLength={2000} rows={4}
              placeholder={TEXTES_RETOUR.placeholder[type]}
              onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) envoyer() }}
              className="w-full resize-y rounded-2xl border-2 border-bord bg-white px-3.5 py-2.5 text-[1rem] leading-relaxed outline-none focus:border-bleu" />
            <p className="mt-2 mb-0 truncate text-[0.8rem] text-gris" title={adresse}>{TEXTES_RETOUR.page} : <code className="rounded bg-nav px-1.5 py-0.5">{adresse}</code></p>
            {erreur && <p role="alert" className="mt-2 mb-0 text-[0.9rem] text-rouge">{erreur}</p>}
            <div className="mt-4 flex justify-end">
              <motion.button whileTap={{ scale: 0.96 }} onClick={envoyer} disabled={texte.trim().length < 3 || envoi || (testeurs.length > 0 && !auteur)}
                className="rounded-full bg-bleu px-5 py-2.5 font-semibold text-white shadow-relief disabled:opacity-40">
                {TEXTES_RETOUR.envoyer}
              </motion.button>
            </div>
          </>
        )}
      </motion.div>
    </motion.div>
  )
}
