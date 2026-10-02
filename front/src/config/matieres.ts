// Habillage des matières : icône seulement. Nom, couleurs (matieres-couleurs.css) et contenu viennent du serveur.
// Une matière absente d'ici garde l'icône par défaut : rien à changer pour en ajouter une côté serveur.
import type { LucideIcon } from "lucide-react"
import { Atom, BookOpenText, Brush, Calculator, Cpu, Globe2, Landmark, Languages, Leaf, Music, Palette, Scale, Library } from "lucide-react"

export const ICONES_MATIERES: Record<string, LucideIcon> = {
  mathematiques: Calculator,
  francais: BookOpenText,
  histoire: Landmark,
  geographie: Globe2,
  "physique-chimie": Atom,
  svt: Leaf,
  technologie: Cpu,
  "arts-plastiques": Palette,
  anglais: Languages,
  "education-musicale": Music,
  "histoire-des-arts": Brush,
  emc: Scale,
}
export const iconeMatiere = (id: string): LucideIcon => ICONES_MATIERES[id] || Library

/** Ordre d'affichage des matières dans la bibliothèque (les autres suivent, par ordre du serveur). */
export const ORDRE_MATIERES = [
  "mathematiques", "francais", "histoire", "geographie", "physique-chimie", "svt",
  "technologie", "anglais", "emc", "arts-plastiques", "education-musicale", "histoire-des-arts",
]
