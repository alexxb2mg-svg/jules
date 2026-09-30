// Registre des rendus d'une fiche visuelle : un composant par type de bloc de SCHEMA-FICHE-VISUELLE.md.
// La logique est celle de jules/web/static/accueil.js (CONSTRUCTEURS) ; seul l'habillage change.
// Ajouter un type = l'ajouter au schéma et au validateur côté serveur, puis une entrée dans RENDUS.
import { useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react"
import { AnimatePresence, motion } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import { Dumbbell, Lightbulb, ListOrdered, Network, Shapes, SlidersHorizontal, Sigma, TriangleAlert, Check, X, ArrowRight, Maximize2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import type {
  BlocCarte, BlocExemple, BlocFiche, BlocFormule, BlocGraphe, BlocMethode, BlocPiege, BlocRenfort, BlocSchema, LienRenfort, TypeBloc,
} from "./types"
import { Riche, typo } from "./texte"
import { disposerCarte, T_LIEN, T_SOUS, T_TITRE, H_SOUS, H_TITRE } from "./carte"
import { couleurCss, dessinerGabarit, evaluerCondition } from "./ponts"

/** Titres par défaut (repris de accueil.js) et icône de chaque type. */
export const TYPES: Partial<Record<TypeBloc, { titre: string; Icone: LucideIcon }>> = {
  formule: { titre: "L'essentiel en une ligne", Icone: Sigma },
  carte: { titre: "Comment les notions s'articulent", Icone: Network },
  graphe: { titre: "Vois la notion bouger", Icone: SlidersHorizontal },
  methode: { titre: "La méthode, étape par étape", Icone: ListOrdered },
  piege: { titre: "Le piège classique", Icone: TriangleAlert },
  exemple: { titre: "Dans la vraie vie", Icone: Lightbulb },
  renfort: { titre: "Ensuite, pour ancrer", Icone: Dumbbell },
  schema: { titre: "Un schéma pour s'y retrouver", Icone: Shapes },
}

export type ContexteRendu = {
  /** Ouvre un outil d'un bloc renfort (ex. la leçon de la notion) ; absent = outil pas encore disponible. */
  ouvrirOutil: (lien: LienRenfort) => (() => void) | null
}

const apparition = {
  initial: { opacity: 0, y: 10 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-40px" },
}

/* ---------------------------------------------------------------- formule */
function Formule({ bloc }: { bloc: BlocFormule }) {
  const longueur = String(bloc.expression || "").replace(/[[\]]/g, "").length
  const termes = (bloc.ordre || Object.keys(bloc.termes || {})).map((nom) => [nom, bloc.termes?.[nom]] as const).filter(([, i]) => i)
  return (
    <div className="flex flex-wrap items-center gap-x-10 gap-y-5">
      <div data-formule className={cn("formule-expression font-serif leading-tight text-encre",
        longueur > 50 ? "text-[1.375rem]" : longueur > 32 ? "text-[1.5rem] md:text-[1.75rem]" : "text-[1.875rem] md:text-[2.625rem]")}>
        {String(bloc.expression || "").split(/(\[[^\]]+\])/).map((m, i) => {
          const t = m.match(/^\[([^\]]+)\]$/)
          return t ? <b key={i} style={{ color: couleurCss(bloc.termes?.[t[1]]?.couleur) }}>{t[1]}</b> : m
        })}
      </div>
      <div className="flex min-w-[min(240px,100%)] flex-1 flex-col gap-2.5">
        {termes.map(([nom, info], i) => (
          <motion.div key={nom} {...apparition} transition={{ delay: 0.08 * i }}
            className="rounded-r-xl border-l-4 bg-[#F8F9FC] py-2 pr-3 pl-3.5" style={{ borderColor: couleurCss(info!.couleur) }}>
            <b style={{ color: couleurCss(info!.couleur) }}>{nom}</b>{" "}<Riche texte={info!.legende} />
          </motion.div>
        ))}
      </div>
    </div>
  )
}

/* ---------------------------------------------------------------- carte */
/** Le dessin de la carte (SVG seul). `statique` : pas d'animation d'entrée (dans l'agrandissement). */
function CarteSvg({ d, className, statique }: { d: ReturnType<typeof disposerCarte>; className?: string; statique?: boolean }) {
  return (
  <svg viewBox={`0 0 ${d.largeur} ${d.hauteur}`} role="img" aria-label="Carte des notions" className={cn("mx-auto block w-full", className)}>
    {d.traits.map((t, i) => (
      <g key={i}>
        {t.forme === "ligne"
          ? <motion.line x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} stroke="#8A94A3" strokeWidth={2}
              initial={statique ? false : { pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={{ once: true }} transition={{ duration: 0.5, delay: 0.25 + 0.06 * i }} />
          : <motion.polyline points={t.points} fill="none" stroke="#8A94A3" strokeWidth={2}
              initial={statique ? false : { pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={{ once: true }} transition={{ duration: 0.6, delay: 0.3 + 0.06 * i }} />}
        {t.libelle && (
          <motion.text x={t.libelle.x} y={t.libelle.y} fontSize={T_LIEN} fill="#4A5566" textAnchor={t.libelle.ancre}
            paintOrder="stroke" stroke="#FFFFFF" strokeWidth={5} initial={statique ? false : { opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            transition={{ delay: 0.6 + 0.06 * i }}>{t.libelle.texte}</motion.text>
        )}
      </g>
    ))}
    {d.noeuds.map((p, i) => {
      const principal = Boolean(p.noeud.principal)
      let y = p.y - (p.titre.length * H_TITRE + p.sous.length * H_SOUS) / 2 + 15
      return (
        <motion.g key={p.noeud.id} className="carte-noeud" data-adresse={`carte/${p.noeud.id}`}
          style={{ transformOrigin: `${p.x}px ${p.y}px`, transformBox: "view-box" }}
          initial={statique ? false : { opacity: 0, scale: 0.85 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 260, damping: 22, delay: principal ? 0 : 0.12 + 0.07 * i }}
          whileHover={{ scale: 1.03 }}>
          <rect x={p.boite.gauche} y={p.boite.haut} width={p.boite.droite - p.boite.gauche} height={p.boite.bas - p.boite.haut} rx={14}
            fill={principal ? "var(--m-texte)" : "var(--m-fond)"} stroke={principal ? "var(--m-texte)" : "var(--m-accent)"} strokeWidth={principal ? 0 : 1.5} />
          {p.titre.map((l) => { const e = <text key={`t${y}`} x={p.x} y={y} fontSize={T_TITRE} fontWeight={700} textAnchor="middle" className="carte-titre" fill={principal ? "#FFFFFF" : "var(--m-texte)"}>{l}</text>; y += H_TITRE; return e })}
          {p.sous.map((l) => { const e = <text key={`s${y}`} x={p.x} y={y + 1} fontSize={T_SOUS} textAnchor="middle" fill={principal ? "rgba(255,255,255,.85)" : "#4A5566"}>{l}</text>; y += H_SOUS; return e })}
        </motion.g>
      )
    })}
  </svg>
  )
}

// Petit écran : la carte se réduit à la largeur de l'écran (vue d'ensemble) ; « Agrandir » l'ouvre dans un Dialog
// où elle garde une taille lisible (>= 11 px réels) et défile horizontalement si l'écran est plus étroit.
function Carte({ bloc }: { bloc: BlocCarte }) {
  const d = useMemo(() => disposerCarte(bloc), [bloc])
  const [ouvert, setOuvert] = useState(false)
  const bouton = useRef<HTMLButtonElement>(null)
  const [couleurs, setCouleurs] = useState<Record<string, string>>({})
  // Le dialog vit hors de la fiche (portail) : il ne voit pas les couleurs de la matière, on les lui recopie.
  const ouvrir = () => {
    const cs = bouton.current ? getComputedStyle(bouton.current) : null
    setCouleurs(Object.fromEntries(["--m-fond", "--m-texte", "--m-accent"].map((v) => [v, cs?.getPropertyValue(v).trim() ?? ""]).filter(([, v]) => v)))
    setOuvert(true)
  }
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <p data-carte-vue-ensemble className="text-sm text-gris md:hidden">Vue d'ensemble : touche « Agrandir » pour lire les textes.</p>
        <button ref={bouton} type="button" data-carte-agrandir onClick={(e) => { e.stopPropagation(); ouvrir() }}
          className="ml-auto inline-flex min-h-11 shrink-0 items-center gap-2 rounded-xl border border-bord bg-white px-3.5 text-sm font-semibold text-encre transition-colors hover:bg-(--m-fond) focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none">
          <Maximize2 size={16} aria-hidden="true" />Agrandir la carte
        </button>
      </div>
      <CarteSvg d={d} />
      <Dialog open={ouvert} onOpenChange={setOuvert}>
        <DialogContent libelleFermer="Fermer la carte" className="max-w-5xl" style={couleurs as CSSProperties}
          onCloseAutoFocus={(e) => { e.preventDefault(); bouton.current?.focus() }}
          onClick={(e) => { if (!(e.target as Element).closest?.("[data-adresse]")) e.stopPropagation(); else setOuvert(false) }}>
          <DialogHeader>
            <DialogTitle>Comment les notions s'articulent</DialogTitle>
            <DialogDescription className="min-[780px]:hidden" data-carte-indice>Fais défiler vers la droite pour voir toute la carte.</DialogDescription>
          </DialogHeader>
          <div data-carte-defilement tabIndex={0} aria-label="Carte des notions, à faire défiler" className="overflow-auto rounded-xl bg-white p-2 [scrollbar-width:thin]">
            <CarteSvg d={d} statique className="min-w-[700px]" />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

/* ---------------------------------------------------------------- graphe */
function Graphe({ bloc }: { bloc: BlocGraphe }) {
  const svg = useRef<SVGSVGElement>(null)
  const [valeurs, setValeurs] = useState<Record<string, number>>(() =>
    Object.fromEntries((bloc.curseurs || []).map((c) => [c.nom, Number(c.depart ?? c.min ?? 0)])))
  const [gabaritAbsent, setGabaritAbsent] = useState(false)
  useEffect(() => { setGabaritAbsent(!dessinerGabarit(svg.current, bloc.gabarit, valeurs)) }, [bloc.gabarit, valeurs])
  const lectures = (bloc.lectures || []).filter((l) => evaluerCondition(l.si, valeurs))
  return (
    <div className="grid items-start gap-6 md:grid-cols-[minmax(240px,340px)_1fr]" onClick={(e) => e.stopPropagation()}>
      <div className="rounded-2xl bg-[#F8F9FC] p-2">
        <svg ref={svg} className="figure block w-full" role="img" aria-label="Figure interactive" />
        {gabaritAbsent && <p className="p-3 text-sm text-gris">Figure indisponible.</p>}
      </div>
      <div>
        {(bloc.curseurs || []).map((c) => (
          <label key={c.id} className="mb-4 block">
            <span className="mb-1.5 flex items-baseline justify-between font-semibold">
              <span>{c.nom}</span>
              <motion.span key={valeurs[c.nom]} initial={{ scale: 1.25, color: "var(--m-accent)" }} animate={{ scale: 1, color: "var(--j-encre)" }}
                className="rounded-lg bg-white px-2.5 py-0.5 font-titre text-lg tabular-nums shadow-relief">
                {String(valeurs[c.nom]).replace(".", ",")}
              </motion.span>
            </span>
            <input type="range" min={c.min} max={c.max} step={c.pas ?? 1} value={valeurs[c.nom]} data-adresse={`graphe/${c.id}`}
              onChange={(e) => setValeurs((v) => ({ ...v, [c.nom]: Number(e.target.value) }))}
              className="h-2 w-full cursor-pointer accent-(--m-accent)" />
          </label>
        ))}
        <div className="min-h-[3.5rem] rounded-2xl border border-bord bg-white p-4 leading-relaxed" aria-live="polite">
          <AnimatePresence mode="popLayout" initial={false}>
            {lectures.map((l) => (
              <motion.p key={l.si + l.texte} layout initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} className="my-1">
                <Riche texte={l.texte} />
              </motion.p>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

/* ---------------------------------------------------------------- méthode */
function Methode({ bloc }: { bloc: BlocMethode }) {
  return (
    <ol className="relative m-0 flex list-none flex-col gap-3 p-0">
      <span aria-hidden className="absolute top-4 bottom-4 left-[15px] w-0.5 rounded bg-(--m-fond)" />
      {(bloc.etapes || []).map((etape, i) => (
        <motion.li key={i} {...apparition} transition={{ delay: 0.06 * i }} className="relative flex items-start gap-4">
          <span className="z-10 grid size-8 shrink-0 place-items-center rounded-full bg-(--m-texte) font-titre font-bold text-white shadow-relief">{i + 1}</span>
          <div className="flex-1 rounded-2xl bg-[#F8F9FC] px-4 py-3 leading-relaxed"><Riche texte={etape} /></div>
        </motion.li>
      ))}
    </ol>
  )
}

/* ---------------------------------------------------------------- piège */
function Piege({ bloc }: { bloc: BlocPiege }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <motion.div {...apparition} className="rounded-2xl border border-[#F5C6BD] bg-[#FFF4F2] p-4 leading-relaxed">
        <span className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#B42318]"><span className="grid size-6 place-items-center rounded-full bg-[#B42318] text-white"><X size={14} strokeWidth={3} /></span>L'erreur</span>
        <Riche texte={bloc.mauvaise_idee} />
      </motion.div>
      <motion.div {...apparition} transition={{ delay: 0.12 }} className="rounded-2xl border border-[#BFE3C7] bg-[#F1FAF3] p-4 leading-relaxed">
        <span className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#1E7B34]"><span className="grid size-6 place-items-center rounded-full bg-[#1E7B34] text-white"><Check size={14} strokeWidth={3} /></span>Le bon réflexe</span>
        <Riche texte={bloc.bonne_idee} />
      </motion.div>
      {bloc.pourquoi_faux && <p className="m-0 leading-relaxed text-gris md:col-span-2"><Riche texte={bloc.pourquoi_faux} /></p>}
    </div>
  )
}

/* ---------------------------------------------------------------- exemple */
function Exemple({ bloc }: { bloc: BlocExemple }) {
  const svg = useRef<SVGSVGElement>(null)
  useEffect(() => {
    if (bloc.figure) dessinerGabarit(svg.current, bloc.figure.gabarit, Object.fromEntries((bloc.figure.curseurs || []).map((c) => [c.nom, Number(c.depart)])))
  }, [bloc.figure])
  return (
    <div className="flex flex-col gap-3 leading-relaxed">
      {bloc.situation && <p className="m-0"><Riche texte={bloc.situation} /></p>}
      {bloc.calcul && <p className="m-0 rounded-2xl bg-[#F8F9FC] px-4 py-3"><Riche texte={bloc.calcul} /></p>}
      {bloc.figure && <svg ref={svg} className="figure" width={300} height={180} />}
      {bloc.conclusion && (
        <motion.p {...apparition} className="exemple-conclusion m-0 flex gap-3 rounded-2xl border-2 border-(--m-accent) bg-(--m-fond) px-4 py-3 font-semibold text-(--m-texte)">
          <ArrowRight className="mt-1 shrink-0" size={18} /><span><Riche texte={bloc.conclusion} /></span>
        </motion.p>
      )}
    </div>
  )
}

/* ---------------------------------------------------------------- renfort */
function Renfort({ bloc, ctx }: { bloc: BlocRenfort; ctx: ContexteRendu }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-3.5">
      {(bloc.liens || []).map((lien, i) => {
        const ouvrir = ctx.ouvrirOutil(lien)
        const contenu = (
          <>
            <span className="text-2xl" aria-hidden>{lien.icone || "🔧"}</span>
            <b className="mt-1.5 block">{lien.titre}</b>
            {(ouvrir || lien.description) && <small className="mt-0.5 block text-gris">{ouvrir ? "Ouvrir la leçon" : lien.description}</small>}
          </>
        )
        return ouvrir ? (
          <motion.button key={i} onClick={(e) => { e.stopPropagation(); ouvrir() }} whileHover={{ y: -3 }} whileTap={{ scale: 0.97 }}
            className="rounded-2xl border-2 border-(--m-accent) bg-(--m-fond) p-4 text-center text-(--m-texte) shadow-relief">{contenu}</motion.button>
        ) : (
          <div key={i} className="rounded-2xl border border-dashed border-[#B7C3D3] p-4 text-center text-[#4A5566]">{contenu}</div>
        )
      })}
    </div>
  )
}

/* ---------------------------------------------------------------- schéma */
// Le SVG a été nettoyé côté serveur par liste blanche (jules/svg_sur.py) ; on l'importe par DOMParser +
// importNode (jamais innerHTML), comme accueil.js. Styles : .bloc-schema dans /static/fiche-contenu.css.
function Schema({ bloc }: { bloc: BlocSchema }) {
  const zone = useRef<HTMLDivElement>(null)
  const [illisible, setIllisible] = useState(false)
  useEffect(() => {
    const doc = new DOMParser().parseFromString(String(bloc.svg || ""), "image/svg+xml")
    const racine = doc.documentElement
    if (zone.current && racine?.tagName === "svg" && !doc.querySelector("parsererror")) {
      zone.current.replaceChildren(document.importNode(racine, true))
      setIllisible(false)
    } else setIllisible(true)
  }, [bloc.svg])
  return (
    <>
      <div ref={zone} className="bloc-schema" />
      {illisible && <p className="text-sm text-gris">Schéma illisible.</p>}
    </>
  )
}

/* ---------------------------------------------------------------- registre */
type Rendu = (p: { bloc: never; ctx: ContexteRendu }) => ReactNode
export const RENDUS: Partial<Record<TypeBloc, Rendu>> = {
  formule: Formule as Rendu,
  carte: Carte as Rendu,
  graphe: Graphe as Rendu,
  methode: Methode as Rendu,
  piege: Piege as Rendu,
  exemple: Exemple as Rendu,
  renfort: Renfort as Rendu,
  schema: Schema as Rendu,
}

/** Un bloc de fiche : carte en relief, titre, contenu ; un clic montre ce qu'en dit Jules. */
export function BlocVisuel({ bloc, index, actif, ctx, onActiver }: {
  bloc: BlocFiche; index: number; actif: boolean; ctx: ContexteRendu
  onActiver: (bloc: BlocFiche, adresse: string) => void
}) {
  const Rendu = RENDUS[bloc.type]
  const type = TYPES[bloc.type]
  if (!Rendu || !type) return null
  const Icone = type.Icone
  return (
    <motion.section id={`bloc-${bloc.id}`} data-adresse={`fiche/${bloc.id}`}
      initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, ease: [0.2, 0.8, 0.2, 1], delay: Math.min(index, 2) * 0.05 }}
      onClick={(e) => {
        const cible = (e.target as Element).closest?.("[data-adresse]") as HTMLElement | SVGElement | null
        onActiver(bloc, cible?.dataset.adresse || `fiche/${bloc.id}`)
      }}
      className={cn("group relative scroll-mt-6 cursor-pointer rounded-3xl border bg-white p-6 shadow-relief transition-[box-shadow,border-color] duration-200 md:p-7",
        actif ? "border-(--m-accent) ring-4 ring-(--m-fond)" : "border-bord hover:border-[#C9D3E3] hover:shadow-relief-haut")}>
      <h2 className="mt-0 mb-5 flex items-center gap-3 text-[1.35rem] font-bold text-encre">
        <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-(--m-fond) text-(--m-texte) transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110">
          <Icone size={20} />
        </span>
        {typo(bloc.titre || type.titre)}
      </h2>
      <Rendu bloc={bloc as never} ctx={ctx} />
    </motion.section>
  )
}
