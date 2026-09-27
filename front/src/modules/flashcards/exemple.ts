import type { PaquetFlash } from "./types"

export const PAQUET_EQUATIONS: PaquetFlash = {
  id: "maths-3e-equations",
  titre: "Équations",
  matiere: "maths",
  cartes: [
    {
      id: "eq-1er-degre",
      recto: "Résoudre 3x + 5 = 11",
      verso: "3x = 11 − 5\n3x = 6\nx = 2",
      indice: "Isole x : enlève 5, puis divise par 3.",
    },
    {
      id: "eq-regle",
      recto: "Dans une équation, que peut-on faire aux deux membres ?",
      verso: "Ajouter ou soustraire le même nombre.\nMultiplier ou diviser par le même nombre (pas 0).",
    },
    {
      id: "eq-produit-nul",
      recto: "Règle du produit nul",
      verso: "Si A × B = 0,\nalors A = 0 ou B = 0.",
      indice: "Un produit vaut 0 si un facteur vaut 0.",
    },
    {
      id: "eq-produit-nul-exemple",
      recto: "Résoudre (x − 2)(x + 3) = 0",
      verso: "x − 2 = 0 ou x + 3 = 0\nx = 2 ou x = −3",
      indice: "Produit nul.",
    },
    {
      id: "eq-carre-positif",
      recto: "Solutions de x² = a, avec a > 0 ?",
      verso: "Deux solutions :\nx = √a ou x = −√a\n(si a = 0 : x = 0 ; si a < 0 : aucune)",
    },
    {
      id: "eq-carre-exemple",
      recto: "Résoudre x² = 25",
      verso: "x = 5 ou x = −5",
      indice: "Pense aux deux signes.",
    },
  ],
}
