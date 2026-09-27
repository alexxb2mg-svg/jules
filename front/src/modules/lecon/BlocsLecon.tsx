// Rendu d'une leçon bloc par bloc. Un type de bloc = un composant dans RENDUS : en ajouter un ne touche rien d'autre.
// Le juste/faux vient du serveur (verifier_reponse côté Python), jamais du modèle.
import { useState, type ReactNode } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Check, Lightbulb, Target, BookOpenText, PenLine, Sparkles, RotateCcw, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"
import { cours, type Bloc, type EtatBloc, type Progression, type Tentative } from "@/api/jules"

type Ctx = {
  session: string
  etat: EtatBloc
  onProgression: (p: Progression) => void
  /** Signale au panneau Jules qu'il doit relire la conversation (Jules a pu y réagir). */
  onJulesARepondu: () => void
}

/** Mise en forme minimale **gras** des contenus de leçon. */
function Riche({ texte }: { texte: string }) {
  return <>{texte.split(/(\*\*[^*]+\*\*)/g).map((p, i) => p.startsWith("**") ? <strong key={i} className="font-semibold text-encre">{p.slice(2, -2)}</strong> : p)}</>
}

function Cadre({ Icone, etiquette, teinte = "bleu", etat, children }: {
  Icone: typeof Target; etiquette: string; teinte?: "bleu" | "orange" | "vert" | "violet"; etat?: EtatBloc; children: ReactNode
}) {
  const couleurs = {
    bleu: "text-bleu bg-bleu-clair", orange: "text-orange bg-[#FFF3E0]", vert: "text-vert bg-[#E3F4EA]", violet: "text-francais bg-[#F6E9F1]",
  }[teinte]
  const bordure = etat === "reussi" ? "border-vert/50" : etat === "a_revoir" ? "border-orange/60" : "border-bord"
  return (
    <motion.section layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
      className={cn("rounded-2xl border bg-white p-5 shadow-relief transition-colors", bordure)}>
      <div className="mb-3 flex items-center gap-2">
        <span className={cn("grid size-7 place-items-center rounded-lg", couleurs)}><Icone size={16} /></span>
        <span className={cn("text-[13px] font-semibold uppercase tracking-wide", couleurs.split(" ")[0])}>{etiquette}</span>
        {etat === "reussi" && <span className="ml-auto flex items-center gap-1 text-[13px] font-semibold text-vert"><Check size={14} /> réussi</span>}
        {etat === "a_revoir" && <span className="ml-auto flex items-center gap-1 text-[13px] font-semibold text-orange"><AlertTriangle size={14} /> à revoir</span>}
      </div>
      {children}
    </motion.section>
  )
}

/* ---------------- rendus par type ---------------- */

function Objectifs({ bloc }: { bloc: Extract<Bloc, { type: "objectifs" }> }) {
  return (
    <Cadre Icone={Target} etiquette="Ce que tu vas savoir faire">
      <ul className="space-y-1.5">{bloc.items.map((it) => <li key={it} className="flex gap-2"><Check size={18} className="mt-0.5 shrink-0 text-vert" />{it}</li>)}</ul>
    </Cadre>
  )
}

function Texte({ bloc }: { bloc: Extract<Bloc, { type: "texte" }> }) {
  return (
    <Cadre Icone={BookOpenText} etiquette="À retenir" teinte="orange">
      {bloc.titre && <h3 className="mb-2 text-[20px] font-bold">{bloc.titre}</h3>}
      <p className="leading-relaxed text-encre/90"><Riche texte={bloc.contenu} /></p>
    </Cadre>
  )
}

function Exemple({ bloc }: { bloc: Extract<Bloc, { type: "exemple" }> }) {
  const [vues, setVues] = useState(1)
  return (
    <Cadre Icone={Sparkles} etiquette="Exemple guidé" teinte="violet">
      <p className="mb-3 font-semibold">{bloc.enonce}</p>
      <ol className="space-y-2">
        <AnimatePresence initial={false}>
          {bloc.etapes.slice(0, vues).map((e, i) => (
            <motion.li key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} className="flex gap-3">
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-[#F6E9F1] text-[13px] font-bold text-francais">{i + 1}</span>
              <span>{e}</span>
            </motion.li>
          ))}
        </AnimatePresence>
      </ol>
      {vues < bloc.etapes.length && (
        <button onClick={() => setVues(vues + 1)} className="mt-3 rounded-xl border border-bord px-3 py-1.5 text-[14px] font-semibold text-francais hover:bg-[#F6E9F1]">
          Étape suivante
        </button>
      )}
    </Cadre>
  )
}

function Exercice({ bloc, ctx, numero }: { bloc: Extract<Bloc, { type: "exercice" }>; ctx: Ctx; numero: number }) {
  const [reponse, setReponse] = useState("")
  const [retour, setRetour] = useState<Tentative | null>(null)
  const [indices, setIndices] = useState<string[]>([])
  const [restants, setRestants] = useState(bloc.indices?.length ?? 0)
  const [envoi, setEnvoi] = useState(false)
  const fini = ctx.etat === "reussi" || ctx.etat === "a_revoir"

  const valider = async () => {
    if (!reponse.trim() || envoi) return
    setEnvoi(true)
    try {
      const r = await cours.tentative(ctx.session, bloc.index, reponse.trim())
      setRetour(r); ctx.onProgression(r.progression)
      if (r.jules) ctx.onJulesARepondu()
    } finally { setEnvoi(false) }
  }
  const indice = async () => {
    const r = await cours.indice(ctx.session, bloc.index)
    if (r.indice) setIndices((l) => [...l, r.indice!])
    setRestants(r.restants); ctx.onProgression(r.progression)
  }

  return (
    <Cadre Icone={PenLine} etiquette={`Exercice ${numero}`} etat={ctx.etat}>
      <p className="mb-3 text-[18px] font-medium">{bloc.enonce}</p>
      <div className="flex gap-2">
        <input value={reponse} onChange={(e) => setReponse(e.target.value)} onKeyDown={(e) => e.key === "Enter" && valider()}
          disabled={fini} inputMode={bloc.forme === "nombre" ? "decimal" : "text"}
          placeholder={bloc.forme === "nombre" ? "Ta réponse (un nombre)" : "Ta réponse"}
          className="flex-1 rounded-xl border-2 border-bord px-3 py-2 text-[17px] outline-none focus:border-bleu disabled:bg-nav" />
        <button onClick={valider} disabled={fini || envoi || !reponse.trim()}
          className="rounded-xl bg-bleu px-5 font-semibold text-white transition-opacity disabled:opacity-40">Vérifier</button>
      </div>

      <AnimatePresence>
        {retour && (
          <motion.div key={retour.tentatives} initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
            className={cn("mt-3 rounded-xl px-4 py-2.5 text-[15px]",
              retour.juste ? "bg-[#E3F4EA] text-vert" : "bg-[#FFF3E0] text-orange")}>
            <b>{retour.juste ? "Juste !" : ctx.etat === "a_revoir" ? "Pas encore : regarde la correction." : "Pas tout à fait. Jules t'écrit à droite 👉"}</b>
            {retour.explication && <p className="mt-1 text-encre/90">{retour.explication}</p>}
          </motion.div>
        )}
      </AnimatePresence>

      {indices.map((t, i) => (
        <motion.p key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-2 flex gap-2 rounded-xl bg-bleu-clair px-3 py-2 text-[15px]">
          <Lightbulb size={17} className="mt-0.5 shrink-0 text-bleu" />{t}
        </motion.p>
      ))}
      {!fini && restants > 0 && (
        <button onClick={indice} className="mt-2 flex items-center gap-1.5 text-[14px] font-semibold text-bleu hover:underline">
          <Lightbulb size={15} /> Un indice ({restants})
        </button>
      )}
    </Cadre>
  )
}

function Ouverte({ bloc, ctx, consigne, etiquette }: { bloc: Bloc; ctx: Ctx; consigne: string; etiquette: string }) {
  const [texte, setTexte] = useState("")
  const [envoye, setEnvoye] = useState(ctx.etat === "fait")
  const envoyer = async () => {
    if (!texte.trim()) return
    const r = await cours.tentative(ctx.session, bloc.index, texte.trim())
    setEnvoye(true); ctx.onProgression(r.progression); ctx.onJulesARepondu()
  }
  return (
    <Cadre Icone={RotateCcw} etiquette={etiquette} teinte="vert" etat={envoye ? "fait" : ctx.etat}>
      <p className="mb-3 font-medium">{consigne}</p>
      {envoye ? (
        <p className="text-[15px] text-vert">Envoyé : Jules te relit à droite.</p>
      ) : (
        <>
          <textarea value={texte} onChange={(e) => setTexte(e.target.value)} rows={3} placeholder="Avec tes mots…"
            className="w-full resize-y rounded-xl border-2 border-bord px-3 py-2 outline-none focus:border-bleu" />
          <button onClick={envoyer} disabled={!texte.trim()} className="mt-2 rounded-xl bg-vert px-4 py-2 font-semibold text-white disabled:opacity-40">
            Faire relire par Jules
          </button>
        </>
      )}
    </Cadre>
  )
}

/* ---------------- registre ---------------- */

type Rendu = (p: { bloc: Bloc; ctx: Ctx; numero: number }) => ReactNode

export const RENDUS: Record<Bloc["type"], Rendu> = {
  objectifs: ({ bloc }) => <Objectifs bloc={bloc as Extract<Bloc, { type: "objectifs" }>} />,
  texte: ({ bloc }) => <Texte bloc={bloc as Extract<Bloc, { type: "texte" }>} />,
  exemple: ({ bloc }) => <Exemple bloc={bloc as Extract<Bloc, { type: "exemple" }>} />,
  exercice: ({ bloc, ctx, numero }) => <Exercice bloc={bloc as Extract<Bloc, { type: "exercice" }>} ctx={ctx} numero={numero} />,
  question_ouverte: ({ bloc, ctx }) => <Ouverte bloc={bloc} ctx={ctx} etiquette="Explique avec tes mots" consigne={(bloc as Extract<Bloc, { type: "question_ouverte" }>).question} />,
  synthese: ({ bloc, ctx }) => <Ouverte bloc={bloc} ctx={ctx} etiquette="Pour finir" consigne={(bloc as Extract<Bloc, { type: "synthese" }>).consigne} />,
}

export function BlocLecon(p: { bloc: Bloc; ctx: Ctx; numero: number }) {
  const R = RENDUS[p.bloc.type]
  return R ? <>{R(p)}</> : null
}
