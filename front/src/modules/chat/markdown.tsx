// Markdown léger pour les bulles du chat. Même stack que PanneauJules
// (react-markdown + remark-gfm + remark-math + rehype-katex).

import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"

export function BulleMarkdown({ texte }: { texte: string }) {
  return (
    <div className="prose-jules [&_p]:my-1 [&_strong]:font-semibold [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_table]:text-sm [&_code]:rounded [&_code]:bg-white/50 [&_code]:px-1">
      <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
        {texte}
      </Markdown>
    </div>
  )
}
