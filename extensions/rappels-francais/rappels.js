// Extension rappels-francais : abreviations de grammaire (famille `rappels`, docs/EXTENSIONS.md).
// Des donnees seules : Symboles.dictionnaire() du coeur fait le reste.
"use strict";

Symboles.dictionnaire({
  id: "grammaire", matieres: ["francais"], classe: "abreviation",
  entrees: {
    COD: "complément d'objet direct (répond à « quoi ? » ou « qui ? » après le verbe)",
    COI: "complément d'objet indirect (introduit par à, de...)",
    COS: "complément d'objet second",
    CC: "complément circonstanciel",
    CCT: "complément circonstanciel de temps",
    CCL: "complément circonstanciel de lieu",
    CCM: "complément circonstanciel de manière",
    CCB: "complément circonstanciel de but",
    CCC: "complément circonstanciel de cause",
    GN: "groupe nominal",
    GNS: "groupe nominal sujet",
    GV: "groupe verbal",
    GP: "groupe prépositionnel",
    "adj.": "adjectif",
    "adv.": "adverbe",
    "prép.": "préposition",
    "pron.": "pronom",
    "dét.": "déterminant",
    "conj.": "conjonction",
    "sing.": "singulier",
    "plur.": "pluriel",
    "masc.": "masculin",
    "fém.": "féminin",
  },
});
