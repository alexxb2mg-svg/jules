// Icônes des modes de discussion (consignes/modes/*.md). Le serveur envoie aussi un emoji (`icone`) pour les
// anciennes pages : l'interface React ne l'affiche pas, elle prend l'icône lucide d'ici. Mode inconnu → bulle.
import type { LucideIcon } from "lucide-react"
import { BookOpen, CalendarCheck, Compass, FileText, Lightbulb, MessageCircle, NotebookPen, PenLine, Target, Wrench } from "lucide-react"

export const ICONES_MODES: Record<string, LucideIcon> = {
  "aide-devoirs": PenLine,
  controle: CalendarCheck,
  cours: BookOpen,
  epreuve: Compass,
  exercice: NotebookPen,
  fiche: FileText,
  quiz: Target,
  reexplique: Lightbulb,
  studio: Wrench,
}
export const iconeMode = (id: string): LucideIcon => ICONES_MODES[id] || MessageCircle

/** Suggestions de départ d'une nouvelle discussion (pastilles à toucher), par mode ; mode absent → DEPART. */
const DEPART = ["Je ne comprends pas mon exercice", "Tu peux m'expliquer autrement ?", "Vérifie ce que j'ai fait"]
export const EXEMPLES_MODES: Record<string, string[]> = {
  "aide-devoirs": ["Je ne sais pas par où commencer", "Je t'envoie une photo de mon exercice", "Vérifie ma réponse"],
  controle: ["J'ai un contrôle la semaine prochaine", "Fais-moi réviser un chapitre", "Quels sont les pièges classiques ?"],
  cours: ["Explique-moi la leçon du jour", "Fais-moi un résumé du chapitre", "Donne-moi un exemple simple"],
  quiz: ["Pose-moi 5 questions", "Interroge-moi sur mon dernier chapitre", "Commence facile, puis plus dur"],
  reexplique: ["Réexplique-moi avec un exemple", "Plus simplement, s'il te plaît", "Avec un schéma en mots"],
}
export const exemplesMode = (id: string): string[] => EXEMPLES_MODES[id] || DEPART
