// Types d'une fiche visuelle, recopiés champ pour champ de bibliotheque/SCHEMA-FICHE-VISUELLE.md et de la
// réponse de GET /api/eleve/fiches_visuelles/notions/<id> (jules/modules/fiches_visuelles.py).
// Le front ne crée aucun format : un type de bloc inconnu du registre n'est pas affiché.

export type Couleur = "bleu" | "orange" | "vert" | "rouge" | "violet" | "gris" | string

type Base = { id: string; adresse: string; titre?: string; jules?: string }

export type BlocAttendus = Base & { type: "attendus"; attendus: string[] }
export type BlocFormule = Base & {
  type: "formule"; expression: string
  termes: Record<string, { couleur: Couleur; legende: string }>
  ordre?: string[]
}
export type NoeudCarte = { id: string; titre: string; sous_titre?: string; principal?: boolean }
export type BlocCarte = Base & { type: "carte"; noeuds: NoeudCarte[]; liens: { de: string; vers: string; libelle?: string }[] }
export type Curseur = { id: string; nom: string; min: number; max: number; pas?: number; depart?: number }
export type BlocGraphe = Base & { type: "graphe"; gabarit: string; curseurs: Curseur[]; lectures: { si: string; texte: string }[] }
export type BlocMethode = Base & { type: "methode"; etapes: string[] }
export type BlocPiege = Base & { type: "piege"; mauvaise_idee: string; pourquoi_faux?: string; bonne_idee: string }
export type BlocExemple = Base & {
  type: "exemple"; situation?: string; calcul?: string; conclusion?: string
  figure?: { gabarit: string; curseurs?: Curseur[] }
}
export type LienRenfort = { icone?: string; titre: string; description?: string; outil?: string }
export type BlocRenfort = Base & { type: "renfort"; liens: LienRenfort[] }
export type BlocSchema = Base & { type: "schema"; svg: string }

export type BlocFiche =
  | BlocAttendus | BlocFormule | BlocCarte | BlocGraphe | BlocMethode
  | BlocPiege | BlocExemple | BlocRenfort | BlocSchema

export type TypeBloc = BlocFiche["type"]

export type Fiche = {
  notion: string
  titre: string
  matiere: string
  nom_matiere: string
  niveau: string
  statut: string
  relecture: string
  relecture_a_relire: boolean
  avertissement?: string
  licence: string
  sources: { titre: string; url?: string; licence?: string }[]
  variables: Record<string, string>
  abreviations: Record<string, string>
  blocs: BlocFiche[]
}

export type NotionIndex = { id: string; titre: string; chapitre: string }
export type MatiereIndex = { id: string; nom: string; notions: NotionIndex[] }
export type IndexFiches = { matieres: MatiereIndex[] }
