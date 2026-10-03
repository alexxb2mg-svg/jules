// A : matière courante, partagée par tous les écrans et mémorisée. null = toutes les matières.
// E : étapes faites par notion (lire la fiche, leçon, entraînement), mémorisées sur l'appareil ET synchronisées
//     avec le serveur (module « synchro ») pour suivre l'élève d'un appareil à l'autre ;
//     les cartes mémoire, elles, viennent du serveur (studio).
import { useSyncExternalStore } from "react"
import { magasin } from "@/lib/magasin"

const matiere = magasin<string | null>("jules.matiere", null, { cle: "matiere" })
export const useMatiere = () => useSyncExternalStore(matiere.abonner, matiere.lire)
export const lireMatiere = matiere.lire
export function choisirMatiere(m: string | null) { if (m !== matiere.lire()) matiere.ecrire(m) }

export type Etape = "fiche" | "lecon" | "exercices"
const ORDRE: Etape[] = ["fiche", "lecon", "exercices"]
/** Union par notion : une étape faite sur un appareil n'est jamais perdue à cause d'un autre appareil. */
function fusionEtapes(a: Record<string, Etape[]>, b: Record<string, Etape[]>): Record<string, Etape[]> {
  const out: Record<string, Etape[]> = {}
  for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const vues = new Set([...(a[n] ?? []), ...(b[n] ?? [])])
    out[n] = ORDRE.filter((e) => vues.has(e))
  }
  return out
}
const etapes = magasin<Record<string, Etape[]>>("jules.etapes", {}, { cle: "etapes", fusion: fusionEtapes })
export const useEtapes = (notion: string) => useSyncExternalStore(etapes.abonner, () => etapes.lire()[notion] ?? VIDE)
const VIDE: Etape[] = []
export function marquerEtape(notion: string, e: Etape) {
  const tout = etapes.lire()
  if ((tout[notion] ?? []).includes(e)) return
  etapes.ecrire({ ...tout, [notion]: [...(tout[notion] ?? []), e] })
}
