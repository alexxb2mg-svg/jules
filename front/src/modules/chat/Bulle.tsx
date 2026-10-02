// Bulle de conversation : élève à droite (bleu), bot à gauche (clair) avec avatar.
// Le texte du bot est rendu en markdown (même pipeline que PanneauJules).
import { memo } from "react"
import type { MessageJules } from "@/api/jules"
import { BulleMarkdown } from "./markdown"

function BullePhoto({ src }: { src: string }) {
  return (
    <img src={src} alt="photo" loading="lazy"
      className="max-h-48 rounded-lg object-cover" />
  )
}

export const Bulle = memo(function Bulle({ message }: { message: MessageJules }) {
  const estEleve = message.role === "eleve"
  const images = (message.images ?? []).map((n) =>
    n.startsWith("/") || n.startsWith("http") ? n : `/api/images/${encodeURIComponent(n)}`,
  )

  if (estEleve) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-bleu px-4 py-2.5 text-[15px] text-white sm:max-w-[70%]">
          {images.length > 0 && <div className="mb-1.5 flex flex-wrap gap-1.5">{images.map((s) => <BullePhoto key={s} src={s} />)}</div>}
          <p className="whitespace-pre-line">{message.texte}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2">
      <img src="/api/persona/avatar" alt="" className="mt-1 size-8 shrink-0 rounded-full bg-bleu-clair"
        onError={(e) => { e.currentTarget.style.display = "none" }} />
      <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-bleu-clair px-4 py-2.5 text-[15px] leading-relaxed sm:max-w-[70%]">
        {images.length > 0 && <div className="mb-1.5 flex flex-wrap gap-1.5">{images.map((s) => <BullePhoto key={s} src={s} />)}</div>}
        <BulleMarkdown texte={message.texte} />
      </div>
    </div>
  )
})

export function BulleAttente() {
  return (
    <div className="flex items-start gap-2">
      <img src="/api/persona/avatar" alt="" className="mt-1 size-8 shrink-0 rounded-full bg-bleu-clair"
        onError={(e) => { e.currentTarget.style.display = "none" }} />
      <div className="flex gap-1 rounded-2xl rounded-bl-md bg-bleu-clair px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span key={i} className="size-2 animate-bounce rounded-full bg-bleu/60"
            style={{ animationDelay: `${i * 120}ms` }} />
        ))}
      </div>
    </div>
  )
}
