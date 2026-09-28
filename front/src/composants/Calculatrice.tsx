// Calculatrice : bouton flottant + panneau, outil isolé servi par le module 'outils' (docs/OUTILS-CONTRAT.md).
// Portage React de calculatrice.js + outils-hote.js : iframe sandbox="allow-scripts" SANS allow-same-origin
// (origine opaque : ni cookie, ni DOM, ni localStorage), messages acceptés seulement de CETTE iframe, poignée de main
// des adaptations (chaque « pret » reçoit les leviers de l'élève), événement réservé « fermer » (Échap dans l'iframe).
// UI : shadcn (Radix). Grand écran : Popover non modal, la page pousse son contenu pour lui faire de la place.
// Mobile : tiroir modal en bas (Sheet), la page dessous n'est pas utilisable de toute façon. Échap, focus et aria : Radix.
// Pas de bouton mort : il n'existe que si l'outil figure dans le catalogue de /api/infos. Les fichiers de l'outil ne
// sont demandés qu'à l'ouverture ; à la fermeture l'iframe est démontée.
import { useEffect, useRef, useState } from "react"
import { Calculator, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverClose, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet"
import { useIsMobile } from "@/hooks/use-mobile"
import type { Infos } from "@/api/jules"

const OUTIL = "calculatrice"
const TEXTES = { nom: "Calculatrice", fermer: "Fermer la calculatrice" }

type EntreeOutil = { id: string; titre?: string; evenements?: string[] }
const estObjet = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === "object" && !Array.isArray(v)

/** `onOuvert` : la page réserve la place du panneau (sur grand écran) au lieu de la laisser passer dessous. */
export function Calculatrice({ infos, onOuvert }: { infos: Infos | null; onOuvert?: (ouvert: boolean) => void }) {
  const outil = (infos?.outils?.catalogue ?? []).find((o: EntreeOutil) => o?.id === OUTIL)
  const [ouvert, setOuvert] = useState(false)
  const mobile = useIsMobile()
  const boutonMobile = useRef<HTMLButtonElement>(null)
  const cadre = useRef<HTMLIFrameElement>(null)
  const leviers = useRef<Record<string, unknown>>({})
  leviers.current = infos?.leviers ?? {}

  useEffect(() => { onOuvert?.(ouvert) }, [ouvert, onOuvert])

  useEffect(() => {
    if (!ouvert) return
    const recu = (e: MessageEvent) => {
      // Jamais event.origin (« null » pour une iframe sandboxée) : seule la fenêtre de CETTE iframe compte.
      if (!cadre.current?.contentWindow || e.source !== cadre.current.contentWindow || !estObjet(e.data)) return
      if (e.data.type === "pret") cadre.current.contentWindow.postMessage({ type: "adaptations", leviers: leviers.current }, "*")
      // Échap pressé DANS l'iframe : la page ne voit pas ce clavier (origine opaque), l'outil demande la fermeture.
      else if (e.data.type === "evenement" && e.data.evenement === "fermer" && (outil?.evenements ?? []).includes("fermer")) setOuvert(false)
    }
    addEventListener("message", recu)
    return () => removeEventListener("message", recu)
  }, [ouvert, outil])

  if (!outil) return null
  const titre = outil.titre || TEXTES.nom
  const cadreOutil = (
    <iframe ref={cadre} title={titre} sandbox="allow-scripts" referrerPolicy="no-referrer"
      src={`/api/eleve/outils/${encodeURIComponent(OUTIL)}/`} className="min-h-0 w-full flex-1 border-0" />
  )
  const boutonFermer = (Fermer: typeof PopoverClose | typeof SheetClose) => (
    <Fermer asChild>
      <Button type="button" variant="ghost" size="icon" aria-label={TEXTES.fermer} className="size-11 rounded-xl text-encre hover:bg-bleu-clair"><X className="size-5" /></Button>
    </Fermer>
  )
  const classeBouton = "absolute top-3 right-4 z-40 size-11 rounded-full border-bord bg-white text-bleu shadow-relief hover:border-bleu hover:bg-white hover:text-bleu aria-expanded:bg-bleu aria-expanded:text-white [&_svg:not([class*='size-'])]:size-[22px]"

  if (mobile) {
    return (
      <>
        <Button ref={boutonMobile} type="button" variant="outline" size="icon" aria-label={TEXTES.nom} title={TEXTES.nom} aria-expanded={ouvert}
          onClick={() => setOuvert(true)} className={classeBouton}><Calculator /></Button>
        <Sheet open={ouvert} onOpenChange={setOuvert}>
          <SheetContent side="bottom" showCloseButton={false} onCloseAutoFocus={(e) => { e.preventDefault(); boutonMobile.current?.focus() }} className="h-[min(38rem,92dvh)] gap-0 rounded-t-2xl border-bord bg-white p-0">
            <div className="flex items-center justify-between border-b border-bord py-1 pr-1 pl-3.5">
              <SheetTitle className="font-titre text-base font-bold text-bleu">{titre}</SheetTitle>
              {boutonFermer(SheetClose)}
            </div>
            <SheetDescription className="sr-only">Calculatrice scientifique</SheetDescription>
            {cadreOutil}
          </SheetContent>
        </Sheet>
      </>
    )
  }
  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" size="icon" aria-label={TEXTES.nom} title={TEXTES.nom} className={classeBouton}>
          <Calculator />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" side="bottom" sideOffset={8} collisionPadding={16} aria-label={titre}
        // Non modale : la calculatrice reste ouverte quand on lit ou écrit dans la page ; on la ferme par le bouton, la croix ou Échap.
        onInteractOutside={(e) => e.preventDefault()}
        className="flex h-[min(36rem,var(--radix-popover-content-available-height))] w-[19rem] flex-col overflow-hidden rounded-2xl border-bord bg-white p-0 shadow-relief-haut">
        <div className="flex items-center justify-between border-b border-bord py-1 pr-1 pl-3.5">
          <span className="font-titre text-base font-bold text-bleu">{titre}</span>
          {boutonFermer(PopoverClose)}
        </div>
        {cadreOutil}
      </PopoverContent>
    </Popover>
  )
}
