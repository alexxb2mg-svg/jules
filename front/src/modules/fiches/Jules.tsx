// Jules sur une fiche : bulles préécrites (champ `jules:` des blocs), aucun appel IA (jules_cadrage_interface.md).
// Même règle que accueil.js : une seule bulle à la fois ; elle reste le temps de la lire (6 à 20 s selon la
// longueur, en pause au survol) puis s'efface ; un clic la ferme.
import { useCallback, useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { MessageCircle } from "lucide-react"
import { Riche } from "./texte"

export function useBulleJules(accueil: string) {
  const [texte, setTexte] = useState<string | null>(accueil)
  const [cle, setCle] = useState(0)
  const dire = useCallback((t: string) => { setTexte(t); setCle((k) => k + 1) }, [])
  const fermer = useCallback(() => setTexte(null), [])
  return { texte, cle, dire, fermer }
}

export function BulleJules({ texte, cle, fermer, lienDiscuter }: {
  texte: string | null; cle: number; fermer: () => void; lienDiscuter?: string
}) {
  const minuterie = useRef<number | undefined>(undefined)
  const armer = useCallback(() => {
    window.clearTimeout(minuterie.current)
    if (texte) minuterie.current = window.setTimeout(fermer, Math.min(20000, 6000 + 60 * texte.length))
  }, [texte, fermer])
  useEffect(() => { armer(); return () => window.clearTimeout(minuterie.current) }, [armer, cle])

  return (
    <div className="flex items-end gap-3">
      <motion.img src="/api/persona/avatar" alt="Jules" className="size-12 shrink-0 rounded-full border-4 border-white bg-bleu-clair object-cover shadow-relief-haut"
        animate={texte ? { rotate: [0, -8, 6, 0] } : { rotate: 0 }} transition={{ duration: 0.6 }} key={`a${cle}`} />
      <div className="min-w-0 flex-1">
        <AnimatePresence mode="wait">
          {texte ? (
            <motion.div key={cle} role="status" title="Clique pour fermer"
              initial={{ opacity: 0, y: 12, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6, scale: 0.98 }}
              transition={{ type: "spring", stiffness: 380, damping: 30 }}
              onClick={fermer} onMouseEnter={() => window.clearTimeout(minuterie.current)} onMouseLeave={armer}
              className="bulle-jules relative cursor-pointer rounded-3xl rounded-bl-md bg-bleu px-4 py-3 text-[0.97rem] leading-relaxed text-white shadow-relief-haut [&_.cle]:bg-white/20">
              <Riche texte={texte} />
            </motion.div>
          ) : lienDiscuter ? (
            <motion.a key="discuter" href={lienDiscuter} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="inline-flex items-center gap-2 rounded-full border border-bord bg-white px-4 py-2 text-[0.95rem] font-semibold text-bleu shadow-relief hover:bg-bleu-clair">
              <MessageCircle size={16} /> Poser une question à Jules
            </motion.a>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  )
}
