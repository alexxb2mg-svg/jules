// Jules sur une fiche : bulles préécrites (champ `jules:` des blocs), aucun appel IA (jules_cadrage_interface.md).
// Même règle que accueil.js : une seule bulle à la fois ; elle reste le temps de la lire (6 à 20 s selon la
// longueur, en pause au survol) puis s'efface ; un clic la ferme.
import { useCallback, useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { MessageCircle } from "lucide-react"
import { Riche } from "./texte"
import { avatarVariants } from "@/components/ui/variantes"
import { buttonVariants } from "@/components/ui/button"
import { bulleVariants } from "@/components/ui/variantes"
import { cn } from "@/lib/utils"

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
      <motion.img src="/api/persona/avatar" alt="Jules" className={avatarVariants({ taille: "lg", className: "object-cover ring-4 ring-card shadow-souleve" })}
        animate={texte ? { rotate: [0, -8, 6, 0] } : { rotate: 0 }} transition={{ duration: 0.6 }} key={`a${cle}`} />
      <div className="min-w-0 flex-1">
        <AnimatePresence mode="wait">
          {texte ? (
            <motion.div key={cle} role="status" title="Clique pour fermer"
              initial={{ opacity: 0, y: 12, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6, scale: 0.98 }}
              transition={{ type: "spring", stiffness: 380, damping: 30 }}
              onClick={fermer} onMouseEnter={() => window.clearTimeout(minuterie.current)} onMouseLeave={armer}
              className={cn(bulleVariants({ auteur: "jules", tete: false }), "bulle-jules relative cursor-pointer rounded-bl-md bg-bleu text-white shadow-souleve [&_.cle]:bg-white/20")}>
              <Riche texte={texte} />
            </motion.div>
          ) : lienDiscuter ? (
            <motion.a key="discuter" href={lienDiscuter} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className={buttonVariants({ variant: "sombre", size: "pastille", className: "text-bleu shadow-souleve hover:bg-bleu-clair" })}>
              <MessageCircle size={16} /> Poser une question à Jules
            </motion.a>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  )
}
