// Espace parent — écran principal (#/parent). Reproduit fidèlement toutes les sections de parent.html + parent.js.
// Aucune donnée fictive : tout vient des API. Style cohérent avec les autres modules (Tailwind, cartes, lucide-react).
import { useCallback, useEffect, useRef, useState } from "react"
import {
  Users, AlertTriangle, FileText, StickyNote, MessageSquare, Settings2,
  Volume2, FolderDown, Trash2, Send, Plus, Check, RotateCcw, X,
  ChevronDown, ChevronRight, Bug, Download,
} from "lucide-react"
import { Porte } from "./Porte"
import {
  sessionParent, modulesActifs, alertes as apiAlertes, rapport as apiRapport,
  notes as apiNotes, retours as apiRetours, conversations as apiConversations,
  adaptations as apiAdaptations, dossier as apiDossier,
  libelleRetour,
  type ModuleActif, type Alerte, type Note, type Retour,
  type ConversationResume, type Message, type EtatAdaptations, type Conflit,
  type ChoixAdaptations,
} from "./api"

// -- helpers ------------------------------------------------------------------

const aujourdhui = () => {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

const heure = (iso: string) => {
  if (!iso) return ""
  return new Date(iso).toLocaleString("fr-FR", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })
}

function Carte({ id, titre, Icone, cache, enfants }: {
  id?: string; titre: string; Icone: typeof Users; cache?: boolean; enfants: React.ReactNode
}) {
  if (cache) return null
  return (
    <section id={id} className="rounded-surface bg-card p-5 shadow-relief">
      <div className="mb-3 flex items-center gap-2">
        <Icone className="size-5 text-bleu" />
        <h2 className="text-base font-semibold">{titre}</h2>
      </div>
      {enfants}
    </section>
  )
}

// -- Section Alertes ----------------------------------------------------------

function SectionAlertes({ actif }: { actif: boolean }) {
  const [liste, setListe] = useState<Alerte[]>([])
  const [charge, setCharge] = useState(true)
  useEffect(() => {
    if (!actif) return
    apiAlertes().then(setListe).catch(() => {}).finally(() => setCharge(false))
  }, [actif])
  return (
    <Carte titre="Signaux de vigilance (30 derniers)" Icone={AlertTriangle} cache={!actif} enfants={
      charge ? <p className="text-gris italic">Chargement…</p>
        : liste.length === 0 ? <p className="text-gris italic">Aucun signal.</p>
        : <div className="flex flex-col gap-2">
            {liste.slice(0, 30).map((ev, i) => (
              <div key={i} className="rounded-xl bg-orange-50 px-3 py-2 text-sm">
                <span className="font-semibold">{ev.donnees.niveau}</span>
                <span className="text-gris"> — {heure(ev.horodatage)} : </span>
                <span>{ev.donnees.motif}</span>
              </div>
            ))}
          </div>
    } />
  )
}

// -- Section Rapport ----------------------------------------------------------

function SectionRapport({ actif, jour }: { actif: boolean; jour: string }) {
  const [texte, setTexte] = useState<string | null>(null)
  const [charge, setCharge] = useState(false)
  const [etatEnvoi, setEtatEnvoi] = useState("")

  const charger = useCallback((j: string) => {
    if (!actif) return
    setCharge(true)
    setTexte("Calcul en cours (quelques secondes)…")
    apiRapport.lire(j).then((r) => setTexte(r.texte)).catch((e) => setTexte(`Erreur : ${e.message}`)).finally(() => setCharge(false))
  }, [actif])

  useEffect(() => { charger(jour) }, [jour, charger])

  const envoyer = async () => {
    setEtatEnvoi("Envoi…")
    try {
      const r = await apiRapport.envoyer(jour)
      setEtatEnvoi(r.envoye ? "Envoyé." : (r.erreurs?.length ? `Échec : ${r.erreurs.join(" ; ")}` : "Rien à envoyer ce jour-là."))
    } catch (e) { setEtatEnvoi(`Erreur : ${e instanceof Error ? e.message : e}`) }
  }

  return (
    <Carte titre="Rapport du jour" Icone={FileText} cache={!actif} enfants={
      <>
        <pre className={`whitespace-pre-wrap text-sm ${charge ? "text-gris italic" : ""}`}>{texte}</pre>
        <div className="mt-3 flex items-center gap-3">
          <button onClick={envoyer} className="flex items-center gap-1.5 rounded-lg border border-bord px-3 py-1.5 text-sm font-medium transition hover:bg-bleu-clair/40">
            <Send className="size-4" /> Envoyer ce rapport maintenant
          </button>
          {etatEnvoi && <span className="text-sm text-gris">{etatEnvoi}</span>}
        </div>
      </>
    } />
  )
}

// -- Section Notes (Infos pour Jules) -----------------------------------------

function SectionNotes({ actif }: { actif: boolean }) {
  const [liste, setListe] = useState<Note[]>([])
  const [texte, setTexte] = useState("")
  const [fin, setFin] = useState("")

  const charger = useCallback(() => {
    if (!actif) return
    apiNotes.lister().then(setListe).catch(() => {})
  }, [actif])

  useEffect(charger, [charger])

  const ajouter = async (ev: React.FormEvent) => {
    ev.preventDefault()
    if (!texte.trim()) return
    await apiNotes.ajouter(texte.trim(), fin || null)
    setTexte(""); setFin("")
    charger()
  }

  const supprimer = async (id: string) => {
    await apiNotes.supprimer(id)
    charger()
  }

  return (
    <Carte titre="Infos pour Jules" Icone={StickyNote} cache={!actif} enfants={
      <>
        <p className="mb-3 text-sm text-gris">Ce que le bot doit savoir (contrôle à venir, chapitre en cours…). Il s'en sert avec tact.</p>
        <form onSubmit={ajouter} className="mb-3 flex flex-wrap items-center gap-2">
          <input type="text" value={texte} onChange={(e) => setTexte(e.target.value)} placeholder="Ex. contrôle de maths vendredi sur les fractions" maxLength={500}
            className="min-w-0 flex-1 rounded-lg border border-bord px-3 py-1.5 text-sm focus:border-bleu focus:ring-1 focus:ring-bleu focus:outline-none" />
          <label className="flex items-center gap-1 text-sm text-gris">
            jusqu'au <input type="date" value={fin} onChange={(e) => setFin(e.target.value)}
              className="rounded-lg border border-bord px-2 py-1 text-sm focus:border-bleu focus:outline-none" />
          </label>
          <button type="submit" className="flex items-center gap-1 rounded-lg bg-bleu px-3 py-1.5 text-sm font-medium text-white transition hover:bg-bleu/90">
            <Plus className="size-4" /> Ajouter
          </button>
        </form>
        {liste.length === 0
          ? <p className="text-sm text-gris italic">Aucune info pour le moment.</p>
          : <ul className="flex flex-col gap-1.5">
              {liste.map((n) => (
                <li key={n.id} className="flex items-center gap-2 rounded-xl bg-bleu-clair/30 px-3 py-2 text-sm">
                  <span className="flex-1">{n.texte}{n.jusqu_au && <span className="text-gris"> (jusqu'au {n.jusqu_au})</span>}</span>
                  <button onClick={() => supprimer(n.id)} title="Supprimer" className="shrink-0 text-gris transition hover:text-rouge"><X className="size-4" /></button>
                </li>
              ))}
            </ul>
        }
      </>
    } />
  )
}

// -- Section Retours ----------------------------------------------------------

function SectionRetours({ actif }: { actif: boolean }) {
  const [liste, setListe] = useState<Retour[]>([])
  const [traites, setTraites] = useState(false)

  const charger = useCallback(() => {
    if (!actif) return
    apiRetours.lister(traites).then(setListe).catch(() => {})
  }, [actif, traites])

  useEffect(charger, [charger])

  return (
    <Carte titre="Retours : bugs et idées" Icone={Bug} cache={!actif} enfants={
      <>
        <p className="mb-2 text-sm text-gris">Envoyés avec le petit bouton de chaque page. L'adresse permet de rouvrir la page concernée.</p>
        <label className="mb-3 flex items-center gap-2 text-sm text-gris">
          <input type="checkbox" checked={traites} onChange={(e) => setTraites(e.target.checked)} className="rounded" />
          afficher aussi les retours traités
        </label>
        {liste.length === 0
          ? <p className="text-sm text-gris italic">Aucun retour en attente.</p>
          : <ul className="flex flex-col gap-2">
              {liste.map((r) => (
                <li key={r.id} className="rounded-xl border border-bord px-3 py-2 text-sm">
                  <div>
                    <span className="font-semibold">{libelleRetour(r.type)}</span>
                    {r.auteur && <span className="text-gris"> — {r.auteur}</span>}
                    {r.traite && <span className="text-gris"> (traité)</span>}
                    {" : "}
                    <span className="whitespace-pre-line">{r.texte}</span>
                  </div>
                  <div className="mt-1 text-xs text-gris">
                    {heure(r.cree_le)}
                    {r.adresse && <> · <a href={r.adresse} target="_blank" rel="noopener noreferrer" className="underline">{r.adresse}</a></>}
                    {r.ecran && <> · écran {r.ecran}</>}
                  </div>
                  <div className="mt-2 flex gap-2">
                    <button onClick={async () => { await apiRetours.basculer(r.id, !r.traite); charger() }}
                      className="flex items-center gap-1 rounded-lg border border-bord px-2 py-1 text-xs transition hover:bg-bleu-clair/40">
                      {r.traite ? <><RotateCcw className="size-3" /> Rouvrir</> : <><Check className="size-3" /> Traité</>}
                    </button>
                    <button onClick={async () => { await apiRetours.supprimer(r.id); charger() }}
                      className="flex items-center gap-1 rounded-lg border border-bord px-2 py-1 text-xs text-rouge transition hover:bg-rouge/10">
                      <Trash2 className="size-3" /> Supprimer
                    </button>
                  </div>
                </li>
              ))}
            </ul>
        }
      </>
    } />
  )
}

// -- Section Conversations ----------------------------------------------------

function SectionConversations({ jour, onSupprimee }: { jour: string; onSupprimee: () => void }) {
  const [liste, setListe] = useState<ConversationResume[]>([])
  const [charge, setCharge] = useState(true)

  const charger = useCallback(() => {
    setCharge(true)
    apiConversations.lister(jour).then(setListe).catch(() => {}).finally(() => setCharge(false))
  }, [jour])

  useEffect(charger, [charger])

  const pleines = liste.filter((c) => c.nb > 0)

  return (
    <Carte titre="Conversations du jour" Icone={MessageSquare} enfants={
      charge ? <p className="text-gris italic">Chargement…</p>
        : pleines.length === 0 ? <p className="text-gris italic">Aucune conversation ce jour-là.</p>
        : <div className="flex flex-col gap-2">
            {pleines.map((c) => (
              <ConversationDetail key={c.id} conv={c} onSupprimee={() => { charger(); onSupprimee() }} />
            ))}
          </div>
    } />
  )
}

function ConversationDetail({ conv, onSupprimee }: { conv: ConversationResume; onSupprimee: () => void }) {
  const [ouvert, setOuvert] = useState(false)
  const [messages, setMessages] = useState<Message[] | null>(null)

  useEffect(() => {
    if (!ouvert || messages) return
    apiConversations.lire(conv.id).then((c) => setMessages(c.messages)).catch(() => {})
  }, [ouvert, messages, conv.id])

  const supprimer = async () => {
    const titre = conv.titre || conv.mode
    if (!window.confirm(`Effacer définitivement « ${titre} » (messages, photos et analyses) ? Impossible de revenir en arrière.`)) return
    try {
      await apiConversations.supprimer(conv.id)
      onSupprimee()
    } catch (e) { window.alert(`Erreur : ${e instanceof Error ? e.message : e}`) }
  }

  return (
    <div className="rounded-xl border border-bord">
      <button onClick={() => setOuvert(!ouvert)} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-medium transition hover:bg-bleu-clair/20">
        {ouvert ? <ChevronDown className="size-4 shrink-0 text-gris" /> : <ChevronRight className="size-4 shrink-0 text-gris" />}
        <span className="flex-1">{conv.titre || conv.mode} — {heure(conv.debut)} ({conv.nb} messages)</span>
      </button>
      {ouvert && (
        <div className="border-t border-bord px-3 py-2">
          {messages === null
            ? <p className="text-sm text-gris italic">Chargement…</p>
            : <>
                {messages.map((m, i) => (
                  <div key={i} className="mb-2 text-sm">
                    <span className="font-semibold">{m.role === "eleve" ? "Élève" : "Bot"}{m.images?.length ? ` [${m.images.length} photo(s)]` : ""} : </span>
                    <span className="whitespace-pre-line">{m.texte}</span>
                  </div>
                ))}
                <button onClick={supprimer} className="mt-2 flex items-center gap-1 rounded-lg bg-rouge/10 px-3 py-1.5 text-sm font-medium text-rouge transition hover:bg-rouge/20">
                  <Trash2 className="size-4" /> Effacer cette conversation
                </button>
              </>
          }
        </div>
      )}
    </div>
  )
}

// -- Section Adaptations (Aménagements) ---------------------------------------

function SectionAdaptations() {
  const [etat, setEtat] = useState<EtatAdaptations | null>(null)
  const [coches, setCoches] = useState<Set<string>>(new Set())
  const [prefPolice, setPrefPolice] = useState("")
  const [prefFond, setPrefFond] = useState("")
  const [lectureAuto, setLectureAuto] = useState(false)
  const [conflits, setConflits] = useState<Conflit[]>([])
  const [etatMsg, setEtatMsg] = useState("")

  useEffect(() => {
    apiAdaptations.charger().then((e) => {
      setEtat(e)
      setCoches(new Set(e.amenagements.filter((a) => a.coche).map((a) => a.id)))
      setPrefPolice(e.preferences.police.valeur)
      setPrefFond(e.preferences.fond.valeur)
      setLectureAuto(e.lecture_automatique)
      setConflits(e.conflits)
    }).catch(() => {})
  }, [])

  const lireChoix = useCallback((): ChoixAdaptations => {
    const preferences: Record<string, string> = { police: prefPolice, fond: prefFond }
    if (lectureAuto) preferences["lecture-vocale"] = "automatique"
    return { amenagements: [...coches], preferences }
  }, [coches, prefPolice, prefFond, lectureAuto])

  const apercu = useCallback(async () => {
    try {
      const r = await apiAdaptations.apercu(lireChoix())
      setConflits(r.conflits)
      setEtatMsg("Modifications non enregistrées.")
    } catch (e) { setEtatMsg(`Erreur : ${e instanceof Error ? e.message : e}`) }
  }, [lireChoix])

  const toggleAmenagement = (id: string) => {
    setCoches((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
    // apercu déclenché par l'effet ci-dessous
  }

  // Aperçu à chaque changement de choix
  const prevChoix = useRef<string>("")
  useEffect(() => {
    if (!etat) return
    const sig = JSON.stringify(lireChoix())
    if (sig === prevChoix.current) return
    prevChoix.current = sig
    apercu()
  }, [etat, lireChoix, apercu])

  const enregistrer = async (ev: React.FormEvent) => {
    ev.preventDefault()
    setEtatMsg("Enregistrement…")
    try {
      const e = await apiAdaptations.enregistrer(lireChoix())
      setEtat(e)
      setCoches(new Set(e.amenagements.filter((a) => a.coche).map((a) => a.id)))
      setPrefPolice(e.preferences.police.valeur)
      setPrefFond(e.preferences.fond.valeur)
      setLectureAuto(e.lecture_automatique)
      setConflits(e.conflits)
      setEtatMsg("Enregistré.")
    } catch (e) { setEtatMsg(`Erreur : ${e instanceof Error ? e.message : e}`) }
  }

  if (!etat) return null

  const pap = etat.amenagements.filter((a) => !a.rubrique_autres)
  const autres = etat.amenagements.filter((a) => a.rubrique_autres)

  const ligneAmenagement = (a: typeof etat.amenagements[0]) => (
    <li key={a.id} className="flex items-start gap-2 py-1">
      <input type="checkbox" checked={coches.has(a.id)} onChange={() => toggleAmenagement(a.id)}
        data-amenagement={a.id} className="mt-0.5 rounded" />
      <span className="text-sm">
        {a.rubrique_autres
          ? <>{a.reference ? `${a.reference.texte} (libellé ${a.reference.nom_niveau}, p. ${a.reference.page})` : a.id}<em className="text-gris"> : {a.mention}</em></>
          : <>{a.texte} (p. {a.page})</>
        }
      </span>
    </li>
  )

  return (
    <Carte titre="Aménagements" Icone={Settings2} enfants={
      <>
        <p className="mb-1 text-sm text-gris">
          Cochez les aménagements du plan d'accompagnement de l'élève sur lesquels Jules peut agir. Libellés du modèle officiel, niveau <span className="font-medium">{etat.nom_niveau}{etat.niveau_reconnu ? "" : " (classe non reconnue)"}</span>.
        </p>
        <p className="mb-3 text-sm text-gris">
          Fonctionnalité expérimentale : ces aménagements ne sont pas relus par un professionnel et ne remplacent pas un avis médical ou pédagogique.
        </p>
        <form onSubmit={enregistrer}>
          <fieldset className="mb-4 rounded-xl border border-bord p-3">
            <legend className="px-2 text-sm font-semibold">Aménagements du PAP</legend>
            <ul>{pap.map(ligneAmenagement)}</ul>
          </fieldset>
          {autres.length > 0 && (
            <fieldset className="mb-4 rounded-xl border border-bord p-3">
              <legend className="px-2 text-sm font-semibold">
                {etat.rubrique_autres.page ? `${etat.rubrique_autres.titre} (p. ${etat.rubrique_autres.page})` : etat.rubrique_autres.titre}
              </legend>
              <ul>{autres.map(ligneAmenagement)}</ul>
            </fieldset>
          )}
          <fieldset className="mb-4 rounded-xl border border-bord p-3">
            <legend className="px-2 text-sm font-semibold">Préférences d'affichage (hors PAP)</legend>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-2 text-sm">
                Police
                <select value={prefPolice} onChange={(e) => setPrefPolice(e.target.value)}
                  className="rounded-lg border border-bord px-2 py-1 text-sm focus:border-bleu focus:outline-none">
                  {etat.preferences.police.choix.map((c) => <option key={c.valeur} value={c.valeur}>{c.libelle}</option>)}
                </select>
              </label>
              <label className="flex items-center gap-2 text-sm">
                Fond
                <select value={prefFond} onChange={(e) => setPrefFond(e.target.value)}
                  className="rounded-lg border border-bord px-2 py-1 text-sm focus:border-bleu focus:outline-none">
                  {etat.preferences.fond.choix.map((c) => <option key={c.valeur} value={c.valeur}>{c.libelle}</option>)}
                </select>
              </label>
            </div>
            <label className="mt-2 flex items-center gap-2 text-sm">
              <input type="checkbox" checked={lectureAuto} onChange={(e) => setLectureAuto(e.target.checked)} className="rounded" />
              Lecture automatique : chaque réponse de Jules est lue à voix haute
            </label>
          </fieldset>
          {conflits.length > 0 && (
            <div className="mb-3 rounded-xl bg-orange-50 px-4 py-3 text-sm" role="status" aria-live="polite">
              <p className="font-medium">À savoir : ces réglages s'appliquent tous, mais leur combinaison a un effet à surveiller.</p>
              <ul className="mt-1 list-inside list-disc">
                {conflits.map((c) => <li key={c.id}>{c.message}</li>)}
              </ul>
            </div>
          )}
          <div className="flex items-center gap-3">
            <button type="submit" className="rounded-lg bg-bleu px-4 py-1.5 text-sm font-medium text-white transition hover:bg-bleu/90">Enregistrer</button>
            {etatMsg && <span className="text-sm text-gris">{etatMsg}</span>}
          </div>
        </form>
      </>
    } />
  )
}

// -- Section Lecture vocale ---------------------------------------------------

function SectionLectureVocale() {
  const [etat, setEtat] = useState("Vérification des voix…")

  useEffect(() => {
    const DISPONIBLE = "Lecture vocale disponible sur cet appareil (voix installées localement)."
    const INDISPONIBLE = "Lecture vocale indisponible sur cet appareil : aucune voix installée localement."

    const verifier = () => {
      if (typeof speechSynthesis === "undefined") { setEtat(INDISPONIBLE); return }
      const voix = speechSynthesis.getVoices().filter((v) => v.localService)
      setEtat(voix.length > 0 ? DISPONIBLE : INDISPONIBLE)
    }

    verifier()
    if (typeof speechSynthesis !== "undefined" && speechSynthesis.addEventListener) {
      speechSynthesis.addEventListener("voiceschanged", verifier)
      return () => speechSynthesis.removeEventListener("voiceschanged", verifier)
    }
  }, [])

  return (
    <Carte titre="Lecture vocale" Icone={Volume2} enfants={
      <>
        <p className="mb-2 text-sm text-gris">{etat}</p>
        <p className="text-sm text-gris">
          Seules les voix installées sur l'appareil sont utilisées : le texte lu ne part jamais sur Internet.
          Ce constat vaut pour l'appareil qui affiche cette page ; ouvrez-la sur celui de l'élève pour savoir ce qu'il en est chez lui.
        </p>
      </>
    } />
  )
}

// -- Section Dossier ----------------------------------------------------------

function SectionDossier({ onEfface }: { onEfface: () => void }) {
  const [mot, setMot] = useState("")
  const [etatMsg, setEtatMsg] = useState("")
  const [enCours, setEnCours] = useState(false)

  const effacer = async (ev: React.FormEvent) => {
    ev.preventDefault()
    if (mot.trim().toUpperCase() !== "EFFACER") return
    if (!window.confirm("Dernière vérification : tout le dossier de l'élève va être effacé, sans retour possible. Continuer ?")) return
    setEnCours(true)
    setEtatMsg("Effacement…")
    try {
      const r = await apiDossier.effacer(mot)
      const e = r.efface
      setEtatMsg(`Dossier effacé : ${e.conversations} conversation(s), ${e.evenements} analyse(s), ${e.bilans} fichier(s) de bilans.`)
      setMot("")
      onEfface()
    } catch (e) {
      setEtatMsg(`Erreur : ${e instanceof Error ? e.message : e}`)
      setEnCours(false)
    }
  }

  return (
    <Carte titre="Le dossier de l'élève" Icone={FolderDown} enfants={
      <>
        <p className="mb-3 text-sm text-gris">
          Tout ce que Jules garde reste sur cet ordinateur : conversations, photos, notions travaillées, signaux, bilans envoyés et vos notes. Vous pouvez le récupérer ou l'effacer quand vous voulez.
        </p>
        <a href={apiDossier.exportUrl} download
          className="inline-flex items-center gap-2 rounded-lg border border-bord px-3 py-1.5 text-sm font-medium transition hover:bg-bleu-clair/40">
          <Download className="size-4" /> Télécharger tout le dossier (.zip)
        </a>
        <div className="mt-4 rounded-xl border-2 border-rouge/30 bg-rouge/5 p-4">
          <h3 className="mb-2 flex items-center gap-2 font-semibold text-rouge"><Trash2 className="size-4" /> Tout effacer</h3>
          <p className="mb-1 text-sm">
            Efface définitivement les conversations, les photos, les notions suivies, les signaux, les bilans et vos notes. <strong>Impossible de revenir en arrière</strong> : téléchargez d'abord le dossier si vous voulez le garder.
          </p>
          <p className="mb-3 text-sm text-gris">
            Restent en place : le profil de l'élève, les réglages et les codes d'accès. Ce qui a déjà été envoyé ailleurs (Telegram…) ne peut pas être effacé d'ici.
          </p>
          <form onSubmit={effacer} className="flex flex-wrap items-center gap-2">
            <label htmlFor="effacer-mot" className="text-sm">Pour confirmer, tapez <strong>EFFACER</strong> :</label>
            <input id="effacer-mot" type="text" autoComplete="off" spellCheck={false} value={mot} onChange={(e) => setMot(e.target.value)}
              className="rounded-lg border border-bord px-3 py-1.5 text-sm focus:border-rouge focus:ring-1 focus:ring-rouge focus:outline-none" />
            <button type="submit" disabled={mot.trim().toUpperCase() !== "EFFACER" || enCours}
              className="rounded-lg bg-rouge px-3 py-1.5 text-sm font-medium text-white transition hover:bg-rouge/90 disabled:opacity-50">
              Tout effacer
            </button>
          </form>
          {etatMsg && <p className="mt-2 text-sm text-gris">{etatMsg}</p>}
        </div>
      </>
    } />
  )
}

// -- Écran principal ----------------------------------------------------------

export function Parent() {
  const [acces, setAcces] = useState<boolean | null>(null) // null = vérification en cours
  const [modules, setModules] = useState<ModuleActif[]>([])
  const [jour, setJour] = useState(aujourdhui)
  const [cle, setCle] = useState(0) // incrémenter pour forcer le rechargement

  const actif = (id: string) => modules.some((m) => m.id === id)

  // Vérifier la session au montage
  useEffect(() => {
    sessionParent.etat()
      .then((s) => { if (s.parent) { setAcces(true) } else { setAcces(false) } })
      .catch(() => setAcces(false))
  }, [])

  // Charger les modules actifs après accès
  useEffect(() => {
    if (!acces) return
    modulesActifs().then(setModules).catch(() => {})
  }, [acces])

  if (acces === null) {
    return <div className="flex h-full items-center justify-center"><p className="text-gris">Vérification…</p></div>
  }

  if (!acces) {
    return <Porte onAcces={() => setAcces(true)} />
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        {/* En-tête */}
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-bleu text-white">
            <Users className="size-5" />
          </div>
          <h1 className="flex-1 text-xl font-bold text-bleu">Espace parent</h1>
          <input type="date" value={jour} onChange={(e) => setJour(e.target.value)}
            className="rounded-lg border border-bord px-3 py-1.5 text-sm focus:border-bleu focus:ring-1 focus:ring-bleu focus:outline-none" />
        </div>

        {/* Sections */}
        <div className="flex flex-col gap-6">
          <SectionAlertes actif={actif("vigilance")} />
          <SectionRapport actif={actif("rapport")} jour={jour} />
          <SectionNotes actif={actif("memoire")} />
          <SectionRetours actif={actif("retours")} />
          <SectionConversations jour={jour} onSupprimee={() => setCle((k) => k + 1)} key={`conv-${cle}`} />
          <SectionAdaptations />
          <SectionLectureVocale />
          <SectionDossier onEfface={() => setCle((k) => k + 1)} />
        </div>
      </div>
    </div>
  )
}
