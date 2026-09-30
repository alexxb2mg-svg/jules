// Presets d'animation (framer-motion) : le seul endroit où vivent les durées et les courbes des écrans.
// `useMotion()` rend des props à étaler sur un composant `motion.*` ; tout est vide si l'élève a demandé
// moins de mouvement (prefers-reduced-motion), l'élément s'affiche alors directement dans son état final.
import { useReducedMotion, type MotionProps } from "framer-motion"

const COURBE = [0.2, 0.8, 0.2, 1] as const

/** Apparition courte (bulle de Jules, message) : fondu + 6 px, 180 ms. */
const apparition: MotionProps = { initial: { opacity: 0, y: 6 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.18, ease: "easeOut" } }
/** Entrée d'un bloc quand il arrive à l'écran (leçon, fiche, carte de liste). */
const entree: MotionProps = {
  initial: { opacity: 0, y: 12 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-40px" },
  transition: { duration: 0.3, ease: COURBE },
}
/** Retour tactile : la surface s'enfonce un peu sous le doigt. */
const tap: MotionProps = { whileTap: { scale: 0.97 } }

const AUCUN = { apparition: {}, entree: {}, tap: {} } as const satisfies Record<string, MotionProps>

export function useMotion(): Record<keyof typeof AUCUN, MotionProps> {
  return useReducedMotion() ? AUCUN : { apparition, entree, tap }
}
