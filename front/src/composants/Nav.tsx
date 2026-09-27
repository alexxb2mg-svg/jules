// Barre latérale : entièrement pilotée par config/navigation.ts.
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { NAV, MARQUE, type SectionId } from "@/config/navigation"

export function Nav({ actif, onChange, eleve }: {
  actif: SectionId; onChange: (s: SectionId) => void; eleve: { prenom: string; classe: string }
}) {
  const haut = NAV.filter((e) => e.groupe !== "bas")
  const bas = NAV.filter((e) => e.groupe === "bas")

  const Entree = ({ id, nom, Icone, bientot }: (typeof NAV)[number]) => {
    const estActif = actif === id
    return (
      <button key={id} onClick={() => !bientot && onChange(id)} aria-current={estActif ? "page" : undefined}
        className={cn("relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-left font-medium transition-colors",
          estActif ? "text-white" : bientot ? "text-gris/70" : "text-encre hover:bg-[#ECEAF6]")}>
        {estActif && (
          <motion.span layoutId="nav-actif" className="absolute inset-0 rounded-xl bg-bleu shadow-relief"
            transition={{ type: "spring", stiffness: 500, damping: 40 }} />
        )}
        <Icone size={20} className="relative z-10" />
        <span className="relative z-10">{nom}</span>
        {bientot && <span className="relative z-10 ml-auto rounded-md bg-[#E7E4F3] px-1.5 text-[11px] font-semibold text-gris">bientôt</span>}
      </button>
    )
  }

  return (
    <aside className="flex h-full w-[232px] shrink-0 flex-col gap-1 border-r border-bord bg-nav px-3 py-5">
      <div className="mb-4 px-3 font-titre text-[26px] font-bold text-bleu">{MARQUE.nom}<span className="text-rouge">{MARQUE.point}</span></div>
      {haut.map(Entree)}
      {bas.length > 0 && <div className="my-3 h-px bg-bord" />}
      {bas.map(Entree)}
      <div className="mt-auto flex items-center gap-3 px-3 py-2 text-[15px] text-gris">
        <span className="grid size-8 place-items-center rounded-full bg-bleu font-titre font-bold text-white">{eleve.prenom[0]}</span>
        <span><b className="block text-encre">{eleve.prenom}</b>{eleve.classe}</span>
      </div>
    </aside>
  )
}
