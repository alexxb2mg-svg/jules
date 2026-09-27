import { motion, useReducedMotion } from "framer-motion"
import { forwardRef, useState } from "react"
import { cn } from "@/lib/utils"

type Props = {
  recto: string
  verso: string
  indice?: string
  retournee: boolean
  onRetourner: () => void
  className?: string
}

const faceCommune =
  "absolute inset-0 flex flex-col items-center justify-center gap-4 rounded-3xl border border-bord p-8 text-center [backface-visibility:hidden] [-webkit-backface-visibility:hidden]"

/** Carte qui se retourne (clic, Espace ou Entrée). Fondu si l'utilisateur réduit les animations. */
export const CarteRetournable = forwardRef<HTMLButtonElement, Props>(function CarteRetournable(
  { recto, verso, indice, retournee, onRetourner, className },
  ref,
) {
  const reduire = useReducedMotion()

  return (
    <button
      ref={ref}
      type="button"
      onClick={onRetourner}
      aria-pressed={retournee}
      aria-label={retournee ? `Réponse : ${verso}. Appuie pour revoir la question.` : `Question : ${recto}. Appuie pour voir la réponse.`}
      className={cn(
        "group relative block h-72 w-full max-w-xl cursor-pointer rounded-3xl bg-transparent [perspective:1200px] sm:h-80",
        "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-bleu/40 focus-visible:ring-offset-4",
        className,
      )}
    >
      {reduire ? (
        <span className="relative block h-full w-full rounded-3xl shadow-relief transition-shadow duration-200 group-hover:shadow-relief-haut">
          <motion.span
            className={cn(faceCommune, "bg-white")}
            initial={false}
            animate={{ opacity: retournee ? 0 : 1 }}
            transition={{ duration: 0.2 }}
            aria-hidden
          >
            <FaceRecto recto={recto} indice={indice} />
          </motion.span>
          <motion.span
            className={cn(faceCommune, "bg-bleu-clair")}
            initial={false}
            animate={{ opacity: retournee ? 1 : 0 }}
            transition={{ duration: 0.2 }}
            aria-hidden
          >
            <FaceVerso verso={verso} />
          </motion.span>
        </span>
      ) : (
        <motion.span
          className="relative block h-full w-full rounded-3xl shadow-relief transition-shadow duration-200 [transform-style:preserve-3d] group-hover:shadow-relief-haut"
          initial={false}
          animate={{ rotateY: retournee ? 180 : 0 }}
          whileHover={{ y: -4 }}
          transition={{ type: "spring", stiffness: 260, damping: 26 }}
        >
          <span className={cn(faceCommune, "bg-white")} aria-hidden>
            <FaceRecto recto={recto} indice={indice} />
          </span>
          <span className={cn(faceCommune, "bg-bleu-clair [transform:rotateY(180deg)]")} aria-hidden>
            <FaceVerso verso={verso} />
          </span>
        </motion.span>
      )}
    </button>
  )
})

function FaceRecto({ recto, indice }: { recto: string; indice?: string }) {
  const [voirIndice, setVoirIndice] = useState(false)
  return (
    <>
      <span className="text-sm font-semibold uppercase tracking-wider text-gris">Question</span>
      <span className="font-titre text-[26px] font-semibold leading-snug text-encre sm:text-[28px]">{recto}</span>
      {indice && (voirIndice ? (
        <span className="rounded-xl bg-bleu-clair px-3 py-1.5 text-[18px] text-bleu">💡 {indice}</span>
      ) : (
        // L'indice ne s'affiche qu'à la demande : il ne doit pas court-circuiter l'effort de rappel.
        <span role="button" tabIndex={0}
          onClick={(e) => { e.stopPropagation(); setVoirIndice(true) }}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.stopPropagation(); setVoirIndice(true) } }}
          className="rounded-full border border-bord px-3 py-1 text-[15px] font-semibold text-bleu hover:bg-bleu-clair">
          💡 Un indice
        </span>
      ))}
      <span className="mt-2 text-sm text-gris">Clique ou appuie sur Espace pour retourner</span>
    </>
  )
}

function FaceVerso({ verso }: { verso: string }) {
  return (
    <>
      <span className="text-sm font-semibold uppercase tracking-wider text-bleu">Réponse</span>
      <span className="font-titre text-[24px] font-medium leading-snug whitespace-pre-line text-encre sm:text-[26px]">{verso}</span>
    </>
  )
}
