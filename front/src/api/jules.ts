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
const json = (corps: unknown): RequestInit => ({
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corps),
})

/* ---- session, infos de l'interface (persona, leviers dys) ---- */

export type EtatSession = { role: string | null; eleve: boolean; parent: boolean }
export type Infos = {
  prenom: string
  persona: { id: string; nom: string; accueil: string; couleurs: Record<string, string>; avatar: boolean }
  leviers: Record<string, unknown>
  leviers_css: Record<string, string>
}

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

export const conversations = {
  lire: (id: string) => api<Conversation>(`/api/conversations/${encodeURIComponent(id)}`),
  creer: (mode?: string) => api<{ id: string; mode: string }>("/api/conversations", json({ mode })),
  envoyer: (id: string, texte: string) => {
    const f = new FormData()
    f.append("texte", texte)
    return api<{ reponse: string; horodatage: string }>(`/api/conversations/${encodeURIComponent(id)}/messages`, { method: "POST", body: f })
  },
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

export type NotionParcours = { id: string; titre: string; chapitre: string; etat: string; lecon: boolean }
export type Parcours = { matieres: { id: string; nom: string }[]; matiere: string; notions: NotionParcours[]; estimation: string }

const S = (id: string) => `/api/eleve/cours/sessions/${encodeURIComponent(id)}`

export const cours = {
  parcours: (matiere?: string) => api<Parcours>(`/api/eleve/cours/parcours${matiere ? `?matiere=${encodeURIComponent(matiere)}` : ""}`),
  ouvrir: (notion: string) => api<Session>(`/api/eleve/cours/lecons/${encodeURIComponent(notion)}/ouvrir`, { method: "POST" }),
  session: (id: string) => api<Session>(S(id)),
  tentative: (id: string, bloc: number, reponse: string) => api<Tentative>(`${S(id)}/blocs/${bloc}/tentative`, json({ reponse })),
  indice: (id: string, bloc: number) => api<{ indice: string | null; restants: number; progression: Progression }>(`${S(id)}/blocs/${bloc}/indice`, { method: "POST" }),
  fait: (id: string, bloc: number) => api<{ progression: Progression }>(`${S(id)}/blocs/${bloc}/fait`, { method: "POST" }),
}
