// Presets d'animation (framer-motion) : le seul endroit où vivent les durées et les courbes des écrans.
// `useMotion()` rend des props à étaler sur un composant `motion.*` ; tout est vide si l'élève a demandé
// moins de mouvement (prefers-reduced-motion), l'élément s'affiche alors directement dans son état final.
import { useReducedMotion, type MotionProps } from "framer-motion"

const COURBE = [0.2, 0.8, 0.2, 1] as const

/** Apparition courte (bulle de Jules, message) : fondu + 6 px, 180 ms. */
const apparition: MotionProps = { initial: { opacity: 0, y: 6 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.18, ease: "easeOut" } }
/** Changement d'écran (App.tsx, un seul endroit) : l'apparition, un peu plus ample (8 px), et une sortie brève. */
const page: MotionProps = {
  initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -4 },
  transition: { duration: 0.22, ease: COURBE },
}
/** Entrée d'un bloc quand il arrive à l'écran (leçon, fiche, carte de liste). */
const entree: MotionProps = {
  initial: { opacity: 0, y: 12 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-40px" },
  transition: { duration: 0.3, ease: COURBE },
}
/** Retour tactile : la surface s'enfonce un peu sous le doigt. */
const tap: MotionProps = { whileTap: { scale: 0.97 } }

const AUCUN = { apparition: {}, page: {}, entree: {}, tap: {} } as const satisfies Record<string, MotionProps>

export function useMotion(): Record<keyof typeof AUCUN, MotionProps> {
  return useReducedMotion() ? AUCUN : { apparition, page, entree, tap }
}

/** « Jules écrit… » : trois points qui sautent l'un après l'autre (i = 0, 1, 2) ; immobiles si moins de mouvement. */
export function usePoint(): (i: number) => MotionProps {
  const reduit = useReducedMotion()
  return (i) => reduit ? {} : {
    animate: { y: [0, -4, 0], opacity: [0.45, 1, 0.45] },
    transition: { duration: 0.9, repeat: Infinity, ease: "easeInOut", delay: i * 0.15 },
  }
}
