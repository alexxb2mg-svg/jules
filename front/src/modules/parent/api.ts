// Client API de l'espace parent. Reproduit les appels de parent.js (page statique).
// Aucune donnée fictive : tout vient du serveur.

async function api<T>(chemin: string, init?: RequestInit): Promise<T> {
  const r = await fetch(chemin, { credentials: "same-origin", ...init })
  if (!r.ok) {
    let detail = `${r.status}`
    try { detail = (await r.json()).detail ?? detail } catch { /* corps non JSON */ }
    throw new Error(detail)
  }
  return r.json() as Promise<T>
}

const json = (corps: unknown, methode = "POST"): RequestInit => ({
  method: methode, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corps),
})

/* ---- session ---- */

export type EtatSession = { parent: boolean; eleve: boolean; role: string | null }

export const sessionParent = {
  etat: () => api<EtatSession>("/api/session"),
  ouvrir: (code: string) => api<{ role: string }>("/api/session", json({ code })),
}

/* ---- modules actifs ---- */

export type ModuleActif = { id: string }

export const modulesActifs = () => api<ModuleActif[]>("/api/parent/modules")

/* ---- alertes (vigilance) ---- */

export type Alerte = {
  horodatage: string
  donnees: { niveau: string; motif: string }
}

export const alertes = () => api<Alerte[]>("/api/parent/evenements/vigilance")

/* ---- rapport du jour ---- */

export type Rapport = { texte: string }
export type EnvoiRapport = { envoye: boolean; erreurs?: string[] }

export const rapport = {
  lire: (date: string) => api<Rapport>(`/api/modules/rapport/jour?date=${encodeURIComponent(date)}`),
  envoyer: (date: string) => api<EnvoiRapport>(`/api/modules/rapport/envoyer?date=${encodeURIComponent(date)}`, { method: "POST" }),
}

/* ---- notes (infos pour Jules) ---- */

export type Note = { id: string; texte: string; jusqu_au: string | null }

export const notes = {
  lister: () => api<Note[]>("/api/modules/memoire/notes"),
  ajouter: (texte: string, jusqu_au: string | null) => api<Note>("/api/modules/memoire/notes", json({ texte, jusqu_au })),
  supprimer: (id: string) => api<void>(`/api/modules/memoire/notes/${encodeURIComponent(id)}`, { method: "DELETE" }),
}

/* ---- retours (bugs, suggestions) ---- */

export type Retour = {
  id: string; type: string; texte: string; adresse: string; ecran?: string
  auteur?: string; traite: boolean; cree_le: string
}

const TYPES_RETOUR: Record<string, string> = {
  bug: "Bug", dysfonctionnement: "Ça marche mal", suggestion: "Suggestion", amelioration: "Amélioration",
}
export const libelleRetour = (type: string) => TYPES_RETOUR[type] || type

export const retours = {
  lister: (traites = false) => api<Retour[]>(`/api/modules/retours/liste${traites ? "" : "?traite=false"}`),
  basculer: (id: string, traite: boolean) => api<Retour>(`/api/modules/retours/${encodeURIComponent(id)}`, json({ traite }, "PATCH")),
  supprimer: (id: string) => api<void>(`/api/modules/retours/${encodeURIComponent(id)}`, { method: "DELETE" }),
}

/* ---- conversations ---- */

export type ConversationResume = { id: string; mode: string; titre?: string; debut: string; nb: number }
export type Message = { role: string; texte: string; images: string[] }
export type ConversationComplete = { messages: Message[] }

export const conversations = {
  lister: (jour: string) => api<ConversationResume[]>(`/api/conversations?jour=${encodeURIComponent(jour)}`),
  lire: (id: string) => api<ConversationComplete>(`/api/conversations/${encodeURIComponent(id)}`),
  supprimer: (id: string) => api<void>(`/api/parent/conversations/${encodeURIComponent(id)}`, { method: "DELETE" }),
}

/* ---- adaptations (aménagements PAP) ---- */

export type Amenagement = {
  id: string; texte?: string; page?: number; coche: boolean
  rubrique_autres?: boolean; mention?: string
  reference?: { texte: string; nom_niveau: string; page: number }
}

export type PreferencesChoix = { choix: { valeur: string; libelle: string }[]; valeur: string }

export type Conflit = { id: string; message: string }

export type EtatAdaptations = {
  nom_niveau: string; niveau_reconnu: boolean
  amenagements: Amenagement[]
  rubrique_autres: { titre: string; page?: number }
  preferences: { police: PreferencesChoix; fond: PreferencesChoix }
  lecture_automatique: boolean
  conflits: Conflit[]
}

export type ChoixAdaptations = { amenagements: string[]; preferences: Record<string, string> }

export const adaptations = {
  charger: () => api<EtatAdaptations>("/api/parent/adaptations"),
  apercu: (choix: ChoixAdaptations) => api<{ conflits: Conflit[] }>("/api/parent/adaptations/apercu", json(choix)),
  enregistrer: (choix: ChoixAdaptations) => api<EtatAdaptations>("/api/parent/adaptations", json(choix, "PUT")),
}

/* ---- dossier (export + effacement) ---- */

export type ResultatEffacement = { efface: { conversations: number; evenements: number; bilans: number } }

export const dossier = {
  exportUrl: "/api/parent/dossier/export",
  effacer: (confirmation: string) => api<ResultatEffacement>("/api/parent/dossier/effacer", json({ confirmation })),
}
