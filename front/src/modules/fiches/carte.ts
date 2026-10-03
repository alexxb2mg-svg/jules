// Disposition de la carte des notions : portage exact de CONSTRUCTEURS.carte (jules/web/static/accueil.js),
// sous forme de fonction pure (données → positions). Le rendu SVG est dans blocs.tsx.
import type { BlocCarte, NoeudCarte } from "./types"

export const T_TITRE = 16, T_SOUS = 14, T_LIEN = 13, H_TITRE = 20, H_SOUS = 18

/** Texte coupé en lignes selon la largeur de la boîte (un caractère ≈ 0,58 em). */
export function lignes(texte: string | undefined, largeur: number, taille: number): string[] {
  const max = Math.max(8, Math.floor(largeur / (taille * 0.58)))
  const sortie: string[] = []
  let courante = ""
  // Un nombre (« 12 500 ») et la ponctuation haute ne sont jamais séparés du mot voisin.
  const insecable = String(texte || "").replace(/(\d) (?=\d{3}(?!\d))/g, "$1\u202F").replace(/ ([?!:;»])/g, "\u202F$1").replace(/« /g, "«\u202F")
  for (const mot of insecable.split(/[ \t\n]+/).filter(Boolean)) {
    if (courante && (courante + " " + mot).length > max) { sortie.push(courante); courante = mot }
    else courante = courante ? courante + " " + mot : mot
  }
  if (courante) sortie.push(courante)
  return sortie
}

export type Boite = { gauche: number; droite: number; haut: number; bas: number }
export type NoeudPlace = { noeud: NoeudCarte; x: number; y: number; boite: Boite; titre: string[]; sous: string[] }
export type Trait =
  | { forme: "ligne"; x1: number; y1: number; x2: number; y2: number; libelle?: { x: number; y: number; texte: string; ancre: "middle" | "start" } }
  | { forme: "coude"; points: string; libelle?: { x: number; y: number; texte: string; ancre: "middle" | "start" } }

export function disposerCarte(bloc: BlocCarte): { largeur: number; hauteur: number; noeuds: NoeudPlace[]; traits: Trait[] } {
  const noeuds = bloc.noeuds || []
  const secondaires = noeuds.filter((n) => !n.principal)
  // Jusqu'à 4 notions : en éventail sous le nœud principal. Au-delà : principal à gauche, notions en colonne.
  const enColonne = secondaires.length > 4
  const largeur = (n: NoeudCarte) => (enColonne ? (n.principal ? 230 : 380) : n.principal ? 260 : Math.min(220, 860 / Math.max(secondaires.length, 1) - 16))
  const contenu = new Map<string, { titre: string[]; sous: string[]; hauteur: number }>()
  for (const n of noeuds) {
    const l = largeur(n) - 20
    const titre = lignes(n.titre, l, T_TITRE), sous = n.sous_titre ? lignes(n.sous_titre, l, T_SOUS) : []
    contenu.set(n.id, { titre, sous, hauteur: 22 + titre.length * H_TITRE + sous.length * H_SOUS })
  }
  const hMax = Math.max(...secondaires.map((n) => contenu.get(n.id)!.hauteur), 56)
  const positions = new Map<string, { x: number; y: number }>()
  let hauteurTotale: number
  if (enColonne) {
    const pasY = hMax + 18
    hauteurTotale = secondaires.length * pasY + 10
    secondaires.forEach((n, i) => positions.set(n.id, { x: 650, y: 10 + pasY * i + pasY / 2 }))
    noeuds.filter((n) => n.principal).forEach((n) => positions.set(n.id, { x: 125, y: hauteurTotale / 2 }))
  } else {
    const hPrincipal = Math.max(...noeuds.filter((n) => n.principal).map((n) => contenu.get(n.id)!.hauteur), 56)
    const pas = 860 / Math.max(secondaires.length, 1)
    const yBas = hPrincipal + 130 + hMax / 2
    hauteurTotale = yBas + hMax / 2 + 6
    noeuds.filter((n) => n.principal).forEach((n) => positions.set(n.id, { x: 430, y: 4 + hPrincipal / 2 }))
    secondaires.forEach((n, i) => positions.set(n.id, { x: pas * i + pas / 2, y: yBas }))
  }
  // Un lien entre deux notions du même rang fait un coude (sous la ligne, ou à droite de la colonne).
  const principaux = new Set(noeuds.filter((n) => n.principal).map((n) => n.id))
  const liens = bloc.liens || []
  const lateraux = liens.filter((l) => !principaux.has(l.de) && !principaux.has(l.vers) && positions.has(l.de) && positions.has(l.vers))
  const largeurTotale = enColonne && lateraux.length ? 1000 : 860
  if (!enColonne && lateraux.length) hauteurTotale += 22 + 26 * lateraux.length
  const boite = (n: NoeudCarte): Boite => {
    const pos = positions.get(n.id)!, h = n.principal ? contenu.get(n.id)!.hauteur : hMax, w = largeur(n)
    return { gauche: pos.x - w / 2, droite: pos.x + w / 2, haut: pos.y - h / 2, bas: pos.y + h / 2 }
  }
  const traits: Trait[] = []
  for (const lien of liens) {
    const a = noeuds.find((n) => n.id === lien.de), b = noeuds.find((n) => n.id === lien.vers)
    if (!a || !b || !positions.has(a.id) || !positions.has(b.id)) continue
    const pa = positions.get(a.id)!, pb = positions.get(b.id)!, ba = boite(a), bb = boite(b)
    const rang = lateraux.indexOf(lien)
    if (rang >= 0) {
      if (enColonne) {
        const x = ba.droite + 24 + 14 * rang
        traits.push({ forme: "coude", points: `${ba.droite},${pa.y} ${x},${pa.y} ${x},${pb.y} ${bb.droite},${pb.y}`,
          libelle: lien.libelle ? { x: x + 6, y: (pa.y + pb.y) / 2 + 4, texte: lien.libelle, ancre: "start" } : undefined })
      } else {
        const y = Math.max(ba.bas, bb.bas) + 14 + 26 * rang
        traits.push({ forme: "coude", points: `${pa.x},${ba.bas} ${pa.x},${y} ${pb.x},${y} ${pb.x},${bb.bas}`,
          libelle: lien.libelle ? { x: (pa.x + pb.x) / 2, y: y + 16, texte: lien.libelle, ancre: "middle" } : undefined })
      }
      continue
    }
    let x1: number, y1: number, x2: number, y2: number
    if (enColonne || pa.y === pb.y) {
      ;[x1, y1, x2, y2] = pa.x < pb.x ? [ba.droite, pa.y, bb.gauche, pb.y] : [ba.gauche, pa.y, bb.droite, pb.y]
    } else {
      ;[x1, y1, x2, y2] = pa.y < pb.y ? [pa.x, ba.bas, pb.x, bb.haut] : [pa.x, ba.haut, pb.x, bb.bas]
    }
    let libelle: Trait["libelle"]
    if (lien.libelle) {
      // Un peu plus près de l'arrivée ; entre deux boîtes d'une même ligne, au-dessus des boîtes.
      const t = enColonne ? 0.62 : 0.55, memeLigne = !enColonne && pa.y === pb.y
      const yLibelle = memeLigne ? Math.min(ba.haut, bb.haut) - 8 : y1 + (y2 - y1) * t - 6
      libelle = { x: x1 + (x2 - x1) * t, y: yLibelle, texte: lien.libelle, ancre: "middle" }
    }
    traits.push({ forme: "ligne", x1, y1, x2, y2, libelle })
  }
  const places: NoeudPlace[] = noeuds.map((n) => {
    const pos = positions.get(n.id)!, c = contenu.get(n.id)!
    return { noeud: n, x: pos.x, y: pos.y, boite: boite(n), titre: c.titre, sous: c.sous }
  })
  return { largeur: largeurTotale, hauteur: Math.ceil(hauteurTotale), noeuds: places, traits }
}
