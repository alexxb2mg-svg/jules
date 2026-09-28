// Écran partagé : la leçon/exercice à gauche, Jules à droite (idée n°1 de la veille DinoBot).
// Panneaux redimensionnables (shadcn Resizable) ; le tuteur voit la même conversation que la séance.
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { ChevronLeft, Clock } from "lucide-react"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Progress } from "@/components/ui/progress"
import { cours, type Session, type Progression } from "@/api/jules"
import { BlocLecon } from "@/modules/lecon/BlocsLecon"
import { PanneauJules, type AideRapide } from "@/modules/tuteur/PanneauJules"
import { SUGGESTIONS } from "@/config/veille"
import type { Lecon } from "@/api/jules"

/** B : suggestions tirées de la leçon affichée (objectifs, titres des parties), jamais générées. */
function suggestionsDe(lecon: Lecon): AideRapide[] {
  const objectifs = lecon.blocs.flatMap((b) => (b.type === "objectifs" ? b.items : []))
  const parties = lecon.blocs.flatMap((b) => (b.type === "texte" && b.titre ? [b.titre] : []))
  return [...objectifs.slice(0, 2).map(SUGGESTIONS.objectif), ...parties.slice(0, 2).map(SUGGESTIONS.partie)].slice(0, SUGGESTIONS.max)
}

const AIDES: AideRapide[] = [
  { libelle: "Je bloque", message: "Je bloque sur l'exercice, tu peux m'aider à démarrer sans me donner la réponse ?" },
  { libelle: "Réexplique", message: "Tu peux me réexpliquer la méthode autrement ?" },
  { libelle: "Un exemple", message: "Tu peux me donner un autre exemple, plus simple ?" },
]

export function EcranPartage({ notion, fil, onRetour }: { notion: string; fil: string; onRetour: () => void }) {
  const [session, setSession] = useState<Session | null>(null)
  const [progression, setProgression] = useState<Progression | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [relire, setRelire] = useState(0)

  useEffect(() => {
    cours.ouvrir(notion).then((s) => { setSession(s); setProgression(s.progression) }).catch((e) => setErreur(e.message))
  }, [notion])

  // #/lecon/<notion>/<bloc> : défile jusqu'au bloc demandé (reprise « là où tu t'étais arrêtée »).
  useEffect(() => {
    const cible = window.location.hash.match(/^#\/lecon\/[\w-]+\/(\d+)/)?.[1]
    if (session && cible) setTimeout(() => document.getElementById(`bloc-${cible}`)?.scrollIntoView({ block: "start" }), 50)
  }, [session])

  if (erreur) return <div className="grid h-full place-items-center text-gris">Impossible d'ouvrir la leçon ({erreur}).</div>
  if (!session || !progression) return <div className="grid h-full place-items-center text-gris">Chargement de la leçon…</div>

  const { lecon } = session
  const faits = progression.blocs.filter((b) => b.etat !== "a_faire" && b.etat !== "en_cours").length
  const pct = Math.round((faits / progression.blocs.length) * 100)
  let numExo = 0

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-4 border-b border-bord px-6 py-3">
        <button onClick={onRetour} className="flex items-center gap-1 rounded-lg px-2 py-1 text-[15px] text-gris hover:bg-survol">
          <ChevronLeft size={16} /> Retour
        </button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] text-gris">{fil}</p>
          <h1 className="truncate text-[20px] leading-tight font-bold">{lecon.titre}</h1>
        </div>
        {lecon.duree_minutes && <span className="flex items-center gap-1 text-[14px] text-gris"><Clock size={15} /> {lecon.duree_minutes} min</span>}
        <div className="flex w-44 items-center gap-2">
          <Progress value={pct} className="h-2.5" />
          <span className="w-10 text-right text-[13px] font-semibold text-bleu">{pct}%</span>
        </div>
      </header>

      <ResizablePanelGroup orientation="horizontal" className="min-h-0 flex-1">
        <ResizablePanel defaultSize="64" minSize="40">
          <div className="h-full overflow-y-auto">
            <motion.div className="mx-auto flex max-w-[760px] flex-col gap-4 px-8 py-6"
              initial="cache" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.05 } } }}>
              {lecon.blocs.map((b) => {
                if (b.type === "exercice") numExo += 1
                return (
                  <div key={b.index} id={`bloc-${b.index}`} className="scroll-mt-4">
                    <BlocLecon bloc={b} numero={numExo} ctx={{
                      session: session.session,
                      etat: progression.blocs[b.index]?.etat ?? "a_faire",
                      onProgression: setProgression,
                      onJulesARepondu: () => setRelire((n) => n + 1),
                    }} />
                  </div>
                )
              })}
              <p className="pt-2 text-[12px] leading-snug text-gris">
                Sources : {lecon.sources.map((s) => `${s.titre} (${s.licence})`).join(" · ")}
              </p>
            </motion.div>
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize="36" minSize="26" maxSize="55">
          <PanneauJules conversationId={session.conversation} sousTitre="Il voit la leçon que tu fais" aides={AIDES}
            suggestions={suggestionsDe(lecon)} rafraichir={relire} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
