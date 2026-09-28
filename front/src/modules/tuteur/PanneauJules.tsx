// Panneau « Jules » : chat assistant-ui branché sur une conversation réelle du serveur.
// assistant-ui gère l'affichage, le défilement, la saisie, le markdown et les formules ;
// nous ne fournissons que l'adaptateur (useExternalStoreRuntime) vers /api/conversations.
import { useCallback, useEffect, useState } from "react"
import {
  AssistantRuntimeProvider, ComposerPrimitive, MessagePrimitive, ThreadPrimitive,
  useExternalStoreRuntime, type AppendMessage, type ThreadMessageLike,
} from "@assistant-ui/react"
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"
import { ArrowUp, MessageCircleQuestion } from "lucide-react"
import { motion } from "framer-motion"
import { conversations, type MessageJules } from "@/api/jules"

export type AideRapide = { libelle: string; message: string }
/** J : parties du contenu affiché que Jules peut citer (titre exact → id du bloc à illuminer). */
export type Ancre = { titre: string; cible: string }

/** Notes techniques écrites par le module cours dans la conversation : utiles au modèle, pas à l'élève. */
const NOTE_INTERNE = /^\[Correction automatique\]/
/** « 📝 Ma réponse (bloc 6) : -3 » → « Ma réponse : -3 » (le numéro de bloc est interne). */
const nettoyer = (t: string) => t.replace(/^📝 Ma réponse \(bloc \d+\) :/, "📝 Ma réponse :")

const convertir = (m: MessageJules, i: number): ThreadMessageLike => ({
  id: `${i}`,
  role: m.role === "eleve" ? "user" : "assistant",
  content: [{ type: "text", text: nettoyer(m.texte) }],
})

export function PanneauJules({ conversationId, sousTitre, aides = [], suggestions = [], ancres = [], rafraichir = 0 }: {
  conversationId: string
  sousTitre?: string
  aides?: AideRapide[]
  /** Questions proposées tant que la conversation est vide (tirées du contenu affiché, jamais générées). */
  suggestions?: AideRapide[]
  /** Titres de parties : quand la réponse de Jules en cite un, il devient un lien vers le bloc. */
  ancres?: Ancre[]
  /** Incrémenter pour relire la conversation (ex. après une réponse corrigée côté exercice). */
  rafraichir?: number
}) {
  const [messages, setMessages] = useState<MessageJules[]>([])
  const [enCours, setEnCours] = useState(false)

  useEffect(() => {
    conversations.lire(conversationId)
      .then((c) => setMessages(c.messages.filter((m) => !NOTE_INTERNE.test(m.texte))))
      .catch(() => setMessages([]))
  }, [conversationId, rafraichir])

  const envoyer = useCallback(async (texte: string) => {
    setMessages((m) => [...m, { role: "eleve", texte }])
    setEnCours(true)
    try {
      const r = await conversations.envoyer(conversationId, texte)
      setMessages((m) => [...m, { role: "jules", texte: r.reponse, horodatage: r.horodatage }])
    } catch (e) {
      setMessages((m) => [...m, { role: "jules", texte: `Oups, je n'ai pas pu répondre (${(e as Error).message}). Réessaie dans un instant.` }])
    } finally {
      setEnCours(false)
    }
  }, [conversationId])

  const lier = useCallback((t: string) => lierCitations(t, ancres), [ancres])
  const runtime = useExternalStoreRuntime({
    messages,
    isRunning: enCours,
    convertMessage: (m: MessageJules, i: number) => (m.role === "eleve" ? convertir(m, i) : convertir({ ...m, texte: lier(m.texte) }, i)),
    onNew: async (m: AppendMessage) => {
      const texte = m.content.map((p) => (p.type === "text" ? p.text : "")).join("").trim()
      if (texte) await envoyer(texte)
    },
  })

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex h-full flex-col bg-nav">
        <div className="flex items-center gap-3 border-b border-bord px-5 py-3.5">
          <img src="/api/persona/avatar" alt="" className="size-9 rounded-full bg-bleu" onError={(e) => (e.currentTarget.style.display = "none")} />
          <div className="leading-tight">
            <b className="font-titre text-[17px]">Jules</b>
            {sousTitre && <small className="block text-[13px] text-gris">{sousTitre}</small>}
          </div>
        </div>

        <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col">
          <ThreadPrimitive.Viewport className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4">
            <ThreadPrimitive.Empty>
              <div className="m-auto flex max-w-[320px] flex-col items-center gap-4 text-center text-[15px] text-gris">
                <p className="m-0">Je suis là si tu bloques. Je ne te donne pas la réponse, mais je t'aide à la trouver.</p>
                {suggestions.length > 0 && (
                  <div className="flex w-full flex-col gap-2">
                    {suggestions.map((s, i) => (
                      <ThreadPrimitive.Suggestion key={s.libelle} prompt={s.message} send asChild>
                        <motion.button initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 * i }}
                          className="flex items-center gap-2 rounded-2xl border border-bord bg-white px-3.5 py-2.5 text-left text-[14px] font-medium text-encre shadow-relief transition-colors hover:border-bleu hover:text-bleu">
                          <MessageCircleQuestion size={16} className="shrink-0 text-bleu" /> <span className="line-clamp-2">{s.libelle}</span>
                        </motion.button>
                      </ThreadPrimitive.Suggestion>
                    ))}
                  </div>
                )}
              </div>
            </ThreadPrimitive.Empty>
            <ThreadPrimitive.Messages components={{ UserMessage: MessageEleve, AssistantMessage: MessageJulesBulle }} />
            <ThreadPrimitive.If running>
              <div className="flex gap-1 self-start rounded-2xl rounded-bl-md bg-bleu-clair px-4 py-3">
                {[0, 1, 2].map((i) => <span key={i} className="size-2 animate-bounce rounded-full bg-bleu/60" style={{ animationDelay: `${i * 120}ms` }} />)}
              </div>
            </ThreadPrimitive.If>
          </ThreadPrimitive.Viewport>

          {aides.length > 0 && (
            <div className="flex flex-wrap gap-1.5 px-3 pb-2">
              {aides.map((a) => (
                <ThreadPrimitive.Suggestion key={a.libelle} prompt={a.message} send
                  className="rounded-full border border-bord bg-white px-3 py-1 text-[13px] font-medium transition-colors hover:border-bleu hover:text-bleu">
                  {a.libelle}
                </ThreadPrimitive.Suggestion>
              ))}
            </div>
          )}

          <ComposerPrimitive.Root className="m-3 mt-0 flex items-end gap-2 rounded-2xl border-2 border-bord bg-white p-2 focus-within:border-bleu">
            <ComposerPrimitive.Input placeholder="Écris à Jules…" rows={1} autoFocus={false}
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-[16px] outline-none placeholder:text-gris" />
            <ComposerPrimitive.Send className="grid size-9 place-items-center rounded-xl bg-bleu text-white transition-opacity disabled:opacity-40" aria-label="Envoyer">
              <ArrowUp size={18} />
            </ComposerPrimitive.Send>
          </ComposerPrimitive.Root>
        </ThreadPrimitive.Root>
      </div>
    </AssistantRuntimeProvider>
  )
}

function MessageEleve() {
  return (
    <MessagePrimitive.Root className="max-w-[88%] self-end rounded-2xl rounded-br-md bg-bleu px-4 py-2.5 text-[16px] text-white">
      <MessagePrimitive.Parts />
    </MessagePrimitive.Root>
  )
}

/** Remplace, dans une réponse de Jules, la première mention de chaque titre de partie par un lien #cible:<id>
 *  (sans toucher aux formules ni aux liens déjà présents). Le lien illumine le bloc au lieu de naviguer. */
function lierCitations(texte: string, ancres: Ancre[]): string {
  let t = texte
  for (const a of [...ancres].sort((x, y) => y.titre.length - x.titre.length)) {
    if (a.titre.length < 6) continue
    const echappe = a.titre.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    const motif = new RegExp(`(^|[^\\[$\\w])(${echappe})(?![\\w\\]])`, "i")
    t = t.replace(motif, (_m, avant: string, titre: string) => `${avant}[${titre}](#cible:${a.cible})`)
  }
  return t
}

/** Clic sur une citation : défile jusqu'au bloc et le fait briller un instant. */
function allerALaCitation(cible: string) {
  const el = document.getElementById(cible)
  if (!el) return
  el.scrollIntoView({ behavior: "smooth", block: "center" })
  el.classList.remove("jules-cite"); void el.offsetWidth; el.classList.add("jules-cite")
  setTimeout(() => el.classList.remove("jules-cite"), 2700)
}

function Lien({ href, children, ...reste }: React.AnchorHTMLAttributes<HTMLAnchorElement>) {
  if (href?.startsWith("#cible:")) {
    const cible = href.slice(7)
    return (
      <a href={`#${cible}`} role="button" onClick={(e) => { e.preventDefault(); allerALaCitation(cible) }} title="Voir ce passage"
        className="rounded bg-white/70 px-0.5 font-semibold text-bleu underline decoration-bleu/40 decoration-2 underline-offset-2 [box-decoration-break:clone] hover:decoration-bleu">
        {children}
      </a>
    )
  }
  return <a href={href} {...reste} target="_blank" rel="noreferrer">{children}</a>
}

function Markdown() {
  return <MarkdownTextPrimitive remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]} components={{ a: Lien }}
    className="prose-jules [&_p]:my-1 [&_strong]:font-semibold [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5" />
}

function MessageJulesBulle() {
  return (
    <MessagePrimitive.Root className="max-w-[92%] self-start rounded-2xl rounded-bl-md bg-bleu-clair px-4 py-2.5 text-[16px] leading-relaxed">
      <MessagePrimitive.Parts components={{ Text: Markdown }} />
    </MessagePrimitive.Root>
  )
}
