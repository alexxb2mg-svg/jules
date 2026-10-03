// Recherche des notions (barre latérale) : logique sans rendu. Classement local, route d'ouverture,
// raccourci clavier global. Les données viennent de GET /api/eleve/notions/index (rien n'est fabriqué ici).
import { useEffect } from "react"
import { useSidebar } from "@/components/ui/sidebar"
import { plat } from "@/lib/texte"
import type { NotionRecherche } from "@/api/jules"
import type { Route } from "@/routes"

export const MAX_RESULTATS = 8
export const TEXTES_RECHERCHE = {
  libelle: "Rechercher une notion",
  indication: "Rechercher une notion…",
  aucune: "Aucune notion ne correspond",
  indisponible: "Recherche indisponible pour le moment",
  chargement: "Chargement des notions…",
  fiche: "Fiche",
  lecon: "Leçon",
  raccourci: "Raccourci : / ou Ctrl+K",
}

/** Nom de matière sans la précision entre parenthèses (« Anglais (langue vivante) » → « Anglais »). */
export const nomCourt = (nom: string) => nom.replace(/ \(.*\)$/, "")

/** Notions qui contiennent tous les mots de la requête (titre, chapitre, matière, mots-clés), les meilleures d'abord :
 *  titre qui commence par la requête, puis titre qui la contient, puis le reste (chapitre, mots-clés…). */
export function chercher(notions: NotionRecherche[], requete: string, max = MAX_RESULTATS): NotionRecherche[] {
  const q = plat(requete.trim()).replace(/\s+/g, " ")
  if (!q) return []
  const mots = q.split(" ")
  const notes: { n: NotionRecherche; rang: number; i: number }[] = []
  notions.forEach((n, i) => {
    const titre = plat(n.titre)
    const texte = `${titre} ${plat(n.chapitre)} ${plat(n.nom_matiere)} ${plat(n.mots_cles.join(" "))}`
    if (!mots.every((m) => texte.includes(m))) return
    const rang = titre.startsWith(q) ? 0 : titre.includes(q) ? 1 : mots.every((m) => titre.includes(m)) ? 2 : 3
    notes.push({ n, rang, i })
  })
  return notes.sort((a, b) => a.rang - b.rang || a.i - b.i).slice(0, max).map((x) => x.n)
}

/** Où mène un résultat : la leçon si elle existe, sinon la fiche, sinon les leçons de la matière. */
export const routeDe = (n: NotionRecherche): Route =>
  n.lecon ? { ecran: "lecon", notion: n.id } : n.fiche ? { ecran: "fiche", notion: n.id } : { ecran: "lecons", matiere: n.matiere }

/* ---- mise au point du champ depuis n'importe où (raccourci, loupe de la barre repliée) ---- */

const EVENEMENT = "jules:recherche-focus"
let enAttente = false

/** Le champ prend le focus dès qu'il est visible (il peut être dans un tiroir fermé ou une barre repliée). */
export function demanderFocus() {
  enAttente = true
  dispatchEvent(new Event(EVENEMENT))
}

/** Appelé par le champ : true si une demande de focus attend (et la consomme). */
export function prendreDemande(): boolean {
  const oui = enAttente
  enAttente = false
  return oui
}

export function surDemande(rappel: () => void): () => void {
  addEventListener(EVENEMENT, rappel)
  return () => removeEventListener(EVENEMENT, rappel)
}

const estSaisie = (cible: EventTarget | null) => {
  const el = cible as HTMLElement | null
  if (!el || !el.tagName) return false
  return el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName) || el.getAttribute("role") === "textbox"
}

/** « / » ou Ctrl+K (Cmd+K) : ouvre la barre (ou le tiroir) et met le focus dans la recherche, sauf pendant une saisie.
 *  À appeler dans un composant toujours monté (Nav) : sur téléphone, le champ n'existe pas tiroir fermé. */
export function useRaccourciRecherche() {
  const { isMobile, setOpen, setOpenMobile } = useSidebar()
  useEffect(() => {
    const touche = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.isComposing || estSaisie(e.target)) return
      const barre = e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey
      const ctrlK = (e.ctrlKey || e.metaKey) && !e.altKey && e.key.toLowerCase() === "k"
      if (!barre && !ctrlK) return
      e.preventDefault()
      if (isMobile) setOpenMobile(true)
      else setOpen(true)
      demanderFocus()
    }
    addEventListener("keydown", touche)
    return () => removeEventListener("keydown", touche)
  }, [isMobile, setOpen, setOpenMobile])
}
