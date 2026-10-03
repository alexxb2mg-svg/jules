import type { CSSProperties } from "react"

/** Variables CSS de la matière (table SPEC, /static/matieres-couleurs.css) reprises sous --m-*. */
export const styleMatiere = (matiere: string) => ({
  "--m-fond": `var(--matiere-${matiere}-fond, var(--j-bleu-clair))`,
  "--m-texte": `var(--matiere-${matiere}-texte, var(--j-bleu))`,
  "--m-accent": `var(--matiere-${matiere}-accent, var(--j-bleu))`,
}) as CSSProperties
