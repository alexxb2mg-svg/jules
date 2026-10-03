// Rendu d'une leçon bloc par bloc. Un type de bloc = un composant dans RENDUS : en ajouter un ne touche rien d'autre.
// Le juste/faux vient du serveur (verifier_reponse côté Python), jamais du modèle.
import { useState, type ReactNode } from "react"
import { AnimatePresence, motion } from "framer-motion"
import katex from "katex"
import type { VariantProps } from "class-variance-authority"
import { Check, Lightbulb, Target, BookOpenText, PenLine, Sparkles, MessageSquareText, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useMotion } from "@/lib/motion"
import { useIsMobile } from "@/hooks/use-mobile"
import { buttonVariants } from "@/components/ui/button"
import { Pastille } from "@/components/ui/pastille"
import { blocVariants, formuleVariants, titreVariants } from "@/components/ui/variantes"
import { cours, type Bloc, type EtatBloc, type Progression, type Tentative } from "@/api/jules"

type TypeCadre = NonNullable<VariantProps<typeof blocVariants>["type"]>

type Ctx = {
  session: string
  etat: EtatBloc
  onProgression: (p: Progression) => void
  /** Signale au panneau Jules qu'il doit relire la conversation (Jules a pu y réagir). */
  onJulesARepondu: () => void
}

/** Mise en forme minimale **gras** des contenus de leçon. */
function Riche({ texte }: { texte: string }) {
  return <>{texte.split(/(\*\*[^*]+\*\*)/g).map((p, i) => p.startsWith("**") ? <strong key={i} className="font-semibold text-encre">{p.slice(2, -2)}</strong> : p)}</>
}

/** Dernier recours pour une phrase seule trop longue (> limite) : coupe à la virgule la plus proche du milieu,
 *  hors parenthèses et hors gras. D'abord devant une conjonction (ou, et, mais, donc, car…), jamais dans une
 *  énumération de points (« A, M, B ») ; à défaut, à n'importe quelle virgule si la phrase dépasse encore la limite de plus de 5 %. */
function coupeVirgule(ph: string, limite: number): string[] {
  if (ph.length <= limite) return [ph]
  const cherche = (conjonction: boolean) => {
    let profondeur = 0, gras = false, formule = false, meilleur = -1
    for (let i = 0; i < ph.length - 1; i++) {
      const c = ph[i]
      if (c === "$") { formule = !formule; continue }
      if (formule) continue
      if (c === "(" || c === "[") profondeur++
      else if (c === ")" || c === "]") profondeur--
      else if (c === "*" && ph[i + 1] === "*") { gras = !gras; i++ }
      else if (c === "," && profondeur === 0 && !gras && ph[i + 1] === " " && i > 40 && ph.length - i > 40
        && !/(?:^|\s)[A-Z]$/.test(ph.slice(0, i))
        && (!conjonction || /^ (?:ou|et|mais|donc|car|alors|sinon|puis|tandis) /.test(ph.slice(i + 1, i + 12)))
        && (meilleur < 0 || Math.abs(i - ph.length / 2) < Math.abs(meilleur - ph.length / 2))) meilleur = i
    }
    return meilleur
  }
  let coupe = cherche(true)
  if (coupe < 0 && ph.length > limite * 1.05) coupe = cherche(false)
  if (coupe < 0) return [ph]
  return [...coupeVirgule(ph.slice(0, coupe + 1), limite), ...coupeVirgule(ph.slice(coupe + 2), limite)]
}

/** Découpe un long paragraphe en paragraphes plus courts, aux fins de phrase seulement (jamais au milieu d'une
 *  phrase, d'un passage en gras ni d'une parenthèse). Ordre et mots inchangés ; seul l'affichage est aéré. */
function decouper(texte: string, max = 140): string[] {
  if (texte.length <= max) return [texte]
  const morceaux = texte.replace(/([.!?…]\*{0,2}[»)]?)\s+(?=[A-ZÀ-ÖØ-Þ«(*])/g, "$1\u0001").split("\u0001")
    // Phrase vraiment longue (plus d'une fois et demie la limite) : on la coupe aussi après un point-virgule.
    .flatMap((ph) => (ph.length > max * 1.5 ? ph.replace(/(;\*{0,2})\s+/g, "$1\u0002").split("\u0002") : [ph]))
    .flatMap((ph) => coupeVirgule(ph, max * 1.5))
  const phrases: string[] = []
  for (const m of morceaux) {
    const dernier = phrases[phrases.length - 1]
    // Coupure fausse : gras ouvert non refermé, parenthèse ouverte, initiale seule (« M. Dupont »), abréviation.
    const ouvert = dernier !== undefined && ((dernier.match(/\*\*/g) ?? []).length % 2 === 1
      || (dernier.match(/\(/g) ?? []).length > (dernier.match(/\)/g) ?? []).length
      || /(?:^|\s)(?:[A-ZÀ-Þ]|cf|p|etc|ex|env|fig|n°)\.$/.test(dernier))
    if (ouvert) phrases[phrases.length - 1] = `${dernier} ${m}`
    else phrases.push(m)
  }
  const paragraphes: string[] = []
  for (const ph of phrases) {
    const dernier = paragraphes[paragraphes.length - 1]
    if (dernier !== undefined && dernier.length + ph.length + 1 <= max) paragraphes[paragraphes.length - 1] = `${dernier} ${ph}`
    else paragraphes.push(ph)
  }
  return paragraphes
}

/** Formule dans un contenu : $…$ (KaTeX) ou passage en gras qui contient « = », ponctuation qui suit comprise. */
const FORMULE = /((?:\$[^$]+\$|\*\*[^*]*=[^*]*\*\*)[.,;:]?)/

/** Un paragraphe de leçon ; ses formules sortent sur leur propre ligne, centrées (formuleVariants). */
function Paragraphe({ texte }: { texte: string }) {
  return <>{texte.split(FORMULE).map((m, i) => {
    if (i % 2 === 0) return m.trim() && <p key={i} className="text-lecture text-encre/90"><Riche texte={m.trim()} /></p>
    const tex = m.match(/^\$([^$]+)\$(.?)$/)
    return tex
      ? <div key={i} data-formule className={formuleVariants()}><span dangerouslySetInnerHTML={{ __html: katex.renderToString(tex[1], { throwOnError: false }) }} />{tex[2]}</div>
      : <div key={i} data-formule className={formuleVariants()}>{m.replace(/\*\*/g, "")}</div>
  })}</>
}

/** Un bloc de leçon : son type se reconnaît d'un coup d'œil (teinte de fond + icône dans une pastille pleine,
 *  blocVariants) ; filet vert/orange une fois corrigé. Pas de cadre ni d'ombre : l'espace sépare les blocs. */
function Cadre({ Icone, etiquette, type, etat, children }: {
  Icone: typeof Target; etiquette: string; type: TypeCadre; etat?: EtatBloc; children: ReactNode
}) {
  const { entree } = useMotion()
  const lisere = etat === "reussi" ? "succes" : etat === "a_revoir" ? "alerte" : "aucun"
  return (
    <motion.section layout {...entree} data-type={type} className={blocVariants({ type, lisere })}>
      <div className="mb-4 flex items-center gap-3">
        <Pastille ton="bloc" taille="bloc" aria-hidden><Icone size={18} /></Pastille>
        <span className={titreVariants({ niveau: "etiquette", className: "font-sans text-(--b-plein)" })}>{etiquette}</span>
        {etat === "reussi" && <Pastille ton="succes" className="ml-auto"><Check size={15} /> réussi</Pastille>}
        {etat === "a_revoir" && <Pastille ton="alerte" className="ml-auto"><AlertTriangle size={15} /> à revoir</Pastille>}
      </div>
      {children}
    </motion.section>
  )
}

/* ---------------- rendus par type ---------------- */

function Objectifs({ bloc }: { bloc: Extract<Bloc, { type: "objectifs" }> }) {
  return (
    <Cadre Icone={Target} etiquette="Ce que tu vas savoir faire" type="objectifs">
      <ul className="m-0 list-none space-y-2.5 p-0 text-lecture">{bloc.items.map((it) => <li key={it} className="flex gap-2.5"><Check size={19} className="mt-1 shrink-0 text-(--b-plein)" /><span className="min-w-0">{it}</span></li>)}</ul>
    </Cadre>
  )
}

function Texte({ bloc }: { bloc: Extract<Bloc, { type: "texte" }> }) {
  // Téléphone seulement (découpage et formules sur leur ligne) : le bureau garde le paragraphe d'origine, d'un seul tenant.
  const mobile = useIsMobile()
  return (
    <Cadre Icone={BookOpenText} etiquette="À retenir" type="retenir">
      {bloc.titre && <h3 className={titreVariants({ niveau: "bloc", className: "mb-3" })}>{bloc.titre}</h3>}
      <div className="space-y-4">
        {mobile
          ? decouper(bloc.contenu).map((p, i) => <Paragraphe key={i} texte={p} />)
          : <p className="text-lecture text-encre/90"><Riche texte={bloc.contenu} /></p>}
      </div>
    </Cadre>
  )
}

function Exemple({ bloc }: { bloc: Extract<Bloc, { type: "exemple" }> }) {
  const [vues, setVues] = useState(1)
  const { apparition, tap } = useMotion()
  return (
    <Cadre Icone={Sparkles} etiquette="Exemple guidé" type="exemple">
      <p className="mt-0 mb-4 text-lecture font-semibold">{bloc.enonce}</p>
      <ol className="m-0 list-none space-y-3 p-0 text-lecture">
        <AnimatePresence initial={false}>
          {bloc.etapes.slice(0, vues).map((e, i) => (
            <motion.li key={i} {...apparition} className="flex gap-3">
              <Pastille ton="bloc" taille="puce" className="size-7 font-bold">{i + 1}</Pastille>
              <span>{e}</span>
            </motion.li>
          ))}
        </AnimatePresence>
      </ol>
      {vues < bloc.etapes.length && (
        <motion.button {...tap} onClick={() => setVues(vues + 1)} className={buttonVariants({ variant: "sombre", size: "pastille-sm", className: "mt-4 text-(--b-plein)" })}>
          Étape suivante
        </motion.button>
      )}
    </Cadre>
  )
}

function Exercice({ bloc, ctx, numero }: { bloc: Extract<Bloc, { type: "exercice" }>; ctx: Ctx; numero: number }) {
  const [reponse, setReponse] = useState("")
  const [retour, setRetour] = useState<Tentative | null>(null)
  const [indices, setIndices] = useState<string[]>([])
  const [restants, setRestants] = useState(bloc.indices?.length ?? 0)
  const [envoi, setEnvoi] = useState(false)
  const fini = ctx.etat === "reussi" || ctx.etat === "a_revoir"
  const { apparition, tap } = useMotion()

  const valider = async () => {
    if (!reponse.trim() || envoi) return
    setEnvoi(true)
    try {
      const r = await cours.tentative(ctx.session, bloc.index, reponse.trim())
      setRetour(r); ctx.onProgression(r.progression)
      if (r.jules) ctx.onJulesARepondu()
    } finally { setEnvoi(false) }
  }
  const indice = async () => {
    const r = await cours.indice(ctx.session, bloc.index)
    if (r.indice) setIndices((l) => [...l, r.indice!])
    setRestants(r.restants); ctx.onProgression(r.progression)
  }

  return (
    <Cadre Icone={PenLine} etiquette={`Exercice ${numero}`} type="exercice" etat={ctx.etat}>
      <p className="mt-0 mb-4 text-lecture font-semibold">{bloc.enonce}</p>
      <div className="flex gap-2">
        <input value={reponse} onChange={(e) => setReponse(e.target.value)} onKeyDown={(e) => e.key === "Enter" && valider()}
          disabled={fini} inputMode={bloc.forme === "nombre" ? "decimal" : "text"}
          placeholder={bloc.forme === "nombre" ? "Ta réponse (un nombre)" : "Ta réponse"}
          className="h-12 min-w-0 flex-1 rounded-full border-2 border-transparent bg-card px-4 text-courant outline-none placeholder:text-gris focus:border-(--b-plein) disabled:opacity-70" />
        <motion.button {...tap} onClick={valider} disabled={fini || envoi || !reponse.trim()}
          className={buttonVariants({ variant: "matiere", className: "h-12 px-5 text-courant disabled:opacity-40" })}>Vérifier</motion.button>
      </div>

      <AnimatePresence>
        {retour && (
          <motion.div key={retour.tentatives} {...apparition}
            className={cn("mt-3 rounded-2xl px-4 py-3 text-courant",
              retour.juste ? "bg-succes-fond text-succes" : "bg-alerte-fond text-alerte")}>
            <b>{retour.juste ? "Juste !" : ctx.etat === "a_revoir" ? "Pas encore : regarde la correction." : "Pas tout à fait. Jules t'écrit un conseil."}</b>
            {retour.explication && <p className="mt-1 text-encre/90">{retour.explication}</p>}
          </motion.div>
        )}
      </AnimatePresence>

      {indices.map((t, i) => (
        <motion.p key={i} {...apparition} className="mt-2 mb-0 flex gap-2 rounded-2xl bg-bleu-clair px-4 py-3 text-courant">
          <Lightbulb size={17} className="mt-0.5 shrink-0 text-bleu" />{t}
        </motion.p>
      ))}
      {!fini && restants > 0 && (
        <button onClick={indice} className="mt-3 flex min-h-9 items-center gap-1.5 text-petit font-semibold text-bleu hover:underline">
          <Lightbulb size={15} /> Un indice ({restants})
        </button>
      )}
    </Cadre>
  )
}

function Ouverte({ bloc, ctx, consigne, etiquette }: { bloc: Bloc; ctx: Ctx; consigne: string; etiquette: string }) {
  const [texte, setTexte] = useState("")
  const [envoye, setEnvoye] = useState(ctx.etat === "fait")
  const { tap } = useMotion()
  const envoyer = async () => {
    if (!texte.trim()) return
    const r = await cours.tentative(ctx.session, bloc.index, texte.trim())
    setEnvoye(true); ctx.onProgression(r.progression); ctx.onJulesARepondu()
  }
  return (
    <Cadre Icone={MessageSquareText} etiquette={etiquette} type="ouverte" etat={envoye ? "fait" : ctx.etat}>
      <p className="mt-0 mb-4 text-lecture font-semibold">{consigne}</p>
      {envoye ? (
        <p className="m-0 text-courant font-semibold text-succes">Envoyé : Jules te relit à droite.</p>
      ) : (
        <>
          <textarea value={texte} onChange={(e) => setTexte(e.target.value)} rows={3} placeholder="Avec tes mots…"
            className="w-full resize-y rounded-2xl border-2 border-transparent bg-card px-4 py-3 text-courant outline-none placeholder:text-gris focus:border-(--b-plein)" />
          <motion.button {...tap} onClick={envoyer} disabled={!texte.trim()} className={buttonVariants({ variant: "jules", size: "pastille", className: "mt-3 shadow-none disabled:opacity-40" })}>
            Faire relire par Jules
          </motion.button>
        </>
      )}
    </Cadre>
  )
}

/* ---------------- registre ---------------- */

type Rendu = (p: { bloc: Bloc; ctx: Ctx; numero: number }) => ReactNode

export const RENDUS: Record<Bloc["type"], Rendu> = {
  objectifs: ({ bloc }) => <Objectifs bloc={bloc as Extract<Bloc, { type: "objectifs" }>} />,
  texte: ({ bloc }) => <Texte bloc={bloc as Extract<Bloc, { type: "texte" }>} />,
  exemple: ({ bloc }) => <Exemple bloc={bloc as Extract<Bloc, { type: "exemple" }>} />,
  exercice: ({ bloc, ctx, numero }) => <Exercice bloc={bloc as Extract<Bloc, { type: "exercice" }>} ctx={ctx} numero={numero} />,
  question_ouverte: ({ bloc, ctx }) => <Ouverte bloc={bloc} ctx={ctx} etiquette="Explique avec tes mots" consigne={(bloc as Extract<Bloc, { type: "question_ouverte" }>).question} />,
  synthese: ({ bloc, ctx }) => <Ouverte bloc={bloc} ctx={ctx} etiquette="Pour finir" consigne={(bloc as Extract<Bloc, { type: "synthese" }>).consigne} />,
}

export function BlocLecon(p: { bloc: Bloc; ctx: Ctx; numero: number }) {
  const R = RENDUS[p.bloc.type]
  return R ? <>{R(p)}</> : null
}
