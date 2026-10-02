// Markdown léger pour les bulles du chat. Même stack que PanneauJules
// (react-markdown + remark-gfm + remark-math + rehype-katex).
// Un bloc ```figure (JSON {gabarit, valeurs}, déjà vérifié par le serveur : jules/modules/figures.py) est dessiné
// par FigureGabarit à sa place dans le texte ; illisible, il ne s'affiche pas.

import { useMemo } from "react"
import Markdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"
import { FigureGabarit } from "@/modules/fiches/blocs"

function FigureBulle({ source }: { source: string }) {
  const figure = useMemo(() => {
    try {
      const o = JSON.parse(source)
      return typeof o?.gabarit === "string" && o.valeurs && typeof o.valeurs === "object" ? (o as { gabarit: string; valeurs: Record<string, number> }) : null
    } catch { return null }
  }, [source])
  if (!figure) return null
  return <FigureGabarit gabarit={figure.gabarit} valeurs={figure.valeurs} libelle={`Figure : ${figure.gabarit.replaceAll("-", " ")}`} className="my-2" />
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
