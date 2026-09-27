// Fil d'Ariane cliquable : chaque cran remonte à l'étape correspondante.
import { motion } from "framer-motion"
import { ChevronLeft } from "lucide-react"
import { cn } from "@/lib/utils"

export type Cran = { libelle: string; onClick?: () => void; actif?: boolean }

export function FilAriane({ crans }: { crans: Cran[] }) {
  return (
    <motion.nav initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
      className="mb-6 flex items-center gap-2 text-[15px] text-gris" aria-label="Fil d'Ariane">
      {crans.map((c, i) => (
        <span key={i} className="flex items-center gap-2">
          {i > 0 && <span>›</span>}
          <button onClick={c.onClick} disabled={!c.onClick}
            className={cn("flex items-center gap-1 rounded-lg px-2 py-1",
              c.onClick ? "hover:bg-[#ECEAF6]" : "cursor-default",
              i === 0 ? "" : c.actif ? "font-semibold text-encre" : "font-semibold text-bleu")}>
            {i === 0 && <ChevronLeft size={16} />}{c.libelle}
          </button>
        </span>
      ))}
    </motion.nav>
  )
}
