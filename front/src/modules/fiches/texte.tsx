// Texte des fiches : portage exact de ecrireRiche() et typo() de jules/web/static/accueil.js.
// Les notions clés sont marquées **ainsi** (contrôle côté serveur) ; jamais de HTML injecté.
import { Fragment } from "react"

/** Typographie française : espace fine insécable devant ? ! : ; » et après «. */
export const typo = (texte?: string) =>
  String(texte || "").replace(/ ([?!:;»])/g, "\u202F$1").replace(/« /g, "«\u202F")

/** Découpe « texte **clé** texte » en morceaux ; l'article élidé (« l'**époque** ») rejoint la clé. */
export function morceauxRiches(texte?: string): { cle: boolean; colle: boolean; texte: string }[] {
  const m = String(texte || "").split(/\*\*(.+?)\*\*/)
  for (let i = 1; i < m.length; i += 2) {
    const elision = m[i - 1].match(/(^|[^\p{L}])(\p{L}{1,3}['’])$/u)
    if (elision) {
      m[i - 1] = m[i - 1].slice(0, m[i - 1].length - elision[2].length)
      m[i] = elision[2] + m[i]
    }
  }
  return m.flatMap((t, i) => {
    if (!t) return []
    // Une partie de mot (« ba-**NA**-na ») : surlignage sans marge, collé aux lettres voisines.
    const colle = i % 2 === 1 && (/[\p{L}\p{N}-]$/u.test(m[i - 1] || "") || /^[\p{L}\p{N}-]/u.test(m[i + 1] || ""))
    return [{ cle: i % 2 === 1, colle, texte: t }]
  })
}

/** Texte riche d'une fiche : <strong class="cle"> pour les notions clés (style dans fiche-contenu.css). */
export function Riche({ texte }: { texte?: string }) {
  return (
    <>
      {morceauxRiches(texte).map((m, i) =>
        m.cle ? <strong key={i} className={m.colle ? "cle colle" : "cle"}>{m.texte}</strong> : <Fragment key={i}>{m.texte}</Fragment>,
      )}
    </>
  )
}
