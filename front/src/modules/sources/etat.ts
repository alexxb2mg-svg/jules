// État partagé des sources personnelles, sans dépendance : filtre natif/perso (mémorisé), fiches ouvertes
// récemment (barre latérale), garde « on la garde ? » (contrat §7), rafraîchissement de la bibliothèque perso.
import { useSyncExternalStore } from "react"
import { sources, type BibliothequePerso } from "@/api/jules"
import type { Filtre } from "@/config/sources"

/** Identifiant du dossier fixe « Non classé » (jules/sources.py NON_CLASSE). */
export const NON_CLASSE = "non-classe"

function magasin<T>(cle: string | null, initial: T) {
  let valeur: T = initial
  if (cle) { try { const v = localStorage.getItem(cle); if (v) valeur = JSON.parse(v) } catch { /* stockage indisponible */ } }
  const abonnes = new Set<() => void>()
  return {
    lire: () => valeur,
    ecrire: (v: T) => {
      valeur = v
      if (cle) { try { localStorage.setItem(cle, JSON.stringify(v)) } catch { /* stockage indisponible */ } }
      abonnes.forEach((f) => f())
    },
    abonner: (f: () => void) => { abonnes.add(f); return () => { abonnes.delete(f) } },
  }
}

/* ---- filtre ---- */
const filtre = magasin<Filtre>("jules.filtre-fiches", "toutes")
export const useFiltre = (): [Filtre, (f: Filtre) => void] => [useSyncExternalStore(filtre.abonner, filtre.lire), filtre.ecrire]

/* ---- ouvertes récemment ---- */
export type Recente = { genre: "native" | "perso"; id: string; titre: string; matiere: string }
const recentes = magasin<Recente[]>("jules.fiches-recentes", [])
export const useRecentes = () => useSyncExternalStore(recentes.abonner, recentes.lire)
export function noterOuverture(r: Recente) {
  recentes.ecrire([r, ...recentes.lire().filter((x) => !(x.genre === r.genre && x.id === r.id))].slice(0, 6))
}
export function oublierRecente(id: string) {
  recentes.ecrire(recentes.lire().filter((x) => !(x.genre === "perso" && x.id === id)))
}

/* ---- bibliothèque personnelle (une requête partagée, rechargée après chaque changement) ---- */
const biblio = magasin<BibliothequePerso | null>(null, null)
let enCours: Promise<void> | null = null
export function rechargerPerso(): Promise<void> {
  enCours = sources.bibliotheque().then(biblio.ecrire).catch(() => {}).finally(() => { enCours = null })
  return enCours
}
export function useBibliothequePerso(): BibliothequePerso | null {
  const v = useSyncExternalStore(biblio.abonner, biblio.lire)
  if (v === null && !enCours) rechargerPerso()
  return v
}

/* ---- garde « on la garde ? » : consultée avant de quitter une fiche à ranger ---- */
export type Garde = (continuer: () => void) => void
let garde: Garde | null = null
export const poserGarde = (g: Garde | null) => { garde = g }
/** Navigue, sauf si une fiche à ranger est ouverte : la question est posée d'abord. */
export function quitter(continuer: () => void) {
  if (garde) garde(continuer)
  else continuer()
}
export const gardeActive = () => garde !== null
