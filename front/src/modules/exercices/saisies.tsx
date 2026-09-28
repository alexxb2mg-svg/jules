// Une saisie par type d'exercice des fiches v2 (docs/FICHES-V2.md, jules/fiches/parcours.py presenter()).
// Le composant ne connaît jamais la bonne réponse : il fabrique ce que l'élève propose, le serveur tranche.
import { useState } from "react"
import { motion, Reorder } from "framer-motion"
import { ArrowDown, ArrowUp, Check, GripVertical } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ExerciceVue, OptionExercice, ReponseExercice } from "@/api/jules"
import { Riche } from "@/modules/fiches/texte"

export type PropsSaisie = {
  exercice: ExerciceVue
  bloque: boolean
  onRepondre: (reponse: ReponseExercice) => void
}
type Saisie = (p: PropsSaisie) => React.ReactNode

const bouton = "inline-flex items-center justify-center gap-1.5 rounded-full bg-(--m-texte) px-5 py-2.5 text-[0.95rem] font-semibold text-white shadow-relief transition disabled:opacity-40"

function Valider({ actif, onClick }: { actif: boolean; onClick: () => void }) {
  return (
    <motion.button type="button" whileTap={{ scale: 0.96 }} disabled={!actif} onClick={onClick} className={bouton}>
      <Check size={17} /> Valider
    </motion.button>
  )
}

/* ---- nombre, expression, texte court : une ligne libre, l'aide de format du serveur dessous ---- */
function Libre({ exercice, bloque, onRepondre }: PropsSaisie) {
  const [texte, setTexte] = useState("")
  const envoyer = () => { if (texte.trim() && !bloque) { onRepondre(texte.trim()); setTexte("") } }
  return (
    <form onSubmit={(e) => { e.preventDefault(); envoyer() }} className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        <input value={texte} onChange={(e) => setTexte(e.target.value)} disabled={bloque} autoComplete="off" spellCheck={exercice.type === "texte_court"}
          aria-label="Ta réponse" placeholder="Ta réponse"
          className="min-w-0 flex-1 rounded-2xl border-2 border-bord bg-white px-4 py-2.5 text-[1.05rem] outline-none focus:border-(--m-accent)" />
        <Valider actif={!!texte.trim() && !bloque} onClick={envoyer} />
      </div>
      {exercice.aide_format && <p className="m-0 text-[0.85rem] text-gris">{exercice.aide_format}</p>}
    </form>
  )
}

/* ---- choix : cartes à cocher ; une seule ou plusieurs selon « plusieurs » ---- */
function Choix({ exercice, bloque, onRepondre }: PropsSaisie) {
  const [pris, setPris] = useState<string[]>([])
  const plusieurs = !!exercice.plusieurs
  const basculer = (id: string) => {
    if (bloque) return
    if (!plusieurs) { onRepondre([id]); return }
    setPris((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))
  }
  return (
    <div className="flex flex-col gap-3">
      {plusieurs && <p className="m-0 text-[0.85rem] font-semibold text-(--m-texte)">Plusieurs réponses possibles.</p>}
      <div className="grid gap-2.5 sm:grid-cols-2">
        {(exercice.options || []).map((o, i) => {
          const on = pris.includes(o.id)
          return (
            <motion.button key={o.id} type="button" disabled={bloque} onClick={() => basculer(o.id)}
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} aria-pressed={on}
              className={cn("flex items-start gap-3 rounded-2xl border-2 bg-white px-4 py-3 text-left text-[0.98rem] leading-snug transition-colors",
                on ? "border-(--m-accent) bg-(--m-fond)" : "border-bord hover:border-(--m-accent)/50")}>
              <span className={cn("grid size-7 shrink-0 place-items-center rounded-full text-[0.85rem] font-bold uppercase",
                on ? "bg-(--m-accent) text-white" : "bg-nav text-(--m-texte)")}>{o.id}</span>
              <span className="pt-0.5"><Riche texte={o.texte} /></span>
            </motion.button>
          )
        })}
      </div>
      {plusieurs && <div><Valider actif={pris.length > 0 && !bloque} onClick={() => onRepondre([...pris].sort())} /></div>}
    </div>
  )
}

/* ---- ordre : liste à glisser (ou flèches, au clavier) ---- */
function Ordre({ exercice, bloque, onRepondre }: PropsSaisie) {
  const [liste, setListe] = useState<OptionExercice[]>(exercice.elements || [])
  const deplacer = (i: number, d: number) => {
    const j = i + d
    if (j < 0 || j >= liste.length) return
    const n = [...liste]; [n[i], n[j]] = [n[j]!, n[i]!]; setListe(n)
  }
  return (
    <div className="flex flex-col gap-3">
      <p className="m-0 text-[0.85rem] text-gris">Glisse les étiquettes (ou utilise les flèches) pour les remettre dans l'ordre.</p>
      <Reorder.Group axis="y" values={liste} onReorder={setListe} className="m-0 flex list-none flex-col gap-2 p-0">
        {liste.map((e, i) => (
          <Reorder.Item key={e.id} value={e} dragListener={!bloque}
            className="flex cursor-grab items-center gap-3 rounded-2xl border-2 border-bord bg-white px-3 py-2.5 active:cursor-grabbing"
            whileDrag={{ scale: 1.02, boxShadow: "var(--shadow-relief-haut)" }}>
            <GripVertical size={18} className="shrink-0 text-gris" aria-hidden />
            <span className="grid size-7 shrink-0 place-items-center rounded-full bg-(--m-fond) text-[0.85rem] font-bold text-(--m-texte)">{i + 1}</span>
            <span className="flex-1 text-[0.98rem] leading-snug"><Riche texte={e.texte} /></span>
            <span className="flex shrink-0 flex-col">
              <button type="button" aria-label="Monter" disabled={bloque || i === 0} onClick={() => deplacer(i, -1)} className="rounded p-0.5 text-gris hover:text-encre disabled:opacity-25"><ArrowUp size={15} /></button>
              <button type="button" aria-label="Descendre" disabled={bloque || i === liste.length - 1} onClick={() => deplacer(i, 1)} className="rounded p-0.5 text-gris hover:text-encre disabled:opacity-25"><ArrowDown size={15} /></button>
            </span>
          </Reorder.Item>
        ))}
      </Reorder.Group>
      <div><Valider actif={!bloque} onClick={() => onRepondre(liste.map((e) => e.id))} /></div>
    </div>
  )
}

/* ---- association : pour chaque élément de gauche, choisir sa case de droite ---- */
function Association({ exercice, bloque, onRepondre }: PropsSaisie) {
  const gauche = exercice.gauche || []
  const droite = exercice.droite || []
  const [paires, setPaires] = useState<Record<string, string>>({})
  const complet = gauche.every((g) => paires[g.id])
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-2">
        {gauche.map((g) => (
          <div key={g.id} className="flex flex-col gap-2 rounded-2xl border-2 border-bord bg-white px-4 py-3">
            <span className="text-[0.98rem] leading-snug font-medium"><Riche texte={g.texte} /></span>
            <div className="flex shrink-0 flex-wrap gap-1.5" role="radiogroup" aria-label={g.texte}>
              {droite.map((d) => {
                const on = paires[g.id] === d.id
                return (
                  <motion.button key={d.id} type="button" role="radio" aria-checked={on} disabled={bloque} whileTap={{ scale: 0.95 }}
                    onClick={() => setPaires((p) => ({ ...p, [g.id]: d.id }))}
                    className={cn("rounded-full border-2 px-3 py-1 text-[0.88rem] font-semibold transition-colors",
                      on ? "border-(--m-accent) bg-(--m-accent) text-white" : "border-bord text-(--m-texte) hover:border-(--m-accent)/60")}>
                    {d.texte}
                  </motion.button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
      <div><Valider actif={complet && !bloque} onClick={() => onRepondre(paires)} /></div>
    </div>
  )
}

/** Registre type d'exercice → saisie. Un type inconnu n'est pas affiché (voir Entrainement). */
export const SAISIES: Record<string, Saisie> = {
  nombre: Libre,
  expression: Libre,
  texte_court: Libre,
  choix: Choix,
  ordre: Ordre,
  association: Association,
}
