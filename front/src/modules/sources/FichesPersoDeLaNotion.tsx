// Sous une fiche native : « Mes fiches sur cette notion » (fiches perso rangées dans la notion), contrat §8.
import { Sparkles } from "lucide-react"
import { TEXTES, stylePerso } from "@/config/sources"
import { useBibliothequePerso, useFiltre } from "./etat"
import { TuilePerso, voitPerso } from "./pieces"

export function FichesPersoDeLaNotion({ notion, onOuvrir }: { notion: string; onOuvrir: (id: string) => void }) {
  const biblio = useBibliothequePerso()
  const [filtre] = useFiltre()
  const liste = (biblio?.fiches ?? []).filter((f) => f.etat === "rangee" && f.notion === notion)
  if (!voitPerso(filtre) || liste.length === 0) return null
  return (
    <section data-sans-symboles style={stylePerso} className="rounded-3xl border border-(--m-accent)/25 bg-(--m-fond)/50 p-5">
      <h2 className="mt-0 mb-3 flex items-center gap-2 text-[1.1rem] font-bold text-(--m-texte)"><Sparkles size={18} /> {TEXTES.mesFichesSurNotion}</h2>
      <div className="grid gap-3 md:grid-cols-2">{liste.map((f, i) => <TuilePerso key={f.id} f={f} i={i} onOuvrir={onOuvrir} />)}</div>
    </section>
  )
}
