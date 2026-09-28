// Registre des écrans : un type de route (routes.ts) → un composant. Ajouter un écran = une route + une entrée ici.
import type { Infos } from "@/api/jules"
import type { Route } from "@/routes"
import { Bibliotheque } from "@/modules/fiches/Bibliotheque"
import { FicheVisuelle } from "@/modules/fiches/FicheVisuelle"
import { Lecons } from "@/ecrans/Lecons"
import { EcranPartage } from "@/ecrans/EcranPartage"
import { Studio } from "@/modules/studio/Studio"
import { EditeurSupport } from "@/modules/studio/EditeurSupport"
import { Revision } from "@/modules/studio/Revision"
import { AjouterCours } from "@/modules/sources/AjouterCours"
import { FichePersonnelle } from "@/modules/sources/FichePersonnelle"
import { EcranDossier } from "@/modules/sources/pieces"
import { FichesPersoDeLaNotion } from "@/modules/sources/FichesPersoDeLaNotion"
import { noterOuverture } from "@/modules/sources/etat"
import { choisirMatiere } from "@/modules/accueil/etat"

export type PropsEcran = { route: Route; aller: (r: Route) => void; infos: Infos | null }
type Ecran = (p: PropsEcran) => React.JSX.Element | null

export const ECRANS: Record<Route["ecran"], Ecran> = {
  fiches: ({ route, aller }) => route.ecran !== "fiches" ? null : (
    <div className="h-full overflow-y-auto">
      <Bibliotheque matiere={route.matiere}
        onMatiere={(m) => aller({ ecran: "fiches", matiere: m })}
        onOuvrir={(n) => aller({ ecran: "fiche", notion: n })}
        onOuvrirPerso={(id) => aller({ ecran: "perso", id })}
        onAjouter={() => aller({ ecran: "ajouter" })}
        onDossier={(id) => aller({ ecran: "dossier", id })}
        onReviser={() => aller({ ecran: "revision" })} />
    </div>
  ),
  fiche: ({ route, aller }) => route.ecran !== "fiche" ? null : (
    <FicheVisuelle notion={route.notion} retour="Mes fiches"
      onRetour={() => history.length > 1 ? history.back() : aller({ ecran: "fiches", matiere: null })}
      onOuvrirLecon={(n) => aller({ ecran: "lecon", notion: n })}
      onChargee={(f) => { noterOuverture({ genre: "native", id: route.notion, titre: f.titre, matiere: f.matiere }); choisirMatiere(f.matiere) }}
      onCartes={(m) => aller({ ecran: "supports", matiere: m })}
      suite={<FichesPersoDeLaNotion notion={route.notion} onOuvrir={(id) => aller({ ecran: "perso", id })} />} />
  ),
  lecons: ({ route, aller }) => route.ecran !== "lecons" ? null : (
    <div className="h-full overflow-y-auto">
      <Lecons matiere={route.matiere}
        onMatiere={(m) => aller({ ecran: "lecons", matiere: m })}
        onLecon={(n) => aller({ ecran: "lecon", notion: n })}
        onFiche={(n) => aller({ ecran: "fiche", notion: n })} />
    </div>
  ),
  lecon: ({ route, aller }) => route.ecran !== "lecon" ? null : (
    <EcranPartage notion={route.notion} fil="Mes leçons"
      onRetour={() => history.length > 1 ? history.back() : aller({ ecran: "lecons", matiere: null })} />
  ),
  supports: ({ route, aller }) => route.ecran !== "supports" ? null : (
    <div className="h-full overflow-y-auto">
      <Studio matiere={route.matiere}
        onMatiere={(m) => aller({ ecran: "supports", matiere: m })}
        onOuvrir={(id, m) => aller({ ecran: "support", matiere: m, id })}
        onReviser={() => aller({ ecran: "revision" })} />
    </div>
  ),
  support: ({ route, aller }) => route.ecran !== "support" ? null : (
    <EditeurSupport id={route.id} matiere={route.matiere}
      onRetour={() => aller({ ecran: "supports", matiere: route.matiere })}
      onSupprime={() => aller({ ecran: "supports", matiere: route.matiere })} />
  ),
  revision: ({ aller }) => <Revision onRetour={() => aller({ ecran: "supports", matiere: null })} />,
  ajouter: ({ aller }) => (
    <div className="h-full overflow-y-auto">
      <AjouterCours onRetour={() => aller({ ecran: "fiches", matiere: null })}
        onNatif={() => aller({ ecran: "fiches", matiere: null })}
        onFiche={(id) => aller({ ecran: "perso", id })} />
    </div>
  ),
  perso: ({ route, aller }) => route.ecran !== "perso" ? null : (
    <FichePersonnelle id={route.id}
      onRetour={() => aller({ ecran: "fiches", matiere: null })}
      onOuvrirLecon={(n) => aller({ ecran: "lecon", notion: n })}
      onRegeneree={(id) => aller({ ecran: "perso", id })} />
  ),
  dossier: ({ route, aller }) => route.ecran !== "dossier" ? null : (
    <div className="h-full overflow-y-auto">
      <EcranDossier id={route.id} onRetour={() => aller({ ecran: "fiches", matiere: null })} onOuvrir={(id) => aller({ ecran: "perso", id })} />
    </div>
  ),
}
