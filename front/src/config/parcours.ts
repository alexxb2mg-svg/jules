// Parcours = suite d'étapes de choix avant de lancer une activité.
// Chaque intention déclare ses étapes et ses textes ; le composant Parcours les enchaîne.

export type Intention = "devoir" | "reviser"

export type EtapeId = "matiere" | "chapitre"

export type DefinitionParcours = {
  intention: Intention
  /** Libellé dans le fil d'Ariane. */
  libelle: string
  etapes: { id: EtapeId; question: string }[]
}

export const PARCOURS: Record<Intention, DefinitionParcours> = {
  devoir: {
    intention: "devoir",
    libelle: "Un devoir",
    etapes: [
      { id: "matiere", question: "C'est un devoir de quoi ?" },
      { id: "chapitre", question: "{matiere} · quel chapitre ?" },
    ],
  },
  reviser: {
    intention: "reviser",
    libelle: "Réviser",
    etapes: [
      { id: "matiere", question: "Tu veux réviser quoi ?" },
      { id: "chapitre", question: "{matiere} · quel chapitre ?" },
    ],
  },
}

export const FIL = { racine: "Accueil" }

/** Libellés des états d'un chapitre (issus du suivi). */
export const ETATS = {
  acquis: { libelle: "acquis", teinte: "vert" },
  fragile: { libelle: "à revoir", teinte: "orange" },
  "en-cours": { libelle: "en cours", teinte: "bleu" },
  nouveau: { libelle: "nouveau", teinte: "gris" },
} as const

export type EtatChapitre = keyof typeof ETATS
