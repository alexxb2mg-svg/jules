// Registre des écrans : une section de la nav → un composant. Les écrans non faits affichent un gabarit.
import type { SectionId } from "@/config/navigation"
import type { Lancement } from "@/composants/Parcours"
import { Accueil } from "@/ecrans/Accueil"
import { SessionFlash, PAQUET_EQUATIONS } from "@/modules/flashcards"

export type PropsEcran = { onLancer: (l: Lancement) => void }

function AVenir({ nom }: { nom: string }) {
  return <div className="grid h-full place-items-center text-gris">Maquette « {nom} » à venir</div>
}

function Entrainer() {
  return (
    <div className="mx-auto max-w-[760px] px-10 py-10">
      <p className="mb-2 text-[13px] font-semibold uppercase tracking-wide text-gris">Cartes de révision · Maths</p>
      <SessionFlash paquet={PAQUET_EQUATIONS} />
    </div>
  )
}

export const ECRANS: Record<SectionId, (p: PropsEcran) => React.JSX.Element> = {
  accueil: Accueil,
  devoir: () => <AVenir nom="Mes devoirs" />,
  reviser: () => <AVenir nom="Réviser" />,
  exercices: Entrainer,
  brevet: () => <AVenir nom="Brevet" />,
  discuter: () => <AVenir nom="Parler à Jules" />,
  parent: () => <AVenir nom="Espace parent" />,
}
