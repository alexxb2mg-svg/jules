// Client HTTP du serveur Jules (FastAPI). Seul point d'accès réseau du front : tout passe par ici.
// Les formes reprennent exactement les réponses de jules/web/app.py et jules/modules/cours.py.

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
