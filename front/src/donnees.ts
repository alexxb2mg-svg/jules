// Données de maquette : matières et chapitres de 3e, avec un état de progression fictif pour Ellie.
// À remplacer par /api/infos (notions.bibliotheques) une fois l'écran validé.

export type Matiere = {
  id: string
  nom: string
  couleur: string // classe Tailwind bg-*
  chapitres: Chapitre[]
}

export type Chapitre = {
  id: string
  titre: string
  etat: "nouveau" | "en-cours" | "acquis" | "fragile"
  fiches: number
  exercices: number
}

export const MATIERES: Matiere[] = [
  {
    id: "maths", nom: "Maths", couleur: "bg-maths",
    chapitres: [
      { id: "m1", titre: "Nombres rationnels et fractions", etat: "acquis", fiches: 3, exercices: 12 },
      { id: "m2", titre: "Calcul littéral : développer, factoriser", etat: "en-cours", fiches: 2, exercices: 9 },
      { id: "m3", titre: "Équations du premier degré", etat: "fragile", fiches: 2, exercices: 8 },
      { id: "m4", titre: "Théorème de Pythagore", etat: "acquis", fiches: 1, exercices: 6 },
      { id: "m5", titre: "Théorème de Thalès", etat: "en-cours", fiches: 1, exercices: 6 },
      { id: "m6", titre: "Fonctions linéaires et affines", etat: "nouveau", fiches: 2, exercices: 7 },
      { id: "m7", titre: "Statistiques : moyenne, médiane, étendue", etat: "nouveau", fiches: 1, exercices: 5 },
      { id: "m8", titre: "Probabilités", etat: "nouveau", fiches: 1, exercices: 5 },
    ],
  },
  {
    id: "francais", nom: "Français", couleur: "bg-francais",
    chapitres: [
      { id: "f1", titre: "Accord du participe passé", etat: "fragile", fiches: 2, exercices: 6 },
      { id: "f2", titre: "La phrase complexe", etat: "en-cours", fiches: 1, exercices: 4 },
      { id: "f3", titre: "Récit de soi et autoportrait", etat: "nouveau", fiches: 2, exercices: 3 },
      { id: "f4", titre: "Satire et dénonciation sociale", etat: "nouveau", fiches: 1, exercices: 2 },
    ],
  },
  {
    id: "hg", nom: "Histoire-géo", couleur: "bg-hg",
    chapitres: [
      { id: "h1", titre: "La Première Guerre mondiale", etat: "acquis", fiches: 3, exercices: 4 },
      { id: "h2", titre: "Régimes totalitaires", etat: "en-cours", fiches: 2, exercices: 3 },
      { id: "h3", titre: "La Seconde Guerre mondiale", etat: "nouveau", fiches: 4, exercices: 5 },
      { id: "h4", titre: "Les aires urbaines en France", etat: "nouveau", fiches: 2, exercices: 3 },
    ],
  },
  {
    id: "pc", nom: "Physique-chimie", couleur: "bg-pc",
    chapitres: [
      { id: "p1", titre: "Atomes et classification périodique", etat: "en-cours", fiches: 2, exercices: 5 },
      { id: "p2", titre: "Poids, masse, gravitation", etat: "nouveau", fiches: 1, exercices: 4 },
      { id: "p3", titre: "Énergie cinétique", etat: "nouveau", fiches: 1, exercices: 4 },
    ],
  },
  {
    id: "svt", nom: "SVT", couleur: "bg-svt",
    chapitres: [
      { id: "s1", titre: "ADN, mutations, méiose", etat: "nouveau", fiches: 2, exercices: 3 },
      { id: "s2", titre: "Réactions immunitaires", etat: "nouveau", fiches: 1, exercices: 2 },
    ],
  },
  { id: "techno", nom: "Technologie", couleur: "bg-techno", chapitres: [
      { id: "t1", titre: "Algorithmes et programmation par blocs", etat: "en-cours", fiches: 3, exercices: 4 },
  ] },
  { id: "anglais", nom: "Anglais", couleur: "bg-anglais", chapitres: [
      { id: "a1", titre: "Écouter et comprendre", etat: "nouveau", fiches: 1, exercices: 0 },
  ] },
]

export const ELEVE = { prenom: "Ellie", classe: "3e" }

// Ce que Jules propose de reprendre : dernier chapitre travaillé + chapitre fragile.
export const REPRISE = { matiere: "maths", chapitre: "m5", depuis: "hier, 18 min" }
export const FRAGILE = { matiere: "maths", chapitre: "m3", raison: "2 erreurs sur 3 au dernier quiz" }
