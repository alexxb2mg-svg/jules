// Routage par fragment (#/…) : liens profonds, favoris, bouton retour du navigateur. Aucune dépendance.
//   #/fiches                 bibliothèque des fiches     #/fiches/<matiere>   chapitres d'une matière
//   #/fiche/<notion>         une fiche visuelle
//   #/lecons                 leçons                      #/lecons/<matiere>   leçons d'une matière
//   #/lecon/<notion>[/<bloc>] une leçon (écran partagé leçon | Jules)
//   #/supports[/<matiere>]   studio                      #/support/<matiere>/<id>  un support ouvert
//   #/revision               révision des cartes mémoire
//   #/ajouter                ajouter mon cours (sources personnelles, docs/SOURCES-CONTRAT.md)
//   #/perso/<id>             une fiche personnelle    #/dossier/<id>|non-classe  un dossier perso
//   #/bilan                  mon bilan (en verbes, points forts d'abord)
import { useEffect, useRef, useState } from "react"
import { SECTION_ACCUEIL, type SectionId } from "@/config/navigation"
import { gardeActive, quitter } from "@/modules/sources/etat"

export type Route =
  | { ecran: "fiches"; matiere: string | null }
  | { ecran: "fiche"; notion: string }
  | { ecran: "lecons"; matiere: string | null }
  | { ecran: "lecon"; notion: string }
  | { ecran: "supports"; matiere: string | null }
  | { ecran: "support"; matiere: string; id: string }
  | { ecran: "revision" }
  | { ecran: "ajouter" }
  | { ecran: "perso"; id: string }
  | { ecran: "dossier"; id: string }
  | { ecran: "bilan" }
  | { ecran: "pronote" }
  | { ecran: "parent" }

const ID = "([a-z0-9][a-z0-9-]*)"

export function lireRoute(hash = window.location.hash): Route {
  let m
  if ((m = hash.match(new RegExp(`^#/fiche/${ID}`)))) return { ecran: "fiche", notion: m[1] }
  if ((m = hash.match(new RegExp(`^#/lecon/${ID}`)))) return { ecran: "lecon", notion: m[1] }
  if ((m = hash.match(new RegExp(`^#/support/${ID}/${ID}`)))) return { ecran: "support", matiere: m[1], id: m[2] }
  if ((m = hash.match(new RegExp(`^#/supports(?:/${ID})?/?$`)))) return { ecran: "supports", matiere: m[1] || null }
  if (/^#\/revision\/?$/.test(hash)) return { ecran: "revision" }
  if (/^#\/ajouter\/?$/.test(hash)) return { ecran: "ajouter" }
  if (/^#\/bilan\/?$/.test(hash)) return { ecran: "bilan" }
  if (/^#\/pronote\/?$/.test(hash)) return { ecran: "pronote" }
  if (/^#\/parent\/?$/.test(hash)) return { ecran: "parent" }
  if ((m = hash.match(new RegExp(`^#/perso/${ID}`)))) return { ecran: "perso", id: m[1] }
  if ((m = hash.match(new RegExp(`^#/dossier/${ID}`)))) return { ecran: "dossier", id: m[1] }
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
    case "ajouter": return "#/ajouter"
    case "perso": return `#/perso/${r.id}`
    case "dossier": return `#/dossier/${r.id}`
    case "bilan": return "#/bilan"
    case "pronote": return "#/pronote"
    case "parent": return "#/parent"
  }
}

/** Section de la nav allumée pour une route. */
export const sectionDe = (r: Route): SectionId =>
  r.ecran === "fiche" || r.ecran === "fiches" || r.ecran === "ajouter" || r.ecran === "perso" || r.ecran === "dossier" ? "fiches"
    : r.ecran === "supports" || r.ecran === "support" || r.ecran === "revision" || r.ecran === "bilan" ? "supports"
    : r.ecran === "pronote" ? "pronote" : r.ecran === "parent" ? "parent" : "lecons"

export function useRoute(): [Route, (r: Route) => void] {
  const [route, setRoute] = useState<Route>(() => lireRoute())
  const hashCourant = useRef(window.location.hash)
  useEffect(() => {
    const suivre = () => {
      const cible = window.location.hash
      if (cible === hashCourant.current) return
      if (gardeActive()) {
        // Retour du navigateur ou lien depuis une fiche à ranger : on revient d'abord, la question est posée,
        // puis on part vers la cible si l'élève a répondu (docs/SOURCES-CONTRAT.md §7).
        history.pushState(null, "", hashCourant.current || "#/")
        quitter(() => { hashCourant.current = cible; history.pushState(null, "", cible); setRoute(lireRoute(cible)) })
        return
      }
      hashCourant.current = cible
      setRoute(lireRoute(cible))
    }
    addEventListener("hashchange", suivre)
    return () => removeEventListener("hashchange", suivre)
  }, [])
  const aller = (r: Route) => quitter(() => {
    const h = ecrireRoute(r)
    hashCourant.current = h
    if (window.location.hash !== h) history.pushState(null, "", h)
    setRoute(r)
  })
  return [route, aller]
}
