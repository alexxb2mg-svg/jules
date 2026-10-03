// Brique « prendre / choisir une photo » partagée par « Ajouter mon cours » et le chat.
// Téléphone : deux actions distinctes (appareil photo direct = input `capture`, galerie = input sans `capture`).
// Bureau : un seul sélecteur de fichiers, l'apparence d'origine est fournie par `children` ; l'input `capture` n'existe pas.
import { useRef, type ReactNode } from "react"
import { Camera, ImagePlus } from "lucide-react"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"

export const TEXTE_PRENDRE = "Prendre une photo"
export const TEXTE_CHOISIR = "Choisir une image"

export function PriseDePhoto({ accept, multiple, onFichiers, children, compact, className }: {
  accept: string
  multiple?: boolean
  onFichiers: (fichiers: File[]) => void
  /** Bureau : rend le déclencheur d'origine ; `ouvrir` ouvre le sélecteur de fichiers. */
  children: (ouvrir: () => void) => ReactNode
  /** Mobile : boutons carrés avec icône seule (place comptée), sinon boutons avec libellé. */
  compact?: boolean
  className?: string
}) {
  const mobile = useIsMobile()
  const appareil = useRef<HTMLInputElement>(null)
  const galerie = useRef<HTMLInputElement>(null)
  const recevoir = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) onFichiers(Array.from(e.target.files))
    e.target.value = ""
  }
  const ouvrirGalerie = () => galerie.current?.click()
  const entree = (ref: React.RefObject<HTMLInputElement | null>, capture: boolean) => (
    <input ref={ref} type="file" hidden multiple={multiple} accept={accept}
      {...(capture ? { capture: "environment" as const } : {})} onChange={recevoir} />
  )

  if (!mobile) {
    return <>{children(ouvrirGalerie)}{entree(galerie, false)}</>
  }
  const actions = [
    { Icone: Camera, texte: TEXTE_PRENDRE, ref: appareil },
    { Icone: ImagePlus, texte: TEXTE_CHOISIR, ref: galerie },
  ]
  return (
    <div className={cn(compact ? "flex shrink-0 items-center" : "grid grid-cols-2 gap-3", className)}>
      {actions.map(({ Icone, texte, ref }) => (
        <button key={texte} type="button" onClick={() => ref.current?.click()} aria-label={compact ? texte : undefined} title={texte}
          className={compact
            ? "grid size-11 place-items-center rounded-xl text-gris transition hover:bg-bleu-clair/40 hover:text-bleu"
            : "flex min-h-[72px] flex-col items-center justify-center gap-1.5 rounded-2xl border-2 border-dashed border-bord bg-nav px-3 py-3 text-center text-[0.95rem] font-semibold text-encre active:border-(--m-accent) active:bg-(--m-fond)"}>
          <Icone size={compact ? 22 : 26} aria-hidden />
          {!compact && texte}
        </button>
      ))}
      {entree(appareil, true)}
      {entree(galerie, false)}
    </div>
  )
}
