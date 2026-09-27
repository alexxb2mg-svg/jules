// Routage par fragment (#/…) : liens profonds, favoris, bouton retour du navigateur. Aucune dépendance.
//   #/fiches                 bibliothèque des fiches     #/fiches/<matiere>   chapitres d'une matière
//   #/fiche/<notion>         une fiche visuelle
//   #/lecons                 leçons                      #/lecons/<matiere>   leçons d'une matière
//   #/lecon/<notion>[/<bloc>] une leçon (écran partagé leçon | Jules)
//   #/supports[/<matiere>]   studio                      #/support/<matiere>/<id>  un support ouvert
//   #/revision               révision des cartes mémoire
import { useEffect, useState } from "react"
import { SECTION_ACCUEIL, type SectionId } from "@/config/navigation"

export type Route =
  | { ecran: "fiches"; matiere: string | null }
  | { ecran: "fiche"; notion: string }
  | { ecran: "lecons"; matiere: string | null }
  | { ecran: "lecon"; notion: string }
  | { ecran: "supports"; matiere: string | null }
  | { ecran: "support"; matiere: string; id: string }
  | { ecran: "revision" }

const ID = "([a-z0-9][a-z0-9-]*)"

export function lireRoute(hash = window.location.hash): Route {
  let m
  if ((m = hash.match(new RegExp(`^#/fiche/${ID}`)))) return { ecran: "fiche", notion: m[1] }
  if ((m = hash.match(new RegExp(`^#/lecon/${ID}`)))) return { ecran: "lecon", notion: m[1] }
  if ((m = hash.match(new RegExp(`^#/support/${ID}/${ID}`)))) return { ecran: "support", matiere: m[1], id: m[2] }
  if ((m = hash.match(new RegExp(`^#/supports(?:/${ID})?/?$`)))) return { ecran: "supports", matiere: m[1] || null }
  if (/^#\/revision\/?$/.test(hash)) return { ecran: "revision" }
  if ((m = hash.match(new RegExp(`^#/lecons(?:/${ID})?/?$`)))) return { ecran: "lecons", matiere: m[1] || null }
  if ((m = hash.match(new RegExp(`^#/fiches(?:/${ID})?/?$`)))) return { ecran: "fiches", matiere: m[1] || null }
  return SECTION_ACCUEIL === "fiches" ? { ecran: "fiches", matiere: null } : { ecran: "lecons", matiere: null }
}

export function ecrireRoute(r: Route): string {
  switch (r.ecran) {
    case "fiche": return `#/fiche/${r.notion}`
    case "lecon": return `#/lecon/${r.notion}`
    case "lecons": return r.matiere ? `#/lecons/${r.matiere}` : "#/lecons"
    case "fiches": return r.matiere ? `#/fiches/${r.matiere}` : "#/fiches"
    case "supports": return r.matiere ? `#/supports/${r.matiere}` : "#/supports"
    case "support": return `#/support/${r.matiere}/${r.id}`
    case "revision": return "#/revision"
  }
}

/** Section de la nav allumée pour une route. */
export const sectionDe = (r: Route): SectionId =>
  r.ecran === "fiche" || r.ecran === "fiches" ? "fiches"
    : r.ecran === "supports" || r.ecran === "support" || r.ecran === "revision" ? "supports" : "lecons"

export function useRoute(): [Route, (r: Route) => void] {
  const [route, setRoute] = useState<Route>(() => lireRoute())
  useEffect(() => {
    const suivre = () => setRoute(lireRoute())
    addEventListener("hashchange", suivre)
    return () => removeEventListener("hashchange", suivre)
  }, [])
  const aller = (r: Route) => {
    const h = ecrireRoute(r)
    if (window.location.hash !== h) window.location.hash = h
    else setRoute(r)
  }
  return [route, aller]
}
