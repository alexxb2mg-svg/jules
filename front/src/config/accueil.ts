// Contenu de l'accueil : textes, grandes cartes d'intention, suggestions.
// Tout est modifiable ici sans toucher aux composants.
import type { LucideIcon } from "lucide-react"
import { PenLine, BookOpen, Clock, AlertTriangle } from "lucide-react"
import type { Intention } from "@/config/parcours"

export type CarteIntention = {
  intention: Intention
  titre: string
  sousTitre: string
  action: string
  Icone: LucideIcon
  /** Classe Tailwind de couleur de fond (bg-*), voir les tokens dans index.css. */
  couleur: string
}

export const ACCUEIL = {
  /** {salut} et {prenom} sont remplacés à l'affichage. */
  bienvenue: "{salut} {prenom} 👋",
  question: "On fait quoi aujourd'hui ?",
  salutations: { matin: "Bonjour", aprem: "Salut", soir: "Bonsoir" },
  titreSuggestions: "Jules te propose",

  intentions: [
    { intention: "devoir", titre: "J'ai un devoir", sousTitre: "Jules t'aide à le faire toi-même, étape par étape.", action: "C'est parti", Icone: PenLine, couleur: "bg-bleu" },
    { intention: "reviser", titre: "Je révise", sousTitre: "Une fiche, puis des exercices corrigés tout de suite.", action: "C'est parti", Icone: BookOpen, couleur: "bg-francais" },
  ] satisfies CarteIntention[],

  /** Types de suggestion que Jules peut afficher ; la donnée vient du suivi de l'élève. */
  typesSuggestion: {
    reprendre: { badge: "Reprendre", Icone: Clock, teinte: "bleu" as const },
    consolider: { badge: "À consolider", Icone: AlertTriangle, teinte: "orange" as const },
  },
}
