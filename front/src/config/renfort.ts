// Icônes des tuiles « Ensuite, pour ancrer » (bloc renfort des fiches). Les contrats YAML portent un emoji
// (`icone`) pour les anciennes pages ; l'interface React affiche l'icône lucide correspondante, jamais l'emoji.
import type { LucideIcon } from "lucide-react"
import { BookOpen, CircleHelp, Layers, PenLine, Wrench } from "lucide-react"
import type { LienRenfort } from "@/modules/fiches/types"

const PAR_OUTIL: Record<string, LucideIcon> = { lecon: BookOpen }
const PAR_EMOJI: Record<string, LucideIcon> = { "✏️": PenLine, "❓": CircleHelp, "🃏": Layers, "📖": BookOpen }

export const iconeRenfort = (lien: LienRenfort): LucideIcon =>
  PAR_EMOJI[lien.icone ?? ""] || PAR_OUTIL[lien.outil ?? ""] || Wrench
