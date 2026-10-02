// Ponts vers l'infrastructure commune de Jules, chargée par index.html comme dans les anciennes pages :
//   /static/symboles.js puis /rappels.js (bulles de rappel au survol, extensions « rappels ») ;
//   /gabarits.js (figures des blocs graphe/exemple, extensions « figures »).
// Le front ne réimplémente ni les figures ni les rappels : il les appelle.

type Gabarit = { dessiner: (svg: SVGSVGElement, valeurs: Record<string, number>) => void }
type Rappels = { matiere?: string | null; variables?: Record<string, string>; abreviations?: Record<string, string> }

declare global {
  interface Window { GABARITS?: Record<string, Gabarit> }
}
// symboles.js déclare `const Symboles` au niveau global d'un script classique : visible comme identifiant
// global, mais pas comme propriété de window.
declare const Symboles: { contexte: (racine: Element, rappels: Rappels) => void } | undefined

export function dessinerGabarit(svg: SVGSVGElement | null, nom: string, valeurs: Record<string, number>) {
  const g = window.GABARITS?.[nom]
  if (svg && g) g.dessiner(svg, valeurs)
  return Boolean(g)
}

/** Déclare la zone d'une fiche aux bulles de rappel (matière, lettres des formules, abréviations). */
export function contexteSymboles(racine: Element | null, rappels: Rappels) {
  if (racine && typeof Symboles !== "undefined") Symboles.contexte(racine, rappels)
}

/** Couleurs déclarées dans les fiches (mots français) → couleurs fixes ; inconnue → bleu Jules. */
const COULEURS: Record<string, string> = { bleu: "#1D4E89", orange: "#D9480F", vert: "#2B8A3E", rouge: "#C92A2A", violet: "#7048E8", gris: "#6B7686" }
export const couleurCss = (nom?: string) => (nom && COULEURS[nom]) || "#1D4E89"

/** Évaluateur sûr des conditions « si » des lectures (jamais d'eval) : (var op nombre) (&& …)*. */
export function evaluerCondition(expression: string | undefined, valeurs: Record<string, number>) {
  if (!expression) return false
  return String(expression).split("&&").every((partie) => {
    const m = partie.trim().match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*(<=|>=|==|!=|<|>)\s*(-?\d+(?:\.\d+)?)$/)
    if (!m) return false
    const valeur = valeurs[m[1]], nombre = Number(m[3])
    if (valeur === undefined) return false
    switch (m[2]) {
      case "<": return valeur < nombre
      case "<=": return valeur <= nombre
      case ">": return valeur > nombre
      case ">=": return valeur >= nombre
      case "==": return valeur === nombre
      case "!=": return valeur !== nombre
      default: return false
    }
  })
}

/** Leviers d'adaptation (dys…) : portage exact de MS.appliquerLeviers (commun.js), attributs data-adapt-* et
 *  variables --adapt-* sur <body>, lus par /static/adaptations.css. */
export function appliquerLeviers(infos: { leviers?: unknown; leviers_css?: unknown } | null) {
  const corps = document.body
  for (const nom of [...corps.getAttributeNames()]) if (nom.startsWith("data-adapt-")) corps.removeAttribute(nom)
  for (const nom of [...corps.style]) if (nom.startsWith("--adapt-")) corps.style.removeProperty(nom)
  const objet = (v: unknown): Record<string, unknown> => (v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {})
  for (const [variable, valeur] of Object.entries(objet(infos?.leviers_css))) {
    if (/^--adapt-[a-z-]+$/.test(variable)) corps.style.setProperty(variable, String(valeur))
  }
  for (const [levier, valeur] of Object.entries(objet(infos?.leviers))) {
    if (/^[a-z][a-z-]*$/.test(levier)) corps.setAttribute(`data-adapt-${levier}`, String(valeur))
  }
}
