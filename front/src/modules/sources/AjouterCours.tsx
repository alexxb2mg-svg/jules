// « Ajouter mon cours » : deux cartes sources (Mes cours Jules | Mon document), dépôt, puis progression
// RÉELLE (étapes envoyées par le serveur), et ouverture de la fiche générée. docs/SOURCES-CONTRAT.md §2, §8.
import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, Check, ChevronLeft, CloudUpload, Library, Loader2, Sparkles, TriangleAlert, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { fiches, sources, type EtapeSource, type SuggestionSource } from "@/api/jules"
import { ORDRE_MATIERES } from "@/config/matieres"
import { ETAPES, FORMES, LIMITES, TEXTES, stylePerso, type FormeSource } from "@/config/sources"
import { rechargerPerso, useBibliothequePerso } from "./etat"

type Progression = { faites: number; suggestion?: SuggestionSource; erreur?: string }
const RANG_ETAPE: Record<EtapeSource["etape"], number> = { notion: 1, ecriture: 2, verification: 3, fin: 4, erreur: -1 }

export function AjouterCours({ onRetour, onNatif, onFiche }: {
  onRetour: () => void
  onNatif: () => void
  onFiche: (id: string) => void
}) {
  const [forme, setForme] = useState<FormeSource | null>(null)
  const [photos, setPhotos] = useState<File[]>([])
  const [pdf, setPdf] = useState<File | null>(null)
  const [texte, setTexte] = useState("")
  const [matiere, setMatiere] = useState("")
  const [matieres, setMatieres] = useState<{ id: string; nom: string }[]>([])
  const [progression, setProgression] = useState<Progression | null>(null)
  const [refus, setRefus] = useState<string | null>(null)
  const biblio = useBibliothequePerso()

  useEffect(() => {
    fiches.index().then((i) => {
      const rang = (id: string) => { const k = ORDRE_MATIERES.indexOf(id); return k < 0 ? 99 : k }
      setMatieres(i.matieres.map((m) => ({ id: m.id, nom: m.nom.replace(/ \(.*\)$/, "") })).sort((a, b) => rang(a.id) - rang(b.id)))
    }).catch(() => {})
  }, [])

  const quota = biblio?.quota
  const reste = quota ? Math.max(0, quota.par_jour - quota.utilisees) : null
  const pret = forme === "photos" ? photos.length > 0 : forme === "pdf" ? !!pdf : forme === "texte" ? texte.trim().length >= LIMITES.texteMin : false

  const lancer = async () => {
    setRefus(null)
    setProgression({ faites: 0 })
    try {
      const fin = await sources.deposer(
        { photos: forme === "photos" ? photos : undefined, pdf: forme === "pdf" ? pdf ?? undefined : undefined, texte: forme === "texte" ? texte : undefined, matiere: matiere || undefined },
        (e) => setProgression((p) => e.etape === "erreur" ? { ...(p ?? { faites: 0 }), erreur: e.message }
          : { ...(p ?? { faites: 0 }), faites: RANG_ETAPE[e.etape], suggestion: e.etape === "ecriture" ? e.suggestion : p?.suggestion }),
      )
      await rechargerPerso()
      if (fin.etape === "fin") window.setTimeout(() => onFiche(fin.fiche.id), 500)
    } catch (e) {
      setProgression(null)
      setRefus((e as Error).message)
    }
  }

  return (
    <div className="mx-auto max-w-[980px] px-5 pt-16 pb-16 md:px-10 md:pt-8" style={stylePerso}>
      <button onClick={onRetour} className="mb-4 -ml-1 inline-flex items-center gap-1 rounded-full px-1 py-2 text-[0.95rem] font-semibold text-gris hover:text-bleu">
        <ChevronLeft size={16} /> Mes fiches
      </button>
      <h1 className="m-0 text-[2.2rem] leading-tight font-bold text-encre">{TEXTES.titreAjout}</h1>
      <p className="mt-1 mb-7 max-w-[640px] text-gris">{TEXTES.sousTitreAjout}</p>

      <AnimatePresence mode="wait" initial={false}>
        {progression ? (
          <Avancement key="avancement" p={progression} onRecommencer={() => setProgression(null)} />
        ) : (
          <motion.div key="choix" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="flex flex-col gap-6">
            {/* Deux cartes sources (patron DinoBot, habillage Jules) */}
            <div className="grid gap-4 md:grid-cols-2">
              <CarteSource Icone={Library} titre={TEXTES.carteNatif.titre} texte={TEXTES.carteNatif.texte} onClick={onNatif} natif />
              <CarteSource Icone={Sparkles} titre={TEXTES.carteDocument.titre} texte={TEXTES.carteDocument.texte} actif onClick={() => {}} />
            </div>

            <section className="rounded-3xl border border-bord bg-white p-5 shadow-relief md:p-7">
              <div role="tablist" aria-label="Forme du document" className="mb-5 flex flex-wrap gap-2">
                {FORMES.map(({ id, nom, Icone }) => (
                  <button key={id} role="tab" aria-selected={forme === id} onClick={() => setForme(id)}
                    className={cn("relative inline-flex items-center gap-2 rounded-full px-4 py-2 text-[0.95rem] font-semibold transition-colors",
                      forme === id ? "text-white" : "bg-nav text-encre hover:bg-(--m-fond)")}>
                    {forme === id && <motion.span layoutId="forme-active" className="absolute inset-0 rounded-full bg-(--m-accent)" transition={{ type: "spring", stiffness: 400, damping: 32 }} />}
                    <Icone size={17} className="relative" /><span className="relative">{nom}</span>
                  </button>
                ))}
              </div>

              <AnimatePresence mode="wait" initial={false}>
                <motion.div key={forme ?? "rien"} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.18 }}>
                  {forme === null && <p className="m-0 text-gris">Choisis la forme de ton document : photos, PDF ou texte.</p>}
                  {forme === "photos" && <Depot multiple accept="image/jpeg,image/png,image/webp,image/heic,.heic" fichiers={photos} max={LIMITES.photos}
                    libelle={TEXTES.deposerPhotos} aide={FORMES[0].aide} onChange={setPhotos} />}
                  {forme === "pdf" && <Depot accept="application/pdf,.pdf" fichiers={pdf ? [pdf] : []} max={1}
                    libelle={TEXTES.deposerPdf} aide={FORMES[1].aide} onChange={(f) => setPdf(f[0] ?? null)} />}
                  {forme === "texte" && (
                    <div>
                      <textarea value={texte} onChange={(e) => setTexte(e.target.value.slice(0, LIMITES.texte))} rows={9} placeholder={TEXTES.placeholderTexte}
                        className="w-full resize-y rounded-2xl border border-bord bg-white p-4 text-[1rem] leading-relaxed outline-none focus:border-(--m-accent) focus:ring-4 focus:ring-(--m-fond)" />
                      <p className="m-0 mt-1 text-right text-[0.8rem] text-gris tabular-nums">{texte.length.toLocaleString("fr")} / {LIMITES.texte.toLocaleString("fr")}</p>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>

              {forme && (
                <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
                  <label className="flex flex-col gap-1.5 text-[0.9rem] font-semibold text-gris">
                    {TEXTES.matiere}
                    <select value={matiere} onChange={(e) => setMatiere(e.target.value)}
                      className="h-11 min-w-[220px] rounded-xl border border-bord bg-white px-3 text-[1rem] font-normal text-encre outline-none focus:border-(--m-accent)">
                      <option value="">{TEXTES.matiereInconnue}</option>
                      {matieres.map((m) => <option key={m.id} value={m.id}>{m.nom}</option>)}
                    </select>
                  </label>
                  <div className="flex flex-col items-end gap-1.5">
                    <motion.button whileHover={pret ? { y: -2 } : undefined} whileTap={pret ? { scale: 0.97 } : undefined}
                      disabled={!pret || reste === 0} onClick={lancer}
                      className="inline-flex items-center gap-2 rounded-2xl bg-(--m-accent) px-6 py-3 text-[1.02rem] font-semibold text-white shadow-relief-haut disabled:opacity-40">
                      <Sparkles size={18} /> {TEXTES.generer}
                    </motion.button>
                    {quota && reste !== null && <span className="text-[0.82rem] text-gris">{TEXTES.quota(reste, quota.par_jour)}</span>}
                  </div>
                </div>
              )}
              {refus && <p role="alert" className="mt-4 mb-0 flex items-start gap-2 rounded-2xl bg-[#FDECEE] px-4 py-3 text-[0.95rem] text-rouge"><TriangleAlert size={18} className="mt-0.5 shrink-0" />{refus}</p>}
            </section>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function CarteSource({ Icone, titre, texte, onClick, actif, natif }: {
  Icone: typeof Library; titre: string; texte: string; onClick: () => void; actif?: boolean; natif?: boolean
}) {
  return (
    <motion.button onClick={onClick} whileHover={{ y: -3 }} whileTap={{ scale: 0.98 }} aria-pressed={actif}
      className={cn("group relative flex items-center gap-4 overflow-hidden rounded-3xl border-2 bg-white p-5 text-left shadow-relief transition-colors",
        actif ? "border-(--m-accent)" : "border-bord hover:border-bleu")}>
      <span aria-hidden className={cn("absolute -right-10 -bottom-12 size-36 rounded-full transition-transform duration-500 group-hover:scale-125", natif ? "bg-bleu-clair" : "bg-(--m-fond)")} />
      <span className={cn("relative grid size-13 shrink-0 place-items-center rounded-2xl", natif ? "bg-bleu-clair text-bleu" : "bg-(--m-fond) text-(--m-texte)")}><Icone size={26} /></span>
      <span className="relative min-w-0 flex-1">
        <b className="block text-[1.1rem] text-encre">{titre}</b>
        <span className="block text-[0.93rem] leading-snug text-gris">{texte}</span>
      </span>
      {natif ? <ArrowRight size={19} className="relative shrink-0 text-bleu transition-transform group-hover:translate-x-1" />
        : <span className="relative grid size-6 shrink-0 place-items-center rounded-full bg-(--m-accent) text-white"><Check size={15} /></span>}
    </motion.button>
  )
}

function Depot({ multiple, accept, fichiers, max, libelle, aide, onChange }: {
  multiple?: boolean; accept: string; fichiers: File[]; max: number; libelle: string; aide: string; onChange: (f: File[]) => void
}) {
  const champ = useRef<HTMLInputElement>(null)
  const [survol, setSurvol] = useState(false)
  const ajouter = (liste: FileList | null) => {
    if (!liste) return
    const nouveaux = Array.from(liste)
    onChange(multiple ? [...fichiers, ...nouveaux].slice(0, max) : nouveaux.slice(0, 1))
  }
  const apercus = useApercus(fichiers)
  return (
    <div>
      <button type="button" onClick={() => champ.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setSurvol(true) }} onDragLeave={() => setSurvol(false)}
        onDrop={(e) => { e.preventDefault(); setSurvol(false); ajouter(e.dataTransfer.files) }}
        className={cn("flex w-full flex-col items-center gap-2 rounded-2xl border-2 border-dashed px-6 py-9 text-center transition-colors",
          survol ? "border-(--m-accent) bg-(--m-fond)" : "border-bord bg-nav hover:border-(--m-accent) hover:bg-(--m-fond)")}>
        <motion.span animate={survol ? { y: -4, scale: 1.08 } : { y: 0, scale: 1 }} className="grid size-14 place-items-center rounded-2xl bg-white text-(--m-texte) shadow-relief"><CloudUpload size={28} /></motion.span>
        <b className="text-encre">{libelle}</b>
        <span className="text-[0.9rem] text-gris">{aide}</span>
      </button>
      <input ref={champ} type="file" hidden multiple={multiple} accept={accept} onChange={(e) => { ajouter(e.target.files); e.target.value = "" }} />
      {fichiers.length > 0 && (
        <ul className="m-0 mt-4 flex list-none flex-wrap gap-3 p-0">
          <AnimatePresence>
            {fichiers.map((f, i) => (
              <motion.li key={`${f.name}-${i}`} layout initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}
                className="relative flex items-center gap-2.5 rounded-2xl border border-bord bg-white p-2 pr-3 shadow-relief">
                {apercus[i] ? <img src={apercus[i]!} alt="" className="size-14 rounded-xl object-cover" /> // lgtm[js/xss-through-dom]
                  : <span className="grid size-14 place-items-center rounded-xl bg-(--m-fond) text-[0.8rem] font-bold text-(--m-texte)">PDF</span>}
                <span className="max-w-[160px] truncate text-[0.9rem] text-encre">{f.name}</span>
                <button onClick={() => onChange(fichiers.filter((_, k) => k !== i))} aria-label={`${TEXTES.retirer} ${f.name}`}
                  className="rounded-full p-1 text-gris hover:bg-survol hover:text-rouge"><X size={15} /></button>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      )}
    </div>
  )
}

function useApercus(fichiers: File[]): (string | null)[] {
  const [urls, setUrls] = useState<(string | null)[]>([])
  useEffect(() => {
    const u = fichiers.map((f) => {
      if (!f.type.startsWith("image/") || f.type === "image/heic") return null
      const url = URL.createObjectURL(f)
      return url.startsWith("blob:") ? url : null
    })
    setUrls(u)
    return () => u.forEach((x) => x && URL.revokeObjectURL(x))
  }, [fichiers])
  return urls
}

function Avancement({ p, onRecommencer }: { p: Progression; onRecommencer: () => void }) {
  const fini = p.faites >= 4
  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
      className="mx-auto flex max-w-[560px] flex-col gap-5 rounded-3xl border border-bord bg-white p-6 shadow-relief md:p-8" aria-live="polite">
      <div className="flex items-center gap-4">
        <motion.img src="/api/persona/avatar" alt="Jules" className="size-14 rounded-full border-4 border-(--m-fond) bg-bleu-clair object-cover"
          animate={p.erreur ? { rotate: 0 } : { rotate: [0, -6, 6, 0] }} transition={{ repeat: p.erreur || fini ? 0 : Infinity, duration: 1.6 }} />
        <b className="text-[1.15rem] text-encre">{p.erreur ? "Ça n'a pas marché" : fini ? "Ta fiche est prête !" : "Jules fait ta fiche…"}</b>
      </div>
      <ol className="m-0 flex list-none flex-col gap-3 p-0">
        {ETAPES.map((e, i) => {
          const faite = p.faites > i, enCours = !p.erreur && p.faites === i
          return (
            <li key={e.id} className="flex items-center gap-3">
              <span className={cn("grid size-8 shrink-0 place-items-center rounded-full transition-colors",
                faite ? "bg-(--m-accent) text-white" : enCours ? "bg-(--m-fond) text-(--m-texte)" : "bg-nav text-gris")}>
                {faite ? <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }}><Check size={16} /></motion.span>
                  : enCours ? <Loader2 size={16} className="animate-spin" /> : <span className="text-[0.85rem] font-bold">{i + 1}</span>}
              </span>
              <span className={cn("text-[1rem]", faite || enCours ? "text-encre" : "text-gris")}>{e.nom}</span>
              {e.id === "notion" && p.suggestion && (
                <motion.span initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                  className="ml-auto truncate rounded-full bg-(--m-fond) px-3 py-1 text-[0.85rem] font-semibold text-(--m-texte)">
                  {p.suggestion.titre_notion ?? TEXTES.nonClasse}
                </motion.span>
              )}
            </li>
          )
        })}
      </ol>
      {p.suggestion?.avertissement && <p className="m-0 flex items-start gap-2 rounded-2xl bg-[#FFF8EC] px-4 py-2.5 text-[0.92rem] text-[#7A4B00]"><TriangleAlert size={16} className="mt-0.5 shrink-0" />{p.suggestion.avertissement}</p>}
      {p.erreur && (
        <>
          <p role="alert" className="m-0 rounded-2xl bg-[#FDECEE] px-4 py-3 text-[0.95rem] text-rouge">{p.erreur}</p>
          <button onClick={onRecommencer} className="self-start rounded-2xl bg-encre px-5 py-2.5 font-semibold text-white">{TEXTES.recommencer}</button>
        </>
      )}
    </motion.section>
  )
}
