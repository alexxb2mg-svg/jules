// Briques d'interface réutilisables. Aucun texte métier ici : tout vient des props.
import type { ReactNode } from "react"
import { motion, type HTMLMotionProps } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import { ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

/** Animation d'entrée/sortie standard d'un écran ou d'une étape. */
export const glisse = {
  initial: { opacity: 0, y: 18, filter: "blur(4px)" },
  animate: { opacity: 1, y: 0, filter: "blur(0px)" },
  exit: { opacity: 0, y: -12, filter: "blur(4px)" },
  transition: { duration: 0.28, ease: [0.2, 0.8, 0.2, 1] as const },
}

/** Apparition en cascade d'un élément de liste (i = index). */
export const cascade = (i: number, axe: "x" | "y" = "y") => ({
  initial: { opacity: 0, [axe]: axe === "y" ? 14 : -10 },
  animate: { opacity: 1, [axe]: 0 },
  transition: { delay: i * 0.04 },
})

/** Carte cliquable avec relief au survol. Base de toutes les cartes de Jules. */
export function CarteBouton({ className, children, ...props }: HTMLMotionProps<"button">) {
  return (
    <motion.button
      whileHover={{ y: -4, boxShadow: "var(--shadow-relief-haut)" }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      className={cn("rounded-2xl border border-bord bg-white text-left shadow-relief", className)}
      {...props}
    >
      {children}
    </motion.button>
  )
}

/** Grande carte d'intention : icône colorée, titre, sous-titre, appel à l'action. */
export function CarteIntention({ Icone, titre, sousTitre, action, couleur, onClick }: {
  Icone: LucideIcon; titre: string; sousTitre: string; action: string; couleur: string; onClick: () => void
}) {
  return (
    <CarteBouton onClick={onClick} className="group relative overflow-hidden rounded-3xl p-7">
      <span className={cn("absolute -top-10 -right-10 size-36 rounded-full opacity-10 transition-transform duration-500 group-hover:scale-150", couleur)} />
      <span className={cn("grid size-14 place-items-center rounded-2xl text-white shadow-relief", couleur)}><Icone size={28} /></span>
      <b className="mt-5 block font-titre text-[26px] font-bold">{titre}</b>
      <span className="mt-1 block text-gris">{sousTitre}</span>
      <span className="mt-5 inline-flex items-center gap-1 font-semibold text-bleu">
        {action} <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
      </span>
    </CarteBouton>
  )
}

/** Ligne de liste : pastille/numéro à gauche, contenu, extrémité droite. */
export function Ligne({ gauche, children, droite, onClick, index = 0, axe = "y" }: {
  gauche?: ReactNode; children: ReactNode; droite?: ReactNode; onClick: () => void; index?: number; axe?: "x" | "y"
}) {
  return (
    <CarteBouton onClick={onClick} className="flex items-center gap-3 px-4 py-3.5" {...cascade(index, axe)}>
      {gauche}
      <span className="flex-1 leading-snug">{children}</span>
      {droite}
    </CarteBouton>
  )
}

export function Numero({ n }: { n: number }) {
  return <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-[#ECEAF6] font-titre font-bold text-bleu">{n}</span>
}

export function Pastille({ couleur, taille = 3 }: { couleur: string; taille?: 3 | 4 }) {
  return <span className={cn("shrink-0 rounded-full", taille === 3 ? "size-3" : "size-4", couleur)} />
}

const TEINTES = {
  bleu: "text-bleu", vert: "text-vert", orange: "text-orange", gris: "text-gris",
} as const
export type Teinte = keyof typeof TEINTES

/** Étiquette d'état (acquis, à revoir…). */
export function Etiquette({ teinte, Icone, children }: { teinte: Teinte; Icone?: LucideIcon; children: ReactNode }) {
  return (
    <span className={cn("flex items-center gap-1 text-[13px]", teinte === "gris" ? "" : "font-semibold", TEINTES[teinte])}>
      {Icone && <Icone size={14} />}{children}
    </span>
  )
}

/** Titre de section discret en capitales. */
export function TitreSection({ children }: { children: ReactNode }) {
  return <h2 className="mt-12 mb-3 text-[15px] font-semibold uppercase tracking-wide text-gris">{children}</h2>
}

export function Titre({ children, avant }: { children: ReactNode; avant?: ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      {avant}
      <h1 className="text-[32px] font-bold leading-tight">{children}</h1>
    </div>
  )
}
