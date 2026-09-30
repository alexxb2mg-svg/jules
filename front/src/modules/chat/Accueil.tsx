// Écran d'accueil du chat : avatar + message d'accueil + grille de modes + encart épreuve + exercices.
// Fidèle à ecranAccueil() / proposerEpreuve() / proposerExercices() de eleve.js.
import { useEffect, useState } from "react"
import { epreuve as apiEpreuve, type InfosChat, type ModeChat } from "@/api/jules"
import { Compass, Dumbbell } from "lucide-react"

type Props = {
  infos: InfosChat
  onDemarrer: (mode: string) => void
  onEpreuve: () => void
  onExercice: (notionId: string, generee?: boolean) => void
}

export function Accueil({ infos, onDemarrer, onEpreuve, onExercice }: Props) {
  const modes = (infos.modes ?? []).filter((m) => !m.cache)

  return (
    <div className="flex flex-col items-center gap-6 px-4 py-8">
      {/* Avatar + accueil */}
      <div className="flex flex-col items-center gap-3 text-center">
        <img src="/api/persona/avatar" alt="" className="size-20 rounded-full bg-bleu-clair"
          onError={(e) => { e.currentTarget.style.display = "none" }} />
        <p className="max-w-md text-[15px] text-gris">{infos.persona.accueil}</p>
      </div>

      {/* Grille de modes */}
      {modes.length > 0 && (
        <div className="grid w-full max-w-lg grid-cols-1 gap-3 sm:grid-cols-2">
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
  return (
    <button onClick={onClick}
      className="flex items-start gap-3 rounded-2xl border border-bord bg-white px-4 py-3 text-left shadow-relief transition hover:border-bleu hover:shadow-md">
      <span className="text-2xl leading-none">{mode.icone}</span>
      <div className="min-w-0">
        <strong className="block text-[14px] font-semibold">{mode.nom}</strong>
        <small className="text-[13px] max-md:text-[14px] text-gris">{mode.description}</small>
      </div>
    </button>
  )
}

function EncartEpreuve({ onCommencer }: { onCommencer: () => void }) {
  const [notions, setNotions] = useState<string[]>([])
  const [visible, setVisible] = useState(false)

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
    <div className="w-full max-w-lg rounded-2xl border border-bord bg-white p-4 shadow-relief">
      <div className="mb-2 flex items-center gap-2">
        <Compass className="size-5 text-bleu" />
        <strong className="text-[14px]">Épreuve sans aide</strong>
      </div>
      <p className="mb-3 text-[13px] max-md:text-[14px] text-gris">
        Il y a quelques jours, tu avais compris {notions.join(", ")}. Est-ce que ça a tenu ?
      </p>
      <button onClick={onCommencer}
        className="rounded-lg bg-bleu px-4 py-1.5 text-sm font-medium text-white transition hover:bg-bleu/90">
        Faire l'épreuve
      </button>
    </div>
  )
}

function EncartExercices({ exercices, onCommencer }: {
  exercices: { id: string; titre: string; nb: number; generateur?: boolean }[]
  onCommencer: (notionId: string, generee?: boolean) => void
}) {
  return (
    <div className="w-full max-w-lg rounded-2xl border border-bord bg-white p-4 shadow-relief">
      <div className="mb-2 flex items-center gap-2">
        <Dumbbell className="size-5 text-bleu" />
        <strong className="text-[14px]">S'entraîner sans IA</strong>
      </div>
      <p className="mb-3 text-[13px] max-md:text-[14px] text-gris">
        Des exercices corrigés tout de suite, avec un indice si tu bloques.
      </p>
      <div className="flex flex-wrap gap-2">
        {exercices.map((n) => (
          <div key={n.id} className="flex gap-1">
            <button onClick={() => onCommencer(n.id)}
              className="rounded-lg border border-bord px-3 py-1.5 text-[13px] max-md:text-[14px] font-medium transition hover:border-bleu hover:text-bleu">
              {n.titre} ({n.nb})
            </button>
            {n.generateur && (
              <button onClick={() => onCommencer(n.id, true)} title="Une série avec d'autres nombres à chaque fois"
                className="rounded-lg border border-bord px-3 py-1.5 text-[13px] max-md:text-[14px] font-medium transition hover:border-bleu hover:text-bleu">
                {n.titre} : nouveaux nombres
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
