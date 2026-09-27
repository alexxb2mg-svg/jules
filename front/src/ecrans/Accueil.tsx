import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, ChevronLeft, PenLine, BookOpen, Sparkles, AlertTriangle, Check, Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import { ELEVE, MATIERES, REPRISE, FRAGILE, type Chapitre, type Matiere } from "@/donnees"

type Intention = "devoir" | "reviser"
type Etape = { intention?: Intention; matiere?: Matiere; chapitre?: Chapitre }

const glisse = {
  initial: { opacity: 0, y: 18, filter: "blur(4px)" },
  animate: { opacity: 1, y: 0, filter: "blur(0px)" },
  exit: { opacity: 0, y: -12, filter: "blur(4px)" },
  transition: { duration: 0.28, ease: [0.2, 0.8, 0.2, 1] as const },
}

function trouver(matiereId: string, chapitreId: string) {
  const m = MATIERES.find((x) => x.id === matiereId)!
  return { matiere: m, chapitre: m.chapitres.find((c) => c.id === chapitreId)! }
}

export function Accueil({ onLancer }: { onLancer: (e: Required<Etape>) => void }) {
  const [etape, setEtape] = useState<Etape>({})
  const heure = new Date().getHours()
  const salut = heure < 12 ? "Bonjour" : heure < 18 ? "Salut" : "Bonsoir"

  return (
    <div className="mx-auto max-w-[1040px] px-10 py-10">
      {/* fil d'ariane du parcours : n'apparaît qu'après le premier choix */}
      <AnimatePresence>
        {etape.intention && (
          <motion.div
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="mb-6 flex items-center gap-2 text-[15px] text-gris"
          >
            <button onClick={() => setEtape({})} className="flex items-center gap-1 rounded-lg px-2 py-1 hover:bg-[#ECEAF6]">
              <ChevronLeft size={16} /> Accueil
            </button>
            <span>›</span>
            <button onClick={() => setEtape({ intention: etape.intention })} className="rounded-lg px-2 py-1 font-semibold text-bleu hover:bg-bleu-clair">
              {etape.intention === "devoir" ? "Un devoir" : "Réviser"}
            </button>
            {etape.matiere && (
              <>
                <span>›</span>
                <span className="rounded-lg px-2 py-1 font-semibold text-encre">{etape.matiere.nom}</span>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {/* ÉTAPE 1 : une seule question */}
        {!etape.intention && (
          <motion.section key="q" {...glisse}>
            <p className="text-lg text-gris">{salut} {ELEVE.prenom} 👋</p>
            <h1 className="mt-1 text-[38px] font-bold leading-tight">On fait quoi aujourd'hui ?</h1>

            <div className="mt-8 grid grid-cols-2 gap-5">
              <GrandeCarte
                Icone={PenLine} titre="J'ai un devoir" sousTitre="Jules t'aide à le faire toi-même, étape par étape."
                couleur="bg-bleu" onClick={() => setEtape({ intention: "devoir" })}
              />
              <GrandeCarte
                Icone={BookOpen} titre="Je révise" sousTitre="Une fiche, puis des exercices corrigés tout de suite."
                couleur="bg-francais" onClick={() => setEtape({ intention: "reviser" })}
              />
            </div>

            <h2 className="mt-12 mb-3 text-[15px] font-semibold uppercase tracking-wide text-gris">Jules te propose</h2>
            <div className="grid grid-cols-2 gap-4">
              <Suggestion
                Icone={Clock} badge="Reprendre" teinte="bleu"
                {...trouver(REPRISE.matiere, REPRISE.chapitre)} detail={`Travaillé ${REPRISE.depuis}`}
                onClick={() => onLancer({ intention: "reviser", ...trouver(REPRISE.matiere, REPRISE.chapitre) })}
              />
              <Suggestion
                Icone={AlertTriangle} badge="À consolider" teinte="orange"
                {...trouver(FRAGILE.matiere, FRAGILE.chapitre)} detail={FRAGILE.raison}
                onClick={() => onLancer({ intention: "reviser", ...trouver(FRAGILE.matiere, FRAGILE.chapitre) })}
              />
            </div>
          </motion.section>
        )}

        {/* ÉTAPE 2 : matière */}
        {etape.intention && !etape.matiere && (
          <motion.section key="m" {...glisse}>
            <h1 className="text-[32px] font-bold leading-tight">
              {etape.intention === "devoir" ? "C'est un devoir de quoi ?" : "Tu veux réviser quoi ?"}
            </h1>
            <div className="mt-7 grid grid-cols-3 gap-4">
              {MATIERES.map((m, i) => {
                const fragiles = m.chapitres.filter((c) => c.etat === "fragile").length
                return (
                  <motion.button
                    key={m.id}
                    initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                    whileHover={{ y: -4, boxShadow: "var(--shadow-relief-haut)" }} whileTap={{ scale: 0.98 }}
                    onClick={() => setEtape({ ...etape, matiere: m })}
                    className="flex items-center gap-4 rounded-2xl border border-bord bg-white p-4 text-left shadow-relief"
                  >
                    <span className={cn("size-3 shrink-0 rounded-full", m.couleur)} />
                    <span className="flex-1">
                      <b className="block font-titre text-lg">{m.nom}</b>
                      <span className="text-[14px] text-gris">{m.chapitres.length} chapitres{fragiles ? ` · ${fragiles} à revoir` : ""}</span>
                    </span>
                    <ArrowRight size={18} className="text-gris" />
                  </motion.button>
                )
              })}
            </div>
          </motion.section>
        )}

        {/* ÉTAPE 3 : chapitre */}
        {etape.intention && etape.matiere && (
          <motion.section key="c" {...glisse}>
            <div className="flex items-center gap-3">
              <span className={cn("size-3 rounded-full", etape.matiere.couleur)} />
              <h1 className="text-[32px] font-bold leading-tight">{etape.matiere.nom} · quel chapitre ?</h1>
            </div>
            <div className="mt-7 grid grid-cols-2 gap-3">
              {etape.matiere.chapitres.map((c, i) => (
                <motion.button
                  key={c.id}
                  initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.035 }}
                  whileHover={{ y: -3, boxShadow: "var(--shadow-relief-haut)" }} whileTap={{ scale: 0.98 }}
                  onClick={() => onLancer({ intention: etape.intention!, matiere: etape.matiere!, chapitre: c })}
                  className="flex items-center gap-3 rounded-2xl border border-bord bg-white px-4 py-3.5 text-left shadow-relief"
                >
                  <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-[#ECEAF6] font-titre font-bold text-bleu">{i + 1}</span>
                  <span className="flex-1 font-medium leading-snug">{c.titre}</span>
                  <Etat etat={c.etat} />
                </motion.button>
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  )
}

function GrandeCarte({ Icone, titre, sousTitre, couleur, onClick }: {
  Icone: typeof PenLine; titre: string; sousTitre: string; couleur: string; onClick: () => void
}) {
  return (
    <motion.button
      whileHover={{ y: -5, boxShadow: "var(--shadow-relief-haut)" }} whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      onClick={onClick}
      className="group relative overflow-hidden rounded-3xl border border-bord bg-white p-7 text-left shadow-relief"
    >
      <span className={cn("absolute -top-10 -right-10 size-36 rounded-full opacity-10 transition-transform duration-500 group-hover:scale-150", couleur)} />
      <span className={cn("grid size-14 place-items-center rounded-2xl text-white shadow-relief", couleur)}>
        <Icone size={28} />
      </span>
      <b className="mt-5 block font-titre text-[26px] font-bold">{titre}</b>
      <span className="mt-1 block text-gris">{sousTitre}</span>
      <span className="mt-5 inline-flex items-center gap-1 font-semibold text-bleu">
        C'est parti <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
      </span>
    </motion.button>
  )
}

function Suggestion({ Icone, badge, teinte, matiere, chapitre, detail, onClick }: {
  Icone: typeof Clock; badge: string; teinte: "bleu" | "orange"; matiere: Matiere; chapitre: Chapitre; detail: string; onClick: () => void
}) {
  return (
    <motion.button
      whileHover={{ y: -3, boxShadow: "var(--shadow-relief-haut)" }} whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="flex items-start gap-4 rounded-2xl border border-bord bg-white p-4 text-left shadow-relief"
    >
      <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", teinte === "bleu" ? "bg-bleu-clair text-bleu" : "bg-[#FDEEDC] text-orange")}>
        <Icone size={20} />
      </span>
      <span className="flex-1">
        <span className={cn("text-[13px] font-semibold uppercase tracking-wide", teinte === "bleu" ? "text-bleu" : "text-orange")}>{badge}</span>
        <b className="block leading-snug">{chapitre.titre}</b>
        <span className="text-[14px] text-gris">{matiere.nom} · {detail}</span>
      </span>
      <Sparkles size={18} className="mt-1 text-gris/60" />
    </motion.button>
  )
}

function Etat({ etat }: { etat: Chapitre["etat"] }) {
  if (etat === "acquis") return <span className="flex items-center gap-1 text-[13px] font-semibold text-vert"><Check size={14} /> acquis</span>
  if (etat === "fragile") return <span className="flex items-center gap-1 text-[13px] font-semibold text-orange"><AlertTriangle size={14} /> à revoir</span>
  if (etat === "en-cours") return <span className="text-[13px] font-semibold text-bleu">en cours</span>
  return <span className="text-[13px] text-gris">nouveau</span>
}
