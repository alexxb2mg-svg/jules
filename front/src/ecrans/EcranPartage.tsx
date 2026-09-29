// Écran partagé : la leçon/exercice à gauche, Jules à droite (idée n°1 de la veille DinoBot).
// Panneaux redimensionnables (shadcn Resizable) ; le tuteur voit la même conversation que la séance.
// Téléphone : deux colonnes n'y tiennent pas ; la leçon prend toute la largeur et Jules s'ouvre en tiroir
// du bas (Sheet Radix) depuis un bouton flottant.
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { ChevronLeft, Clock, MessageCircle } from "lucide-react"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet"
import { useIsMobile } from "@/hooks/use-mobile"
import { Progress } from "@/components/ui/progress"
import { cours, type Session, type Progression } from "@/api/jules"
import { BlocLecon } from "@/modules/lecon/BlocsLecon"
import { PanneauJules, type AideRapide } from "@/modules/tuteur/PanneauJules"
import { SUGGESTIONS } from "@/config/veille"
import { marquerEtape } from "@/modules/accueil/etat"
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
  const mobile = useIsMobile()
  const [julesOuvert, setJulesOuvert] = useState(false)

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

  if (progression.termine) marquerEtape(notion, "lecon")
  const { lecon } = session
  const faits = progression.blocs.filter((b) => b.etat !== "a_faire" && b.etat !== "en_cours").length
  const pct = Math.round((faits / progression.blocs.length) * 100)
  let numExo = 0
  const contenu = (
    <motion.div className={`mx-auto flex max-w-[760px] flex-col gap-4 ${mobile ? "px-4 pt-5 pb-28" : "px-8 py-6"}`}
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
  )
  // Une citation d'une partie (« voir À retenir ») dans le tiroir y mène : on ferme le tiroir pour la montrer.
  const panneau = (
    <div className="h-full" onClickCapture={(e) => { if (mobile && (e.target as HTMLElement).closest("a[href^='#bloc-']")) setJulesOuvert(false) }}>
      <PanneauJules conversationId={session.conversation} sousTitre="Il voit la leçon que tu fais" aides={AIDES}
        suggestions={suggestionsDe(lecon)} rafraichir={relire}
        ancres={lecon.blocs.flatMap((b) => (b.type === "texte" && b.titre ? [{ titre: b.titre, cible: `bloc-${b.index}` }] : []))} />
    </div>
  )

  return (
    <div className="relative flex h-full flex-col">
      {/* pl/pr : place du bouton de la barre (téléphone) et de la calculatrice, tous deux flottants en haut. */}
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-bord py-3 pr-16 pl-12 md:flex-nowrap md:pr-20 md:pl-6">
        <button onClick={onRetour} aria-label="Retour" className="flex items-center gap-1 rounded-lg px-2 py-2 text-[15px] text-gris hover:bg-survol">
          <ChevronLeft size={16} /> <span className="hidden md:inline">Retour</span>
        </button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] text-gris">{fil}</p>
          <h1 className="line-clamp-2 text-[18px] leading-tight font-bold md:truncate md:text-[20px]">{lecon.titre}</h1>
        </div>
        <div className="flex w-full items-center gap-3 md:contents">
          {lecon.duree_minutes && <span className="flex shrink-0 items-center gap-1 text-[14px] text-gris"><Clock size={15} /> {lecon.duree_minutes} min</span>}
          <div className="flex flex-1 items-center gap-2 md:w-44 md:flex-none">
            <Progress value={pct} className="h-2.5" />
            <span className="w-10 text-right text-[13px] font-semibold text-bleu">{pct}%</span>
          </div>
        </div>
      </header>

      {mobile ? (
        <>
          <div className="min-h-0 flex-1 overflow-y-auto">{contenu}</div>
          <button onClick={() => setJulesOuvert(true)}
            className="absolute right-4 bottom-4 z-30 flex items-center gap-2 rounded-full bg-bleu py-2 pr-4 pl-2 text-[15px] font-semibold text-white shadow-relief-haut">
            <img src="/api/persona/avatar" alt="" className="size-9 rounded-full bg-white/20" onError={(e) => (e.currentTarget.style.display = "none")} />
            <MessageCircle size={17} /> Demander à Jules
          </button>
          <Sheet open={julesOuvert} onOpenChange={setJulesOuvert}>
            <SheetContent side="bottom" className="h-[88dvh] gap-0 overflow-hidden rounded-t-2xl border-bord p-0">
              <SheetTitle className="sr-only">Jules</SheetTitle>
              <SheetDescription className="sr-only">Jules voit la leçon que tu fais</SheetDescription>
              {panneau}
            </SheetContent>
          </Sheet>
        </>
      ) : (
      <ResizablePanelGroup orientation="horizontal" className="min-h-0 flex-1">
        <ResizablePanel defaultSize="64" minSize="40">
          <div className="h-full overflow-y-auto">{contenu}</div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize="36" minSize="26" maxSize="55">{panneau}</ResizablePanel>
      </ResizablePanelGroup>
      )}
    </div>
  )
}
