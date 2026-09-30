// Le studio en données : types de support, statuts, minimums de validation. Recopié du contrat
// (docs/STUDIO-CONTRAT.md §1) et de jules/studio.py (_MINIMUM_ELEMENTS, TAILLE_CHAMP_MAX). Le serveur reste
// seul juge (pret_a_valider) : ceci sert seulement à dire à l'élève ce qui manque AVANT qu'il clique.
import type { LucideIcon } from "lucide-react"
import { BrainCircuit, CircleHelp, FileText, Layers } from "lucide-react"
import type { Support, TypeSupport } from "@/api/jules"

export const TAILLE_CHAMP_MAX = 200

export type DefType = {
  nom: string
  Icone: LucideIcon
  /** Une phrase pour choisir le type (écran de création). */
  pitch: string
  /** Liste du contenu et libellés. */
  liste: "noeuds" | "sections" | "questions" | "cartes"
  ajouter: string
  vide: string
  minimum: number
  manque: (n: number) => string
}

export const TYPES: Record<TypeSupport, DefType> = {
  carte_mentale: {
    nom: "Carte mentale", Icone: BrainCircuit, pitch: "Une idée au centre, des branches autour.",
    liste: "noeuds", ajouter: "Ajouter une idée", vide: "Commence par l'idée du centre : de quoi parle cette notion ?",
    minimum: 3, manque: (n) => `Encore ${n} branche${n > 1 ? "s" : ""} pour pouvoir valider.`,
  },
  fiche: {
    nom: "Fiche", Icone: FileText, pitch: "Des sections avec un titre et ce que tu retiens.",
    liste: "sections", ajouter: "Ajouter une section", vide: "Une section = un titre et ce que tu en retiens, avec tes mots.",
    minimum: 2, manque: (n) => `Encore ${n} section${n > 1 ? "s" : ""} remplie${n > 1 ? "s" : ""} pour pouvoir valider.`,
  },
  quiz: {
    nom: "Quiz", Icone: CircleHelp, pitch: "Tes propres questions, pour te tester plus tard.",
    liste: "questions", ajouter: "Ajouter une question", vide: "C'est toi qui écris les questions et leurs réponses.",
    minimum: 3, manque: (n) => `Encore ${n} question${n > 1 ? "s" : ""} avec réponse pour pouvoir valider.`,
  },
  cartes_memoire: {
    nom: "Cartes mémoire", Icone: Layers, pitch: "Recto, verso : Jules te les ressort au bon moment.",
    liste: "cartes", ajouter: "Ajouter une carte", vide: "Au recto une question ou un mot, au verso ce qu'il faut retrouver.",
    minimum: 4, manque: (n) => `Encore ${n} carte${n > 1 ? "s" : ""} (recto et verso) pour pouvoir valider.`,
  },
}
export const ORDRE_TYPES: TypeSupport[] = ["fiche", "carte_mentale", "quiz", "cartes_memoire"]

export const STATUTS: Record<string, { texte: string; classe: string }> = {
  brouillon: { texte: "Brouillon", classe: "bg-nav text-gris" },
  relu: { texte: "Relu par Jules", classe: "bg-bleu-clair text-bleu" },
  valide: { texte: "Validé", classe: "bg-succes-fond text-succes" },
}

/** Éléments qui comptent pour la validation (même règle que jules/studio.py _verifier_nombre_elements). */
export function elementsComptes(s: Support): number {
  const c = s.contenu
  switch (s.type) {
    case "carte_mentale": return (c.noeuds || []).filter((n) => n.texte.trim()).length
    case "fiche": return (c.sections || []).filter((x) => x.contenu.trim()).length
    case "quiz": return (c.questions || []).filter((q) => q.question.trim() && q.reponse.trim()).length
    case "cartes_memoire": return (c.cartes || []).filter((k) => k.recto.trim() && k.verso.trim()).length
  }
}

export const REPONSES_CARTE = [
  { id: "rate", texte: "Raté", aide: "je la revois demain", classe: "border-erreur-bord bg-erreur-fond text-erreur" },
  { id: "difficile", texte: "Difficile", aide: "même délai", classe: "border-alerte-bord bg-alerte-fond text-alerte" },
  { id: "facile", texte: "Facile", aide: "plus tard", classe: "border-succes-bord bg-succes-fond text-succes" },
] as const
