import { AnimatePresence, motion, useReducedMotion } from "framer-motion"
import { CalendarClock, PartyPopper, RotateCcw } from "lucide-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { ReactNode } from "react"
import { cn } from "@/lib/utils"
import { CarteRetournable } from "./CarteRetournable"
import {
  NOTES,
  ORDRE_NOTES,
  apercu,
  cartesDues,
  chargerEtats,
  etatDe,
  formaterDate,
  formaterIntervalle,
  noter,
  prochaineEcheance,
  sauverEtats,
} from "./planificateur"
import type { EtatsPaquet, NoteFlash } from "./planificateur"
import type { BilanFlash, CarteFlash, PaquetFlash } from "./types"

type Props = {
  paquet: PaquetFlash
  onFin?: (bilan: BilanFlash) => void
}

// Clés = valeurs de Rating (1 Again, 2 Hard, 3 Good, 4 Easy).
const LIBELLES: Record<NoteFlash, { texte: string; classe: string }> = {
  1: { texte: "Pas su", classe: "border-rouge/40 text-rouge hover:bg-rouge/5" },
  2: { texte: "Difficile", classe: "border-orange/40 text-orange hover:bg-orange/5" },
  3: { texte: "Su", classe: "border-vert/40 text-vert hover:bg-vert/5" },
  4: { texte: "Facile", classe: "border-bleu/40 text-bleu hover:bg-bleu/5" },
}

type Session = {
  file: CarteFlash[]
  position: number
  /** Résultat de la première tentative de chaque carte. */
  resultats: Record<string, boolean>
  /** Cartes déjà remises en fin de file après « Pas su » (une seule fois). */
  remises: string[]
  terminee: boolean
}

function nouvelleSession(cartes: CarteFlash[]): Session {
  return { file: cartes, position: 0, resultats: {}, remises: [], terminee: cartes.length === 0 }
}

export function SessionFlash({ paquet, onFin }: Props) {
  const [etats, setEtats] = useState<EtatsPaquet>(() => chargerEtats(paquet.id))
  const [session, setSession] = useState<Session>(() => nouvelleSession(cartesDues(paquet, chargerEtats(paquet.id), new Date())))
  const [retournee, setRetournee] = useState(false)
  const [maintenant, setMaintenant] = useState(() => new Date())
  const refCarte = useRef<HTMLButtonElement>(null)
  const reduire = useReducedMotion()

  // Changement de paquet : on repart de zéro.
  useEffect(() => {
    const e = chargerEtats(paquet.id)
    setEtats(e)
    setSession(nouvelleSession(cartesDues(paquet, e, new Date())))
    setRetournee(false)
  }, [paquet])

  const carte = session.terminee ? undefined : session.file[session.position]
  const etatCourant = carte ? etatDe(etats, carte.id, maintenant) : undefined
  const previsions = useMemo(() => (etatCourant ? apercu(etatCourant, maintenant) : null), [etatCourant, maintenant])

  useEffect(() => {
    if (carte) refCarte.current?.focus({ preventScroll: true })
  }, [carte])

  const retourner = useCallback(() => {
    setRetournee((r) => !r)
    setMaintenant(new Date())
  }, [])

  const choisir = useCallback(
    (note: NoteFlash) => {
      if (!carte || !etatCourant || !retournee) return
      const instant = new Date()
      const suivants = { ...etats, [carte.id]: noter(etatCourant, note, instant) }
      setEtats(suivants)
      sauverEtats(paquet.id, suivants)

      const echec = note === NOTES.pasSu
      const dejaVue = carte.id in session.resultats
      const resultats = dejaVue ? session.resultats : { ...session.resultats, [carte.id]: !echec }
      let file = session.file
      let remises = session.remises
      if (echec && !remises.includes(carte.id)) {
        file = [...file, carte]
        remises = [...remises, carte.id]
      }
      const position = session.position + 1
      const terminee = position >= file.length
      setSession({ file, position, resultats, remises, terminee })
      setRetournee(false)
      setMaintenant(instant)

      if (terminee) {
        const valeurs = Object.values(resultats)
        const su = valeurs.filter(Boolean).length
        onFin?.({ total: valeurs.length, su, aRevoir: valeurs.length - su })
      }
    },
    [carte, etatCourant, retournee, etats, paquet.id, session, onFin],
  )

  // Raccourcis : 1-4 pour noter, Espace/Entrée pour retourner (hors bouton focalisé).
  useEffect(() => {
    function surTouche(ev: KeyboardEvent) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || !carte) return
      const cible = ev.target as HTMLElement | null
      if (cible && /^(INPUT|TEXTAREA|SELECT)$/.test(cible.tagName)) return
      if (retournee && ["1", "2", "3", "4"].includes(ev.key)) {
        ev.preventDefault()
        choisir(ORDRE_NOTES[Number(ev.key) - 1])
        return
      }
      if ((ev.key === " " || ev.key === "Enter") && !(cible && cible.closest("button"))) {
        ev.preventDefault()
        retourner()
      }
    }
    window.addEventListener("keydown", surTouche)
    return () => window.removeEventListener("keydown", surTouche)
  }, [carte, retournee, choisir, retourner])

  const recommencer = (toutes: boolean) => {
    const e = chargerEtats(paquet.id)
    setEtats(e)
    setSession(nouvelleSession(toutes ? paquet.cartes : cartesDues(paquet, e, new Date())))
    setRetournee(false)
    setMaintenant(new Date())
  }

  const total = session.file.length
  const faites = Math.min(session.position, total)
  const aucunDu = total === 0

  return (
    <section className="mx-auto flex w-full max-w-2xl flex-col items-center gap-6" aria-label={`Flashcards : ${paquet.titre}`}>
      <header className="w-full">
        <div className="mb-2 flex items-baseline justify-between gap-4">
          <h2 className="font-titre text-2xl font-semibold text-encre">{paquet.titre}</h2>
          {!aucunDu && (
            <span className="text-base font-medium text-gris" aria-live="polite">
              {faites} / {total}
            </span>
          )}
        </div>
        {!aucunDu && (
          <div
            className="h-3 w-full overflow-hidden rounded-full bg-bleu-clair"
            role="progressbar"
            aria-label="Progression de la session"
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={faites}
          >
            <motion.div
              className="h-full rounded-full bg-bleu"
              initial={false}
              animate={{ width: `${total ? (faites / total) * 100 : 0}%` }}
              transition={{ duration: reduire ? 0 : 0.35, ease: "easeOut" }}
            />
          </div>
        )}
      </header>

      <AnimatePresence mode="wait" initial={false}>
        {aucunDu ? (
          <RienARevoir key="vide" prochaine={prochaineEcheance(paquet, etats)} onToutRevoir={() => recommencer(true)} />
        ) : session.terminee ? (
          <Bilan key="bilan" resultats={session.resultats} onRecommencer={() => recommencer(false)} onToutRevoir={() => recommencer(true)} />
        ) : carte ? (
          <motion.div
            key={`${carte.id}-${session.position}`}
            className="flex w-full flex-col items-center gap-6"
            initial={reduire ? { opacity: 0 } : { opacity: 0, x: 60 }}
            animate={{ opacity: 1, x: 0 }}
            exit={reduire ? { opacity: 0 } : { opacity: 0, x: -60 }}
            transition={{ duration: reduire ? 0.15 : 0.28, ease: "easeOut" }}
          >
            <CarteRetournable
              ref={refCarte}
              recto={carte.recto}
              verso={carte.verso}
              indice={carte.indice}
              retournee={retournee}
              onRetourner={retourner}
            />

            <div className="min-h-[104px] w-full">
              {retournee && previsions ? (
                <motion.div
                  className="grid w-full grid-cols-2 gap-3 sm:grid-cols-4"
                  initial={{ opacity: 0, y: reduire ? 0 : 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  role="group"
                  aria-label="Comment ça s'est passé ?"
                >
                  {ORDRE_NOTES.map((note, i) => {
                    const intervalle = formaterIntervalle(maintenant, previsions[note])
                    return (
                      <button
                        key={note}
                        type="button"
                        onClick={() => choisir(note)}
                        aria-label={`${LIBELLES[note].texte}, revoir ${intervalle}. Raccourci ${i + 1}`}
                        aria-keyshortcuts={String(i + 1)}
                        className={cn(
                          "flex flex-col items-center gap-1 rounded-2xl border-2 bg-white px-3 py-3 shadow-relief transition",
                          "hover:-translate-y-0.5 hover:shadow-relief-haut focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-bleu/40",
                          LIBELLES[note].classe,
                        )}
                      >
                        <span className="font-titre text-lg font-semibold">{LIBELLES[note].texte}</span>
                        <span className="text-sm text-gris">{intervalle}</span>
                        <kbd className="rounded-md border border-bord px-1.5 text-xs text-gris">{i + 1}</kbd>
                      </button>
                    )
                  })}
                </motion.div>
              ) : (
                <p className="pt-6 text-center text-base text-gris">Réfléchis à la réponse, puis retourne la carte.</p>
              )}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  )
}

function Panneau({ children }: { children: ReactNode }) {
  const reduire = useReducedMotion()
  return (
    <motion.div
      className="flex w-full flex-col items-center gap-4 rounded-3xl border border-bord bg-white p-8 text-center shadow-relief"
      initial={{ opacity: 0, y: reduire ? 0 : 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
    >
      {children}
    </motion.div>
  )
}

const boutonPrincipal =
  "inline-flex items-center gap-2 rounded-2xl bg-bleu px-5 py-3 font-titre text-lg font-semibold text-white shadow-relief transition hover:-translate-y-0.5 hover:shadow-relief-haut focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-bleu/40 focus-visible:ring-offset-2"
const boutonSecondaire =
  "inline-flex items-center gap-2 rounded-2xl border border-bord bg-white px-5 py-3 font-titre text-lg font-medium text-encre transition hover:bg-nav focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-bleu/40 focus-visible:ring-offset-2"

function Bilan({
  resultats,
  onRecommencer,
  onToutRevoir,
}: {
  resultats: Record<string, boolean>
  onRecommencer: () => void
  onToutRevoir: () => void
}) {
  const valeurs = Object.values(resultats)
  const su = valeurs.filter(Boolean).length
  const aRevoir = valeurs.length - su
  return (
    <Panneau>
      <PartyPopper className="size-10 text-bleu" aria-hidden />
      <h3 className="font-titre text-2xl font-semibold text-encre">Session terminée !</h3>
      <div className="flex gap-4" aria-live="polite">
        <div className="rounded-2xl bg-bleu-clair px-5 py-3">
          <div className="font-titre text-3xl font-bold text-vert">{su}</div>
          <div className="text-base text-encre">su{su > 1 ? "es" : ""}</div>
        </div>
        <div className="rounded-2xl bg-bleu-clair px-5 py-3">
          <div className="font-titre text-3xl font-bold text-orange">{aRevoir}</div>
          <div className="text-base text-encre">à revoir</div>
        </div>
      </div>
      <p className="text-base text-gris">Jules te reproposera ces cartes au bon moment.</p>
      <div className="flex flex-wrap justify-center gap-3">
        <button type="button" onClick={onRecommencer} className={boutonPrincipal}>
          <RotateCcw className="size-5" aria-hidden />
          Recommencer
        </button>
        <button type="button" onClick={onToutRevoir} className={boutonSecondaire}>
          Tout revoir
        </button>
      </div>
    </Panneau>
  )
}

function RienARevoir({ prochaine, onToutRevoir }: { prochaine: Date | null; onToutRevoir: () => void }) {
  return (
    <Panneau>
      <CalendarClock className="size-10 text-vert" aria-hidden />
      <h3 className="font-titre text-2xl font-semibold text-encre">Rien à revoir pour l'instant</h3>
      {prochaine && (
        <p className="text-lg text-encre">
          Prochaine révision : <strong className="font-semibold">{formaterDate(prochaine)}</strong>
        </p>
      )}
      <p className="text-base text-gris">Ta mémoire travaille pendant la pause. Reviens plus tard !</p>
      <button type="button" onClick={onToutRevoir} className={boutonSecondaire}>
        Réviser quand même
      </button>
    </Panneau>
  )
}
