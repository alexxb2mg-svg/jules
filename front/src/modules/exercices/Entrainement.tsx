// « M'entraîner » dans la fiche : la série d'exercices de la fiche v2 de la notion, corrigée par le code.
// Chaque réponse passe par Tuteur.echanger (même historique et même suivi que dans le chat), sans IA.
import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, CircleCheck, CircleX, Dumbbell, Lightbulb, RotateCcw, Shuffle, Sparkles, TriangleAlert } from "lucide-react"
import { cn } from "@/lib/utils"
import { exercices, type Bilan, type ExerciceVue, type ReponseExercice, type Verdict } from "@/api/jules"
import { Riche } from "@/modules/fiches/texte"
import { SAISIES } from "./saisies"

/** Libellés de l'écran (un seul endroit). Les messages de correction, eux, viennent du serveur. */
const TEXTES = {
  titre: "M'entraîner",
  intro: (nb: number) => `${nb} exercice${nb > 1 ? "s" : ""} sur cette notion, corrigés tout de suite. Si tu bloques, Jules te donne un indice.`,
  commencer: "Commencer",
  generer: "Une série avec d'autres nombres",
  suivant: "Exercice suivant",
  recommencer: "Recommencer",
  exercice: (i: number, n: number) => `Exercice ${i} sur ${n}`,
  aRevoir: "À revoir avant de continuer :",
  correction: "La correction",
  bilan: (b: Bilan) => `${b.reussis} sur ${b.faits} réussi${b.reussis > 1 ? "s" : ""}`,
  sansAide: (n: number) => `${n} sans indice`,
  avecAide: (n: number) => `${n} avec un coup de pouce`,
  typeInconnu: "Cet exercice ne peut pas encore s'afficher ici : réponds-y dans Discuter avec Jules.",
}

const DIFFICULTE = ["", "Facile", "Moyen", "Costaud"]

/** Aspect d'un retour, selon le verdict décidé par le serveur. */
const RETOURS: Record<Verdict["verdict"], { Icone: typeof CircleCheck; classe: string }> = {
  juste: { Icone: CircleCheck, classe: "border-[#9BD8B5] bg-[#EEFAF2] text-[#135C33]" },
  faux: { Icone: CircleX, classe: "border-[#F2B8B5] bg-[#FDF1F0] text-[#8A1F17]" },
  indice: { Icone: Lightbulb, classe: "border-[#F3D9A6] bg-[#FFF8EC] text-[#7A4B00]" },
  illisible: { Icone: TriangleAlert, classe: "border-[#F3D9A6] bg-[#FFF8EC] text-[#7A4B00]" },
  relire: { Icone: Sparkles, classe: "border-bord bg-nav text-encre" },
  fini: { Icone: Sparkles, classe: "border-bord bg-nav text-encre" },
}

type Serie = { conv: string; exercice: ExerciceVue; numero: number; total: number; resultats: boolean[] }

export function Entrainement({ notion, nb, generateur }: { notion: string; nb: number; generateur: boolean }) {
  const [serie, setSerie] = useState<Serie | null>(null)
  const [verdict, setVerdict] = useState<Verdict | null>(null)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)

  const lancer = async (genere: boolean) => {
    setErreur(null); setVerdict(null); setEnvoi(true)
    try {
      const r = await (genere ? exercices.generer(notion) : exercices.commencer(notion))
      setSerie({ conv: r.conversation, exercice: r.exercice, numero: 1, total: r.total, resultats: [] })
    } catch (e) { setErreur((e as Error).message) } finally { setEnvoi(false) }
  }

  const repondre = async (reponse: ReponseExercice) => {
    if (!serie || envoi) return
    setEnvoi(true); setErreur(null)
    try {
      const v = await exercices.repondre(serie.conv, reponse)
      setVerdict(v)
      if (v.termine && v.verdict !== "fini") setSerie((s) => s && { ...s, resultats: [...s.resultats, v.verdict === "juste"] })
    } catch (e) { setErreur((e as Error).message) } finally { setEnvoi(false) }
  }

  const suivant = () => {
    if (!serie || !verdict?.suivant) return
    setSerie({ ...serie, exercice: verdict.suivant, numero: serie.numero + 1 })
    setVerdict(null)
  }

  const bilan = verdict?.bilan
  const exerciceTermine = !!verdict?.termine

  return (
    <section id="bloc-entrainement" data-bloc="entrainement" className="scroll-mt-6 overflow-hidden rounded-[22px] border-2 border-(--m-accent) bg-white shadow-relief">
      <header className="flex items-center gap-3 bg-(--m-fond) px-5 py-3.5">
        <span className="grid size-9 place-items-center rounded-xl bg-(--m-accent) text-white"><Dumbbell size={19} /></span>
        <h2 className="m-0 flex-1 font-titre text-[1.2rem] font-bold text-(--m-texte)">{TEXTES.titre}</h2>
        {serie && !bilan && <Pastilles total={serie.total} resultats={serie.resultats} courant={serie.numero} />}
      </header>

      <div className="px-5 py-5">
        <AnimatePresence mode="wait">
          {!serie && (
            <motion.div key="intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-start gap-4">
              <p className="m-0 text-[1rem] leading-relaxed">{TEXTES.intro(nb)}</p>
              <div className="flex flex-wrap gap-2">
                <motion.button whileTap={{ scale: 0.96 }} disabled={envoi} onClick={() => lancer(false)}
                  className="inline-flex items-center gap-2 rounded-full bg-(--m-texte) px-5 py-2.5 font-semibold text-white shadow-relief disabled:opacity-50">
                  {TEXTES.commencer} <ArrowRight size={17} />
                </motion.button>
                {generateur && (
                  <motion.button whileTap={{ scale: 0.96 }} disabled={envoi} onClick={() => lancer(true)}
                    className="inline-flex items-center gap-2 rounded-full border-2 border-(--m-accent) px-4 py-2 font-semibold text-(--m-texte) disabled:opacity-50">
                    <Shuffle size={16} /> {TEXTES.generer}
                  </motion.button>
                )}
              </div>
            </motion.div>
          )}

          {serie && bilan && (
            <motion.div key="bilan" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center gap-3 py-4 text-center">
              <motion.span initial={{ scale: 0, rotate: -20 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 260, damping: 14 }}
                className="grid size-16 place-items-center rounded-full bg-(--m-accent) text-white"><Sparkles size={30} /></motion.span>
              <p className="m-0 font-titre text-[1.6rem] font-bold text-(--m-texte)">{TEXTES.bilan(bilan)}</p>
              <p className="m-0 text-[0.95rem] text-gris">{TEXTES.sansAide(bilan.sans_indice)} · {TEXTES.avecAide(bilan.avec_indice)}</p>
              <p className="m-0 max-w-[520px] text-[1rem] leading-relaxed">{bilan.message}</p>
              <Pastilles total={serie.total} resultats={serie.resultats} courant={0} />
              <button onClick={() => { setSerie(null); setVerdict(null) }} className="mt-1 inline-flex items-center gap-1.5 rounded-full px-4 py-2 font-semibold text-(--m-texte) hover:bg-(--m-fond)">
                <RotateCcw size={16} /> {TEXTES.recommencer}
              </button>
            </motion.div>
          )}

          {serie && !bilan && (
            <motion.div key={`ex-${serie.exercice.id}`} initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.25 }}
              className="flex flex-col gap-4">
              <p className="m-0 flex items-center gap-2 text-[0.85rem] font-semibold text-gris">
                {TEXTES.exercice(serie.numero, serie.total)}
                {DIFFICULTE[serie.exercice.difficulte] && <span className="rounded-full bg-nav px-2 py-0.5 text-[0.75rem]">{DIFFICULTE[serie.exercice.difficulte]}</span>}
              </p>
              <p className="m-0 text-[1.1rem] leading-relaxed font-medium whitespace-pre-line text-encre"><Riche texte={serie.exercice.enonce} /></p>

              {(() => {
                const Saisie = SAISIES[serie.exercice.type]
                if (!Saisie) return <p className="m-0 text-gris">{TEXTES.typeInconnu}</p>
                // key = l'exercice seul : après une erreur, l'élève garde ses choix (paires, ordre, cases) et corrige.
                return exerciceTermine ? null : <Saisie key={serie.exercice.id} exercice={serie.exercice} bloque={envoi} onRepondre={repondre} />
              })()}

              <AnimatePresence>
                {verdict && <Retour key={`${verdict.verdict}-${verdict.palier}-${verdict.message.length}`} verdict={verdict} />}
              </AnimatePresence>

              {exerciceTermine && verdict?.suivant && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                  <motion.button whileTap={{ scale: 0.96 }} onClick={suivant} autoFocus
                    className="inline-flex items-center gap-2 rounded-full bg-(--m-texte) px-5 py-2.5 font-semibold text-white shadow-relief">
                    {TEXTES.suivant} <ArrowRight size={17} />
                  </motion.button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
        {erreur && <p className="mt-3 mb-0 text-[0.9rem] text-rouge">{erreur}</p>}
      </div>
    </section>
  )
}

function Retour({ verdict }: { verdict: Verdict }) {
  // Une relance sur un piège n'est pas une sanction : même aspect qu'un indice (le verdict reste celui du serveur).
  const { Icone, classe } = RETOURS[verdict.piege && verdict.verdict === "faux" ? "indice" : verdict.verdict]
  return (
    <motion.div initial={{ opacity: 0, y: 10, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0 }}
      role="status" className={cn("flex flex-col gap-2 rounded-2xl border-2 px-4 py-3", classe)}>
      <p className="m-0 flex items-start gap-2.5 text-[1rem] leading-relaxed whitespace-pre-line">
        <motion.span initial={verdict.verdict === "juste" ? { scale: 0 } : false} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 400, damping: 12 }}
          className="mt-0.5 shrink-0"><Icone size={20} /></motion.span>
        <span><Riche texte={verdict.message} /></span>
      </p>
      {verdict.correction && (
        <div className="ml-7 rounded-xl bg-white/70 px-3 py-2 text-encre">
          <p className="m-0 text-[0.8rem] font-semibold tracking-wide text-gris">{TEXTES.correction}</p>
          <p className="m-0 text-[0.95rem] leading-relaxed whitespace-pre-line"><Riche texte={verdict.correction} /></p>
        </div>
      )}
      {verdict.a_revoir.length > 0 && (
        <p className="m-0 ml-7 text-[0.9rem]">{TEXTES.aRevoir} <b>{verdict.a_revoir.join(", ")}</b></p>
      )}
    </motion.div>
  )
}

/** Une pastille par exercice : réussi, raté, en cours, à venir. */
function Pastilles({ total, resultats, courant }: { total: number; resultats: boolean[]; courant: number }) {
  return (
    <ol className="m-0 flex list-none gap-1.5 p-0" aria-label="Avancée de la série">
      {Array.from({ length: total }, (_, i) => {
        const r = resultats[i]
        return (
          <motion.li key={i} layout initial={false} animate={{ scale: i + 1 === courant ? 1.15 : 1 }}
            className={cn("size-3 rounded-full",
              r === true ? "bg-vert" : r === false ? "bg-rouge" : i + 1 === courant ? "bg-(--m-accent) ring-2 ring-(--m-accent)/30" : "bg-bord")} />
        )
      })}
    </ol>
  )
}
