// « Mes fiches » : les fiches visuelles de la bibliothèque, par matière puis par chapitre.
// Données : GET /api/eleve/fiches_visuelles/notions (index seul, sans IA). Recherche locale sur les titres.
import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, LayoutGroup, motion } from "framer-motion"
import { ArrowRight, ChevronLeft, Plus, Search, Sparkles, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useMotion } from "@/lib/motion"
import { buttonVariants } from "@/components/ui/button"
import { Pastille } from "@/components/ui/pastille"
import { surfaceVariants, titreVariants } from "@/components/ui/variantes"
import { BandeauMatieres, EnteteMatiere } from "@/composants/EnteteMatiere"
import { fiches } from "@/api/jules"
import type { IndexFiches, MatiereIndex, NotionIndex } from "./types"
import { iconeMatiere, ORDRE_MATIERES } from "@/config/matieres"
import { styleMatiere } from "./FicheVisuelle"
import type { EntreePerso } from "@/api/jules"
import { TEXTES } from "@/config/sources"
import { useBibliothequePerso, useFiltre } from "@/modules/sources/etat"
import { FiltreFiches, SectionDossiers, TuilePerso, voitNatives, voitPerso } from "@/modules/sources/pieces"
import { LegendeOrigine, Reprise } from "@/modules/accueil/Reprise"
import { estNouveau, LIBELLE_NOUVEAU } from "@/config/veille"

/** Comparaison sans accents ni casse, pour la recherche. */
const plat = (s: string) => s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()

export function Bibliotheque({ matiere, onMatiere, onOuvrir, onOuvrirPerso, onAjouter, onDossier, onReviser }: {
  matiere: string | null
  onMatiere: (id: string | null) => void
  onOuvrir: (notion: string) => void
  onOuvrirPerso: (id: string) => void
  onAjouter: () => void
  onDossier: (id: string) => void
  onReviser: () => void
}) {
  const [index, setIndex] = useState<IndexFiches | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [recherche, setRecherche] = useState("")
  useEffect(() => { fiches.index().then(setIndex).catch((e) => setErreur(e.message)) }, [])
  const { tap } = useMotion()
  const [filtre] = useFiltre()
  const perso = useBibliothequePerso()
  // Fiches perso rangées dans une matière (notion ou matière reconnue), par matière ; à ranger : dans « Mes dossiers ».
  const persoParMatiere = useMemo(() => {
    const par = new Map<string, EntreePerso[]>()
    for (const f of perso?.fiches ?? []) {
      // Sans notion : Non classé ou dossier seulement. À ranger : section « Mes dossiers ».
      if (f.etat !== "rangee" || !f.matiere || !f.notion) continue
      par.set(f.matiere, [...(par.get(f.matiere) ?? []), f])
    }
    return par
  }, [perso])

  const matieres = useMemo(() => {
    const liste = [...(index?.matieres || [])]
    const rang = (id: string) => { const i = ORDRE_MATIERES.indexOf(id); return i < 0 ? 99 : i }
    return liste.sort((a, b) => rang(a.id) - rang(b.id))
  }, [index])
  const total = matieres.reduce((n, m) => n + m.notions.length, 0)
  const choisie = matieres.find((m) => m.id === matiere) || null

  const trouvees = useMemo(() => {
    const q = plat(recherche.trim())
    if (q.length < 2) return null
    const mots = q.split(/\s+/)
    const natives = !voitNatives(filtre) ? [] : matieres.flatMap((m) => m.notions.filter((n) => {
      const texte = plat(`${n.titre} ${n.chapitre} ${m.nom}`)
      return mots.every((w) => texte.includes(w))
    }).map((n) => ({ m, n }))).slice(0, 40)
    const persos = !voitPerso(filtre) ? [] : (perso?.fiches ?? []).filter((f) => {
      const texte = plat(`${f.titre} ${f.titre_notion ?? ""} ${f.nom_matiere ?? ""} ${f.source.titre}`)
      return mots.every((w) => texte.includes(w))
    })
    return { natives, persos }
  }, [recherche, matieres, filtre, perso])

  if (erreur) return <div className="grid h-full place-items-center p-8 text-gris">La bibliothèque ne répond pas ({erreur}).</div>

  return (
    <div className="mx-auto max-w-[1180px] px-5 pt-16 pb-16 md:px-10 md:pt-8">
      {/* En-tête + recherche */}
      {choisie ? (
        <>
          <button onClick={() => onMatiere(null)} className={buttonVariants({ variant: "ghost", size: "pastille-sm", className: "-ml-3 mb-1 text-gris" })}>
            <ChevronLeft /> Toutes les matières
          </button>
          <EnteteMatiere rubrique="Mes fiches" matiere={choisie.id} nom={choisie.nom}
            sousTitre={`${choisie.notions.length} fiches visuelles · ${new Set(choisie.notions.map((n) => n.chapitre)).size} chapitres`}>
        <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:items-end">
        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <FiltreFiches />
          <motion.button {...tap} onClick={onAjouter} className={buttonVariants({ variant: "sombre", size: "pastille", className: "bg-perso text-white hover:bg-perso/90" })}>
            <Plus /> {TEXTES.ajouter}
            {estNouveau("fiches:ajouter") && <span className="rounded-full bg-white px-2 py-px text-petit font-bold text-perso">{LIBELLE_NOUVEAU}</span>}
          </motion.button>
        </div>
        <label className="relative flex w-full items-center sm:w-[340px]">
          <Search size={18} className="pointer-events-none absolute left-4 text-gris" />
          <input value={recherche} onChange={(e) => setRecherche(e.target.value)} placeholder="Chercher une notion…" aria-label="Chercher une notion"
            className="h-12 w-full rounded-full bg-card pr-10 pl-11 text-courant outline-none transition-shadow focus:ring-2 focus:ring-bleu/40" />
          {recherche && <button onClick={() => setRecherche("")} aria-label="Effacer" className="absolute right-3 rounded-full p-1 text-gris hover:bg-survol"><X size={16} /></button>}
        </label>
        </div>
          </EnteteMatiere>
          <BandeauMatieres matieres={matieres} courante={choisie.id} onChoix={onMatiere} />
        </>
      ) : (
        <div className="mb-7 flex flex-wrap items-end justify-between gap-5">
          <div>
            <h1 className={titreVariants({ niveau: "ecran" })}>Mes fiches</h1>
            <p className="mt-1 mb-0 text-courant text-gris">{index ? `${total} fiches visuelles pour toute la 3e, rangées par matière.` : "Chargement de la bibliothèque…"}</p>
            {(perso?.fiches.length ?? 0) > 0 && <LegendeOrigine />}
          </div>
        <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:items-end">
        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <FiltreFiches />
          <motion.button {...tap} onClick={onAjouter} className={buttonVariants({ variant: "sombre", size: "pastille", className: "bg-perso text-white hover:bg-perso/90" })}>
            <Plus /> {TEXTES.ajouter}
            {estNouveau("fiches:ajouter") && <span className="rounded-full bg-white px-2 py-px text-petit font-bold text-perso">{LIBELLE_NOUVEAU}</span>}
          </motion.button>
        </div>
        <label className="relative flex w-full items-center sm:w-[340px]">
          <Search size={18} className="pointer-events-none absolute left-4 text-gris" />
          <input value={recherche} onChange={(e) => setRecherche(e.target.value)} placeholder="Chercher une notion…" aria-label="Chercher une notion"
            className="h-12 w-full rounded-full bg-card pr-10 pl-11 text-courant outline-none transition-shadow focus:ring-2 focus:ring-bleu/40" />
          {recherche && <button onClick={() => setRecherche("")} aria-label="Effacer" className="absolute right-3 rounded-full p-1 text-gris hover:bg-survol"><X size={16} /></button>}
        </label>
        </div>
        </div>
      )}

      {!choisie && !trouvees && <Reprise onFiche={onOuvrir} onPerso={onOuvrirPerso} onReviser={onReviser} />}

      <AnimatePresence mode="wait" initial={false}>
        {trouvees ? (
          <motion.div key="recherche" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {(() => { const n = trouvees.natives.length + trouvees.persos.length; return <p className="mt-0 mb-3 text-gris">{n ? `${n} fiche${n > 1 ? "s" : ""} trouvée${n > 1 ? "s" : ""}` : "Aucune fiche ne correspond."}</p> })()}
            <div className="grid gap-3 md:grid-cols-2">
              {trouvees.persos.map((f, i) => <TuilePerso key={f.id} f={f} i={i} onOuvrir={onOuvrirPerso} avecLieu />)}
              {trouvees.natives.map(({ m, n }) => <TuileNotion key={n.id} n={n} m={m} onOuvrir={onOuvrir} avecMatiere />)}
            </div>
          </motion.div>
        ) : choisie ? (
          <motion.div key={`m-${choisie.id}`} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
            transition={{ type: "spring", stiffness: 260, damping: 30 }}>
            <Chapitres m={choisie} onOuvrir={onOuvrir} natives={voitNatives(filtre)}
              perso={voitPerso(filtre) ? persoParMatiere.get(choisie.id) ?? [] : []} onOuvrirPerso={onOuvrirPerso} />
          </motion.div>
        ) : (
          <motion.div key="grille" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, x: -20 }}>
            <LayoutGroup>
              <div className="grid grid-cols-[repeat(auto-fill,minmax(230px,1fr))] gap-4">
                {index
                  ? matieres.filter((m) => voitNatives(filtre) || persoParMatiere.has(m.id)).map((m) => (
                    <TuileMatiere key={m.id} m={m} onClick={() => onMatiere(m.id)}
                      natives={voitNatives(filtre)} nbPerso={voitPerso(filtre) ? persoParMatiere.get(m.id)?.length ?? 0 : 0} />))
                  : Array.from({ length: 12 }, (_, i) => <div key={i} className="h-[150px] animate-pulse rounded-3xl bg-nav" />)}
              </div>
            </LayoutGroup>
            {filtre === "perso" && perso && perso.fiches.length === 0 && <p className="mt-6 text-gris">{TEXTES.aucunePerso}</p>}
            {voitPerso(filtre) && <SectionDossiers onDossier={onDossier} onOuvrir={onOuvrirPerso} />}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function TuileMatiere({ m, onClick, natives, nbPerso }: { m: MatiereIndex; onClick: () => void; natives: boolean; nbPerso: number }) {
  const Icone = iconeMatiere(m.id)
  const { entree, tap } = useMotion()
  const chapitres = new Set(m.notions.map((n) => n.chapitre)).size
  return (
    <motion.button onClick={onClick} style={styleMatiere(m.id)} {...entree} {...tap}
      className={surfaceVariants({ ton: "degrade", className: "group flex h-[150px] flex-col justify-between text-left" })}>
      <Pastille ton="matiere-accent" taille="icone" className="transition-transform duration-300 group-hover:-rotate-6">
        <Icone size={22} />
      </Pastille>
      <span>
        <b className={titreVariants({ niveau: "bloc", className: "block" })}>{m.nom.replace(/ \(.*\)$/, "")}</b>
        <span className="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-petit text-(--m-texte)">
          {natives ? <span>{m.notions.length} fiches · {chapitres} chapitre{chapitres > 1 ? "s" : ""}</span> : null}
          {nbPerso > 0 && <span className="rounded-full bg-perso-clair px-2 py-px text-petit font-semibold whitespace-nowrap text-perso">{natives ? "+" : ""}{nbPerso} perso</span>}
          <ArrowRight size={15} className="ml-auto text-(--m-texte) opacity-0 transition-all group-hover:translate-x-1 group-hover:opacity-100" />
        </span>
      </span>
    </motion.button>
  )
}

function Chapitres({ m, onOuvrir, natives, perso, onOuvrirPerso }: {
  m: MatiereIndex; onOuvrir: (notion: string) => void; natives: boolean; perso: EntreePerso[]; onOuvrirPerso: (id: string) => void
}) {
  // Les fiches perso rejoignent le chapitre de leur notion, juste après la fiche native (docs/SOURCES-CONTRAT.md §8).
  const chapitres = useMemo(() => {
    const ordre: string[] = [], par = new Map<string, NotionIndex[]>(), persoPar = new Map<string, EntreePerso[]>()
    const ajouterChapitre = (c: string) => { if (!par.has(c)) { par.set(c, []); persoPar.set(c, []); ordre.push(c) } }
    for (const n of m.notions) { ajouterChapitre(n.chapitre); if (natives) par.get(n.chapitre)!.push(n) }
    for (const f of perso) { const c = f.chapitre ?? TEXTES.nonClasse; ajouterChapitre(c); persoPar.get(c)!.push(f) }
    return ordre.map((c) => ({ titre: c, notions: par.get(c)!, perso: persoPar.get(c)! })).filter((c) => c.notions.length + c.perso.length > 0)
  }, [m, natives, perso])
  let k = 0
  return (
    <div className="flex flex-col gap-8" style={styleMatiere(m.id)}>
      {chapitres.map((c, ci) => (
        <section key={c.titre}>
          <h2 className={titreVariants({ niveau: "bloc", className: "mt-0 mb-3 flex items-baseline gap-3 text-(--m-texte)" })}>
            <span className="text-petit tabular-nums">{String(ci + 1).padStart(2, "0")}</span>
            {c.titre}
          </h2>
          <div className="grid gap-3 md:grid-cols-2">
            {c.notions.flatMap((n) => [
              <TuileNotion key={n.id} n={n} m={m} onOuvrir={onOuvrir} />,
              ...c.perso.filter((f) => f.notion === n.id).map((f) => <TuilePerso key={f.id} f={f} i={k++} onOuvrir={onOuvrirPerso} />),
            ])}
            {c.perso.filter((f) => !c.notions.some((n) => n.id === f.notion)).map((f) => <TuilePerso key={f.id} f={f} i={k++} onOuvrir={onOuvrirPerso} avecLieu />)}
          </div>
        </section>
      ))}
    </div>
  )
}

function TuileNotion({ n, m, onOuvrir, avecMatiere }: { n: NotionIndex; m: MatiereIndex; onOuvrir: (id: string) => void; avecMatiere?: boolean }) {
  const Icone = iconeMatiere(m.id)
  const { entree, tap } = useMotion()
  return (
    <motion.button onClick={() => onOuvrir(n.id)} style={styleMatiere(m.id)} {...entree} {...tap}
      className={surfaceVariants({ ton: "degrade", espace: "compact", className: "group flex items-center gap-4 text-left" })}>
      <Pastille ton="matiere-accent" taille="icone">
        {avecMatiere ? <Icone size={19} /> : <Sparkles size={18} />}
      </Pastille>
      <span className="min-w-0 flex-1">
        <b className="block text-courant leading-snug text-encre">{n.titre}</b>
        {avecMatiere && <span className="block truncate text-petit text-(--m-texte)">{m.nom} · {n.chapitre}</span>}
      </span>
      <ArrowRight size={18} className={cn("shrink-0 text-(--m-texte) transition-transform group-hover:translate-x-1")} />
    </motion.button>
  )
}
