// Markdown léger pour les bulles du chat. Même stack que PanneauJules
// (react-markdown + remark-gfm + remark-math + rehype-katex).
// Un bloc ```figure (JSON {gabarit, valeurs}, déjà vérifié par le serveur : jules/modules/figures.py) est dessiné
// à sa place dans le texte ; illisible, il ne s'affiche pas. Lot 3 : la figure est DYNAMIQUE, comme dans les fiches
// (même composant Graphe) : un curseur par valeur, bornes déclarées par l'extension (/api/infos → figures),
// départ = valeurs choisies par Jules. Sans bornes connues (infos pas encore lues), la figure reste fixe.
// Un bloc ```figure {"schema": id} (schéma de la fiche visuelle de la notion, vérifié par le même module) est
// rendu par SchemaNotion (même rendu que dans la fiche : importNode, bouton Agrandir, feuille claire en sombre).

import { createContext, useContext, useMemo } from "react"
import Markdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"
import type { BornesFigures } from "@/api/jules"
import { FigureGabarit, Graphe, SchemaNotion } from "@/modules/fiches/blocs"
import type { BlocGraphe } from "@/modules/fiches/types"

/** Bornes des curseurs, fournies par l'écran de discussion (Chat.tsx) et par l'écran de la leçon (EcranPartage.tsx)
 *  depuis /api/infos. */
export const BornesFiguresContexte = createContext<BornesFigures | undefined>(undefined)

const borner = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v))

type FigureLue = { gabarit: string; valeurs: Record<string, number> } | { schema: string }

/** Aussi utilisée par le panneau de la leçon (PanneauJules : bloc ```figure de MarkdownTextPrimitive). */
export function FigureBulle({ source }: { source: string }) {
  const bornes = useContext(BornesFiguresContexte)
  const figure = useMemo((): FigureLue | null => {
    try {
      const o = JSON.parse(source)
      if (typeof o?.schema === "string" && /^[a-z0-9][a-z0-9-]*$/.test(o.schema)) return { schema: o.schema }
      return typeof o?.gabarit === "string" && o.valeurs && typeof o.valeurs === "object" ? (o as { gabarit: string; valeurs: Record<string, number> }) : null
    } catch { return null }
  }, [source])
  const gabarit = figure && "gabarit" in figure ? figure : null
  const declarees = gabarit ? bornes?.[gabarit.gabarit] : undefined
  const bloc = useMemo<BlocGraphe | null>(() => {
    if (!gabarit || !declarees || !Object.keys(declarees).length) return null
    return {
      type: "graphe", id: "figure-bulle", adresse: "figure-bulle", gabarit: gabarit.gabarit, lectures: [],
      curseurs: Object.entries(declarees).map(([nom, b]) => {
        const v = Number(gabarit.valeurs[nom])
        return { id: nom, nom, min: b.min, max: b.max, pas: b.pas, depart: borner(Number.isFinite(v) ? v : b.defaut, b.min, b.max) }
      }),
    }
  }, [gabarit, declarees])
  if (!figure) return null
  if ("schema" in figure) return <SchemaNotion notion={figure.schema} className="my-2" />
  const nom = figure.gabarit.replaceAll("-", " ")
  if (!bloc) return <FigureGabarit gabarit={figure.gabarit} valeurs={figure.valeurs} libelle={`Figure : ${nom}`} className="my-2 w-[340px] max-w-full" />
  // key : une autre figure (autre source) repart des valeurs de Jules au lieu de garder celles de l'élève.
  // Largeur explicite : la bulle s'ajuste à son contenu, et un conteneur @container (inline-size) n'a pas de largeur
  // propre ; sans elle, la bulle se replie sur le texte et la figure tombe à ~75 px. 340 px au plus, la bulle sinon.
  return (
    <div role="group" aria-label={`Figure ${nom}, à faire bouger avec les curseurs`} data-figure-bulle className="my-2 w-[340px] max-w-full">
      <Graphe key={source} bloc={bloc} libelle={`Figure : ${nom}`} classeFigure="" />
    </div>
  )
}

// react-markdown 10 : un bloc ```figure donne <pre><code className="language-figure">…</code></pre> ; le nœud hast
// du <pre> porte la classe et le texte du <code>, on remplace donc le <pre> entier.
const composants: Components = {
  pre({ node, children, ...props }) {
    const code = node?.children[0]
    if (code?.type === "element" && code.tagName === "code" && String(code.properties.className) === "language-figure") {
      const texte = code.children[0]
      return <FigureBulle source={texte?.type === "text" ? texte.value : ""} />
    }
    return <pre {...props}>{children}</pre>
  },
}

export function BulleMarkdown({ texte }: { texte: string }) {
  return (
    <div className="prose-jules [&_p]:my-1 [&_strong]:font-semibold [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_table]:text-sm [&_code]:rounded [&_code]:bg-card/60 [&_code]:px-1">
      <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]} components={composants}>
        {texte}
      </Markdown>
    </div>
  )
}
