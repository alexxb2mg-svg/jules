// Révision des cartes mémoire (paliers 1-3-7-15-30-60 j, jules/revisions.py) : une carte à la fois, recto,
// « retourner » (le verso vient de GET supports/<id>, comme dans le contrat §3), puis raté / difficile / facile.
import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ChevronLeft, PartyPopper, RotateCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { studio, type CarteDue, type ReponseCarte } from "@/api/jules"
import { REPONSES_CARTE } from "./config"

export function Revision({ onRetour }: { onRetour: () => void }) {
  const [cartes, setCartes] = useState<CarteDue[] | null>(null)
  const [i, setI] = useState(0)
  const [verso, setVerso] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [bilan, setBilan] = useState<Record<ReponseCarte, number>>({ facile: 0, difficile: 0, rate: 0 })

  useEffect(() => { studio.revisions().then((r) => setCartes(r.cartes)).catch((e) => setErreur(e.message)) }, [])

  const carte = cartes?.[i]
  const retourner = async () => {
    if (!carte || verso !== null) return
    try {
      const r = await studio.lire(carte.support)
      setVerso(r.support.contenu.cartes?.find((c) => c.id === carte.carte_id)?.verso ?? "…")
    } catch (e) { setErreur((e as Error).message) }
  }
  const repondre = async (reponse: ReponseCarte) => {
    if (!carte || envoi) return
    setEnvoi(true); setErreur(null)
    try {
      await studio.repondreCarte(carte.support, carte.carte_id, reponse)
      setBilan((b) => ({ ...b, [reponse]: b[reponse] + 1 }))
      setVerso(null); setI((x) => x + 1)
    } catch (e) { setErreur((e as Error).message) } finally { setEnvoi(false) }
  }

  useEffect(() => {
    const touche = (e: KeyboardEvent) => {
      if (e.key === " " || e.key === "Enter") { if (verso === null) { e.preventDefault(); retourner() } }
      else if (verso !== null && ["1", "2", "3"].includes(e.key)) repondre(REPONSES_CARTE[Number(e.key) - 1]!.id)
    }
    addEventListener("keydown", touche)
    return () => removeEventListener("keydown", touche)
  })

  const total = cartes?.length ?? 0
  const fini = cartes !== null && i >= total

  return (
    <div className="flex h-full flex-col bg-[radial-gradient(ellipse_at_top,var(--j-bleu-clair),transparent_60%)]">
      <header className="flex items-center gap-3 px-5 pt-4 pl-16 md:px-10">
        <button onClick={onRetour} className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-[0.9rem] font-semibold text-bleu hover:bg-white">
          <ChevronLeft size={16} /> Exercices et supports
        </button>
        {total > 0 && !fini && (
          <div className="ml-auto flex items-center gap-3">
            <span className="text-[0.88rem] font-semibold text-gris">{i + 1} / {total}</span>
            <div className="h-2 w-40 overflow-hidden rounded-full bg-bord">
              <motion.div className="h-full rounded-full bg-bleu" animate={{ width: `${(i / total) * 100}%` }} />
            </div>
          </div>
        )}
      </header>

      <div className="grid flex-1 place-items-center px-5 pb-10">
        {erreur && <p className="text-rouge">{erreur}</p>}
        {cartes === null && !erreur && <div className="size-10 animate-spin rounded-full border-4 border-bord border-t-bleu" />}
        {cartes !== null && total === 0 && <p className="text-gris">Aucune carte à revoir aujourd'hui. Reviens demain !</p>}

        <AnimatePresence mode="wait">
          {carte && (
            <motion.div key={`${carte.support}-${carte.carte_id}`} className="flex w-full max-w-[560px] flex-col items-center gap-6"
              initial={{ opacity: 0, x: 60, rotate: 3 }} animate={{ opacity: 1, x: 0, rotate: 0 }} exit={{ opacity: 0, x: -80, rotate: -4 }}
              transition={{ type: "spring", stiffness: 260, damping: 26 }}>
              <p className="m-0 text-[0.9rem] font-semibold text-gris">{carte.notion}</p>
              <button onClick={retourner} aria-label={verso === null ? "Retourner la carte" : "Carte retournée"}
                className="w-full [perspective:1200px]">
                <motion.div animate={{ rotateY: verso === null ? 0 : 180 }} transition={{ type: "spring", stiffness: 200, damping: 22 }}
                  className="relative h-[280px] w-full [transform-style:preserve-3d]">
                  <div className="absolute inset-0 grid place-items-center rounded-[28px] bg-white p-8 text-center shadow-relief-haut [backface-visibility:hidden]">
                    <p className="m-0 text-[1.5rem] leading-snug font-bold text-encre">{carte.recto}</p>
                    <span className="absolute bottom-5 inline-flex items-center gap-1.5 text-[0.85rem] font-semibold text-gris"><RotateCw size={14} /> Clique ou Espace pour retourner</span>
                  </div>
                  <div className="absolute inset-0 grid [transform:rotateY(180deg)] place-items-center rounded-[28px] border-4 border-bleu bg-white p-8 text-center shadow-relief-haut [backface-visibility:hidden]">
                    <p className="m-0 text-[1.3rem] leading-snug text-encre">{verso}</p>
                  </div>
                </motion.div>
              </button>
              <div className={cn("grid w-full grid-cols-3 gap-3 transition-opacity", verso === null && "pointer-events-none opacity-0")}>
                {REPONSES_CARTE.map((r, k) => (
                  <motion.button key={r.id} whileTap={{ scale: 0.95 }} disabled={envoi || verso === null} onClick={() => repondre(r.id)}
                    className={cn("flex flex-col items-center rounded-2xl border-2 px-3 py-3 font-bold", r.classe)}>
                    {r.texte}<small className="font-normal opacity-80">{r.aide} · {k + 1}</small>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
          {fini && total > 0 && (
            <motion.div key="fin" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center gap-3 text-center">
              <motion.span initial={{ rotate: -30, scale: 0 }} animate={{ rotate: 0, scale: 1 }} transition={{ type: "spring", stiffness: 240, damping: 12 }}
                className="grid size-20 place-items-center rounded-full bg-bleu text-white"><PartyPopper size={38} /></motion.span>
              <p className="m-0 text-[1.8rem] font-bold text-encre">Révision du jour terminée</p>
              <p className="m-0 text-gris">{bilan.facile} facile{bilan.facile > 1 ? "s" : ""} · {bilan.difficile} difficile{bilan.difficile > 1 ? "s" : ""} · {bilan.rate} raté{bilan.rate > 1 ? "s" : ""}</p>
              <p className="m-0 max-w-[420px] text-[0.95rem] text-gris">Les cartes ratées reviennent demain, les autres plus tard : c'est l'espacement qui fait tenir la mémoire.</p>
              <button onClick={onRetour} className="mt-2 rounded-full bg-bleu px-5 py-2.5 font-semibold text-white shadow-relief">Retour au studio</button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
