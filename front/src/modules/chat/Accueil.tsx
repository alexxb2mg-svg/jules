// Écran d'accueil du chat : Jules en personnage + son message d'accueil + grille de modes + encart épreuve + exercices.
// Fidèle à ecranAccueil() / proposerEpreuve() / proposerExercices() de eleve.js.
import { createElement, useEffect, useState } from "react"
import { motion } from "framer-motion"
import { epreuve as apiEpreuve, type InfosChat, type ModeChat } from "@/api/jules"
import { Compass, Dumbbell } from "lucide-react"
import { AvatarJules } from "@/components/ui/avatar"
import { bulleVariants } from "@/components/ui/variantes"
import { buttonVariants } from "@/components/ui/button"
import { Pastille } from "@/components/ui/pastille"
import { surfaceVariants, titreVariants } from "@/components/ui/variantes"
import { iconeMode } from "@/config/modes"
import { useMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"

type Props = {
  infos: InfosChat
  onDemarrer: (mode: string) => void
  onEpreuve: () => void
  onExercice: (notionId: string, generee?: boolean) => void
}

export function Accueil({ infos, onDemarrer, onEpreuve, onExercice }: Props) {
  const modes = (infos.modes ?? []).filter((m) => !m.cache)
  const { apparition } = useMotion()

  return (
    <div className="mx-auto flex w-full max-w-lg flex-col gap-8 px-4 pt-4 pb-10">
      {/* Jules t'accueille : portrait et première bulle */}
      <motion.div {...apparition} className="flex items-end gap-3">
        <AvatarJules taille="xl" className="ring-8 ring-bleu-clair/60" />
        <p className={cn(bulleVariants({ auteur: "jules", tete: false }), "m-0 mb-2 rounded-bl-md")}>{infos.persona.accueil}</p>
      </motion.div>

      {/* Grille de modes */}
      {modes.length > 0 && (
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {modes.map((mode) => (
            <ModeButton key={mode.id} mode={mode} onClick={() => onDemarrer(mode.id)} />
          ))}
        </div>
      )}

      {/* Encart épreuve */}
      {infos.epreuve && <EncartEpreuve onCommencer={onEpreuve} />}

      {/* Encart exercices */}
      {(infos.exercices ?? []).length > 0 && (
        <EncartExercices exercices={infos.exercices!} onCommencer={onExercice} />
      )}
    </div>
  )
}

function ModeButton({ mode, onClick }: { mode: ModeChat; onClick: () => void }) {
  const { tap } = useMotion()
  return (
    <motion.button {...tap} onClick={onClick}
      className={surfaceVariants({ ton: "plat", espace: "compact", cliquable: true, className: "flex items-center gap-3.5" })}>
      <Pastille ton="jules" taille="icone">{createElement(iconeMode(mode.id), { size: 20 })}</Pastille>
      <div className="min-w-0">
        <strong className="block text-courant font-semibold">{mode.nom}</strong>
        <small className="block text-petit text-gris">{mode.description}</small>
      </div>
    </motion.button>
  )
}

function EncartEpreuve({ onCommencer }: { onCommencer: () => void }) {
  const [notions, setNotions] = useState<string[]>([])
  const [visible, setVisible] = useState(false)
  const { tap } = useMotion()

  useEffect(() => {
    apiEpreuve.proposition()
      .then((r) => {
        if (r.notions.length > 0) {
          setNotions(r.notions.map((n) => n.notion))
          setVisible(true)
        }
      })
      .catch(() => {})
  }, [])

  if (!visible) return null

  return (
    <section className={surfaceVariants({ ton: "plat" })}>
      <h2 className={titreVariants({ niveau: "bloc", className: "mb-1.5 flex items-center gap-2.5" })}>
        <Compass className="size-5 text-bleu" /> Épreuve sans aide
      </h2>
      <p className="mt-0 mb-4 text-courant text-gris">
        Il y a quelques jours, tu avais compris {notions.join(", ")}. Est-ce que ça a tenu ?
      </p>
      <motion.button {...tap} onClick={onCommencer} className={buttonVariants({ variant: "jules", size: "pastille" })}>
        Faire l'épreuve
      </motion.button>
    </section>
  )
}

function EncartExercices({ exercices, onCommencer }: {
  exercices: { id: string; titre: string; nb: number; generateur?: boolean }[]
  onCommencer: (notionId: string, generee?: boolean) => void
}) {
  const chip = buttonVariants({ variant: "doux", size: "pastille-sm", className: "h-auto min-h-9 py-1.5 whitespace-normal text-left" })
  return (
    <section className={surfaceVariants({ ton: "plat" })}>
      <h2 className={titreVariants({ niveau: "bloc", className: "mb-1.5 flex items-center gap-2.5" })}>
        <Dumbbell className="size-5 text-bleu" /> S'entraîner sans IA
      </h2>
      <p className="mt-0 mb-4 text-courant text-gris">
        Des exercices corrigés tout de suite, avec un indice si tu bloques.
      </p>
      <div className="flex flex-wrap gap-2">
        {exercices.map((n) => (
          <div key={n.id} className="flex flex-wrap gap-2">
            <button onClick={() => onCommencer(n.id)} className={chip}>
              {n.titre} ({n.nb})
            </button>
            {n.generateur && (
              <button onClick={() => onCommencer(n.id, true)} title="Une série avec d'autres nombres à chaque fois" className={chip}>
                {n.titre} : nouveaux nombres
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
