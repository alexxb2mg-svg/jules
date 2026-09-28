// Registre des sections de Jules : la nav, le routage et les écrans en découlent.
// Rubriques et libellés = tests/navigation-reference.json (référence SPEC, EX-202). Ne pas les renommer ici
// sans changer la référence. Ajouter une section = une entrée ici + un écran dans ecrans/registre.tsx.
import type { LucideIcon } from "lucide-react"
import { BookOpen, GraduationCap, Dumbbell, MessageCircle, Users, ClipboardList } from "lucide-react"

export type SectionId = "fiches" | "lecons" | "supports" | "discuter" | "parent" | "pronote"

export type EntreeNav = {
  id: SectionId
  nom: string
  Icone: LucideIcon
  /** Écran pas encore porté dans la nouvelle interface : lien vers la page existante du serveur. */
  pageExistante?: string
}

export type Rubrique = { titre: string; entrees: EntreeNav[] }

export const NAV_ARIA = "Sections de Jules"

export const RUBRIQUES: Rubrique[] = [
  { titre: "Apprendre", entrees: [
    { id: "fiches", nom: "Mes fiches", Icone: BookOpen },
    { id: "lecons", nom: "Mes leçons", Icone: GraduationCap },
  ] },
  { titre: "M'entraîner", entrees: [
    { id: "supports", nom: "Exercices et supports", Icone: Dumbbell },
  ] },
  { titre: "Discuter", entrees: [
    { id: "discuter", nom: "Discuter avec Jules", Icone: MessageCircle, pageExistante: "/discuter" },
  ] },
  { titre: "Mon espace", entrees: [
    { id: "parent", nom: "Espace parent", Icone: Users, pageExistante: "/parent" },
    { id: "pronote", nom: "Pronote", Icone: ClipboardList },
  ] },
]

export const SECTIONS = RUBRIQUES.flatMap((r) => r.entrees)
export const SECTION_ACCUEIL: SectionId = "fiches"

export const MARQUE = { nom: "Jules", point: "." }
