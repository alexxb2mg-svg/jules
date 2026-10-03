// Une fiche visuelle ouverte : en-tête aux couleurs de la matière, blocs du registre RENDUS, sommaire qui suit
// la lecture, Jules en bulles préécrites. Données : GET /api/eleve/fiches_visuelles/notions/<id>, sans IA.
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { motion, useScroll, useSpring } from "framer-motion"
import { BookOpen, ChevronDown, ChevronLeft, Dumbbell, Info, Target } from "lucide-react"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"
import { titreVariants } from "@/components/ui/variantes"
import { cours, exercices, fiches, type NotionExercices } from "@/api/jules"
import { Entrainement } from "@/modules/exercices/Entrainement"
import type { BlocAttendus, BlocFiche, Fiche, LienRenfort } from "./types"
import { BlocVisuel, RENDUS, TYPES, type ContexteRendu } from "./blocs"
import { BulleJules, useBulleJules } from "./Jules"
import { contexteSymboles } from "./ponts"
import { typo, Riche } from "./texte"
import { Chemin } from "@/modules/accueil/Chemin"
import { marquerEtape } from "@/modules/accueil/etat"

/** Variables CSS de la matière (table SPEC, /static/matieres-couleurs.css) reprises sous --m-*. */
export const styleMatiere = (matiere: string) => ({
  "--m-fond": `var(--matiere-${matiere}-fond, var(--j-bleu-clair))`,
  "--m-texte": `var(--matiere-${matiere}-texte, var(--j-bleu))`,
  "--m-accent": `var(--matiere-${matiere}-accent, var(--j-bleu))`,
}) as React.CSSProperties

/** La figure interactive (premier bloc « graphe ») remonte juste après le premier bloc (l'énoncé) ;
 *  le reste garde son ordre. Ordre d'affichage seulement : les données ne changent pas. */
function figureEnTete(blocs: BlocFiche[]): BlocFiche[] {
  const i = blocs.findIndex((b) => b.type === "graphe")
  if (i <= 1) return blocs
  return [blocs[0], blocs[i], ...blocs.slice(1, i), ...blocs.slice(i + 1)]
}

const ACCUEIL_JULES ="Clique sur un bloc de la fiche : je t'explique ce qu'il faut en retenir."

/** Habillage d'une fiche qui n'est pas une fiche native (fiche personnelle, docs/SOURCES-CONTRAT.md §8) :
 *  mêmes blocs, même rendu ; seuls la couleur, l'en-tête, les actions et la mention des sources changent. */
export type Habillage = {
  style: React.CSSProperties
  surtitre: React.ReactNode
  actions?: React.ReactNode
  mention: string
  accueil: string
}

export function FicheVisuelle({ notion, onRetour, retour, onOuvrirLecon, charger, habillage, suite, onChargee, onCartes }: {
  notion: string
  onRetour: () => void
  retour: string
  onOuvrirLecon: (notion: string) => void
  /** Fiche d'une autre origine que la bibliothèque native (par défaut : GET /api/eleve/fiches_visuelles/notions/<id>). */
  charger?: (id: string) => Promise<Fiche>
  habillage?: Habillage
  /** Contenu ajouté après les blocs (ex. « Mes fiches sur cette notion »). */
  suite?: React.ReactNode
  onChargee?: (f: Fiche) => void
  /** E : ouvre les cartes mémoire de la notion (studio). Absent : pas de chemin (fiche personnelle). */
  onCartes?: (matiere: string) => void
}) {
  const [fiche, setFiche] = useState<Fiche | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [avecLecon, setAvecLecon] = useState(false)
  const [entrainement, setEntrainement] = useState<NotionExercices | null>(null)
  const [actif, setActif] = useState<string | null>(null)
  const [attendusOuverts, setAttendusOuverts] = useState(false)
  const zone = useRef<HTMLDivElement>(null)
  const article = useRef<HTMLElement>(null)
  const bulleZone = useRef<HTMLDivElement>(null)
  const bulleColonne = useRef<HTMLDivElement>(null)
  const bulle = useBulleJules(habillage?.accueil ?? ACCUEIL_JULES)
  const native = !charger

  useEffect(() => {
    let annule = false
    setFiche(null); setErreur(null); setActif(null); setAvecLecon(false); setEntrainement(null)
    // Série d'exercices de la fiche v2 de la notion, si elle est servable sans IA (fiches natives).
    if (native) exercices.notions().then((l) => !annule && setEntrainement(l.find((n) => n.id === notion) ?? null)).catch(() => {})
    ;(charger ?? fiches.lire)(notion).then((f) => {
      if (annule) return
      setFiche(f)
      onChargee?.(f)
      zone.current?.scrollTo({ top: 0 })
      // La tuile « Exercices corrigés » d'un renfort ouvre la leçon seulement si elle existe vraiment.
      if (native) cours.parcours(f.matiere).then((p) => !annule && setAvecLecon(p.notions.some((n) => n.id === notion && n.lecon))).catch(() => {})
    }).catch((e) => !annule && setErreur(e.message))
    return () => { annule = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- recharger seulement quand la fiche change
  }, [notion])

  // Bulles de rappel au survol (symboles.js) : matière, lettres des formules et abréviations de la fiche.
  useEffect(() => {
    if (!fiche) return
    const rappels = { matiere: fiche.matiere, variables: fiche.variables, abreviations: fiche.abreviations }
    contexteSymboles(article.current, rappels)
    contexteSymboles(bulleZone.current, rappels)
    contexteSymboles(bulleColonne.current, rappels)
  }, [fiche])

  const activer = useCallback((bloc: BlocFiche, adresse: string) => {
    setActif(bloc.id)
    if (bloc.jules) bulle.dire(bloc.jules)
    if (native) fiches.blocConsulte(adresse, notion)
  }, [bulle, notion, native])

  const ctx: ContexteRendu = useMemo(() => ({
    ouvrirOutil: (lien: LienRenfort) => (lien.outil === "lecon" && avecLecon ? () => onOuvrirLecon(notion) : null),
  }), [avecLecon, notion, onOuvrirLecon])

  const notionReelle = native ? notion : fiche?.notion
  const lienDiscuter = notionReelle ? `/discuter?notion=${encodeURIComponent(notionReelle)}` : "/discuter"
  const blocs = figureEnTete((fiche?.blocs || []).filter((b) => b.type !== "attendus" && RENDUS[b.type]))
  const attendus = (fiche?.blocs.find((b) => b.type === "attendus") as BlocAttendus | undefined)?.attendus || []

  const { scrollYProgress } = useScroll({ container: zone })
  const progression = useSpring(scrollYProgress, { stiffness: 200, damping: 30 })
  // E : la fiche compte comme lue quand l'élève est allée jusqu'au bout.
  useEffect(() => scrollYProgress.on("change", (v) => { if (v > 0.92 && native && fiche) marquerEtape(notion, "fiche") }), [scrollYProgress, native, fiche, notion])
  const allerA = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" })
  const chemin = native && fiche && onCartes ? (horizontal: boolean) => (
    <Chemin notion={notion} matiere={fiche.matiere} avecLecon={avecLecon} avecExercices={!!entrainement} horizontal={horizontal}
      onFiche={() => allerA(`bloc-${blocs[0]?.id}`)} onLecon={() => onOuvrirLecon(notion)}
      onExercices={() => allerA("bloc-entrainement")} onCartes={() => onCartes(fiche.matiere)} />
  ) : null

  if (erreur) return <div className="grid h-full place-items-center p-8 text-center text-gris">Impossible d'ouvrir cette fiche ({erreur}).</div>

  return (
    <div className="relative flex h-full flex-col" style={habillage?.style ?? (fiche ? styleMatiere(fiche.matiere) : undefined)}>
      <motion.div aria-hidden className="absolute inset-x-0 top-0 z-20 h-1 origin-left bg-(--m-accent)" style={{ scaleX: progression }} />
      <div ref={zone} className="flex-1 overflow-y-auto">
        {/* En-tête : bandeau aux couleurs de la matière */}
        <header data-sans-symboles className="relative overflow-hidden bg-(--m-fond) px-6 pt-5 pb-8 pl-16 md:px-12">
          <span aria-hidden className="absolute -top-24 -right-16 size-72 rounded-full bg-(--m-accent) opacity-[0.08]" />
          <span aria-hidden className="absolute top-10 right-40 size-24 rounded-full bg-(--m-accent) opacity-[0.06]" />
          <div className="relative mx-auto max-w-[1180px]">
            <button onClick={onRetour} className={buttonVariants({ variant: "sombre", size: "pastille-sm", className: "mb-4 bg-card/70 backdrop-blur" })}>
              <ChevronLeft size={16} /> {retour}
            </button>
            {fiche ? (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
                <p className={titreVariants({ niveau: "surtitre", className: "font-sans" })}>{habillage?.surtitre ?? `${fiche.nom_matiere} · ${fiche.niveau}`}</p>
                <h1 className={titreVariants({ niveau: "ecran", className: "mt-1 max-w-[900px]" })}>{typo(fiche.titre)}</h1>
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  {attendus.length > 0 && (
                    <button onClick={() => setAttendusOuverts((o) => !o)} aria-expanded={attendusOuverts}
                      className={buttonVariants({ variant: "sombre", size: "pastille-sm" })}>
                      <Target size={15} /> Ce qu'on attend de toi <ChevronDown size={15} className={cn("transition-transform", attendusOuverts && "rotate-180")} />
                    </button>
                  )}
                  {entrainement && (
                    <button onClick={() => document.getElementById("bloc-entrainement")?.scrollIntoView({ behavior: "smooth", block: "start" })}
                      className={buttonVariants({ variant: "sombre", size: "pastille-sm", className: chemin ? "hidden lg:inline-flex" : "inline-flex" })}>
                      <Dumbbell size={15} /> M'entraîner
                    </button>
                  )}
                  {avecLecon && (
                    <button onClick={() => onOuvrirLecon(notion)}
                      className={buttonVariants({ variant: "matiere", size: "pastille-sm" })}>
                      <BookOpen size={15} /> Faire la leçon avec Jules
                    </button>
                  )}
                  {habillage?.actions}
                </div>
                {chemin && <div className="mt-4 lg:hidden">{chemin(true)}</div>}
                <motion.ul initial={false} animate={{ height: attendusOuverts ? "auto" : 0, opacity: attendusOuverts ? 1 : 0 }}
                  className="m-0 grid list-none gap-2 overflow-hidden p-0 md:grid-cols-2">
                  {attendus.map((a, i) => (
                    <li key={i} className={cn("rounded-2xl bg-card/80 px-4 py-2.5 text-courant", i === 0 && "mt-3", i === 1 && "md:mt-3")}>{a}</li>
                  ))}
                </motion.ul>
              </motion.div>
            ) : (
              <div className="h-24 animate-pulse rounded-surface bg-card/50" />
            )}
          </div>
        </header>

        {fiche && (
          <div className="mx-auto grid max-w-[1180px] gap-8 px-4 pt-5 pb-40 md:px-8 lg:grid-cols-[minmax(0,1fr)_290px]">
            <article ref={article} className="flex min-w-0 flex-col gap-5">
              {fiche.relecture_a_relire && (
                <p data-sans-symboles className="m-0 flex items-start gap-2 rounded-2xl bg-alerte-fond px-4 py-3 text-petit text-alerte">
                  <Info size={16} className="mt-0.5 shrink-0" />
                  Fiche expérimentale, pas encore relue par un adulte : sers-t'en comme appui, pas comme vérité absolue.
                </p>
              )}
              {blocs.map((b, i) => (
                <BlocVisuel key={`${notion}-${b.id}`} bloc={b} index={i} actif={actif === b.id} ctx={ctx} onActiver={activer} />
              ))}
              {entrainement && <Entrainement key={notion} notion={notion} nb={entrainement.nb} generateur={entrainement.generateur} />}
              {suite}
              <p data-sans-symboles className="m-0 text-petit text-gris">
                {habillage?.mention ?? `Sources : ${fiche.sources.map((s) => (s.licence ? `${s.titre} (${s.licence})` : s.titre)).join(" · ")} — fiche sous licence ${fiche.licence}`}
              </p>
            </article>
            <aside className="sticky top-6 hidden flex-col gap-6 self-start lg:flex">
              {chemin?.(false)}
              <Sommaire blocs={blocs} actif={actif} zone={zone} entrainement={!!entrainement} />
              <div ref={bulleColonne}>
                <BulleJules texte={bulle.texte} cle={bulle.cle} fermer={bulle.fermer} lienDiscuter={lienDiscuter} />
              </div>
            </aside>
          </div>
        )}
      </div>

      {/* Jules : bulle préécrite en bas à droite */}
      {/* Petit écran : Jules flotte en bas ; grand écran : il est dans la colonne de droite, sous le sommaire. */}
      <div ref={bulleZone} className="pointer-events-none absolute right-4 bottom-4 z-30 w-[min(360px,calc(100%-2rem))] [&>*]:pointer-events-auto md:right-8 md:bottom-6 lg:hidden">
        <BulleJules texte={bulle.texte} cle={bulle.cle} fermer={bulle.fermer} lienDiscuter={lienDiscuter} />
      </div>
    </div>
  )
}

/** Sommaire de la fiche : suit la lecture (bloc le plus haut visible) et y mène au clic. */
function Sommaire({ blocs, actif, zone, entrainement }: { blocs: BlocFiche[]; actif: string | null; zone: React.RefObject<HTMLDivElement | null>; entrainement: boolean }) {
  const [visible, setVisible] = useState<string | null>(blocs[0]?.id ?? null)
  useEffect(() => {
    const racine = zone.current
    if (!racine) return
    const obs = new IntersectionObserver((entrees) => {
      const vus = entrees.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
      if (vus[0]) setVisible(vus[0].target.id.replace(/^bloc-/, ""))
    }, { root: racine, rootMargin: "-10% 0px -60% 0px" })
    blocs.forEach((b) => { const el = document.getElementById(`bloc-${b.id}`); if (el) obs.observe(el) })
    const ex = document.getElementById("bloc-entrainement")
    if (ex) obs.observe(ex)
    return () => obs.disconnect()
  }, [blocs, zone, entrainement])
  const courant = actif ?? visible
  return (
    <nav data-sans-symboles aria-label="Sommaire de la fiche">
      <p className={titreVariants({ niveau: "etiquette", className: "mb-2 font-sans text-gris" })}>Dans cette fiche</p>
      <ul className="relative m-0 flex list-none flex-col gap-0.5 border-l-2 border-bord p-0">
        {[...blocs.map((b) => ({ id: b.id, Icone: TYPES[b.type]!.Icone, titre: b.titre || TYPES[b.type]!.titre })),
          ...(entrainement ? [{ id: "entrainement", Icone: Dumbbell, titre: "M'entraîner" }] : [])].map((b) => {
          const t = b
          const on = courant === b.id
          return (
            <li key={b.id} className="relative">
              {on && <motion.span layoutId="sommaire-actif" className="absolute top-0 bottom-0 -left-[2px] w-[3px] rounded bg-(--m-accent)" />}
              <button onClick={() => document.getElementById(`bloc-${b.id}`)?.scrollIntoView({ behavior: "smooth", block: "start" })}
                className={cn("flex w-full items-center gap-2 rounded-r-lg py-1.5 pr-2 pl-3 text-left text-petit transition-colors",
                  on ? "font-semibold text-(--m-texte)" : "text-gris hover:text-encre")}>
                <t.Icone size={15} className="shrink-0" />
                <span className="line-clamp-2"><Riche texte={t.titre.replace(/\*\*/g, "")} /></span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
