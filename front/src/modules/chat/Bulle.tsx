// Bulle de conversation : élève à droite (aplat d'encre), Jules à gauche avec son portrait une fois par groupe
// de bulles consécutives. Le texte de Jules est rendu en markdown (même pipeline que PanneauJules).
// Seules les bulles de Jules apparaissent en douceur (lib/motion) ; celles de l'élève sont là tout de suite.
import { memo } from "react"
import { motion } from "framer-motion"
import type { MessageJules } from "@/api/jules"
import { AvatarJules } from "@/components/ui/avatar"
import { bulleVariants } from "@/components/ui/variantes"
import { useMotion, usePoint } from "@/lib/motion"
import { cn } from "@/lib/utils"
import { BulleMarkdown } from "./markdown"

function BullePhoto({ src }: { src: string }) {
  return (
    <img src={src} alt="photo" loading="lazy"
      className="max-h-48 rounded-xl object-cover" />
  )
}

/** Colonne du portrait : l'avatar sur la première bulle d'un groupe, une place vide ensuite (bulles alignées). */
function Portrait({ visible }: { visible: boolean }) {
  return visible ? <AvatarJules taille="md" className="mt-0.5" /> : <span aria-hidden className="w-10 shrink-0" />
}

export const Bulle = memo(function Bulle({ message, tete = true }: { message: MessageJules; tete?: boolean }) {
  const { apparition } = useMotion()
  const estEleve = message.role === "eleve"
  const images = (message.images ?? []).map((n) =>
    n.startsWith("/") || n.startsWith("http") ? n : `/api/images/${encodeURIComponent(n)}`,
  )

  if (estEleve) {
    return (
      <div className="flex justify-end pl-12">
        <div className={cn(bulleVariants({ auteur: "eleve" }), "max-w-[85%] sm:max-w-[70%]")}>
          {images.length > 0 && <div className="mb-1.5 flex flex-wrap gap-1.5">{images.map((s) => <BullePhoto key={s} src={s} />)}</div>}
          <p className="m-0 whitespace-pre-line">{message.texte}</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div {...apparition} className="flex items-start gap-2.5">
      <Portrait visible={tete} />
      <div className={cn(bulleVariants({ auteur: "jules", tete }), "bulle-jules max-w-[85%] sm:max-w-[70%]")}>
        {images.length > 0 && <div className="mb-1.5 flex flex-wrap gap-1.5">{images.map((s) => <BullePhoto key={s} src={s} />)}</div>}
        <BulleMarkdown texte={message.texte} />
      </div>
    </motion.div>
  )
})

/** Pendant l'attente : « Jules écrit… » et trois points animés (lib/motion, immobiles si moins de mouvement). */
export function BulleAttente({ tete = true }: { tete?: boolean }) {
  const { apparition } = useMotion()
  const point = usePoint()
  return (
    <motion.div {...apparition} className="flex items-start gap-2.5" role="status">
      <Portrait visible={tete} />
      <div className={cn(bulleVariants({ auteur: "jules", tete }), "flex items-center gap-2.5 py-3")}>
        <span className="text-courant text-bleu">Jules écrit</span>
        <span aria-hidden className="flex gap-1">
          {[0, 1, 2].map((i) => <motion.span key={i} {...point(i)} className="size-2 rounded-full bg-bleu" />)}
        </span>
      </div>
    </motion.div>
  )
}
