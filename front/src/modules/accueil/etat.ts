// A : matière courante, partagée par tous les écrans et mémorisée. null = toutes les matières.
// E : étapes faites par notion (lire la fiche, leçon, entraînement), mémorisées sur l'appareil ;
//     les cartes mémoire, elles, viennent du serveur (studio).
import { useSyncExternalStore } from "react"

function magasin<T>(cle: string, initial: T) {
  let valeur: T = initial
  try { const v = localStorage.getItem(cle); if (v) valeur = JSON.parse(v) } catch { /* stockage indisponible */ }
  const abonnes = new Set<() => void>()
  return {
    lire: () => valeur,
    ecrire: (v: T) => {
      valeur = v
      try { localStorage.setItem(cle, JSON.stringify(v)) } catch { /* stockage indisponible */ }
      abonnes.forEach((f) => f())
    },
    abonner: (f: () => void) => { abonnes.add(f); return () => { abonnes.delete(f) } },
  }
}

const matiere = magasin<string | null>("jules.matiere", null)
export const useMatiere = () => useSyncExternalStore(matiere.abonner, matiere.lire)
export const lireMatiere = matiere.lire
export function choisirMatiere(m: string | null) { if (m !== matiere.lire()) matiere.ecrire(m) }

export type Etape = "fiche" | "lecon" | "exercices"
const etapes = magasin<Record<string, Etape[]>>("jules.etapes", {})
export const useEtapes = (notion: string) => useSyncExternalStore(etapes.abonner, () => etapes.lire()[notion] ?? VIDE)
const VIDE: Etape[] = []
export function marquerEtape(notion: string, e: Etape) {
  const tout = etapes.lire()
  if ((tout[notion] ?? []).includes(e)) return
  etapes.ecrire({ ...tout, [notion]: [...(tout[notion] ?? []), e] })
}
