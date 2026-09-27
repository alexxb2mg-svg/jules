// Registre des écrans : une section de la nav → un composant. Les écrans non faits affichent un gabarit.
import type { SectionId } from "@/config/navigation"
import type { Lancement } from "@/composants/Parcours"
import { Accueil } from "@/ecrans/Accueil"

export type PropsEcran = { onLancer: (l: Lancement) => void }

function AVenir({ nom }: { nom: string }) {
  return <div className="grid h-full place-items-center text-gris">Maquette « {nom} » à venir</div>
}

export const ECRANS: Record<SectionId, (p: PropsEcran) => React.JSX.Element> = {
  accueil: Accueil,
  devoir: () => <AVenir nom="Mes devoirs" />,
  reviser: () => <AVenir nom="Réviser" />,
  exercices: () => <AVenir nom="M'entraîner" />,
  brevet: () => <AVenir nom="Brevet" />,
  discuter: () => <AVenir nom="Parler à Jules" />,
  parent: () => <AVenir nom="Espace parent" />,
}
