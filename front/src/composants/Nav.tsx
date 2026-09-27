import { motion } from "framer-motion"
import { BookOpen, Home, MessageCircle, PenLine, ClipboardCheck, Users, Layers } from "lucide-react"
import { cn } from "@/lib/utils"
import { ELEVE } from "@/donnees"

export type Section = "accueil" | "devoir" | "reviser" | "exercices" | "brevet" | "discuter" | "parent"

const ENTREES: { id: Section; nom: string; Icone: typeof Home; bientot?: boolean }[] = [
  { id: "accueil", nom: "Accueil", Icone: Home },
  { id: "devoir", nom: "Mes devoirs", Icone: PenLine },
  { id: "reviser", nom: "Réviser", Icone: BookOpen },
  { id: "exercices", nom: "M'entraîner", Icone: Layers },
  { id: "brevet", nom: "Brevet", Icone: ClipboardCheck, bientot: true },
  { id: "discuter", nom: "Parler à Jules", Icone: MessageCircle },
]

export function Nav({ actif, onChange }: { actif: Section; onChange: (s: Section) => void }) {
  return (
    <aside className="flex h-full w-[232px] shrink-0 flex-col gap-1 border-r border-bord bg-nav px-3 py-5">
      <div className="mb-4 px-3 font-titre text-[26px] font-bold text-bleu">
        Jules<span className="text-rouge">.</span>
      </div>

      {ENTREES.map(({ id, nom, Icone, bientot }) => {
        const estActif = actif === id
        return (
          <button
            key={id}
            onClick={() => !bientot && onChange(id)}
            className={cn(
              "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-left font-medium transition-colors",
              estActif ? "text-white" : bientot ? "text-gris/70" : "text-encre hover:bg-[#ECEAF6]",
            )}
          >
            {estActif && (
              <motion.span
                layoutId="nav-actif"
                className="absolute inset-0 rounded-xl bg-bleu shadow-relief"
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
              />
            )}
            <Icone size={20} className="relative z-10" />
            <span className="relative z-10">{nom}</span>
            {bientot && <span className="relative z-10 ml-auto rounded-md bg-[#E7E4F3] px-1.5 text-[11px] font-semibold text-gris">bientôt</span>}
          </button>
        )
      })}

      <div className="my-3 h-px bg-bord" />

      <button
        onClick={() => onChange("parent")}
        className={cn(
          "flex items-center gap-3 rounded-xl px-3 py-2.5 text-left font-medium transition-colors",
          actif === "parent" ? "bg-encre text-white" : "text-gris hover:bg-[#ECEAF6]",
        )}
      >
        <Users size={20} />
        Espace parent
      </button>

      <div className="mt-auto flex items-center gap-3 px-3 py-2 text-[15px] text-gris">
        <span className="grid size-8 place-items-center rounded-full bg-bleu font-titre font-bold text-white">
          {ELEVE.prenom[0]}
        </span>
        <span>
          <b className="block text-encre">{ELEVE.prenom}</b>
          {ELEVE.classe}
        </span>
      </div>
    </aside>
  )
}
