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
