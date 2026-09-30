// Écran partagé : la leçon/exercice à gauche, Jules à droite (idée n°1 de la veille DinoBot).
// Panneaux redimensionnables (shadcn Resizable) ; le tuteur voit la même conversation que la séance.
// Téléphone : deux colonnes n'y tiennent pas ; la leçon prend toute la largeur et Jules s'ouvre en tiroir
// du bas (Sheet Radix) depuis un bouton flottant.
import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { ChevronLeft, Clock, MessageCircle } from "lucide-react"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet"
import { useIsMobile } from "@/hooks/use-mobile"
import { Progress } from "@/components/ui/progress"
import { AvatarJules } from "@/components/ui/avatar"
import { buttonVariants } from "@/components/ui/button"
import { titreVariants } from "@/components/ui/variantes"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import { useMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"
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
  const { tap } = useMotion()
  // Bouton « Demander à Jules » : réduit en pastille ronde pendant qu'on défile vers le bas, complet à l'arrêt ou en remontant.
  const [reduit, setReduit] = useState(false)
  const dernierY = useRef(0)
  const arret = useRef<number | undefined>(undefined)
  const auDefilement = (e: React.UIEvent<HTMLDivElement>) => {
    const y = e.currentTarget.scrollTop, delta = y - dernierY.current
    dernierY.current = y
    if (delta > 2) setReduit(true)
    else if (delta < -2) setReduit(false)
    window.clearTimeout(arret.current)
    arret.current = window.setTimeout(() => setReduit(false), 500)
  }
  useEffect(() => () => window.clearTimeout(arret.current), [])

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
    <motion.div className={`mx-auto flex max-w-[760px] flex-col gap-5 ${mobile ? "px-4 pt-2 pb-28" : "px-8 py-6"}`}
      initial="cache" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.05 } } }}>
      {lecon.blocs.map((b) => {
        if (b.type === "exercice") numExo += 1
        return (
          <div key={b.index} id={`bloc-${b.index}`} className="scroll-mt-36 md:scroll-mt-4">
            <BlocLecon bloc={b} numero={numExo} ctx={{
              session: session.session,
              etat: progression.blocs[b.index]?.etat ?? "a_faire",
              onProgression: setProgression,
              onJulesARepondu: () => setRelire((n) => n + 1),
            }} />
          </div>
        )
      })}
      <p className="m-0 pt-2 text-petit text-gris">
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

  // Téléphone : l'en-tête colle en haut pendant qu'on lit (titre 20 px, temps, progression), sur un fond translucide ;
  // bureau : il reste au-dessus des deux panneaux. pl/pr : place du bouton de la barre et de la calculatrice (flottants).
  const entete = (
    <header className="sticky top-0 z-20 flex flex-col gap-2.5 bg-background/85 px-4 pt-3 pb-3 backdrop-blur-md md:static md:flex-row md:items-center md:gap-5 md:bg-transparent md:py-4 md:pr-20 md:pl-6 md:backdrop-blur-none">
      <div className="flex h-11 min-w-0 items-center pr-12 pl-12 md:contents">
        <button onClick={onRetour} aria-label={`Retour : ${fil}`} className={buttonVariants({ variant: "ghost", size: "pastille-sm", className: "-ml-1 px-2 text-(--m-texte) md:order-first md:text-gris" })}>
          <ChevronLeft className="size-5" /> <span className="md:hidden">{fil}</span><span className="hidden md:inline">Retour</span>
        </button>
      </div>
      <div className="min-w-0 md:flex-1">
        <p className={titreVariants({ niveau: "surtitre", className: "hidden truncate md:block" })}>{fil}</p>
        <h1 className={titreVariants({ niveau: "bloc", className: "line-clamp-2 md:truncate" })}>{lecon.titre}</h1>
      </div>
      <div className="flex items-center gap-3 md:w-72 md:flex-none">
        {lecon.duree_minutes && <span className="flex shrink-0 items-center gap-1.5 text-petit text-gris"><Clock size={16} /> {lecon.duree_minutes} min</span>}
        <Progress value={pct} ton="matiere" className="h-2.5 flex-1" />
        <span className="w-11 text-right text-petit font-bold text-(--m-texte)">{pct}%</span>
      </div>
    </header>
  )

  return (
    <div className="relative flex h-full flex-col" style={styleMatiere(lecon.matiere)}>
      {mobile ? (
        <>
          <div className="min-h-0 flex-1 overflow-y-auto" onScroll={auDefilement}>{entete}{contenu}</div>
          <motion.button {...tap} onClick={() => setJulesOuvert(true)} aria-label="Demander à Jules" data-reduit={reduit}
            className={cn(buttonVariants({ variant: "jules" }), "absolute right-4 bottom-4 z-30 text-courant transition-[width,padding] duration-200",
              reduit ? "size-12 px-0" : "h-13 gap-2.5 pr-5 pl-1.5")}>
            {reduit ? <MessageCircle className="size-[22px]" /> : <><AvatarJules taille="md" className="ring-2 ring-white/40" /> Demander à Jules</>}
          </motion.button>
          <Sheet open={julesOuvert} onOpenChange={setJulesOuvert}>
            <SheetContent side="bottom" className="h-[88dvh] gap-0 overflow-hidden rounded-t-surface border-0 p-0 shadow-souleve">
              <SheetTitle className="sr-only">Jules</SheetTitle>
              <SheetDescription className="sr-only">Jules voit la leçon que tu fais</SheetDescription>
              {panneau}
            </SheetContent>
          </Sheet>
        </>
      ) : (
      <>
      {entete}
      <ResizablePanelGroup orientation="horizontal" className="min-h-0 flex-1">
        <ResizablePanel defaultSize="64" minSize="40">
          <div className="h-full overflow-y-auto">{contenu}</div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize="36" minSize="26" maxSize="55">{panneau}</ResizablePanel>
      </ResizablePanelGroup>
      </>
      )}
    </div>
  )
}
