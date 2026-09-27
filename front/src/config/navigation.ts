// Registre des sections de Jules : la nav, le routage et les écrans en découlent.
// Ajouter une section = ajouter une entrée ici + un écran dans ecrans/registre.tsx.
import type { LucideIcon } from "lucide-react"
import { BookOpen, Home, MessageCircle, PenLine, ClipboardCheck, Users, Layers } from "lucide-react"

export type SectionId = "accueil" | "devoir" | "reviser" | "exercices" | "brevet" | "discuter" | "parent"

export type EntreeNav = {
  id: SectionId
  nom: string
  Icone: LucideIcon
  /** Affiché grisé avec une étiquette, non cliquable. */
  bientot?: boolean
  /** "bas" = groupe secondaire après le séparateur (espace parent). */
  groupe?: "haut" | "bas"
}

export const NAV: EntreeNav[] = [
  { id: "accueil", nom: "Accueil", Icone: Home },
  { id: "devoir", nom: "Mes devoirs", Icone: PenLine },
  { id: "reviser", nom: "Réviser", Icone: BookOpen },
  { id: "exercices", nom: "M'entraîner", Icone: Layers },
  { id: "brevet", nom: "Brevet", Icone: ClipboardCheck, bientot: true },
  { id: "discuter", nom: "Parler à Jules", Icone: MessageCircle },
  { id: "parent", nom: "Espace parent", Icone: Users, groupe: "bas" },
]

export const MARQUE = { nom: "Jules", point: "." }
