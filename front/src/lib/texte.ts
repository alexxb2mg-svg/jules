// Petits outils de texte partagés par les écrans (recherche locale, comparaisons).

/** Comparaison sans accents ni casse, pour la recherche. */
export const plat = (s: string) => s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()
