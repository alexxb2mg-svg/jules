/**
 * Planificateur de révisions espacées (FSRS via ts-fsrs).
 * Fonctions pures, sans React : testables unitairement.
 */
import { Rating, State, createEmptyCard, fsrs } from "ts-fsrs"
import type { Card, Grade } from "ts-fsrs"
import type { CarteFlash, PaquetFlash } from "./types"

export type EtatCarte = Card
export type EtatsPaquet = Record<string, EtatCarte>
export type NoteFlash = Grade

export const NOTES = {
  pasSu: Rating.Again as Grade,
  difficile: Rating.Hard as Grade,
  su: Rating.Good as Grade,
  facile: Rating.Easy as Grade,
} as const

export const ORDRE_NOTES: readonly NoteFlash[] = [NOTES.pasSu, NOTES.difficile, NOTES.su, NOTES.facile]

const planificateur = fsrs({ enable_fuzz: false })

export const cleStockage = (paquetId: string) => `jules.flashcards.${paquetId}`

/** État d'une carte : celui enregistré, ou une carte neuve (due tout de suite). */
export function etatDe(etats: EtatsPaquet, carteId: string, maintenant: Date = new Date()): EtatCarte {
  return etats[carteId] ?? createEmptyCard(maintenant)
}

/** Cartes du paquet à revoir maintenant (neuves comprises), les plus en retard d'abord. */
export function cartesDues(paquet: PaquetFlash, etats: EtatsPaquet, maintenant: Date = new Date()): CarteFlash[] {
  return paquet.cartes
    .map((carte, rang) => ({ carte, rang, etat: etats[carte.id] }))
    .filter(({ etat }) => !etat || etat.due.getTime() <= maintenant.getTime())
    .sort((a, b) => {
      const da = a.etat ? a.etat.due.getTime() : Number.POSITIVE_INFINITY
      const db = b.etat ? b.etat.due.getTime() : Number.POSITIVE_INFINITY
      return da === db ? a.rang - b.rang : da - db
    })
    .map(({ carte }) => carte)
}

/** Nouvel état de la carte après la note donnée. */
export function noter(etat: EtatCarte, note: NoteFlash, maintenant: Date = new Date()): EtatCarte {
  return planificateur.next(etat, maintenant, note).card
}

/** Date de prochaine révision pour chacune des 4 notes possibles. */
export function apercu(etat: EtatCarte, maintenant: Date = new Date()): Record<NoteFlash, Date> {
  const log = planificateur.repeat(etat, maintenant)
  return {
    [Rating.Again]: log[Rating.Again].card.due,
    [Rating.Hard]: log[Rating.Hard].card.due,
    [Rating.Good]: log[Rating.Good].card.due,
    [Rating.Easy]: log[Rating.Easy].card.due,
  } as Record<NoteFlash, Date>
}

/** Prochaine échéance parmi les cartes du paquet (null si une carte n'a jamais été vue). */
export function prochaineEcheance(paquet: PaquetFlash, etats: EtatsPaquet): Date | null {
  let min: Date | null = null
  for (const carte of paquet.cartes) {
    const etat = etats[carte.id]
    if (!etat) return null
    if (!min || etat.due < min) min = etat.due
  }
  return min
}

/** « dans 10 min », « dans 3 j »… */
export function formaterIntervalle(de: Date, a: Date): string {
  const minutes = Math.max(1, Math.round((a.getTime() - de.getTime()) / 60_000))
  if (minutes < 60) return `dans ${minutes} min`
  const heures = Math.round(minutes / 60)
  if (heures < 24) return `dans ${heures} h`
  const jours = Math.round(heures / 24)
  if (jours < 31) return `dans ${jours} j`
  const mois = Math.round(jours / 30)
  if (mois < 12) return `dans ${mois} mois`
  const ans = Math.round(jours / 365)
  return `dans ${ans} an${ans > 1 ? "s" : ""}`
}

export function formaterDate(date: Date): string {
  return date.toLocaleString("fr-FR", { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" })
}

/* ---------- Persistance (JSON, dates en ISO) ---------- */

type EtatSerialise = Omit<Card, "due" | "last_review"> & { due: string; last_review?: string }

export function serialiser(etats: EtatsPaquet): string {
  const sortie: Record<string, EtatSerialise> = {}
  for (const [id, e] of Object.entries(etats)) {
    sortie[id] = { ...e, due: e.due.toISOString(), last_review: e.last_review?.toISOString() }
  }
  return JSON.stringify(sortie)
}

export function deserialiser(texte: string | null): EtatsPaquet {
  if (!texte) return {}
  try {
    const brut = JSON.parse(texte) as Record<string, EtatSerialise>
    const etats: EtatsPaquet = {}
    for (const [id, e] of Object.entries(brut)) {
      const due = new Date(e.due)
      if (Number.isNaN(due.getTime())) continue
      etats[id] = {
        ...e,
        state: (e.state ?? State.New) as State,
        due,
        last_review: e.last_review ? new Date(e.last_review) : undefined,
      }
    }
    return etats
  } catch {
    return {}
  }
}

function stockage(): Storage | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage
  } catch {
    return null
  }
}

export function chargerEtats(paquetId: string): EtatsPaquet {
  return deserialiser(stockage()?.getItem(cleStockage(paquetId)) ?? null)
}

export function sauverEtats(paquetId: string, etats: EtatsPaquet): void {
  try {
    stockage()?.setItem(cleStockage(paquetId), serialiser(etats))
  } catch {
    /* quota plein ou stockage interdit : on continue sans persistance */
  }
}

export function effacerEtats(paquetId: string): void {
  stockage()?.removeItem(cleStockage(paquetId))
}
