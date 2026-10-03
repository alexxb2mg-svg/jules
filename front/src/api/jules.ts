// Client HTTP du serveur Jules (FastAPI). Seul point d'accès réseau du front : tout passe par ici.
// Les formes reprennent exactement les réponses de jules/web/app.py et jules/modules/cours.py.
import type { Fiche, IndexFiches } from "@/modules/fiches/types"

async function api<T>(chemin: string, init?: RequestInit): Promise<T> {
  const r = await fetch(chemin, { credentials: "same-origin", ...init })
  if (!r.ok) {
    let detail = `${r.status}`
    try { detail = (await r.json()).detail ?? detail } catch { /* corps non JSON */ }
    throw new Error(detail)
  }
  return r.json() as Promise<T>
}
const json = (corps: unknown, method = "POST"): RequestInit => ({
  method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corps),
})

/* ---- session, infos de l'interface (persona, leviers dys) ---- */

export type EtatSession = { role: string | null; eleve: boolean; parent: boolean; distant?: boolean }
export type Infos = {
  prenom: string
  persona: { id: string; nom: string; accueil: string; couleurs: Record<string, string>; avatar: boolean }
  leviers: Record<string, unknown>
  leviers_css: Record<string, string>
  /** Module 'retours' : testeurs déclarés dans le profil (qui peut signer un retour). */
  retours?: { types: string[]; testeurs: string[] }
  /** Module 'outils' : catalogue des outils isolés disponibles (calculatrice…). */
  outils?: { catalogue: { id: string; titre?: string; evenements?: string[] }[] }
  /** Module 'figures' : bornes des curseurs d'une figure de la discussion, par gabarit puis par valeur. */
  figures?: BornesFigures
}
export type BornesFigures = Record<string, Record<string, { min: number; max: number; pas: number; defaut: number }>>

export const session = {
  etat: () => api<EtatSession>("/api/session"),
  ouvrir: (code: string) => api<{ role: string }>("/api/session", json({ code })),
}
export const infos = () => api<Infos>("/api/infos")

/* ---- fiches visuelles (aucun appel IA) ---- */

let indexEnCours: Promise<IndexFiches> | null = null
export const fiches = {
  /** Index matières → notions ; une seule requête pour toute la session de la page. */
  index: () => (indexEnCours ??= api<IndexFiches>("/api/eleve/fiches_visuelles/notions").catch((e) => { indexEnCours = null; throw e })),
  lire: (notion: string) => api<Fiche>(`/api/eleve/fiches_visuelles/notions/${encodeURIComponent(notion)}`),
  /** Point d'accroche « bloc_consulte » des extensions : rien n'est attendu en retour. */
  blocConsulte: (adresse: string, notion: string) => { api("/api/seance/bloc_consulte", json({ adresse, notion })).catch(() => {}) },
}

/* ---- conversations (chat avec Jules) ---- */

export type MessageJules = { role: "eleve" | "jules" | string; texte: string; horodatage?: string; images?: string[] }
export type Conversation = { id: string; mode: string; titre?: string; messages: MessageJules[] }
export type ConversationResume = { id: string; titre: string; mode: string; nb: number; debut: string; dernier: string }
export type ModeChat = { id: string; nom: string; icone: string; description: string; cache?: boolean }
export type InfosChat = Infos & {
  modes?: ModeChat[]
  notions?: { matieres: { nom: string; notions: { id: string; titre: string; chapitre: string; fiche?: boolean }[] }[]; bibliotheques: { titre: string; avertissement?: string }[] }
  epreuve?: boolean
  exercices?: { id: string; titre: string; nb: number; generateur?: boolean }[]
}

export const conversations = {
  lister: () => api<ConversationResume[]>("/api/conversations"),
  lire: (id: string) => api<Conversation>(`/api/conversations/${encodeURIComponent(id)}`),
  creer: (mode?: string) => api<{ id: string; mode: string }>("/api/conversations", json({ mode })),
  envoyer: (id: string, texte: string, photos?: Blob[]) => {
    const f = new FormData()
    f.append("texte", texte)
    if (photos) photos.forEach((b, i) => f.append("photos", b, `photo${i}.jpg`))
    return api<{ reponse: string; horodatage: string }>(`/api/conversations/${encodeURIComponent(id)}/messages`, { method: "POST", body: f })
  },
}

export const infosChat = () => api<InfosChat>("/api/infos")

export const epreuve = {
  proposition: () => api<{ notions: { notion: string }[] }>("/api/eleve/epreuve/proposition"),
  commencer: () => api<{ id: string; mode: string; titre: string; presentation: string }>("/api/eleve/epreuve/commencer", { method: "POST" }),
}

/* ---- recherche des notions (barre latérale) : index complet du référentiel, sans IA ---- */
// Forme : jules/modules/notions.py index_recherche() (GET /api/eleve/notions/index).

export type NotionRecherche = {
  id: string; titre: string; chapitre: string; matiere: string; nom_matiere: string; niveau: string
  /** Fiche visuelle disponible (« Mes fiches »). */
  fiche: boolean
  /** Leçon à blocs disponible (module cours). */
  lecon: boolean
  mots_cles: string[]
}

let indexNotions: Promise<NotionRecherche[]> | null = null
export const rechercheNotions = {
  /** Toutes les notions du référentiel ; une seule requête pour toute la session de la page. */
  index: () => (indexNotions ??= api<{ notions: NotionRecherche[] }>("/api/eleve/notions/index")
    .then((r) => r.notions).catch((e) => { indexNotions = null; throw e })),
}

export const notionsTravaillees = {
  lire: (convId: string) => api<{ notion: { id: string; titre: string; matiere: string; origine?: string } | null }>(`/api/eleve/notions/conversations/${encodeURIComponent(convId)}`),
  choisir: (convId: string, notionId: string) => api<{ notion: { id: string; titre: string; matiere: string } }>(`/api/eleve/notions/conversations/${encodeURIComponent(convId)}`, json({ notion: notionId }, "PUT")),
  retirer: (convId: string) => api<void>(`/api/eleve/notions/conversations/${encodeURIComponent(convId)}`, { method: "DELETE" }),
}

/* ---- exercices des fiches v2 : corrigés par le code (jules/fiches/correction.py), jamais par l'IA ---- */
// Formes : jules/fiches/parcours.py presenter() et jules/modules/exercices.py (route /repondre).

export type OptionExercice = { id: string; texte: string }
export type ExerciceVue = {
  id: string
  type: "nombre" | "expression" | "choix" | "texte_court" | "ordre" | "association" | string
  difficulte: number
  enonce: string
  aide_format?: string
  options?: OptionExercice[]
  plusieurs?: boolean
  elements?: OptionExercice[]
  gauche?: OptionExercice[]
  droite?: OptionExercice[]
}
export type ReponseExercice = string | string[] | Record<string, string>
export type Bilan = { faits: number; reussis: number; avec_indice: number; sans_indice: number; message: string }
export type Verdict = {
  verdict: "juste" | "faux" | "indice" | "illisible" | "relire" | "fini"
  message: string
  palier: number
  indice: string | null
  piege: string | null
  correction: string | null
  /** Après une réponse juste seulement : la solution rédigée de la fiche (« Pourquoi ? »). */
  pourquoi?: string | null
  termine: boolean
  a_revoir: string[]
  suivant: ExerciceVue | null
  bilan: Bilan | null
}
export type NotionExercices = { id: string; titre: string; matiere: string; nb: number; generateur: boolean }

const E = (s: string) => `/api/eleve/exercices/${encodeURIComponent(s)}`
let notionsExercices: Promise<NotionExercices[]> | null = null

export const exercices = {
  /** Notions entraînables (fiches v2 servables sans IA) ; une requête par page. */
  notions: () => (notionsExercices ??= api<{ exercices: NotionExercices[] }>("/api/eleve/exercices/notions")
    .then((r) => r.exercices).catch((e) => { notionsExercices = null; throw e })),
  commencer: (notion: string) => api<{ conversation: string; exercice: ExerciceVue; total: number }>(`${E(notion)}/commencer`, { method: "POST" }),
  generer: (notion: string) => api<{ conversation: string; exercice: ExerciceVue; total: number }>(`${E(notion)}/generer`, { method: "POST" }),
  repondre: (conv: string, reponse: ReponseExercice) => api<Verdict>(`${E(conv)}/repondre`, json({ reponse })),
  /** Coup de pouce demandé avant de répondre : palier suivant de l'échelle, décidé par le serveur. */
  indice: (conv: string) => api<{ indice: string | null; palier: number; message: string }>(`${E(conv)}/indice`, { method: "POST" }),
}

/* ---- studio : l'élève fabrique ses supports, Jules relit (docs/STUDIO-CONTRAT.md §3) ---- */

export type TypeSupport = "carte_mentale" | "fiche" | "quiz" | "cartes_memoire"
export type StatutSupport = "brouillon" | "relu" | "valide"
export type Noeud = { id: string; texte: string; parent: string | null }
export type Section = { id: string; titre: string; contenu: string }
export type QuestionQuiz = { id: string; question: string; reponse: string; forme: string }
export type CarteMemoire = { id: string; recto: string; verso: string; etat: string; prochaine_revision: string | null; palier: number }
export type Support = {
  id: string; notion: string; type: TypeSupport; titre: string; statut: StatutSupport; cree_le: string; modifie_le: string
  contenu: { noeuds?: Noeud[]; sections?: Section[]; questions?: QuestionQuiz[]; cartes?: CarteMemoire[] }
}
export type ResumeSupport = { id: string; type: TypeSupport; titre: string; statut: StatutSupport }
export type NotionStudio = { id: string; titre: string; chapitre: string; etat: string; lecon: boolean; supports: ResumeSupport[] }
export type CatalogueStudio = { matieres: { id: string; nom: string }[]; matiere: string; notions: NotionStudio[]; estimation?: string }
export type CarteDue = { support: string; carte_id: string; recto: string; notion: string }
export type ReponseCarte = "facile" | "difficile" | "rate"

const SUP = (id: string) => `/api/eleve/studio/supports/${encodeURIComponent(id)}`
type AvecSupport = { support: Support }

export const studio = {
  notions: (matiere?: string) => api<CatalogueStudio>(`/api/eleve/studio/notions${matiere ? `?matiere=${encodeURIComponent(matiere)}` : ""}`),
  creer: (notion: string, type: TypeSupport) => api<AvecSupport>(`/api/eleve/studio/notions/${encodeURIComponent(notion)}/creer`, json({ type })),
  lire: (id: string) => api<AvecSupport>(SUP(id)),
  ecrire: (id: string, chemin: (string | number)[], valeur: string) => api<AvecSupport>(`${SUP(id)}/ecrire`, json({ chemin, valeur })),
  rattacher: (id: string, index: number, parent: string | null) => api<AvecSupport>(`${SUP(id)}/rattacher`, json({ index, parent })),
  relire: (id: string) => api<{ retours: { chemin: (string | number)[]; message: string }[]; support: Support }>(`${SUP(id)}/relire`, { method: "POST" }),
  valider: (id: string) => api<AvecSupport>(`${SUP(id)}/valider`, { method: "POST" }),
  devalider: (id: string) => api<AvecSupport>(`${SUP(id)}/devalider`, { method: "POST" }),
  supprimer: async (id: string) => { const r = await fetch(SUP(id), { method: "DELETE", credentials: "same-origin" }); if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? `${r.status}`) },
  revisions: () => api<{ cartes: CarteDue[]; nombre_du_jour: number }>("/api/eleve/studio/revisions"),
  repondreCarte: (support: string, carte: string, reponse: ReponseCarte) =>
    api<{ carte: Omit<CarteMemoire, "verso">; restantes: number }>(`/api/eleve/studio/revisions/${encodeURIComponent(support)}/${encodeURIComponent(carte)}/reponse`, json({ reponse })),
}

/* ---- cours : leçons à blocs, correction par le code ---- */

export type EtatBloc = "a_faire" | "en_cours" | "reussi" | "a_revoir" | "fait"
export type Progression = {
  bloc_courant: number
  termine: boolean
  blocs: { index: number; etat: EtatBloc; tentatives: number; indices_vus: number }[]
}

export type Bloc =
  | { index: number; type: "objectifs"; items: string[] }
  | { index: number; type: "texte"; titre?: string; contenu: string }
  | { index: number; type: "exemple"; enonce: string; etapes: string[] }
  | { index: number; type: "exercice"; enonce: string; forme: "nombre" | "reponse_courte" | string; indices?: string[] }
  | { index: number; type: "question_ouverte"; question: string; indices?: string[] }
  | { index: number; type: "synthese"; consigne: string }

export type Lecon = {
  notion: string; titre: string; matiere: string; niveau: string; statut: string
  avertissement?: string; duree_minutes?: number
  sources: { titre: string; url: string; licence: string }[]
  blocs: Bloc[]
}

export type Session = { session: string; conversation: string; lecon: Lecon; progression: Progression }
export type Tentative = { juste: boolean | null; tentatives: number; explication: string | null; jules: string | null; progression: Progression }

export type NotionParcours = { id: string; titre: string; chapitre: string; etat: string; lecon: boolean; duree_minutes?: number }
export type Parcours = { matieres: { id: string; nom: string }[]; matiere: string; notions: NotionParcours[]; estimation: string }

const S = (id: string) => `/api/eleve/cours/sessions/${encodeURIComponent(id)}`

/* ---- retours : bugs, dysfonctionnements, suggestions (jules/modules/retours.py) ---- */
export type TypeRetour = "bug" | "dysfonctionnement" | "suggestion" | "amelioration"
export const retours = {
  deposer: (r: { type: TypeRetour; texte: string; adresse: string; titre_page: string; ecran: string; auteur?: string }) =>
    api<{ id: string; ok: boolean }>("/api/eleve/retours/deposer", json(r)),
}

/* ---- synchro : l'état de l'interface suit l'élève d'un appareil à l'autre (jules/modules/synchro.py) ---- */
export const synchro = {
  etat: () => api<Record<string, unknown>>("/api/eleve/synchro/etat"),
  ecrire: (cle: string, valeur: unknown) => api<{ valeur: unknown }>(`/api/eleve/synchro/${encodeURIComponent(cle)}`, json({ valeur }, "PUT")),
}

export type BilanNotions = {
  groupes: { etat: string; titre: string; notions: { notion: string; titre: string; matiere: string; nom_matiere: string; savoir_faire: string[]; lecon: boolean }[] }[]
  a_explorer: number
  estimation: string
}

export const cours = {
  bilan: (matiere?: string) => api<BilanNotions>(`/api/eleve/cours/bilan${matiere ? `?matiere=${encodeURIComponent(matiere)}` : ""}`),
  parcours: (matiere?: string) => api<Parcours>(`/api/eleve/cours/parcours${matiere ? `?matiere=${encodeURIComponent(matiere)}` : ""}`),
  ouvrir: (notion: string) => api<Session>(`/api/eleve/cours/lecons/${encodeURIComponent(notion)}/ouvrir`, { method: "POST" }),
  session: (id: string) => api<Session>(S(id)),
  tentative: (id: string, bloc: number, reponse: string) => api<Tentative>(`${S(id)}/blocs/${bloc}/tentative`, json({ reponse })),
  indice: (id: string, bloc: number) => api<{ indice: string | null; restants: number; progression: Progression }>(`${S(id)}/blocs/${bloc}/indice`, { method: "POST" }),
  fait: (id: string, bloc: number) => api<{ progression: Progression }>(`${S(id)}/blocs/${bloc}/fait`, { method: "POST" }),
}

/* ---- sources personnelles (docs/SOURCES-CONTRAT.md, jules/modules/sources.py) ---- */

export type SuggestionSource = { notion: string | null; titre_notion: string | null; matiere: string | null; raison: string; avertissement: string }
export type EtatFichePerso = "a_ranger" | "rangee"
export type EntreePerso = {
  id: string; titre: string; notion: string | null; matiere: string | null; dossier: string | null
  etat: EtatFichePerso; suggestion: SuggestionSource; cree_le: string
  source: { id: string; type: "photos" | "pdf" | "texte"; titre: string; fichiers: string[] }
  titre_notion?: string | null; chapitre?: string | null; nom_matiere?: string | null
}
export type DossierPerso = { id: string; nom: string }
export type BibliothequePerso = { fiches: EntreePerso[]; dossiers: DossierPerso[]; quota: { par_jour: number; utilisees: number } }
export type FichePerso = Fiche & {
  id: string; origine: "personnelle"
  rangement: Pick<EntreePerso, "etat" | "notion" | "dossier" | "suggestion" | "cree_le">
  source: EntreePerso["source"]
}
export type EtapeSource =
  | { etape: "notion" } | { etape: "ecriture"; suggestion: SuggestionSource } | { etape: "verification" }
  | { etape: "fin"; fiche: EntreePerso } | { etape: "erreur"; message: string }
export type ModeRangement = "notion" | "dossier" | "non_classe"

const SRC = "/api/eleve/sources"
const F = (id: string) => `${SRC}/fiches/${encodeURIComponent(id)}`
const envoi = (method: string, corps?: unknown): RequestInit =>
  corps === undefined ? { method } : { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corps) }

/** Étapes réelles de la génération (NDJSON), transmises au fil de l'eau. */
async function flux(chemin: string, init: RequestInit, surEtape: (e: EtapeSource) => void): Promise<EtapeSource> {
  const r = await fetch(chemin, { credentials: "same-origin", ...init })
  if (!r.ok || !r.body) {
    let detail = `${r.status}`
    try { detail = (await r.json()).detail ?? detail } catch { /* corps non JSON */ }
    throw new Error(detail)
  }
  const lecteur = r.body.pipeThrough(new TextDecoderStream()).getReader()
  let reste = "", derniere: EtapeSource = { etape: "erreur", message: "La génération s'est interrompue." }
  for (;;) {
    const { value, done } = await lecteur.read()
    if (done) break
    reste += value
    const lignes = reste.split("\n")
    reste = lignes.pop() ?? ""
    for (const l of lignes) if (l.trim()) { derniere = JSON.parse(l); surEtape(derniere) }
  }
  if (reste.trim()) { derniere = JSON.parse(reste); surEtape(derniere) }
  return derniere
}

export const sources = {
  deposer: (entree: { photos?: File[]; pdf?: File; texte?: string; matiere?: string }, surEtape: (e: EtapeSource) => void) => {
    const corps = new FormData()
    for (const p of entree.photos ?? []) corps.append("photos", p)
    if (entree.pdf) corps.append("pdf", entree.pdf)
    if (entree.texte) corps.append("texte", entree.texte)
    if (entree.matiere) corps.append("matiere", entree.matiere)
    return flux(`${SRC}/deposer`, { method: "POST", body: corps }, surEtape)
  },
  regenerer: (id: string, surEtape: (e: EtapeSource) => void) => flux(`${F(id)}/regenerer`, { method: "POST" }, surEtape),
  bibliotheque: () => api<BibliothequePerso>(`${SRC}/fiches`),
  lire: (id: string) => api<FichePerso>(F(id)),
  /** Le document d'origine (texte lu, images) pour la version lisible (idée H). */
  source: (id: string) => api<{ type: string; titre: string; texte: string; images: string[] }>(`${F(id)}/source`),
  ranger: (id: string, mode: ModeRangement, dossier?: string) => api<EntreePerso>(`${F(id)}/ranger`, json({ mode, dossier })),
  renommer: (id: string, titre: string) => api<EntreePerso>(F(id), envoi("PATCH", { titre })),
  supprimer: (id: string) => api<{ ok: boolean }>(F(id), envoi("DELETE")),
  aRanger: () => api<EntreePerso[]>(`${SRC}/a_ranger`),
  creerDossier: (nom: string) => api<DossierPerso>(`${SRC}/dossiers`, json({ nom })),
  renommerDossier: (id: string, nom: string) => api<DossierPerso>(`${SRC}/dossiers/${encodeURIComponent(id)}`, envoi("PATCH", { nom })),
  supprimerDossier: (id: string) => api<{ deplacees: number }>(`${SRC}/dossiers/${encodeURIComponent(id)}`, envoi("DELETE")),
}
