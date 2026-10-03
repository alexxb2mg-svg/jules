// Magasin d'état mémorisé sur l'appareil (localStorage) ET synchronisé avec le serveur (module « synchro »).
// Le localStorage donne l'affichage immédiat ; le serveur est la source commune à tous les appareils
// (téléphone, PC, tunnel sont des origines différentes : sans lui, chacun aurait sa propre mémoire).
import { synchro } from "@/api/jules"

type Serveur<T> = { cle: string; fusion?: (local: T, distant: T) => T }
type Participant = { charger: (distant: Record<string, unknown>) => void }
const participants: Participant[] = []

export function magasin<T>(cle: string | null, initial: T, serveur?: Serveur<T>) {
  let valeur: T = initial
  if (cle) { try { const v = localStorage.getItem(cle); if (v) valeur = JSON.parse(v) } catch { /* stockage indisponible */ } }
  const abonnes = new Set<() => void>()
  const garder = (v: T) => {
    valeur = v
    if (cle) { try { localStorage.setItem(cle, JSON.stringify(v)) } catch { /* stockage indisponible */ } }
    abonnes.forEach((f) => f())
  }
  const m = {
    lire: () => valeur,
    ecrire: (v: T) => {
      garder(v)
      if (serveur) synchro.ecrire(serveur.cle, v).catch(() => { /* hors ligne ou non connecté : le local suffit, la prochaine synchro rattrape */ })
    },
    abonner: (f: () => void) => { abonnes.add(f); return () => { abonnes.delete(f) } },
  }
  if (serveur) {
    participants.push({
      charger: (distant) => {
        if (!(serveur.cle in distant)) {  // le serveur ne connaît pas encore cette clé : il reçoit l'état de cet appareil
          if (JSON.stringify(valeur) !== JSON.stringify(initial)) synchro.ecrire(serveur.cle, valeur).catch(() => {})
          return
        }
        const d = distant[serveur.cle] as T
        const retenu = serveur.fusion ? serveur.fusion(valeur, d) : d
        if (JSON.stringify(retenu) !== JSON.stringify(valeur)) garder(retenu)
        // fusion qui a ajouté du local que le serveur ignore : le lui renvoyer
        if (serveur.fusion && JSON.stringify(retenu) !== JSON.stringify(d)) synchro.ecrire(serveur.cle, retenu).catch(() => {})
      },
    })
  }
  return m
}

/** Récupère l'état du serveur et l'applique à tous les magasins synchronisés (échec silencieux : hors ligne, pas connecté). */
export async function synchroniser(): Promise<void> {
  try {
    const distant = await synchro.etat()
    participants.forEach((p) => p.charger(distant))
  } catch { /* pas de réseau ou pas de session : on garde l'état local */ }
}
