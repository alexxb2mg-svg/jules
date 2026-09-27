// Une fiche visuelle ouverte : en-tête aux couleurs de la matière, blocs du registre RENDUS, sommaire qui suit
// la lecture, Jules en bulles préécrites. Données : GET /api/eleve/fiches_visuelles/notions/<id>, sans IA.
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { motion, useScroll, useSpring } from "framer-motion"
import { BookOpen, ChevronDown, ChevronLeft, Info, Target } from "lucide-react"
import { cn } from "@/lib/utils"
import { cours, fiches } from "@/api/jules"
import type { BlocAttendus, BlocFiche, Fiche, LienRenfort } from "./types"
import { BlocVisuel, RENDUS, TYPES, type ContexteRendu } from "./blocs"
import { BulleJules, useBulleJules } from "./Jules"
import { contexteSymboles } from "./ponts"
import { typo, Riche } from "./texte"

/** Variables CSS de la matière (table SPEC, /static/matieres-couleurs.css) reprises sous --m-*. */
export const styleMatiere = (matiere: string) => ({
  "--m-fond": `var(--matiere-${matiere}-fond, var(--j-bleu-clair))`,
  "--m-texte": `var(--matiere-${matiere}-texte, var(--j-bleu))`,
  "--m-accent": `var(--matiere-${matiere}-accent, var(--j-bleu))`,
}) as React.CSSProperties

const ACCUEIL_JULES = "Clique sur un bloc de la fiche : je t'explique ce qu'il faut en retenir."

export function FicheVisuelle({ notion, onRetour, retour, onOuvrirLecon }: {
  notion: string
  onRetour: () => void
  retour: string
  onOuvrirLecon: (notion: string) => void
}) {
  const [fiche, setFiche] = useState<Fiche | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [avecLecon, setAvecLecon] = useState(false)
  const [actif, setActif] = useState<string | null>(null)
  const [attendusOuverts, setAttendusOuverts] = useState(false)
  const zone = useRef<HTMLDivElement>(null)
  const article = useRef<HTMLElement>(null)
  const bulleZone = useRef<HTMLDivElement>(null)
  const bulleColonne = useRef<HTMLDivElement>(null)
  const bulle = useBulleJules(ACCUEIL_JULES)

  useEffect(() => {
    let annule = false
    setFiche(null); setErreur(null); setActif(null); setAvecLecon(false)
    fiches.lire(notion).then((f) => {
      if (annule) return
      setFiche(f)
      zone.current?.scrollTo({ top: 0 })
      // La tuile « Exercices corrigés » d'un renfort ouvre la leçon seulement si elle existe vraiment.
      cours.parcours(f.matiere).then((p) => !annule && setAvecLecon(p.notions.some((n) => n.id === notion && n.lecon))).catch(() => {})
    }).catch((e) => !annule && setErreur(e.message))
    return () => { annule = true }
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
    fiches.blocConsulte(adresse, notion)
  }, [bulle, notion])

  const ctx: ContexteRendu = useMemo(() => ({
    ouvrirOutil: (lien: LienRenfort) => (lien.outil === "lecon" && avecLecon ? () => onOuvrirLecon(notion) : null),
  }), [avecLecon, notion, onOuvrirLecon])

  const blocs = (fiche?.blocs || []).filter((b) => b.type !== "attendus" && RENDUS[b.type])
  const attendus = (fiche?.blocs.find((b) => b.type === "attendus") as BlocAttendus | undefined)?.attendus || []

  const { scrollYProgress } = useScroll({ container: zone })
  const progression = useSpring(scrollYProgress, { stiffness: 200, damping: 30 })

  if (erreur) return <div className="grid h-full place-items-center p-8 text-center text-gris">Impossible d'ouvrir cette fiche ({erreur}).</div>

  return (
    <div className="relative flex h-full flex-col" style={fiche ? styleMatiere(fiche.matiere) : undefined}>
      <motion.div aria-hidden className="absolute inset-x-0 top-0 z-20 h-1 origin-left bg-(--m-accent)" style={{ scaleX: progression }} />
      <div ref={zone} className="flex-1 overflow-y-auto">
        {/* En-tête : bandeau aux couleurs de la matière */}
        <header data-sans-symboles className="relative overflow-hidden bg-(--m-fond) px-6 pt-5 pb-8 pl-16 md:px-12">
          <span aria-hidden className="absolute -top-24 -right-16 size-72 rounded-full bg-(--m-accent) opacity-[0.08]" />
          <span aria-hidden className="absolute top-10 right-40 size-24 rounded-full bg-(--m-accent) opacity-[0.06]" />
          <div className="relative mx-auto max-w-[1180px]">
            <button onClick={onRetour} className="mb-4 inline-flex items-center gap-1 rounded-full bg-white/70 px-3 py-1.5 text-[0.9rem] font-semibold text-(--m-texte) backdrop-blur hover:bg-white">
              <ChevronLeft size={16} /> {retour}
            </button>
            {fiche ? (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
                <p className="m-0 text-[0.95rem] font-semibold tracking-wide text-(--m-texte)">{fiche.nom_matiere} · {fiche.niveau}</p>
                <h1 className="mt-1 mb-0 max-w-[900px] text-[2.1rem] leading-tight font-bold text-balance text-encre md:text-[2.5rem]">{typo(fiche.titre)}</h1>
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  {attendus.length > 0 && (
                    <button onClick={() => setAttendusOuverts((o) => !o)} aria-expanded={attendusOuverts}
                      className="inline-flex items-center gap-1.5 rounded-full bg-white px-3.5 py-1.5 text-[0.9rem] font-semibold text-(--m-texte) shadow-relief">
                      <Target size={15} /> Ce qu'on attend de toi <ChevronDown size={15} className={cn("transition-transform", attendusOuverts && "rotate-180")} />
                    </button>
                  )}
                  {avecLecon && (
                    <button onClick={() => onOuvrirLecon(notion)}
                      className="inline-flex items-center gap-1.5 rounded-full bg-(--m-texte) px-3.5 py-1.5 text-[0.9rem] font-semibold text-white shadow-relief">
                      <BookOpen size={15} /> Faire la leçon avec Jules
                    </button>
                  )}
                </div>
                <motion.ul initial={false} animate={{ height: attendusOuverts ? "auto" : 0, opacity: attendusOuverts ? 1 : 0 }}
                  className="m-0 grid list-none gap-2 overflow-hidden p-0 md:grid-cols-2">
                  {attendus.map((a, i) => (
                    <li key={i} className={cn("rounded-2xl bg-white/80 px-4 py-2.5 text-[0.95rem] leading-snug", i === 0 && "mt-3", i === 1 && "md:mt-3")}>{a}</li>
                  ))}
                </motion.ul>
              </motion.div>
            ) : (
              <div className="h-24 animate-pulse rounded-2xl bg-white/50" />
            )}
          </div>
        </header>

        {fiche && (
          <div className="mx-auto grid max-w-[1180px] gap-8 px-4 pt-6 pb-40 md:px-8 lg:grid-cols-[minmax(0,1fr)_290px]">
            <article ref={article} className="flex min-w-0 flex-col gap-6">
              {fiche.relecture_a_relire && (
                <p data-sans-symboles className="m-0 flex items-start gap-2 rounded-2xl border border-[#F3D9A6] bg-[#FFF8EC] px-4 py-2.5 text-[0.9rem] text-[#7A4B00]">
                  <Info size={16} className="mt-0.5 shrink-0" />
                  Fiche expérimentale, pas encore relue par un adulte : sers-t'en comme appui, pas comme vérité absolue.
                </p>
              )}
              {blocs.map((b, i) => (
                <BlocVisuel key={`${notion}-${b.id}`} bloc={b} index={i} actif={actif === b.id} ctx={ctx} onActiver={activer} />
              ))}
              <p data-sans-symboles className="m-0 text-[0.8rem] leading-relaxed text-gris">
                Sources : {fiche.sources.map((s) => (s.licence ? `${s.titre} (${s.licence})` : s.titre)).join(" · ")} — fiche sous licence {fiche.licence}
              </p>
            </article>
            <aside className="sticky top-6 hidden flex-col gap-6 self-start lg:flex">
              <Sommaire blocs={blocs} actif={actif} zone={zone} />
              <div ref={bulleColonne}>
                <BulleJules texte={bulle.texte} cle={bulle.cle} fermer={bulle.fermer} lienDiscuter={`/discuter?notion=${encodeURIComponent(notion)}`} />
              </div>
            </aside>
          </div>
        )}
      </div>

      {/* Jules : bulle préécrite en bas à droite */}
      {/* Petit écran : Jules flotte en bas ; grand écran : il est dans la colonne de droite, sous le sommaire. */}
      <div ref={bulleZone} className="pointer-events-none absolute right-4 bottom-4 z-30 w-[min(360px,calc(100%-2rem))] [&>*]:pointer-events-auto md:right-8 md:bottom-6 lg:hidden">
        <BulleJules texte={bulle.texte} cle={bulle.cle} fermer={bulle.fermer} lienDiscuter={`/discuter?notion=${encodeURIComponent(notion)}`} />
      </div>
    </div>
  )
}

/** Sommaire de la fiche : suit la lecture (bloc le plus haut visible) et y mène au clic. */
function Sommaire({ blocs, actif, zone }: { blocs: BlocFiche[]; actif: string | null; zone: React.RefObject<HTMLDivElement | null> }) {
  const [visible, setVisible] = useState<string | null>(blocs[0]?.id ?? null)
  useEffect(() => {
    const racine = zone.current
    if (!racine) return
    const obs = new IntersectionObserver((entrees) => {
      const vus = entrees.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
      if (vus[0]) setVisible(vus[0].target.id.replace(/^bloc-/, ""))
    }, { root: racine, rootMargin: "-10% 0px -60% 0px" })
    blocs.forEach((b) => { const el = document.getElementById(`bloc-${b.id}`); if (el) obs.observe(el) })
    return () => obs.disconnect()
  }, [blocs, zone])
  const courant = actif ?? visible
  return (
    <nav data-sans-symboles aria-label="Sommaire de la fiche">
      <p className="mt-0 mb-2 text-[0.8rem] font-semibold tracking-wide text-gris">Dans cette fiche</p>
      <ul className="relative m-0 flex list-none flex-col gap-0.5 border-l-2 border-bord p-0">
        {blocs.map((b) => {
          const t = TYPES[b.type]!
          const on = courant === b.id
          return (
            <li key={b.id} className="relative">
              {on && <motion.span layoutId="sommaire-actif" className="absolute top-0 bottom-0 -left-[2px] w-[3px] rounded bg-(--m-accent)" />}
              <button onClick={() => document.getElementById(`bloc-${b.id}`)?.scrollIntoView({ behavior: "smooth", block: "start" })}
                className={cn("flex w-full items-center gap-2 rounded-r-lg py-1.5 pr-2 pl-3 text-left text-[0.88rem] leading-snug transition-colors",
                  on ? "font-semibold text-(--m-texte)" : "text-gris hover:text-encre")}>
                <t.Icone size={15} className="shrink-0" />
                <span className="line-clamp-2"><Riche texte={(b.titre || t.titre).replace(/\*\*/g, "")} /></span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
