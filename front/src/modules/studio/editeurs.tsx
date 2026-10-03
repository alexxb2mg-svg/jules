// Un éditeur par type de support (docs/STUDIO-CONTRAT.md §1 et §6). Trame VIDE : aucun texte n'est pré-rempli,
// seuls des emplacements et des questions d'aide. Chaque champ s'enregistre quand l'élève le quitte (route
// ecrire) ; le serveur valide chemin et taille. Registre EDITEURS : type → composant.
import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { CornerDownRight, Plus, RotateCw } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Noeud, Support, TypeSupport } from "@/api/jules"
import { TAILLE_CHAMP_MAX, TYPES } from "./config"

export type Chemin = (string | number)[]
export type PropsEditeur = {
  support: Support
  verrouille: boolean
  ecrire: (chemin: Chemin, valeur: string) => Promise<void>
  ajouter: (parent?: string | null) => Promise<void>
  rattacher: (index: number, parent: string | null) => Promise<void>
}

/* ---- champ texte : enregistré au blur, compteur 200, jamais de valeur pré-remplie ---- */
export function Champ({ valeur, chemin, ecrire, verrouille, placeholder, zone, label, className, autoFocus }: {
  valeur: string; chemin: Chemin; ecrire: PropsEditeur["ecrire"]; verrouille: boolean
  placeholder: string; zone?: boolean; label: string; className?: string; autoFocus?: boolean
}) {
  const [v, setV] = useState(valeur)
  const [etat, setEtat] = useState<"" | "envoi" | "ok" | "erreur">("")
  const envoye = useRef(valeur)
  const courant = useRef(valeur) // valeur réelle du champ, même si le blur arrive avant le rendu
  useEffect(() => { setV(valeur); envoye.current = valeur; courant.current = valeur }, [valeur])
  const enregistrer = async () => {
    const propre = courant.current.trim()
    if (propre === envoye.current.trim()) return
    setEtat("envoi")
    try { await ecrire(chemin, propre); envoye.current = propre; setEtat("ok"); setTimeout(() => setEtat(""), 1200) } catch { setEtat("erreur") }
  }
  const commun = {
    value: v, disabled: verrouille, maxLength: TAILLE_CHAMP_MAX, placeholder, "aria-label": label, autoFocus,
    onChange: (e: React.ChangeEvent<HTMLInputElement & HTMLTextAreaElement>) => { courant.current = e.target.value; setV(e.target.value) },
    onBlur: enregistrer,
    className: cn("w-full resize-none rounded-xl border-2 border-transparent bg-transparent px-2.5 py-1.5 outline-none transition-colors",
      "placeholder:text-gris/60 hover:border-bord focus:border-(--m-accent) focus:bg-card disabled:hover:border-transparent", className),
  }
  const reste = TAILLE_CHAMP_MAX - v.length
  return (
    <div className="group/champ relative">
      {zone
        ? <textarea rows={Math.min(6, Math.max(2, Math.ceil(v.length / 60)))} {...commun} />
        : <input type="text" {...commun} onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()} />}
      {!verrouille && (
        <span className={cn("pointer-events-none absolute right-2 -bottom-4 text-[0.72rem] opacity-0 transition-opacity group-focus-within/champ:opacity-100",
          reste < 20 ? "text-rouge" : "text-gris", etat === "erreur" && "text-rouge opacity-100")}>
          {etat === "envoi" ? "…" : etat === "erreur" ? "Pas enregistré, réessaie" : `${v.length} / ${TAILLE_CHAMP_MAX}`}
        </span>
      )}
      <AnimatePresence>{etat === "ok" && (
        <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="pointer-events-none absolute top-1/2 right-2 -translate-y-1/2 text-[0.75rem] font-semibold text-vert">enregistré</motion.span>
      )}</AnimatePresence>
    </div>
  )
}

function BoutonAjouter({ texte, onClick, petit }: { texte: string; onClick: () => void; petit?: boolean }) {
  return (
    <motion.button type="button" whileTap={{ scale: 0.97 }} onClick={onClick}
      className={cn("inline-flex items-center gap-1.5 rounded-full border-2 border-dashed border-(--m-accent)/40 font-semibold text-(--m-texte) transition-colors hover:border-(--m-accent) hover:bg-(--m-fond)",
        petit ? "px-3 py-1 text-[0.85rem]" : "px-4 py-2 text-[0.95rem]")}>
      <Plus size={petit ? 14 : 16} /> {texte}
    </motion.button>
  )
}

const apparition = { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, scale: 0.97 } }

/* ---- fiche : sections empilées ---- */
function Fiche({ support, verrouille, ecrire, ajouter }: PropsEditeur) {
  const sections = support.contenu.sections || []
  return (
    <div className="flex flex-col gap-4">
      <AnimatePresence initial={false}>
        {sections.map((s, i) => (
          <motion.section key={s.id} layout {...apparition} className="rounded-surface bg-card p-3 shadow-relief">
            <div className="flex items-center gap-2">
              <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-(--m-fond) text-[0.85rem] font-bold text-(--m-texte)">{i + 1}</span>
              <Champ valeur={s.titre} chemin={["sections", i, "titre"]} ecrire={ecrire} verrouille={verrouille} label={`Titre de la section ${i + 1}`}
                placeholder="Titre de la section" className="text-[1.05rem] font-bold" autoFocus={!s.titre && i === sections.length - 1} />
            </div>
            <div className="mt-1 pl-9">
              <Champ zone valeur={s.contenu} chemin={["sections", i, "contenu"]} ecrire={ecrire} verrouille={verrouille} label={`Contenu de la section ${i + 1}`}
                placeholder="Ce que tu en retiens, avec tes mots…" className="text-[0.98rem] leading-relaxed" />
            </div>
          </motion.section>
        ))}
      </AnimatePresence>
      {!verrouille && <div><BoutonAjouter texte={TYPES.fiche.ajouter} onClick={() => ajouter()} /></div>}
    </div>
  )
}

/* ---- quiz : questions/réponses écrites par l'élève, jamais corrigées automatiquement ---- */
function Quiz({ support, verrouille, ecrire, ajouter }: PropsEditeur) {
  const questions = support.contenu.questions || []
  return (
    <div className="flex flex-col gap-3">
      <AnimatePresence initial={false}>
        {questions.map((q, i) => (
          <motion.div key={q.id} layout {...apparition} className="grid gap-1 rounded-surface bg-card p-3 shadow-relief sm:grid-cols-[1fr_1fr] sm:gap-3">
            <div className="flex items-start gap-2">
              <span className="mt-1.5 grid size-7 shrink-0 place-items-center rounded-full bg-(--m-accent) text-[0.8rem] font-bold text-white">Q{i + 1}</span>
              <Champ zone valeur={q.question} chemin={["questions", i, "question"]} ecrire={ecrire} verrouille={verrouille} label={`Question ${i + 1}`}
                placeholder="Ta question…" className="font-semibold" autoFocus={!q.question && i === questions.length - 1} />
            </div>
            <div className="flex items-start gap-2 sm:border-l sm:border-bord sm:pl-3">
              <span className="mt-1.5 grid size-7 shrink-0 place-items-center rounded-full bg-(--m-fond) text-[0.8rem] font-bold text-(--m-texte)">R</span>
              <Champ zone valeur={q.reponse} chemin={["questions", i, "reponse"]} ecrire={ecrire} verrouille={verrouille} label={`Réponse ${i + 1}`}
                placeholder="Ta réponse…" />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      {!verrouille && <div><BoutonAjouter texte={TYPES.quiz.ajouter} onClick={() => ajouter()} /></div>}
    </div>
  )
}

/* ---- cartes mémoire : recto | verso, aperçu retournable ---- */
function CartesMemoire({ support, verrouille, ecrire, ajouter }: PropsEditeur) {
  const cartes = support.contenu.cartes || []
  const [retournee, setRetournee] = useState<string | null>(null)
  return (
    <div className="flex flex-col gap-3">
      <AnimatePresence initial={false}>
        {cartes.map((c, i) => (
          <motion.div key={c.id} layout {...apparition} className="rounded-surface bg-card p-3 shadow-relief">
            <div className="mb-1 flex items-center justify-between px-1">
              <span className="text-[0.8rem] font-semibold text-gris">Carte {i + 1}</span>
              {verrouille && (
                <button type="button" onClick={() => setRetournee(retournee === c.id ? null : c.id)}
                  className="inline-flex items-center gap-1 text-[0.8rem] font-semibold text-(--m-texte)"><RotateCw size={13} /> Retourner</button>
              )}
            </div>
            {verrouille ? (
              <div className="[perspective:900px]">
                <motion.div animate={{ rotateY: retournee === c.id ? 180 : 0 }} transition={{ type: "spring", stiffness: 260, damping: 24 }}
                  className="relative min-h-[84px] [transform-style:preserve-3d]">
                  <p className="absolute inset-0 m-0 grid place-items-center rounded-xl bg-(--m-fond) p-3 text-center font-semibold [backface-visibility:hidden]">{c.recto}</p>
                  <p className="absolute inset-0 m-0 grid [transform:rotateY(180deg)] place-items-center rounded-xl border-2 border-(--m-accent) p-3 text-center [backface-visibility:hidden]">{c.verso}</p>
                </motion.div>
              </div>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="rounded-xl bg-(--m-fond) p-1.5">
                  <p className="m-0 px-2.5 pt-1 text-[0.72rem] font-bold tracking-wide text-(--m-texte) uppercase">Recto</p>
                  <Champ zone valeur={c.recto} chemin={["cartes", i, "recto"]} ecrire={ecrire} verrouille={verrouille} label={`Recto de la carte ${i + 1}`}
                    placeholder="Une question, un mot…" className="font-semibold" autoFocus={!c.recto && i === cartes.length - 1} />
                </div>
                <div className="rounded-xl border-2 border-dashed border-bord p-1.5">
                  <p className="m-0 px-2.5 pt-1 text-[0.72rem] font-bold tracking-wide text-gris uppercase">Verso</p>
                  <Champ zone valeur={c.verso} chemin={["cartes", i, "verso"]} ecrire={ecrire} verrouille={verrouille} label={`Verso de la carte ${i + 1}`}
                    placeholder="Ce qu'il faut retrouver" />
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
      {!verrouille && <div><BoutonAjouter texte={TYPES.cartes_memoire.ajouter} onClick={() => ajouter()} /></div>}
    </div>
  )
}

/* ---- carte mentale : idée(s) au centre, branches, sous-branches ---- */
// Composant de niveau module (pas défini dans le rendu) : un champ garde son état et son focus entre deux saves.
type Arbre = PropsEditeur & { index: Map<string, number>; enfants: (p: string | null) => Noeud[] }

function Branche({ id, niveau, arbre }: { id: string; niveau: number; arbre: Arbre }) {
  const { support, verrouille, ecrire, ajouter, index, enfants } = arbre
  const noeuds = support.contenu.noeuds || []
  const i = index.get(id)!
  const n = noeuds[i]!
  const sous = enfants(id)
  return (
    <motion.li layout {...apparition} className="relative list-none">
      <div className={cn("flex items-center gap-1.5", niveau > 1 && "pl-1")}>
        {niveau > 1 && <CornerDownRight size={15} className="shrink-0 text-(--m-accent)/60" />}
        <Champ zone valeur={n.texte} chemin={["noeuds", i, "texte"]} ecrire={ecrire} verrouille={verrouille} label={`Branche ${i + 1}`}
          placeholder={niveau === 1 ? "Une grande idée…" : "Un détail, un exemple…"}
          className={niveau === 1 ? "font-bold text-(--m-texte)" : "text-[0.95rem]"} autoFocus={!n.texte && i === noeuds.length - 1} />
      </div>
      {(sous.length > 0 || (!verrouille && niveau < 3)) && (
        <ul className="m-0 ml-3 flex flex-col gap-1 border-l-2 border-(--m-accent)/20 py-1 pl-3">
          <AnimatePresence initial={false}>{sous.map((s) => <Branche key={s.id} id={s.id} niveau={niveau + 1} arbre={arbre} />)}</AnimatePresence>
          {!verrouille && niveau < 3 && <li className="list-none"><BoutonAjouter petit texte={niveau === 1 ? "sous-idée" : "détail"} onClick={() => ajouter(id)} /></li>}
        </ul>
      )}
    </motion.li>
  )
}

function CarteMentale(props: PropsEditeur) {
  const { support, verrouille, ecrire, ajouter } = props
  const noeuds = support.contenu.noeuds || []
  const index = new Map(noeuds.map((n, i) => [n.id, i]))
  const enfants = (p: string | null) => noeuds.filter((n) => (n.parent || null) === p)
  const arbre: Arbre = { ...props, index, enfants }
  const racines = enfants(null)

  return (
    <div className="flex flex-col gap-6">
      {racines.map((r) => {
        const i = index.get(r.id)!
        return (
          <div key={r.id} className="flex flex-col items-center gap-5">
            <motion.div layout className="w-full max-w-[420px] rounded-3xl bg-(--m-texte) px-3 py-2 text-center text-white shadow-relief-haut">
              <Champ valeur={r.texte} chemin={["noeuds", i, "texte"]} ecrire={ecrire} verrouille={verrouille} label="Idée centrale"
                placeholder="L'idée centrale" className="text-center text-[1.2rem] font-bold text-white placeholder:text-white/60 hover:border-white/30 focus:border-white focus:bg-white/10"
                autoFocus={!r.texte} />
            </motion.div>
            <ul className="m-0 grid w-full grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-3 p-0">
              <AnimatePresence initial={false}>
                {enfants(r.id).map((b) => (
                  <div key={b.id} className="rounded-2xl border-2 border-(--m-accent)/30 bg-card p-2 shadow-relief">
                    <Branche id={b.id} niveau={1} arbre={arbre} />
                  </div>
                ))}
              </AnimatePresence>
              {!verrouille && (
                <li className="grid min-h-[80px] list-none place-items-center rounded-2xl border-2 border-dashed border-(--m-accent)/30">
                  <BoutonAjouter texte="Nouvelle branche" onClick={() => ajouter(r.id)} />
                </li>
              )}
            </ul>
          </div>
        )
      })}
      {!verrouille && racines.length === 0 && <div className="text-center"><BoutonAjouter texte="Écrire l'idée centrale" onClick={() => ajouter(null)} /></div>}
    </div>
  )
}

export const EDITEURS: Record<TypeSupport, (p: PropsEditeur) => React.ReactNode> = {
  fiche: Fiche,
  quiz: Quiz,
  cartes_memoire: CartesMemoire,
  carte_mentale: CarteMentale,
}
