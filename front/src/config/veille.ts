// Petites idées de la veille UI (docs/veille/synthese-ui-dinobot-marche.md), en données :
// C « Continuer », G légende d'origine, P pastilles « Nouveau », F revoir les ratées, B suggestions.
// Les composants lisent ce fichier ; aucun libellé métier n'est écrit ailleurs.

/** P : entrées signalées « Nouveau » jusqu'à une date (AAAA-MM-JJ), puis la pastille disparaît seule. */
export const NOUVEAUTES: Record<string, string> = {
  "fiches:ajouter": "2026-10-31",
}
export const LIBELLE_NOUVEAU = "Nouveau"
export const estNouveau = (cle: string, aujourdhui = new Date().toISOString().slice(0, 10)) =>
  (NOUVEAUTES[cle] ?? "") >= aujourdhui

/** C : reprise en un clic, en tête de « Mes fiches ». */
export const REPRISE = {
  continuer: "Continuer",
  fiche: "ta fiche",
  lecon: "ta leçon",
  perso: "ta fiche perso",
  cartes: (n: number) => `${n} carte${n > 1 ? "s" : ""} à revoir aujourd'hui`,
  reviser: "Réviser",
}

/** G : légende des étiquettes d'origine, en tête de la bibliothèque. */
export const LEGENDE = {
  jules: { nom: "Jules", texte: "fiches vérifiées de Jules" },
  perso: { nom: "Perso", texte: "fiches faites depuis tes documents" },
}

/** F : fin de révision. Le tour « ratées » est un entraînement : il ne change pas les dates de révision. */
export const REVOIR_RATEES = {
  bouton: (n: number) => `Revoir ${n === 1 ? "la carte ratée" : `les ${n} cartes ratées`}`,
  explication: "Juste pour t'entraîner : ça ne change pas quand elles reviendront.",
  fin: "Tour d'entraînement terminé.",
}

/** B : suggestions sous le chat, construites depuis la leçon affichée (jamais générées). */
export const SUGGESTIONS = {
  titre: "Suggestions",
  // Libellés entiers (jamais coupés au milieu d'un mot : illisible en dys) ; l'affichage limite à 2 lignes.
  objectif: (o: string) => ({ libelle: o, message: `Aide-moi à savoir faire ceci, sans me donner la réponse : « ${o} »` }),
  partie: (t: string) => ({ libelle: `Réexplique-moi « ${t} »`, message: `Tu peux me réexpliquer la partie « ${t} » autrement ?` }),
  max: 4,
}
